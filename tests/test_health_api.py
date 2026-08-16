"""Tests for liveness/readiness health endpoints."""

from fastapi.testclient import TestClient


def test_health_liveness(client: TestClient):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_health_readiness_with_db(client: TestClient):
    resp = client.get("/api/v1/health/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert body["database"] == "ok"
