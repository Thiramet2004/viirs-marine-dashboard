#!/usr/bin/env python3
"""Generate yearly anomaly RGB rasters from the prepared numeric sources."""

import json
import os
from pathlib import Path

import numpy as np
import rasterio
from rasterio.mask import mask


PROJECT_DIR = Path(__file__).resolve().parent
SOURCE_DIR = Path(os.environ.get("VIIRS_SOURCE_YEARLY_DIR", "/Volumes/New Volume"))
OUTPUT_DIR = Path(os.environ.get("VIIRS_YEARLY_DIR", PROJECT_DIR / "data" / "Yearly_RGB"))
ZONE_DIR = Path(os.environ.get("VIIRS_MARINE_ZONES_DIR", "/Volumes/New Volume/EEZ_MarineZone"))
YEARS = range(2018, 2026)

PALETTES = {
    "sst": [(-5, (0, 0, 100)), (-4.5, (5, 5, 130)), (-4, (20, 20, 165)), (-3.5, (30, 42, 195)),
            (-3, (33, 70, 225)), (-2.5, (37, 110, 249)), (-2, (48, 153, 255)), (-1.5, (75, 200, 255)),
            (-1, (140, 235, 255)), (-0.5, (200, 250, 255)), (0, (255, 255, 255)), (0.5, (255, 250, 170)),
            (1, (255, 237, 80)), (1.5, (255, 210, 30)), (2, (255, 160, 10)), (2.5, (250, 105, 4)),
            (3, (240, 53, 1)), (3.5, (210, 16, 0)), (4, (165, 3, 0)), (4.5, (135, 0, 0)), (5, (110, 0, 0))],
    "chl": [(-20, (0, 0, 100)), (-18, (5, 5, 130)), (-16, (20, 20, 165)), (-14, (30, 42, 195)),
            (-12, (33, 70, 225)), (-10, (37, 110, 249)), (-8, (48, 153, 255)), (-6, (75, 200, 255)),
            (-4, (140, 235, 255)), (-2, (200, 250, 255)), (0, (255, 255, 255)), (2, (255, 250, 170)),
            (4, (255, 237, 80)), (6, (255, 210, 30)), (8, (255, 160, 10)), (10, (250, 105, 4)),
            (12, (240, 53, 1)), (14, (210, 16, 0)), (16, (165, 3, 0)), (18, (135, 0, 0)), (20, (110, 0, 0))],
}


def colorize(values, palette):
    rgb = np.zeros((3, values.shape[0], values.shape[1]), dtype=np.uint8)
    valid = ~np.ma.getmaskarray(values)
    numeric = values.filled(np.nan)
    for (low, low_color), (high, high_color) in zip(palette, palette[1:]):
        pixels = valid & (numeric >= low) & (numeric < high)
        fraction = (numeric[pixels] - low) / (high - low)
        for band in range(3):
            rgb[band][pixels] = (low_color[band] + fraction * (high_color[band] - low_color[band])).astype(np.uint8)
    for band in range(3):
        rgb[band][valid & (numeric >= palette[-1][0])] = palette[-1][1][band]
        rgb[band][valid & (numeric < palette[0][0])] = palette[0][1][band]
    return rgb


def source_path(param, year):
    if param == "sst":
        return SOURCE_DIR / "SST_Yearly_Anomaly" / str(year) / f"SST_Yearly_Anomaly_{year}_msk.tif"
    return SOURCE_DIR / "Chlor_a_Yearly_Anomaly" / str(year) / f"Chlor_a_Yearly_Anomaly_{year}_msk.tif"


def main():
    stats = {"years": list(YEARS), "sst": {}, "chl": {}}
    zone_files = [
        ("upper_gulf", "1_Marine_Zone_Andaman_GoT.shp"),
        ("rayong", "2_Marine_Zone_GoT_GULF1.shp"),
        ("trat", "3_Marine_Zone_GoT_GULF21.shp"),
        ("central_gulf", "4_Marine_Zone_GoT_GULF31.shp"),
        ("lower_gulf", "5_Marine_Zone_GoT_GULF3.shp"),
        ("andaman", "7_Marine_Zone_Andaman_GULF41.shp"),
    ]
    zones = []
    if ZONE_DIR.exists():
        import geopandas as gpd
        for zone_id, filename in zone_files:
            path = ZONE_DIR / filename
            if path.exists():
                zones.append((zone_id, gpd.read_file(path).geometry.iloc[0]))
    for param in ("sst", "chl"):
        for year in YEARS:
            source = source_path(param, year)
            if not source.exists():
                continue
            with rasterio.open(source) as dataset:
                values = dataset.read(1, masked=True)
                valid = values.compressed()
                record = {"mean": float(valid.mean()), "min": float(valid.min()), "max": float(valid.max()), "zones": {}}
                for zone_id, geometry in zones:
                    zone_values, _ = mask(dataset, [geometry], crop=False, filled=False)
                    zone_valid = zone_values[0].compressed()
                    if zone_valid.size:
                        record["zones"][zone_id] = float(zone_valid.mean())
                stats[param][str(year)] = record
                output = OUTPUT_DIR / param / f"{param}_Yearly_Anomaly_RGB_{year}.tif"
                output.parent.mkdir(parents=True, exist_ok=True)
                with rasterio.open(output, "w", driver="GTiff", height=values.shape[0], width=values.shape[1], count=3,
                                   dtype="uint8", crs=dataset.crs, transform=dataset.transform, compress="lzw") as target:
                    target.write(colorize(values, PALETTES[param]))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated yearly rasters and {OUTPUT_DIR / 'stats.json'}")


if __name__ == "__main__":
    main()