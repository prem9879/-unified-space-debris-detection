from fastapi.testclient import TestClient

from app.main import app


def _token(client: TestClient) -> str:
    response = client.post("/api/v1/auth/token", json={"username": "analyst", "password": "analyst123"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_collision_assess() -> None:
    client = TestClient(app)
    token = _token(client)
    payload = {
        "object_a": "A",
        "object_b": "B",
        "position_a_km": [7000.0, 10.0, 5.0],
        "velocity_a_km_s": [0.0, 7.6, 0.0],
        "position_b_km": [7000.6, 10.2, 5.1],
        "velocity_b_km_s": [0.0, 7.58, 0.0],
    }
    res = client.post("/api/v1/collision/assess", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    body = res.json()
    assert body["closest_approach_km"] >= 0
    assert 0 <= body["risk_score"] <= 100
    assert body["risk_level"] in {"Low", "Medium", "High", "Critical"}


def test_collision_risk_endpoint_alias() -> None:
    client = TestClient(app)
    token = _token(client)
    payload = {
        "object_a": "SAT-1",
        "object_b": "DEBRIS-7",
        "position_a_km": [7000.0, 10.0, 5.0],
        "velocity_a_km_s": [0.0, 7.6, 0.0],
        "position_b_km": [7001.2, 10.6, 5.2],
        "velocity_b_km_s": [0.0, 7.55, 0.0],
        "ai_forecast_horizon_s": 3600,
        "ai_risk_weight": 0.4,
        "history_a": [
            {"t_s": 0.0, "x_km": 7000.0, "y_km": 10.0, "z_km": 5.0},
            {"t_s": 60.0, "x_km": 7000.08, "y_km": 10.45, "z_km": 5.02},
            {"t_s": 120.0, "x_km": 7000.16, "y_km": 10.9, "z_km": 5.05},
        ],
        "history_b": [
            {"t_s": 0.0, "x_km": 7001.2, "y_km": 10.6, "z_km": 5.2},
            {"t_s": 60.0, "x_km": 7001.25, "y_km": 11.0, "z_km": 5.22},
            {"t_s": 120.0, "x_km": 7001.31, "y_km": 11.4, "z_km": 5.25},
        ],
    }
    res = client.post("/api/v1/collision/collision-risk", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    body = res.json()
    assert body["object_a"] == "SAT-1"
    assert body["object_b"] == "DEBRIS-7"
    assert "Closest Distance" in body["summary"]
    assert body["time_to_collision_hours"] >= 0
    assert body["fusion_method"] in {"gru-lstm-transformer-adapter", "fallback-relative-velocity"}


def test_trajectory_predict() -> None:
    client = TestClient(app)
    token = _token(client)
    payload = {
        "object_id": "OBJ-001",
        "history": [
            {"t_s": 0.0, "x_km": 100.0, "y_km": 5.0, "z_km": 2.0},
            {"t_s": 30.0, "x_km": 101.5, "y_km": 5.2, "z_km": 2.1},
        ],
        "horizon_s": 120,
    }
    res = client.post("/api/v1/detection/trajectory", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    body = res.json()
    assert body["method"].startswith("convlstm")
    assert len(body["predicted"]) > 0
