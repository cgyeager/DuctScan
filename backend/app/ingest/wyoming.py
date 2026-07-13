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

import requests
import pandas as pd

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
    try:
        df = fetch_sounding_siphon("72293", when)
        print(f"siphon: {len(df)} levels")
    except Exception as e:
        print("siphon failed, trying CSV:", e)
        df = fetch_sounding_csv("72293", when, src=src)
        print(f"csv: {len(df)} levels")
    print(df.head())
