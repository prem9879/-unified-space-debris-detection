# Rollback Plan

## Trigger Conditions

- gate failures in canary window
- SLO breach (latency/error budget)
- calibration drift beyond threshold

## Steps

1. Freeze traffic to candidate model.
2. Route 100% traffic to previous stable model.
3. Mark candidate release as blocked.
4. Open incident and attach signed audit evidence.
5. Re-run validation before re-deploy.
