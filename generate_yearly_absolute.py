#!/usr/bin/env python3
"""Create yearly absolute rasters and EEZ statistics from monthly ENVI rasters."""

import json
import os
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.mask import mask


PROJECT_DIR = Path(__file__).resolve().parent
MONTHLY_DIR = Path(os.environ.get("VIIRS_MONTHLY_SOURCE_DIR", r"E:\SST_Chlor\Monthly"))
CLIMATOLOGY_DIR = Path(os.environ.get("VIIRS_CLIMATOLOGY_DIR", r"E:\Monthly Climatology"))
ZONE_DIR = Path(os.environ.get("VIIRS_MARINE_ZONES_DIR", r"E:\SST_Chlor\EEZ_MarineZone"))
OUTPUT_DIR = Path(os.environ.get("VIIRS_YEARLY_DIR", PROJECT_DIR / "data" / "Yearly_RGB"))
YEARS = range(2018, 2027)

OVERALL_FILE = "1_Marine_Zone_Andaman_GoT.shp"
ZONE_FILES = {
    "upper_gulf": "2_Marine_Zone_GoT_GULF1.shp",
    "rayong": "3_Marine_Zone_GoT_GULF21.shp",
    "trat": "4_Marine_Zone_GoT_GULF31.shp",
    "central_gulf": "5_Marine_Zone_GoT_GULF3.shp",
    "lower_gulf": "6_Marine_Zone_GoT_GULF4.shp",
    "andaman": "7_Marine_Zone_Andaman_GULF41.shp",
}


def source_files(param, year):
    folder = "SST_4km" if param == "sst" else "Chlor_a_4km"
    name = "sst_mean.img" if param == "sst" else "chlor_a_mean.img"
    return sorted((MONTHLY_DIR / folder / str(year)).glob(f"*/{name}"))


def climatology_files(param):
    folder = "SST_4km" if param == "sst" else "Chlor_a_4km"
    name = "sst_mean.img" if param == "sst" else "chlor_a_mean.img"
    return sorted((CLIMATOLOGY_DIR / folder).glob(f"*/{name}"))


def colorize(values, minimum, maximum):
    colors = {
        "sst": [[0.0, [0, 0, 255]], [0.214, [35, 7, 241]], [2.606, [10, 5, 181]],
                [5.003, [9, 69, 105]], [7.4, [7, 111, 162]], [9.614, [14, 170, 168]],
                [12.006, [16, 220, 230]], [14.403, [18, 225, 179]], [16.8, [15, 189, 113]],
                [19.014, [10, 142, 74]], [21.406, [45, 153, 3]], [23.803, [116, 203, 11]],
                [26.2, [222, 229, 8]], [28.414, [220, 167, 5]], [30.806, [217, 73, 9]],
                [33.203, [178, 10, 5]], [35.6, [106, 22, 17]], [37.814, [129, 67, 62]],
                [40.206, [159, 110, 109]], [42.603, [183, 159, 159]], [45.0, [0, 0, 0]]],
        "chl": [[0.0, [147, 0, 108]], [0.01, [147, 0, 108]], [0.014, [111, 0, 144]],
                [0.021, [72, 0, 183]], [0.031, [33, 0, 222]], [0.046, [0, 10, 255]],
                [0.065, [0, 74, 255]], [0.096, [0, 144, 255]], [0.142, [0, 213, 255]],
                [0.209, [0, 255, 215]], [0.299, [0, 255, 119]], [0.44, [0, 255, 15]],
                [0.649, [96, 255, 0]], [0.956, [200, 255, 0]], [1.368, [255, 235, 0]],
                [2.014, [255, 183, 0]], [2.968, [255, 131, 0]], [4.373, [255, 79, 0]],
                [6.256, [255, 31, 0]], [9.211, [230, 0, 0]], [13.573, [165, 0, 0]],
                [20.0, [105, 0, 0]]],
    }["sst" if maximum == 40 else "chl"]
    stops = np.array([value for value, _ in colors], dtype=float)
    colors = np.array([color for _, color in colors])
    valid = ~np.ma.getmaskarray(values)
    numeric = values.filled(np.nan)
    positions = np.interp(np.nan_to_num(numeric, nan=minimum), stops, np.arange(len(stops)))
    low = np.floor(positions).astype(int)
    high = np.minimum(low + 1, len(colors) - 1)
    fraction = positions - low
    rgb = np.zeros((3, values.shape[0], values.shape[1]), dtype=np.uint8)
    for band in range(3):
        band_values = colors[low, band] + fraction * (colors[high, band] - colors[low, band])
        rgb[band][valid] = band_values[valid].astype(np.uint8)
    return rgb


