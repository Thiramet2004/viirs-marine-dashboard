#!/usr/bin/env python3
"""
update_from_nasa.py
-------------------
Monthly update for GitHub Actions (no E: drive, no SNAP): downloads new VIIRS Level-3 monthly files from NASA
OB.DAAC, and updates the dashboard rasters, data/Yearly_RGB/stats.json and the zonal CSV tables.

Uses the same processing functions as build_dashboard_data.py, with the inputs it saved in data/ci/:
  masks.tif               land mask, Thai EEZ, marine zones and the Gulf / Andaman parts (bit mask)
  climatology_<p>.tif     per-pixel monthly climatology (VIIRS 2018-2025), 12 bands
  monthly/<p>/<YYYY>/     monthly values of the open year(s), so a year can be recomputed when a month is added
  monthly_index.json      source and status of those monthly values

Each run, per parameter:
  - months after the latest month in stats.json up to the last complete calendar month are downloaded
    (the standard NASA file, or the near-real-time .NRT file while the standard one is not out yet);
  - months that are MODIS estimates or NRT files are tried again, and replaced when a standard VIIRS file exists;
  - every year that changed is recomputed from all of its months.

Login: EARTHDATA_TOKEN (NASA Earthdata user token), see download_viirs_monthly.py.

Usage:
  python update_from_nasa.py                    # normal run (GitHub Actions)
  python update_from_nasa.py --dry-run          # only report which months would be downloaded
  python update_from_nasa.py --source local ... # test: take the months from the local SNAP products instead of NASA
"""

import argparse
import csv
import datetime as dt
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import rasterio

import build_dashboard_data as B
import download_viirs_monthly as N

STATS_PATH = B.DATA_DIR / "Yearly_RGB" / "stats.json"
INDEX_PATH = B.CI_DIR / "monthly_index.json"
ZONE_ORDER = ["overall", *B.ZONE_IDS]


# ----------------------------------------------------------------------------- inputs

def load_ci_context(param):
    """Masks and climatology from data/ci, as build_dashboard_data.area_context expects them."""
    with rasterio.open(B.CI_DIR / "masks.tif") as dataset:
        bits, transform, crs = dataset.read(1), dataset.transform, dataset.crs
        bit_of = json.loads(dataset.tags()["BITS"])
    unpack = lambda name: ((bits >> bit_of[name]) & 1).astype(bool)
    land, overall = unpack("land"), unpack("overall")
    masks = {zone_id: unpack(zone_id) for zone_id in B.ZONE_IDS}
    with rasterio.open(B.CI_DIR / f"climatology_{param}.tif") as dataset:
        climatology = {month: np.ma.masked_invalid(dataset.read(month).astype("float32")) for month in range(1, 13)}
    return B.area_context(param, climatology, land, overall, masks), transform, crs


def read_float(path):
    with rasterio.open(path) as dataset:
        return np.ma.masked_invalid(dataset.read(1).astype("float32"))


# ----------------------------------------------------------------------------- sources

class NasaSource:
    """NASA OB.DAAC L3m monthly files, cut to the dashboard grid (download_viirs_monthly.py)."""

    def __init__(self):
        self.session = None
        self.raw_dir = Path(tempfile.mkdtemp(prefix="viirs_raw_"))

    def get(self, param, year, month):
        if self.session is None:
            self.session = N.session()
        for nrt in (False, True):
            paths = []
            for platform in N.PLATFORMS:
                name = N.file_name(platform, param, year, month, nrt=nrt)
                path = N.download(self.session, name, self.raw_dir)
                if path:
                    paths.append(path)
            if paths:
                values = N.merge(paths, N.PRODUCTS[param]["variable"])
                label = "+".join(path.name.split(".")[0] for path in paths) + (" (NRT)" if nrt else "")
                for path in paths:
                    path.unlink(missing_ok=True)
                return values, label, "nrt" if nrt else "viirs"
        return None


class LocalSource:
    """Test source: the local SNAP products used by build_dashboard_data.py."""

    def get(self, param, year, month):
        path = B.monthly_source(param, year, month)
        if not path:
            return None
        return B.read(path)[0].filled(np.nan), "local " + path.parent.name, "viirs"


# ----------------------------------------------------------------------------- csv helpers

