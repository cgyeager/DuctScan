# tests/fixtures/

Golden test fixtures: small NetCDF soundings with **known, verified duct conditions**
(e.g. IGRA soundings from coastal stations during documented ducting events).

Workflow:

1. Find an IGRA sounding with a well-understood duct (or a clean no-duct case).
2. Subset/convert it to a small NetCDF file and drop it here (these small files
   ARE committed, unlike `data/`).
3. Record the expected result (duct type, base/top heights, strength) in a comment
   or sidecar file, and assert it in `tests/test_ducts.py::test_golden_igra_sounding`.
