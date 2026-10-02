# VIIRS Marine Dashboard 🌊

Web GIS dashboard for monitoring Sea Surface Temperature (SST) and Chlorophyll-a in the Gulf of Thailand and
the Andaman Sea from VIIRS satellite data, by GISTDA.

**Live:** [Monthly dashboard](https://thiramet2004.github.io/viirs-marine-dashboard/) ·
[Yearly dashboard](https://thiramet2004.github.io/viirs-marine-dashboard/yearly/) ·
[Embed guide](EMBED_GUIDE.md) · [GitHub Pages notes](GITHUB_PAGES_SETUP.md)

## 📋 Overview

- 🗺️ **Interactive map** – monthly absolute and anomaly rasters with click-to-query values, a timeline that
  opens on the newest month, and the 7 EEZ marine-zone boundaries on top
- 📊 **Charts** – monthly time series, monthly anomalies, inter-annual trend with uncertainty and a long-term
  reference, and the SST–Chl-a anomaly relationship, per zone or for all zones
- 📅 **Yearly page** – annual anomaly maps and statistics per zone
- 🌡️ **Parameters** – SST (°C) and Chlorophyll-a (µg/L)
- 📆 **Period** – SST January 2018 – August 2026 (2026 is a MODIS-based estimate, see
  [Known data issues](#known-data-issues)); Chl-a January 2018 – August 2026
- 📁 **Open tables** – every value shown is also in `data/zonal_stats/*.csv`

## 🚀 Quick Start

The dashboard runs on GitHub Pages without a server (links above). To run it locally:

```bash
git clone https://github.com/Thiramet2004/viirs-marine-dashboard.git
cd viirs-marine-dashboard
pip install -r requirements.txt
python server.py          # http://localhost:5001  (yearly page: /yearly)
```

Python 3.9+ is needed; rebuilding the data also needs the source products on `E:` (see
[Updating Data](#-updating-data)).

## 📊 Dashboard Components

| Figure | Content |
|--------|---------|
| Fig. 1 Map | Monthly raster (absolute or anomaly) for the selected month, EEZ zones, click for the pixel value |
| Fig. 2 Monthly time series | All years overlaid with the selected zone's climatology (VIIRS 2018–2025) |
| Fig. 3 Monthly anomaly | Anomaly of each month of the selected year (red above normal, blue below) |
| Fig. 4 Inter-annual trend | Annual means, linear trend from complete years with its 95 % interval, and the NOAA OISST long-term trend for SST. Years with fewer than 12 months are seasonally adjusted (zone climatology + mean anomaly of the available months), drawn as triangles and kept out of the fit |
| Fig. 5 Gulf vs Andaman | Annual values of the whole Gulf of Thailand and the whole Andaman Sea (the two parts of the Thai EEZ), each with its own trend line, 95 % interval and significance, and the Gulf − Andaman difference per year; same partial-year rule as Fig. 4 |
| Fig. 6 SST vs Chl-a | SST and Chl-a anomalies of the selected year on two axes |

"Overall" is the equal-weight mean of the six marine zones. Besides the zones, the area selector has two
whole-sea areas, **อ่าวไทย (ทั้งหมด)** and **ทะเลอันดามัน (ทั้งหมด)**: the Gulf of Thailand and Andaman parts of the
Thai EEZ polygon (`1_Marine_Zone_Andaman_GoT.shp` has exactly these two parts), averaged over all their pixels. Months estimated from MODIS are labelled
"ประมาณการจาก MODIS" in the charts.

### Map display

The rasters are 4 km (1/24°). The browser draws only the visible part of the map at screen resolution and redraws it
after every zoom or pan, so the image is never stretched (sharp at every zoom). Colours are blended between
neighbouring ocean pixels, rows are resampled to Web Mercator so they line up with the basemap (error < 0.5 km),
and land and cloud gaps are never blended, so the coastline and data gaps are exactly the data's 4 km pixels.

## 📁 Project Structure

```
viirs-marine-dashboard/
├── index.html                  # Monthly dashboard
├── index_yearly.html           # Yearly dashboard (served by server.py at /yearly)
├── yearly/index.html           # Yearly dashboard with relative paths (GitHub Pages copy source)
├── embed_dashboard.html        # iframe wrapper with ?mode=map|charts
├── docs/                       # GitHub Pages site (copies of the pages above + assets)
├── server.py                   # Optional local Flask server and API
├── build_dashboard_data.py     # Rebuilds all rasters, stats.json and CSV from the source products
├── download_viirs_monthly.py   # Fills missing months from NASA OB.DAAC (Earthdata login)
├── fetch_oisst_reference.py    # NOAA OISST long-term SST reference for the Thai EEZ
├── convert_monthly_to_rgb.py   # Palettes and colouring used by the build (and the older one-month converter)
├── regenerate_anomaly_rgb.py   # Anomaly palettes and colouring used by the build
├── SLD_wq/                     # SLD colour ramps the palettes are taken from
├── assets/                     # MHESI and GISTDA logos, favicon
├── data/
│   ├── Monthly_RGB/<P>/<YYYY>/<MM>/   # Absolute monthly RGB GeoTIFF
│   ├── Anomaly_RGB/<P>/<YYYY>/<MM>/   # Anomaly monthly RGB GeoTIFF
│   ├── Yearly_RGB/                    # Yearly rasters and stats.json (all chart data)
│   ├── zonal_stats/                   # CSV/JSON tables per EEZ zone, sources, OISST reference
│   └── marine_zones.geojson           # 7 EEZ marine-zone polygons
└── requirements.txt
```

`<P>` is `SST` or `Chlor_a`. Older one-off scripts (`add_raster_map.py`, `fix_map_rgb.py`, `reorder_map.py`,
`update_fig_numbers.py`, `generate_tiles.py`, `generate_yearly_absolute.py`, `regenerate_yearly_rgb.py`) are
superseded by `build_dashboard_data.py` and kept only for history.

## 🛠️ Technical Stack

- **Data processing:** Python – rasterio, numpy, geopandas, scipy, netCDF4 (no SNAP needed)
- **Frontend:** Leaflet 1.9, georaster (GeoTIFF parsing), Chart.js 4; plain HTML/JS, no build step
- **Hosting:** GitHub Pages (`docs/`), data read from `raw.githubusercontent.com`
- **Optional server:** Flask + flask-cors

**Raster format:** 3-band RGB GeoTIFF, LZW, EPSG:4326, 1/24° (≈ 4.6 km), 1080 × 960 pixels,
82.17–127.17 °E, 12.67 °S – 27.33 °N. Black (0, 0, 0) = no data / land.

## 🗺️ Data Sources

| Data | Source |
|------|--------|
| SST, Chl-a | NASA OB.DAAC VIIRS Level-3 monthly, 4 km (Suomi NPP and NOAA-20), binned to the dashboard grid in SNAP (`E:\SST_Chlor\Monthly`) |
| SST 2026 (estimate) | NASA Aqua + Terra MODIS L3 monthly, corrected to VIIRS (see Known data issues) |
| Climatology | Computed from the VIIRS products above, 2018–2025 |
| Long-term SST reference | NOAA OISST v2.1 (NOAA CoastWatch ERDDAP), 1982–present |
| Marine zones | `E:\SST_Chlor\EEZ_MarineZone` (7 polygons), land mask `country_Asean.shp` |

Marine zones: Thai EEZ overall, Upper Gulf (อ่าวไทยตอนบน), Rayong Bay (อ่าวระยอง), Trat Bay (อ่าวตราด),
Central Gulf (อ่าวไทยตอนกลาง), Lower Gulf (อ่าวไทยตอนล่าง), Andaman Sea (ทะเลอันดามัน).

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

- **SST 2026 is an estimate.** Every local 2026 SST file (`E:\SST_Chlor\Monthly\SST_4km\2026`, `E:\2026`) was
  made from Aqua/Terra **MODIS**, not VIIRS. Until VIIRS is downloaded, 2026 SST = MODIS minus the per-pixel
  MODIS − VIIRS offset measured in 2024 (`E:\2024` MODIS vs VIIRS, 11 months, EEZ mean −0.44 °C).
  Leave-one-month-out on 2024: RMSE 0.37 °C per zone-month (0.55 °C uncorrected). Against NOAA OISST the
  Jan–Aug 2026 mean anomaly is +0.09 °C vs +0.20 °C (monthly RMSE 0.26 °C). The dashboard labels these months
  "ประมาณการจาก MODIS"; downloaded VIIRS files replace them automatically.
- `E:\2024` is MODIS and `E:\2025` contains VIIRS data from **2024**; neither is used as observations.
- NOAA-20 SST for 2025 reads about 0.4 °C cooler, relative to NOAA OISST, than in 2019–2024
  (VIIRS − OISST: 0.6–0.9 °C in 2019–2024, 0.3 °C in 2025), so the 2025 SST anomaly is exaggerated by about
  that much. OISST also shows 2025 cooler than average, but by about −0.2 °C rather than −0.6 °C.

### SST trend and the long-term reference

The VIIRS record (2018–2025) is too short for a climate trend: its fitted slope is about −0.7 ± 1.2 °C/decade
(95 % interval, not significant) and turns positive if the biased 2025 is left out. `fetch_oisst_reference.py`
downloads NOAA OISST v2.1 (no login) for the Thai EEZ and writes `data/zonal_stats/oisst_reference.json`, which
the dashboard shows under Fig. 4:

| NOAA OISST, Thai EEZ (103 grid points) | Trend |
|---|---|
| 1982–2025 | +0.15 ± 0.06 °C/decade (p ≈ 10⁻⁶) |
| 2000–2025 | +0.26 ± 0.10 °C/decade |
| 2018–2025 | +0.18 ± 0.90 °C/decade (not significant) |

In this warming record, 9 of the 37 eight-year windows still have a negative slope, so a short negative
VIIRS trend does not contradict long-term warming. (NOAA's server copy of OISST has about half the days
missing in 1994–1998; those years use the available days, and 1998, which lacks Aug–Dec, is left out.)

All outputs are stored as `<YYYY>/<MM>/` folders.

Values extracted per EEZ marine zone (`E:\SST_Chlor\EEZ_MarineZone`, pixel centres inside each polygon) are
also written as CSV in `data/zonal_stats/`:

| File | Contents |
|------|----------|
| `<p>_monthly_zonal.csv` | year, month, zone, absolute mean, climatology, anomaly, valid pixels |
| `<p>_climatology_zonal.csv` | month, zone, climatology (VIIRS 2018–2025), pixels, years used |
| `<p>_yearly_zonal.csv` | year, zone, mean of monthly anomalies, months used, yearly anomaly product (`E:\SST_Chlor\*_Yearly_Anomaly`) |
| `sources.csv` | every month: source file, sensors, used or rejected and why |

`<p>` is `sst` or `chl`; zone `overall` is the whole EEZ (`1_Marine_Zone_Andaman_GoT.shp`), and
`gulf_of_thailand` / `andaman_sea` are its two parts (their pixel counts add up to `overall`).

### Source folder layout

```
E:\SST_Chlor\Monthly\
├── Chlor_a_4km\<YYYY>\Chlor_a_VIIRS_<MM>_<Month>_<YYYY>_4km.data\chlor_a_mean.img
└── SST_4km\<YYYY>\SST_VIIRS_<MM>_<Month>_<YYYY>_4km.data\sst_mean.img
E:\SST_Chlor\EEZ_MarineZone\     1_..7_Marine_Zone_*.shp, country_Asean.shp
E:\2024\                         MODIS SST 2024 (used only to calibrate MODIS against VIIRS)
```

Every path can be changed with the environment variables listed at the top of `build_dashboard_data.py`.

## 🌐 Embedding

Use the GitHub Pages URL in an iframe; `?mode=map` or `?mode=charts` shows one part only:

```html
<iframe src="https://thiramet2004.github.io/viirs-marine-dashboard/?mode=map"
        width="100%" height="900" frameborder="0" loading="lazy"></iframe>
```

More options, sizes and a WordPress shortcode: [EMBED_GUIDE.md](EMBED_GUIDE.md).

## 🔧 API (local server only)

`server.py` serves the same pages plus these endpoints; GitHub Pages reads the files directly instead.

| Endpoint | Returns |
|----------|---------|
| `GET /api/tif/<view>/<param>/<year>/<month>` | Monthly RGB GeoTIFF (`view` = `absolute` or `anomaly`, `param` = `sst` or `chl`) |
| `GET /api/available/<view>/<param>` | Available year-months |
| `GET /api/metadata/<view>/<param>/<year>/<month>` | File name, unit, label, availability |
| `GET /api/yearly/<param>/<year>` | Yearly anomaly GeoTIFF |
| `GET /api/yearly/absolute/<param>/<year>` | Yearly "SST − climatology" GeoTIFF |
| `GET /api/yearly/stats` | `data/Yearly_RGB/stats.json` (all chart data) |
| `GET /api/geojson/marine_zones` | Marine-zone polygons (from the shapefiles, or `data/marine_zones.geojson`) |

Example: `http://localhost:5001/api/tif/anomaly/sst/2025/6`

## 📝 Configuration

Server settings (environment variables, defaults shown):

```bash
VIIRS_PORT=5001        # port
VIIRS_HOST=127.0.0.1   # 0.0.0.0 allows other machines on the network
VIIRS_DEBUG=0          # 1 enables Flask debug mode; never on a shared network
VIIRS_MONTHLY_DIR=data/Monthly_RGB    VIIRS_ANOMALY_DIR=data/Anomaly_RGB    VIIRS_YEARLY_DIR=data/Yearly_RGB
```

The server only serves pages and data files (HTML, JSON/GeoJSON, GeoTIFF, images); source code and
dot-folders such as `.git` are never served.

**Colour ramps** come from `SLD_wq/` and live in `convert_monthly_to_rgb.py` (absolute: `CHLOR_A_PALETTE`,
`SST_PALETTE`) and `regenerate_anomaly_rgb.py` (anomaly). The legends in the pages use the same stops.

## 🐛 Troubleshooting

- **Old page or favicon after an update** – Ctrl+F5; GitHub Pages caches for a few minutes.
- **Map stuck on "กำลังโหลด GeoTIFF..."** – files come from `raw.githubusercontent.com` (≈ 1 MB per month);
  check the browser console and the network.
- **Port 5001 in use (local)** – `netstat -ano | findstr :5001` (Windows) or `lsof -i :5001`, or run on
  another port with `VIIRS_PORT=5002 python server.py`.
- **`PROJ: proj_create_from_database: Cannot find proj.db`** – `PROJ_LIB` points to another installation
  (for example PostGIS). The build still works because the rasters carry a full WGS 84 definition; unset
  `PROJ_LIB` to silence it.
- **A month is missing after a rebuild** – look it up in `data/zonal_stats/sources.csv`; rejected sources
  (MODIS, wrong year) are listed there with the reason.

## 📊 Data Statistics

- **Rasters:** 416 monthly RGB GeoTIFF (208 absolute + 208 anomaly) and 36 yearly, about 450 MB in `data/`
- **Time range:** 2018-01 to 2026-08 for both parameters (SST 2026 estimated from MODIS)
- **Update:** monthly – rebuild, copy pages to `docs/` if changed, push
- **Coverage:** Gulf of Thailand, Andaman Sea and surrounding seas (82–127 °E, 13 °S – 27 °N)
- **Pixel size:** 1/24° (≈ 4.6 km)

## 👥 Authors

- **Thiramet** – [@Thiramet2004](https://github.com/Thiramet2004)

## 🙏 Acknowledgments

- NASA Ocean Biology Processing Group / OB.DAAC for the VIIRS and MODIS Level-3 products
- NOAA NCEI and NOAA CoastWatch for OISST v2.1
- ESA SNAP for the binning of the source products
- Thailand Department of Marine and Coastal Resources for the marine-zone boundaries
- Leaflet, georaster and Chart.js
- Logos: Ministry of Higher Education, Science, Research and Innovation (Wikimedia Commons) and GISTDA

## 📧 Contact

GitHub Issues: https://github.com/Thiramet2004/viirs-marine-dashboard/issues

## 🔗 Related

- [NASA OceanColor](https://oceancolor.gsfc.nasa.gov/) · [NOAA OISST](https://www.ncei.noaa.gov/products/optimum-interpolation-sst)
- [SNAP](https://step.esa.int/main/download/snap-download/) · [Marine GIS Portal](https://marinegis.dmcr.go.th/)
- [GISTDA](https://www.gistda.or.th/)
