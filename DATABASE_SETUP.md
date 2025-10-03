# SafeHorizon Database Setup for Ubuntu

This guide helps you set up only the database components for SafeHorizon on Ubuntu servers.

## Quick Setup

### 1. Automated Setup (Recommended)

Run the automated setup script:

```bash
# Basic database setup
python3 setup_database.py

# With sample data for testing
python3 setup_database.py --with-sample-data

# Custom database name and user
python3 setup_database.py --db-name mydb --db-user myuser --with-sample-data
```

### 2. What the Script Does

- ✅ Installs PostgreSQL 15 with PostGIS
- ✅ Creates database and user with secure password
- ✅ Enables PostGIS extensions
- ✅ Creates `.env` configuration file
- ✅ Installs Python dependencies
- ✅ Runs database migrations to create schema
- ✅ Optionally creates sample data
- ✅ Tests the connection

### 3. Verify Setup

After running the setup, verify everything works:

```bash
python3 verify_database.py
```

## Manual Setup (Alternative)

If you prefer to set up manually:

### Install PostgreSQL

```bash
sudo apt update
sudo apt install -y postgresql-15 postgresql-contrib-15 postgresql-15-postgis-3
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Create Database

```bash
sudo -u postgres psql
```

```sql
CREATE USER safehorizon_user WITH PASSWORD 'your_secure_password';
CREATE DATABASE safehorizon OWNER safehorizon_user;
GRANT ALL PRIVILEGES ON DATABASE safehorizon TO safehorizon_user;
ALTER USER safehorizon_user CREATEDB;
\q
```

### Enable PostGIS

```bash
sudo -u postgres psql -d safehorizon -c "CREATE EXTENSION IF NOT EXISTS postgis;"
sudo -u postgres psql -d safehorizon -c "CREATE EXTENSION IF NOT EXISTS postgis_topology;"
```

### Install Python Dependencies

```bash
sudo apt install -y python3-pip python3-dev libpq-dev build-essential
python3 -m pip install -r requirements.txt --user
```

### Create .env File

Create `.env` with your database credentials:

```env
DATABASE_URL=postgresql+asyncpg://safehorizon_user:your_password@localhost:5432/safehorizon
SYNC_DATABASE_URL=postgresql://safehorizon_user:your_password@localhost:5432/safehorizon
APP_DEBUG=true
API_PREFIX=/api
```

### Run Migrations

```bash
python3 -m alembic upgrade head
```

## Database Information

After setup, you'll have:

- **Database**: `safehorizon` (or your custom name)
- **User**: `safehorizon_user` (or your custom user)
- **Host**: `localhost`
- **Port**: `5432`
- **Extensions**: PostGIS, UUID-OSSP

## Sample Data (Optional)

If you used `--with-sample-data`, you'll have:

### Sample Tourist Accounts
- Email: `john.doe@example.com` | Password: `password123`
- Email: `alice.smith@example.com` | Password: `password123`

### Sample Authority Accounts
- Email: `officer.johnson@police.gov` | Password: `police123`
- Email: `detective.brown@police.gov` | Password: `police123`

### Sample Zones
- High Crime Area Downtown (Risky)
- Tourist Safe Zone (Safe)
- Military Base Restricted (Restricted)

## Database Connection

Connect to your database:

```bash
# Using psql
psql -h localhost -p 5432 -U safehorizon_user -d safehorizon

# Connection string for applications
postgresql://safehorizon_user:PASSWORD@localhost:5432/safehorizon
```

## Next Steps

1. **Start your FastAPI application**:
   ```bash
   python3 -m uvicorn app.main:app --reload
   ```

2. **Access API documentation**:
   - Open: `http://localhost:8000/docs`
   - Health check: `http://localhost:8000/health`

3. **Install additional services** (optional):
   - Redis for caching: `sudo apt install redis-server`
   - Nginx for reverse proxy: `sudo apt install nginx`

## Troubleshooting

### Connection Issues

If you get connection errors:

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check if PostgreSQL is listening
sudo netstat -tlnp | grep 5432

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

### Permission Issues

If you get permission errors:

```bash
# Reset PostgreSQL user password
sudo -u postgres psql -c "ALTER USER safehorizon_user WITH PASSWORD 'new_password';"

# Grant all privileges again
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE safehorizon TO safehorizon_user;"
```

### Migration Issues

If migrations fail:

```bash
# Check Alembic status
python3 -m alembic current

# Reset migrations (WARNING: This will drop all data)
python3 -m alembic downgrade base
python3 -m alembic upgrade head
```

## Security Notes

- 🔒 Database password is auto-generated and stored in `.env`
- 🔒 Change sample passwords before production use
- 🔒 Consider setting up firewall rules for PostgreSQL
- 🔒 Enable SSL for database connections in production
- 🔒 Regular backups are recommended

## Database Schema

The database includes these main tables:

- `tourists` - Tourist user accounts
- `authorities` - Police/authority accounts  
- `trips` - Trip planning and management
- `locations` - GPS tracking data
- `alerts` - Safety alerts and notifications
- `restricted_zones` - Geofenced areas
- `incidents` - Police incident management
- `efirs` - Electronic First Information Reports
- `user_devices` - Push notification tokens
- `emergency_broadcasts` - Mass alert system
- `broadcast_acknowledgments` - Tourist responses

For detailed schema information, see `DATABASE_SCHEMA_VISUAL.md`.