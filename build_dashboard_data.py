#!/usr/bin/env python3
"""
build_dashboard_data.py
-----------------------
Rebuild every dashboard raster and data/Yearly_RGB/stats.json from the source
products in one pass, so maps and charts always come from the same numbers.

Sources (override with environment variables):
  VIIRS_SOURCE_ANOMALY_DIR   E:\\SST_Chlor\\Anomaly       <P>_Monthly_Anomaly/<YYYY>/<MM or MM_YYYY>/
  VIIRS_SOURCE_MONTHLY_DIR   E:\\SST_Chlor\\Monthly       <P>_4km/<YYYY>/*_<MM>_*_4km.data/<var>_mean.img
  VIIRS_PREPARED_SST_ROOT    E:\\                         <YYYY>/SST_VIIRS_<MM>_*_4km.data/sst_mean.img
                                                         (reprocessed SST; preferred when present, because
                                                          the SST anomaly products were computed from it)
  VIIRS_CLIMATOLOGY_DIR      E:\\Monthly Climatology      <P>_4km/*_VIIRS_<MM>_*.data/<var>_mean.img
  VIIRS_MARINE_ZONES_DIR     E:\\SST_Chlor\\EEZ_MarineZone
  VIIRS_SOURCE_YEARLY_DIR    E:\\SST_Chlor                 <P>_Yearly_Anomaly/<YYYY>/<P>_Yearly_Anomaly_<YYYY>_msk.tif

Outputs:
  data/Anomaly_RGB/<P>/<YYYY>/<MM>/<P>_Anomaly_RGB_<MM>_<YYYY>.tif
  data/Monthly_RGB/<P>/<YYYY>/<MM>/<P>_Monthly_RGB_<MM>_<YYYY>.tif
  data/Yearly_RGB/{sst,chl}/<p>_Yearly_Anomaly_RGB_<YYYY>.tif
  data/Yearly_RGB/absolute/{sst,chl}/<p>_Yearly_Absolute_RGB_<YYYY>.tif   (annual mean of SST - climatology)
  data/Yearly_RGB/stats.json
  data/zonal_stats/<p>_monthly_zonal.csv       year, month, zone, absolute, climatology, anomaly, pixels
  data/zonal_stats/<p>_climatology_zonal.csv   month, zone, climatology, pixels, source
  data/zonal_stats/<p>_yearly_zonal.csv        year, zone, mean of monthly anomalies, yearly anomaly product

Usage:
  python build_dashboard_data.py            # rebuild everything
  python build_dashboard_data.py --check    # only verify sources (anomaly == monthly - climatology)
"""

import argparse
import csv
import glob
import json
import os
import re
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
ANOMALY_SRC = Path(os.environ.get("VIIRS_SOURCE_ANOMALY_DIR", r"E:\SST_Chlor\Anomaly"))
MONTHLY_SRC = Path(os.environ.get("VIIRS_SOURCE_MONTHLY_DIR", r"E:\SST_Chlor\Monthly"))
PREPARED_SST_ROOT = Path(os.environ.get("VIIRS_PREPARED_SST_ROOT", "E:\\"))
CLIMATOLOGY_DIR = Path(os.environ.get("VIIRS_CLIMATOLOGY_DIR", r"E:\Monthly Climatology"))
YEARLY_SRC = Path(os.environ.get("VIIRS_SOURCE_YEARLY_DIR", r"E:\SST_Chlor"))
ZONE_DIR = Path(os.environ.get("VIIRS_MARINE_ZONES_DIR", r"E:\SST_Chlor\EEZ_MarineZone"))
YEARS = range(2018, 2027)

# Same zone order and shapefiles as server.py; file 1 is the whole EEZ.
OVERALL_FILE = "1_Marine_Zone_Andaman_GoT.shp"
ZONE_FILES = {
    "upper_gulf": "2_Marine_Zone_GoT_GULF1.shp",
    "rayong": "3_Marine_Zone_GoT_GULF21.shp",
    "trat": "4_Marine_Zone_GoT_GULF31.shp",
    "central_gulf": "5_Marine_Zone_GoT_GULF3.shp",
    "lower_gulf": "6_Marine_Zone_GoT_GULF4.shp",
    "andaman": "7_Marine_Zone_Andaman_GULF41.shp",
}

