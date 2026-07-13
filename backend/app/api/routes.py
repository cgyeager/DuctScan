"""API routes.

Both endpoints orchestrate stubbed core functions. The stubs raise
``NotImplementedError`` at call time (never at import time), which is translated
here into an HTTP 501 so the scaffold stays runnable end to end.
"""

import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from app.core.ducts import detect_ducts
from app.core.refractivity import compute_m_profile
from app.ingest.loading_data import load_sounding
from app.llm.provider import get_provider
from app.schemas import AnalyzeResponse, ChatRequest, ChatResponse

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(file: UploadFile) -> AnalyzeResponse:
    """Analyze an uploaded NetCDF sounding: ingest -> M-profile -> duct detection."""
    suffix = Path(file.filename or "sounding.nc").suffix or ".nc"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        sounding = load_sounding(tmp_path)
        m_profile = compute_m_profile(sounding)
        ducts = detect_ducts(m_profile)
        return AnalyzeResponse(sounding=sounding, m_profile=m_profile, ducts=ducts)

    except NotImplementedError as exc:
        raise HTTPException(
            status_code=501,
            detail=f"Analysis pipeline not implemented yet: {exc}",
        ) from exc
    finally:
        tmp_path.unlink(missing_ok=True)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Chat with the (future) RAG/agentic LLM layer about analysis results."""
    try:
        provider = get_provider()
        return await provider.chat(request)
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=501,
            detail=f"LLM layer not implemented yet: {exc}",
        ) from exc
