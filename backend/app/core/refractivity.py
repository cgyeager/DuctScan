"""Refractivity computations.

TODO(core): implement everything in this module — it is the scientific heart of
the app. Nothing here should run at import time; the stubs raise only when called.
"""

import numpy as np

from app.schemas import MProfile, Sounding


def compute_N(
    pressure_hpa: np.ndarray,
    temperature_k: np.ndarray,
    vapor_pressure_hpa: np.ndarray,
) -> np.ndarray:
    """Compute atmospheric refractivity N at each level.

    Formula (Bean & Dutton / ITU-R P.453):

        N = 77.6 * (P / T) + 3.73e5 * (e / T^2)

    where P is total pressure [hPa], T is temperature [K], and e is water vapor
    partial pressure [hPa]. N is dimensionless ("N-units").

    TODO(core): implement. Validate array shapes match; watch units carefully.
    """
    raise NotImplementedError("compute_N: implement the refractivity formula")


def compute_M(n_units: np.ndarray, height_m: np.ndarray) -> np.ndarray:
    """Compute modified refractivity M at each level.

    Formula:

        M = N + (z / R_e) * 1e6  ≈  N + 0.157 * z

    where z is height above the surface [m] and R_e is the Earth's radius
    (~6.371e6 m). M is in "M-units".

    TODO(core): implement.
    """
    raise NotImplementedError("compute_M: implement the modified refractivity formula")


def compute_m_profile(sounding: Sounding) -> MProfile:
    """Build the full M-profile for a sounding: compute_N -> compute_M -> MProfile.

    TODO(core): implement by converting the sounding's level arrays to numpy,
    chaining compute_N and compute_M, and returning an MProfile.
    Consider: sorting/deduplicating levels, handling missing values (NaN).
    """
    raise NotImplementedError("compute_m_profile: chain compute_N and compute_M")
