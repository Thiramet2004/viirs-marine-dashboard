#!/usr/bin/env python3
"""
Convert VIIRS Monthly ENVI .img files to RGB GeoTIFF for Web GIS display.
Reads chlor_a_mean.img and sst_mean.img, applies color palettes, exports RGB GeoTIFF.
"""

import numpy as np
import rasterio
from rasterio.transform import Affine
from rasterio.crs import CRS
import os
import sys
from pathlib import Path

# Color palettes for Absolute values (inspired by SNAP ocean color palettes)
# Chl-a: 0-5 mg/m³ (typical range, with extended range up to 10 for coastal outliers)
CHLOR_A_PALETTE = [
    (0.0, (0, 0, 100)),      # Dark blue
    (0.05, (20, 20, 165)),
    (0.1, (33, 70, 225)),
    (0.2, (48, 153, 255)),
    (0.3, (140, 235, 255)),  # Light blue
    (0.5, (200, 250, 255)),  # Very light blue
    (0.7, (255, 250, 170)),  # Pale yellow
    (1.0, (255, 210, 30)),   # Yellow
    (1.5, (250, 105, 4)),    # Orange
    (2.0, (240, 53, 1)),     # Red-orange
    (3.0, (210, 16, 0)),     # Red
    (5.0, (165, 3, 0)),      # Dark red
    (10.0, (110, 0, 0)),     # Very dark red (coastal/outliers)
]

# SST: 20-35°C (extended range to handle outliers, typical 25-32°C)
SST_PALETTE = [
    (20.0, (0, 0, 100)),     # Dark blue (cold outliers)
    (24.0, (20, 20, 165)),
    (25.0, (33, 70, 225)),
    (26.0, (48, 153, 255)),  # Blue
    (27.0, (75, 200, 255)),
    (28.0, (140, 235, 255)), # Light blue
    (29.0, (200, 250, 255)), # Very light blue
    (29.5, (255, 250, 170)), # Pale yellow
    (30.0, (255, 210, 30)),  # Yellow
    (30.5, (250, 105, 4)),   # Orange
    (31.0, (240, 53, 1)),    # Red-orange
    (32.0, (210, 16, 0)),    # Red
    (35.0, (165, 3, 0)),     # Dark red (warm outliers)
]


def read_envi_img(img_path, hdr_path):
    """Read ENVI .img file with georeference from .hdr"""
    
    # Parse .hdr file for georeferencing
    with open(hdr_path, 'r') as f:
        hdr_content = f.read()
    
    # Extract dimensions
    samples = int([line for line in hdr_content.split('\n') if 'samples' in line][0].split('=')[1].strip())
    lines = int([line for line in hdr_content.split('\n') if 'lines' in line][0].split('=')[1].strip())
    
    # Extract map info: {Geographic Lat/Lon,541.5,481.5,104.6875,7.3125,0.04166,0.04166,WGS84,...}
    map_info_line = [line for line in hdr_content.split('\n') if 'map info' in line][0]
    map_info = map_info_line.split('{')[1].split('}')[0].split(',')
    
    # Parse georeferencing
    # map_info format: [projection, x_pixel_ref, y_pixel_ref, x_coord, y_coord, x_pixel_size, y_pixel_size, datum, ...]
    x_ref = float(map_info[1])  # Reference pixel X
    y_ref = float(map_info[2])  # Reference pixel Y
    x_coord = float(map_info[3])  # Geographic X of reference pixel (longitude)
    y_coord = float(map_info[4])  # Geographic Y of reference pixel (latitude)
    pixel_size_x = float(map_info[5])
    pixel_size_y = float(map_info[6])
    
    # Calculate upper-left corner (GDAL convention)
    # Reference pixel is at (x_ref, y_ref) in pixel coordinates (1-indexed)
    # We need upper-left corner of (0, 0) pixel
    ulx = x_coord - (x_ref - 0.5) * pixel_size_x
    uly = y_coord + (y_ref - 0.5) * pixel_size_y  # Y increases downward in image space
    
    # Create affine transform
    transform = Affine.translation(ulx, uly) * Affine.scale(pixel_size_x, -pixel_size_y)
    
    # Read binary .img file (data type 4 = float32, byte order 1 = little-endian BUT actual data is big-endian!)
    # Try big-endian first (SNAP often exports as big-endian despite .hdr saying little-endian)
    data = np.fromfile(img_path, dtype='>f4').reshape((lines, samples))
    
    # Mask NaN and fill values
    data = np.ma.masked_invalid(data)
    
    return data, transform


