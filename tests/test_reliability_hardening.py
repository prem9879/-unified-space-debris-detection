"""Reliability hardening tests: repeated, malformed, timeout-like storms, and concurrency."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

from webapp.flask_app import app


def _predict_once(client) -> int:
    img = Image.new("RGB", (96, 96), (90, 120, 150))
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    res = client.post(
        "/predict",
        data={
            "optical": (buf, "sample.png"),
            "physics": "0.12,0.05,0.22,0.08,0.9,1.1,0.7,0.2,0.4,0.6,1.5,1.9,2.1,0.3,0.44,0.77",
            "operator_profile": "balanced",
        },
        content_type="multipart/form-data",
    )
    return res.status_code


def test_repeated_requests_stable() -> None:
    client = app.test_client()
    statuses = [_predict_once(client) for _ in range(8)]
    assert all(s == 200 for s in statuses)


def test_malformed_image_rejected_gracefully() -> None:
    client = app.test_client()
    res = client.post(
        "/predict",
        data={"optical": (BytesIO(b"not-an-image"), "bad.png")},
        content_type="multipart/form-data",
    )
    assert res.status_code in (400, 500)


def test_timeout_storm_like_sequence_no_crash() -> None:
    client = app.test_client()
    for _ in range(20):
        res = client.get("/healthz")
        assert res.status_code == 200


def test_concurrent_single_and_batch_paths() -> None:
    client = app.test_client()

    def run_single() -> int:
        return _predict_once(client)

    def run_batch() -> int:
        res = client.post(
            "/predict_dataset",
            data={
                "dataset_dir": "c:/Users/PREM DIWAN/Desktop/ml/images",
                "modality": "optical",
                "max_samples": "2",
            },
        )
        return res.status_code

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(
            pool.map(lambda fn: fn(), [run_single, run_single, run_batch, run_single])
        )

    assert all(code in (200, 400) for code in results)


def test_generate_slo_report_script() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "generate_slo_report.py"
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr

    report_path = repo_root / "artifacts" / "reports" / "slo_report.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert "latency_ms" in report
    assert "error_budget" in report
