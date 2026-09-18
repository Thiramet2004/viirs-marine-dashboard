#!/usr/bin/env python3
"""
server.py
---------
Flask server เสิร์ฟ GeoTIFF files จากโฟลเดอร์ data ใน repository
พร้อม CORS สำหรับ web GIS
รองรับทั้ง Anomaly และ Absolute (Monthly) views

Run:
    python3 server.py

Access:
    http://localhost:5001/
"""

import os
import pandas as pd
from flask import Flask, send_file, abort, send_from_directory, jsonify
from flask_cors import CORS

app = Flask(__name__, static_folder='.')
CORS(app)

# Path config. Defaults are portable and can be overridden in deployment.
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DATA_ANOMALY = os.environ.get(
    "VIIRS_ANOMALY_DIR",
    os.path.join(PROJECT_DIR, "data", "Anomaly_RGB"),
)
BASE_DATA_MONTHLY = os.environ.get(
    "VIIRS_MONTHLY_DIR",
    os.path.join(PROJECT_DIR, "data", "Monthly_RGB"),
)

PARAMS = {
    "chl": "Chlor_a",
    "sst": "SST",
}

VIEWS = {
    "anomaly": BASE_DATA_ANOMALY,
    "absolute": BASE_DATA_MONTHLY,
    "monthly": BASE_DATA_MONTHLY,  # Alias
}

@app.route('/')
def index():
    """Serve index.html"""
    return send_file('index.html')

@app.route('/embed')
def embed():
    """Serve embeddable dashboard"""
    return send_file('embed_dashboard.html')

@app.route('/<path:path>')
def static_files(path):
    """Serve static files (CSS, JS, etc)"""
    return send_from_directory('.', path)

