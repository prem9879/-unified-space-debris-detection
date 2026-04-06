# Space Debris Command Center - Complete Running System

## ✅ SYSTEM STATUS: ALL OPERATIONAL

### Current Running Services

| Service | URL | Status | Purpose |
|---------|-----|--------|---------|
| **FastAPI Backend** | http://127.0.0.1:8000 | ✓ Running | Multi-modal debris detection API |
| **React Frontend** | http://localhost:5173 | ✓ Running | Real-time mission control dashboard |
| **API Documentation** | http://127.0.0.1:8000/docs | ✓ Interactive | Swagger UI for API exploration |
| **Health Check** | http://127.0.0.1:8000/healthz | ✓ OK | Service health status |
| **Metrics** | http://127.0.0.1:8000/metrics | ✓ Active | Prometheus metrics endpoint |

---

## 🚀 QUICK START

### Option 1: Batch Script (Windows)
```bash
START_SYSTEM.bat
```
Automatically launches both backend and frontend in separate terminals.

### Option 2: Manual Start (PowerShell)

**Terminal 1 - Backend:**
```powershell
cd "c:/Users/PREM DIWAN/Desktop/ml/unified-space-debris-detection/production_system/backend"
& "c:/Users/PREM DIWAN/Desktop/ml/.venv/Scripts/python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```powershell
cd "c:/Users/PREM DIWAN/Desktop/ml/unified-space-debris-detection/production_system/frontend"
npm run dev
```

**Terminal 3 - Status Monitor:**
```powershell
& "c:/Users/PREM DIWAN/Desktop/ml/.venv/Scripts/python.exe" "c:/Users/PREM DIWAN/Desktop/ml/unified-space-debris-detection/system_status.py"
```

---

## 🔐 Authentication

### Demo Credentials
- **Username:** `analyst`
- **Password:** `analyst123`

### Available Roles
| Role | Permissions | Use Case |
|------|-------------|----------|
| `analyst` | Full access to detection, collision analysis, alerts | Default operational user |
| `admin` | All analyst permissions + model management | System administration |
| `viewer` | Read-only access to dashboards and reports | Stakeholder visibility |

The frontend automatically logs in with the `analyst` role when loaded. No additional login required.

---

## 📊 API Endpoints Reference

### Authentication
```
POST /api/v1/auth/token
  Body: {"username": "analyst", "password": "analyst123"}
  Response: {"access_token": "...", "role": "analyst", "token_type": "bearer"}
```

### Object Detection
```
POST /api/v1/detection/infer
  - Image-based debris detection
  - Supports: FITS, RADAR, Optical modalities
  - Returns: Bounding boxes, confidence scores, segmentation masks

POST /api/v1/detection/infer_video
  - Frame sequence processing with trajectory tracking
  - Returns: Tracked object IDs, velocity estimates, frame-by-frame detections

GET /api/v1/detection/tracks
  - Live tracking data for all detected objects
```

### Collision Assessment
```
POST /api/v1/collision/assess
  Body: {"debris_id": "OBJ-001", "time_horizon_minutes": 60}
  Response: {
    "closest_approach_km": 0.5,
    "time_to_impact_minutes": 12,
    "collision_probability": 0.034,
    "risk_level": "MEDIUM"
  }
```

### Models & Registry
```
GET /api/v1/models/
  - List available ML models (YOLOv8, ViT, SAM, ConvLSTM, Bayesian)
  - Includes: version, architecture, active status

POST /api/v1/models/promote
  Body: {"name": "yolov8", "version": "8.2.0"}
  - Promote model version to production
  - Requires admin role
```

### Trajectory Prediction
```
POST /api/v1/trajectory/predict
  Body: {"object_id": "OBJ-001", "horizon_minutes": 120}
  Response: {
    "predicted_positions": [...],
    "confidence_intervals": [...],
    "uncertainty_method": "bayesian"
  }
```

### Monitoring & SLOs
```
GET /api/v1/monitoring/slo
  Response: {
    "image_detection_latency_ms_p95": 92,
    "api_latency_ms_p95": 164,
    "video_fps_min": 30,
    "uptime_sla": 99.9
  }
```

### Alerts
```
GET /api/v1/alerts/history
  - Retrieve all alert events (collisions, detections, system)
  
POST /api/v1/alerts/trigger
  Body: {"event_type": "COLLISION_WARNING", "object_id": "OBJ-001"}
  - Manually trigger alert with email/SMS/Slack/Discord notifications
```

### Reports
```
POST /api/v1/reports/generate
  Body: {"report_type": "COLLISION_RISK", "date_range": "2026-04-01,2026-04-06"}
  - Generate PDF reports with analysis and recommendations
```

### WebSocket Streams (Real-time)
```
WebSocket /api/v1/streams/live
  - Live tracking feed with velocity, risk percentages
  - Format: {"object_id": "OBJ-001", "velocity_km_s": 8.37, "risk_percentage": 54.1}
