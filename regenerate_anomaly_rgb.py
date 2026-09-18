#!/usr/bin/env python3
"""Regenerate monthly anomaly RGB GeoTIFFs using the SLD_wq ramps."""

import os
from pathlib import Path

import numpy as np
import rasterio


PROJECT_DIR = Path(__file__).resolve().parent
SOURCE_DIR = Path(os.environ.get("VIIRS_SOURCE_ANOMALY_DIR", "/Volumes/New Volume/Anomaly"))
OUTPUT_DIR = Path(os.environ.get("VIIRS_ANOMALY_DIR", PROJECT_DIR / "data" / "Anomaly_RGB"))

CHLOR_A_PALETTE = [
    (-20, (0, 0, 100)), (-18, (5, 5, 130)), (-16, (20, 20, 165)), (-14, (30, 42, 195)),
    (-12, (33, 70, 225)), (-10, (37, 110, 249)), (-8, (48, 153, 255)), (-6, (75, 200, 255)),
    (-4, (140, 235, 255)), (-2, (200, 250, 255)), (0, (255, 255, 255)), (2, (255, 250, 170)),
    (4, (255, 237, 80)), (6, (255, 210, 30)), (8, (255, 160, 10)), (10, (250, 105, 4)),
    (12, (240, 53, 1)), (14, (210, 16, 0)), (16, (165, 3, 0)), (18, (135, 0, 0)), (20, (110, 0, 0)),
]

SST_PALETTE = [
    (-5, (0, 0, 100)), (-4.5, (5, 5, 130)), (-4, (20, 20, 165)), (-3.5, (30, 42, 195)),
    (-3, (33, 70, 225)), (-2.5, (37, 110, 249)), (-2, (48, 153, 255)), (-1.5, (75, 200, 255)),
    (-1, (140, 235, 255)), (-0.5, (200, 250, 255)), (0, (255, 255, 255)), (0.5, (255, 250, 170)),
    (1, (255, 237, 80)), (1.5, (255, 210, 30)), (2, (255, 160, 10)), (2.5, (250, 105, 4)),
    (3, (240, 53, 1)), (3.5, (210, 16, 0)), (4, (165, 3, 0)), (4.5, (135, 0, 0)), (5, (110, 0, 0)),
]


def colorize(values, palette):
    rgb = np.zeros((3, values.shape[0], values.shape[1]), dtype=np.uint8)
    valid = ~np.ma.getmaskarray(values)
    numeric = values.filled(np.nan)
    for (low_value, low_color), (high_value, high_color) in zip(palette, palette[1:]):
        pixels = valid & (numeric >= low_value) & (numeric < high_value)
        fraction = (numeric[pixels] - low_value) / (high_value - low_value)
        for band in range(3):
            rgb[band][pixels] = (low_color[band] + fraction * (high_color[band] - low_color[band])).astype(np.uint8)
    for band in range(3):
        rgb[band][valid & (numeric >= palette[-1][0])] = palette[-1][1][band]
        rgb[band][valid & (numeric < palette[0][0])] = palette[0][1][band]
    return rgb


def regenerate(parameter, year, month):
    month_text = f"{month:02d}"
    if parameter == "Chlor_a":
        folder = SOURCE_DIR / "Chlor_a_Monthly_Anomaly" / str(year) / month_text
        source = folder / f"Chlor_a_Monthly_Anomaly_{month_text}_{year}_msk.tif"
        output = OUTPUT_DIR / "Chlor_a" / str(year) / month_text / f"Chlor_a_Anomaly_RGB_{month_text}_{year}.tif"
        palette = CHLOR_A_PALETTE
    else:
        folder = SOURCE_DIR / "SST_Monthly_Anomaly" / str(year) / month_text
        source = folder / f"SST_Monthly_Anomaly_{month_text}_{year}_msk.tif"
        output = OUTPUT_DIR / "SST" / str(year) / month_text / f"SST_Anomaly_RGB_{month_text}_{year}.tif"
        palette = SST_PALETTE
    if not source.exists():
        return False
    with rasterio.open(source) as dataset:
        values = dataset.read(1, masked=True)
        rgb = colorize(values, palette)
        output.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(output, "w", driver="GTiff", height=rgb.shape[1], width=rgb.shape[2], count=3,
                           dtype="uint8", crs=dataset.crs, transform=dataset.transform, compress="lzw") as target:
            target.write(rgb)
    return True


def main():
    converted = 0
    for parameter in ("Chlor_a", "SST"):
        for year in range(2018, 2027):
            for month in range(1, 13):
                if regenerate(parameter, year, month):
                    converted += 1
    print(f"Regenerated {converted} monthly anomaly RGB files")


if __name__ == "__main__":
    main()