@app.route('/api/geojson/marine_zones')
def get_marine_zones():
    """
    Return Marine Zones as GeoJSON
    """
    try:
        import geopandas as gpd
        
        base = os.environ.get(
            "VIIRS_MARINE_ZONES_DIR",
            "/Volumes/New Volume/EEZ_MarineZone",
        )
        
        # รวม shapefile ทั้งหมด (ยกเว้น country_Asean)
        shapefiles = [
            "1_Marine_Zone_Andaman_GoT.shp",
            "2_Marine_Zone_GoT_GULF1.shp",
            "3_Marine_Zone_GoT_GULF21.shp",
            "4_Marine_Zone_GoT_GULF31.shp",
            "5_Marine_Zone_GoT_GULF3.shp",
            "6_Marine_Zone_GoT_GULF4.shp",
            "7_Marine_Zone_Andaman_GULF41.shp"
        ]
        
        gdfs = []
        for shp in shapefiles:
            path = os.path.join(base, shp)
            if os.path.exists(path):
                gdf = gpd.read_file(path)
                gdfs.append(gdf)
        
        if gdfs:
            combined = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))
            combined = combined[combined.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]
            if combined.empty:
                return jsonify({"error": "EEZ shapefiles contain no polygon geometries"}), 404
            geojson = combined.to_json()
            return geojson, 200, {'Content-Type': 'application/json'}

        return jsonify({"error": "No EEZ polygon shapefiles found"}), 404
            
    except ImportError:
        return jsonify({"error": "geopandas not installed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tif/<view>/<param>/<int:year>/<int:month>')
def get_tif(view, param, year, month):
    """
    Serve GeoTIFF file
    
    Args:
        view: 'anomaly' or 'absolute' (or 'monthly')
        param: 'chl' or 'sst'
        year: year (2018-2025)
        month: month (1-12)
    
    Example:
        /api/tif/anomaly/chl/2025/1 → Chlor_a_Anomaly_RGB_01_2025.tif
        /api/tif/absolute/sst/2024/12 → SST_Monthly_RGB_12_2024.tif
    """
    if view not in VIEWS:
        abort(404, f"Invalid view: {view}. Use 'anomaly' or 'absolute'")
    
    if param not in PARAMS:
        abort(404, f"Invalid param: {param}")
    
    folder = PARAMS[param]
    mm = f"{month:02d}"
    base_data = VIEWS[view]
    
    if param == "chl":
        if view == "anomaly":
            filename = f"Chlor_a_Anomaly_RGB_{mm}_{year}.tif"
        else:
            filename = f"Chlor_a_Monthly_RGB_{mm}_{year}.tif"
    else:
        if view == "anomaly":
            filename = f"SST_Anomaly_RGB_{mm}_{year}.tif"
        else:
            filename = f"SST_Monthly_RGB_{mm}_{year}.tif"
    
    tif_path = os.path.join(base_data, folder, str(year), mm, filename)
    if not os.path.exists(tif_path):
        tif_path = os.path.join(base_data, folder, str(year), filename)
    
    if not os.path.exists(tif_path):
        abort(404, f"File not found: {filename}")
    
    return send_file(tif_path, mimetype='image/tiff')

@app.route('/api/metadata/<view>/<param>/<int:year>/<int:month>')
def get_metadata(view, param, year, month):
    """
    Return metadata about the requested GeoTIFF
    """
    if view not in VIEWS:
        abort(404, f"Invalid view: {view}")
    
    if param not in PARAMS:
        abort(404, f"Invalid param: {param}")
    
    folder = PARAMS[param]
    mm = f"{month:02d}"
    base_data = VIEWS[view]
    
    if param == "chl":
        if view == "anomaly":
            filename = f"Chlor_a_Anomaly_RGB_{mm}_{year}.tif"
            unit = "mg/m³"
            label = "Chlorophyll-a Anomaly"
        else:
            filename = f"Chlor_a_Monthly_RGB_{mm}_{year}.tif"
            unit = "mg/m³"
            label = "Chlorophyll-a (Absolute)"
    else:
        if view == "anomaly":
            filename = f"SST_Anomaly_RGB_{mm}_{year}.tif"
            unit = "°C"
            label = "Sea Surface Temperature Anomaly"
        else:
            filename = f"SST_Monthly_RGB_{mm}_{year}.tif"
            unit = "°C"
            label = "Sea Surface Temperature (Absolute)"
    
    tif_path = os.path.join(base_data, folder, str(year), mm, filename)
    if not os.path.exists(tif_path):
        tif_path = os.path.join(base_data, folder, str(year), filename)
    
    return jsonify({
        "view": view,
        "param": param,
        "year": year,
        "month": month,
        "filename": filename,
        "exists": os.path.exists(tif_path),
        "unit": unit,
        "label": label,
        "path": f"/api/tif/{view}/{param}/{year}/{month}"
    })

@app.route('/api/available/<view>/<param>')
def get_available_dates(view, param):
    """
    List all available year-month combinations for a parameter and view
    """
    if view not in VIEWS:
        abort(404, f"Invalid view: {view}")
    
    if param not in PARAMS:
        abort(404, f"Invalid param: {param}")
    
    folder = PARAMS[param]
    base_data = VIEWS[view]
    base = os.path.join(base_data, folder)
    
    available = []
    if os.path.exists(base):
        for year_dir in sorted(os.listdir(base)):
            year_path = os.path.join(base, year_dir)
            if not os.path.isdir(year_path) or not year_dir.isdigit():
                continue
            
            year = int(year_dir)
            for month_dir in sorted(os.listdir(year_path)):
                month_path = os.path.join(year_path, month_dir)
                if not os.path.isdir(month_path) or not month_dir.isdigit():
                    continue
                
                month = int(month_dir)
                # Check if .tif exists
                if param == "chl":
                    if view == "anomaly":
                        tif_name = f"Chlor_a_Anomaly_RGB_{month:02d}_{year}.tif"
                    else:
                        tif_name = f"Chlor_a_Monthly_RGB_{month:02d}_{year}.tif"
                else:
                    if view == "anomaly":
                        tif_name = f"SST_Anomaly_RGB_{month:02d}_{year}.tif"
                    else:
                        tif_name = f"SST_Monthly_RGB_{month:02d}_{year}.tif"
                
                tif_path = os.path.join(month_path, tif_name)
                if not os.path.exists(tif_path):
                    tif_path = os.path.join(year_path, tif_name)
                if os.path.exists(tif_path):
                    available.append({"year": year, "month": month})
    
    return jsonify({
        "view": view,
        "param": param,
        "count": len(available),
        "dates": available
    })

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 VIIRS Marine Dashboard Server")
    print("=" * 60)
    print(f"📂 Anomaly data: {BASE_DATA_ANOMALY}")
    print(f"📂 Monthly data: {BASE_DATA_MONTHLY}")
    print(f"🌐 Server running at: http://localhost:5001")
    print(f"📊 Available endpoints:")
    print(f"   - GET /")
    print(f"   - GET /api/tif/<view>/<param>/<year>/<month>")
    print(f"   - GET /api/metadata/<view>/<param>/<year>/<month>")
    print(f"   - GET /api/available/<view>/<param>")
    print(f"   - GET /api/geojson/marine_zones")
    print("=" * 60)
    print("Press Ctrl+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