PARAMS = {
    "sst": {"folder": "SST", "var": "sst_mean", "palette": SST_PALETTE, "anomaly_palette": SST_ANOMALY_PALETTE},
    "chl": {"folder": "Chlor_a", "var": "chlor_a_mean", "palette": CHLOR_A_PALETTE, "anomaly_palette": CHL_ANOMALY_PALETTE},
}


def read(path):
    with rasterio.open(path) as dataset:
        values = np.ma.masked_invalid(dataset.read(1, masked=True).astype("float32"))
        return values, dataset.transform, dataset.crs


def first(pattern):
    matches = sorted(glob.glob(str(pattern)))
    return Path(matches[0]) if matches else None


def anomaly_source(param, year, month):
    folder = PARAMS[param]["folder"]
    base = ANOMALY_SRC / f"{folder}_Monthly_Anomaly" / str(year)
    for month_dir in (base / f"{month:02d}", base / f"{month:02d}_{year}"):
        for name in (
            f"{folder}_Monthly_Anomaly_{month:02d}_{year}_msk.tif",
            f"{folder}_Monthly_Anomaly_{month:02d}_{year}.tif",
        ):
            if (month_dir / name).exists():
                return month_dir / name
    return None


def monthly_source(param, year, month):
    folder, var = PARAMS[param]["folder"], PARAMS[param]["var"]
    if param == "sst":
        prepared = first(PREPARED_SST_ROOT / str(year) / f"SST_VIIRS_{month:02d}_*_4km.data" / f"{var}.img")
        if prepared:
            return prepared
    return first(MONTHLY_SRC / f"{folder}_4km" / str(year) / f"{folder}_VIIRS_{month:02d}_*_4km.data" / f"{var}.img")


def climatology_source(param, month):
    folder, var = PARAMS[param]["folder"], PARAMS[param]["var"]
    return first(CLIMATOLOGY_DIR / f"{folder}_4km" / f"{folder}_VIIRS_{month:02d}_*.data" / f"{var}.img")


def yearly_product_source(param, year):
    folder = PARAMS[param]["folder"]
    return first(YEARLY_SRC / f"{folder}_Yearly_Anomaly" / str(year) / f"{folder}_Yearly_Anomaly_{year}_msk.tif")


def write_rgb(path, rgb, transform, crs):
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path, "w", driver="GTiff", height=rgb.shape[1], width=rgb.shape[2], count=3,
        dtype="uint8", crs=crs, transform=transform, compress="lzw",
    ) as target:
        target.write(rgb)


def zone_masks(shape, transform):
    """Boolean 'inside' masks (pixel centres, all_touched=False) for the EEZ and each zone."""
    def inside(filename):
        geometry = gpd.read_file(ZONE_DIR / filename).to_crs(4326).geometry.union_all()
        return ~geometry_mask([geometry], out_shape=shape, transform=transform, all_touched=False)
    return inside(OVERALL_FILE), {zone_id: inside(filename) for zone_id, filename in ZONE_FILES.items()}


def zone_mean(values, inside):
    selected = values[inside]
    return float(selected.mean()) if selected.count() else None


def zone_count(values, inside):
    return int(values[inside].count())


def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for row in rows:
            writer.writerow(["" if value is None else round(value, 6) if isinstance(value, float) else value
                             for value in row])


def mean_or_none(values):
    values = [value for value in values if value is not None]
    return float(np.mean(values)) if values else None


def check_sources():
    """Verify every anomaly product equals monthly - climatology on the same grid."""
    problems = []
    for param in PARAMS:
        climatology = {month: read(climatology_source(param, month))[0] for month in range(1, 13)}
        for year in YEARS:
            for month in range(1, 13):
                anomaly_path, monthly_path = anomaly_source(param, year, month), monthly_source(param, year, month)
                if not anomaly_path or not monthly_path:
                    continue
                anomaly, anomaly_transform, _ = read(anomaly_path)
                monthly, monthly_transform, _ = read(monthly_path)
                difference = np.ma.abs((monthly - climatology[month]) - anomaly)
                worst = float(difference.max()) if difference.count() else 0.0
                if worst > 1e-3 or anomaly_transform != monthly_transform:
                    problems.append(f"{param} {year}-{month:02d}: max |monthly - climatology - anomaly| = {worst:.3f}")
    print("\n".join(problems) if problems else "All anomaly products equal monthly - climatology.")
    return not problems


