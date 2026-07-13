"""Smoke tests that must pass even while core logic is stubbed."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_returns_501_while_stubbed():
    """The stubbed pipeline must fail loudly (501), not crash or silently succeed."""
    response = client.post(
        "/api/analyze", files={"file": ("sounding.nc", b"not a real netcdf")}
    )
    assert response.status_code == 501


def test_chat_returns_501_while_stubbed():
    response = client.post("/api/chat", json={"message": "hello"})
    assert response.status_code == 501
