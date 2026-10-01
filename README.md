# VIIRS Marine Dashboard 🌊

Interactive Web GIS Dashboard for monitoring Sea Surface Temperature (SST) and Chlorophyll-a in the Gulf of Thailand and Andaman Sea using VIIRS satellite data.

![Dashboard Preview](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## 📋 Overview

This dashboard provides comprehensive visualization and analysis of VIIRS (Visible Infrared Imaging Radiometer Suite) satellite data for marine environmental monitoring in Thai waters.

**Features:**
- 🗺️ **Interactive Raster Map** - Browse satellite imagery with pixel-level query capability
- 📊 **Statistical Charts** - 4 interactive charts analyzing marine parameters
- 🌡️ **Dual Parameters** - Sea Surface Temperature (SST) and Chlorophyll-a
- 📈 **Dual Views** - Absolute (Monthly) and Anomaly views
- 🏝️ **Land Masking** - Ocean-only display with transparent land areas
- 🗾 **Marine Zones** - EEZ boundary overlays for 6 marine zones
- 📅 **Time-series Archive** - Monthly SST (January 2018 – December 2025) and Chlorophyll-a (January 2018 – August 2026), absolute and anomaly

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Thiramet2004/viirs-marine-dashboard.git
   cd viirs-marine-dashboard
   ```

2. **Install Python dependencies**
   ```bash
   pip3 install flask flask-cors rasterio geopandas numpy pandas
   ```

3. **Run the server**
   ```bash
   python3 server.py
   ```

4. **Open in browser**
   ```
   http://localhost:5001
   ```

## 📊 Dashboard Components

### Figure 1: Interactive Raster Map
- Real-time GeoTIFF rendering with Leaflet
- Click to query pixel values (lat/lon/value)
- Month slider for temporal navigation
- Marine EEZ zone boundaries overlay

### Figure 2: Monthly Mean Time Series
- Multi-year comparison with climatology baseline
- 8-year average reference line
- Individual year trends

### Figure 3: Monthly Anomaly Bar Chart
- Positive (red) and negative (blue) anomalies
- Deviation from long-term mean
- Quick identification of unusual patterns

### Figure 4: Inter-annual Trend
- Year-to-year changes
- Linear trend with slope calculation
- Long-term climate analysis

### Figure 5: SST-Chl-a Inverse Relationship
- Dual-axis overlay chart
- Inverse correlation visualization
- Anomaly comparison

## 📁 Project Structure

```
viirs-marine-dashboard/
├── server.py                      # Flask server with API endpoints
├── index.html                     # Main dashboard UI
├── convert_monthly_to_rgb.py      # ENVI to RGB GeoTIFF converter
├── embed_dashboard.html           # Embeddable iframe version
├── data/
│   └── Monthly_RGB/               # 192 RGB GeoTIFF files (277 MB)
│       ├── Chlor_a/               # Chlorophyll-a (2018-2025)
│       └── SST/                   # Sea Surface Temperature (2018-2025)
├── data/
│   └── Anomaly_RGB/               # SST and Chlorophyll-a anomaly GeoTIFF files
└── README.md
```

## 🛠️ Technical Stack

### Backend
- **Flask** - Lightweight web server
- **rasterio** - Geospatial raster I/O
- **geopandas** - Vector data processing
- **numpy/pandas** - Data manipulation

### Frontend
- **Leaflet** - Interactive mapping library
- **georaster-layer-for-leaflet** - GeoTIFF rendering
- **Chart.js** - Statistical visualizations
- **geoblaze** - Raster pixel queries

### Data Format
- **RGB GeoTIFF** - 3-band compressed (LZW)
- **EPSG:4326** - WGS84 geographic coordinate system
- **Resolution** - 4 km (~0.04167°)
- **Extent** - 94-111°E, -4-21°N

## 🗺️ Data Sources

### Satellite Data
- **Sensor**: VIIRS (Suomi NPP / NOAA-20)
- **Level**: L3 Monthly Composite
- **Processing**: SNAP ESA Toolbox
- **Parameters**:
  - Sea Surface Temperature (SST) - degrees Celsius
  - Chlorophyll-a concentration - µg/L

### Marine Zones
- Gulf of Thailand Upper (อ่าวไทยตอนบน)
- Rayong Bay (อ่าวระยอง)
- Trat Bay (อ่าวตราด)
- Gulf of Thailand Central (อ่าวไทยตอนกลาง)
- Gulf of Thailand Lower (อ่าวไทยตอนล่าง)
- Andaman Sea (ทะเลอันดามัน)

## 🔧 API Endpoints

### Get GeoTIFF
```http
GET /api/tif/<view>/<param>/<year>/<month>
```
- `view`: `absolute` or `anomaly`
- `param`: `chl` or `sst`
- `year`: 2018-2026, depending on available data
- `month`: 1-12

**Example:**
```
http://localhost:5001/api/tif/absolute/sst/2024/6
```

### Get Metadata
```http
GET /api/metadata/<view>/<param>/<year>/<month>
```

Returns JSON with file info, units, and availability.

### Get Marine Zones
```http
GET /api/geojson/marine_zones
```

Returns combined GeoJSON of all 7 marine zone boundaries.

### Get Available Dates
```http
GET /api/available/<view>/<param>
```

Returns list of all available year-month combinations.

## 🌐 Embedding in Marine GIS Portal

### Option 1: Full iframe (Recommended)
```html
<iframe 
  src="http://localhost:5001/embed_dashboard.html"
  width="100%" 
  height="1200px" 
  frameborder="0"
  style="border: 1px solid #e2e8f0; border-radius: 8px;"
></iframe>
```

### Option 2: Map Only
```html
<iframe 
  src="http://localhost:5001/embed_dashboard.html?mode=map"
  width="100%" 
  height="600px" 
  frameborder="0"
></iframe>
```

### Option 3: Charts Only
```html
<iframe 
  src="http://localhost:5001/embed_dashboard.html?mode=charts"
  width="100%" 
  height="800px" 
  frameborder="0"
></iframe>
```

## 🔄 Updating Data

### Rebuild everything (recommended)

`build_dashboard_data.py` computes everything in Python (no SNAP) from the VIIRS monthly products in
`E:\SST_Chlor\Monthly` and writes all monthly anomaly/absolute RGB GeoTIFFs, the yearly rasters,
`data/Yearly_RGB/stats.json` and the CSV tables in one pass, so the maps and charts always use the same numbers.

```bash
python build_dashboard_data.py --check   # audit sources + reproduce the SNAP anomaly products
python build_dashboard_data.py           # rebuild rasters, stats.json and CSV
```

Method:

1. **Source check** – the `.dim` of every monthly product lists the NASA files it was made from. Only VIIRS
   (SNPP / NOAA-20 / NOAA-21) files of the product's own year and month are accepted; products built from
   MODIS or from another year are rejected. `data/zonal_stats/sources.csv` lists the decision for every month.
2. **Climatology** – per-pixel mean of the accepted products for 2018–2025, the same 8 years for every month
   (a pixel needs at least 4 valid years). `--climatology nasa` uses `E:\Monthly Climatology` instead.
3. **Mask** – land pixels (centres inside `country_Asean.shp`) are removed; for SST, pixels where the observed
   or climatology value is below 26 °C are removed as likely cloud contamination. This is the same rule as the
   SNAP anomaly products for 2018–2023: `--check` reproduces all 144 of them with zero difference.
4. **Anomaly** = monthly − climatology; zonal values are means of pixel centres inside each EEZ zone.

### Filling missing months from NASA (no SNAP)

`download_viirs_monthly.py` downloads NASA OB.DAAC VIIRS L3m monthly files (4 km), cuts them to the dashboard
grid and averages the VIIRS platforms that have data. `build_dashboard_data.py` uses these files for months
whose local product was rejected. It needs a free NASA Earthdata login, given as the `EARTHDATA_TOKEN`
environment variable or in `%USERPROFILE%\_netrc`:

```bash
python download_viirs_monthly.py --param sst --year 2026 --months 1-8
python build_dashboard_data.py
```

### Known data issues

- **SST 2026** is not shown: every local 2026 SST file (`E:\SST_Chlor\Monthly\SST_4km\2026`, `E:\2026`) was
  made from Aqua/Terra **MODIS**, not VIIRS. Run the download above to add VIIRS 2026.
- `E:\2024` is MODIS and `E:\2025` contains VIIRS data from **2024**; neither is used.
- NOAA-20 SST for 2025 reads about 0.4 °C cooler, relative to NOAA OISST, than in 2019–2024
  (VIIRS − OISST: 0.6–0.9 °C in 2019–2024, 0.3 °C in 2025), so the 2025 SST anomaly is exaggerated by about
  that much. OISST also shows 2025 cooler than average, but by about −0.2 °C rather than −0.6 °C.

All outputs are stored as `<YYYY>/<MM>/` folders.

Values extracted per EEZ marine zone (`E:\SST_Chlor\EEZ_MarineZone`, pixel centres inside each polygon) are
also written as CSV in `data/zonal_stats/`:

| File | Contents |
|------|----------|
| `<p>_monthly_zonal.csv` | year, month, zone, absolute mean, climatology, anomaly, valid pixels |
| `<p>_climatology_zonal.csv` | month, zone, climatology (VIIRS 2018–2025), pixels, years used |
| `<p>_yearly_zonal.csv` | year, zone, mean of monthly anomalies, months used, yearly anomaly product (`E:\SST_Chlor\*_Yearly_Anomaly`) |
| `sources.csv` | every month: source file, sensors, used or rejected and why |

`<p>` is `sst` or `chl`; zone `overall` is the whole EEZ (`1_Marine_Zone_Andaman_GoT.shp`).


### Convert New Monthly Data

When new VIIRS data is processed in SNAP:

```bash
# Convert single file
python3 convert_monthly_to_rgb.py Chlor_a 2025 12

# Convert all data for a year
for month in {1..12}; do
  python3 convert_monthly_to_rgb.py Chlor_a 2025 $month
  python3 convert_monthly_to_rgb.py SST 2025 $month
done
```

The converter:
1. Reads ENVI `.img` files from source directory
2. Applies SNAP ocean color palettes
3. Masks land using Anomaly RGB reference
4. Exports to RGB GeoTIFF with LZW compression
5. Saves to `data/Monthly_RGB/`

### Data Requirements

**Source data location:** Set `VIIRS_SOURCE_MONTHLY_DIR` to the folder containing the ENVI source data:
```
<source>/Monthly/
├── Chlor_a_4km/YYYY/
│   └── Chlor_a_VIIRS_MM_MonthName_YYYY_4km.data/
│       └── chlor_a_mean.img
└── SST_4km/YYYY/
    └── SST_VIIRS_MM_MonthName_YYYY_4km.data/
        └── sst_mean.img
```

**Land mask reference:** Set `VIIRS_SOURCE_ANOMALY_DIR` when the source anomaly rasters are outside the repository:
```
<source>/Anomaly/RGB_FINAL/
```

## 📝 Configuration

### Server Port, Host and Debug Mode
Set environment variables (defaults shown):
```bash
VIIRS_PORT=5001        # port
VIIRS_HOST=127.0.0.1   # use 0.0.0.0 to allow other machines on the network
VIIRS_DEBUG=0          # 1 enables Flask debug mode; never enable it on a shared network
```
The server only serves dashboard pages and data files (HTML, JSON/GeoJSON, GeoTIFF, images);
source code and dot-folders such as `.git` are never served.

### Data Paths
Edit `server.py`:
```python
VIIRS_ANOMALY_DIR=/path/to/data/Anomaly_RGB
VIIRS_MONTHLY_DIR=/path/to/data/Monthly_RGB
```

### Color Palettes
Edit `convert_monthly_to_rgb.py`:
```python
CHLOR_A_PALETTE = [
    (0.0, (0, 0, 100)),    # Dark blue
    (0.5, (200, 250, 255)), # Light blue
    (2.0, (240, 53, 1)),    # Red-orange
    # ... customize ranges
]
```

## 🐛 Troubleshooting

### Server won't start
```bash
# Check if port 5001 is in use
lsof -i :5001

# Kill existing process
kill -9 <PID>

# Try different port
VIIRS_PORT=5002 python3 server.py
```

### GeoTIFF not loading
1. Check Flask server logs
2. Verify file exists: `ls data/Monthly_RGB/SST/2024/01/`
3. Test API directly: `curl http://localhost:5001/api/tif/absolute/sst/2024/1`
4. Check browser console for CORS errors

### Land mask not working
1. Ensure Anomaly RGB files exist for the same year/month
2. Verify paths in `convert_monthly_to_rgb.py`
3. Re-run converter with `--force` flag

### Slow performance
1. Enable CORS caching in `server.py`
2. Use nginx as reverse proxy
3. Enable GeoTIFF compression
4. Use CDN for static assets

## 📊 Data Statistics

- **Total Files**: 400 monthly RGB GeoTIFF (200 absolute + 200 anomaly) plus 34 yearly
- **Total Size**: 277 MB (compressed)
- **Average File Size**: 1.5 MB
- **Time Range**: SST 2018-01 to 2025-12, Chl-a 2018-01 to 2026-08
- **Update Frequency**: Monthly
- **Spatial Coverage**: Gulf of Thailand & Andaman Sea
- **Pixel Resolution**: 4 km (0.04167°)

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Thiramet** - *Initial work* - [@Thiramet2004](https://github.com/Thiramet2004)

## 🙏 Acknowledgments

- VIIRS data courtesy of NASA/NOAA
- SNAP ESA Toolbox for data processing
- Marine zones from Thailand Department of Marine and Coastal Resources
- Leaflet community for mapping tools
- Chart.js for visualization components

## 📧 Contact

For questions or support:
- GitHub Issues: https://github.com/Thiramet2004/viirs-marine-dashboard/issues
- Email: [Your email]

## 🔗 Related Projects

- [VIIRS Data Portal](https://oceancolor.gsfc.nasa.gov/)
- [SNAP ESA Toolbox](https://step.esa.int/main/download/snap-download/)
- [Marine GIS Portal](https://marinegis.dmcr.go.th/)

---

**Built with ❤️ for marine environmental monitoring in Thailand** 🇹🇭
