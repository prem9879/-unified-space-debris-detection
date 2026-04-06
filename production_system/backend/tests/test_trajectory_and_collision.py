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
