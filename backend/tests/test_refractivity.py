"""Tests for app.core.refractivity.

TODO(core): un-skip and flesh out these tests as you implement the module.
Good reference values: Bean & Dutton worked examples, or hand-computed values
for a standard atmosphere.
"""

import pytest


@pytest.mark.skip(reason="TODO(core): implement compute_N, then test against known values")
def test_compute_n_known_values():
    """e.g. P=1013.25 hPa, T=288.15 K, e=10 hPa should give N ≈ 317.7."""
    ...


@pytest.mark.skip(reason="TODO(core): implement compute_M, then test the 0.157*z term")
def test_compute_m_adds_height_term():
    """M at z=1000 m should exceed N by ~157 M-units."""
    ...


@pytest.mark.skip(reason="TODO(core): implement compute_m_profile, then test end to end")
def test_compute_m_profile_from_sounding():
    """Build a small synthetic Sounding and check the resulting MProfile shape/values."""
    ...
