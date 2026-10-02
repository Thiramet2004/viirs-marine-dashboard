#!/usr/bin/env python3
"""
build_dashboard_data.py
-----------------------
Rebuild every dashboard raster, data/Yearly_RGB/stats.json and the zonal CSV tables from the
VIIRS monthly products in one pass (Python only, no SNAP), so maps and charts always come from
the same numbers.

Method
  1. Monthly source: VIIRS L3 monthly means. Each product's .dim is checked: every source NetCDF
     must be VIIRS (SNPP / NOAA-20 / NOAA-21) and cover the product's own year and month. Products
     built from MODIS or from another year are rejected. A month that fails the check is taken from
     a NASA download (download_viirs_monthly.py) when one exists, otherwise it is left out.
  2. Climatology: per-pixel mean of the accepted monthly products for CLIMATOLOGY_YEARS (the same
     period and sensor for all 12 months). A pixel needs MIN_CLIMATOLOGY_YEARS valid years.
     Use --climatology nasa to use the SNAP climatology products in E:\\Monthly Climatology instead.
  3. Mask (the same rule as the SNAP anomaly products for 2018-2023):
       - land: pixel centres inside country_Asean.shp are removed
       - SST: observed and climatology SST must both be >= SST_MIN_VALID (cloud-contamination filter)
  4. Anomaly = monthly - climatology.
  5. Zonal statistics: mean of pixel centres inside each EEZ marine-zone polygon.

Sources (override with environment variables):
  VIIRS_SOURCE_MONTHLY_DIR   E:\\SST_Chlor\\Monthly         <P>_4km/<YYYY>/<P>_VIIRS_<MM>_*_4km.data/<var>_mean.img
  VIIRS_DOWNLOAD_DIR         E:\\SST_Chlor\\Monthly_NASA    <P>/<YYYY>/<P>_VIIRS_<YYYY>_<MM>.tif (download_viirs_monthly.py)
  VIIRS_CLIMATOLOGY_DIR      E:\\Monthly Climatology        only with --climatology nasa
  VIIRS_SOURCE_ANOMALY_DIR   E:\\SST_Chlor\\Anomaly         only for --check (reproduce the SNAP anomaly products)
  VIIRS_SOURCE_YEARLY_DIR    E:\\SST_Chlor                  <P>_Yearly_Anomaly/<YYYY>/... (comparison column in CSV)
  VIIRS_MARINE_ZONES_DIR     E:\\SST_Chlor\\EEZ_MarineZone

Outputs:
  data/Anomaly_RGB/<P>/<YYYY>/<MM>/<P>_Anomaly_RGB_<MM>_<YYYY>.tif
  data/Monthly_RGB/<P>/<YYYY>/<MM>/<P>_Monthly_RGB_<MM>_<YYYY>.tif
  data/Yearly_RGB/{sst,chl}/<p>_Yearly_Anomaly_RGB_<YYYY>.tif
  data/Yearly_RGB/absolute/{sst,chl}/<p>_Yearly_Absolute_RGB_<YYYY>.tif   (annual absolute value, absolute colour scale)
  data/Yearly_RGB/stats.json
  data/zonal_stats/<p>_monthly_zonal.csv       year, month, zone, absolute, climatology, anomaly, pixels
  data/zonal_stats/<p>_climatology_zonal.csv   month, zone, climatology, pixels, years
  data/zonal_stats/<p>_yearly_zonal.csv        year, zone, mean of monthly anomalies, yearly anomaly product
  data/zonal_stats/sources.csv                 which source file was used or rejected for every month, and why

Usage:
  python build_dashboard_data.py             # rebuild everything
  python build_dashboard_data.py --check     # source audit + reproduce the SNAP anomaly products
"""

import argparse
import csv
import glob
import json
import os
import re
import shutil
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask

from convert_monthly_to_rgb import CHLOR_A_PALETTE, SST_PALETTE, apply_color_palette
from regenerate_anomaly_rgb import CHLOR_A_PALETTE as CHL_ANOMALY_PALETTE
from regenerate_anomaly_rgb import SST_PALETTE as SST_ANOMALY_PALETTE
from regenerate_anomaly_rgb import colorize as colorize_anomaly

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
MONTHLY_SRC = Path(os.environ.get("VIIRS_SOURCE_MONTHLY_DIR", r"E:\SST_Chlor\Monthly"))
DOWNLOAD_DIR = Path(os.environ.get("VIIRS_DOWNLOAD_DIR", r"E:\SST_Chlor\Monthly_NASA"))
CLIMATOLOGY_DIR = Path(os.environ.get("VIIRS_CLIMATOLOGY_DIR", r"E:\Monthly Climatology"))
ANOMALY_SRC = Path(os.environ.get("VIIRS_SOURCE_ANOMALY_DIR", r"E:\SST_Chlor\Anomaly"))
YEARLY_SRC = Path(os.environ.get("VIIRS_SOURCE_YEARLY_DIR", r"E:\SST_Chlor"))
ZONE_DIR = Path(os.environ.get("VIIRS_MARINE_ZONES_DIR", r"E:\SST_Chlor\EEZ_MarineZone"))

