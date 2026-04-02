# Read Start Here

## Status

The dashboard is running locally and the repository now includes a release-readiness evidence bundle for scientific, reliability, security, and operations review.

## Live Dashboard

[Open the dashboard](http://127.0.0.1:7868)

## What Changed

- RGB channel analysis with fixed-size histogram rendering.
- Immutable dataset manifest and split protocol support.
- Release-readiness pack generation.
- Security policy, SLO, and hard-negative indexing artifacts.
- Blind external evaluation package and procurement docs.

## Evidence Bundle

- [Readiness scorecard](docs/READINESS_SCORECARD.md)
- [Release readiness policy](docs/RELEASE_READINESS.md)
- [Safety case](docs/SAFETY_CASE.md)
- [Security architecture brief](docs/SECURITY_ARCHITECTURE_BRIEF.md)
- [Uptime and incident response](docs/UPTIME_INCIDENT_RESPONSE.md)
- [Blind evaluation protocol](external_validation/BLIND_EVAL_PROTOCOL.md)

## Run These

```bash
python scripts/generate_security_policy.py
python scripts/generate_slo_report.py
python scripts/generate_readiness_pack.py
```

## Practical Next Step

Use a real labeled debris dataset with a frozen manifest, then regenerate the benchmark card and readiness pack before any external review.
