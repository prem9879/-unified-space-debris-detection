from __future__ import annotations

import numpy as np

from app.schemas.collision import CollisionRequest, CollisionResponse
from app.services.sequence_fusion import SequenceFusionEngine


class CollisionService:
    def __init__(self) -> None:
        self._fusion = SequenceFusionEngine()

    @staticmethod
    def _risk_level(score: float) -> str:
        if score >= 75.0:
            return "Critical"
        if score >= 50.0:
            return "High"
        if score >= 25.0:
            return "Medium"
        return "Low"

    def assess(self, payload: CollisionRequest) -> CollisionResponse:
        pa = np.asarray(payload.position_a_km, dtype=np.float64)
        va = np.asarray(payload.velocity_a_km_s, dtype=np.float64)
        pb = np.asarray(payload.position_b_km, dtype=np.float64)
        vb = np.asarray(payload.velocity_b_km_s, dtype=np.float64)

        rel_p = pb - pa
        rel_v = vb - va
        rel_speed = float(np.linalg.norm(rel_v))
        rel_speed_sq = rel_speed**2 + 1e-9

        t_star = max(0.0, -float(np.dot(rel_p, rel_v)) / rel_speed_sq)
        closest_vec = rel_p + rel_v * t_star
        closest_km = float(np.linalg.norm(closest_vec))

        # Physics term: exponential miss-distance decay with velocity sensitivity.
        physics_probability = float(
            np.clip(np.exp(-closest_km / 7.5) * np.clip(rel_speed / 12.0, 0.2, 1.0), 0.0, 1.0)
        )

        fused_rel_velocity, fusion_meta = self._fusion.fused_relative_velocity(
            history_a=payload.history_a,
            history_b=payload.history_b,
            fallback_rel_velocity=rel_v,
        )
        ai_probability = self._fusion.ai_probability_from_forecast(
            relative_position=rel_p,
            fused_relative_velocity=fused_rel_velocity,
            horizon_s=payload.ai_forecast_horizon_s,
        )

        blend = float(np.clip(payload.ai_risk_weight, 0.0, 1.0))
        probability = float(np.clip((1.0 - blend) * physics_probability + blend * ai_probability, 0.0, 1.0))

        inverse_distance_term = 1.0 / (1.0 + closest_km)
        velocity_term = np.clip(rel_speed / 12.0, 0.0, 1.0)
        risk_score = float(np.clip(100.0 * (0.62 * probability + 0.23 * velocity_term + 0.15 * inverse_distance_term), 0.0, 100.0))
        risk_level = self._risk_level(risk_score)
        hours_to_collision = float(t_star / 3600.0)

        if risk_level in {"Critical", "High"}:
            maneuver = "Immediate conjunction review: execute phased burn window and covariance update."
        elif risk_level == "Medium":
            maneuver = "Track closely and schedule secondary observation before maneuver commitment."
        else:
            maneuver = "Continue monitoring and refresh trajectory forecast on next telemetry cycle."

        summary = (
            f"{payload.object_a} vs {payload.object_b} | Closest Distance: {closest_km:.3f} km | "
            f"Time to collision: {hours_to_collision:.3f} h | Risk Score: {risk_score:.2f}% | Risk Level: {risk_level}"
        )

        return CollisionResponse(
            object_a=payload.object_a,
            object_b=payload.object_b,
            closest_approach_km=round(closest_km, 6),
            time_to_impact_s=round(t_star, 3),
            relative_velocity_km_s=round(rel_speed, 6),
            physics_collision_probability=round(physics_probability, 5),
            ai_collision_probability=round(ai_probability, 5),
            collision_probability=round(probability, 5),
            risk_score=round(risk_score, 3),
            risk_level=risk_level,
            fusion_method=str(fusion_meta.get("fusion_method", "fallback-relative-velocity")),
            time_to_collision_hours=round(hours_to_collision, 6),
            summary=summary,
            suggested_maneuver=maneuver,
        )
