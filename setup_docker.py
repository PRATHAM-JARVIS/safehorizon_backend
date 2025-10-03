#!/usr/bin/env python3
"""
SafeHorizon Docker Setup Script
==============================

Alternative setup using Docker containers for easier deployment.
This script sets up everything using Docker Compose.

Usage:
    python setup_docker.py --environment production
    python setup_docker.py --environment development --with-sample-data
"""

import os
import sys
import subprocess
import logging
import argparse
import secrets
import asyncio
from pathlib import Path
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DockerSetup:
    def __init__(self, environment='production', with_sample_data=False):
        self.environment = environment
        self.with_sample_data = with_sample_data
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / '.env'

    def run_command(self, command, check=True, shell=True, capture_output=False):
        """Run a system command with error handling"""
        logger.info(f"Running: {command}")
        try:
            if capture_output:
                result = subprocess.run(command, shell=shell, check=check, 
                                      capture_output=True, text=True)
                return result.stdout.strip()
            else:
                subprocess.run(command, shell=shell, check=check)
                return None
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {command}")
            logger.error(f"Error: {e}")
            raise

    def check_docker(self):
        """Check if Docker and Docker Compose are installed"""
        logger.info("Checking Docker installation...")
        
        try:
            docker_version = self.run_command("docker --version", capture_output=True)
            logger.info(f"Found: {docker_version}")
        except subprocess.CalledProcessError:
            logger.error("Docker is not installed or not in PATH")
            logger.info("Please install Docker: https://docs.docker.com/get-docker/")
            sys.exit(1)
        
        try:
            compose_version = self.run_command("docker compose version", capture_output=True)
            logger.info(f"Found: {compose_version}")
        except subprocess.CalledProcessError:
            try:
                compose_version = self.run_command("docker-compose --version", capture_output=True)
                logger.info(f"Found: {compose_version}")
            except subprocess.CalledProcessError:
                logger.error("Docker Compose is not installed or not in PATH")
                logger.info("Please install Docker Compose")
                sys.exit(1)

    def create_env_file(self):
        """Create .env file with Docker-specific configuration"""
        logger.info("Creating Docker environment configuration...")
        
        jwt_secret = secrets.token_urlsafe(64)
        db_password = secrets.token_urlsafe(32)
        
        env_content = f"""# SafeHorizon Docker Environment Configuration
# Generated on {datetime.now(timezone.utc).isoformat()}

# Application Settings
APP_NAME=SafeHorizon API
APP_ENV={self.environment}
APP_DEBUG={'true' if self.environment == 'development' else 'false'}
API_PREFIX=/api

# Database Configuration (Docker)
POSTGRES_USER=safehorizon_user
POSTGRES_PASSWORD={db_password}
POSTGRES_DB=safehorizon
DATABASE_URL=postgresql+asyncpg://safehorizon_user:{db_password}@db:5432/safehorizon
SYNC_DATABASE_URL=postgresql://safehorizon_user:{db_password}@db:5432/safehorizon

# Redis Configuration (Docker)
REDIS_URL=redis://redis:6379/0

# Security
JWT_SECRET_KEY={jwt_secret}

# External Services (Optional - Configure as needed)
# FIREBASE_CREDENTIALS_JSON_PATH=./firebase-credentials.json
# TWILIO_ACCOUNT_SID=your_twilio_account_sid
# TWILIO_AUTH_TOKEN=your_twilio_auth_token
# TWILIO_FROM_NUMBER=your_twilio_phone_number

# CORS Configuration
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173","http://localhost:8080","*"]

# Models Directory
MODELS_DIR=./models_store
"""
        
        with open(self.env_file, 'w') as f:
            f.write(env_content)
        
        logger.info(f"Environment file created: {self.env_file}")

    def create_docker_compose_override(self):
        """Create docker-compose override for environment-specific settings"""
        if self.environment == 'development':
            override_content = """version: "3.9"
services:
  api:
    volumes:
      - .:/app
    environment:
      - APP_DEBUG=true
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"

  db:
    ports:
      - "5432:5432"

  redis:
    ports:
      - "6379:6379"
"""
        else:
            override_content = """version: "3.9"
services:
  api:
    restart: unless-stopped
    environment:
      - APP_DEBUG=false
    command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

  nginx:
    image: nginx:alpine
    container_name: safehorizon_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/nginx/ssl  # Mount SSL certificates here
    depends_on:
      - api
    restart: unless-stopped
"""
        
        override_file = self.project_root / f'docker-compose.{self.environment}.yml'
        with open(override_file, 'w') as f:
            f.write(override_content)
        
        logger.info(f"Docker Compose override created: {override_file}")

    def create_init_script(self):
        """Create database initialization script"""
        init_script = """#!/bin/bash
set -e

# Create extensions
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS postgis;
    CREATE EXTENSION IF NOT EXISTS postgis_topology;
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
EOSQL

echo "Database initialization completed!"
"""
        
        init_file = self.project_root / 'init-db.sh'
        with open(init_file, 'w') as f:
            f.write(init_script)
        
        # Make it executable
        os.chmod(init_file, 0o755)
        logger.info(f"Database init script created: {init_file}")

    def create_production_dockerfile(self):
        """Create optimized production Dockerfile"""
        if self.environment != 'production':
            return
            
        dockerfile_content = """# Multi-stage build for production
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \\
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \\
    libpq5 \\
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN groupadd -r safehorizon && useradd -r -g safehorizon safehorizon

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Create models directory
RUN mkdir -p models_store && chown -R safehorizon:safehorizon models_store

# Change ownership of app directory
RUN chown -R safehorizon:safehorizon /app

# Switch to non-root user
USER safehorizon

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
"""
        
        dockerfile_prod = self.project_root / 'Dockerfile.production'
        with open(dockerfile_prod, 'w') as f:
            f.write(dockerfile_content)
        
        logger.info(f"Production Dockerfile created: {dockerfile_prod}")

    def create_sample_data_script(self):
        """Create script to populate sample data"""
        if not self.with_sample_data:
            return
            
        script_content = """#!/usr/bin/env python3
import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, '/app')

from app.database import AsyncSessionLocal
from app.models.database_models import Tourist, Authority, RestrictedZone, ZoneType
from app.auth.local_auth import local_auth

async def create_sample_data():
    print("Creating sample data...")
    
    async with AsyncSessionLocal() as session:
        # Create sample tourists
        sample_tourists = [
            Tourist(
                id='tourist_001',
                email='john.doe@example.com',
                name='John Doe',
                phone='+1234567890',
                emergency_contact='Jane Doe',
                emergency_phone='+1234567891',
                password_hash=local_auth.hash_password('password123'),
                safety_score=85,
                last_location_lat=40.7128,
                last_location_lon=-74.0060
            ),
            Tourist(
                id='tourist_002',
                email='alice.smith@example.com',
                name='Alice Smith',
                phone='+1234567892',
                emergency_contact='Bob Smith',
                emergency_phone='+1234567893',
                password_hash=local_auth.hash_password('password123'),
                safety_score=92,
                last_location_lat=34.0522,
                last_location_lon=-118.2437
            )
        ]
        
        for tourist in sample_tourists:
            session.add(tourist)
        
        # Create sample authorities
        sample_authorities = [
            Authority(
                id='auth_001',
                email='officer.johnson@police.gov',
                name='Officer Johnson',
                badge_number='BADGE001',
                department='NYPD',
                rank='Sergeant',
                phone='+1234567894',
                password_hash=local_auth.hash_password('police123')
            ),
            Authority(
                id='auth_002',
                email='detective.brown@police.gov',
                name='Detective Brown',
                badge_number='BADGE002',
                department='LAPD',
                rank='Detective',
                phone='+1234567895',
                password_hash=local_auth.hash_password('police123')
            )
        ]
        
        for authority in sample_authorities:
            session.add(authority)
        
        # Create sample zones
        sample_zones = [
            RestrictedZone(
                name='High Crime Area Downtown',
                description='Area with increased criminal activity',
                zone_type=ZoneType.RISKY,
                center_latitude=40.7589,
                center_longitude=-73.9851,
                radius_meters=500,
                created_by='auth_001'
            ),
            RestrictedZone(
                name='Tourist Safe Zone',
                description='Well-monitored tourist area',
                zone_type=ZoneType.SAFE,
                center_latitude=40.7614,
                center_longitude=-73.9776,
                radius_meters=750,
                created_by='auth_002'
            )
        ]
        
        for zone in sample_zones:
            session.add(zone)
        
        await session.commit()
        print("Sample data created successfully!")

if __name__ == '__main__':
    asyncio.run(create_sample_data())
"""
        
        script_file = self.project_root / 'create_sample_data.py'
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        logger.info(f"Sample data script created: {script_file}")

    def build_and_start_containers(self):
        """Build and start Docker containers"""
        logger.info("Building and starting Docker containers...")
        
        # Build containers
        if self.environment == 'production':
            self.run_command("docker compose -f docker-compose.yml -f docker-compose.production.yml build")
        else:
            self.run_command("docker compose -f docker-compose.yml -f docker-compose.development.yml build")
        
        # Start containers
        if self.environment == 'production':
            self.run_command("docker compose -f docker-compose.yml -f docker-compose.production.yml up -d")
        else:
            self.run_command("docker compose -f docker-compose.yml -f docker-compose.development.yml up -d")

    def run_migrations(self):
        """Run database migrations inside container"""
        logger.info("Running database migrations...")
        
        # Wait for database to be ready
        self.run_command("docker compose exec -T api python -c \\"import time; time.sleep(10)\\"")
        
        # Run migrations
        self.run_command("docker compose exec -T api alembic upgrade head")

    def create_sample_data_in_container(self):
        """Create sample data inside container"""
        if not self.with_sample_data:
            return
            
        logger.info("Creating sample data in container...")
        self.run_command("docker compose exec -T api python create_sample_data.py")

    def validate_deployment(self):
        """Validate that containers are running correctly"""
        logger.info("Validating Docker deployment...")
        
        # Check container status
        result = self.run_command("docker compose ps", capture_output=True)
        logger.info("Container status:")
        logger.info(result)
        
        # Check API health
        try:
            import time
            time.sleep(5)  # Wait for services to be ready
            
            health_check = self.run_command("curl -f http://localhost:8000/health || echo 'Health check failed'", 
                                          capture_output=True)
            if "ok" in health_check:
                logger.info("✅ API health check passed")
            else:
                logger.warning("❌ API health check failed")
                logger.info("Check logs with: docker compose logs api")
        except Exception as e:
            logger.warning(f"Could not perform health check: {e}")

    def setup(self):
        """Run the complete Docker setup"""
        logger.info("Starting SafeHorizon Docker setup...")
        logger.info(f"Environment: {self.environment}")
        logger.info(f"Sample data: {self.with_sample_data}")
        
        try:
            # 1. Check Docker installation
            self.check_docker()
            
            # 2. Create environment file
            self.create_env_file()
            
            # 3. Create Docker Compose override
            self.create_docker_compose_override()
            
            # 4. Create database init script
            self.create_init_script()
            
            # 5. Create production Dockerfile if needed
            self.create_production_dockerfile()
            
            # 6. Create sample data script
            self.create_sample_data_script()
            
            # 7. Build and start containers
            self.build_and_start_containers()
            
            # 8. Run migrations
            self.run_migrations()
            
            # 9. Create sample data
            self.create_sample_data_in_container()
            
            # 10. Validate deployment
            self.validate_deployment()
            
            logger.info("🎉 SafeHorizon Docker setup completed successfully!")
            self.print_next_steps()
            
        except Exception as e:
            logger.error(f"Docker setup failed: {e}")
            logger.info("Cleaning up...")
            try:
                self.run_command("docker compose down")
            except:
                pass
            raise

    def print_next_steps(self):
        """Print next steps for Docker deployment"""
        logger.info("\\n" + "="*50)
        logger.info("DOCKER SETUP COMPLETED - NEXT STEPS")
        logger.info("="*50)
        
        logger.info("\\n1. Access the application:")
        logger.info("   API Documentation: http://localhost:8000/docs")
        logger.info("   Health Check: http://localhost:8000/health")
        
        logger.info("\\n2. Manage containers:")
        if self.environment == 'production':
            logger.info("   docker compose -f docker-compose.yml -f docker-compose.production.yml logs")
            logger.info("   docker compose -f docker-compose.yml -f docker-compose.production.yml restart")
            logger.info("   docker compose -f docker-compose.yml -f docker-compose.production.yml down")
        else:
            logger.info("   docker compose -f docker-compose.yml -f docker-compose.development.yml logs")
            logger.info("   docker compose -f docker-compose.yml -f docker-compose.development.yml restart")
            logger.info("   docker compose -f docker-compose.yml -f docker-compose.development.yml down")
        
        if self.with_sample_data:
            logger.info("\\n3. Sample Login Credentials:")
            logger.info("   Tourist: john.doe@example.com / password123")
            logger.info("   Tourist: alice.smith@example.com / password123")
            logger.info("   Authority: officer.johnson@police.gov / police123")
            logger.info("   Authority: detective.brown@police.gov / police123")
        
        logger.info("\\n4. Database access:")
        logger.info("   docker compose exec db psql -U safehorizon_user -d safehorizon")
        
        logger.info("\\n5. Application logs:")
        logger.info("   docker compose logs -f api")
        
        logger.info("\\n6. For production deployment:")
        logger.info("   - Set up SSL certificates in ./ssl/ directory")
        logger.info("   - Configure domain name in nginx.prod.conf")
        logger.info("   - Set up external services (Firebase, Twilio)")
        logger.info("   - Configure monitoring and backup")


def main():
    parser = argparse.ArgumentParser(description='SafeHorizon Docker Setup')
    parser.add_argument('--environment', choices=['development', 'production'], 
                       default='production', help='Deployment environment')
    parser.add_argument('--with-sample-data', action='store_true', 
                       help='Create sample data for testing')
    
    args = parser.parse_args()
    
    setup = DockerSetup(
        environment=args.environment,
        with_sample_data=args.with_sample_data
    )
    
    setup.setup()


if __name__ == '__main__':
    main()