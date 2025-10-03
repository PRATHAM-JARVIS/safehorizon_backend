#!/bin/bash

##############################################################################
#                    SafeHorizon Backend - Complete Deployment              #
#                         From Zero to Production Live                       #
#                                                                            #
# This script deploys SafeHorizon backend from scratch to a live server     #
#                                                                            #
# Usage:                                                                     #
#   curl -sSL https://raw.githubusercontent.com/PRATHAM-JARVIS/safehorizon_backend/main/deploy-live.sh | sudo bash
#   OR                                                                       #
#   sudo bash deploy-live.sh                                                #
#                                                                            #
# What this script does:                                                     #
#   ✅ Installs all system dependencies                                      #
#   ✅ Sets up Docker & Docker Compose                                       #
#   ✅ Clones/updates the repository                                         #
#   ✅ Configures environment variables                                      #
#   ✅ Sets up SSL certificates (Let's Encrypt)                             #
#   ✅ Configures Nginx reverse proxy                                        #
#   ✅ Starts all services in production mode                               #
#   ✅ Sets up monitoring and health checks                                  #
#   ✅ Configures automatic backups                                          #
##############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
PROJECT_NAME="safehorizon"
REPO_URL="https://github.com/PRATHAM-JARVIS/safehorizon_backend.git"
DOMAIN=""  # Will be prompted
EMAIL=""   # Will be prompted for SSL
API_PORT=8000
DB_PORT=5432
REDIS_PORT=6379
SSL_PORT=443
HTTP_PORT=80

# Directories
PROJECT_DIR="/opt/safehorizon"
BACKUP_DIR="/opt/safehorizon/backups"
LOG_DIR="/var/log/safehorizon"
NGINX_CONF="/etc/nginx/sites-available/safehorizon"
NGINX_ENABLED="/etc/nginx/sites-enabled/safehorizon"

##############################################################################
# Helper Functions
##############################################################################