def colorize_anomaly(values, param):
    stops = (
        [-5, -4.5, -4, -3.5, -3, -2.5, -2, -1.5, -1, -0.5, 0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]
        if param == "sst"
        else [-20, -18, -16, -14, -12, -10, -8, -6, -4, -2, 0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
    )
    colors = np.array(
        [[0, 0, 100], [5, 5, 130], [20, 20, 165], [30, 42, 195], [33, 70, 225],
         [37, 110, 249], [48, 153, 255], [75, 200, 255], [140, 235, 255], [200, 250, 255],
         [255, 255, 255], [255, 250, 170], [255, 237, 80], [255, 210, 30], [255, 160, 10],
         [250, 105, 4], [240, 53, 1], [210, 16, 0], [165, 3, 0], [135, 0, 0], [110, 0, 0]],
        dtype=float,
    )
    if param == "chl":
        colors = np.array(
            [[0, 0, 100], [5, 5, 130], [20, 20, 165], [30, 42, 195], [33, 70, 225],
             [37, 110, 249], [48, 153, 255], [75, 200, 255], [140, 235, 255], [200, 250, 255],
             [255, 255, 255], [255, 250, 170], [255, 237, 80], [255, 210, 30], [255, 160, 10],
             [250, 105, 4], [240, 53, 1], [210, 16, 0], [165, 3, 0], [135, 0, 0], [110, 0, 0]],
            dtype=float,
        )
    numeric = np.ma.masked_invalid(values)
    positions = np.interp(numeric.filled(0), stops, np.arange(len(stops)))
    low = np.floor(positions).astype(int)
    high = np.minimum(low + 1, len(colors) - 1)
    fraction = positions - low
    rgb = np.zeros((3, values.shape[0], values.shape[1]), dtype=np.uint8)
    valid = ~np.ma.getmaskarray(numeric)
    for band in range(3):
        channel = colors[low, band] + fraction * (colors[high, band] - colors[low, band])
        rgb[band][valid] = channel[valid].astype(np.uint8)
    return rgb


def main():
    stats_path = OUTPUT_DIR / "stats.json"
    stats = json.loads(stats_path.read_text(encoding="utf-8")) if stats_path.exists() else {"years": list(YEARS)}
    stats["years"] = list(YEARS)
    stats["absolute"] = {"sst": {}, "chl": {}}
    stats["trend"] = {"absolute": {}, "anomaly": {}}
    stats["baseline"] = {}
    monthly_records = {"sst": {}, "chl": {}}
    monthly_arrays = {"sst": {}, "chl": {}}
    annual_arrays = {"sst": {}, "chl": {}}
    overall_path = ZONE_DIR / OVERALL_FILE
    if not overall_path.exists():
        raise RuntimeError(f"Overall EEZ polygon was not found: {overall_path}")
    overall_geometry = gpd.read_file(overall_path).geometry.iloc[0]
    zones = []
    for zone_id, filename in ZONE_FILES.items():
        path = ZONE_DIR / filename
        if path.exists():
            zones.append((zone_id, gpd.read_file(path).geometry.iloc[0]))

    ranges = {"sst": (0, 40), "chl": (0, 20)}
    for param in ("sst", "chl"):
        for year in YEARS:
            paths = source_files(param, year)
            if not paths:
                continue
            with rasterio.open(paths[0]) as template:
                zone_masks = {
                    zone_id: mask(template, [geometry], crop=False, filled=False)[0].mask
                    for zone_id, geometry in zones
                }
                if not zone_masks:
                    raise RuntimeError("No EEZ Marine Zone polygons were found")
                eez_mask = mask(template, [overall_geometry], crop=False, filled=False)[0].mask
                arrays = []
                for path in paths:
                    with rasterio.open(path) as dataset:
                        monthly_values = np.ma.masked_invalid(dataset.read(1, masked=True))
                        arrays.append(monthly_values)
                        monthly_valid = np.ma.array(
                            monthly_values,
                            mask=np.ma.getmaskarray(monthly_values) | eez_mask,
                        ).compressed()
                        if monthly_valid.size:
                            monthly_record = {"mean": float(monthly_valid.mean()), "zones": {}}
                            for zone_id, zone_mask in zone_masks.items():
                                zone_valid = np.ma.array(monthly_values, mask=np.ma.getmaskarray(monthly_values) | zone_mask).compressed()
                                if zone_valid.size:
                                    monthly_record["zones"][zone_id] = float(zone_valid.mean())
                            monthly_records[param].setdefault(year, []).append(monthly_record)
                values = np.ma.mean(np.ma.stack(arrays), axis=0)
                values = np.ma.masked_invalid(values)
                monthly_arrays[param][year] = arrays
                annual_arrays[param][year] = values
    for param in ("sst", "chl"):
        available = monthly_records[param]
        stats["trend"]["absolute"][param] = {}
        stats["trend"]["anomaly"][param] = {}
        climatology_paths = climatology_files(param)
        if len(climatology_paths) != 12:
            raise RuntimeError(
                f"Expected 12 monthly climatology rasters for {param}, found {len(climatology_paths)}"
            )
        climatology_arrays = []
        climatology = []
        zone_climatology = {zone_id: [] for zone_id in ZONE_FILES}
        with rasterio.open(climatology_paths[0]) as template:
            for path in climatology_paths:
                with rasterio.open(path) as dataset:
                    values = np.ma.masked_invalid(dataset.read(1, masked=True))
                climatology_arrays.append(values)
                eez_values = np.ma.array(
                    values,
                    mask=np.ma.getmaskarray(values) | eez_mask,
                ).compressed()
                climatology.append(float(eez_values.mean()) if eez_values.size else None)
                for zone_id, zone_mask in zone_masks.items():
                    zone_values = np.ma.array(
                        values,
                        mask=np.ma.getmaskarray(values) | zone_mask,
                    ).compressed()
                    zone_climatology[zone_id].append(
                        float(zone_values.mean()) if zone_values.size else None
                    )
        valid_climatology = [value for value in climatology if value is not None]
        stats["baseline"][param] = float(np.mean(valid_climatology)) if valid_climatology else None
        stats[param] = {}
        for year, records in available.items():
            absolute_months = [item["mean"] for item in records if np.isfinite(item["mean"])]
            absolute_zone_values = {
                zone_id: [item["zones"][zone_id] for item in records if zone_id in item["zones"]]
                for zone_id in ZONE_FILES
            }
            stats["trend"]["absolute"][param][str(year)] = {
                "mean": float(np.mean(absolute_months)) if absolute_months else None,
                "zones": {
                    zone_id: float(np.mean(values))
                    for zone_id, values in absolute_zone_values.items()
                    if values
                },
            }
            if year in annual_arrays[param]:
                anomaly_array = np.ma.masked_invalid(
                    np.ma.mean(
                        np.ma.stack([
                            monthly_arrays[param][year][month]
                            - climatology_arrays[month]
                            for month in range(len(monthly_arrays[param][year]))
                        ]),
                        axis=0,
                    )
                )
                anomaly_values = np.array([
                    records_item["mean"] - climatology[index]
                    for index, records_item in enumerate(records)
                    if climatology[index] is not None
                ])
                anomaly_zone_values = {
                    zone_id: [
                        records_item["zones"][zone_id] - zone_climatology[zone_id][index]
                        for index, records_item in enumerate(records)
                        if index < len(zone_climatology.get(zone_id, []))
                        and zone_id in records_item["zones"]
                        and zone_climatology[zone_id][index] is not None
                    ]
                    for zone_id in ZONE_FILES
                }
                anomaly_zones = {}
                with rasterio.open(source_files(param, year)[0]) as template:
                    for zone_id, geometry in zones:
                        zone_mask = mask(template, [geometry], crop=False, filled=False)[0].mask
                        zone_values = np.ma.array(anomaly_array, mask=np.ma.getmaskarray(anomaly_array) | zone_mask).compressed()
                        if zone_values.size:
                            anomaly_zones[zone_id] = float(zone_values.mean())
                record = {
                    "mean": float(np.mean(anomaly_values)) if anomaly_values.size else None,
                    "min": float(np.min(anomaly_values)) if anomaly_values.size else None,
                    "max": float(np.max(anomaly_values)) if anomaly_values.size else None,
                    "zones": anomaly_zones,
                }
                stats["absolute"][param][str(year)] = record
                stats[param][str(year)] = record
                stats["trend"]["absolute"][param][str(year)] = {
                    "mean": record["mean"],
                    "zones": {
                        zone_id: float(np.mean(values))
                        for zone_id, values in anomaly_zone_values.items()
                        if values
                    },
                }
                stats["trend"]["anomaly"][param][str(year)] = {
                    "mean": record["mean"],
                    "zones": {
                        zone_id: float(np.mean(values))
                        for zone_id, values in anomaly_zone_values.items()
                        if values
                    },
                }
            else:
                anomaly_values = np.array([])
                anomaly_zones = {}
            if not anomaly_values.size:
                stats["absolute"][param][str(year)] = {
                    "mean": None, "min": None, "max": None, "zones": {}
                }
        for year, arrays in monthly_arrays[param].items():
            anomaly = np.ma.mean(
                np.ma.stack([arrays[month] - climatology_arrays[month] for month in range(len(arrays))]),
                axis=0,
            )
            anomaly = np.ma.masked_invalid(anomaly)
            absolute_output = OUTPUT_DIR / "absolute" / param / f"{param}_Yearly_Absolute_RGB_{year}.tif"
            absolute_output.parent.mkdir(parents=True, exist_ok=True)
            output = OUTPUT_DIR / param / f"{param}_Yearly_Anomaly_RGB_{year}.tif"
            output.parent.mkdir(parents=True, exist_ok=True)
            template_path = source_files(param, year)[0]
            with rasterio.open(template_path) as template:
                profile = template.profile.copy()
                profile.update(
                    driver="GTiff",
                    count=3,
                    dtype="uint8",
                    compress="lzw",
                    crs=template.crs,
                )
                with rasterio.open(absolute_output, "w", **profile) as target:
                    target.write(colorize_anomaly(anomaly, param))
                with rasterio.open(output, "w", **profile) as target:
                    target.write(colorize_anomaly(anomaly, param))
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