YEARS = range(2018, 2027)
CLIMATOLOGY_YEARS = range(2018, 2026)
MIN_CLIMATOLOGY_YEARS = 4
SST_MIN_VALID = 26.0
# Months with no VIIRS SST (2026 so far) are estimated from the MODIS products, corrected by the MODIS - VIIRS
# offset measured in a year that has both (E:\2024 holds MODIS products for 2024).
MODIS_CALIBRATION_YEAR = 2024
MODIS_OVERLAP_DIR = Path(os.environ.get("VIIRS_MODIS_OVERLAP_DIR", r"E:\2024"))

# Same zone order and shapefiles as server.py; file 1 is the whole EEZ.
OVERALL_FILE = "1_Marine_Zone_Andaman_GoT.shp"
LAND_FILE = "country_Asean.shp"
ZONE_FILES = {
    "upper_gulf": "2_Marine_Zone_GoT_GULF1.shp",
    "rayong": "3_Marine_Zone_GoT_GULF21.shp",
    "trat": "4_Marine_Zone_GoT_GULF31.shp",
    "central_gulf": "5_Marine_Zone_GoT_GULF3.shp",
    "lower_gulf": "6_Marine_Zone_GoT_GULF4.shp",
    "andaman": "7_Marine_Zone_Andaman_GULF41.shp",
}
# Whole-sea regions: the two parts of the Thai EEZ polygon (OVERALL_FILE), east = Gulf of Thailand.
REGION_IDS = ("gulf_of_thailand", "andaman_sea")
ZONE_IDS = [*ZONE_FILES, *REGION_IDS]

PARAMS = {
    "sst": {"folder": "SST", "var": "sst_mean", "palette": SST_PALETTE, "anomaly_palette": SST_ANOMALY_PALETTE},
    "chl": {"folder": "Chlor_a", "var": "chlor_a_mean", "palette": CHLOR_A_PALETTE, "anomaly_palette": CHL_ANOMALY_PALETTE},
}

# Source NetCDF names written by SNAP into the .dim, e.g. JPSS1_VIIRS.20240101_20240131.L3m.MO.SST.sst.4km.nc
SOURCE_NC = re.compile(r"([A-Z0-9]+)_([A-Z]+)\.(\d{4})(\d{2})\d{2}_\d{8}\.L3m\.MO\.")
VIIRS_PLATFORMS = {"SNPP", "JPSS1", "JPSS2"}


# ----------------------------------------------------------------------------- helpers

def read(path):
    with rasterio.open(path) as dataset:
        values = np.ma.masked_invalid(dataset.read(1, masked=True).astype("float32"))
        return values, dataset.transform, dataset.crs


def first(pattern):
    matches = sorted(glob.glob(str(pattern)))
    return Path(matches[0]) if matches else None


def write_rgb(path, rgb, transform, crs):
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path, "w", driver="GTiff", height=rgb.shape[1], width=rgb.shape[2], count=3,
        dtype="uint8", crs=crs, transform=transform, compress="lzw",
    ) as target:
        target.write(rgb)


def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for row in rows:
            writer.writerow(["" if value is None else round(value, 6) if isinstance(value, float) else value
                             for value in row])


def polygon_mask(filename, shape, transform):
    """True for pixel centres inside the shapefile's polygons."""
    geometry = gpd.read_file(ZONE_DIR / filename).to_crs(4326).geometry.union_all()
    return ~geometry_mask([geometry], out_shape=shape, transform=transform, all_touched=False)


def region_masks(shape, transform):
    """Gulf of Thailand and Andaman Sea parts of the Thai EEZ polygon (pixel centres)."""
    eez = gpd.read_file(ZONE_DIR / OVERALL_FILE).to_crs(4326).geometry.union_all()
    parts = sorted(getattr(eez, "geoms", [eez]), key=lambda part: part.area, reverse=True)[:2]
    if len(parts) != 2:
        raise RuntimeError(f"Expected the EEZ polygon to have a Gulf and an Andaman part, found {len(parts)}")
    gulf, andaman = sorted(parts, key=lambda part: part.centroid.x, reverse=True)
    inside = lambda geometry: ~geometry_mask([geometry], out_shape=shape, transform=transform, all_touched=False)
    return {"gulf_of_thailand": inside(gulf), "andaman_sea": inside(andaman)}


