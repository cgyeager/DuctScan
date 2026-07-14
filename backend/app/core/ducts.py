"""Atmospheric duct detection from the vertical M-gradient.

TODO(core): implement duct detection — the second half of the scientific core.
"""

import numpy as np

from app.schemas import Duct, MProfile


def detect_ducts(m_profile: MProfile) -> list[Duct]:
    """Detect ducts: layers where the vertical M-gradient is negative (dM/dz < 0).

    A trapping layer exists wherever dM/dz < 0. For each detected layer, classify:

    - ``surface`` duct: the duct extends down to the surface (the M value within
      the trapping layer drops below M at the surface).
    - ``elevated`` duct: trapping layer aloft, duct base above the surface.

    Return one ``Duct`` per detected layer with base/top heights, thickness, and
    strength (total M decrease across the trapping layer, ``strength_dm``).

      TODO: Consider a minimum-strength/thickness threshold to filter noise.
    """

    height_m: list[float] = m_profile.height_m
    M: list[float]  = m_profile.m_units

    height_m = np.asarray(height_m, float)
    M = np.asarray(M, float)

    order = np.argsort(height_m)
    h, m = height_m[order], M[order]

    dMdz = np.gradient(m, h)

    ducts = []
    n = len(height_m)
    for i in range(n-1):
        
        if M[i+1] < M[i]:
            j = i
            while j + 1 < n and M[j+1] < M[j]:
                j += 1

            duct = Duct(
                type="surface" if i == 0 else "elevated",
                base_height_m=float(h[i]),
                top_height_m=float(h[j]),
                thickness_m=float(h[j] - h[i]),
                strength_dm=float(m[i] - m[j]),
            )
            ducts.append(duct)
            i = j
      
    ducts = [d for d in ducts if d.strength_dm >= 1.0]
    return ducts, dMdz
