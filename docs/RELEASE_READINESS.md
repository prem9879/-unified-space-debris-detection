# Release Readiness

This repository uses a readiness pack to consolidate scientific, reliability, security, and operational evidence.

## Required artifacts

- immutable dataset manifest
- hard-negative / OOD index
- calibration report with acceptance gates
- reliability SLO report
- security policy output
- benchmark card
- release readiness pack

## Release criteria

1. Scientific package must include manifest digest, class balance, split protocol, confidence intervals, and false-positive cost analysis.
2. Reliability package must include p50/p95 latency, error budget, and memory ceiling.
3. Security package must use managed-identity or Key Vault-backed key rings in production profile.
4. External blind evaluation protocol must be available for third-party validation.
5. Incident response and rollback plan must be documented.

## Operational rule

If any gate fails, the release remains in review until a new readiness pack is generated.
