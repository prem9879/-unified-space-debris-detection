# Uptime and Incident Response

## SLO targets

- p50 latency target
- p95 latency target
- 5xx error budget ceiling

## Monitoring

- health/readiness probes
- SLO report generator (`scripts/generate_slo_report.py`)
- anomaly alerts for request storms

## Incident workflow

1. detect and classify severity
2. stabilize service (rollback/circuit control)
3. capture signed audit traces
4. root-cause and corrective action
