#!/bin/bash

##############################################################################
#                    SafeHorizon Backend Deployment Script                   #
#                   Complete Automated Linux Deployment                      #
#                                                                            #
# Usage:                                                                     #
#   sudo bash deploy.sh                 - Full deployment                   #
#   bash deploy.sh start                - Start services                    #
#   bash deploy.sh stop                 - Stop services                     #
#   bash deploy.sh restart              - Restart services                  #
#   bash deploy.sh status               - Check status                      #
#   bash deploy.sh logs                 - View logs                         #
#   bash deploy.sh backup               - Backup database                   #
#   bash deploy.sh clean                - Clean all data                    #
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
DB_PASSWORD="safehorizon_prod_2025"
API_PORT=8000
DB_PORT=5432
REDIS_PORT=6379

##############################################################################
# Helper Functions
##############################################################################

print_header() {
    echo -e "\n${BOLD}${BLUE}========================================${NC}"
    echo -e "${BOLD}${BLUE}$1${NC}"
    echo -e "${BOLD}${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

check_root() {
    if [ "$EUID" -ne 0 ] && [ "$1" != "logs" ] && [ "$1" != "status" ]; then 
        print_error "Please run with sudo for installation commands"
        exit 1
    fi
}

##############################################################################
# Prerequisites Installation
##############################################################################

install_docker() {
    print_header "Installing Docker"
    
    if command -v docker &> /dev/null; then
        print_success "Docker already installed"
        docker --version
        return 0
    fi
    
    print_info "Installing Docker..."
    
    # Update package list
    apt-get update -y
    
    # Install dependencies
    apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release \
        software-properties-common
    
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Add Docker repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    # Add current user to docker group
    if [ -n "$SUDO_USER" ]; then
        usermod -aG docker $SUDO_USER
    fi
    
    print_success "Docker installed successfully!"
}

install_docker_compose() {
    print_header "Installing Docker Compose"
    
    if command -v docker-compose &> /dev/null; then
        print_success "Docker Compose already installed"
        docker-compose --version
        return 0
    fi
    
    print_info "Installing Docker Compose..."
    
    # Get latest version
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    
    # Download Docker Compose
    curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    
    # Make executable
    chmod +x /usr/local/bin/docker-compose
    
    # Create symlink
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    print_success "Docker Compose installed successfully!"
}

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        install_docker
    else
        print_success "Docker is installed"
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        install_docker_compose
    else
        print_success "Docker Compose is installed"
    fi
}

##############################################################################
# Environment Configuration
##############################################################################

create_env_file() {
    print_header "Creating Environment Configuration"
    
    ENV_FILE=".env.production"
    
    if [ -f "$ENV_FILE" ]; then
        print_warning "$ENV_FILE already exists"
        read -p "Regenerate? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Keeping existing environment file"
            return 0
        fi
        
        # Backup existing file
        BACKUP_FILE="${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$ENV_FILE" "$BACKUP_FILE"
        print_info "Backed up to $BACKUP_FILE"
    fi
    
    print_info "Creating $ENV_FILE with production credentials..."
    
    cat > "$ENV_FILE" << EOF
# SafeHorizon Backend Environment Configuration
# Auto-generated on $(date)

# App Settings
APP_NAME=SafeHorizon API
APP_ENV=production
APP_DEBUG=False
API_PREFIX=/api

# Database Configuration (PostgreSQL + PostGIS)
DATABASE_URL=postgresql+asyncpg://postgres:${DB_PASSWORD}@db:5432/${PROJECT_NAME}
SYNC_DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/${PROJECT_NAME}

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Supabase (Optional - currently using local auth)
SUPABASE_URL=https://dcbrwujnbjjstbtcywxf.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRjYnJ3dWpuYmpqc3RidGN5d3hmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkwNzY4OTIsImV4cCI6MjA3NDY1Mjg5Mn0.V8tGGeNLLdPK96Qq3y7EWFeyWey5w1DP6kz2uSmW6B4
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRjYnJ3dWpuYmpqc3RidGN5d3hmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTA3Njg5MiwiZXhwIjoyMDc0NjUyODkyfQ.Kb4LFx_j-q3_TGgt1Kp2RfS-Gd3Tjqd_0N5fsq_kCsA
SUPABASE_JWT_SECRET=QKvMUmVzrLgSzPpRtNeMhLka60jpe5+Av8hEp1l/INDb0tgDJmb0G6M/WAXGU4z8YIujr468G1WWqnLtEMt1hA==

# Firebase Configuration (for push notifications)
FIREBASE_CREDENTIALS_JSON_PATH=docs/firebase-admin-sdk.json

# Twilio Configuration (for SMS notifications)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=

# AI Models Storage
MODELS_DIR=./models_store

# CORS Settings
ALLOWED_ORIGINS=*

# Security Settings
JWT_SECRET_KEY=${PROJECT_NAME}_secret_key_$(openssl rand -hex 16)
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440
EOF
    
    print_success "$ENV_FILE created successfully!"
}