def zone_masks(shape, transform):
    masks = {zone_id: polygon_mask(filename, shape, transform) for zone_id, filename in ZONE_FILES.items()}
    masks.update(region_masks(shape, transform))
    return polygon_mask(OVERALL_FILE, shape, transform), masks


def zone_mean(values, inside):
    selected = values[inside]
    return float(selected.mean()) if selected.count() else None


def zone_count(values, inside):
    return int(values[inside].count())


def mean_or_none(values):
    values = [value for value in values if value is not None]
    return float(np.mean(values)) if values else None


# ----------------------------------------------------------------------------- sources

def snap_monthly_product(param, year, month):
    folder, var = PARAMS[param]["folder"], PARAMS[param]["var"]
    return first(MONTHLY_SRC / f"{folder}_4km" / str(year) / f"{folder}_VIIRS_{month:02d}_*_4km.data" / f"{var}.img")


def provenance(image_path, year, month):
    """(ok, sensors, reason) from the source NetCDF names recorded in the product's .dim file."""
    dim = image_path.parent.with_suffix(".dim")
    text = dim.read_text(encoding="utf-8", errors="replace") if dim.exists() else ""
    product_name = re.search(r'name="product_name"[^>]*>([^<]*)', text)
    sources = sorted(set(SOURCE_NC.findall(text)))
    sensors = "+".join(f"{platform}_{sensor}" for platform, sensor, _, _ in sources)
    if product_name and "MODIS" in product_name.group(1).upper():
        return False, sensors or "MODIS", f"product_name is {product_name.group(1)}"
    for platform, sensor, source_year, source_month in sources:
        if sensor != "VIIRS" or platform not in VIIRS_PLATFORMS:
            return False, sensors, f"built from {platform}_{sensor}"
        if (int(source_year), int(source_month)) != (year, month):
            return False, sensors, f"built from {source_year}-{source_month} data"
    if not sources:
        return True, "VIIRS (not listed in .dim)", "accepted: product name is VIIRS, sources not recorded"
    return True, sensors, "accepted"


def monthly_source(param, year, month, log=None):
    """Accepted monthly VIIRS product for param/year/month, or None."""
    path = snap_monthly_product(param, year, month)
    if path:
        ok, sensors, reason = provenance(path, year, month)
        if log is not None:
            log.append([param, year, month, str(path.parent), sensors, "used" if ok else "rejected", reason])
        if ok:
            return path
    folder = PARAMS[param]["folder"]
    downloaded = DOWNLOAD_DIR / folder / str(year) / f"{folder}_VIIRS_{year}_{month:02d}.tif"
    if downloaded.exists():
        if log is not None:
            log.append([param, year, month, str(downloaded), "NASA OB.DAAC download", "used", "NASA L3m VIIRS"])
        return downloaded
    return None


def modis_product(param, year, month):
    """SST product built from MODIS (rejected as a VIIRS source), used only as a calibrated estimate."""
    path = snap_monthly_product(param, year, month)
    if param != "sst" or not path:
        return None
    text = path.parent.with_suffix(".dim").read_text(encoding="utf-8", errors="replace")
    return path if "MODIS" in text else None


def modis_offset(land):
    """Per-pixel mean (MODIS - VIIRS) over the calibration year, from months where both Aqua and Terra were merged.

    Leave-one-month-out on 2024 gives zone-month errors of RMSE 0.37 C after this correction (0.55 C without).
    """
    differences, months = [], []
    for month in range(1, 13):
        modis = first(MODIS_OVERLAP_DIR / f"SST_VIIRS_{month:02d}_*_4km.data" / "sst_mean.img")
        viirs = monthly_source("sst", MODIS_CALIBRATION_YEAR, month)
        if not modis or not viirs:
            continue
        dim = modis.parent.with_suffix(".dim").read_text(encoding="utf-8", errors="replace")
        if not ("AQUA_MODIS" in dim and "TERRA_MODIS" in dim):
            continue
        m, v = read(modis)[0], read(viirs)[0]
        ok = ~np.ma.getmaskarray(m) & ~np.ma.getmaskarray(v) & ~land & (m.filled(0) >= SST_MIN_VALID) & (v.filled(0) >= SST_MIN_VALID)
        differences.append(np.ma.array(m - v, mask=~ok))
        months.append(month)
    offset = np.ma.stack(differences).mean(axis=0)
    scalar = float(offset.mean())
    return offset.filled(scalar).astype("float32"), scalar, months


