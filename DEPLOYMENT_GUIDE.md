# Unified Space Debris Detection System - Deployment Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Local Development Setup](#local-development-setup)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes/Cloud Deployment](#kubernetescloud-deployment)
5. [Configuration](#configuration)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)

---

## System Overview

The Unified Space Debris Detection System is a production-grade AI platform for:
- **Real-time TLE data ingestion** from CelesTrak/Space-Track
- **Multi-modal trajectory prediction** using LSTM/Transformers
- **Conjunction risk assessment** with GNN-based orbital interactions
- **Collision avoidance recommendations** via automated maneuver planning
- **Kessler Syndrome modeling** and cascade risk prediction
- **3D orbital visualization** with real-time dashboard

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     TLE Data Sources                        │
│            CelesTrak (6h) | Space-Track (on-demand)        │
└──────────────────────────┬──────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│        Data Pipeline (TLE Feature Engineering)               │
│   tle_pipeline.py: Orbital elements → Derived features     │
└──────────────────────────┬──────────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
    ┌─────────┐    ┌────────────┐   ┌──────────────┐
    │LSTM     │    │Transformer │   │GNN Orbital   │
    │Predictor│───►│Predictor   │──►│Interactions  │
    └─────────┘    └────────────┘   └──────────────┘
         │                │                │
         └────────────────┼────────────────┘
                          ▼
    ┌────────────────────────────────┐
    │ Conjunction Risk Detector      │
    │ (Real-Time Pairwise Analysis)  │
    └────────────┬───────────────────┘
                 ▼
    ┌────────────────────────────────┐
    │ Real-Time Monitoring & Alerts  │
    │ (Redis Pub/Sub + Events)       │
    └────────────┬───────────────────┘
                 ▼
    ┌────────────────────────────────┐
    │ Dashboard & Visualization      │
    │ (3D Orbital 3D + Analytics)    │
    └────────────────────────────────┘
```

---

## Local Development Setup

### Prerequisites

- **Python 3.11+**
- **CUDA 12.1+** (for GPU acceleration)
- **Docker & Docker Compose** (for containerized deployment)
- **Git**
- **4GB+ RAM**, 2+ CPU cores

### Step 1: Clone Repository

```bash
git clone https://github.com/prem9879/unified-space-debris-detection.git
cd unified-space-debris-detection
```

### Step 2: Create Virtual Environment

```bash
# Create venv
python3.11 -m venv .venv

# Activate
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### Step 3: Install Dependencies

```bash
# Install base requirements
pip install -r requirements.txt

# Install development tools
pip install pytest pytest-cov black ruff mypy
```

### Step 4: Run Tests

```bash
# Run all tests
pytest tests/ -v --cov=src

# Specific test suite
pytest tests/test_setup.py::test_healthz_endpoint -v
```

### Step 5: Initialize TLE Data

```bash
# Fetch fresh TLE catalog
python -m src.data.tle_pipeline

# Output:
# ✓ Loaded 34,000 debris objects
# ⚠️  Found 150 high-risk pairs
```

### Step 6: Run Flask Dashboard

```bash
# Start development server
export FLASK_ENV=development
export USDD_PORT=5000
python webapp/flask_app.py

# Access at: http://localhost:5000
```

### Step 7: Run Integration Smoke Tests

```bash
# Test system components
python -m src.system_integration

# Output:
# ✓ ALL COMPONENTS INITIALIZED SUCCESSFULLY
# ✓ Updated catalog: 34,000 objects
# ✓ Dashboard snapshot generated
```

---

## Docker Deployment

### Quick Start (Development)

```bash
# Build all images
docker-compose build

# Start stack
docker-compose up -d

# Verify services
docker-compose ps

# Check logs
docker-compose logs api
docker-compose logs trajectory-worker
docker-compose logs conjunction-detector
```

### Production Deployment

#### 1. Build Production Images

```bash
# Build API
docker build -f deployment/Dockerfile.api -t debris-api:latest .

# Build Trajectory Worker
docker build -f deployment/Dockerfile.trajectory -t debris-trajectory:latest .

# Tag for registry
docker tag debris-api:latest myregistry.azurecr.io/debris-api:v1.0
docker tag debris-trajectory:latest myregistry.azurecr.io/debris-trajectory:v1.0

# Push to registry
docker push myregistry.azurecr.io/debris-api:v1.0
docker push myregistry.azurecr.io/debris-trajectory:v1.0
```

#### 2. Configure Environment

```bash
# Create .env file
cat > .env << EOF
# Database
DB_PASSWORD=YourSecurePassword123!
TS_PASSWORD=TimeSeriesPassword456!
REDIS_PASSWORD=RedisPassword789!

# External APIs
CELESTRAK_API_KEY=your_key_here
SPACE_TRACK_USER=your_username
SPACE_TRACK_PASS=your_password

# Grafana
GRAFANA_PASSWORD=GrafanaAdmin123!

# Cloud Registry
REGISTRY=myregistry.azurecr.io
EOF

chmod 600 .env
```

#### 3. Deploy with Docker Compose

```bash
# Production deployment
docker-compose -f docker-compose.yml up -d

# Scale services
docker-compose up -d --scale trajectory-worker=3

# Monitor stack
docker stats

# View logs
docker-compose logs -f api
```

#### 4. Health Checks

```bash
# API health
curl http://localhost:5000/healthz
# {"status":"ok", "version":"1.0"}

# Database health
docker-compose exec postgres pg_isready -U debris_admin

# Redis health
docker-compose exec redis redis-cli ping
# PONG
```

---

## Kubernetes/Cloud Deployment

### AWS EKS Deployment

#### Prerequisites

```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure

# Install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
```

#### Create EKS Cluster

```bash
# Create cluster with GPU support
eksctl create cluster \
  --name space-debris \
  --region us-east-1 \
  --version 1.28 \
  --nodegroup-name gpu-nodes \
  --node-type g4dn.12xlarge \
  --nodes 3 \
  --nodes-min 3 \
  --nodes-max 10
```

#### Deploy Application

```bash
# Create namespace
kubectl create namespace space-debris

# Create secrets
kubectl create secret generic usdd-secrets \
  --from-literal=DATABASE_PASSWORD=YourPassword \
  --from-literal=REDIS_PASSWORD=RedisPassword \
  --from-literal=SPACE_TRACK_USERNAME=username \
  --from-literal=SPACE_TRACK_PASSWORD=password \
  -n space-debris

# Apply Kubernetes manifests
kubectl apply -f deployment/kubernetes.yaml

# Verify deployment
kubectl get pods -n space-debris -w
```

#### Configure Ingress (ALB)

```bash
# Install AWS Load Balancer Controller
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=space-debris

# Check Ingress status
kubectl get ingress -n space-debris
```

#### Monitor with Prometheus

```bash
# Port forward to Prometheus
kubectl port-forward -n space-debris svc/prometheus 9090:9090

# Access: http://localhost:9090

# Port forward to Grafana
kubectl port-forward -n space-debris svc/grafana 3000:3000

# Access: http://localhost:3000 (admin/Admin123!)
```

### GCP GKE Deployment

```bash
# Create GKE cluster
gcloud container clusters create space-debris \
  --region us-central1 \
  --num-nodes 3 \
  --enable-autoscaling \
  --min-nodes 3 \
  --max-nodes 10 \
  --machine-type n1-standard-4 \
  --enable-ip-alias \
  --enable-stackdriver-kubernetes

# Get credentials
gcloud container clusters get-credentials space-debris --region us-central1

# Deploy application
kubectl apply -f deployment/kubernetes.yaml
```

---

## Configuration

### Environment Variables

```bash
# TLE Pipeline
TLE_UPDATE_INTERVAL=3600              # Seconds between TLE fetches
CELESTRAK_API_KEY=                    # Optional CelesTrak API key
SPACE_TRACK_USERNAME=                 # Required for Space-Track
SPACE_TRACK_PASSWORD=                 # Required for Space-Track

# Trajectory Prediction
MODEL_PATH=/app/models/trajectory_predictor.pt
BATCH_SIZE=32
DEVICE=cuda                           # cuda or cpu
PREDICTION_HORIZON=24                 # Hours

# Conjunction Detection
CONJUNCTION_ALERT_THRESHOLD=0.7       # Risk score threshold
ANALYSIS_WINDOW_HOURS=24              # Prediction window

# Database
DATABASE_URL=postgresql://debris_admin:password@postgres:5432/orbital_data
TIMESCALE_URL=postgresql://ts_admin:password@timescaledb:5432/orbital_telemetry

# Redis
REDIS_URL=redis://:password@redis:6379/0

# Logging
LOG_LEVEL=INFO                        # DEBUG, INFO, WARNING, ERROR
```

### ConfigMap (Kubernetes)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: usdd-config
  namespace: space-debris
data:
  TLE_UPDATE_INTERVAL: "3600"
  CONJUNCTION_ALERT_THRESHOLD: "0.7"
  TRAJECTORY_PREDICTION_HORIZON: "24"
  LOG_LEVEL: "INFO"
```

---

## Monitoring

### Prometheus Metrics

```bash
# Query active debris count
curl 'http://prometheus:9090/api/v1/query?query=usdd_debris_count'

# Conjunction detection rate
curl 'http://prometheus:9090/api/v1/query?query=usdd_conjunction_detections_total'

# Prediction latency (p99)
curl 'http://prometheus:9090/api/v1/query?query=histogram_quantile(0.99, usdd_prediction_latency_ms)'
```

### Grafana Dashboards

Pre-configured dashboards:
- **System Health**: API response time, error rates, database latency
- **Debris Analysis**: Orbital distribution, LEO/GEO/MEO density
- **Conjunction Alerts**: High-risk pairs, probability distribution
- **Resource Usage**: GPU utilization, memory, disk I/O
- **Kessler Syndrome**: Cascade risk projections, debris growth

### Application Insights (Azure)

```bash
# Connection string
APPINSIGHTS_INSTRUMENTATION_KEY=your_key_here

# View traces
az monitor log-analytics query \
  --workspace /subscriptions/xxx/resourcegroups/xxx/providers/microsoft.operationalinsights/workspaces/xxx \
  --analytics-query "traces | where message contains 'conjunction'"
```

---

## Troubleshooting

### Common Issues

#### 1. TLE Fetch Failures

```bash
# Check network
curl -I https://celestrak.org/NORAD/elements/debris.txt

# Verify Space-Track credentials
curl -u username:password https://www.space-track.org/basicspacedata/query 

# Manually fetch
python -c "from src.data.tle_pipeline import TLEFetcher; f = TLEFetcher(); print(f.fetch_celestrak_debris()[:100])"
```

#### 2. Database Connection Errors

```bash
# Test PostgreSQL
psql -h localhost -U debris_admin -d orbital_data -c "\dt"

# Check TimescaleDB
psql -h localhost -U ts_admin -d orbital_telemetry -c "SELECT * FROM time_bucket_gapfill('1 hour', time) LIMIT 1;"

# View logs
docker-compose logs postgres
```

#### 3. GPU Memory Issues

```bash
# Check GPU status
nvidia-smi

# Reduce batch size
export BATCH_SIZE=8

# Monitor GPU during prediction
watch -n 1 nvidia-smi
```

#### 4. High API Latency

```bash
# Check Redis connection
redis-cli PING

# Analyze slow queries
docker-compose exec postgres psql -U debris_admin -d orbital_data -c "\dt+"

# Scale API replicas
docker-compose up -d --scale api=5
```

#### 5. Kubernetes Pod Crashes

```bash
# Check pod events
kubectl describe pod <pod-name> -n space-debris

# View pod logs
kubectl logs <pod-name> -n space-debris

# Check resource requests/limits
kubectl top nodes
kubectl top pods -n space-debris
```

### Debug Mode

```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG

# Run with profiling
python -m cProfile -s cumulative src/system_integration.py

# Export profile
python -m py_spy record -o profile.svg -- python src/system_integration.py
```

---

## Performance Tuning

### API Server

```bash
# Increase worker count
gunicorn --workers 8 --worker-class sync --bind 0.0.0.0:5000 webapp.flask_app:app

# Enable async
gunicorn --workers 4 --worker-class gevent --bind 0.0.0.0:5000 webapp.flask_app:app
```

### Database

```sql
-- Create indexes for common queries
CREATE INDEX idx_debris_altitude ON orbital_data(altitude_km);
CREATE INDEX idx_debris_norad_id ON orbital_data(norad_cat_id);
CREATE INDEX idx_conjunction_risk ON orbital_data(conjunction_risk);

-- Analyze query plans
EXPLAIN ANALYZE SELECT * FROM orbital_data WHERE conjunction_risk > 0.7;
```

### Redis Caching

```python
# Cache conjunction results for 1 hour
redis_client.setex(f"conjunctions:{object_id}", 3600, json.dumps(conjunctions))

# Clear cache on new TLE updates
redis_client.flushdb(async_op=True)
```

---

## Security Hardening

### API Security

```python
# Enable CORS restrictions
CORS(app, resources={r"/api/*": {"origins": ["https://dashboard.example.com"]}})

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.config['RATELIMIT_STORAGE_URL'] = 'redis://localhost:6379'

# API authentication
@app.route('/api/predict', methods=['POST'])
@require_api_key
def predict():
    pass
```

### Network Security

```yaml
# Kubernetes NetworkPolicy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: usdd-network-policy
spec:
  podSelector: {}
  policyTypes: [ Ingress, Egress ]
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: space-debris
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: space-debris
    - podSelector:
        matchLabels:
          k8s-app: kube-dns
```

---

## Support & Contributing

- **Issues**: https://github.com/prem9879/unified-space-debris-detection/issues
- **Discussions**: https://github.com/prem9879/unified-space-debris-detection/discussions
- **Documentation**: https://debris-detection.readthedocs.io

---

**Version**: 1.0.0  
**Last Updated**: April 2026  
**Status**: Production Ready ✅