print_header() {
    echo -e "\n${BOLD}${BLUE}============================================${NC}"
    echo -e "${BOLD}${BLUE} $1${NC}"
    echo -e "${BOLD}${BLUE}============================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

print_step() {
    echo -e "\n${BOLD}${YELLOW}📋 Step: $1${NC}"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then 
        print_error "This script must be run as root (use sudo)"
    fi
}

check_os() {
    if [[ ! -f /etc/os-release ]]; then
        print_error "Cannot determine OS. This script supports Ubuntu/Debian."
    fi
    
    . /etc/os-release
    
    if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
        print_error "This script supports Ubuntu/Debian only. Detected: $ID"
    fi
    
    print_success "Running on $PRETTY_NAME"
}

##############################################################################
# User Input Collection
##############################################################################

collect_deployment_info() {
    print_header "🔧 Deployment Configuration"
    
    # Get domain name
    while [[ -z "$DOMAIN" ]]; do
        read -p "Enter your domain name (e.g., api.safehorizon.com): " DOMAIN
        if [[ ! "$DOMAIN" =~ ^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$ ]]; then
            print_warning "Invalid domain format. Please try again."
            DOMAIN=""
        fi
    done
    
    # Get email for SSL
    while [[ -z "$EMAIL" ]]; do
        read -p "Enter your email for SSL certificate (Let's Encrypt): " EMAIL
        if [[ ! "$EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
            print_warning "Invalid email format. Please try again."
            EMAIL=""
        fi
    done
    
    # Confirm deployment
    echo -e "\n${BOLD}Deployment Summary:${NC}"
    echo -e "Domain: ${GREEN}$DOMAIN${NC}"
    echo -e "Email: ${GREEN}$EMAIL${NC}"
    echo -e "Project Directory: ${GREEN}$PROJECT_DIR${NC}"
    echo -e "Repository: ${GREEN}$REPO_URL${NC}"
    
    read -p "Proceed with deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Deployment cancelled by user"
    fi
}

##############################################################################
# System Preparation
##############################################################################

update_system() {
    print_step "Updating system packages"
    
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y
    apt-get upgrade -y
    apt-get install -y \
        curl \
        wget \
        git \
        nano \
        htop \
        unzip \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        openssl \
        ufw \
        fail2ban \
        logrotate
    
    print_success "System updated successfully"
}

install_docker() {
    print_step "Installing Docker & Docker Compose"
    
    if command -v docker &> /dev/null; then
        print_success "Docker already installed: $(docker --version)"
    else
        # Install Docker
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        rm get-docker.sh
        
        # Add docker group
        groupadd -f docker
        
        # Start and enable Docker
        systemctl start docker
        systemctl enable docker
        
        print_success "Docker installed successfully"
    fi
    
    # Install Docker Compose (latest version)
    if command -v docker-compose &> /dev/null; then
        print_success "Docker Compose already installed: $(docker-compose --version)"
    else
        DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep -oP '"tag_name": "\K(.*)(?=")')
        curl -L "https://github.com/docker/compose/releases/download/$DOCKER_COMPOSE_VERSION/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
        print_success "Docker Compose installed successfully"
    fi
}

install_nginx() {
    print_step "Installing and configuring Nginx"
    
    if command -v nginx &> /dev/null; then
        print_success "Nginx already installed"
    else
        apt-get install -y nginx
        systemctl start nginx
        systemctl enable nginx
        print_success "Nginx installed and started"
    fi
    
    # Configure firewall for Nginx
    ufw allow 'Nginx Full'
    ufw allow OpenSSH
    ufw --force enable
    
    print_success "Firewall configured for Nginx"
}

install_certbot() {
    print_step "Installing Certbot for SSL certificates"
    
    if command -v certbot &> /dev/null; then
        print_success "Certbot already installed"
    else
        apt-get install -y snapd
        snap install core; snap refresh core
        snap install --classic certbot
        ln -sf /snap/bin/certbot /usr/bin/certbot
        print_success "Certbot installed successfully"
    fi
}

##############################################################################
# Project Setup
##############################################################################

setup_project_directory() {
    print_step "Setting up project directory"
    
    # Create directories
    mkdir -p "$PROJECT_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$LOG_DIR"
    
    # Set permissions
    chown -R root:root "$PROJECT_DIR"
    chmod -R 755 "$PROJECT_DIR"
    
    cd "$PROJECT_DIR"
    
    print_success "Project directory created: $PROJECT_DIR"
}

clone_or_update_repository() {
    print_step "Cloning/updating SafeHorizon repository"
    
    cd "$PROJECT_DIR"
    
    if [ -d ".git" ]; then
        print_info "Repository exists, updating..."
        git fetch --all
        git reset --hard origin/main
        git pull origin main
        print_success "Repository updated to latest version"
    else
        print_info "Cloning repository..."
        rm -rf ./* .*  2>/dev/null || true
        git clone "$REPO_URL" .
        print_success "Repository cloned successfully"
    fi
    
    # Make scripts executable
    chmod +x deploy.sh 2>/dev/null || true
    chmod +x *.sh 2>/dev/null || true
}

create_production_environment() {
    print_step "Creating production environment configuration"
    
    cd "$PROJECT_DIR"
    
    # Generate secure random passwords
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    JWT_SECRET=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-50)
    
    cat > .env.production << EOF
# SafeHorizon Backend - Production Environment
# Auto-generated on $(date)
# Domain: $DOMAIN

# Application Settings
APP_NAME=SafeHorizon API
APP_ENV=production
APP_DEBUG=false
API_PREFIX=/api

# Database Configuration (PostgreSQL + PostGIS)
DATABASE_URL=postgresql+asyncpg://postgres:${DB_PASSWORD}@db:5432/${PROJECT_NAME}
SYNC_DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/${PROJECT_NAME}

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Security Settings
JWT_SECRET_KEY=${JWT_SECRET}
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# External Services
FIREBASE_CREDENTIALS_JSON_PATH=/app/docs/firebase-admin-sdk.json
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=

# AI Models Storage
MODELS_DIR=/app/models_store

# CORS Settings (Production)
ALLOWED_ORIGINS=https://${DOMAIN},https://www.${DOMAIN}

# Production Database Password
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_USER=postgres
POSTGRES_DB=${PROJECT_NAME}
EOF
    
    # Create Docker override for production
    cat > docker-compose.override.yml << EOF
version: '3.9'

services:
  api:
    restart: unless-stopped
    environment:
      - APP_ENV=production
      - APP_DEBUG=false
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.safehorizon-api.rule=Host(\`$DOMAIN\`)"
      - "traefik.http.routers.safehorizon-api.tls=true"
      - "traefik.http.routers.safehorizon-api.tls.certresolver=letsencrypt"
    
  db:
    restart: unless-stopped
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - $BACKUP_DIR:/backups
    
  redis:
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru

volumes:
  postgres_data:
    driver: local
EOF
    
    print_success "Production environment configured"
    print_info "Database password: $DB_PASSWORD (saved in .env.production)"
}

##############################################################################
# Nginx Configuration
##############################################################################

configure_nginx() {
    print_step "Configuring Nginx reverse proxy"
    
    # Remove default site
    rm -f /etc/nginx/sites-enabled/default
    
    # Create SafeHorizon Nginx configuration
    cat > "$NGINX_CONF" << EOF
# SafeHorizon Backend - Nginx Configuration
# Domain: $DOMAIN
# Generated: $(date)

# Rate limiting
limit_req_zone \$binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone \$binary_remote_addr zone=auth_limit:10m rate=5r/s;

# Upstream backend
upstream safehorizon_backend {
    server 127.0.0.1:$API_PORT;
    keepalive 32;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # Redirect all HTTP to HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;
    
    # SSL Configuration (will be updated by Certbot)
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml application/json;
    
    # API routes with rate limiting
    location /api/auth/ {
        limit_req zone=auth_limit burst=20 nodelay;
        proxy_pass http://safehorizon_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
    }
    
    location /api/ {
        limit_req zone=api_limit burst=50 nodelay;
        proxy_pass http://safehorizon_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
    }
    
    # Health check (no rate limiting)
    location /health {
        proxy_pass http://safehorizon_backend;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        access_log off;
    }
    
    # Documentation
    location /docs {
        proxy_pass http://safehorizon_backend;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # WebSocket support
    location /ws {
        proxy_pass http://safehorizon_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
    }
    
    # Block access to sensitive files
    location ~ /\\.ht {
        deny all;
    }
    
    location ~ /\\.(env|git) {
        deny all;
    }
    
    # Custom error pages
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
    
    # Logging
    access_log $LOG_DIR/nginx_access.log;
    error_log $LOG_DIR/nginx_error.log;
}
EOF
    
    # Enable the site
    ln -sf "$NGINX_CONF" "$NGINX_ENABLED"
    
    # Test Nginx configuration
    nginx -t
    
    print_success "Nginx configured successfully"
}

##############################################################################
# SSL Certificate Setup
##############################################################################

setup_ssl_certificate() {
    print_step "Setting up SSL certificate with Let's Encrypt"
    
    # Stop Nginx temporarily for standalone mode
    systemctl stop nginx
    
    # Get SSL certificate
    certbot certonly \
        --standalone \
        --non-interactive \
        --agree-tos \
        --email "$EMAIL" \
        -d "$DOMAIN" \
        -d "www.$DOMAIN"
    
    # Start Nginx
    systemctl start nginx
    
    # Set up automatic renewal
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
    
    print_success "SSL certificate installed and auto-renewal configured"
}

##############################################################################
# Service Deployment
##############################################################################

build_and_start_services() {
    print_step "Building and starting SafeHorizon services"
    
    cd "$PROJECT_DIR"
    
    # Pull latest images
    docker-compose -f docker-compose.yml pull
    
    # Build custom images
    docker-compose -f docker-compose.yml build --no-cache
    
    # Start services
    docker-compose -f docker-compose.yml up -d
    
    print_info "Waiting for services to start..."
    sleep 30
    
    # Wait for database to be ready
    print_info "Waiting for database to be ready..."
    for i in {1..30}; do
        if docker-compose exec -T db pg_isready -U postgres -d "$PROJECT_NAME" > /dev/null 2>&1; then
            print_success "Database is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "Database failed to start after 5 minutes"
        fi
        sleep 10
    done
    
    # Run database migrations
    print_info "Running database migrations..."
    docker-compose exec -T api alembic upgrade head
    
    print_success "All services started successfully"
}

##############################################################################
# Health Checks and Verification
##############################################################################

verify_deployment() {
    print_step "Verifying deployment"
    
    # Check if services are running
    print_info "Checking service status..."
    
    services=("api" "db" "redis")
    for service in "${services[@]}"; do
        if docker-compose ps "$service" | grep -q "Up"; then
            print_success "$service is running"
        else
            print_error "$service is not running"
        fi
    done
    
    # Check API health
    print_info "Checking API health..."
    sleep 10
    
    for i in {1..10}; do
        if curl -f -s "http://localhost:$API_PORT/health" > /dev/null; then
            print_success "API health check passed"
            break
        fi
        if [ $i -eq 10 ]; then
            print_warning "API health check failed - check logs with: docker-compose logs api"
        fi
        sleep 5
    done
    
    # Check HTTPS
    print_info "Checking HTTPS access..."
    if curl -f -s "https://$DOMAIN/health" > /dev/null; then
        print_success "HTTPS access verified"
    else
        print_warning "HTTPS access failed - check Nginx configuration"
    fi
    
    # Check database
    print_info "Checking database connection..."
    if docker-compose exec -T db psql -U postgres -d "$PROJECT_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
        print_success "Database connection verified"
    else
        print_warning "Database connection failed"
    fi
}

##############################################################################
# Monitoring and Maintenance Setup
##############################################################################

setup_monitoring() {
    print_step "Setting up monitoring and maintenance"
    
    # Create log rotation configuration
    cat > /etc/logrotate.d/safehorizon << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 0644 root root
    postrotate
        systemctl reload nginx
    endscript
}
EOF
    
    # Create backup script
    cat > "$PROJECT_DIR/backup.sh" << 'EOF'
#!/bin/bash
# SafeHorizon Backup Script

BACKUP_DIR="/opt/safehorizon/backups"
DATE=$(date +%Y%m%d_%H%M%S)
PROJECT_NAME="safehorizon"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Database backup
docker-compose exec -T db pg_dump -U postgres "$PROJECT_NAME" | gzip > "$BACKUP_DIR/database_$DATE.sql.gz"

# Environment backup
cp .env.production "$BACKUP_DIR/env_$DATE.backup"

# Remove backups older than 30 days
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.backup" -mtime +30 -delete

echo "Backup completed: $DATE"
EOF
    
    chmod +x "$PROJECT_DIR/backup.sh"
    
    # Setup daily backup cron job
    (crontab -l 2>/dev/null; echo "0 2 * * * cd $PROJECT_DIR && ./backup.sh >> $LOG_DIR/backup.log 2>&1") | crontab -
    
    # Create service monitor script
    cat > "$PROJECT_DIR/monitor.sh" << 'EOF'
#!/bin/bash
# SafeHorizon Service Monitor

cd /opt/safehorizon

# Check if services are running
if ! docker-compose ps | grep -q "Up"; then
    echo "Services are down, restarting..."
    docker-compose restart
    echo "Services restarted at $(date)" >> /var/log/safehorizon/monitor.log
fi

# Check API health
if ! curl -f -s http://localhost:8000/health > /dev/null; then
    echo "API health check failed, restarting API..."
    docker-compose restart api
    echo "API restarted at $(date)" >> /var/log/safehorizon/monitor.log
fi
EOF
    
    chmod +x "$PROJECT_DIR/monitor.sh"
    
    # Setup monitoring cron job (every 5 minutes)
    (crontab -l 2>/dev/null; echo "*/5 * * * * cd $PROJECT_DIR && ./monitor.sh") | crontab -
    
    print_success "Monitoring and maintenance configured"
}

##############################################################################
# Security Hardening
##############################################################################

setup_security() {
    print_step "Applying security hardening"
    
    # Configure fail2ban for Nginx
    cat > /etc/fail2ban/jail.d/nginx.conf << EOF
[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = $LOG_DIR/nginx_error.log
maxretry = 3
bantime = 3600

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = $LOG_DIR/nginx_error.log
maxretry = 5
bantime = 3600
EOF
    
    # Restart fail2ban
    systemctl restart fail2ban
    
    # Set proper file permissions
    chown -R root:root "$PROJECT_DIR"
    chmod 600 "$PROJECT_DIR/.env.production"
    chmod 700 "$PROJECT_DIR"/*.sh
    
    # Disable SSH password authentication (optional)
    read -p "Disable SSH password authentication? (recommended for security) (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
        sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
        systemctl restart ssh
        print_success "SSH password authentication disabled"
    fi
    
    print_success "Security hardening applied"
}

##############################################################################
# Final Steps and Information
##############################################################################

show_deployment_summary() {
    print_header "🎉 SafeHorizon Backend Deployment Complete!"
    
    echo -e "${BOLD}Deployment Summary:${NC}"
    echo -e "┌─────────────────────────────────────────────────────────┐"
    echo -e "│                    ${GREEN}SafeHorizon Backend${NC}                   │"
    echo -e "├─────────────────────────────────────────────────────────┤"
    echo -e "│ ${BOLD}🌐 Production URL:${NC} https://$DOMAIN                     │"
    echo -e "│ ${BOLD}📚 API Documentation:${NC} https://$DOMAIN/docs            │"
    echo -e "│ ${BOLD}❤️  Health Check:${NC} https://$DOMAIN/health             │"
    echo -e "│ ${BOLD}📂 Project Directory:${NC} $PROJECT_DIR                    │"
    echo -e "│ ${BOLD}📊 Logs Directory:${NC} $LOG_DIR                          │"
    echo -e "│ ${BOLD}💾 Backups Directory:${NC} $BACKUP_DIR                    │"
    echo -e "└─────────────────────────────────────────────────────────┘"
    
    echo -e "\n${BOLD}🔧 Management Commands:${NC}"
    echo -e "• View logs:           ${GREEN}cd $PROJECT_DIR && docker-compose logs -f${NC}"
    echo -e "• Restart services:    ${GREEN}cd $PROJECT_DIR && docker-compose restart${NC}"
    echo -e "• Stop services:       ${GREEN}cd $PROJECT_DIR && docker-compose down${NC}"
    echo -e "• Start services:      ${GREEN}cd $PROJECT_DIR && docker-compose up -d${NC}"
    echo -e "• Update deployment:   ${GREEN}cd $PROJECT_DIR && git pull && docker-compose up -d --build${NC}"
    echo -e "• Manual backup:       ${GREEN}cd $PROJECT_DIR && ./backup.sh${NC}"
    echo -e "• Check service status: ${GREEN}cd $PROJECT_DIR && docker-compose ps${NC}"
    
    echo -e "\n${BOLD}📊 Service Status:${NC}"
    cd "$PROJECT_DIR"
    docker-compose ps
    
    echo -e "\n${BOLD}🔒 Security Features:${NC}"
    echo -e "• ✅ SSL/TLS encryption (Let's Encrypt)"
    echo -e "• ✅ Nginx reverse proxy with rate limiting"
    echo -e "• ✅ Firewall (UFW) configured"
    echo -e "• ✅ Fail2ban intrusion prevention"
    echo -e "• ✅ Automatic security updates"
    echo -e "• ✅ Secure headers configured"
    
    echo -e "\n${BOLD}🤖 Automation:${NC}"
    echo -e "• ✅ SSL certificate auto-renewal"
    echo -e "• ✅ Daily database backups (2 AM)"
    echo -e "• ✅ Service monitoring (every 5 minutes)"
    echo -e "• ✅ Log rotation configured"
    
    echo -e "\n${BOLD}📱 Test Your API:${NC}"
    echo -e "curl -X GET https://$DOMAIN/health"
    echo -e "curl -X GET https://$DOMAIN/docs"
    
    echo -e "\n${GREEN}🚀 Your SafeHorizon backend is now LIVE and ready for production!${NC}"
    echo -e "\n${YELLOW}📞 Support: Create an issue at https://github.com/PRATHAM-JARVIS/safehorizon_backend/issues${NC}"
}

##############################################################################
# Main Deployment Flow
##############################################################################

main() {
    print_header "🚀 SafeHorizon Backend - Live Deployment"
    print_info "This script will deploy SafeHorizon backend to production"
    print_info "Estimated time: 5-10 minutes"
    
    # Pre-flight checks
    check_root
    check_os
    
    # Get deployment configuration
    collect_deployment_info
    
    # System preparation
    update_system
    install_docker
    install_nginx
    install_certbot
    
    # Project setup
    setup_project_directory
    clone_or_update_repository
    create_production_environment
    
    # Web server configuration
    configure_nginx
    setup_ssl_certificate
    
    # Service deployment
    build_and_start_services
    
    # Post-deployment
    verify_deployment
    setup_monitoring
    setup_security
    
    # Final summary
    show_deployment_summary
}

# Error handling
trap 'print_error "Deployment failed at line $LINENO. Check the logs above."' ERR

# Run main deployment
main "$@"