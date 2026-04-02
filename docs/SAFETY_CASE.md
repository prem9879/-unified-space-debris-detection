# Safety Case

## Scope

Decision-support only, not autonomous mission execution.

## Hazards

- false positives causing unnecessary escalations
- false negatives missing critical debris events
- calibration drift over time
- adversarial or malformed input artifacts

## Controls

- calibration acceptance gates
- human-in-the-loop escalation policy
- signed audit logs and retention
- role-based controls + lockout/abuse detection

## Residual risk

Any Tier-3 action requires independent human verification and external sensor confirmation.