def nasa_climatology_source(param, month):
    folder, var = PARAMS[param]["folder"], PARAMS[param]["var"]
    return first(CLIMATOLOGY_DIR / f"{folder}_4km" / f"{folder}_VIIRS_{month:02d}_*.data" / f"{var}.img")


def snap_anomaly_product(param, year, month):
    folder = PARAMS[param]["folder"]
    base = ANOMALY_SRC / f"{folder}_Monthly_Anomaly" / str(year)
    for month_dir in (base / f"{month:02d}", base / f"{month:02d}_{year}"):
        for name in (f"{folder}_Monthly_Anomaly_{month:02d}_{year}_msk.tif", f"{folder}_Monthly_Anomaly_{month:02d}_{year}.tif"):
            if (month_dir / name).exists():
                return month_dir / name
    return None


def yearly_product_source(param, year):
    folder = PARAMS[param]["folder"]
    return first(YEARLY_SRC / f"{folder}_Yearly_Anomaly" / str(year) / f"{folder}_Yearly_Anomaly_{year}_msk.tif")


# ----------------------------------------------------------------------------- method

def valid_mask(param, monthly, climatology, land):
    """Pixels used for absolute and anomaly values (see 'Mask' in the module docstring)."""
    valid = ~np.ma.getmaskarray(monthly) & ~np.ma.getmaskarray(climatology) & ~land
    if param == "sst":
        valid &= (monthly.filled(-999) >= SST_MIN_VALID) & (climatology.filled(-999) >= SST_MIN_VALID)
    return valid


def compute_climatology(param):
    """Per-pixel monthly mean over CLIMATOLOGY_YEARS of the accepted VIIRS products."""
    climatology, years_used = {}, {}
    for month in range(1, 13):
        stack, used = [], []
        for year in CLIMATOLOGY_YEARS:
            path = monthly_source(param, year, month)
            if path:
                stack.append(read(path)[0])
                used.append(year)
        stack = np.ma.stack(stack)
        climatology[month] = np.ma.array(stack.mean(axis=0), mask=stack.count(axis=0) < MIN_CLIMATOLOGY_YEARS)
        years_used[month] = used
    return climatology, years_used


def load_climatology(param, mode):
    if mode == "nasa":
        climatology, labels = {}, {}
        for month in range(1, 13):
            path = nasa_climatology_source(param, month)
            climatology[month] = read(path)[0]
            labels[month] = re.search(r"(\d{4}_\d{4})", path.parent.name).group(1).replace("_", "-")
        return climatology, labels
    climatology, years_used = compute_climatology(param)
    return climatology, {month: f"{min(years)}-{max(years)} ({len(years)} yr)" for month, years in years_used.items()}


# ----------------------------------------------------------------------------- check

def check_sources():
    """Audit every monthly product, then reproduce the SNAP anomaly products for 2018-2023."""
    log = []
    for param in PARAMS:
        for year in YEARS:
            for month in range(1, 13):
                monthly_source(param, year, month, log)
    rejected = [row for row in log if row[5] == "rejected"]
    print(f"Monthly products: {sum(row[5] == 'used' for row in log)} used, {len(rejected)} rejected")
    for row in rejected:
        print(f"  rejected {row[0]} {row[1]}-{row[2]:02d}: {row[6]}")

    template = read(nasa_climatology_source("sst", 1))
    land = polygon_mask(LAND_FILE, template[0].shape, template[1])
    print("Reproducing SNAP anomaly products 2018-2023 with the same climatology and mask rule:")
    for param in PARAMS:
        climatology = load_climatology(param, "nasa")[0]
        worst, mask_mismatch, months = 0.0, 0, 0
        for year in range(2018, 2024):
            for month in range(1, 13):
                product, monthly_path = snap_anomaly_product(param, year, month), monthly_source(param, year, month)
                if not product or not monthly_path:
                    continue
                snap = read(product)[0]
                monthly = read(monthly_path)[0]
                valid = valid_mask(param, monthly, climatology[month], land)
                mine = np.ma.array(monthly - climatology[month], mask=~valid)
                mask_mismatch += int((valid != ~np.ma.getmaskarray(snap)).sum())
                both = valid & ~np.ma.getmaskarray(snap)
                worst = max(worst, float(np.abs(mine.filled(0) - snap.filled(0))[both].max()))
                months += 1
        print(f"  {param}: {months} months, max value difference {worst:.2e}, mask mismatches {mask_mismatch} pixels")
    return log


