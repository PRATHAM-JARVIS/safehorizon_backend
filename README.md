# 🚀 SafeHorizon FastAPI Backend

**Complete production-ready tourist safety platform with AI, real-time tracking, and emergency response.**

## 🏗️ Architecture

```
SafeHorizon Backend
├── FastAPI (Python 3.11)
├── Supabase (Auth + Database)
├── PostgreSQL + PostGIS (Spatial data)
├── Redis (WebSocket scaling)
├── AI Models (Anomaly detection)
├── WebSocket (Real-time alerts)
├── Firebase (Push notifications)
├── Twilio (SMS alerts)
└── Docker (Container deployment)
```

## ✨ Features

### 🧑‍💼 Tourist Mobile App
- **User Registration/Login** with Supabase Auth
- **Real-time GPS Tracking** with PostGIS storage
- **AI Safety Scoring** (0-100 scale)
- **SOS/Panic Button** with instant alerts
- **Trip Management** (start/end tracking)
- **Safety Zone Notifications**

### 👮‍♂️ Police Dashboard
- **Live Tourist Tracking** with WebSocket updates
- **Alert Management** (acknowledge/resolve incidents)
- **Zone Management** (create safe/restricted areas)
- **E-FIR Generation** for incidents
- **Real-time Notifications**

### 🤖 AI-Powered Safety
- **Geofencing** (rule-based zone checking)
- **Isolation Forest** (unsupervised anomaly detection)
- **LSTM Autoencoder** (sequence anomaly detection)
- **Composite Safety Scoring** (weighted multi-model)
- **Model Retraining** (continuous learning)

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL with PostGIS
- Redis
- Supabase account

### 1. Clone Repository
```bash
git clone https://github.com/your-org/safehorizon-backend.git
cd safehorizon-backend
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
nano .env
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
```bash
# Run migrations
alembic upgrade head
```

### 5. Start Services
```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

### 6. Verify Installation
```bash
curl http://localhost:8000/health
```

## 📡 API Endpoints

### 🔐 Authentication
```
POST /api/auth/register          # Tourist registration
POST /api/auth/login            # Tourist login
POST /api/auth/register-authority # Police registration
GET  /api/auth/me               # Get current user
```

### 📍 Location & Tracking
```
POST /api/trip/start            # Start trip tracking
POST /api/trip/end              # End trip tracking  
POST /api/location/update       # GPS location update
GET  /api/location/history      # Location history
GET  /api/safety/score          # Current safety score
```

### 🚨 Emergency & Alerts
```
POST /api/sos/trigger           # Emergency SOS
GET  /api/alerts/recent         # Recent alerts
WS   /api/alerts/subscribe      # Real-time alert stream
POST /api/incident/acknowledge  # Police acknowledge
```

### 🗺️ Zone Management
```
GET  /api/zones/list            # List all zones
POST /api/zones/create          # Create new zone
DELETE /api/zones/{id}          # Delete zone
```

### 🤖 AI Services
```
POST /api/ai/geofence/check     # Check zone status
POST /api/ai/anomaly/point      # Single point anomaly
POST /api/ai/score/compute      # Safety score calculation
POST /api/system/retrain-model  # Retrain AI models
```

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Test Coverage
```bash
pytest --cov=app tests/
```

### Specific Test Categories
```bash
# API endpoint tests
pytest tests/test_tourist_routes.py
pytest tests/test_authority_routes.py

# AI service tests  
pytest tests/test_ai_services.py
pytest tests/test_services.py

# WebSocket tests
pytest tests/test_websocket.py
```

## 🐳 Deployment

### Development
```bash
docker-compose up -d
```

### Production
```bash
# Build production image
docker build -f Dockerfile.prod -t safehorizon/backend .

# Deploy with production compose
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables
```bash
# Required for production
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_key
JWT_SECRET=your_jwt_secret
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
REDIS_URL=redis://host:6379/0
```

## 🔧 Configuration

### Database Models
- **Tourist**: User profiles and safety scores
- **Location**: GPS tracking with PostGIS geometry
- **Alert**: Emergency incidents and notifications
- **RestrictedZone**: Safe/risky area definitions
- **Authority**: Police dashboard users
- **Incident**: Emergency response tracking

### AI Model Configuration
```python
# Anomaly Detection
ISOLATION_FOREST_CONTAMINATION = 0.1
ISOLATION_FOREST_N_ESTIMATORS = 100

# Sequence Analysis
LSTM_SEQUENCE_LENGTH = 10
LSTM_HIDDEN_SIZE = 32
LSTM_LEARNING_RATE = 0.001

# Safety Scoring Weights
GEOFENCE_WEIGHT = 0.4
ANOMALY_WEIGHT = 0.3
SEQUENCE_WEIGHT = 0.3
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ for tourist safety and emergency response.**

## Local dev (without Docker)

- Python 3.11
- Install dependencies:

```pwsh
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Notes
- Supabase: set SUPABASE_URL and keys in `.env` to enable real auth.
- PostGIS: use `geography(Point, 4326)` and ST_Contains for geofencing queries.
- Models: persisted to `MODELS_DIR` via pickle (replace for prod with S3/Supabase Storage).
- Hyperledger: SDK placeholder; integrate when network available.
