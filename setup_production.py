#!/usr/bin/env python3
"""
SafeHorizon Production Setup Script
==================================

This script sets up everything from scratch for SafeHorizon deployment:
- Installs system dependencies (PostgreSQL, Redis, Python packages)
- Creates database and schema
- Runs migrations
- Inserts sample data
- Sets up environment configuration
- Validates the installation

Usage:
    python setup_production.py --environment production
    python setup_production.py --environment development --with-sample-data
"""

import os
import sys
import subprocess
import json
import asyncio
import logging
import argparse
import secrets
from pathlib import Path
from datetime import datetime, timezone
import hashlib

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SafeHorizonSetup:
    def __init__(self, environment='production', with_sample_data=False):
        self.environment = environment
        self.with_sample_data = with_sample_data
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / '.env'
        
        # Database configuration
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'safehorizon',
            'username': 'safehorizon_user',
            'password': self.generate_password()
        }
        
        # Redis configuration
        self.redis_config = {
            'host': 'localhost',
            'port': 6379,
            'database': 0
        }

    def generate_password(self):
        """Generate a secure random password"""
        return secrets.token_urlsafe(32)

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
            if capture_output and e.stdout:
                logger.error(f"Stdout: {e.stdout}")
            if capture_output and e.stderr:
                logger.error(f"Stderr: {e.stderr}")
            raise

    def detect_os(self):
        """Detect the operating system"""
        import platform
        system = platform.system().lower()
        if system == 'linux':
            # Try to detect Linux distribution
            try:
                with open('/etc/os-release', 'r') as f:
                    content = f.read()
                    if 'ubuntu' in content.lower():
                        return 'ubuntu'
                    elif 'centos' in content.lower() or 'rhel' in content.lower():
                        return 'centos'
                    elif 'debian' in content.lower():
                        return 'debian'
                    else:
                        return 'linux'
            except:
                return 'linux'
        elif system == 'darwin':
            return 'macos'
        elif system == 'windows':
            return 'windows'
        else:
            return 'unknown'

    def install_system_dependencies(self):
        """Install system-level dependencies based on OS"""
        logger.info("Installing system dependencies...")
        
        os_type = self.detect_os()
        logger.info(f"Detected OS: {os_type}")

        if os_type in ['ubuntu', 'debian']:
            self.install_ubuntu_dependencies()
        elif os_type == 'centos':
            self.install_centos_dependencies()
        elif os_type == 'macos':
            self.install_macos_dependencies()
        elif os_type == 'windows':
            logger.warning("Windows detected. Please install PostgreSQL and Redis manually.")
            logger.info("PostgreSQL: https://www.postgresql.org/download/windows/")
            logger.info("Redis: https://github.com/microsoftarchive/redis/releases")
            return
        else:
            logger.warning(f"Unsupported OS: {os_type}. Please install dependencies manually.")
            return

    def install_ubuntu_dependencies(self):
        """Install dependencies on Ubuntu/Debian"""
        commands = [
            "sudo apt update",
            "sudo apt install -y postgresql postgresql-contrib postgresql-client",
            "sudo apt install -y postgis postgresql-14-postgis-3",
            "sudo apt install -y redis-server",
            "sudo apt install -y python3-pip python3-venv python3-dev",
            "sudo apt install -y build-essential libpq-dev",
            "sudo systemctl start postgresql",
            "sudo systemctl enable postgresql",
            "sudo systemctl start redis-server",
            "sudo systemctl enable redis-server"
        ]
        
        for cmd in commands:
            try:
                self.run_command(cmd)
            except subprocess.CalledProcessError as e:
                logger.warning(f"Command failed (continuing): {cmd}")

    def install_centos_dependencies(self):
        """Install dependencies on CentOS/RHEL"""
        commands = [
            "sudo yum update -y",
            "sudo yum install -y postgresql postgresql-server postgresql-contrib",
            "sudo yum install -y postgis postgresql-devel",
            "sudo yum install -y redis",
            "sudo yum install -y python3-pip python3-devel",
            "sudo yum groupinstall -y 'Development Tools'",
            "sudo postgresql-setup initdb",
            "sudo systemctl start postgresql",
            "sudo systemctl enable postgresql",
            "sudo systemctl start redis",
            "sudo systemctl enable redis"
        ]
        
        for cmd in commands:
            try:
                self.run_command(cmd)
            except subprocess.CalledProcessError as e:
                logger.warning(f"Command failed (continuing): {cmd}")

    def install_macos_dependencies(self):
        """Install dependencies on macOS using Homebrew"""
        # Check if Homebrew is installed
        try:
            self.run_command("which brew", capture_output=True)
        except subprocess.CalledProcessError:
            logger.info("Installing Homebrew...")
            self.run_command('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')

        commands = [
            "brew update",
            "brew install postgresql@14",
            "brew install postgis",
            "brew install redis",
            "brew services start postgresql@14",
            "brew services start redis"
        ]
        
        for cmd in commands:
            try:
                self.run_command(cmd)
            except subprocess.CalledProcessError as e:
                logger.warning(f"Command failed (continuing): {cmd}")

    def setup_postgresql(self):
        """Set up PostgreSQL database and user"""
        logger.info("Setting up PostgreSQL database...")
        
        # Create database user and database
        postgres_commands = [
            f"CREATE USER {self.db_config['username']} WITH PASSWORD '{self.db_config['password']}';",
            f"CREATE DATABASE {self.db_config['database']} OWNER {self.db_config['username']};",
            f"GRANT ALL PRIVILEGES ON DATABASE {self.db_config['database']} TO {self.db_config['username']};",
            f"ALTER USER {self.db_config['username']} CREATEDB;"
        ]
        
        for cmd in postgres_commands:
            try:
                self.run_command(f'sudo -u postgres psql -c "{cmd}"')
            except subprocess.CalledProcessError as e:
                logger.warning(f"PostgreSQL command failed (might already exist): {cmd}")

        # Enable PostGIS extension
        try:
            self.run_command(f'sudo -u postgres psql -d {self.db_config["database"]} -c "CREATE EXTENSION IF NOT EXISTS postgis;"')
            self.run_command(f'sudo -u postgres psql -d {self.db_config["database"]} -c "CREATE EXTENSION IF NOT EXISTS postgis_topology;"')
        except subprocess.CalledProcessError as e:
            logger.warning("PostGIS extension setup failed (might not be available)")

    def create_env_file(self):
        """Create .env file with configuration"""
        logger.info("Creating environment configuration...")
        
        jwt_secret = secrets.token_urlsafe(64)
        
        env_content = f"""# SafeHorizon Environment Configuration
# Generated on {datetime.now(timezone.utc).isoformat()}

# Application Settings
APP_NAME=SafeHorizon API
APP_ENV={self.environment}
APP_DEBUG={'true' if self.environment == 'development' else 'false'}
API_PREFIX=/api

# Database Configuration
DATABASE_URL=postgresql+asyncpg://{self.db_config['username']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}
SYNC_DATABASE_URL=postgresql://{self.db_config['username']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}

# Redis Configuration
REDIS_URL=redis://{self.redis_config['host']}:{self.redis_config['port']}/{self.redis_config['database']}

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

    def install_python_dependencies(self):
        """Install Python dependencies"""
        logger.info("Installing Python dependencies...")
        
        # Create virtual environment if it doesn't exist
        venv_path = self.project_root / 'venv'
        if not venv_path.exists():
            self.run_command(f"python3 -m venv {venv_path}")
        
        # Install requirements
        pip_path = venv_path / 'bin' / 'pip' if os.name != 'nt' else venv_path / 'Scripts' / 'pip.exe'
        self.run_command(f"{pip_path} install --upgrade pip")
        self.run_command(f"{pip_path} install -r requirements.txt")

    def run_database_migrations(self):
        """Run Alembic database migrations"""
        logger.info("Running database migrations...")
        
        # Set environment variables for Alembic
        env = os.environ.copy()
        env.update({
            'DATABASE_URL': f"postgresql+asyncpg://{self.db_config['username']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}",
            'SYNC_DATABASE_URL': f"postgresql://{self.db_config['username']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
        })
        
        # Run migrations
        venv_python = self.project_root / 'venv' / 'bin' / 'python' if os.name != 'nt' else self.project_root / 'venv' / 'Scripts' / 'python.exe'
        
        try:
            subprocess.run([str(venv_python), '-m', 'alembic', 'upgrade', 'head'], 
                         env=env, check=True, cwd=self.project_root)
        except subprocess.CalledProcessError as e:
            logger.error("Migration failed. Trying to initialize Alembic...")
            try:
                subprocess.run([str(venv_python), '-m', 'alembic', 'init', 'alembic'], 
                             env=env, check=True, cwd=self.project_root)
                subprocess.run([str(venv_python), '-m', 'alembic', 'upgrade', 'head'], 
                             env=env, check=True, cwd=self.project_root)
            except subprocess.CalledProcessError:
                logger.error("Could not run migrations. Database tables may need to be created manually.")

    async def create_sample_data(self):
        """Create sample data for testing"""
        if not self.with_sample_data:
            return
            
        logger.info("Creating sample data...")
        
        # Import required modules
        sys.path.insert(0, str(self.project_root))
        
        try:
            from app.database import AsyncSessionLocal
            from app.models.database_models import Tourist, Authority, RestrictedZone, ZoneType
            from app.auth.local_auth import local_auth
            import asyncio
            
            async with AsyncSessionLocal() as session:
                # Create sample tourists
                sample_tourists = [
                    {
                        'id': 'tourist_001',
                        'email': 'john.doe@example.com',
                        'name': 'John Doe',
                        'phone': '+1234567890',
                        'emergency_contact': 'Jane Doe',
                        'emergency_phone': '+1234567891',
                        'password_hash': local_auth.hash_password('password123'),
                        'safety_score': 85,
                        'last_location_lat': 40.7128,
                        'last_location_lon': -74.0060
                    },
                    {
                        'id': 'tourist_002',
                        'email': 'alice.smith@example.com',
                        'name': 'Alice Smith',
                        'phone': '+1234567892',
                        'emergency_contact': 'Bob Smith',
                        'emergency_phone': '+1234567893',
                        'password_hash': local_auth.hash_password('password123'),
                        'safety_score': 92,
                        'last_location_lat': 34.0522,
                        'last_location_lon': -118.2437
                    }
                ]
                
                for tourist_data in sample_tourists:
                    tourist = Tourist(**tourist_data)
                    session.add(tourist)
                
                # Create sample authorities
                sample_authorities = [
                    {
                        'id': 'auth_001',
                        'email': 'officer.johnson@police.gov',
                        'name': 'Officer Johnson',
                        'badge_number': 'BADGE001',
                        'department': 'NYPD',
                        'rank': 'Sergeant',
                        'phone': '+1234567894',
                        'password_hash': local_auth.hash_password('police123')
                    },
                    {
                        'id': 'auth_002',
                        'email': 'detective.brown@police.gov',
                        'name': 'Detective Brown',
                        'badge_number': 'BADGE002',
                        'department': 'LAPD',
                        'rank': 'Detective',
                        'phone': '+1234567895',
                        'password_hash': local_auth.hash_password('police123')
                    }
                ]
                
                for auth_data in sample_authorities:
                    authority = Authority(**auth_data)
                    session.add(authority)
                
                # Create sample restricted zones
                sample_zones = [
                    {
                        'name': 'High Crime Area Downtown',
                        'description': 'Area with increased criminal activity',
                        'zone_type': ZoneType.RISKY,
                        'center_latitude': 40.7589,
                        'center_longitude': -73.9851,
                        'radius_meters': 500,
                        'created_by': 'auth_001'
                    },
                    {
                        'name': 'Military Base Restricted',
                        'description': 'Military installation - unauthorized entry prohibited',
                        'zone_type': ZoneType.RESTRICTED,
                        'center_latitude': 40.7505,
                        'center_longitude': -73.9934,
                        'radius_meters': 1000,
                        'created_by': 'auth_001'
                    },
                    {
                        'name': 'Tourist Safe Zone',
                        'description': 'Well-monitored tourist area',
                        'zone_type': ZoneType.SAFE,
                        'center_latitude': 40.7614,
                        'center_longitude': -73.9776,
                        'radius_meters': 750,
                        'created_by': 'auth_002'
                    }
                ]
                
                for zone_data in sample_zones:
                    zone = RestrictedZone(**zone_data)
                    session.add(zone)
                
                await session.commit()
                logger.info("Sample data created successfully!")
                
        except Exception as e:
            logger.error(f"Failed to create sample data: {e}")

    def create_models_directory(self):
        """Create models directory for ML models"""
        models_dir = self.project_root / 'models_store'
        models_dir.mkdir(exist_ok=True)
        
        # Create a placeholder file
        placeholder = models_dir / '.gitkeep'
        placeholder.touch()
        
        logger.info(f"Models directory created: {models_dir}")

    def create_systemd_service(self):
        """Create systemd service file for production deployment"""
        if self.environment != 'production':
            return
            
        logger.info("Creating systemd service file...")
        
        service_content = f"""[Unit]
