from __future__ import annotations

import numpy as np

from app.schemas.collision import CollisionRequest, CollisionResponse


class CollisionService:
    def assess(self, payload: CollisionRequest) -> CollisionResponse:
        pa = np.asarray(payload.position_a_km, dtype=np.float64)
        va = np.asarray(payload.velocity_a_km_s, dtype=np.float64)
        pb = np.asarray(payload.position_b_km, dtype=np.float64)
        vb = np.asarray(payload.velocity_b_km_s, dtype=np.float64)

        rel_p = pb - pa
        rel_v = vb - va
        rel_speed_sq = float(np.dot(rel_v, rel_v)) + 1e-9

        t_star = max(0.0, -float(np.dot(rel_p, rel_v)) / rel_speed_sq)
        closest_vec = rel_p + rel_v * t_star
        closest_km = float(np.linalg.norm(closest_vec))

        probability = float(np.clip(np.exp(-closest_km / 5.0), 0.0, 1.0))
        maneuver = (
            "Raise orbit by 2-5 km and phase shift burn" if probability > 0.6 else "Track and monitor; no immediate burn"
        )

        return CollisionResponse(
            closest_approach_km=round(closest_km, 6),
            time_to_impact_s=round(t_star, 3),
            collision_probability=round(probability, 5),
            suggested_maneuver=maneuver,
        )
