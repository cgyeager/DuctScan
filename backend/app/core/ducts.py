"""Atmospheric duct detection from the vertical M-gradient.

TODO(core): implement duct detection — the second half of the scientific core.
"""

from app.schemas import Duct, MProfile


def detect_ducts(m_profile: MProfile) -> list[Duct]:
    """Detect ducts: layers where the vertical M-gradient is negative (dM/dz < 0).

    A trapping layer exists wherever dM/dz < 0. For each detected layer, classify:

    - ``surface`` duct: the duct extends down to the surface (the M value within
      the trapping layer drops below M at the surface).
    - ``elevated`` duct: trapping layer aloft, duct base above the surface.

    Return one ``Duct`` per detected layer with base/top heights, thickness, and
    strength (total M decrease across the trapping layer, ``strength_dm``).

    TODO(core): implement. Suggested approach:
      1. Compute dM/dz between adjacent levels (np.diff or np.gradient).
      2. Find contiguous runs of negative gradient (the trapping layers).
      3. Derive duct base/top from the trapping layer and the surrounding profile,
         then classify surface vs. elevated.
      4. Consider a minimum-strength/thickness threshold to filter noise.
    """
    raise NotImplementedError("detect_ducts: implement M-gradient duct detection")
