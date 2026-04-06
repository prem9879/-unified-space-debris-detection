# Architecture

## System Overview (Mermaid)

```mermaid
flowchart LR
  subgraph UI[React + Three.js Dashboard]
    A1[Live Orbit Scene]
    A2[Upload + Detection Overlay]
    A3[Alerts + Analytics]
  end

  subgraph API[FastAPI Backend]
    B1[Auth + RBAC]
    B2[Detection Service\nYOLOv8/ViT/SAM]
    B3[Trajectory + Collision Engine\nConvLSTM + Physics]
    B4[Model Registry + A/B]
    B5[Alert Engine]
    B6[Reporting Engine]
    B7[WebSocket Stream]
  end

  subgraph Data[Data Plane]
    C1[(PostgreSQL)]
    C2[(Redis)]
    C3[(MinIO/S3)]
  end

  subgraph External[External Sources]
    D1[NASA TLE]
    D2[Space-Track]
    D3[ESA Feeds]
  end

  UI <--> API
  API --> Data
  External --> API
```

## Core Runtime Path

1. Incoming frame or video chunk enters detection pipeline.
2. Detection boxes and uncertainty scores are emitted.
3. Tracker updates object histories and velocity vectors.
4. Collision engine computes closest approach and impact time.
5. Alerts and analytics are pushed via WebSocket + persisted stores.
