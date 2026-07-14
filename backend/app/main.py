"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

app = FastAPI(
    title="Refractivity Duct Analyzer",
    description=(
        "Ingests radiosonde soundings (NetCDF), computes modified refractivity (M), "
        "and detects atmospheric ducts from the vertical M-gradient."
    ),
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe. Always available, even while core logic is stubbed."""
    return {"status": "ok"}

