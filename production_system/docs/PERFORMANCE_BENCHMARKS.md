# Performance Benchmarks

## Targets

- Image detection latency: < 100 ms
- Video processing throughput: >= 30 FPS
- API response p95: < 200 ms
- Dashboard first load: < 2 s
- Concurrent users: >= 1000
- Uptime SLA: 99.9%

## Baseline Measurement Template

| Metric                   | Target | Current | Status  |
| ------------------------ | -----: | ------: | ------- |
| detection_latency_ms_p95 |    100 |     TBD | pending |
| api_latency_ms_p95       |    200 |     TBD | pending |
| stream_fps               |     30 |     TBD | pending |
| dashboard_load_s         |    2.0 |     TBD | pending |
| uptime_percent           |   99.9 |     TBD | pending |

## Method

- Run k6 load tests for API.
- Use browser trace for frontend load.
- Measure stream jitter and dropped frames under load.