```

---

## 💻 Frontend Dashboard

### Key Features
- **Real-time 3D Orbit Visualization** - Earth sphere with debris orbits and tracking
- **Live Tracking Feed** - Velocity, risk assessment, object IDs
- **Drag-and-Drop Inference** - Upload images/videos for detection
- **Detection Confidence Chart** - Multi-class confidence visualization
- **Trajectory Timeline** - Playback of predicted trajectories
- **SLO Monitoring** - API latency, uptime tracking, model stack status
- **Theme Toggle** - Dark/light mode support

### Dashboard URL
```
http://localhost:5173
```

### Auto-Login
The dashboard automatically logs in with `analyst` credentials on load. No manual login required unless you want to use a different account.

---

## 🧪 Testing

### Health Check
```bash
curl -s http://127.0.0.1:8000/healthz | python -m json.tool
```

### API Test Script
```bash
python c:/Users/PREM/Desktop/ml/test_api.py
```

### System Status Check
```bash
python c:/Users/PREM/Desktop/ml/unified-space-debris-detection/system_status.py
```

### Manual API Test (PowerShell)
```powershell
$token = (Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/auth/token" -Method POST -ContentType "application/json" -Body '{"username":"analyst","password":"analyst123"}' | ConvertFrom-Json).access_token

$headers = @{"Authorization"="Bearer $token"}

Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/models/" -Headers $headers | ConvertFrom-Json
```

---

## 📁 Project Structure

```
unified-space-debris-detection/
├── production_system/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── main.py              # FastAPI entry point
│   │   │   ├── api/v1/              # API routes (auth, detection, collision, etc.)
│   │   │   ├── core/                # Config, security, rate limiting
│   │   │   ├── services/            # Business logic
│   │   │   └── schemas/             # Pydantic data validation
│   │   ├── requirements.txt         # Python dependencies
│   │   └── .env                     # Environment configuration
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── pages/DashboardPage.tsx
│   │   │   ├── components/          # React components
│   │   │   ├── services/api.ts      # API client
│   │   │   └── styles/
│   │   ├── package.json
│   │   └── vite.config.ts
│   ├── docker-compose.yml           # Multi-service containers (PostgreSQL, Redis, MinIO)
│   ├── infra/k8s/                   # Kubernetes manifests (deployment, HPA, ingress)
│   └── docs/                        # Architecture, API reference, deployment guides
├── system_status.py                 # Status dashboard script
└── test_api.py                      # API integration tests
```

---

## 🔧 Configuration

### Backend Config (`production_system/backend/app/core/config.py`)

```python
# API Settings
api_prefix = "/api/v1"
jwt_secret = "change-me-in-prod"
jwt_expire_minutes = 60

# Rate Limiting
max_requests_per_minute = 100
max_tracking_objects = 100

# Model Checkpoints
yolov8_checkpoint = "models/yolov8.pt"
vit_checkpoint = "models/vit.bin"
sam_checkpoint = "models/sam.pth"
convlstm_checkpoint = "models/convlstm.pt"
bayesian_checkpoint = "models/bayesian.pt"

# External Services (stubs for local dev)
redis_url = "redis://localhost:6379/0"
database_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/debris"
s3_endpoint_url = "http://localhost:9000"
```

### Frontend Config (`production_system/frontend/.env`)

```env
VITE_API_BASE=http://127.0.0.1:8000
```

---

## 📦 Dependencies Installed

### Python Backend
- **FastAPI 0.111.0** - Async web framework
- **Uvicorn 0.30.1** - ASGI application server
- **Pydantic 2.12.5** - Data validation
- **python-jose 3.3.0** - JWT authentication
- **passlib 1.7.4** - Password hashing
- **pydantic-settings 2.3.4** - Configuration management
- **prometheus-client 0.20.0** - Metrics collection
- **reportlab 4.4.10** - PDF report generation
- **matplotlib, pillow** - Visualization
- **websockets** - Real-time streaming

### JavaScript Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite 5.4** - Build tool with hot reload
- **Three.js** - 3D visualization
- **Chart.js** - Analytics charts
- **TailwindCSS** - Styling
- **Framer Motion** - Animations

---

## 🎯 Next Steps

1. **Test the Dashboard**: Open http://localhost:5173
2. **Upload Test Images**: Use the drag-and-drop area on "Upload Image or Frame" panel
3. **Check Predictions**: View results in real-time with confidence scores
4. **Monitor SLOs**: Watch API latency and model stack in "Operational Snapshot"
5. **Live Stream**: View real-time tracking feed on the right panel
6. **Read API Docs**: Visit http://127.0.0.1:8000/docs for interactive Swagger UI

---

## 🐛 Troubleshooting

### Backend won't start
- Check Python version: `python --version` (Should be 3.10+)
- Verify venv activated: Check for `(.venv)` in terminal prefix
- Install missing deps: `pip install -r production_system/backend/requirements.txt`

### Frontend won't load
- Clear browser cache: Ctrl+Shift+Delete
- Check npm installed: `npm --version`
- Reinstall deps: `npm install` in frontend directory

### API returns 401
- Credentials must be exactly: `analyst` / `analyst123`
- Token expires after 60 minutes (set in config)
- Check Authorization header format: `Bearer <token>`

### WebSocket connection fails
- Check CORS is enabled (it is, in main.py)
- Verify backend health: http://127.0.0.1:8000/healthz returns 200

---

## 📞 Support

For issues or questions:
1. Check system status: `python system_status.py`
2. Review API docs: http://127.0.0.1:8000/docs
3. Check backend logs in running terminal
4. Review frontend browser console (F12)

---

**System Generated:** 2026-04-06
**All Services:** ✓ Operational
**Status:** Ready for Operations
