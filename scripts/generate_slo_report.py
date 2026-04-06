"""Generate reliability SLO report (latency/error budget/memory) from API stress probes."""

from __future__ import annotations

import json
import statistics
import time
import tracemalloc
from pathlib import Path
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from webapp.flask_app import app  # noqa: E402


def _single_request(client) -> tuple[int, float]:
    start = time.perf_counter()
    img = Image.new("RGB", (96, 96), (90, 120, 150))
    from io import BytesIO

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
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return res.status_code, elapsed_ms


def main() -> None:
    output = Path("artifacts/reports/slo_report.json")
    output.parent.mkdir(parents=True, exist_ok=True)

    client = app.test_client()
    samples = 50

    latencies = []
    errors = 0

    tracemalloc.start()
    for _ in range(samples):
        status, elapsed = _single_request(client)
        latencies.append(elapsed)
        if status >= 500:
            errors += 1
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    p50 = statistics.median(latencies)
    p95 = sorted(latencies)[int(0.95 * (len(latencies) - 1))]
    error_budget = errors / max(1, samples)

    report = {
        "samples": samples,
        "latency_ms": {"p50": p50, "p95": p95, "max": max(latencies)},
        "error_budget": {"5xx_rate": error_budget},
        "memory": {"peak_bytes": int(peak)},
    }

    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
