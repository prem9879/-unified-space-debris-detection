"""Core smoke tests for API behavior, security controls, and reproducibility hooks."""

from io import BytesIO

import pytest
from PIL import Image

from src.data.synthetic_dataset import make_demo_sample
from src.training.train_image_bench import build_reproducible_split_indices
from webapp import flask_app

app = flask_app.app


@pytest.fixture(autouse=True)
def clear_rate_limit_state(monkeypatch: pytest.MonkeyPatch):
    flask_app._RATE_LIMIT_STATE["window_start"] = 0.0
    flask_app._RATE_LIMIT_STATE["buckets"] = {}
    monkeypatch.delenv("USDD_REQUIRE_AUTH", raising=False)
    monkeypatch.delenv("USDD_API_KEYS", raising=False)
    monkeypatch.delenv("USDD_API_KEY", raising=False)
    monkeypatch.delenv("USDD_RATE_LIMIT_PER_MIN", raising=False)
    monkeypatch.delenv("USDD_ROLE_RATE_LIMITS_JSON", raising=False)
    monkeypatch.delenv("USDD_AUDIT_LOG_ENABLED", raising=False)
    yield


def test_demo_sample_shapes() -> None:
    sample = make_demo_sample()
    assert tuple(sample["radar"].shape) == (1, 1, 64, 64)
    assert tuple(sample["optical"].shape) == (1, 4, 3, 64, 64)
    assert tuple(sample["physics"].shape) == (1, 16)


def test_healthz_endpoint() -> None:
    client = app.test_client()
    res = client.get("/healthz")
    assert res.status_code == 200
    payload = res.get_json()
    assert isinstance(payload, dict)
    assert payload.get("status") == "ok"


def test_readiness_endpoint() -> None:
    client = app.test_client()
    res = client.get("/readyz")
    # Ready in a configured workspace, not ready in a fresh workspace without checkpoints.
    assert res.status_code in (200, 503)
    payload = res.get_json()
    assert isinstance(payload, dict)
    assert "status" in payload


def test_predict_endpoint_smoke() -> None:
    img = Image.new("RGB", (96, 96), (90, 120, 150))
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    client = app.test_client()
    data = {
        "optical": (buf, "sample.png"),
        "physics": "0.12,0.05,0.22,0.08,0.9,1.1,0.7,0.2,0.4,0.6,1.5,1.9,2.1,0.3,0.44,0.77",
        "operator_profile": "balanced",
    }
    res = client.post("/predict", data=data, content_type="multipart/form-data")
    assert res.status_code == 200
    payload = res.get_json()
    assert isinstance(payload, dict)
    assert "detect_probability" in payload
    assert "operational_summary" in payload


def test_ui_home_smoke() -> None:
    client = app.test_client()
    res = client.get("/")
    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert "heroLoadAllBtn" in body
    assert "runDemoBtn" in body
    assert "Model Benchmark" in body


def test_dataset_inventory_requires_folder() -> None:
    client = app.test_client()
    res = client.get("/dataset_inventory")
    assert res.status_code == 400


def test_predict_consistency_same_input() -> None:
    img = Image.new("RGB", (96, 96), (90, 120, 150))

    def _payload() -> dict:
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return {
            "optical": (buf, "sample.png"),
            "physics": "0.12,0.05,0.22,0.08,0.9,1.1,0.7,0.2,0.4,0.6,1.5,1.9,2.1,0.3,0.44,0.77",
            "operator_profile": "balanced",
        }

    client = app.test_client()
    res_1 = client.post("/predict", data=_payload(), content_type="multipart/form-data")
    res_2 = client.post("/predict", data=_payload(), content_type="multipart/form-data")
    assert res_1.status_code == 200
    assert res_2.status_code == 200
    p1 = res_1.get_json()
    p2 = res_2.get_json()
    assert isinstance(p1, dict)
    assert isinstance(p2, dict)
    assert abs(float(p1["detect_probability"]) - float(p2["detect_probability"])) < 1e-6


def test_calibration_report_smoke(tmp_path) -> None:
    debris_dir = tmp_path / "debris"
    non_debris_dir = tmp_path / "non_debris"
    debris_dir.mkdir(parents=True, exist_ok=True)
    non_debris_dir.mkdir(parents=True, exist_ok=True)

    for i in range(2):
        Image.new("RGB", (96, 96), (220, 220, 220)).save(debris_dir / f"d_{i}.png")
        Image.new("RGB", (96, 96), (20, 20, 20)).save(non_debris_dir / f"n_{i}.png")

    client = app.test_client()
    data = {
        "dataset_dir": str(tmp_path),
        "modality": "optical",
        "max_samples": "4",
        "bins": "10",
    }
    res = client.post("/calibration_report", data=data)
    assert res.status_code == 200
    payload = res.get_json()
    assert isinstance(payload, dict)
    assert int(payload.get("evaluated", 0)) >= 1
    metrics = payload.get("metrics", {})
    assert "ece" in metrics
    assert "brier_score" in metrics


def test_auth_required_blocks_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USDD_REQUIRE_AUTH", "1")
    monkeypatch.setenv("USDD_API_KEYS", '{"analyst-key":"analyst","admin-key":"admin"}')

    client = app.test_client()
    res = client.post("/predict", data={})
    assert res.status_code == 401


def test_role_based_access_for_admin_route(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USDD_REQUIRE_AUTH", "1")
    monkeypatch.setenv("USDD_API_KEYS", '{"analyst-key":"analyst","admin-key":"admin"}')

    client = app.test_client()
    res = client.post("/load_all_public_data", headers={"X-API-Key": "analyst-key"})
    assert res.status_code == 403


def test_rate_limit_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USDD_REQUIRE_AUTH", "1")
    monkeypatch.setenv("USDD_API_KEYS", '{"viewer-key":"viewer"}')
    monkeypatch.setenv("USDD_ROLE_RATE_LIMITS_JSON", '{"viewer":10}')

    client = app.test_client()
    for _ in range(10):
        res = client.get("/whoami", headers={"X-API-Key": "viewer-key"})
        assert res.status_code == 200

    blocked = client.get("/whoami", headers={"X-API-Key": "viewer-key"})
    assert blocked.status_code == 429


def test_reproducible_split_protocol() -> None:
    split_a = build_reproducible_split_indices(num_samples=100, seed=11)
    split_b = build_reproducible_split_indices(num_samples=100, seed=11)
    split_c = build_reproducible_split_indices(num_samples=100, seed=12)

    assert split_a == split_b
    assert split_a != split_c
    assert len(split_a["train"]) == 70
    assert len(split_a["val"]) == 15
    assert len(split_a["test"]) == 15
