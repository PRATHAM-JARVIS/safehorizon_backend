#!/usr/bin/env python3
"""
SafeHorizon Database Setup Script for Ubuntu
===========================================

This script sets up only the database components for SafeHorizon on Ubuntu:
- Installs PostgreSQL with PostGIS
- Creates database and user
- Runs migrations to create schema
- Optionally inserts sample data

Usage:
    python setup_database.py
    python setup_database.py --with-sample-data
    python setup_database.py --db-name mycustomdb --db-user myuser
"""

import os
import sys
import subprocess
import asyncio
import logging
import argparse
import secrets
from pathlib import Path
from datetime import datetime, timezone

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseSetup:
    def __init__(self, db_name='safehorizon', db_user='safehorizon_user', with_sample_data=False):
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = secrets.token_urlsafe(24)
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
            if capture_output and e.stderr:
                logger.error(f"Stderr: {e.stderr}")
            raise

    def check_ubuntu(self):
        """Verify this is Ubuntu"""
        try:
            with open('/etc/os-release', 'r') as f:
                content = f.read().lower()
                if 'ubuntu' not in content:
                    logger.warning("This script is designed for Ubuntu. Proceeding anyway...")
                else:
                    logger.info("Ubuntu detected ✓")
        except FileNotFoundError:
            logger.warning("Could not detect OS. Proceeding anyway...")

    def install_postgresql(self):
        """Install PostgreSQL and PostGIS on Ubuntu"""
        logger.info("Installing PostgreSQL and PostGIS...")
        
        commands = [
            "sudo apt update",
            "sudo apt install -y wget ca-certificates",
            # Add PostgreSQL official APT repository for latest version
            "wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -",
            "echo 'deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main' | sudo tee /etc/apt/sources.list.d/pgdg.list",
            "sudo apt update",
            # Install PostgreSQL and PostGIS
            "sudo apt install -y postgresql-15 postgresql-client-15 postgresql-contrib-15",
            "sudo apt install -y postgresql-15-postgis-3 postgis",
            # Install development packages for Python
            "sudo apt install -y libpq-dev python3-dev build-essential",
            # Start and enable PostgreSQL
            "sudo systemctl start postgresql",
            "sudo systemctl enable postgresql"
        ]
        
        for cmd in commands:
            try:
                self.run_command(cmd)
            except subprocess.CalledProcessError as e:
                if "already installed" in str(e) or "already exists" in str(e):
                    logger.info(f"Skipping {cmd} - already installed")
                else:
                    logger.warning(f"Command failed (continuing): {cmd}")

    def setup_database_and_user(self):
        """Create database and user"""
        logger.info(f"Creating database '{self.db_name}' and user '{self.db_user}'...")
        
        # PostgreSQL commands to run as postgres user
        postgres_commands = [
            # Create user
            f"CREATE USER {self.db_user} WITH PASSWORD '{self.db_password}';",
            # Create database
            f"CREATE DATABASE {self.db_name} OWNER {self.db_user};",
            # Grant privileges
            f"GRANT ALL PRIVILEGES ON DATABASE {self.db_name} TO {self.db_user};",
            # Allow user to create databases (needed for tests)
            f"ALTER USER {self.db_user} CREATEDB;",
        ]
        
        for cmd in postgres_commands:
            try:
                self.run_command(f'sudo -u postgres psql -c "{cmd}"')
                logger.info(f"✓ Executed: {cmd}")
            except subprocess.CalledProcessError as e:
                if "already exists" in str(e):
                    logger.info(f"Skipping - already exists: {cmd}")
                else:
                    logger.warning(f"Failed: {cmd} - {e}")

    def setup_postgis_extensions(self):
        """Enable PostGIS extensions in the database"""
        logger.info("Setting up PostGIS extensions...")
        
        extensions = [
            "CREATE EXTENSION IF NOT EXISTS postgis;",
            "CREATE EXTENSION IF NOT EXISTS postgis_topology;",
            "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";",
        ]
        
        for ext in extensions:
            try:
                self.run_command(f'sudo -u postgres psql -d {self.db_name} -c "{ext}"')
                logger.info(f"✓ Enabled extension: {ext}")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to create extension: {ext} - {e}")

    def create_env_file(self):
        """Create .env file with database configuration"""
        logger.info("Creating .env file...")
        
        jwt_secret = secrets.token_urlsafe(64)
        
        env_content = f"""# SafeHorizon Database Configuration
# Generated on {datetime.now(timezone.utc).isoformat()}

# Application Settings
APP_NAME=SafeHorizon API
APP_ENV=development
APP_DEBUG=true
API_PREFIX=/api

# Database Configuration
DATABASE_URL=postgresql+asyncpg://{self.db_user}:{self.db_password}@localhost:5432/{self.db_name}
SYNC_DATABASE_URL=postgresql://{self.db_user}:{self.db_password}@localhost:5432/{self.db_name}

# Redis Configuration (optional - install separately if needed)
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET_KEY={jwt_secret}

# CORS Configuration
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173","http://localhost:8080","*"]

# Models Directory
MODELS_DIR=./models_store

# External Services (Optional - Configure as needed)
# FIREBASE_CREDENTIALS_JSON_PATH=./firebase-credentials.json
# TWILIO_ACCOUNT_SID=your_twilio_account_sid
# TWILIO_AUTH_TOKEN=your_twilio_auth_token
# TWILIO_FROM_NUMBER=your_twilio_phone_number
"""
        
        with open(self.env_file, 'w') as f:
            f.write(env_content)
        
        logger.info(f"✓ Environment file created: {self.env_file}")

    def install_python_dependencies(self):
        """Install Python dependencies needed for migrations"""
        logger.info("Installing Python dependencies...")
        
        # Install pip if not available
        try:
            self.run_command("python3 -m pip --version", capture_output=True)
        except subprocess.CalledProcessError:
            logger.info("Installing pip...")
            self.run_command("sudo apt install -y python3-pip")
        
        # Check if requirements.txt exists
        req_file = self.project_root / 'requirements.txt'
        if not req_file.exists():
            logger.error("requirements.txt not found. Please ensure you're in the SafeHorizon project directory.")
            return False
        
        # Install requirements
        try:
            self.run_command("python3 -m pip install -r requirements.txt --user")
            logger.info("✓ Python dependencies installed")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install Python dependencies: {e}")
            logger.info("You may need to install them manually:")
            logger.info("python3 -m pip install -r requirements.txt --user")
            return False

    def run_database_migrations(self):
        """Run Alembic database migrations"""
        logger.info("Running database migrations...")
        
        # Set environment variables for Alembic
        env = os.environ.copy()
        env.update({
            'DATABASE_URL': f"postgresql+asyncpg://{self.db_user}:{self.db_password}@localhost:5432/{self.db_name}",
            'SYNC_DATABASE_URL': f"postgresql://{self.db_user}:{self.db_password}@localhost:5432/{self.db_name}"
        })
        
        # Check if alembic directory exists
        alembic_dir = self.project_root / 'alembic'
        if not alembic_dir.exists():
            logger.error("Alembic directory not found. Database migrations cannot be run.")
            logger.info("You may need to initialize Alembic manually:")
            logger.info("python3 -m alembic init alembic")
            return False
        
        try:
            # Run migrations
            subprocess.run(['python3', '-m', 'alembic', 'upgrade', 'head'], 
                         env=env, check=True, cwd=self.project_root)
            logger.info("✓ Database migrations completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Migration failed: {e}")
            logger.info("You may need to run migrations manually:")
            logger.info("python3 -m alembic upgrade head")
            return False

    async def create_sample_data(self):
        """Create sample data for testing"""
        if not self.with_sample_data:
            return
            
        logger.info("Creating sample data...")
        
        try:
            # Import required modules
            from app.database import AsyncSessionLocal
            from app.models.database_models import Tourist, Authority, RestrictedZone, ZoneType
            from app.auth.local_auth import local_auth
            
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
                    ),
                    RestrictedZone(
                        name='Military Base Restricted',
                        description='Military installation - unauthorized entry prohibited',
                        zone_type=ZoneType.RESTRICTED,
                        center_latitude=40.7505,
                        center_longitude=-73.9934,
                        radius_meters=1000,
                        created_by='auth_001'
                    )
                ]
                
                for zone in sample_zones:
                    session.add(zone)
                
                await session.commit()
                logger.info("✓ Sample data created successfully!")
                
        except Exception as e:
            logger.error(f"Failed to create sample data: {e}")
            logger.info("You can create sample data later by running the application.")

    def test_database_connection(self):
        """Test database connection"""
        logger.info("Testing database connection...")
        
        try:
            import psycopg2
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password
            )
            
            # Test basic query
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            logger.info(f"✓ Database connection successful!")
            logger.info(f"PostgreSQL version: {version}")
            
            # Test PostGIS
            cursor.execute("SELECT PostGIS_version();")
            postgis_version = cursor.fetchone()[0]
            logger.info(f"✓ PostGIS version: {postgis_version}")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

    async def run_setup(self):
        """Run the complete database setup"""
        logger.info("Starting SafeHorizon Database Setup for Ubuntu...")
        logger.info(f"Database: {self.db_name}")
        logger.info(f"User: {self.db_user}")
        logger.info(f"Sample data: {self.with_sample_data}")
        
        try:
            # 1. Check Ubuntu
            self.check_ubuntu()
            
            # 2. Install PostgreSQL and PostGIS
            self.install_postgresql()
            
            # 3. Create database and user
            self.setup_database_and_user()
            
            # 4. Setup PostGIS extensions
            self.setup_postgis_extensions()
            
            # 5. Create .env file
            self.create_env_file()
            
            # 6. Install Python dependencies
            deps_ok = self.install_python_dependencies()
            
            # 7. Run migrations
            if deps_ok:
                migrations_ok = self.run_database_migrations()
            else:
                migrations_ok = False
            
            # 8. Test database connection
            connection_ok = self.test_database_connection()
            
            # 9. Create sample data
            if migrations_ok and connection_ok:
                await self.create_sample_data()
            
            if connection_ok:
                logger.info("🎉 Database setup completed successfully!")
                self.print_summary()
            else:
                logger.error("❌ Database setup completed with errors. Please check the logs above.")
                
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            raise

    def print_summary(self):
        """Print setup summary and next steps"""
        logger.info("\n" + "="*60)
        logger.info("DATABASE SETUP COMPLETED")
        logger.info("="*60)
        
        logger.info(f"\n📊 Database Information:")
        logger.info(f"   Host: localhost")
        logger.info(f"   Port: 5432")
        logger.info(f"   Database: {self.db_name}")
        logger.info(f"   Username: {self.db_user}")
        logger.info(f"   Password: {self.db_password}")
        
        logger.info(f"\n📁 Configuration:")
        logger.info(f"   Environment file: {self.env_file}")
        logger.info(f"   Database URL: postgresql://{self.db_user}:***@localhost:5432/{self.db_name}")
        
        if self.with_sample_data:
            logger.info(f"\n👤 Sample Login Credentials:")
            logger.info(f"   Tourist: john.doe@example.com / password123")
            logger.info(f"   Tourist: alice.smith@example.com / password123")
            logger.info(f"   Authority: officer.johnson@police.gov / police123")
            logger.info(f"   Authority: detective.brown@police.gov / police123")
        
        logger.info(f"\n🔌 Database Connection:")
        logger.info(f"   psql -h localhost -p 5432 -U {self.db_user} -d {self.db_name}")
        
        logger.info(f"\n🚀 Next Steps:")
        logger.info(f"   1. Install remaining dependencies if needed:")
        logger.info(f"      python3 -m pip install -r requirements.txt --user")
        logger.info(f"   2. Start your FastAPI application:")
        logger.info(f"      python3 -m uvicorn app.main:app --reload")
        logger.info(f"   3. Access API documentation:")
        logger.info(f"      http://localhost:8000/docs")
        
        logger.info(f"\n⚠️  Security Notes:")
        logger.info(f"   - Database password is auto-generated and stored in .env")
        logger.info(f"   - Change default sample passwords in production")
        logger.info(f"   - Consider setting up firewall rules for PostgreSQL")


def main():
    parser = argparse.ArgumentParser(description='SafeHorizon Database Setup for Ubuntu')
    parser.add_argument('--db-name', default='safehorizon', 
                       help='Database name (default: safehorizon)')
    parser.add_argument('--db-user', default='safehorizon_user',
                       help='Database user (default: safehorizon_user)')
    parser.add_argument('--with-sample-data', action='store_true',
                       help='Create sample data for testing')
    
    args = parser.parse_args()
    
    setup = DatabaseSetup(
        db_name=args.db_name,
        db_user=args.db_user,
        with_sample_data=args.with_sample_data
    )
    
    # Run the async setup
    asyncio.run(setup.run_setup())


if __name__ == '__main__':
    main()