# ----------------------------------------------------------------------------- shared processing
# Used by build() (local sources) and update_from_nasa.py (GitHub Actions), so both give the same numbers.

CI_DIR = DATA_DIR / "ci"
MASK_BITS = {"land": 0, "overall": 1, **{zone_id: 2 + i for i, zone_id in enumerate(ZONE_IDS)}}


def area_context(param, climatology, land, overall_mask, masks):
    """Per-area climatology and the annual climatology (per area and per pixel) for one parameter."""
    all_zones = [("overall", overall_mask), *masks.items()]
    eez_climatology, zones_climatology = [], {zone_id: [] for zone_id in ZONE_IDS}
    climatology_values, stack = {}, []
    for month in range(1, 13):
        values = climatology[month]
        usable = ~np.ma.getmaskarray(values) & ~land
        if param == "sst":
            usable &= values.filled(-999) >= SST_MIN_VALID
        values = np.ma.array(values, mask=~usable)
        climatology_values[month] = values
        stack.append(values)
        for zone_id, mask in all_zones:
            (eez_climatology if zone_id == "overall" else zones_climatology[zone_id]).append(zone_mean(values, mask))
    stack = np.ma.stack(stack)
    return {
        "climatology": climatology, "land": land, "overall_mask": overall_mask, "masks": masks, "all_zones": all_zones,
        "climatology_values": climatology_values, "eez_climatology": eez_climatology, "zones_climatology": zones_climatology,
        "annual_climatology": {"overall": mean_or_none(eez_climatology),
                               **{zone_id: mean_or_none(values) for zone_id, values in zones_climatology.items()}},
        "pixel_annual_climatology": np.ma.array(stack.mean(axis=0), mask=stack.count(axis=0) < 12),
    }


def climatology_rows_for(ctx, labels):
    return [[month, zone_id, zone_mean(ctx["climatology_values"][month], mask),
             zone_count(ctx["climatology_values"][month], mask), labels[month]]
            for month in range(1, 13) for zone_id, mask in ctx["all_zones"]]


def process_month(param, year, month, observed, ctx, transform, crs):
    """Mask, anomaly, monthly RGB rasters and zonal values for one month. Returns (record, anomaly, csv rows)."""
    config, folder = PARAMS[param], PARAMS[param]["folder"]
    climatology = ctx["climatology"][month]
    valid = valid_mask(param, observed, climatology, ctx["land"])
    monthly = np.ma.array(observed, mask=~valid)
    anomaly = np.ma.array(observed - climatology, mask=~valid)
    mm = f"{month:02d}"
    write_rgb(DATA_DIR / "Anomaly_RGB" / folder / str(year) / mm / f"{folder}_Anomaly_RGB_{mm}_{year}.tif",
              colorize_anomaly(anomaly, config["anomaly_palette"]), transform, crs)
    write_rgb(DATA_DIR / "Monthly_RGB" / folder / str(year) / mm / f"{folder}_Monthly_RGB_{mm}_{year}.tif",
              apply_color_palette(monthly, config["palette"]), transform, crs)
    masks, overall_mask = ctx["masks"], ctx["overall_mask"]
    record = {
        "absolute_mean": zone_mean(monthly, overall_mask),
        "anomaly_mean": zone_mean(anomaly, overall_mask),
        "absolute_zones": {zone_id: zone_mean(monthly, mask) for zone_id, mask in masks.items()},
        "anomaly_zones": {zone_id: zone_mean(anomaly, mask) for zone_id, mask in masks.items()},
    }
    rows = []
    for zone_id, mask in ctx["all_zones"]:
        absolute_value, anomaly_value = zone_mean(monthly, mask), zone_mean(anomaly, mask)
        rows.append([year, month, zone_id, absolute_value,
                     None if absolute_value is None else absolute_value - anomaly_value,
                     anomaly_value, zone_count(anomaly, mask)])
    print(f"{param} {year}-{mm}: EEZ mean {record['absolute_mean']:.3f}, anomaly {record['anomaly_mean']:+.3f}", flush=True)
    return record, anomaly, rows


