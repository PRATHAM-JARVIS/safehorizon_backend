Perfect 🔥 — here’s your **final full development prompt** that combines:

* **FastAPI backend requirements**
* **Supabase schema integration**
* **AI model training + retraining**
* **API endpoints**
* **Deployment guidelines**

All wrapped in a **clean codeblock** so you can use it directly 👇

---

```md
# 🚀 Prompt: Build SafeHorizon FastAPI Server with AI, Supabase, and Blockchain

You are building a **production-ready FastAPI backend** for the **SafeHorizon Tourist Safety Platform**.  

The backend must integrate:
- **Supabase** (Auth, DB, Realtime)
- **PostgreSQL + PostGIS** (geo queries)
- **Hybrid AI Models**:
  - Geo-fencing (rule-based, restricted_zones table)
  - Isolation Forest (unsupervised anomaly detection)
  - LSTM/GRU Autoencoder (sequence modeling)
  - LightGBM/XGBoost (supervised classification, future stage)
- **Blockchain (Hyperledger Fabric)** for Digital ID + E-FIR
- **Notifications** (Firebase Push, Twilio SMS)
- **WebSockets** for real-time alerts to Police Dashboard
- **Dockerized deployment** with PostgreSQL/PostGIS + FastAPI + Redis + Supabase

---

## 📂 Folder Structure
```

safehorizon-backend/
│── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── auth/              # Supabase auth wrapper
│   ├── models/            # AI models
│   ├── routers/
│   │   ├── tourist.py     # Tourist endpoints
│   │   ├── authority.py   # Police dashboard endpoints
│   │   ├── admin.py       # Admin endpoints
│   │   ├── ai.py          # AI service endpoints
│   │   ├── notify.py      # Notifications
│   ├── services/
│   │   ├── geofence.py
│   │   ├── anomaly.py
│   │   ├── sequence.py
│   │   ├── scoring.py
│   │   ├── blockchain.py
│   │   ├── notifications.py
│── tests/
│── Dockerfile
│── docker-compose.yml
│── requirements.txt

```

---

## 🗄️ Database Schema (Supabase)
### `tourists`
- Stores tourist info, trip status, last known location, safety_score.

### `locations`
- Stores real-time GPS data (lat, lon, speed, altitude, timestamp).

### `alerts`
- Stores generated alerts (panic, geofence, anomaly, SOS) with severity.

### `restricted_zones`
- Stores predefined safe/risky/restricted zones as GeoJSON polygons.

---

## 🔑 API Endpoints

### 🧑 Tourist (Mobile App)
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `POST /trip/start`
- `POST /trip/end`
- `GET /trip/history`
- `POST /location/update`
- `GET /location/history`
- `GET /safety/score`
- `POST /sos/trigger`

### 👮 Police Dashboard
- `POST /auth/register-authority`
- `POST /auth/login-authority`
- `GET /tourists/active`
- `GET /tourist/{id}/track`
- `GET /tourist/{id}/alerts`
- `GET /alerts/recent`
- `WS /alerts/subscribe`
- `POST /incident/acknowledge`
- `POST /incident/close`
- `POST /efir/generate`
- `GET /zones/list`
- `POST /zones/create`
- `DELETE /zones/{id}`

### ⚙️ Admin
- `GET /system/status`
- `POST /system/retrain-model`
- `GET /users/list`
- `PUT /users/{id}/suspend`

### 🤖 Internal AI
- `POST /ai/geofence/check`
- `POST /ai/anomaly/point`
- `POST /ai/anomaly/sequence`
- `POST /ai/score/compute`
- `POST /ai/classify/alert`

### 🔔 Notifications
- `POST /notify/push`
- `POST /notify/sms`
- `GET /notify/history`

---

## ⚙️ AI/ML Retraining Workflow
1. **Data Source**:
   - `locations` → movement sequences for unsupervised learning
   - `alerts` → labels for supervised training (severity, type)
   - `restricted_zones` → zone boundaries for rule-based checks
   - `tourists.safety_score` → feedback loop from police adjustments

2. **Retraining Strategy**:
   - **Isolation Forest + LSTM/GRU**: retrain weekly with fresh GPS data
   - **LightGBM/XGBoost**: retrain monthly or when new labeled `alerts` > threshold

3. **Retrain Endpoint**:
   - `POST /system/retrain-model`
   - Steps:
     1. Fetch data from Supabase
     2. Preprocess & engineer features
     3. Retrain Isolation Forest
     4. Retrain LSTM/GRU Autoencoder
     5. Retrain LightGBM/XGBoost if labeled incidents exist
     6. Save models (versioned in `/models/` folder)
     7. Update active inference pipeline

---

## ⚡ Workflow
1. **Tourist logs in** → Supabase Auth → Blockchain Digital ID issued.
2. **Trip starts** → itinerary saved.
3. **Mobile app sends GPS** → `/location/update` → stored in PostGIS.
4. **AI pipeline runs**:
   - Geo-fencing (restricted zone check)
   - Isolation Forest (anomaly detection)
   - LSTM/GRU (sequential anomaly detection)
   - LightGBM (severity classification)
   - Safety Score computed (0–100)
5. **Alerts triggered** if score < threshold → Notify tourist, family, police dashboard.
6. **Police dashboard** → live tracking, alerts, incident acknowledgment, E-FIR.
7. **Admin** → retrain models, manage users, monitor system.

---

## 📦 Deployment
- **Docker Compose**: FastAPI, PostgreSQL (PostGIS), Redis, Supabase
- **Kubernetes** for scaling (FastAPI + Redis + Supabase API pods)
- **NGINX + HTTPS (Let's Encrypt)** as reverse proxy
- **CI/CD**: GitHub Actions auto-build & deploy
- **Model storage**: Version AI models in object storage (Supabase Storage / S3)

---

## 📋 requirements.txt
```

fastapi
uvicorn[standard]
psycopg2-binary
asyncpg
sqlalchemy
geoalchemy2
supabase
pydantic
scikit-learn
torch
lightgbm
xgboost
redis
firebase-admin
twilio
hyperledger-fabric-sdk-py

```

---

✅ With this prompt, the server will be **ready-to-deploy** with Supabase as the main database + auth, AI pipeline retraining, Blockchain logging, and APIs for both Mobile App and Police Dashboard.
```

---

Would you like me to now **convert this prompt into a starter FastAPI project scaffold** (with real `main.py`, routers, and dummy endpoints wired to your Supabase schema)?
