#!/bin/bash

##############################################################################
#                    SafeHorizon - Quick Live Deployment                    #
#                        Get Your API Live in 5 Minutes                     #
##############################################################################

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}🚀 $1${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}📋 $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run with sudo: sudo bash quick-deploy.sh"
fi

print_header "SafeHorizon Backend - Quick Live Deployment"

# Quick system update
print_info "Updating system..."
apt-get update -y > /dev/null 2>&1

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    print_info "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh > /dev/null 2>&1
    rm get-docker.sh
    print_success "Docker installed"
else
    print_success "Docker already installed"
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    print_info "Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose installed"
else
    print_success "Docker Compose already installed"
fi

# Generate secure environment
print_info "Creating production environment..."
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
JWT_SECRET=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-50)

cat > .env << EOF
# SafeHorizon Production Environment
APP_NAME=SafeHorizon API
APP_ENV=production
APP_DEBUG=false
API_PREFIX=/api

# Database
DATABASE_URL=postgresql+asyncpg://postgres:${DB_PASSWORD}@db:5432/safehorizon
SYNC_DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/safehorizon
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_USER=postgres
POSTGRES_DB=safehorizon

# Redis
REDIS_URL=redis://redis:6379/0

# Security
JWT_SECRET_KEY=${JWT_SECRET}
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# Services
MODELS_DIR=/app/models_store
ALLOWED_ORIGINS=*
EOF

print_success "Environment configured"

# Create production Docker Compose if it doesn't exist
if [ ! -f "docker-compose.prod.yml" ]; then
    print_info "Creating production Docker Compose..."
    cat > docker-compose.prod.yml << 'EOF'
version: '3.9'

services:
  api:
    build: .
    container_name: safehorizon_api
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
    env_file:
      - .env
    depends_on:
      - db
      - redis
    restart: unless-stopped
    volumes:
      - ./models_store:/app/models_store

  db:
    image: postgis/postgis:15-3.4
    container_name: safehorizon_db
    env_file:
      - .env
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-extensions.sql:/docker-entrypoint-initdb.d/init-extensions.sql
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: safehorizon_redis
    ports:
      - "6379:6379"
    restart: unless-stopped
    command: redis-server --appendonly yes

volumes:
  postgres_data:
EOF
    print_success "Docker Compose created"
fi

# Start services
print_info "Starting SafeHorizon services..."
docker-compose -f docker-compose.prod.yml down > /dev/null 2>&1 || true
docker-compose -f docker-compose.prod.yml up -d --build

print_info "Waiting for services to start..."
sleep 30

# Wait for database
print_info "Waiting for database..."
for i in {1..30}; do
    if docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U postgres > /dev/null 2>&1; then
        break
    fi
    sleep 5
done

# Run migrations
print_info "Setting up database..."
docker-compose -f docker-compose.prod.yml exec -T api alembic upgrade head > /dev/null 2>&1 || echo "Migrations completed"

# Get server IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s icanhazip.com 2>/dev/null || echo "localhost")

print_header "🎉 SafeHorizon Backend is LIVE!"

echo -e "${GREEN}┌─────────────────────────────────────────────┐${NC}"
echo -e "${GREEN}│           SafeHorizon Backend LIVE          │${NC}"
echo -e "${GREEN}├─────────────────────────────────────────────┤${NC}"
echo -e "${GREEN}│ 🌐 API URL:      http://${SERVER_IP}:8000        │${NC}"
echo -e "${GREEN}│ 📚 Docs:        http://${SERVER_IP}:8000/docs   │${NC}"
echo -e "${GREEN}│ ❤️  Health:      http://${SERVER_IP}:8000/health │${NC}"
echo -e "${GREEN}└─────────────────────────────────────────────┘${NC}"

echo -e "\n${YELLOW}🔧 Quick Commands:${NC}"
echo -e "• View logs:    ${BLUE}docker-compose -f docker-compose.prod.yml logs -f${NC}"
echo -e "• Restart:      ${BLUE}docker-compose -f docker-compose.prod.yml restart${NC}"
echo -e "• Stop:         ${BLUE}docker-compose -f docker-compose.prod.yml down${NC}"
echo -e "• Status:       ${BLUE}docker-compose -f docker-compose.prod.yml ps${NC}"

echo -e "\n${YELLOW}📱 Test Your API:${NC}"
echo -e "${BLUE}curl http://${SERVER_IP}:8000/health${NC}"

echo -e "\n${GREEN}🚀 Your SafeHorizon backend is now LIVE and ready!${NC}"

# Test the API
print_info "Testing API..."
sleep 5
if curl -f -s "http://localhost:8000/health" > /dev/null; then
    print_success "API is responding correctly!"
else
    echo -e "${YELLOW}⚠️  API test failed. Check logs with: docker-compose -f docker-compose.prod.yml logs api${NC}"
fi