def summarize_year(param, year, records, monthly_anomalies, ctx, stats, transform, crs, product=None, product_name=None):
    """Yearly records, trend entries and yearly rasters from the monthly records of one year. Returns csv rows."""
    config = PARAMS[param]
    months = sorted(records)
    stats["monthly"][param][str(year)] = {
        "absolute": {"zones": {z: [records.get(m, {}).get("absolute_zones", {}).get(z) for m in range(1, 13)] for z in ZONE_IDS}},
        "anomaly": {"zones": {z: [records.get(m, {}).get("anomaly_zones", {}).get(z) for m in range(1, 13)] for z in ZONE_IDS}},
        "available_months": months,
    }
    anomaly_means = [records[m]["anomaly_mean"] for m in months if records[m]["anomaly_mean"] is not None]
    anomaly_zone_values = {z: [records[m]["anomaly_zones"][z] for m in months if records[m]["anomaly_zones"][z] is not None] for z in ZONE_IDS}
    absolute_zone_values = {z: [records[m]["absolute_zones"][z] for m in months if records[m]["absolute_zones"][z] is not None] for z in ZONE_IDS}
    record = {
        "mean": mean_or_none(anomaly_means),
        "min": float(min(anomaly_means)) if anomaly_means else None,
        "max": float(max(anomaly_means)) if anomaly_means else None,
        "zones": {z: float(np.mean(v)) for z, v in anomaly_zone_values.items() if v},
    }
    stats[param][str(year)] = record
    # Absolute annual values: the plain mean when all 12 months are present, otherwise seasonally adjusted
    # (annual climatology + mean anomaly of the available months), the same rule as the monthly page.
    annual_climatology = ctx["annual_climatology"]

    def absolute_annual(zone_id, absolute_values, anomaly_values):
        if len(absolute_values) == 12:
            return float(np.mean(absolute_values))
        if not anomaly_values or annual_climatology.get(zone_id) is None:
            return None
        return annual_climatology[zone_id] + float(np.mean(anomaly_values))

    absolute_months = [records[m]["absolute_mean"] for m in months if records[m]["absolute_mean"] is not None]
    absolute_record = {
        "mean": absolute_annual("overall", absolute_months, anomaly_means),
        "min": float(min(absolute_months)) if absolute_months else None,
        "max": float(max(absolute_months)) if absolute_months else None,
        "zones": {z: value for z in ZONE_IDS
                  if (value := absolute_annual(z, absolute_zone_values[z], anomaly_zone_values[z])) is not None},
        "seasonally_adjusted": len(months) < 12,
    }
    stats["absolute"][param][str(year)] = absolute_record
    stats["trend"]["anomaly"][param][str(year)] = {
        "mean": record["mean"], "zones": record["zones"], "months": len(anomaly_means),
        "zone_months": {z: len(v) for z, v in anomaly_zone_values.items()},
    }
    stats["trend"]["absolute"][param][str(year)] = {
        "mean": absolute_record["mean"], "zones": absolute_record["zones"],
        "months": len(absolute_months), "zone_months": {z: len(v) for z, v in absolute_zone_values.items()},
    }
    stats["trend"]["monthly_absolute"][param][str(year)] = {
        "mean": mean_or_none(absolute_months),
        "zones": {z: float(np.mean(v)) for z, v in absolute_zone_values.items() if v},
        "months": len(absolute_months),
        "zone_months": {z: len(v) for z, v in absolute_zone_values.items()},
    }
    # Annual anomaly raster = pixel-wise mean of the available monthly anomalies.
    annual = np.ma.masked_invalid(np.ma.stack(monthly_anomalies).mean(axis=0))
    write_rgb(DATA_DIR / "Yearly_RGB" / param / f"{param}_Yearly_Anomaly_RGB_{year}.tif",
              colorize_anomaly(annual, config["anomaly_palette"]), transform, crs)
    # Annual absolute raster = pixel annual climatology + pixel mean anomaly (equals the plain mean of the
    # monthly values where a pixel has all 12 months), in the absolute colour scale.
    pixel_annual_climatology = ctx["pixel_annual_climatology"]
    annual_absolute = np.ma.array(pixel_annual_climatology + annual,
                                  mask=np.ma.getmaskarray(pixel_annual_climatology) | np.ma.getmaskarray(annual))
    write_rgb(DATA_DIR / "Yearly_RGB" / "absolute" / param / f"{param}_Yearly_Absolute_RGB_{year}.tif",
              apply_color_palette(annual_absolute, config["palette"]), transform, crs)
    # Zonal means of the SNAP yearly anomaly product (local only), kept for comparison.
    if product is not None:
        stats["yearly_product"].setdefault(param, {})[str(year)] = {
            "mean": zone_mean(product, ctx["overall_mask"]),
            "zones": {zone_id: zone_mean(product, mask) for zone_id, mask in ctx["masks"].items()},
            "source": product_name,
        }
    rows = []
    for zone_id, mask in ctx["all_zones"]:
        derived = record["mean"] if zone_id == "overall" else record["zones"].get(zone_id)
        rows.append([year, zone_id, derived, len(months), None if product is None else zone_mean(product, mask)])
    return rows


