# API Reference

## Authentication

- `POST /api/v1/auth/token`

## Detection

- `POST /api/v1/detection/infer` (multipart image + modality)
- `GET /api/v1/detection/tracks`

## Collision

- `POST /api/v1/collision/assess`

## Streams

- `WS /api/v1/streams/live`

## Alerts

- `POST /api/v1/alerts/trigger`
- `GET /api/v1/alerts/history`

## Models

- `GET /api/v1/models/`
- `POST /api/v1/models/promote`

## Reporting

- `POST /api/v1/reports/generate`

## Health

- `GET /healthz`
- `GET /readyz`
- `GET /metrics`