Description=SafeHorizon API Server
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=exec
User=safehorizon
Group=safehorizon
WorkingDirectory={self.project_root}
Environment=PATH={self.project_root}/venv/bin
EnvironmentFile={self.project_root}/.env
ExecStart={self.project_root}/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""
        
        service_file = Path('/tmp/safehorizon.service')
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        logger.info(f"Systemd service file created at: {service_file}")
        logger.info("To install the service, run:")
        logger.info(f"sudo cp {service_file} /etc/systemd/system/")
        logger.info("sudo systemctl daemon-reload")
        logger.info("sudo systemctl enable safehorizon")
        logger.info("sudo systemctl start safehorizon")

    def create_nginx_config(self):
        """Create Nginx configuration for reverse proxy"""
        if self.environment != 'production':
            return
            
        logger.info("Creating Nginx configuration...")
        
        nginx_content = """server {
    listen 80;
    server_name your-domain.com;  # Replace with your actual domain
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;  # Replace with your actual domain
    
    # SSL Configuration (you'll need to set up SSL certificates)
    # ssl_certificate /path/to/your/certificate.crt;
    # ssl_certificate_key /path/to/your/private.key;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # API proxy
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
    
    # Static files (if any)
    location /static {
        alias /path/to/static/files;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
"""
        
        nginx_file = Path('/tmp/safehorizon-nginx.conf')
        with open(nginx_file, 'w') as f:
            f.write(nginx_content)
        
        logger.info(f"Nginx configuration created at: {nginx_file}")
        logger.info("To install the configuration:")
        logger.info(f"sudo cp {nginx_file} /etc/nginx/sites-available/safehorizon")
        logger.info("sudo ln -s /etc/nginx/sites-available/safehorizon /etc/nginx/sites-enabled/")
        logger.info("sudo nginx -t")
        logger.info("sudo systemctl reload nginx")

    def validate_installation(self):
        """Validate that everything is set up correctly"""
        logger.info("Validating installation...")
        
        # Check if .env file exists
        if not self.env_file.exists():
            logger.error(".env file not found!")
            return False
        
        # Check if virtual environment exists
        venv_path = self.project_root / 'venv'
        if not venv_path.exists():
            logger.error("Virtual environment not found!")
            return False
        
        # Check if models directory exists
        models_dir = self.project_root / 'models_store'
        if not models_dir.exists():
            logger.error("Models directory not found!")
            return False
        
        # Test database connection
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['username'],
                password=self.db_config['password']
            )
            conn.close()
            logger.info("✅ Database connection successful")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
        
        # Test Redis connection
        try:
            import redis
            r = redis.Redis(
                host=self.redis_config['host'],
                port=self.redis_config['port'],
                db=self.redis_config['database']
            )
            r.ping()
            logger.info("✅ Redis connection successful")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            return False
        
        logger.info("✅ Installation validation completed successfully!")
        return True

    async def run_setup(self):
        """Run the complete setup process"""
        logger.info("Starting SafeHorizon production setup...")
        logger.info(f"Environment: {self.environment}")
        logger.info(f"Sample data: {self.with_sample_data}")
        
        try:
            # 1. Install system dependencies
            self.install_system_dependencies()
            
            # 2. Set up PostgreSQL
            self.setup_postgresql()
            
            # 3. Create environment file
            self.create_env_file()
            
            # 4. Install Python dependencies
            self.install_python_dependencies()
            
            # 5. Create models directory
            self.create_models_directory()
            
            # 6. Run database migrations
            self.run_database_migrations()
            
            # 7. Create sample data (if requested)
            await self.create_sample_data()
            
            # 8. Create production files
            if self.environment == 'production':
                self.create_systemd_service()
                self.create_nginx_config()
            
            # 9. Validate installation
            if self.validate_installation():
                logger.info("🎉 SafeHorizon setup completed successfully!")
                self.print_next_steps()
            else:
                logger.error("❌ Setup validation failed. Please check the logs above.")
                
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            raise

    def print_next_steps(self):
        """Print next steps for the user"""
        logger.info("\n" + "="*50)
        logger.info("SETUP COMPLETED - NEXT STEPS")
        logger.info("="*50)
        
        logger.info("\n1. Database Configuration:")
        logger.info(f"   Database: {self.db_config['database']}")
        logger.info(f"   Username: {self.db_config['username']}")
        logger.info(f"   Password: {self.db_config['password']}")
        
        logger.info("\n2. Start the application:")
        if self.environment == 'development':
            logger.info("   # Development mode")
            logger.info("   source venv/bin/activate")
            logger.info("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        else:
            logger.info("   # Production mode")
            logger.info("   sudo systemctl start safehorizon")
            logger.info("   sudo systemctl status safehorizon")
        
        logger.info("\n3. Access the API:")
        logger.info("   API Documentation: http://your-server:8000/docs")
        logger.info("   Health Check: http://your-server:8000/health")
        
        if self.with_sample_data:
            logger.info("\n4. Sample Login Credentials:")
            logger.info("   Tourist: john.doe@example.com / password123")
            logger.info("   Tourist: alice.smith@example.com / password123")
            logger.info("   Authority: officer.johnson@police.gov / police123")
            logger.info("   Authority: detective.brown@police.gov / police123")
        
        logger.info("\n5. Configuration Files:")
        logger.info(f"   Environment: {self.env_file}")
        if self.environment == 'production':
            logger.info("   Systemd Service: /tmp/safehorizon.service")
            logger.info("   Nginx Config: /tmp/safehorizon-nginx.conf")
        
        logger.info("\n6. Important Security Notes:")
        logger.info("   - Change default passwords immediately")
        logger.info("   - Set up SSL certificates for production")
        logger.info("   - Configure firewall rules")
        logger.info("   - Set up backup procedures")
        logger.info("   - Configure monitoring and logging")


def main():
    parser = argparse.ArgumentParser(description='SafeHorizon Production Setup')
    parser.add_argument('--environment', choices=['development', 'production'], 
                       default='production', help='Deployment environment')
    parser.add_argument('--with-sample-data', action='store_true', 
                       help='Create sample data for testing')
    parser.add_argument('--skip-system-deps', action='store_true',
                       help='Skip system dependency installation')
    
    args = parser.parse_args()
    
    setup = SafeHorizonSetup(
        environment=args.environment,
        with_sample_data=args.with_sample_data
    )
    
    # Run the async setup
    asyncio.run(setup.run_setup())


if __name__ == '__main__':
    main()