def read_rows(path):
    with open(path, encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        return header, list(reader)


def replace_rows(path, keep, new_rows, sort_key):
    header, rows = read_rows(path)
    rows = [row for row in rows if keep(row)] + new_rows
    rows.sort(key=sort_key)
    B.write_csv(path, header, rows)


# ----------------------------------------------------------------------------- update

def last_complete_month(today):
    previous = today.replace(day=1) - dt.timedelta(days=1)
    return previous.year, previous.month


def months_after(year, month, until):
    out = []
    while (year, month) < until:
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
        out.append((year, month))
    return out


def update(source, until, dry_run=False):
    stats = json.loads(STATS_PATH.read_text(encoding="utf-8"))
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    changed_any = False
    for param in B.PARAMS:
        have = {(int(year), month) for year, record in stats["monthly"][param].items() for month in record["available_months"]}
        estimated = {(int(year), month) for year, months in stats.get("estimated_months", {}).get(param, {}).items() for month in months}
        nrt = {tuple(int(part) for part in key.split("-")) for key, entry in index.get(param, {}).items() if entry["status"] == "nrt"}
        retry = sorted(estimated | nrt)
        new = months_after(*max(have), until)
        print(f"{param}: latest month {max(have)}, new months to try {new}, retry {retry}", flush=True)
        if dry_run:   # check that the stored inputs load (no download, no login needed)
            ctx, _, _ = load_ci_context(param)
            stored = sorted(index.get(param, {}))
            print(f"  inputs ok: EEZ {int(ctx['overall_mask'].sum())} pixels, climatology EEZ mean "
                  f"{ctx['annual_climatology']['overall']:.3f}, stored months {stored[0] if stored else '-'}..{stored[-1] if stored else '-'}",
                  flush=True)
            continue

        updated = {}
        for key in retry:
            result = source.get(param, *key)
            if result and result[2] == "viirs":           # replace an estimate / NRT only with a standard VIIRS file
                updated[key] = result
            elif result and key in estimated:             # an NRT VIIRS file is still better than a MODIS estimate
                updated[key] = result
        for key in new:
            result = source.get(param, *key)
            if result is None:
                print(f"  {param} {key[0]}-{key[1]:02d}: not published yet", flush=True)
                break
            updated[key] = result
        if not updated:
            continue

        ctx, transform, crs = load_ci_context(param)
        index.setdefault(param, {})
        for (year, month), (values, label, status) in updated.items():
            path = B.CI_DIR / "monthly" / param / str(year) / f"{param}_{year}_{month:02d}.tif"
            B.write_float(path, values, transform, crs)
            index[param][f"{year}-{month:02d}"] = {"file": path.relative_to(B.DATA_DIR).as_posix(), "source": label, "status": status}

        for year in sorted({year for year, _ in updated}):
            months = sorted({m for (y, m) in have if y == year} | {m for (y, m) in updated if y == year})
            missing = [m for m in months if f"{year}-{m:02d}" not in index[param]]
            if missing:
                print(f"  {param} {year}: cannot recompute, no stored values for months {missing}", file=sys.stderr)
                continue
            records, anomalies, monthly_rows, source_rows = {}, [], [], []
            for month in months:
                entry = index[param][f"{year}-{month:02d}"]
                record, anomaly, rows = B.process_month(param, year, month, read_float(B.DATA_DIR / entry["file"]),
                                                        ctx, transform, crs)
                records[month] = record
                anomalies.append(anomaly)
                monthly_rows.extend(rows)
                stats["sources"][param]["monthly"][f"{year}-{month:02d}"] = entry["source"]
                source_rows.append([param, year, month, "NASA OB.DAAC L3m" if entry["status"] != "estimate" else "MODIS estimate",
                                    entry["source"], "used" if entry["status"] != "estimate" else "estimate", entry["status"]])
            yearly_rows = B.summarize_year(param, year, records, anomalies, ctx, stats, transform, crs)
            # estimates that are now VIIRS are no longer estimates
            still_estimated = [m for m in months if index[param][f"{year}-{m:02d}"]["status"] == "estimate"]
            if still_estimated:
                stats.setdefault("estimated_months", {}).setdefault(param, {})[str(year)] = still_estimated
            else:
                stats.get("estimated_months", {}).get(param, {}).pop(str(year), None)
            stats["years"] = sorted(set(stats["years"]) | {year})

            out = B.DATA_DIR / "zonal_stats"
            replace_rows(out / f"{param}_monthly_zonal.csv", lambda row: int(row[0]) != year, monthly_rows,
                         lambda row: (int(row[0]), int(row[1]), ZONE_ORDER.index(row[2])))
            replace_rows(out / f"{param}_yearly_zonal.csv", lambda row: int(row[0]) != year, yearly_rows,
                         lambda row: (int(row[0]), ZONE_ORDER.index(row[1])))
            replace_rows(out / "sources.csv", lambda row: not (row[0] == param and int(row[1]) == year), source_rows,
                         lambda row: (["sst", "chl"].index(row[0]), int(row[1]), int(row[2])))
            print(f"  {param} {year}: recomputed months {months}", flush=True)
            changed_any = True

    if changed_any:
        reference = B.DATA_DIR / "zonal_stats" / "oisst_reference.json"
        if reference.exists():
            stats["long_term_reference"] = {"sst": json.loads(reference.read_text(encoding="utf-8"))}
        STATS_PATH.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
        INDEX_PATH.write_text(json.dumps(index, indent=2), encoding="utf-8")
    print("changed" if changed_any else "no new data", flush=True)
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as handle:
            handle.write(f"changed={'true' if changed_any else 'false'}\n")
    return changed_any


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", choices=("nasa", "local"), default="nasa")
    parser.add_argument("--until", help="last month to fetch, YYYY-MM (default: the last complete month)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    until = tuple(int(part) for part in args.until.split("-")) if args.until else last_complete_month(dt.date.today())
    update(LocalSource() if args.source == "local" else NasaSource(), until, args.dry_run)
