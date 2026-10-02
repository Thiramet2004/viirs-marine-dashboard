#!/usr/bin/env python3
"""
download_viirs_monthly.py
-------------------------
Download NASA OB.DAAC VIIRS Level-3 monthly products (4 km) and cut them to the dashboard grid,
so months that are missing or were built from the wrong sensor can be filled without SNAP.

For each month every VIIRS platform that has a file (SNPP, NOAA-20 = JPSS1, NOAA-21 = JPSS2) is
downloaded; where more than one platform has data the pixel value is their mean, as SNAP's
merge of the same files does. Output (read by build_dashboard_data.py):

  <VIIRS_DOWNLOAD_DIR>/<P>/<YYYY>/<P>_VIIRS_<YYYY>_<MM>.tif     float32, NaN = no data
  <VIIRS_DOWNLOAD_DIR>/raw/<NASA file name>.nc                  original files

Login: NASA Earthdata (free, https://urs.earthdata.nasa.gov). Either
  - set EARTHDATA_TOKEN to a token from https://urs.earthdata.nasa.gov/profile (Generate Token), or
  - put "machine urs.earthdata.nasa.gov login <user> password <password>" in %USERPROFILE%\\_netrc.

Examples:
  python download_viirs_monthly.py --param sst --year 2026 --months 1-8
  python download_viirs_monthly.py --param sst --year 2026 --months 1-8 --from-dir D:\\nasa_files   # already downloaded
"""

import argparse
import calendar
import datetime as dt
import netrc
import os
import sys
import warnings
from pathlib import Path

import numpy as np
import rasterio  # import before netCDF4: both bundle PROJ, and rasterio must set up its own first
from rasterio.crs import CRS
from rasterio.transform import Affine
import netCDF4
import requests

DOWNLOAD_DIR = Path(os.environ.get("VIIRS_DOWNLOAD_DIR", r"E:\SST_Chlor\Monthly_NASA"))
GETFILE = "https://oceandata.sci.gsfc.nasa.gov/getfile/"
PLATFORMS = ("JPSS1", "SNPP", "JPSS2")
PRODUCTS = {
    "sst": {"folder": "SST", "suite": "SST.sst", "variable": "sst"},
    "chl": {"folder": "Chlor_a", "suite": "CHL.chlor_a", "variable": "chlor_a"},
}

# Dashboard grid (same as the SNAP products): 1/24 degree, upper-left corner 82.1667E 27.3333N, 1080 x 960.
WIDTH, HEIGHT, CELL = 1080, 960, 1 / 24
WEST, NORTH = 82.16666666666663, 27.333333333333336
TRANSFORM = Affine(CELL, 0.0, WEST, 0.0, -CELL, NORTH)
WGS84 = CRS.from_wkt('GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],'
                     'PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG","4326"]]')
# Row/column of that corner in NASA's global 8640 x 4320 grid (90N, 180W origin).
ROW0, COL0 = round((90 - NORTH) * 24), round((WEST + 180) * 24)


def file_name(platform, param, year, month, nrt=False):
    """NASA file name; nrt=True gives the near-real-time version published before the standard one."""
    last = calendar.monthrange(year, month)[1]
    return (f"{platform}_VIIRS.{year}{month:02d}01_{year}{month:02d}{last}.L3m.MO.{PRODUCTS[param]['suite']}.4km"
            f"{'.NRT' if nrt else ''}.nc")


def session():
    s = requests.Session()
    token = os.environ.get("EARTHDATA_TOKEN")
    if token:
        s.headers["Authorization"] = f"Bearer {token}"
        return s
    for candidate in (Path.home() / "_netrc", Path.home() / ".netrc"):
        if candidate.is_file():
            login = netrc.netrc(candidate).authenticators("urs.earthdata.nasa.gov")
            if login:
                s.auth = (login[0], login[2])
                return s
    sys.exit("No Earthdata login: set EARTHDATA_TOKEN or create %USERPROFILE%\\_netrc (see the top of this file).")


def download(s, name, raw_dir):
    target = raw_dir / name
    if target.exists() and target.stat().st_size > 0:
        return target
    response = s.get(GETFILE + name, timeout=600, stream=True)
    if response.status_code == 404:
        return None
    if "text/html" in response.headers.get("content-type", ""):
        sys.exit(f"Earthdata login was not accepted while downloading {name} (got a login page).")
    response.raise_for_status()
    partial = target.with_suffix(".part")
    with open(partial, "wb") as handle:
        for chunk in response.iter_content(1 << 20):
            handle.write(chunk)
    partial.replace(target)
    return target


def subset(path, variable):
    """Values on the dashboard grid, NaN where NASA has no data."""
    with netCDF4.Dataset(path) as dataset:
        lat, lon = dataset.variables["lat"], dataset.variables["lon"]
        if abs(float(lat[ROW0]) - (NORTH - CELL / 2)) > 1e-3 or abs(float(lon[COL0]) - (WEST + CELL / 2)) > 1e-3:
            raise RuntimeError(f"Unexpected grid in {path}")
        values = dataset.variables[variable][ROW0:ROW0 + HEIGHT, COL0:COL0 + WIDTH]
        return np.ma.filled(values.astype("float32"), np.nan)


def merge(paths, variable):
    stack = np.stack([subset(path, variable) for path in paths])
    with np.errstate(invalid="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # all-NaN pixels (land / no data) stay NaN
        return np.nanmean(stack, axis=0).astype("float32") if len(paths) > 1 else stack[0]


def write(values, path, sources):
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", driver="GTiff", width=WIDTH, height=HEIGHT, count=1, dtype="float32",
                       crs=WGS84, transform=TRANSFORM, nodata=np.nan, compress="lzw") as target:
        target.write(values, 1)
        target.update_tags(SOURCES=",".join(sources), CREATED=dt.datetime.now().isoformat(timespec="seconds"))


def month_list(text):
    months = []
    for part in text.split(","):
        start, _, end = part.partition("-")
        months.extend(range(int(start), int(end or start) + 1))
    return months


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--param", choices=PRODUCTS, required=True)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--months", default="1-12", help="e.g. 1-8 or 1,2,5")
    parser.add_argument("--from-dir", type=Path, help="use NASA .nc files already in this folder instead of downloading")
    args = parser.parse_args()

    config = PRODUCTS[args.param]
    raw_dir = DOWNLOAD_DIR / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    s = None if args.from_dir else session()
    for month in month_list(args.months):
        paths = []
        for platform in PLATFORMS:
            name = file_name(platform, args.param, args.year, month)
            path = (args.from_dir / name if (args.from_dir / name).exists() else None) if args.from_dir else download(s, name, raw_dir)
            if path:
                paths.append(path)
        if not paths:
            print(f"{args.param} {args.year}-{month:02d}: no VIIRS file at NASA yet")
            continue
        out = DOWNLOAD_DIR / config["folder"] / str(args.year) / f"{config['folder']}_VIIRS_{args.year}_{month:02d}.tif"
        values = merge(paths, config["variable"])
        write(values, out, [path.name for path in paths])
        print(f"{args.param} {args.year}-{month:02d}: {', '.join(p.name.split('.')[0] for p in paths)} -> {out} "
              f"({int(np.isfinite(values).sum())} valid pixels)")


if __name__ == "__main__":
    main()
