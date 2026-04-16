"""Integration tests for auth, billing, and security launch-readiness flows."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

import pytest

from webapp import flask_app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "auth.sqlite3"
    monkeypatch.setenv("USDD_AUTH_DB_PATH", str(db_path))
    monkeypatch.setenv("USDD_LOGIN_LOCK_THRESHOLD", "3")
    monkeypatch.setenv("USDD_LOGIN_LOCK_SECONDS", "120")

    flask_app.app.config["TESTING"] = True
    flask_app.app.config["USDD_ROOT"] = str(tmp_path)

    with flask_app.app.test_client() as test_client:
        yield test_client


def _read_mailbox(tmp_path: Path) -> list[dict[str, str]]:
    mailbox = tmp_path / "logs" / "auth_mailbox.log"
    if not mailbox.exists():
        return []
    rows: list[dict[str, str]] = []
    for line in mailbox.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def _extract_path(url: str) -> str:
    parsed = urlparse(url)
    if parsed.query:
        return f"{parsed.path}?{parsed.query}"
    return parsed.path


def _signup(client, email: str = "ops@example.com", password: str = "Password123"):
    return client.post(
        "/signup",
        data={
            "email": email,
            "password": password,
            "confirm_password": password,
        },
    )


def test_signup_verify_login_and_password_reset(client, tmp_path: Path):
    signup_res = _signup(client)
    assert signup_res.status_code == 200

    mail = _read_mailbox(tmp_path)
    verify_rows = [row for row in mail if row.get("kind") == "verify_email"]
    assert verify_rows

    verify_path = _extract_path(verify_rows[-1]["link"])

    login_before_verify = client.post(
        "/login",
        data={"email": "ops@example.com", "password": "Password123"},
    )
    assert login_before_verify.status_code == 403

    verify_res = client.get(verify_path)
    assert verify_res.status_code == 200

    login_res = client.post(
        "/login",
        data={"email": "ops@example.com", "password": "Password123"},
    )
    assert login_res.status_code == 302

    forgot_res = client.post("/forgot-password", data={"email": "ops@example.com"})
    assert forgot_res.status_code == 200

    mail = _read_mailbox(tmp_path)
    reset_rows = [row for row in mail if row.get("kind") == "password_reset"]
    assert reset_rows
    reset_path = _extract_path(reset_rows[-1]["link"])

    reset_res = client.post(
        reset_path,
        data={"password": "NewPass456", "confirm_password": "NewPass456"},
    )
    assert reset_res.status_code == 200

    login_after_reset = client.post(
        "/login",
        data={"email": "ops@example.com", "password": "NewPass456"},
    )
    assert login_after_reset.status_code == 302


def test_login_rate_limiting_blocks_bruteforce(client, tmp_path: Path):
    _signup(client, email="security@example.com", password="SecurePass123")

    mail = _read_mailbox(tmp_path)
    verify_rows = [row for row in mail if row.get("kind") == "verify_email"]
    verify_path = _extract_path(verify_rows[-1]["link"])
    client.get(verify_path)

    for _ in range(2):
        bad = client.post(
            "/login",
            data={"email": "security@example.com", "password": "WrongPass"},
        )
        assert bad.status_code == 401

    locked = client.post(
        "/login",
        data={"email": "security@example.com", "password": "WrongPass"},
    )
    assert locked.status_code == 401 or locked.status_code == 429

    blocked = client.post(
        "/login",
        data={"email": "security@example.com", "password": "SecurePass123"},
    )
    assert blocked.status_code == 429


def test_billing_payment_and_subscription_lifecycle(client, tmp_path: Path):
    _signup(client, email="billing@example.com", password="BillingPass123")
    mail = _read_mailbox(tmp_path)
    verify_rows = [row for row in mail if row.get("kind") == "verify_email"]
    client.get(_extract_path(verify_rows[-1]["link"]))

    login = client.post(
        "/login",
        data={"email": "billing@example.com", "password": "BillingPass123"},
    )
    assert login.status_code == 302

    success = client.post("/billing/checkout", data={"plan": "pro", "outcome": "success"})
    assert success.status_code == 200
    success_payload = success.get_json()
    assert success_payload["status"] == "success"
    assert success_payload["plan"] == "pro"

    failed = client.post("/billing/checkout", data={"plan": "enterprise", "outcome": "failed"})
    assert failed.status_code == 402
    fail_payload = failed.get_json()
    assert fail_payload["status"] == "failed"

    upgrade = client.post("/billing/subscription/upgrade")
    assert upgrade.status_code == 200
    assert upgrade.get_json()["status"] == "success"

    downgrade = client.post("/billing/subscription/downgrade")
    assert downgrade.status_code == 200
    assert downgrade.get_json()["status"] == "success"


def test_tracking_endpoint_accepts_events(client):
    res = client.post(
        "/track_event",
        json={"event": "page_tracking_test", "properties": {"path": "/"}},
    )
    assert res.status_code == 200
    payload = res.get_json()
    assert payload["status"] == "ok"
