"""NetCDF sounding ingestion.

TODO(core): implement loading of IGRA-derived NetCDF soundings via xarray.
"""

from pathlib import Path

import xarray as xr  # noqa: F401  (used once load_sounding is implemented)

from app.schemas import Sounding


def load_sounding(path: Path) -> Sounding:
    """Load a radiosonde sounding from a NetCDF file into a ``Sounding``.

    TODO(core): implement using ``xr.open_dataset(path)``. Steps to consider:
      1. Map the file's variable names (they differ by IGRA product/converter)
         to Sounding fields: pressure, geopotential height, temperature.
      2. Derive vapor pressure from whatever moisture variable exists
         (dewpoint or RH) — or compute it here and keep the formula in one place.
      3. Drop levels with missing/fill values; ensure arrays are bottom-up.
      4. Pull station id / launch time / lat / lon from attrs or coords.
    """
    raise NotImplementedError("load_sounding: implement NetCDF ingestion with xarray")
