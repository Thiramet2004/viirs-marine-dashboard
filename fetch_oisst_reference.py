#!/usr/bin/env python3
"""
fetch_oisst_reference.py
------------------------
Long-term reference for the SST trend: NOAA OISST v2.1 (daily, 0.25 degree; satellites + ships + buoys,
1981-present) from the NOAA CoastWatch ERDDAP server (no login), averaged over the Thai EEZ.

Every second grid point (0.5 degree) inside 1_Marine_Zone_Andaman_GoT.shp is used. Writes:
  data/zonal_stats/oisst_eez_monthly.csv    year, month, sst, points
  data/zonal_stats/oisst_reference.json     annual means and linear trends (read by build_dashboard_data.py)

Raw yearly downloads are cached in VIIRS_OISST_CACHE (default E:\\SST_Chlor\\OISST).

Usage:
  python fetch_oisst_reference.py            # 1982 to the last complete month
"""

import datetime as dt
import json
import os
import sys
import time
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from scipy import stats as sps
from shapely.geometry import Point

PROJECT_DIR = Path(__file__).resolve().parent
OUT_DIR = PROJECT_DIR / "data" / "zonal_stats"
CACHE = Path(os.environ.get("VIIRS_OISST_CACHE", r"E:\SST_Chlor\OISST"))
ZONE_DIR = Path(os.environ.get("VIIRS_MARINE_ZONES_DIR", r"E:\SST_Chlor\EEZ_MarineZone"))
ERDDAP = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21Agg_LonPM180.csv"
FIRST_YEAR = 1982


def download(year, end):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"oisst_{year}.csv"
    if path.exists():
        # keep a cached year only if it already reaches the requested end date
        last_line = path.read_text(encoding="utf-8").rstrip().splitlines()[-1]
        if last_line.startswith(end):
            return path
    query = (f"?sst[({year}-01-01T12:00:00Z):1:({end}T12:00:00Z)][(0.0)]"
             f"[(5.875):2:(13.875)][(95.375):2:(104.125)]").replace("[", "%5B").replace("]", "%5D")
    for attempt in range(10):
        try:
            response = requests.get(ERDDAP + query, timeout=300)
            response.raise_for_status()
            path.write_text(response.text, encoding="utf-8")
            return path
        except requests.RequestException as error:
            print(f"{year}: retry {attempt + 1} ({str(error)[:60]})", flush=True)
            time.sleep(30 * (attempt + 1))
    sys.exit(f"Could not download OISST {year}")


def trend(years, values):
    fit = sps.linregress(years, values)
    t = sps.t.ppf(0.975, len(years) - 2)
    return {"per_decade": fit.slope * 10, "ci95_per_decade": t * fit.stderr * 10, "p_value": fit.pvalue,
            "years": [int(min(years)), int(max(years))]}


def main():
    eez = gpd.read_file(ZONE_DIR / "1_Marine_Zone_Andaman_GoT.shp").to_crs(4326).geometry.union_all()
    # Last month the server covers completely (the dataset runs a few weeks behind real time).
    info = requests.get(ERDDAP.replace("/griddap/", "/info/").replace(".csv", "/index.csv"), timeout=120).text
    coverage_end = dt.date.fromisoformat(next(line for line in info.splitlines() if "time_coverage_end" in line).split(",")[-1][:10])
    next_day = coverage_end + dt.timedelta(days=1)
    last_month = coverage_end if next_day.day == 1 else coverage_end.replace(day=1) - dt.timedelta(days=1)
    frames, points = [], None
    for year in range(FIRST_YEAR, last_month.year + 1):
        end = last_month.isoformat() if year == last_month.year else f"{year}-12-31"
        data = pd.read_csv(download(year, end), skiprows=[1]).dropna(subset=["sst"])
        if points is None:
            grid = data[["latitude", "longitude"]].drop_duplicates().values
            points = {(lat, lon) for lat, lon in grid if eez.contains(Point(lon, lat))}
        data = data[[(lat, lon) in points for lat, lon in zip(data.latitude, data.longitude)]]
        data["time"] = pd.to_datetime(data["time"])
        data = data[data.time.dt.year == year]  # the server can return a day of the neighbouring year
        days = data.groupby(data.time.dt.month).time.nunique()
        short = days[days < pd.Series({m: pd.Period(f"{year}-{m:02d}").days_in_month for m in days.index})]
        if len(short):
            print(f"{year}: months with missing days {dict(short)}", flush=True)
        monthly = data.groupby([data.time.dt.year.rename("year"), data.time.dt.month.rename("month")]).sst.mean()
        frames.append(monthly.reset_index())
        print(f"{year}: {len(points)} points, mean {monthly.mean():.2f} C", flush=True)
    monthly = pd.concat(frames)
    monthly["points"] = len(points)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    monthly.to_csv(OUT_DIR / "oisst_eez_monthly.csv", index=False)

    complete = monthly.groupby("year").filter(lambda g: len(g) == 12)
    annual = complete.groupby("year").sst.mean()
    last = int(annual.index.max())
    reference = {
        "source": "NOAA OISST v2.1 (ncdcOisst21Agg, NOAA CoastWatch ERDDAP)",
        "area": f"Thai EEZ (1_Marine_Zone_Andaman_GoT.shp), {len(points)} grid points",
        "annual_mean": {str(int(y)): float(v) for y, v in annual.items()},
        "trends": {key: trend(annual.loc[a:last].index.values, annual.loc[a:last].values)
                   for key, a in (("long_term", FIRST_YEAR), ("since_2000", 2000), ("dashboard_period", 2018))},
    }
    windows = [trend(annual.loc[a:a + 7].index.values, annual.loc[a:a + 7].values)["per_decade"]
               for a in range(FIRST_YEAR, last - 6)]
    reference["eight_year_windows"] = {"count": len(windows), "negative": int(np.sum(np.array(windows) < 0)),
                                       "min_per_decade": float(min(windows)), "max_per_decade": float(max(windows))}
    (OUT_DIR / "oisst_reference.json").write_text(json.dumps(reference, indent=2), encoding="utf-8")
    t = reference["trends"]["long_term"]
    print(f"Long-term trend {FIRST_YEAR}-{last}: {t['per_decade']:+.3f} +/- {t['ci95_per_decade']:.3f} C/decade "
          f"(p={t['p_value']:.1e})")


if __name__ == "__main__":
    main()
