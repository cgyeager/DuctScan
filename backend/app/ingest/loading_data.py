"""NetCDF sounding ingestion.
"""

from pathlib import Path

import numpy as np
import xarray as xr

from app.schemas import Sounding


def saturation_vapor_pressure(T_celsius: float) -> float:
    """ Saturation vapor pressure over water, hPa. Bolton (1980).
        How much water vapor the air can hold at different temperatures
        Absolute humidity
        Return: es in hectopascal
    """
    return 6.112 * np.exp( (17.67* T_celsius) / (T_celsius + 243.5))

def vapor_pressure(T_kelvin: float, RH_percent: float) -> float:
    """ Actual water-vapor partial pressure e, hPa, from temperature + RH.
        Relative humidity of the absolute humidity
    
        Return e: hectopascals
    """
    T_c = T_kelvin - 273.15
    es = saturation_vapor_pressure(T_c)
    return (RH_percent / 100.0) * es 

def load_grid(path: Path) -> list[Sounding]:
    pass

def load_sounding(path: Path) -> Sounding:
   """Load a radiosonde sounding from a NetCDF file into a ``Sounding``.
   """
   ds = xr.open_dataset(path)
   levels = np.sort(ds.isobaricInhPa.values)[::-1]  # bottom-up (high P first)

   P = levels.astype(float)
   T = ds['t'].sel(isobaricInhPa=levels).values.astype(float)
   RH = ds['r'].sel(isobaricInhPa=levels).values.astype(float)
   H = ds['gh'].sel(isobaricInhPa=levels).values.astype(float)
   e = vapor_pressure(T, RH)

   return Sounding(
       station_id=str(ds.attrs.get('station_id', '')),
       launch_time=None,
       latitude=float(ds.latitude.values),
       longitude=float(ds.longitude.values),
       pressure_hpa=P.tolist(),
       height_m=H.tolist(),
       temperature_k=T.tolist(),
       vapor_pressure_hpa=e.tolist(),
   )
