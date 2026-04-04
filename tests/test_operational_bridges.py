"""Tests for real-ops bridges and low-compute risk screening."""

from __future__ import annotations

from datetime import datetime, timedelta

from src.data.tle_pipeline import RealTimeTLEStream
from src.deployment.operational_bridge import (
    MissionControlBridge,
    OpticalObservation,
    RadarObservation,
    SensorFusionBridge,
)


def test_shortlist_conjunction_candidates_reduces_pair_count() -> None:
    stream = RealTimeTLEStream()

    objects = []
    for i in range(120):
        objects.append(
            {
                "norad_cat_id": 10000 + i,
                "altitude_km": 700.0 + (i % 10) * 5.0,
                "inclination_deg": 97.0 + (i % 6) * 0.8,
                "mean_motion_rev_per_day": 14.8,
            }
        )

    candidates = stream.shortlist_conjunction_candidates(
        objects,
        altitude_window_km=40.0,
        inclination_window_deg=2.0,
        max_pairs=10_000,
    )

    theoretical_pairs = len(objects) * (len(objects) - 1) // 2
    assert len(candidates) > 0
    assert len(candidates) < theoretical_pairs


def test_sensor_fusion_bridge_updates_catalog() -> None:
    bridge = SensorFusionBridge()

    catalog = {
        25544: {
            "norad_cat_id": 25544,
            "altitude_km": 420.0,
            "inclination_deg": 51.6,
            "raan_deg": 12.0,
            "mean_anomaly_deg": 220.0,
        }
    }

    radar = [
        RadarObservation(
            norad_id=25544,
            altitude_km=425.0,
            inclination_deg=51.8,
            confidence=0.8,
            timestamp=datetime.now(),
        )
    ]
    optical = [
        OpticalObservation(
            norad_id=25544,
            raan_deg=12.5,
            mean_anomaly_deg=221.0,
            confidence=0.7,
            timestamp=datetime.now(),
        )
    ]

    result = bridge.fuse_into_catalog(catalog, radar, optical)

    assert result["status"] == "success"
    assert result["updated_objects"] == 1
    assert catalog[25544]["sensor_fused"] is True
    assert catalog[25544]["altitude_km"] > 420.0


def test_mission_control_requires_human_approval() -> None:
    bridge = MissionControlBridge(max_delta_v_km_s=0.05, require_human_approval=True)

    packet = bridge.build_maneuver_command(
        norad_id=25544,
        delta_v_rtn_km_s=(0.01, 0.01, 0.0),
        execute_at=datetime.now() + timedelta(minutes=15),
    )
    assert packet["status"] == "PENDING_APPROVAL"

    rejected = bridge.authorize_command(packet, approved_by=None)
    assert rejected["status"] == "REJECTED"

    approved = bridge.authorize_command(packet, approved_by="flight-director")
    assert approved["status"] == "AUTHORIZED"
