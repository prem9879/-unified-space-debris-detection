"""Tests for the consolidated release readiness pack."""

from __future__ import annotations

import json

from scripts.generate_readiness_pack import build_pack


def test_build_readiness_pack(tmp_path) -> None:
    manifest = tmp_path / "manifest.json"
    benchmark = tmp_path / "benchmark.json"
    calibration = tmp_path / "calibration.json"
    slo = tmp_path / "slo.json"
    security = tmp_path / "security.json"
    hard_negative = tmp_path / "hard_negative.json"
    output = tmp_path / "readiness.json"

    manifest.write_text(
        json.dumps(
            {
                "manifest_digest": "abc123",
                "split_protocol": {"seed": 42},
                "class_counts": {"debris": 4, "non_debris": 4},
            }
        ),
        encoding="utf-8",
    )
    benchmark.write_text(
        json.dumps({"results": {"resnet18": {"f1": 0.9}}}), encoding="utf-8"
    )
    calibration.write_text(
        json.dumps({"acceptance_gates": {"passed": True}}), encoding="utf-8"
    )
    slo.write_text(json.dumps({"latency_ms": {"p50": 10, "p95": 20}}), encoding="utf-8")
    security.write_text(json.dumps({"auth_required": True}), encoding="utf-8")
    hard_negative.write_text(
        json.dumps({"summary": {"total_files": 12}}), encoding="utf-8"
    )

    pack = build_pack(
        manifest, benchmark, calibration, slo, security, hard_negative, output
    )

    assert output.exists()
    assert pack["status"] == "release_ready"
    assert pack["gates"]["scientific"] is True
    assert pack["gates"]["reliability"] is True
    assert pack["gates"]["security"] is True
    assert pack["gates"]["deployment"] is True
    assert pack["gates"]["hard_negatives"] is True
    assert pack["scores_target"]["scientific_credibility"] == 9.0
