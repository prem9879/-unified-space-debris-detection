# Deployment Guide

## Local Containers

```bash
cd production_system
docker compose up --build
```

## Kubernetes

```bash
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/backend.yaml
kubectl apply -f infra/k8s/frontend.yaml
```

## Blue-Green Strategy

- Deploy `debris-api-green` alongside `debris-api-blue`.
- Shift ingress traffic with weighted routing.
- Run smoke checks and rollback if SLOs degrade.

## Backup Strategy

- PostgreSQL snapshot daily.
- MinIO object versioning + lifecycle policy.
- Restore drill monthly.
