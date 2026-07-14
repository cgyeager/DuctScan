#!/usr/bin/env python3
"""
University of Wyoming upper-air access

Endpoints (decoded from the site's JS/HTML):
  Station list : GET /wsgi/sounding_json?datetime=YYYY-MM-DD HH:00:00
                 -> {"datetime":..., "stations":[{stationid,name,lat,lon,src}], "read":1}
                 datetime optional; stations vary by cycle.
  Sounding     : GET /wsgi/sounding?datetime=...&id=STID&src=SRC&type=TEXT:CSV
                 hours: 00,03,06,09,12,15,18,21 Z ; type TEXT:CSV is parseable.
"""
import io
import json
from datetime import datetime

import pandas as pd
import numpy as np
import requests

from app.schemas import Sounding
from app.ingest.loading_data import saturation_vapor_pressure

BASE = "https://weather.uwyo.edu/wsgi"
UA = {"User-Agent": "Mozilla/5.0 (portfolio duct-analyzer)"}


# ----------------------------------------------------------------------
# Station list
# ----------------------------------------------------------------------
def fetch_stations(when: datetime | None = None) -> list[dict]:
    """
    Return the list of station dicts {stationid, name, lat, lon, src} for the
    given cycle (or the current one if when is None).
    """
    url = f"{BASE}/sounding_json"
    params = {}
    if when is not None:
        params["datetime"] = when.strftime("%Y-%m-%d %H:00:00")
    r = requests.get(url, params=params, headers=UA, timeout=60)
    r.raise_for_status()
    payload = r.json()
    return payload.get("stations", [])


def find_station(stations: list[dict], stationid: str) -> dict | None:
    """Look up one station (to recover its 'src') from a station list."""
    for s in stations:
        if str(s.get("stationid")) == str(stationid):
            return s
    return None


def save_stations(stations: list[dict], path: str) -> None:
    with open(path, "w") as f:
        json.dump(stations, f, indent=2)

def fetch_sounding_csv(stationid: str, when: datetime, src: str = "UNKNOWN") -> pd.DataFrame:
    """
    Hit the real /wsgi/sounding endpoint with type=TEXT:CSV and parse it.
    Pass the station's real `src`
    """
    params = {
        "datetime": when.strftime("%Y-%m-%d %H:00:00"),
        "id": stationid,
        "src": src,
        "type": "TEXT:CSV",
    }
    r = requests.get(f"{BASE}/sounding", params=params, headers=UA, timeout=60)
    r.raise_for_status()
    return _parse_csv_response(r.text)


def _parse_csv_response(text: str) -> pd.DataFrame:
    """
    The CSV response embeds the data table amid header/footer text. 
    Extract the CSV block: find the header line with the column names, 
    read until a blank line or non-data content. 
    Kept tolerant since the exact wrapper can vary.
    """
    lines = text.splitlines()
    # Find the line that looks like the CSV header (contains 'pressure')
    start = None
    for i, ln in enumerate(lines):
        low = ln.lower()
        if "pressure" in low and "," in ln:
            start = i
            break
    if start is None:
        raise ValueError("Could not locate CSV header in response; "
                         "inspect the raw text to adjust the parser.")
    # Collect contiguous comma-containing lines from the header down
    block = []
    for ln in lines[start:]:
        if ln.strip() == "" or ("," not in ln):
            if block:  # stop at first gap after we've started
                break
            continue
        block.append(ln)
    df = pd.read_csv(io.StringIO("\n".join(block)))
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def load_sounding_from_wyoming(station_id: str, src: str, when: datetime) -> Sounding:
    """Fetch one sounding from the Wyoming database and convert it to a ``Sounding``.

    This is what POST /api/analyze calls.

    TODO(core):
      1. df = fetch_sounding_csv(station_id, when, src=src)
      2. Map the CSV columns to Sounding fields (pressure, height, temperature —
         inspect df.columns for the exact names; convert temperature to Kelvin
         if the source is in Celsius).
      3. Derive vapor_pressure_hpa from the moisture column (dewpoint or RH),
         reusing your saturation/vapor-pressure functions — consider moving them
         into app/core/refractivity.py so the formulas live in one place.
      4. Drop rows with missing values; ensure levels are ordered bottom-up.
      5. Return Sounding(station_id=station_id, launch_time=when, ...).
    """
    df = fetch_sounding_csv(station_id, when, src)

    d = df[['pressure_hpa','geopotential height_m','temperature_c','dew point temperature_c']].copy()
    d.columns = ['P', 'H', 'T', 'Td']
    d = d.apply(pd.to_numeric, errors='coerce').dropna()
    d = d.sort_values('H')
    d = d[d['H'].diff().fillna(1) > 0]

    edges = np.arange(d['H'].min(), d['H'].max()+20, 20) # 20 m bins
    d['bin'] = np.digitize(d['H'], edges)
    binned = d.groupby('bin').mean().sort_values('H')

    lat = df['latitude'].iloc[0]
    lon = df['longitude'].iloc[0]
    P   = binned['P'].to_numpy(float)
    H   = binned['H'].to_numpy(float)
    T_k = binned['T'].to_numpy(float) + 273.15 # convert to Kelvin
    Td  = binned['Td'].to_numpy(float)

    Td = saturation_vapor_pressure(Td)

    return Sounding(
        station_id=station_id,
        launch_time=when,
        latitude=float(lat),
        longitude=float(lon),
        pressure_hpa=P.tolist(),
        height_m=H.tolist(),
        temperature_k=T_k.tolist(),
        vapor_pressure_hpa=Td.tolist(),
    )


"""
class Sounding(BaseModel):
    station_id: str                             = Field(description="IGRA station identifier, e.g. 'USM00072250'")
    launch_time: dt.datetime | None             = Field(default=None, description="Launch timestamp (UTC)")
    latitude: float | None                      = None
    longitude: float | None                     = None
    pressure_hpa: list[float]                   = Field(description="Pressure at each level [hPa]")
    height_m: list[float]                       = Field(description="Geopotential height at each level [m]")
    temperature_k: list[float]                  = Field(description="Temperature at each level [K]")
    vapor_pressure_hpa: list[float]             = Field(description="Water vapor partial pressure at each level [hPa]"
    )
"""




# ----------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    # Offline test of the CSV parser + station lookup against sample data
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        with open("/tmp/sample_stations.json") as f:
            sample = json.load(f)
        st = sample["stations"]
        print(f"parsed {len(st)} sample stations")
        s = find_station(st, "72293")
        print("lookup 72293 ->", s["name"], "src=", s["src"])
        sys.exit(0)

    # Live run (on your machine): list stations, fetch one sounding
    stations = fetch_stations()  # current cycle
    print(f"{len(stations)} stations this cycle")
    save_stations(stations, "data/wyoming_stations.json")

    # San Diego, most recent 00Z
    when = datetime(2019, 7, 15, 0)
    sd = find_station(stations, "72293")
    src = sd["src"] if sd else "UNKNOWN"
    df = fetch_sounding_csv("72293", when, src=src)
    print(f"csv: {len(df)} levels")
    print(df.head())
