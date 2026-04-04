"""Operational bridges for real sensor ingestion and controlled maneuver commanding.

This module focuses on production interfaces that move the system beyond pure
simulation:
- Ingesting radar/optical observations from external pipelines
- Fusing observations into the tracked catalog
- Producing approval-gated maneuver command packets
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math
from typing import Any


@dataclass(frozen=True)
class RadarObservation:
    """Radar track measurement."""

    norad_id: int
    altitude_km: float
    inclination_deg: float
    confidence: float
    timestamp: datetime


@dataclass(frozen=True)
class OpticalObservation:
    """Optical track measurement."""

    norad_id: int
    raan_deg: float
    mean_anomaly_deg: float
    confidence: float
    timestamp: datetime


class SensorFusionBridge:
    """Fuse external sensor tracks into orbital catalog entries."""

    def fuse_into_catalog(
        self,
        catalog: dict[int, dict[str, Any]],
        radar_observations: list[RadarObservation],
        optical_observations: list[OpticalObservation],
    ) -> dict[str, Any]:
        """Apply confidence-weighted updates from radar/optical tracks.

        Args:
            catalog: Debris catalog indexed by NORAD id.
            radar_observations: Radar updates with altitude and inclination.
            optical_observations: Optical updates with RAAN and mean anomaly.

        Returns:
            Summary of applied updates.
        """
        if not catalog:
            return {"updated_objects": 0, "status": "empty_catalog"}

        updates_by_object: dict[int, dict[str, float]] = {}

        for obs in radar_observations:
            if obs.norad_id not in catalog:
                continue
            state = updates_by_object.setdefault(obs.norad_id, {})
            state["altitude_km"] = self._blend(
                catalog[obs.norad_id].get("altitude_km", obs.altitude_km),
                obs.altitude_km,
                obs.confidence,
            )
            state["inclination_deg"] = self._blend(
                catalog[obs.norad_id].get("inclination_deg", obs.inclination_deg),
                obs.inclination_deg,
                obs.confidence,
            )

        for obs in optical_observations:
            if obs.norad_id not in catalog:
                continue
            state = updates_by_object.setdefault(obs.norad_id, {})
            state["raan_deg"] = self._blend(
                catalog[obs.norad_id].get("raan_deg", obs.raan_deg),
                obs.raan_deg,
                obs.confidence,
            )
            state["mean_anomaly_deg"] = self._blend(
                catalog[obs.norad_id].get("mean_anomaly_deg", obs.mean_anomaly_deg),
                obs.mean_anomaly_deg,
                obs.confidence,
            )

        for norad_id, update in updates_by_object.items():
            catalog[norad_id].update(update)
            catalog[norad_id]["sensor_fused"] = True
            catalog[norad_id]["last_sensor_update"] = datetime.now().isoformat()

        return {
            "status": "success",
            "updated_objects": len(updates_by_object),
            "radar_samples": len(radar_observations),
            "optical_samples": len(optical_observations),
        }

    @staticmethod
    def _blend(current: float, measured: float, confidence: float) -> float:
        alpha = max(0.0, min(1.0, float(confidence)))
        return (1.0 - alpha) * float(current) + alpha * float(measured)


class MissionControlBridge:
    """Generate maneuver command packets with mandatory approval gates."""

    def __init__(
        self,
        max_delta_v_km_s: float = 0.05,
        require_human_approval: bool = True,
    ):
        self.max_delta_v_km_s = max_delta_v_km_s
        self.require_human_approval = require_human_approval

    def build_maneuver_command(
        self,
        norad_id: int,
        delta_v_rtn_km_s: tuple[float, float, float],
        execute_at: datetime,
    ) -> dict[str, Any]:
        """Build command packet in a ground-segment-friendly JSON structure."""
        magnitude = math.sqrt(sum(axis * axis for axis in delta_v_rtn_km_s))
        if magnitude > self.max_delta_v_km_s:
            raise ValueError(
                f"delta-v magnitude {magnitude:.4f} exceeds safety cap {self.max_delta_v_km_s:.4f}"
            )

        return {
            "schema": "usdd.maneuver.v1",
            "norad_id": int(norad_id),
            "delta_v_rtn_km_s": {
                "radial": float(delta_v_rtn_km_s[0]),
                "tangential": float(delta_v_rtn_km_s[1]),
                "normal": float(delta_v_rtn_km_s[2]),
            },
            "delta_v_magnitude_km_s": float(magnitude),
            "execute_at": execute_at.isoformat(),
            "approval_required": self.require_human_approval,
            "status": "PENDING_APPROVAL" if self.require_human_approval else "READY",
            "created_at": datetime.now().isoformat(),
        }

    def authorize_command(
        self,
        command_packet: dict[str, Any],
        approved_by: str | None,
    ) -> dict[str, Any]:
        """Authorize or reject command packet based on configured policy."""
        packet = dict(command_packet)

        if self.require_human_approval and not approved_by:
            packet["status"] = "REJECTED"
            packet["rejection_reason"] = "missing_human_approval"
            return packet

        packet["status"] = "AUTHORIZED"
        packet["approved_by"] = approved_by or "system"
        packet["approved_at"] = datetime.now().isoformat()
        return packet
