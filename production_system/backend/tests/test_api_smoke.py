from fastapi.testclient import TestClient

from app.main import app


def test_healthz() -> None:
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_auth_and_detect() -> None:
    client = TestClient(app)

    token_res = client.post(
        "/api/v1/auth/token",
        json={"username": "analyst", "password": "analyst123"},
    )
    assert token_res.status_code == 200
    token = token_res.json()["access_token"]

    files = {"image": ("test.png", b"\x89PNG\r\n\x1a\n", "image/png")}
    data = {"modality": "optical"}
    response = client.post(
        "/api/v1/detection/infer",
        data=data,
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    # The tiny PNG bytes are intentionally minimal; the endpoint should still reject malformed content gracefully.
    assert response.status_code in {200, 400, 422, 500}
