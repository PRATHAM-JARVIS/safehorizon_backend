# 🚀 SafeHorizon Backend - Simple Deploy

Deploy SafeHorizon backend in 2 minutes using Docker.

## Quick Start

### 1. One-Command Deploy
```bash
curl -sSL https://raw.githubusercontent.com/PRATHAM-JARVIS/safehorizon_backend/main/deploy.sh | bash
```

### 2. Manual Deploy
```bash
git clone https://github.com/PRATHAM-JARVIS/safehorizon_backend.git
cd safehorizon_backend
bash deploy.sh
```

## What You Get

✅ **Complete SafeHorizon API** - All 80+ endpoints  
✅ **PostgreSQL Database** - With PostGIS extensions  
✅ **Redis Cache** - For session management  
✅ **Auto Database Setup** - Migrations run automatically  
✅ **Production Ready** - Configured for production use  

## Access Your API

After deployment:
- **API URL**: `http://YOUR_SERVER_IP:8000`
- **Documentation**: `http://YOUR_SERVER_IP:8000/docs`
- **Health Check**: `http://YOUR_SERVER_IP:8000/health`

## Management Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Check status
docker-compose ps

# Update to latest
git pull && docker-compose up -d --build
```

## Test Your API

```bash
# Health check
curl http://YOUR_SERVER_IP:8000/health

# Register a tourist
curl -X POST http://YOUR_SERVER_IP:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","name":"Test User"}'

# View API documentation
curl http://YOUR_SERVER_IP:8000/docs
```

## Requirements

- **OS**: Ubuntu/Debian/CentOS Linux
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 10GB minimum
- **Ports**: 8000, 5432, 6379

## That's It! 

Your SafeHorizon backend is now live and ready for production use.

---

**🆘 Need Help?** Create an issue at https://github.com/PRATHAM-JARVIS/safehorizon_backend/issues