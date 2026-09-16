#!/usr/bin/env python3
"""
generate_tiles.py
-----------------
แปลง GeoTIFF (RGB 3-band, EPSG:4326) จาก Anomaly/RGB_FINAL/
→ PNG แบบ RGBA (background โปร่งใส) ตัดเฉพาะพื้นที่อ่าวไทย+อันดามัน
→ บันทึกใน ~/viirs-marine-dashboard/tiles/{chl|sst}/YYYY_MM.png

ใช้งาน:
    python3 generate_tiles.py [--param chl|sst|all] [--year 2025] [--all-years]
"""

import os
import sys
import glob
import argparse
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from PIL import Image

# =============================================
# CONFIG
# =============================================
BASE_DATA = "/Volumes/New Volume/04_VIIRS_Monthly/Anomaly/RGB_FINAL"
OUT_DIR   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tiles")

# Crop bounding box: ครอบ อ่าวไทย + อันดามัน
CROP = dict(west=97.0, east=105.5, south=0.5, north=14.5)

# ปีที่มีข้อมูล
YEARS = list(range(2018, 2027))
MONTHS = range(1, 13)

# Param config
PARAMS = {
    "chl": {
        "folder": "Chlor_a",
        "pattern": "Chlor_a_Anomaly_RGB_{mm:02d}_{yyyy}.tif",
    },
    "sst": {
        "folder": "SST",
        "pattern": "SST_Anomaly_RGB_{mm:02d}_{yyyy}.tif",
    },
}

# =============================================
# HELPERS
# =============================================

def tif_to_rgba_png(tif_path: str, out_path: str, crop: dict):
    """
    โหลด GeoTIFF RGB → crop ตาม bounding box → ทำ alpha (black = transparent)
    → บันทึก PNG RGBA
    """
    with rasterio.open(tif_path) as src:
        # คำนวณ window จาก bounding box
        win = from_bounds(
            left=crop["west"], bottom=crop["south"],
            right=crop["east"], top=crop["north"],
            transform=src.transform
        )
        # อ่าน 3 bands พร้อมกัน
        r = src.read(1, window=win)
        g = src.read(2, window=win)
        b = src.read(3, window=win)

    # สร้าง alpha channel: pixel (0,0,0) = nodata → transparent
    nodata_mask = (r == 0) & (g == 0) & (b == 0)
    alpha = np.where(nodata_mask, 0, 255).astype(np.uint8)

    # Stack เป็น RGBA
    rgba = np.stack([r, g, b, alpha], axis=-1)
    img = Image.fromarray(rgba, mode="RGBA")
    img.save(out_path, "PNG")


def process_param(param: str, years: list):
    cfg = PARAMS[param]
    out_param_dir = os.path.join(OUT_DIR, param)
    os.makedirs(out_param_dir, exist_ok=True)

    ok = 0
    skip = 0
    for year in years:
        for month in MONTHS:
            fname = cfg["pattern"].format(mm=month, yyyy=year)
            tif_path = os.path.join(
                BASE_DATA, cfg["folder"],
                str(year), f"{month:02d}", fname
            )
            if not os.path.exists(tif_path):
                skip += 1
                continue

            out_path = os.path.join(out_param_dir, f"{year}_{month:02d}.png")
            try:
                tif_to_rgba_png(tif_path, out_path, CROP)
                print(f"  ✓ {param} {year}-{month:02d} → {os.path.basename(out_path)}")
                ok += 1
            except Exception as e:
                print(f"  ✗ {param} {year}-{month:02d}: {e}")
                skip += 1

    print(f"\n[{param.upper()}] done: {ok} files, {skip} skipped\n")


# =============================================
# MAIN
# =============================================

def main():
    parser = argparse.ArgumentParser(description="Generate PNG tiles from GeoTIFF")
    parser.add_argument("--param", default="all", choices=["chl", "sst", "all"])
    parser.add_argument("--year", type=int, default=None, help="Process single year")
    parser.add_argument("--all-years", action="store_true", help="Process all years 2018-2026")
    args = parser.parse_args()

    if args.year:
        years = [args.year]
    elif args.all_years:
        years = YEARS
    else:
        years = [2025]  # default: ปีล่าสุด

    params = ["chl", "sst"] if args.param == "all" else [args.param]

    print(f"Processing: params={params}, years={years}")
    print(f"Output dir: {OUT_DIR}\n")

    for p in params:
        process_param(p, years)

    print("All done!")


if __name__ == "__main__":
    main()
