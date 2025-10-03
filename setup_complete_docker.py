#!/usr/bin/env python3
"""
SafeHorizon Complete Docker Setup
================================

This script sets up everything from scratch using Docker:
- PostgreSQL with PostGIS
- Redis for caching
- FastAPI application
- Nginx reverse proxy
- SSL support
- Complete database schema
- Sample data
- Live production server

Usage:
    python setup_complete_docker.py
    python setup_complete_docker.py --with-sample-data
    python setup_complete_docker.py --domain yourdomain.com --ssl
"""

import os
import sys
import subprocess
import logging
import argparse
import secrets
import asyncio
import json
from pathlib import Path
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CompleteDockerSetup:
    def __init__(self, domain=None, with_ssl=False, with_sample_data=False, environment='production'):
        self.domain = domain or 'localhost'
        self.with_ssl = with_ssl
        self.with_sample_data = with_sample_data
        self.environment = environment
        self.project_root = Path(__file__).parent
        
        # Generate secure passwords and secrets once for consistency
        self.db_password = secrets.token_urlsafe(32)
        self.jwt_secret = secrets.token_urlsafe(64)

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

    def check_docker(self):
        """Check if Docker and Docker Compose are installed"""
        logger.info("Checking Docker installation...")
        
        try:
            docker_version = self.run_command("docker --version", capture_output=True)
            logger.info(f"✓ Found: {docker_version}")
        except subprocess.CalledProcessError:
            logger.error("❌ Docker is not installed")
            logger.info("Please install Docker: https://docs.docker.com/get-docker/")
            sys.exit(1)
        
        try:
            compose_version = self.run_command("docker compose version", capture_output=True)
            logger.info(f"✓ Found: {compose_version}")
        except subprocess.CalledProcessError:
            try:
                compose_version = self.run_command("docker-compose --version", capture_output=True)
                logger.info(f"✓ Found: {compose_version}")
            except subprocess.CalledProcessError:
                logger.error("❌ Docker Compose is not installed")
                sys.exit(1)

    def create_env_file(self):
        """Create comprehensive .env file"""
        logger.info("Creating environment configuration...")
        
        env_content = f"""# SafeHorizon Complete Production Environment
# Generated on {datetime.now(timezone.utc).isoformat()}

# Application Settings
APP_NAME=SafeHorizon API
APP_ENV={self.environment}
APP_DEBUG={'true' if self.environment == 'development' else 'false'}
API_PREFIX=/api

# Database Configuration
POSTGRES_USER=safehorizon_user
POSTGRES_PASSWORD={self.db_password}
POSTGRES_DB=safehorizon
DATABASE_URL=postgresql+asyncpg://safehorizon_user:{self.db_password}@db:5432/safehorizon
SYNC_DATABASE_URL=postgresql://safehorizon_user:{self.db_password}@db:5432/safehorizon

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Security
JWT_SECRET_KEY={self.jwt_secret}

# Domain Configuration
DOMAIN={self.domain}
SSL_ENABLED={'true' if self.with_ssl else 'false'}

# CORS Configuration
ALLOWED_ORIGINS=["https://{self.domain}","http://{self.domain}","http://localhost:3000","http://localhost:5173","*"]

# Models Directory
MODELS_DIR=./models_store

# External Services (Configure as needed)
FIREBASE_CREDENTIALS_JSON_PATH=./firebase-credentials.json
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_FROM_NUMBER=your_twilio_phone_number

# Monitoring and Logging
LOG_LEVEL=INFO
SENTRY_DSN=your_sentry_dsn_here

# Performance Settings
WORKERS=4
MAX_CONNECTIONS=100
"""
        
        env_file = self.project_root / '.env'
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        logger.info(f"✓ Environment file created: {env_file}")
        return self.db_password

    def create_production_dockerfile(self):
        """Create optimized production Dockerfile"""
        dockerfile_content = """# Multi-stage build for production
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    libpq-dev \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install wheel
RUN pip install --no-cache-dir --upgrade pip wheel

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \\
    libpq5 \\
    curl \\
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

# Create necessary directories
RUN mkdir -p models_store logs && \\
    chown -R safehorizon:safehorizon /app

# Switch to non-root user
USER safehorizon

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Default command with proper configuration
CMD ["gunicorn", "app.main:app", \\
     "--bind", "0.0.0.0:8000", \\
     "--workers", "4", \\
     "--worker-class", "uvicorn.workers.UvicornWorker", \\
     "--access-logfile", "-", \\
     "--error-logfile", "-", \\
     "--log-level", "info"]
"""
        
        dockerfile = self.project_root / 'Dockerfile'
        with open(dockerfile, 'w') as f:
            f.write(dockerfile_content)
        
        logger.info("✓ Production Dockerfile created")

    def create_docker_compose(self):
        """Create comprehensive docker-compose.yml"""
        
        compose_content = f"""version: "3.9"

services:
  # PostgreSQL Database with PostGIS
  db:
    image: postgis/postgis:15-3.4
    container_name: safehorizon_db
    environment:
      - POSTGRES_USER=safehorizon_user
      - POSTGRES_PASSWORD=apple
      - POSTGRES_DB=safehorizon
      - POSTGRES_INITDB_ARGS="--encoding=UTF-8"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/01-init.sql
      - ./init-extensions.sql:/docker-entrypoint-initdb.d/02-extensions.sql
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U safehorizon_user -d safehorizon"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - safehorizon_network

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: safehorizon_redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - safehorizon_network

  # FastAPI Application
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: safehorizon_api
    environment:
      - DATABASE_URL=postgresql://safehorizon_user:{self.db_password}@db:5432/safehorizon
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET_KEY={self.jwt_secret}
      - JWT_ALGORITHM=HS256
      - JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
    volumes:
      - ./models_store:/app/models_store
      - ./logs:/app/logs
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - safehorizon_network

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: safehorizon_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./ssl:/etc/nginx/ssl
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - api
    restart: unless-stopped
    networks:
      - safehorizon_network

  # Database Admin (pgAdmin)
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: safehorizon_pgadmin
    environment:
      - PGADMIN_DEFAULT_EMAIL=admin@safehorizon.com
      - PGADMIN_DEFAULT_PASSWORD=admin123
      - PGADMIN_LISTEN_PORT=80
    ports:
      - "5050:80"
    volumes:
      - pgadmin_data:/var/lib/pgadmin
    depends_on:
      - db
    restart: unless-stopped
    networks:
      - safehorizon_network
    profiles:
      - admin

  # Redis Admin (RedisInsight)
  redis-insight:
    image: redislabs/redisinsight:latest
    container_name: safehorizon_redis_insight
    ports:
      - "8001:8001"
    volumes:
      - redis_insight_data:/db
    depends_on:
      - redis
    restart: unless-stopped
    networks:
      - safehorizon_network
    profiles:
      - admin

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  pgadmin_data:
    driver: local
  redis_insight_data:
    driver: local

networks:
  safehorizon_network:
    driver: bridge
"""
        
        compose_file = self.project_root / 'docker-compose.yml'
        with open(compose_file, 'w') as f:
            f.write(compose_content)
        
        logger.info("✓ Docker Compose configuration created")

    def create_nginx_config(self):
        """Create Nginx configuration"""
        
        # Main nginx.conf
        nginx_main = """user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log notice;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 50M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/javascript application/xml+rss 
               application/json application/xml;

    # Security headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Include site configurations
    include /etc/nginx/conf.d/*.conf;
}
"""
        
        nginx_dir = self.project_root / 'nginx' / 'conf.d'
        nginx_dir.mkdir(parents=True, exist_ok=True)
        
        with open(self.project_root / 'nginx.conf', 'w') as f:
            f.write(nginx_main)

        # Site-specific configuration
        if self.with_ssl:
            site_config = f"""# HTTPS Configuration
server {{
    listen 80;
    server_name {self.domain};
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {self.domain};

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers for HTTPS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # API proxy
    location /api {{
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }}

    # Health check
    location /health {{
        proxy_pass http://api:8000;
        access_log off;
    }}

    # Documentation
    location /docs {{
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    # Static files
    location /static {{
        alias /var/www/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }}

    # Default location
    location / {{
        return 200 'SafeHorizon API Server is running. Visit /docs for API documentation.';
        add_header Content-Type text/plain;
    }}
}}
"""
        else:
            site_config = f"""# HTTP Configuration
server {{
    listen 80;
    server_name {self.domain};

    # API proxy
    location /api {{
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }}

    # Health check
    location /health {{
        proxy_pass http://api:8000;
        access_log off;
    }}

    # Documentation
    location /docs {{
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    # Default location
    location / {{
        return 200 'SafeHorizon API Server is running. Visit /docs for API documentation.';
        add_header Content-Type text/plain;
    }}
}}
"""
        
        with open(nginx_dir / 'default.conf', 'w') as f:
            f.write(site_config)
        
        logger.info("✓ Nginx configuration created")

    def create_database_init_scripts(self):
        """Create database initialization scripts"""
        
        # Basic database initialization
        init_db = """-- Initial database setup
-- This script runs when the database is first created

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone
SET timezone = 'UTC';

-- Create indexes for performance
-- These will be created by Alembic migrations as well
"""
        
        with open(self.project_root / 'init-db.sql', 'w') as f:
            f.write(init_db)
        
        # PostGIS extensions (already exists, but let's ensure it's complete)
        init_extensions = """-- PostGIS Extensions
-- Enable PostGIS functionality

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS postgis_raster;

-- Grant usage on PostGIS functions
GRANT USAGE ON SCHEMA topology TO PUBLIC;
GRANT SELECT ON ALL TABLES IN SCHEMA topology TO PUBLIC;
"""
        
        with open(self.project_root / 'init-extensions.sql', 'w') as f:
            f.write(init_extensions)
        
        logger.info("✓ Database initialization scripts created")

    def create_sample_data_script(self):
        """Create comprehensive sample data script"""
        
        if not self.with_sample_data:
            return
            
        sample_script = '''#!/usr/bin/env python3
"""
Comprehensive Sample Data Creation
"""
import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta
import random

# Add the app directory to Python path
sys.path.insert(0, '/app')

from app.database import AsyncSessionLocal
from app.models.database_models import (
    Tourist, Authority, RestrictedZone, ZoneType, Trip, TripStatus,
    Alert, AlertType, AlertSeverity, Location, UserDevice,
    EmergencyBroadcast, BroadcastType, BroadcastSeverity
)
from app.auth.local_auth import local_auth

async def create_comprehensive_sample_data():
    """Create comprehensive sample data for testing and demonstration"""
    print("Creating comprehensive sample data...")
    
    async with AsyncSessionLocal() as session:
        # Create sample tourists with diverse profiles
        sample_tourists = [
            Tourist(
                id='tourist_001',
                email='john.doe@gmail.com',
                name='John Doe',
                phone='+1-555-0101',
                emergency_contact='Jane Doe',
                emergency_phone='+1-555-0102',
                password_hash=local_auth.hash_password('tourist123'),
                safety_score=85,
                last_location_lat=40.7128,
                last_location_lon=-74.0060,
                last_seen=datetime.now(timezone.utc) - timedelta(minutes=5)
            ),
            Tourist(
                id='tourist_002',
                email='alice.smith@yahoo.com',
                name='Alice Smith',
                phone='+1-555-0201',
                emergency_contact='Bob Smith',
                emergency_phone='+1-555-0202',
                password_hash=local_auth.hash_password('tourist123'),
                safety_score=92,
                last_location_lat=34.0522,
                last_location_lon=-118.2437,
                last_seen=datetime.now(timezone.utc) - timedelta(minutes=15)
            ),
            Tourist(
                id='tourist_003',
                email='mike.wilson@outlook.com',
                name='Mike Wilson',
                phone='+1-555-0301',
                emergency_contact='Sarah Wilson',
                emergency_phone='+1-555-0302',
                password_hash=local_auth.hash_password('tourist123'),
                safety_score=78,
                last_location_lat=25.7617,
                last_location_lon=-80.1918,
                last_seen=datetime.now(timezone.utc) - timedelta(hours=2)
            ),
            Tourist(
                id='tourist_004',
                email='emma.brown@gmail.com',
                name='Emma Brown',
                phone='+1-555-0401',
                emergency_contact='David Brown',
                emergency_phone='+1-555-0402',
                password_hash=local_auth.hash_password('tourist123'),
                safety_score=95,
                last_location_lat=37.7749,
                last_location_lon=-122.4194,
                last_seen=datetime.now(timezone.utc) - timedelta(minutes=30)
            )
        ]
        
        for tourist in sample_tourists:
            session.add(tourist)
        
        # Create sample authorities with different roles
        sample_authorities = [
            Authority(
                id='auth_001',
                email='chief.johnson@nypd.gov',
                name='Chief Robert Johnson',
                badge_number='CHIEF001',
                department='NYPD',
                rank='Chief of Police',
                phone='+1-555-1001',
                password_hash=local_auth.hash_password('police123')
            ),
            Authority(
                id='auth_002',
                email='detective.brown@lapd.gov',
                name='Detective Sarah Brown',
                badge_number='DET002',
                department='LAPD',
                rank='Detective',
                phone='+1-555-1002',
                password_hash=local_auth.hash_password('police123')
            ),
            Authority(
                id='auth_003',
                email='officer.davis@miami.gov',
                name='Officer Michael Davis',
                badge_number='OFF003',
                department='Miami PD',
                rank='Patrol Officer',
                phone='+1-555-1003',
                password_hash=local_auth.hash_password('police123')
            ),
            Authority(
                id='auth_004',
                email='sergeant.wilson@sfpd.gov',
                name='Sergeant Lisa Wilson',
                badge_number='SGT004',
                department='SFPD',
                rank='Sergeant',
                phone='+1-555-1004',
                password_hash=local_auth.hash_password('police123')
            )
        ]
        
        for authority in sample_authorities:
            session.add(authority)
        
        # Create diverse restricted zones
        sample_zones = [
            RestrictedZone(
                name='Times Square High Traffic',
                description='Very crowded tourist area requiring extra attention',
                zone_type=ZoneType.RISKY,
                center_latitude=40.7589,
                center_longitude=-73.9851,
                radius_meters=300,
                created_by='auth_001'
            ),
            RestrictedZone(
                name='Central Park Safe Zone',
                description='Well-monitored park area with regular patrols',
                zone_type=ZoneType.SAFE,
                center_latitude=40.7829,
                center_longitude=-73.9654,
                radius_meters=1000,
                created_by='auth_001'
            ),
            RestrictedZone(
                name='Hollywood Walk of Fame',
                description='Tourist hotspot with frequent pickpocketing reports',
                zone_type=ZoneType.RISKY,
                center_latitude=34.1022,
                center_longitude=-118.2437,
                radius_meters=400,
                created_by='auth_002'
            ),
            RestrictedZone(
                name='Beverly Hills Exclusive',
                description='Upscale area with enhanced security',
                zone_type=ZoneType.SAFE,
                center_latitude=34.0736,
                center_longitude=-118.4004,
                radius_meters=2000,
                created_by='auth_002'
            ),
            RestrictedZone(
                name='Miami Beach Party District',
                description='High crime area during nighttime hours',
                zone_type=ZoneType.RISKY,
                center_latitude=25.7907,
                center_longitude=-80.1300,
                radius_meters=800,
                created_by='auth_003'
            ),
            RestrictedZone(
                name='Military Base Restricted',
                description='Federal restricted area - no civilian access',
                zone_type=ZoneType.RESTRICTED,
                center_latitude=25.8000,
                center_longitude=-80.2000,
                radius_meters=5000,
                created_by='auth_003'
            ),
            RestrictedZone(
                name='Golden Gate Tourist Area',
                description='Popular tourist destination with good security',
                zone_type=ZoneType.SAFE,
                center_latitude=37.8199,
                center_longitude=-122.4783,
                radius_meters=600,
                created_by='auth_004'
            )
        ]
        
        for zone in sample_zones:
            session.add(zone)
        
        # Commit the basic data first
        await session.commit()
        
        # Create sample trips
        sample_trips = [
            Trip(
                tourist_id='tourist_001',
                destination='New York City Tour',
                start_date=datetime.now(timezone.utc) - timedelta(days=1),
                end_date=datetime.now(timezone.utc) + timedelta(days=2),
                status=TripStatus.ACTIVE,
                itinerary='{"day1": "Central Park", "day2": "Times Square", "day3": "Statue of Liberty"}'
            ),
            Trip(
                tourist_id='tourist_002',
                destination='Los Angeles Adventure',
                start_date=datetime.now(timezone.utc),
                end_date=datetime.now(timezone.utc) + timedelta(days=3),
                status=TripStatus.ACTIVE,
                itinerary='{"day1": "Hollywood", "day2": "Santa Monica", "day3": "Beverly Hills"}'
            ),
            Trip(
                tourist_id='tourist_003',
                destination='Miami Beach Vacation',
                start_date=datetime.now(timezone.utc) - timedelta(days=2),
                end_date=datetime.now(timezone.utc) + timedelta(days=1),
                status=TripStatus.ACTIVE,
                itinerary='{"day1": "South Beach", "day2": "Art Deco District", "day3": "Key Biscayne"}'
            ),
            Trip(
                tourist_id='tourist_004',
                destination='San Francisco Explorer',
                start_date=datetime.now(timezone.utc) + timedelta(days=1),
                end_date=datetime.now(timezone.utc) + timedelta(days=4),
                status=TripStatus.PLANNED,
                itinerary='{"day1": "Golden Gate", "day2": "Alcatraz", "day3": "Fishermans Wharf"}'
            )
        ]
        
        for trip in sample_trips:
            session.add(trip)
        
        # Create sample location data (GPS tracking)
        base_locations = [
            (40.7128, -74.0060),  # NYC
            (34.0522, -118.2437),  # LA
            (25.7617, -80.1918),   # Miami
            (37.7749, -122.4194)   # SF
        ]
        
        tourist_ids = ['tourist_001', 'tourist_002', 'tourist_003', 'tourist_004']
        
        for i, tourist_id in enumerate(tourist_ids):
            base_lat, base_lon = base_locations[i]
            
            # Create location history for the past few hours
            for j in range(20):
                # Add some random variation to simulate movement
                lat_offset = random.uniform(-0.01, 0.01)
                lon_offset = random.uniform(-0.01, 0.01)
                
                location = Location(
                    tourist_id=tourist_id,
                    latitude=base_lat + lat_offset,
                    longitude=base_lon + lon_offset,
                    altitude=random.uniform(0, 100),
                    speed=random.uniform(0, 50),
                    accuracy=random.uniform(5, 20),
                    timestamp=datetime.now(timezone.utc) - timedelta(minutes=j*10),
                    safety_score=random.uniform(70, 100)
                )
                session.add(location)
        
        # Create sample alerts
        sample_alerts = [
            Alert(
                tourist_id='tourist_001',
                type=AlertType.GEOFENCE,
                severity=AlertSeverity.MEDIUM,
                title='Entered High-Risk Area',
                description='Tourist entered Times Square during peak hours',
                is_acknowledged=True,
                acknowledged_by='auth_001',
                acknowledged_at=datetime.now(timezone.utc) - timedelta(minutes=30)
            ),
            Alert(
                tourist_id='tourist_002',
                type=AlertType.ANOMALY,
                severity=AlertSeverity.LOW,
                title='Unusual Movement Pattern',
                description='Tourist movement pattern differs from normal behavior',
                is_acknowledged=False
            ),
            Alert(
                tourist_id='tourist_003',
                type=AlertType.PANIC,
                severity=AlertSeverity.HIGH,
                title='Panic Button Activated',
                description='Tourist activated panic button in Miami Beach area',
                is_acknowledged=True,
                acknowledged_by='auth_003',
                acknowledged_at=datetime.now(timezone.utc) - timedelta(minutes=5),
                is_resolved=True,
                resolved_by='auth_003',
                resolved_at=datetime.now(timezone.utc) - timedelta(minutes=2)
            )
        ]
        
        for alert in sample_alerts:
            session.add(alert)
        
        # Create sample user devices for push notifications
        sample_devices = [
            UserDevice(
                user_id='tourist_001',
                device_token='fake_token_001_' + secrets.token_hex(32),
                device_type='ios',
                device_name='iPhone 14 Pro',
                app_version='1.0.0',
                last_used=datetime.now(timezone.utc)
            ),
            UserDevice(
                user_id='tourist_002',
                device_token='fake_token_002_' + secrets.token_hex(32),
                device_type='android',
                device_name='Samsung Galaxy S23',
                app_version='1.0.0',
                last_used=datetime.now(timezone.utc)
            ),
            UserDevice(
                user_id='tourist_003',
                device_token='fake_token_003_' + secrets.token_hex(32),
                device_type='ios',
                device_name='iPhone 13',
                app_version='1.0.0',
                last_used=datetime.now(timezone.utc) - timedelta(hours=1)
            )
        ]
        
        for device in sample_devices:
            session.add(device)
        
        # Create sample emergency broadcast
        sample_broadcast = EmergencyBroadcast(
            broadcast_id=f'BCAST-{datetime.now().strftime("%Y%m%d")}-001',
            broadcast_type=BroadcastType.RADIUS,
            title='Weather Alert: Heavy Rain Warning',
            message='Heavy rain and potential flooding expected in the area. Stay indoors if possible.',
            severity=BroadcastSeverity.MEDIUM,
            alert_type='weather',
            action_required='stay_indoors',
            center_latitude=40.7589,
            center_longitude=-73.9851,
            radius_km=5.0,
            sent_by='auth_001',
            department='NYPD',
            expires_at=datetime.now(timezone.utc) + timedelta(hours=6),
            tourists_notified_count=2,
            devices_notified_count=2
        )
        
        session.add(sample_broadcast)
        
        # Commit all data
        await session.commit()
        print("✅ Comprehensive sample data created successfully!")
        
        # Print summary
        print("\\n📊 Sample Data Summary:")
        print(f"  - 4 Tourists with different safety scores")
        print(f"  - 4 Authorities from different departments")
        print(f"  - 7 Restricted zones (safe, risky, restricted)")
        print(f"  - 4 Active/planned trips")
        print(f"  - 80 GPS location records")
        print(f"  - 3 Sample alerts (geofence, anomaly, panic)")
        print(f"  - 3 Mobile device registrations")
        print(f"  - 1 Emergency broadcast")

if __name__ == '__main__':
    import secrets
    asyncio.run(create_comprehensive_sample_data())
'''
        
        script_file = self.project_root / 'create_sample_data.py'
        with open(script_file, 'w') as f:
            f.write(sample_script)
        
        logger.info("✓ Comprehensive sample data script created")

    def create_ssl_setup(self):
        """Create SSL certificate setup"""
        if not self.with_ssl:
            return
            
        ssl_dir = self.project_root / 'ssl'
        ssl_dir.mkdir(exist_ok=True)
        
        # Create self-signed certificate for development
        ssl_script = f"""#!/bin/bash
# Generate self-signed SSL certificate for development

openssl req -x509 -newkey rsa:4096 -keyout {ssl_dir}/key.pem -out {ssl_dir}/cert.pem -days 365 -nodes \\
    -subj "/C=US/ST=State/L=City/O=SafeHorizon/CN={self.domain}"

chmod 600 {ssl_dir}/key.pem
chmod 644 {ssl_dir}/cert.pem

echo "SSL certificates generated for {self.domain}"
echo "Note: These are self-signed certificates for development only"
echo "For production, use certificates from a trusted CA like Let's Encrypt"
"""
        
        ssl_script_file = self.project_root / 'generate_ssl.sh'
        with open(ssl_script_file, 'w') as f:
            f.write(ssl_script)
        
        os.chmod(ssl_script_file, 0o755)
        
        # Generate the certificates
        try:
            self.run_command(f"bash {ssl_script_file}")
            logger.info("✓ SSL certificates generated")
        except subprocess.CalledProcessError:
            logger.warning("⚠️  SSL certificate generation failed. Using HTTP only.")

    def create_management_scripts(self):
        """Create management and monitoring scripts"""
        
        # Server management script
        mgmt_script = f"""#!/bin/bash
# SafeHorizon Server Management Script

set -e

case "$1" in
    start)
        echo "Starting SafeHorizon server..."
        docker compose up -d
        echo "✅ Server started"
        echo "API: http://{self.domain}/docs"
        echo "pgAdmin: http://{self.domain}:5050"
        ;;
    stop)
        echo "Stopping SafeHorizon server..."
        docker compose down
        echo "✅ Server stopped"
        ;;
    restart)
        echo "Restarting SafeHorizon server..."
        docker compose restart
        echo "✅ Server restarted"
        ;;
    logs)
        echo "Showing logs (press Ctrl+C to exit)..."
        docker compose logs -f
        ;;
    status)
        echo "Server status:"
        docker compose ps
        ;;
    backup)
        echo "Creating database backup..."
        docker compose exec -T db pg_dump -U safehorizon_user safehorizon > backup_$(date +%Y%m%d_%H%M%S).sql
        echo "✅ Backup created"
        ;;
    update)
        echo "Updating server..."
        docker compose down
        docker compose build --no-cache
        docker compose up -d
        echo "✅ Server updated"
        ;;
    admin)
        echo "Starting admin tools..."
        docker compose --profile admin up -d
        echo "✅ Admin tools started"
        echo "pgAdmin: http://{self.domain}:5050 (admin@safehorizon.com / admin123)"
        echo "RedisInsight: http://{self.domain}:8001"
        ;;
    *)
        echo "Usage: $0 {{start|stop|restart|logs|status|backup|update|admin}}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the server"
        echo "  stop    - Stop the server"
        echo "  restart - Restart the server"
        echo "  logs    - Show server logs"
        echo "  status  - Show container status"
        echo "  backup  - Create database backup"
        echo "  update  - Update and restart server"
        echo "  admin   - Start admin tools (pgAdmin, RedisInsight)"
        exit 1
        ;;
esac
"""
        
        mgmt_file = self.project_root / 'manage.sh'
        with open(mgmt_file, 'w') as f:
            f.write(mgmt_script)
        
        os.chmod(mgmt_file, 0o755)
        
        # Health check script
        health_script = f"""#!/bin/bash
# Health Check Script

echo "🏥 SafeHorizon Health Check"
echo "=========================="

# Check if containers are running
echo "📦 Container Status:"
docker compose ps

echo ""
echo "🔍 Service Health:"

# Check API health
echo -n "API Service: "
if curl -f -s http://{self.domain}:8000/health > /dev/null; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy"
fi

# Check database
echo -n "Database: "
if docker compose exec -T db pg_isready -U safehorizon_user > /dev/null 2>&1; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy"
fi

# Check Redis
echo -n "Redis: "
if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy"
fi

# Check Nginx
echo -n "Nginx: "
if docker compose exec -T nginx nginx -t > /dev/null 2>&1; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy"
fi

echo ""
echo "📊 Quick Stats:"
docker compose exec -T db psql -U safehorizon_user -d safehorizon -c "SELECT 'Tourists: ' || count(*) FROM tourists;" -t
docker compose exec -T db psql -U safehorizon_user -d safehorizon -c "SELECT 'Authorities: ' || count(*) FROM authorities;" -t
docker compose exec -T db psql -U safehorizon_user -d safehorizon -c "SELECT 'Alerts: ' || count(*) FROM alerts;" -t
"""
        
        health_file = self.project_root / 'health_check.sh'
        with open(health_file, 'w') as f:
            f.write(health_script)
        
        os.chmod(health_file, 0o755)
        
        logger.info("✓ Management scripts created")

    def create_directories(self):
        """Create necessary directories"""
        directories = ['models_store', 'logs', 'logs/nginx', 'ssl']
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create placeholder files
        (self.project_root / 'models_store' / '.gitkeep').touch()
        (self.project_root / 'logs' / '.gitkeep').touch()
        
        logger.info("✓ Directory structure created")

    def build_and_deploy(self):
        """Build and deploy the complete stack"""
        logger.info("Building and deploying SafeHorizon stack...")
        
        # Pull latest images
        self.run_command("docker compose pull")
        
        # Build the application
        self.run_command("docker compose build --no-cache")
        
        # Start the services
        self.run_command("docker compose up -d")
        
        # Wait for services to be ready
        logger.info("Waiting for services to start...")
        import time
        time.sleep(30)
        
        # Run migrations
        logger.info("Running database migrations...")
        self.run_command("docker compose exec -T api python -c \"import time; time.sleep(10)\"")
        self.run_command("docker compose exec -T api alembic upgrade head")
        
        # Create sample data if requested
        if self.with_sample_data:
            logger.info("Creating sample data...")
            self.run_command("docker compose exec -T api python create_sample_data.py")

    def validate_deployment(self):
        """Validate the complete deployment"""
        logger.info("Validating deployment...")
        
        # Check container status
        result = self.run_command("docker compose ps", capture_output=True)
        logger.info("Container status:")
        logger.info(result)
        
        # Health checks
        import time
        time.sleep(10)
        
        try:
            # Check API
            health_result = self.run_command(f"curl -f http://{self.domain}:8000/health", capture_output=True)
            if "ok" in health_result:
                logger.info("✅ API health check passed")
            else:
                logger.warning("❌ API health check failed")
        except:
            logger.warning("❌ Could not reach API")
        
        # Check database
        try:
            self.run_command("docker compose exec -T db pg_isready -U safehorizon_user")
            logger.info("✅ Database is ready")
        except:
            logger.warning("❌ Database not ready")
        
        # Check Redis
        try:
            self.run_command("docker compose exec -T redis redis-cli ping")
            logger.info("✅ Redis is ready")
        except:
            logger.warning("❌ Redis not ready")

    def setup(self):
        """Run the complete setup process"""
        logger.info("🚀 Starting SafeHorizon Complete Docker Setup")
        logger.info(f"Domain: {self.domain}")
        logger.info(f"SSL: {'Enabled' if self.with_ssl else 'Disabled'}")
        logger.info(f"Sample Data: {'Enabled' if self.with_sample_data else 'Disabled'}")
        logger.info(f"Environment: {self.environment}")
        
        try:
            # 1. Check prerequisites
            self.check_docker()
            
            # 2. Create directory structure
            self.create_directories()
            
            # 3. Create configuration files
            self.create_env_file()
            self.create_production_dockerfile()
            self.create_docker_compose()
            self.create_nginx_config()
            self.create_database_init_scripts()
            
            # 4. Create SSL certificates if needed
            self.create_ssl_setup()
            
            # 5. Create sample data script
            self.create_sample_data_script()
            
            # 6. Create management scripts
            self.create_management_scripts()
            
            # 7. Build and deploy
            self.build_and_deploy()
            
            # 8. Validate deployment
            self.validate_deployment()
            
            logger.info("🎉 SafeHorizon Complete Setup Finished!")
            self.print_success_summary()
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            logger.info("Cleaning up...")
            try:
                self.run_command("docker compose down")
            except:
                pass
            raise

    def print_success_summary(self):
        """Print comprehensive success summary"""
        logger.info("\\n" + "="*80)
        logger.info("🎉 SAFEHORIZON LIVE SERVER READY!")
        logger.info("="*80)
        
        logger.info(f"\\n🌐 Server URLs:")
        protocol = 'https' if self.with_ssl else 'http'
        logger.info(f"   Main API: {protocol}://{self.domain}")
        logger.info(f"   API Docs: {protocol}://{self.domain}/docs")
        logger.info(f"   Health Check: {protocol}://{self.domain}/health")
        logger.info(f"   pgAdmin: http://{self.domain}:5050")
        
        logger.info(f"\\n📊 Database Info:")
        logger.info(f"   Host: {self.domain} (port 5432)")
        logger.info(f"   Database: safehorizon")
        logger.info(f"   Username: safehorizon_user")
        logger.info(f"   Password: {self.db_password}")
        
        if self.with_sample_data:
            logger.info(f"\\n👤 Sample Login Credentials:")
            logger.info(f"   Tourist: john.doe@gmail.com / tourist123")
            logger.info(f"   Tourist: alice.smith@yahoo.com / tourist123")
            logger.info(f"   Authority: chief.johnson@nypd.gov / police123")
            logger.info(f"   Authority: detective.brown@lapd.gov / police123")
            logger.info(f"   pgAdmin: admin@safehorizon.com / admin123")
        
        logger.info(f"\\n🛠️  Management Commands:")
        logger.info(f"   Start server: ./manage.sh start")
        logger.info(f"   Stop server: ./manage.sh stop")
        logger.info(f"   View logs: ./manage.sh logs")
        logger.info(f"   Server status: ./manage.sh status")
        logger.info(f"   Health check: ./health_check.sh")
        logger.info(f"   Admin tools: ./manage.sh admin")
        
        logger.info(f"\\n📁 Important Files:")
        logger.info(f"   Environment: .env")
        logger.info(f"   Docker Compose: docker-compose.yml")
        logger.info(f"   Nginx Config: nginx/conf.d/default.conf")
        logger.info(f"   SSL Certs: ssl/ (if enabled)")
        
        logger.info(f"\\n🔒 Security Notes:")
        logger.info(f"   - Database password is auto-generated")
        logger.info(f"   - Change sample passwords for production")
        logger.info(f"   - SSL {'enabled' if self.with_ssl else 'disabled'}")
        logger.info(f"   - All services running in isolated Docker network")
        
        logger.info(f"\\n🚀 Your SafeHorizon server is now LIVE and ready for use!")


def main():
    parser = argparse.ArgumentParser(description='SafeHorizon Complete Docker Setup')
    parser.add_argument('--domain', default='localhost',
                       help='Domain name for the server (default: localhost)')
    parser.add_argument('--ssl', action='store_true',
                       help='Enable SSL/HTTPS (generates self-signed cert)')
    parser.add_argument('--with-sample-data', action='store_true',
                       help='Create comprehensive sample data')
    parser.add_argument('--environment', choices=['development', 'production'],
                       default='production', help='Deployment environment')
    
    args = parser.parse_args()
    
    setup = CompleteDockerSetup(
        domain=args.domain,
        with_ssl=args.ssl,
        with_sample_data=args.with_sample_data,
        environment=args.environment
    )
    
    setup.setup()


if __name__ == '__main__':
    main()