def apply_color_palette(data, palette):
    """Apply color palette to single-band data, return RGB"""
    
    # Create RGB array
    rgb = np.zeros((3, data.shape[0], data.shape[1]), dtype=np.uint8)
    
    # Sort palette by value
    palette_sorted = sorted(palette, key=lambda x: x[0])
    
    # Apply linear interpolation for each pixel
    for i in range(len(palette_sorted) - 1):
        val_low, color_low = palette_sorted[i]
        val_high, color_high = palette_sorted[i + 1]
        
        # Find pixels in this range
        mask = (data >= val_low) & (data < val_high)
        
        if not np.any(mask):
            continue
        
        # Linear interpolation
        t = (data[mask] - val_low) / (val_high - val_low)
        
        for band in range(3):
            rgb[band][mask] = (
                color_low[band] + t * (color_high[band] - color_low[band])
            ).astype(np.uint8)
    
    # Handle values above max
    val_max, color_max = palette_sorted[-1]
    mask = data >= val_max
    if np.any(mask):
        for band in range(3):
            rgb[band][mask] = color_max[band]
    
    # Handle values below min (shouldn't happen, but just in case)
    val_min, color_min = palette_sorted[0]
    mask = data < val_min
    if np.any(mask):
        for band in range(3):
            rgb[band][mask] = color_min[band]
    
    # Mask invalid/NaN as (0, 0, 0) for land masking
    invalid_mask = data.mask if np.ma.is_masked(data) else np.isnan(data)
    rgb[:, invalid_mask] = 0
    
    return rgb


def get_land_mask_from_anomaly(param, year, month):
    """
    Read land mask from Anomaly RGB GeoTIFF (where (0,0,0) = land)
    Returns: mask array (True = valid ocean, False = land)
    """
    month_str = f"{int(month):02d}"
    
    if param == 'Chlor_a':
        anomaly_path = f"/Volumes/New Volume/04_VIIRS_Monthly/Anomaly/RGB_FINAL/Chlor_a/{year}/{month_str}/Chlor_a_Anomaly_RGB_{month_str}_{year}.tif"
    else:
        anomaly_path = f"/Volumes/New Volume/04_VIIRS_Monthly/Anomaly/RGB_FINAL/SST/{year}/{month_str}/SST_Anomaly_RGB_{month_str}_{year}.tif"
    
    if not os.path.exists(anomaly_path):
        return None
    
    try:
        with rasterio.open(anomaly_path) as src:
            rgb = src.read()  # (3, height, width)
            # Land pixels are (0,0,0) in Anomaly RGB
            land_mask = (rgb[0] == 0) & (rgb[1] == 0) & (rgb[2] == 0)
            ocean_mask = ~land_mask  # True = ocean, False = land
            return ocean_mask
    except:
        return None


