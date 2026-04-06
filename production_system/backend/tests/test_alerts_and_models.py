from fastapi.testclient import TestClient

from app.main import app


def _admin_token(client: TestClient) -> str:
    response = client.post("/api/v1/auth/token", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_alert_trigger_and_history() -> None:
    client = TestClient(app)
    token = _admin_token(client)

    send = client.post(
        "/api/v1/alerts/trigger",
        json={"channel": "slack", "risk": 0.82, "message": "High-risk conjunction candidate"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert send.status_code == 200

    hist = client.get("/api/v1/alerts/history", headers={"Authorization": f"Bearer {token}"})
    assert hist.status_code == 200
    assert len(hist.json()["events"]) >= 1


def test_models_list() -> None:
    client = TestClient(app)
    token = _admin_token(client)
    response = client.get("/api/v1/models/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()["models"]) >= 3
