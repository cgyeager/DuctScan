"""API-level tests.

External services (U. Wyoming, Voyage, Anthropic) are mocked at the route
boundary so the suite is fast and runs without network or API keys — the
science code (compute_m_profile, detect_ducts) still executes for real.
"""

import requests
from fastapi.testclient import TestClient

import app.api.routes as routes
from app.main import app
from app.schemas import ChatRequest, ChatResponse, Sounding

client = TestClient(app)


def _synthetic_sounding() -> Sounding:
    """A small, physically plausible profile (4 levels, no missing data)."""
    return Sounding(
        station_id="72293",
        latitude=32.85,
        longitude=-117.12,
        pressure_hpa=[1000.0, 990.0, 975.0, 950.0],
        height_m=[0.0, 90.0, 220.0, 440.0],
        temperature_k=[288.0, 287.4, 286.5, 285.1],
        vapor_pressure_hpa=[12.0, 11.5, 10.8, 9.9],
    )


ANALYZE_BODY = {"station_id": "72293", "src": "BUFR", "datetime": "2026-07-13T12:00:00"}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_with_mocked_wyoming(monkeypatch):
    """Full pipeline over a synthetic sounding — only the network fetch is faked."""
    monkeypatch.setattr(
        routes, "load_sounding_from_wyoming", lambda *args, **kwargs: _synthetic_sounding()
    )

    response = client.post("/api/analyze", json=ANALYZE_BODY)
    assert response.status_code == 200

    body = response.json()
    assert body["sounding"]["station_id"] == "72293"
    # M-profile mirrors the input levels
    assert len(body["m_profile"]["height_m"]) == 4
    assert len(body["m_profile"]["m_units"]) == 4
    # M must be positive and (for this smooth profile) increasing with height
    m_units = body["m_profile"]["m_units"]
    assert all(m > 0 for m in m_units)
    assert m_units == sorted(m_units)
    # A smooth standard-ish profile contains no ducts
    assert body["ducts"] == []


def test_analyze_wyoming_unreachable_returns_502(monkeypatch):
    def _raise(*args, **kwargs):
        raise requests.ConnectionError("service unreachable")

    monkeypatch.setattr(routes, "load_sounding_from_wyoming", _raise)

    response = client.post("/api/analyze", json=ANALYZE_BODY)
    assert response.status_code == 502


def test_chat_with_mocked_provider(monkeypatch):
    """Route wiring only — the provider (and its RAG/LLM calls) is faked."""

    class FakeProvider:
        async def chat(self, request: ChatRequest) -> ChatResponse:
            assert request.message == "hello"
            return ChatResponse(reply="pong")

    monkeypatch.setattr(routes, "get_provider", lambda: FakeProvider())

    response = client.post("/api/chat", json={"message": "hello"})
    assert response.status_code == 200
    assert response.json() == {"reply": "pong"}
