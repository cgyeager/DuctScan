"""Tests for app.core.ducts.

TODO(core): un-skip and flesh out these tests as you implement detect_ducts.
Start with small synthetic M-profiles where the answer is obvious, then add
golden tests using real IGRA soundings from tests/fixtures/ (see the README there).
"""

import pytest


@pytest.mark.skip(reason="TODO(core): monotonic M-profile -> no ducts")
def test_no_duct_in_standard_atmosphere():
    ...


@pytest.mark.skip(reason="TODO(core): synthetic inversion near the ground -> one surface duct")
def test_detects_surface_duct():
    ...


@pytest.mark.skip(reason="TODO(core): synthetic elevated inversion -> one elevated duct")
def test_detects_elevated_duct():
    """Also assert base/top/thickness/strength_dm values, not just the count."""
    ...


@pytest.mark.skip(reason="TODO(core): golden test against a known-duct IGRA sounding fixture")
def test_golden_igra_sounding():
    ...
