"""Refractivity computations.

TODO(core): implement everything in this module — it is the scientific heart of
the app. Nothing here should run at import time; the stubs raise only when called.
"""

import numpy as np

from app.schemas import MProfile, Sounding


def compute_N(
    P_hPa: np.ndarray,
    T_kelvin: np.ndarray,
    e_hPa: np.ndarray,
) -> np.ndarray:
    """Compute atmospheric refractivity N at each level.

    Formula (Bean & Dutton / ITU-R P.453):

        N = 77.6 * (P / T) + 3.73e5 * (e / T^2)

    where P is total pressure [hPa], T is temperature [K], and e is water vapor
    partial pressure [hPa]. N is dimensionless ("N-units").
    """
    return (77.6 * (P_hPa/T_kelvin)) + 3.73e5 * (e_hPa / T_kelvin**2)


def compute_M(N: np.ndarray, height_m: np.ndarray) -> np.ndarray:
    """Compute modified refractivity M at each level.

    Formula:

        M = N + (z / R_e) * 1e6  ≈  N + 0.157 * z

    where z is height above the surface [m] and R_e is the Earth's radius
    (~6.371e6 m). M is in "M-units".
    """
    return N + 0.157 * height_m


def compute_m_profile(sounding: Sounding) -> MProfile:
    """Build the full M-profile for a sounding: compute_N -> compute_M -> MProfile.

    TODO(core): implement by converting the sounding's level arrays to numpy,
    chaining compute_N and compute_M, and returning an MProfile.
    Consider: sorting/deduplicating levels, handling missing values (NaN).
    """

    pressure_hpa: list[float] = sounding.pressure_hpa
    height_m: list[float] = sounding.height_m
    temperature_k: list[float] = sounding.temperature_k
    vapor_pressure_hpa: list[float] = sounding.vapor_pressure_hpa

    N = compute_N(pressure_hpa, temperature_k, vapor_pressure_hpa)

    m_profile = MProfile()
    m_profile.height_m = height_m
    m_profile.m_units = compute_M(N, height_m)
    return m_profile

"""

class MProfile(BaseModel):

    height_m: list[float] = Field(description="Height at each level [m]")
    m_units: list[float] = Field(description="Modified refractivity M at each level [M-units]")


class Sounding(BaseModel):
    station_id: str = Field(description="IGRA station identifier, e.g. 'USM00072250'")
    launch_time: datetime | None = Field(default=None, description="Launch timestamp (UTC)")
    latitude: float | None = None
    longitude: float | None = None
    pressure_hpa: list[float] = Field(description="Pressure at each level [hPa]")
    height_m: list[float] = Field(description="Geopotential height at each level [m]")
    temperature_k: list[float] = Field(description="Temperature at each level [K]")
    vapor_pressure_hpa: list[float] = Field(
        description="Water vapor partial pressure at each level [hPa]"
    )

"""