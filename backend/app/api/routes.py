"""API routes.

The analysis endpoints orchestrate the ingest/core functions. Remaining stubs
raise ``NotImplementedError`` at call time (never at import time), which is
translated here into an HTTP 501 so the app stays runnable end to end.
"""

from datetime import datetime
import json
import os
from pathlib import Path
import requests
from fastapi import APIRouter, HTTPException, Query

from app.core.ducts import detect_ducts
from app.core.refractivity import compute_m_profile
from app.ingest.wyoming import fetch_stations, load_sounding_from_wyoming
from app.llm.provider import get_provider
from app.schemas import AnalyzeRequest, AnalyzeResponse, ChatRequest, ChatResponse, Station

router = APIRouter()


# Endpoints that call the (blocking) requests library are plain `def`, not
# `async def` — FastAPI runs them in a threadpool so they don't stall the loop.
@router.get("/stations", response_model=list[Station])
def list_stations(
    when: datetime | None = Query(
        default=None,
        alias="datetime",
        description="Cycle time (UTC, ISO format); defaults to the current cycle",
    ),
) -> list[Station]:
    """List radiosonde stations available for a cycle (proxied from U. Wyoming).

    Proxying through the backend avoids browser CORS restrictions and keeps the
    frontend decoupled from the Wyoming API shape.
    """
    try:
        cwd = os.getcwd()
        path = Path(f'{cwd}/cache_stations.json')
        if path.is_file():

            with open(path, 'r') as f:
                raw = json.load(f)
        else:
            raw = fetch_stations(when)
            with open(path, 'w') as f:
                json.dump(raw, f)

    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not reach the U. Wyoming station service: {exc}",
        ) from exc

    stations = [
        Station(
            station_id=str(s["stationid"]),
            name=s.get("name", ""),
            latitude=float(s["lat"]),
            longitude=float(s["lon"]),
            src=s.get("src", "UNKNOWN"),
        )
        for s in raw
        if "stationid" in s and "lat" in s and "lon" in s
    ]
    return stations

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """Fetch a sounding from the Wyoming database and analyze it.

    Pipeline: fetch + convert -> M-profile -> duct detection.
    """
    try:
        sounding = load_sounding_from_wyoming(
            request.station_id, request.src, request.datetime
        )
        m_profile = compute_m_profile(sounding)
        ducts, _ = detect_ducts(m_profile)
        return AnalyzeResponse(sounding=sounding, m_profile=m_profile, ducts=ducts)

    except NotImplementedError as exc:
        raise HTTPException(
            status_code=501,
            detail=f"Analysis pipeline not implemented yet: {exc}",
        ) from exc
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not fetch the sounding from U. Wyoming: {exc}",
        ) from exc


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Chat with the RAG/agentic LLM layer about analysis results."""
    try:
        provider = get_provider()
        return await provider.chat(request)
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=501,
            detail=f"LLM layer not implemented yet: {exc}",
        ) from exc
