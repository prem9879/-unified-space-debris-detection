# Production-Grade Space Debris Detection System

This module is a full-stack production scaffold for multi-modal space debris intelligence.

## What You Get

- FastAPI backend with JWT RBAC, rate limiting, WebSocket live stream, reporting APIs, and model management.
- Adapter-driven model runtime layer for YOLOv8, ViT, SAM, ConvLSTM, and Bayesian UQ with graceful fallback.
- React 18 + TypeScript frontend with Three.js orbit scene, live feed, upload flow, and confidence analytics.
- Docker Compose local stack: API, UI, Redis, PostgreSQL, MinIO.
- Kubernetes manifests with HPA and ingress-ready services.
- CI workflow template for lint/test/build.
- Architecture, deployment, API, and user-guide documentation.

## Quick Start

1. Backend

```bash
cd production_system/backend
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Optional GPU model runtime install:

```bash
pip install -r requirements-ml.txt
```

Set checkpoint paths with environment variables:

```bash
export YOLOV8_CHECKPOINT=models/yolov8.pt
export VIT_CHECKPOINT=models/vit.bin
export SAM_CHECKPOINT=models/sam.pth
export CONVLSTM_CHECKPOINT=models/convlstm.pt
export BAYESIAN_CHECKPOINT=models/bayesian.pt
```

1. Frontend

```bash
cd production_system/frontend
npm install
npm run dev
```

1. Full stack with containers

```bash
cd production_system
docker compose up --build
```

## Credentials (Dev)

- admin / admin123
- analyst / analyst123
- viewer / viewer123

## API Docs

- Swagger: <http://localhost:8000/docs>
- OpenAPI: <http://localhost:8000/openapi.json>

## Performance Targets

- Image detection latency: under 100 ms target
- API p95: under 200 ms target
- Stream updates: 2 Hz baseline, tuneable

## Output Artifacts Included

- Setup instructions: this README
- API docs: FastAPI OpenAPI + docs/API_REFERENCE.md
- User guide: docs/USER_GUIDE.md
- Architecture diagrams: docs/ARCHITECTURE.md
- Performance benchmark template: docs/PERFORMANCE_BENCHMARKS.md
- Deployment guide: docs/DEPLOYMENT_GUIDE.md
- CI/CD pipeline: .github/workflows/ci.yml

## Notes

This implementation provides production-ready architecture and interfaces with deterministic fallback inference so the platform runs without heavyweight model checkpoints. Plug in YOLOv8, ViT, SAM, ConvLSTM, and Bayesian models in app/services for full model serving.

## Benchmarks

```bash
cd production_system/backend
python scripts/benchmark_stub.py
```

For load testing, run k6 scripts under `production_system/loadtests`.
