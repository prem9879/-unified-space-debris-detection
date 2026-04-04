"""Smoke tests for the orbital mission brief endpoints."""

from __future__ import annotations

from webapp import flask_app


def test_orbital_brief_endpoint() -> None:
    client = flask_app.app.test_client()
    res = client.get("/orbital_brief")
    assert res.status_code == 200

    payload = res.get_json()
    assert isinstance(payload, dict)
    assert "architecture" in payload
    assert "model_stack" in payload
    assert "visualization" in payload
    assert "deployment" in payload
    assert len(payload.get("architecture", [])) >= 4


def test_orbital_scene_endpoint() -> None:
    client = flask_app.app.test_client()
    res = client.get("/orbital_scene")
    assert res.status_code == 200

    payload = res.get_json()
    assert isinstance(payload, dict)
    assert "scene" in payload
    assert "shells" in payload
    assert "alerts" in payload