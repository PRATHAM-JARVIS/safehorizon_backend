# 🚀 SafeHorizon Backend - One-Command Deployment

Complete automated deployment script for Linux servers. Everything runs in the background automatically.

## ⚡ Quick Start

### One-Line Deployment

```bash
# Method 1: If you have the repo
sudo bash deploy.sh

# Method 2: Direct from GitHub
curl -sSL https://raw.githubusercontent.com/PRATHAM-JARVIS/safehorizon_backend/main/deploy.sh | sudo bash
```

**That's it!** The script will:
- ✅ Auto-install Docker & Docker Compose
- ✅ Create `.env.production` with your credentials
- ✅ Build all Docker images
- ✅ Start services in background
- ✅ Run database migrations
- ✅ Verify health

## 📋 All Commands

```bash
sudo bash deploy.sh              # Full deployment
sudo bash deploy.sh start        # Start services (background)
sudo bash deploy.sh stop         # Stop all services
sudo bash deploy.sh restart      # Restart services
bash deploy.sh status            # Check status
bash deploy.sh logs              # View live logs
bash deploy.sh health            # Check API health
bash deploy.sh backup            # Backup database
sudo bash deploy.sh restore file # Restore database
sudo bash deploy.sh migrations   # Run migrations
sudo bash deploy.sh build        # Rebuild images
sudo bash deploy.sh clean        # Remove everything
bash deploy.sh info              # Show deployment info
```

## 🌐 Access Points

After deployment:

| Service | URL | Description |
|---------|-----|-------------|
| **API** | http://localhost:8000 | REST API |
| **Docs** | http://localhost:8000/docs | Interactive API documentation |
| **Health** | http://localhost:8000/health | Health check endpoint |

## 🔐 Credentials

Auto-configured in `.env.production`:

- **Database Password**: `safehorizon_prod_2025`
- **Database User**: `postgres`
- **Database Name**: `safehorizon`
- **JWT Secret**: Auto-generated

## 🐳 Docker Containers

Three containers run in background:

- `safehorizon_api` - FastAPI application
- `safehorizon_db` - PostgreSQL + PostGIS
- `safehorizon_redis` - Redis cache

## 📊 Monitoring

```bash
# Check all services
bash deploy.sh status

# Live logs
bash deploy.sh logs

# API health
curl http://localhost:8000/health

# Container stats
docker stats
```

## 🔄 Common Tasks

### Update Application

```bash
git pull origin main
sudo bash deploy.sh restart
```

### Backup Database

```bash
bash deploy.sh backup
# Creates: backups/safehorizon_backup_YYYYMMDD_HHMMSS.sql
```

### View Logs for Specific Service

```bash
docker logs -f safehorizon_api
docker logs -f safehorizon_db
docker logs -f safehorizon_redis
```

### Access Database

```bash
docker exec -it safehorizon_db psql -U postgres safehorizon
```

### Complete Reset

```bash
sudo bash deploy.sh clean
sudo bash deploy.sh
```

## 🛠️ Troubleshooting

### Port Already in Use

```bash
# Check what's using port 8000
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>

# Or use different port in docker-compose.prod.yml
```

### Services Not Starting

```bash
# Check logs
bash deploy.sh logs

# Restart services
sudo bash deploy.sh restart
```

### Database Connection Issues

```bash
# Check if DB is running
docker ps | grep safehorizon_db

# View DB logs
docker logs safehorizon_db

# Access DB directly
docker exec -it safehorizon_db psql -U postgres safehorizon
```

## 🔒 Production Recommendations

1. **Change default password** in `.env.production`
2. **Enable firewall**: `sudo ufw allow 8000/tcp`
3. **Use NGINX** for SSL (config provided in `nginx.prod.conf`)
4. **Restrict CORS** in `.env.production`: `ALLOWED_ORIGINS=https://yourdomain.com`
5. **Set up automated backups**:
   ```bash
   # Add to crontab
   0 2 * * * cd /path/to/repo && bash deploy.sh backup
   ```

## 📁 File Structure

```
safehorizon_backend/
├── deploy.sh                # This deployment script
├── docker-compose.prod.yml  # Production Docker config
├── .env.production          # Auto-generated environment
├── backups/                 # Database backups
│   └── safehorizon_backup_*.sql
└── models_store/            # AI model storage
```

## 🆘 Emergency Commands

```bash
# Stop everything
sudo bash deploy.sh stop

# View what went wrong
bash deploy.sh logs

# Nuclear option - remove everything
sudo bash deploy.sh clean

# Fresh start
sudo bash deploy.sh
```

## 📞 Support

- **API Documentation**: http://localhost:8000/docs
- **GitHub**: https://github.com/PRATHAM-JARVIS/safehorizon_backend
- **Issues**: Create an issue on GitHub

---

**Made with ❤️ for tourist safety**