def write_float(path, values, transform, crs, descriptions=None):
    """Float32 GeoTIFF (NaN = no data) for the inputs GitHub Actions needs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    values = values if values.ndim == 3 else values[None]
    with rasterio.open(path, "w", driver="GTiff", height=values.shape[1], width=values.shape[2], count=values.shape[0],
                       dtype="float32", crs=crs, transform=transform, nodata=np.nan,
                       compress="deflate", predictor=3, zlevel=9) as target:
        target.write(values.astype("float32"))
        if descriptions:
            for band, text in enumerate(descriptions, start=1):
                target.set_band_description(band, text)


def export_ci_inputs(param, ctx, climatology_labels, transform, crs, current_year_floats):
    """Inputs for update_from_nasa.py: zone/land masks, climatology and the open year's monthly values."""
    CI_DIR.mkdir(parents=True, exist_ok=True)
    bits = np.zeros(ctx["land"].shape, dtype="uint16")
    bits |= ctx["land"].astype("uint16") << MASK_BITS["land"]
    bits |= ctx["overall_mask"].astype("uint16") << MASK_BITS["overall"]
    for zone_id, mask in ctx["masks"].items():
        bits |= mask.astype("uint16") << MASK_BITS[zone_id]
    with rasterio.open(CI_DIR / "masks.tif", "w", driver="GTiff", height=bits.shape[0], width=bits.shape[1], count=1,
                       dtype="uint16", crs=crs, transform=transform, compress="deflate") as target:
        target.write(bits, 1)
        target.update_tags(BITS=json.dumps(MASK_BITS))
    stack = np.stack([ctx["climatology"][m].filled(np.nan) for m in range(1, 13)])
    write_float(CI_DIR / f"climatology_{param}.tif", stack, transform, crs,
                descriptions=[f"{m:02d} {climatology_labels[m]}" for m in range(1, 13)])
    index_path = CI_DIR / "monthly_index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {}
    index[param] = {}
    shutil.rmtree(CI_DIR / "monthly" / param, ignore_errors=True)
    for (year, month), (observed, source, status) in sorted(current_year_floats.items()):
        path = CI_DIR / "monthly" / param / str(year) / f"{param}_{year}_{month:02d}.tif"
        write_float(path, observed.filled(np.nan), transform, crs)
        index[param][f"{year}-{month:02d}"] = {"file": path.relative_to(DATA_DIR).as_posix(), "source": source, "status": status}
    index["climatology_labels"] = index.get("climatology_labels", {})
    index["climatology_labels"][param] = climatology_labels
    index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")


# ----------------------------------------------------------------------------- build (local sources)