##############################################################################
# Docker Services Management
##############################################################################

build_images() {
    print_header "Building Docker Images"
    docker-compose -f docker-compose.prod.yml build --no-cache
    print_success "Docker images built successfully!"
}

start_services() {
    print_header "Starting Services in Background"
    
    # Start services in detached mode
    docker-compose -f docker-compose.prod.yml up -d
    
    print_success "Services started in background!"
    print_info "Waiting for services to initialize..."
    sleep 10
    
    check_health
}

stop_services() {
    print_header "Stopping Services"
    docker-compose -f docker-compose.prod.yml down
    print_success "Services stopped successfully!"
}

restart_services() {
    stop_services
    sleep 3
    start_services
}

check_status() {
    print_header "Service Status"
    docker-compose -f docker-compose.prod.yml ps
    echo ""
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

show_logs() {
    print_header "Service Logs (Press Ctrl+C to exit)"
    docker-compose -f docker-compose.prod.yml logs -f --tail=100
}

check_health() {
    print_header "Checking API Health"
    
    for i in {1..30}; do
        if curl -s http://localhost:${API_PORT}/health > /dev/null 2>&1; then
            HEALTH=$(curl -s http://localhost:${API_PORT}/health)
            print_success "API is healthy!"
            echo -e "${CYAN}Response: ${HEALTH}${NC}"
            return 0
        fi
        sleep 2
    done
    
    print_warning "Health check timeout - API might still be starting"
    print_info "Check logs with: bash deploy.sh logs"
}

##############################################################################
# Database Operations
##############################################################################

run_migrations() {
    print_header "Running Database Migrations"
    
    sleep 5  # Wait for DB to be fully ready
    
    docker exec ${PROJECT_NAME}_api alembic upgrade head
    print_success "Migrations completed!"
}

backup_database() {
    print_header "Backing Up Database"
    
    BACKUP_DIR="backups"
    mkdir -p "$BACKUP_DIR"
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="${BACKUP_DIR}/${PROJECT_NAME}_backup_${TIMESTAMP}.sql"
    
    print_info "Creating backup: $BACKUP_FILE"
    docker exec ${PROJECT_NAME}_db pg_dump -U postgres ${PROJECT_NAME} > "$BACKUP_FILE"
    
    print_success "Database backed up to $BACKUP_FILE"
    
    # Keep only last 10 backups
    ls -t ${BACKUP_DIR}/*.sql | tail -n +11 | xargs -r rm
    print_info "Old backups cleaned (keeping last 10)"
}

restore_database() {
    if [ -z "$1" ]; then
        print_error "Usage: bash deploy.sh restore <backup_file>"
        exit 1
    fi
    
    if [ ! -f "$1" ]; then
        print_error "Backup file not found: $1"
        exit 1
    fi
    
    print_header "Restoring Database"
    print_warning "This will overwrite the current database!"
    read -p "Type 'yes' to continue: " -r
    
    if [ "$REPLY" != "yes" ]; then
        print_info "Restore cancelled"
        exit 0
    fi
    
    print_info "Restoring from: $1"
    docker exec -i ${PROJECT_NAME}_db psql -U postgres ${PROJECT_NAME} < "$1"
    print_success "Database restored successfully!"
}

##############################################################################
# Cleanup Operations
##############################################################################

clean_all() {
    print_header "Cleaning Up"
    print_warning "This will remove all containers, volumes, and images!"
    read -p "Type 'yes' to continue: " -r
    
    if [ "$REPLY" != "yes" ]; then
        print_info "Cleanup cancelled"
        exit 0
    fi
    
    print_info "Stopping services..."
    docker-compose -f docker-compose.prod.yml down -v
    
    print_info "Removing Docker resources..."
    docker system prune -af --volumes
    
    print_success "Cleanup completed!"
}

##############################################################################
# Deployment Info
##############################################################################

show_info() {
    print_header "Deployment Information"
    
    cat << EOF
${BOLD}Project:${NC} SafeHorizon Backend
${BOLD}Mode:${NC} Production
${BOLD}Compose File:${NC} docker-compose.prod.yml
${BOLD}Environment:${NC} .env.production

${BOLD}Service URLs:${NC}
  • API:         http://localhost:${API_PORT}
  • API Docs:    http://localhost:${API_PORT}/docs
  • Health:      http://localhost:${API_PORT}/health
  • PostgreSQL:  localhost:${DB_PORT}
  • Redis:       localhost:${REDIS_PORT}

${BOLD}Database Credentials:${NC}
  • User:        postgres
  • Password:    ${DB_PASSWORD}
  • Database:    ${PROJECT_NAME}

${BOLD}Docker Containers:${NC}
  • ${PROJECT_NAME}_api    - FastAPI Application
  • ${PROJECT_NAME}_db     - PostgreSQL + PostGIS
  • ${PROJECT_NAME}_redis  - Redis Cache

${BOLD}Management Commands:${NC}
  • Status:      bash deploy.sh status
  • Logs:        bash deploy.sh logs
  • Restart:     bash deploy.sh restart
  • Stop:        bash deploy.sh stop
  • Backup:      bash deploy.sh backup
  • Clean:       bash deploy.sh clean

${BOLD}Docker Commands:${NC}
  • View logs:   docker logs -f ${PROJECT_NAME}_api
  • Shell:       docker exec -it ${PROJECT_NAME}_api bash
  • Database:    docker exec -it ${PROJECT_NAME}_db psql -U postgres ${PROJECT_NAME}
EOF
}

##############################################################################
# Full Deployment Workflow
##############################################################################

full_deploy() {
    print_header "SafeHorizon Backend - Full Deployment"
    
    # Check prerequisites
    check_prerequisites
    
    # Create environment file
    create_env_file
    
    # Build images
    build_images
    
    # Start services
    start_services
    
    # Run migrations
    run_migrations
    
    # Show deployment info
    show_info
    
    print_success "\n🎉 Deployment completed successfully!"
    print_info "\nAPI is running at: http://localhost:${API_PORT}"
    print_info "View logs with: bash deploy.sh logs"
}

##############################################################################
# Main Script Logic
##############################################################################

case "${1:-deploy}" in
    deploy|install)
        check_root "$1"
        full_deploy
        ;;
    
    start)
        check_root "$1"
        create_env_file
        start_services
        ;;
    
    stop)
        check_root "$1"
        stop_services
        ;;
    
    restart)
        check_root "$1"
        restart_services
        ;;
    
    status)
        check_status
        ;;
    
    logs)
        show_logs
        ;;
    
    health)
        check_health
        ;;
    
    migrations)
        check_root "$1"
        run_migrations
        ;;
    
    backup)
        backup_database
        ;;
    
    restore)
        check_root "$1"
        restore_database "$2"
        ;;
    
    build)
        check_root "$1"
        build_images
        ;;
    
    clean)
        check_root "$1"
        clean_all
        ;;
    
    info)
        show_info
        ;;
    
    *)
        cat << EOF
${BOLD}${BLUE}SafeHorizon Backend Deployment Script${NC}

${BOLD}Usage:${NC}
  sudo bash deploy.sh [command]

${BOLD}Commands:${NC}
  ${GREEN}deploy${NC}         Full deployment (default)
  ${GREEN}start${NC}          Start services in background
  ${GREEN}stop${NC}           Stop all services
  ${GREEN}restart${NC}        Restart all services
  ${GREEN}status${NC}         Show service status
  ${GREEN}logs${NC}           View service logs (live)
  ${GREEN}health${NC}         Check API health
  ${GREEN}backup${NC}         Backup database
  ${GREEN}restore${NC} <file> Restore database
  ${GREEN}migrations${NC}     Run database migrations
  ${GREEN}build${NC}          Rebuild Docker images
  ${GREEN}clean${NC}          Remove all containers/volumes
  ${GREEN}info${NC}           Show deployment information

${BOLD}Examples:${NC}
  sudo bash deploy.sh              # Full deployment
  sudo bash deploy.sh start        # Start services
  bash deploy.sh logs              # View logs
  bash deploy.sh status            # Check status
  bash deploy.sh backup            # Backup database
  sudo bash deploy.sh clean        # Clean everything

${BOLD}Quick Deploy:${NC}
  curl -sSL https://raw.githubusercontent.com/PRATHAM-JARVIS/safehorizon_backend/main/deploy.sh | sudo bash

${BOLD}Documentation:${NC}
  For detailed docs, visit: http://localhost:8000/docs
EOF
        ;;
esac

exit 0