def convert_monthly_to_rgb(param, year, month):
    """
    Convert Monthly ENVI .img to RGB GeoTIFF with land masking
    
    Args:
        param: 'Chlor_a' or 'SST'
        year: year as int or str
        month: month as int (1-12)
    """
    
    # Map month to folder name
    month_names = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]
    month_name = month_names[int(month) - 1]
    month_str = f"{int(month):02d}"
    
    # Input paths
    if param == 'Chlor_a':
        base_dir = f"/Volumes/New Volume/04_VIIRS_Monthly/Monthly/Chlor_a_4km/{year}"
        data_folder = f"Chlor_a_VIIRS_{month_str}_{month_name}_{year}_4km.data"
        img_file = "chlor_a_mean.img"
        hdr_file = "chlor_a_mean.hdr"
        palette = CHLOR_A_PALETTE
    else:  # SST
        base_dir = f"/Volumes/New Volume/04_VIIRS_Monthly/Monthly/SST_4km/{year}"
        data_folder = f"SST_VIIRS_{month_str}_{month_name}_{year}_4km.data"
        img_file = "sst_mean.img"
        hdr_file = "sst_mean.hdr"
        palette = SST_PALETTE
    
    img_path = os.path.join(base_dir, data_folder, img_file)
    hdr_path = os.path.join(base_dir, data_folder, hdr_file)
    
    # Check if input exists
    if not os.path.exists(img_path) or not os.path.exists(hdr_path):
        print(f"ERROR: Input not found: {img_path}")
        return None
    
    print(f"Processing: {param} {year}-{month_str}")
    
    # Read ENVI data
    data, transform = read_envi_img(img_path, hdr_path)
    
    print(f"  Data range: {np.nanmin(data):.4f} to {np.nanmax(data):.4f}")
    
    # Get land mask from Anomaly RGB (same param, year, month)
    land_mask = get_land_mask_from_anomaly(param, year, month)
    
    if land_mask is not None:
        # Apply land mask to data (set land pixels to NaN)
        if land_mask.shape == data.shape:
            data = np.ma.masked_where(~land_mask, data)
            print(f"  Applied land mask from Anomaly RGB")
        else:
            print(f"  Warning: Land mask shape mismatch, using NaN mask only")
    else:
        print(f"  Warning: Could not load land mask, using NaN mask only")
    
    # Apply color palette
    rgb = apply_color_palette(data, palette)
    
    # Output path (write to workspace since NTFS volume is read-only)
    output_dir = f"/Users/hellothiramet/viirs-marine-dashboard/data/Monthly_RGB/{param}/{year}/{month_str}"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{param}_Monthly_RGB_{month_str}_{year}.tif")
    
    # Write RGB GeoTIFF
    with rasterio.open(
        output_file,
        'w',
        driver='GTiff',
        height=rgb.shape[1],
        width=rgb.shape[2],
        count=3,
        dtype=rgb.dtype,
        crs=CRS.from_epsg(4326),
        transform=transform,
        compress='lzw'
    ) as dst:
        dst.write(rgb)
    
    print(f"  Saved: {output_file}")
    
    return output_file


def main():
    """Convert all Monthly data to RGB GeoTIFF"""
    
    if len(sys.argv) > 1:
        # Manual mode: convert specific param/year/month
        if len(sys.argv) != 4:
            print("Usage: python convert_monthly_to_rgb.py [param] [year] [month]")
            print("  param: Chlor_a or SST")
            print("  year: 2018-2025")
            print("  month: 1-12")
            print("\nOr run without arguments to convert all available data.")
            sys.exit(1)
        
        param = sys.argv[1]
        year = sys.argv[2]
        month = sys.argv[3]
        
        convert_monthly_to_rgb(param, year, month)
    
    else:
        # Auto mode: convert all available data
        print("Converting all Monthly data to RGB GeoTIFF...")
        print("=" * 60)
        
        years = range(2018, 2026)  # 2018-2025
        months = range(1, 13)
        params = ['Chlor_a', 'SST']
        
        total = 0
        success = 0
        
        for param in params:
            for year in years:
                for month in months:
                    total += 1
                    result = convert_monthly_to_rgb(param, year, month)
                    if result:
                        success += 1
        
        print("=" * 60)
        print(f"Conversion complete: {success}/{total} files processed successfully")


if __name__ == '__main__':
    main()
