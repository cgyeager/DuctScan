"""Pydantic models for soundings, M-profiles, ducts, and the chat API."""

import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field


class Station(BaseModel):
    """A radiosonde station as listed by the U. Wyoming upper-air service."""

    station_id: str = Field(description="Station identifier, e.g. '72293'")
    name: str
    latitude: float
    longitude: float
    src: str = Field(description="Wyoming data source for this cycle, e.g. 'BUFR' or 'TEMP'")


class AnalyzeRequest(BaseModel):
    """Request to fetch and analyze one sounding from the Wyoming database."""

    station_id: str
    src: str = Field(description="Pass through the station's 'src' from GET /stations")
    # Field named after the wire format; the module alias avoids the name clash.
    datetime: dt.datetime = Field(description="Cycle time (UTC), hours 00/03/.../21Z")


class Sounding(BaseModel):
    """A vertical radiosonde profile"""

    station_id: str = Field(description="IGRA station identifier, e.g. 'USM00072250'")
    launch_time: dt.datetime | None = Field(default=None, description="Launch timestamp (UTC)")
    latitude: float | None = None
    longitude: float | None = None
    pressure_hpa: list[float] = Field(description="Pressure at each level [hPa]")
    height_m: list[float] = Field(description="Geopotential height at each level [m]")
    temperature_k: list[float] = Field(description="Temperature at each level [K]")
    vapor_pressure_hpa: list[float] = Field(
        description="Water vapor partial pressure at each level [hPa]"
    )


class MProfile(BaseModel):
    """Modified refractivity profile derived from a sounding."""

    height_m: list[float] = Field(description="Height at each level [m]")
    m_units: list[float] = Field(description="Modified refractivity M at each level [M-units]")


class Duct(BaseModel):
    """A detected atmospheric duct (layer where dM/dz < 0)."""

    type: Literal["surface", "elevated"]
    base_height_m: float = Field(description="Height of the duct base [m]")
    top_height_m: float = Field(description="Height of the duct top [m]")
    thickness_m: float = Field(description="top_height_m - base_height_m [m]")
    strength_dm: float = Field(
        description="Duct strength: M decrease across the trapping layer [M-units]"
    )


class AnalyzeResponse(BaseModel):
    """Full result of analyzing one uploaded sounding."""

    sounding: Sounding
    m_profile: MProfile
    ducts: list[Duct]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(description="The user's new message")
    history: list[ChatMessage] = Field(default_factory=list, description="Prior turns")
    analysis: AnalyzeResponse | None = None


class ChatResponse(BaseModel):
    reply: str