def build():
    stats = {"years": list(YEARS), "sst": {}, "chl": {}, "absolute": {"sst": {}, "chl": {}},
             "baseline": {}, "trend": {"absolute": {}, "anomaly": {}, "monthly_absolute": {}}, "monthly": {},
             "climatology": {}, "yearly_product": {}, "sources": {}}
    for param, config in PARAMS.items():
        folder = config["folder"]
        climatology = {}
        for month in range(1, 13):
            path = climatology_source(param, month)
            climatology[month] = read(path)[0]
            stats["sources"].setdefault(param, {}).setdefault("climatology", {})[month] = path.parent.name
        template = read(climatology_source(param, 1))
        overall_mask, masks = zone_masks(template[0].shape, template[1])
        stats["baseline"][param] = mean_or_none([zone_mean(climatology[month], overall_mask) for month in range(1, 13)])
        for key in ("absolute", "anomaly", "monthly_absolute"):
            stats["trend"][key][param] = {}
        stats["monthly"][param] = {}
        all_zones = [("overall", overall_mask), *masks.items()]
        monthly_rows, yearly_rows = [], []
        ever_valid = np.zeros(template[0].shape, dtype=bool)

        for year in YEARS:
            monthly_anomalies, records = [], {}
            for month in range(1, 13):
                anomaly_path, monthly_path = anomaly_source(param, year, month), monthly_source(param, year, month)
                if not anomaly_path or not monthly_path:
                    continue
                anomaly, transform, crs = read(anomaly_path)
                monthly, monthly_transform, _ = read(monthly_path)
                if monthly_transform != transform or monthly.shape != anomaly.shape:
                    raise RuntimeError(f"Grid mismatch for {param} {year}-{month:02d}")
                # Absolute values are shown only where the anomaly product is valid (same land mask).
                monthly = np.ma.array(monthly, mask=np.ma.getmaskarray(monthly) | np.ma.getmaskarray(anomaly))
                mm = f"{month:02d}"
                write_rgb(DATA_DIR / "Anomaly_RGB" / folder / str(year) / mm / f"{folder}_Anomaly_RGB_{mm}_{year}.tif",
                          colorize_anomaly(anomaly, config["anomaly_palette"]), transform, crs)
                write_rgb(DATA_DIR / "Monthly_RGB" / folder / str(year) / mm / f"{folder}_Monthly_RGB_{mm}_{year}.tif",
                          apply_color_palette(monthly, config["palette"]), transform, crs)
                monthly_anomalies.append(anomaly)
                ever_valid |= ~np.ma.getmaskarray(anomaly)
                records[month] = {
                    "absolute_mean": zone_mean(monthly, overall_mask),
                    "anomaly_mean": zone_mean(anomaly, overall_mask),
                    "absolute_zones": {zone_id: zone_mean(monthly, mask) for zone_id, mask in masks.items()},
                    "anomaly_zones": {zone_id: zone_mean(anomaly, mask) for zone_id, mask in masks.items()},
                }
                for zone_id, mask in all_zones:
                    absolute_value, anomaly_value = zone_mean(monthly, mask), zone_mean(anomaly, mask)
                    monthly_rows.append([year, month, zone_id, absolute_value,
                                         None if absolute_value is None else absolute_value - anomaly_value,
                                         anomaly_value, zone_count(anomaly, mask)])
                stats["sources"][param].setdefault("monthly", {})[f"{year}-{mm}"] = str(monthly_path.parent.parent)
                print(f"{param} {year}-{mm}: EEZ mean {records[month]['absolute_mean']:.3f}, "
                      f"anomaly {records[month]['anomaly_mean']:+.3f}", flush=True)
            if not records:
                continue

            months = sorted(records)
            stats["monthly"][param][str(year)] = {
                "absolute": {"zones": {z: [records.get(m, {}).get("absolute_zones", {}).get(z) for m in range(1, 13)] for z in ZONE_FILES}},
                "anomaly": {"zones": {z: [records.get(m, {}).get("anomaly_zones", {}).get(z) for m in range(1, 13)] for z in ZONE_FILES}},
                "available_months": months,
            }
            anomaly_means = [records[m]["anomaly_mean"] for m in months if records[m]["anomaly_mean"] is not None]
            anomaly_zone_values = {z: [records[m]["anomaly_zones"][z] for m in months if records[m]["anomaly_zones"][z] is not None] for z in ZONE_FILES}
            absolute_zone_values = {z: [records[m]["absolute_zones"][z] for m in months if records[m]["absolute_zones"][z] is not None] for z in ZONE_FILES}
            record = {
                "mean": mean_or_none(anomaly_means),
                "min": float(min(anomaly_means)) if anomaly_means else None,
                "max": float(max(anomaly_means)) if anomaly_means else None,
                "zones": {z: float(np.mean(v)) for z, v in anomaly_zone_values.items() if v},
            }
            stats[param][str(year)] = record
            stats["absolute"][param][str(year)] = record
            anomaly_trend = {
                "mean": record["mean"],
                "zones": record["zones"],
                "months": len(anomaly_means),
                "zone_months": {z: len(v) for z, v in anomaly_zone_values.items()},
            }
            stats["trend"]["anomaly"][param][str(year)] = anomaly_trend
            stats["trend"]["absolute"][param][str(year)] = anomaly_trend
            absolute_means = [records[m]["absolute_mean"] for m in months if records[m]["absolute_mean"] is not None]
            stats["trend"]["monthly_absolute"][param][str(year)] = {
                "mean": mean_or_none(absolute_means),
                "zones": {z: float(np.mean(v)) for z, v in absolute_zone_values.items() if v},
                "months": len(absolute_means),
                "zone_months": {z: len(v) for z, v in absolute_zone_values.items()},
            }

            # Annual raster = pixel-wise mean of the available monthly anomalies (SST - climatology).
            annual = np.ma.masked_invalid(np.ma.stack(monthly_anomalies).mean(axis=0))
            rgb = colorize_anomaly(annual, config["anomaly_palette"])
            write_rgb(DATA_DIR / "Yearly_RGB" / param / f"{param}_Yearly_Anomaly_RGB_{year}.tif", rgb, transform, crs)
            write_rgb(DATA_DIR / "Yearly_RGB" / "absolute" / param / f"{param}_Yearly_Absolute_RGB_{year}.tif", rgb, transform, crs)

            # Zonal means of the yearly anomaly product, kept next to the monthly-derived values for comparison.
            product_path = yearly_product_source(param, year)
            product = read(product_path)[0] if product_path else None
            if product is not None:
                stats["yearly_product"].setdefault(param, {})[str(year)] = {
                    "mean": zone_mean(product, overall_mask),
                    "zones": {zone_id: zone_mean(product, mask) for zone_id, mask in masks.items()},
                    "source": product_path.name,
                }
            for zone_id, mask in all_zones:
                derived = record["mean"] if zone_id == "overall" else record["zones"].get(zone_id)
                yearly_rows.append([year, zone_id, derived, len(months),
                                    None if product is None else zone_mean(product, mask)])

        # Climatology per zone, on ocean pixels valid in at least one anomaly product (the same land mask).
        climatology_rows, eez_climatology = [], []
        zones_climatology = {zone_id: [] for zone_id in ZONE_FILES}
        for month in range(1, 13):
            values = np.ma.array(climatology[month], mask=np.ma.getmaskarray(climatology[month]) | ~ever_valid)
            for zone_id, mask in all_zones:
                value = zone_mean(values, mask)
                climatology_rows.append([month, zone_id, value, zone_count(values, mask),
                                         stats["sources"][param]["climatology"][month]])
                (eez_climatology if zone_id == "overall" else zones_climatology[zone_id]).append(value)
        stats["climatology"][param] = {
            "eez": eez_climatology,
            "zones": zones_climatology,
            "periods": {month: re.search(r"(\d{4}_\d{4})", name).group(1).replace("_", "-")
                        for month, name in stats["sources"][param]["climatology"].items()},
        }
        output = DATA_DIR / "zonal_stats"
        write_csv(output / f"{param}_monthly_zonal.csv",
                  ["year", "month", "zone", "absolute", "climatology", "anomaly", "pixels"], monthly_rows)
        write_csv(output / f"{param}_climatology_zonal.csv",
                  ["month", "zone", "climatology", "pixels", "source"], climatology_rows)
        write_csv(output / f"{param}_yearly_zonal.csv",
                  ["year", "zone", "anomaly_mean_of_months", "months", "yearly_anomaly_product"], yearly_rows)

    stats_path = DATA_DIR / "Yearly_RGB" / "stats.json"
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {stats_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="only verify the source products")
    args = parser.parse_args()
    if args.check:
        raise SystemExit(0 if check_sources() else 1)
    check_sources()
    build()