def build(climatology_mode):
    stats = {"years": list(YEARS), "sst": {}, "chl": {}, "absolute": {"sst": {}, "chl": {}},
             "baseline": {}, "trend": {"absolute": {}, "anomaly": {}, "monthly_absolute": {}}, "monthly": {},
             "climatology": {}, "yearly_product": {}, "sources": {},
             "method": {"climatology": climatology_mode, "climatology_years": [min(CLIMATOLOGY_YEARS), max(CLIMATOLOGY_YEARS)],
                        "min_climatology_years": MIN_CLIMATOLOGY_YEARS, "sst_min_valid": SST_MIN_VALID,
                        "land_mask": LAND_FILE}}
    source_rows = []
    for param, config in PARAMS.items():
        folder = config["folder"]
        print(f"{param}: climatology ({climatology_mode})", flush=True)
        climatology, climatology_labels = load_climatology(param, climatology_mode)
        template_path = next(path for path in (monthly_source(param, y, 1) for y in YEARS) if path)
        _, transform, crs = read(template_path)
        shape = climatology[1].shape
        land = polygon_mask(LAND_FILE, shape, transform)
        overall_mask, masks = zone_masks(shape, transform)
        ctx = area_context(param, climatology, land, overall_mask, masks)
        for key in ("absolute", "anomaly", "monthly_absolute"):
            stats["trend"][key][param] = {}
        stats["monthly"][param] = {}
        stats["sources"][param] = {"climatology": climatology_labels, "monthly": {}}
        monthly_rows, yearly_rows = [], []

        # Remove previous outputs so a rejected month cannot leave a stale raster behind.
        for kind in ("Anomaly_RGB", "Monthly_RGB"):
            shutil.rmtree(DATA_DIR / kind / folder, ignore_errors=True)
        for path in (DATA_DIR / "Yearly_RGB" / param, DATA_DIR / "Yearly_RGB" / "absolute" / param):
            shutil.rmtree(path, ignore_errors=True)

        offset = None
        if param == "sst":
            offset, offset_scalar, offset_months = modis_offset(land)
            stats["method"]["modis_calibration"] = {
                "year": MODIS_CALIBRATION_YEAR, "months": offset_months, "eez_mean_offset": offset_scalar,
                "validation_rmse_zone_month": 0.37,
            }
        stats["estimated_months"] = stats.get("estimated_months", {})
        stats["climatology"][param] = {"eez": ctx["eez_climatology"], "zones": ctx["zones_climatology"],
                                       "periods": climatology_labels}
        stats["baseline"][param] = mean_or_none(ctx["eez_climatology"])

        year_floats = {}
        for year in YEARS:
            monthly_anomalies, records = [], {}
            for month in range(1, 13):
                monthly_path = monthly_source(param, year, month, source_rows)
                estimated = False
                if not monthly_path and offset is not None:
                    monthly_path = modis_product(param, year, month)
                    if monthly_path:
                        estimated = True
                        source_rows.append([param, year, month, str(monthly_path.parent), "MODIS Aqua+Terra",
                                            "estimate", f"no VIIRS; MODIS minus the {MODIS_CALIBRATION_YEAR} MODIS-VIIRS offset"])
                if not monthly_path:
                    continue
                observed, monthly_transform, _ = read(monthly_path)
                if not monthly_transform.almost_equals(transform) or observed.shape != shape:
                    raise RuntimeError(f"Grid mismatch for {param} {year}-{month:02d}: {monthly_path}")
                if estimated:
                    observed = observed - offset
                    stats["estimated_months"].setdefault(param, {}).setdefault(str(year), []).append(month)
                record, anomaly, rows = process_month(param, year, month, observed, ctx, transform, crs)
                records[month] = record
                monthly_anomalies.append(anomaly)
                monthly_rows.extend(rows)
                stats["sources"][param]["monthly"][f"{year}-{month:02d}"] = source_rows[-1][4]
                year_floats[(year, month)] = (observed, source_rows[-1][4], "estimate" if estimated else "viirs")
            if not records:
                continue
            product_path = yearly_product_source(param, year)
            product = read(product_path)[0] if product_path else None
            yearly_rows.extend(summarize_year(param, year, records, monthly_anomalies, ctx, stats, transform, crs,
                                              product, product_path.name if product_path else None))

        output = DATA_DIR / "zonal_stats"
        write_csv(output / f"{param}_monthly_zonal.csv",
                  ["year", "month", "zone", "absolute", "climatology", "anomaly", "pixels"], monthly_rows)
        write_csv(output / f"{param}_climatology_zonal.csv",
                  ["month", "zone", "climatology", "pixels", "years"], climatology_rows_for(ctx, climatology_labels))
        write_csv(output / f"{param}_yearly_zonal.csv",
                  ["year", "zone", "anomaly_mean_of_months", "months", "yearly_anomaly_product"], yearly_rows)
        # GitHub Actions inputs: masks, climatology, and the monthly values of the latest (still open) year
        latest = max(year for year, _ in year_floats)
        export_ci_inputs(param, ctx, climatology_labels, transform, crs,
                         {key: value for key, value in year_floats.items() if key[0] == latest})

    # Long-term SST reference (fetch_oisst_reference.py), shown next to the short VIIRS trend.
    reference = DATA_DIR / "zonal_stats" / "oisst_reference.json"
    if reference.exists():
        stats["long_term_reference"] = {"sst": json.loads(reference.read_text(encoding="utf-8"))}

    write_csv(DATA_DIR / "zonal_stats" / "sources.csv",
              ["param", "year", "month", "source", "sensors", "status", "reason"], source_rows)
    stats_path = DATA_DIR / "Yearly_RGB" / "stats.json"
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {stats_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="only audit sources and reproduce the SNAP anomaly products")
    parser.add_argument("--climatology", choices=("viirs", "nasa"), default="viirs",
                        help="viirs: compute from the VIIRS monthly products (default); nasa: E:\\Monthly Climatology")
    args = parser.parse_args()
    if args.check:
        check_sources()
    else:
        build(args.climatology)
