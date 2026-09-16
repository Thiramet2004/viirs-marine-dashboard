#!/usr/bin/env python3
"""
add_raster_map.py
-----------------
เพิ่ม Web GIS Raster Map (Fig. 6) เข้า index.html 
โดยแทรกหลัง Fig. 5 (Dual Chart) ก่อน insight-box
"""

# อ่านไฟล์ index.html ต้นฉบับ
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. เพิ่ม Leaflet + Georaster libraries ใน <head>
HEAD_LIBS = '''<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/georaster@1.6.0/dist/georaster.browser.bundle.min.js"></script>
<script src="https://unpkg.com/proj4@2.11.0/dist/proj4.js"></script>
<script src="https://unpkg.com/georaster-layer-for-leaflet@3.10.0/dist/georaster-layer-for-leaflet.min.js"></script>
<script src="https://unpkg.com/geoblaze@2.8.0/dist/geoblaze.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Thai:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">'''

html = html.replace(
    '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>\n<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Thai:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">',
    HEAD_LIBS
)

# 2. เพิ่ม CSS สำหรับ map
MAP_CSS = '''
/* ===== MAP PANEL (Fig. 6) ===== */
.map-panel{overflow:visible}
.map-param-badge{display:inline-block;font-size:.65rem;font-weight:600;color:#fff;background:var(--green);padding:2px 8px;border-radius:3px;margin-left:8px}
.map-param-badge.sst{background:var(--red)}
.map-controls-bar{display:flex;align-items:center;gap:16px;padding:12px 20px;background:var(--bg2);border-bottom:1px solid var(--border);flex-wrap:wrap}
.map-ctrl-group{display:flex;align-items:center;gap:8px;font-size:.75rem;font-weight:500;color:var(--text2)}
.month-slider{width:180px;accent-color:var(--blue);cursor:pointer}
.map-month-display{font-family:var(--mono);font-size:.82rem;font-weight:700;color:var(--blue);background:var(--blue-bg);padding:4px 12px;border-radius:6px;min-width:120px;text-align:center}
.map-nav-btns{display:flex;gap:4px}
.map-nav-btn{background:var(--white);border:1px solid var(--border);border-radius:6px;padding:4px 8px;cursor:pointer;color:var(--text2);transition:all .15s;display:flex;align-items:center}
.map-nav-btn:hover{background:var(--blue-bg);border-color:var(--blue);color:var(--blue)}
.map-nav-btn .material-icons-outlined{font-size:18px}
.map-body{position:relative;height:480px}
#leafletMap{height:100%;width:100%;background:#1a2744}
.map-legend{position:absolute;bottom:16px;right:12px;background:rgba(255,255,255,.94);backdrop-filter:blur(6px);border:1px solid var(--border);border-radius:8px;padding:12px 16px;min-width:180px;z-index:999;box-shadow:var(--shadow)}
.legend-title{font-size:.7rem;font-weight:700;color:var(--accent);margin-bottom:6px;text-align:center}
.legend-gradient{height:14px;border-radius:4px;margin-bottom:4px;border:1px solid var(--border)}
.legend-ticks{display:flex;justify-content:space-between;font-size:.6rem;font-family:var(--mono);color:var(--dim)}
.click-info{position:absolute;top:16px;right:12px;background:rgba(255,255,255,.96);backdrop-filter:blur(6px);border:1px solid var(--blue);border-radius:8px;padding:10px 14px;z-index:1000;box-shadow:0 4px 12px rgba(37,99,235,.25);display:none;min-width:200px}
.click-info.show{display:block}
.click-info-title{font-size:.68rem;font-weight:700;color:var(--blue);margin-bottom:6px;text-transform:uppercase;letter-spacing:.5px}
.click-info-row{display:flex;justify-content:space-between;font-size:.75rem;margin-bottom:3px;padding:3px 0;border-bottom:1px solid var(--border-lt)}
.click-info-row:last-child{border:none;margin:0}
.click-info-label{color:var(--dim);font-weight:500}
.click-info-value{color:var(--text);font-weight:700;font-family:var(--mono);font-size:.76rem}
.click-info-value.anomaly.positive{color:var(--red)}
.click-info-value.anomaly.negative{color:var(--blue)}
.map-loading{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);background:rgba(255,255,255,.92);padding:12px 18px;border-radius:8px;display:none;align-items:center;gap:8px;font-size:.8rem;color:var(--text2);z-index:10000;box-shadow:var(--shadow)}
.map-loading.show{display:flex}
.leaflet-container{font-family:var(--font)}'''

# แทรก MAP_CSS ก่อน </style>
html = html.replace('</style>', MAP_CSS + '\n</style>')

# 3. เพิ่ม HTML สำหรับ map (Fig. 6) หลัง Fig. 5 ก่อน insight-box
MAP_HTML = '''
<!-- Fig 6: Interactive Raster Map -->
<div class="chart-panel chart-wide map-panel" id="mapSection">
<div class="chart-header">
  <div class="chart-title">
    <span class="fig-num">Fig. 6</span> ภาพดาวเทียม Anomaly แบบ Interactive (Raster Map)
    <span class="map-param-badge" id="mapParamBadge">Chl-a Anomaly</span>
  </div>
  <div class="chart-caption">คลิกบนแผนที่เพื่อดูค่า Anomaly ของจุดนั้น · สีน้ำเงิน = ต่ำกว่าปกติ · สีแดง = สูงกว่าปกติ · ข้อมูลจาก VIIRS SNAP</div>
</div>
<div class="map-controls-bar">
  <div class="map-ctrl-group">
    <label>เดือน:</label>
    <input type="range" id="mapMonthSlider" min="1" max="12" value="1" class="month-slider">
    <span class="map-month-display" id="mapMonthDisplay">มกราคม</span>
  </div>
  <div class="map-nav-btns">
    <button class="map-nav-btn" id="mapPrev" title="เดือนก่อนหน้า"><span class="material-icons-outlined">chevron_left</span></button>
    <button class="map-nav-btn" id="mapNext" title="เดือนถัดไป"><span class="material-icons-outlined">chevron_right</span></button>
  </div>
</div>
<div class="map-body">
  <div id="leafletMap"></div>
  <div class="map-loading" id="mapLoading"><span>กำลังโหลด GeoTIFF...</span></div>
  <div class="click-info" id="clickInfo">
    <div class="click-info-title">📍 Pixel Info</div>
    <div class="click-info-row"><span class="click-info-label">Lat:</span><span class="click-info-value" id="clickLat">—</span></div>
    <div class="click-info-row"><span class="click-info-label">Lon:</span><span class="click-info-value" id="clickLon">—</span></div>
    <div class="click-info-row"><span class="click-info-label">Value:</span><span class="click-info-value anomaly" id="clickValue">—</span></div>
  </div>
  <div class="map-legend">
    <div class="legend-title" id="legendTitle">Chl-a Anomaly</div>
    <div class="legend-gradient" id="legendGradient"></div>
    <div class="legend-ticks" id="legendTicks"><span>-5</span><span>0</span><span>+5</span></div>
  </div>
</div>
<div class="chart-desc">
  <strong>วิธีใช้:</strong> คลิกบนแผนที่เพื่อดูค่า Anomaly ของจุดนั้น ๆ พร้อมพิกัด Lat/Lon ·
  ใช้ slider หรือปุ่ม ◀ ▶ เพื่อเปลี่ยนเดือน · ปีและพารามิเตอร์ตามตัวกรองด้านบน ·
  ข้อมูล GeoTIFF โหลดจาก Flask server (http://localhost:5001)
</div>
</div>

<!-- Insight Summary -->
<div class="insight-box">'''

html = html.replace('<!-- Insight Summary -->\n<div class="insight-box">', MAP_HTML)

# 4. เพิ่ม JavaScript สำหรับ map ก่อน </script> ปิด
MAP_JS = '''
// =============================================
// LEAFLET MAP (Fig. 6)
// =============================================

const API_BASE = 'http://localhost:5001/api';

const PALETTES = {
  chl: {
    label: 'Chl-a Anomaly',
    unit: 'mg/m³',
    min: -5.0,
    max: 5.0,
    stops: [
      [-5.0, [0,0,100]], [-4.5, [5,5,130]], [-4.0, [20,20,165]], [-3.5, [30,42,195]],
      [-3.0, [33,70,225]], [-2.5, [37,110,249]], [-2.0, [48,153,255]], [-1.5, [75,200,255]],
      [-1.0, [140,235,255]], [-0.5, [200,250,255]], [0.0, [255,255,255]],
      [0.5, [255,250,170]], [1.0, [255,237,80]], [1.5, [255,210,30]], [2.0, [255,160,10]],
      [2.5, [250,105,4]], [3.0, [240,53,1]], [3.5, [210,16,0]], [4.0, [165,3,0]],
      [4.5, [135,0,0]], [5.0, [110,0,0]]
    ]
  },
  sst: {
    label: 'SST Anomaly',
    unit: '°C',
    min: -20.0,
    max: 20.0,
    stops: [
      [-20.0, [91,10,118]], [-19.8, [34,8,238]], [-17.7, [8,8,179]], [-15.6, [8,70,104]],
      [-13.4, [8,113,155]], [-11.5, [8,172,172]], [-9.3, [8,225,225]], [-7.2, [8,231,178]],
      [-5.1, [8,193,115]], [-3.1, [8,143,79]], [-1.0, [47,151,8]], [1.2, [110,206,8]],
      [3.3, [223,229,8]], [5.3, [224,166,8]], [7.4, [223,70,8]], [9.5, [182,8,8]],
      [11.6, [112,19,19]], [13.6, [134,64,63]], [15.7, [158,112,111]], [17.9, [182,159,159]],
      [20.0, [0,0,0]]
    ]
  }
};

let leafletMap = null;
let currentMapLayer = null;
let currentMapMonth = 1;

function initLeafletMap() {
  leafletMap = L.map('leafletMap', {
    center: [7.5, 101.25],
    zoom: 6,
    minZoom: 5,
    maxZoom: 10,
  });

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap',
    opacity: 0.35
  }).addTo(leafletMap);

  leafletMap.on('click', onMapClick);
}

function interpolateColor(value, stops) {
  let lower = stops[0];
  let upper = stops[stops.length - 1];

  for (let i = 0; i < stops.length - 1; i++) {
    if (value >= stops[i][0] && value <= stops[i + 1][0]) {
      lower = stops[i];
      upper = stops[i + 1];
      break;
    }
  }

  if (value <= stops[0][0]) return `rgb(${stops[0][1].join(',')})`;
  if (value >= stops[stops.length - 1][0]) return `rgb(${stops[stops.length - 1][1].join(',')})`;

  const [v1, c1] = lower;
  const [v2, c2] = upper;
  const t = (value - v1) / (v2 - v1);

  const r = Math.round(c1[0] + t * (c2[0] - c1[0]));
  const g = Math.round(c1[1] + t * (c2[1] - c1[1]));
  const b = Math.round(c1[2] + t * (c2[2] - c1[2]));

  return `rgb(${r},${g},${b})`;
}

async function loadMapGeoTIFF() {
  const param = currentParam === 'sst' ? 'sst' : 'chl';
  const year = document.getElementById('yearSelect').value;
  const url = `${API_BASE}/tif/${param}/${year}/${currentMapMonth}`;
  
  document.getElementById('mapLoading').classList.add('show');
  document.getElementById('clickInfo').classList.remove('show');
  
  if (currentMapLayer) {
    leafletMap.removeLayer(currentMapLayer);
    currentMapLayer = null;
  }

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    
    const arrayBuffer = await response.arrayBuffer();
    const georaster = await parseGeoraster(arrayBuffer);

    const pal = PALETTES[param];
    
    const pixelValuesToColorFn = values => {
      const val = values[0];
      if (val === null || val === undefined || isNaN(val)) return null;
      return interpolateColor(val, pal.stops);
    };

    currentMapLayer = new GeoRasterLayer({
      georaster: georaster,
      opacity: 0.75,
      pixelValuesToColorFn: pixelValuesToColorFn,
      resolution: 256
    });

    currentMapLayer.addTo(leafletMap);
    
    const bounds = [
      [georaster.ymin, georaster.xmin],
      [georaster.ymax, georaster.xmax]
    ];
    leafletMap.fitBounds(bounds);

    document.getElementById('mapLoading').classList.remove('show');

  } catch (error) {
    console.error('Error loading GeoTIFF:', error);
    document.getElementById('mapLoading').classList.remove('show');
    if (!error.message.includes('404')) {
      alert(`ไม่สามารถโหลด GeoTIFF ได้\\n${error.message}\\n\\nตรวจสอบว่า Flask server รันอยู่ที่ http://localhost:5001`);
    }
  }
}

function onMapClick(e) {
  if (!currentMapLayer || !currentMapLayer.georaster) return;

  const lat = e.latlng.lat;
  const lon = e.latlng.lng;

  try {
    const values = geoblaze.identify(currentMapLayer.georaster, [lon, lat]);
    
    if (values && values[0] !== null && values[0] !== undefined) {
      const val = values[0];
      const param = currentParam === 'sst' ? 'sst' : 'chl';
      const pal = PALETTES[param];
      
      document.getElementById('clickLat').textContent = lat.toFixed(4) + '°';
      document.getElementById('clickLon').textContent = lon.toFixed(4) + '°';
      
      const valueEl = document.getElementById('clickValue');
      const formatted = val.toFixed(3) + ' ' + pal.unit;
      valueEl.textContent = (val > 0 ? '+' : '') + formatted;
      valueEl.className = 'click-info-value anomaly ' + (val > 0 ? 'positive' : 'negative');
      
      document.getElementById('clickInfo').classList.add('show');
    }
  } catch (error) {
    console.error('Error getting pixel value:', error);
  }
}

function updateMapUI() {
  const param = currentParam === 'sst' ? 'sst' : 'chl';
  const pal = PALETTES[param];
  
  document.getElementById('mapParamBadge').textContent = pal.label;
  document.getElementById('mapParamBadge').className = 'map-param-badge' + (param === 'sst' ? ' sst' : '');
  
  document.getElementById('mapMonthDisplay').textContent = monthsFull[currentMapMonth - 1];
  
  document.getElementById('legendTitle').textContent = pal.label + ' (' + pal.unit + ')';
  
  const stops = pal.stops;
  const min = stops[0][0];
  const max = stops[stops.length - 1][0];
  const range = max - min;
  
  const gradientStops = stops.map(([val, rgb]) => {
    const pct = ((val - min) / range * 100).toFixed(1);
    return `rgb(${rgb.join(',')}) ${pct}%`;
  }).join(', ');
  
  document.getElementById('legendGradient').style.background = 
    `linear-gradient(to right, ${gradientStops})`;
  
  const ticks = [];
  for (let i = 0; i <= 4; i++) {
    const val = min + (max - min) * i / 4;
    ticks.push((val > 0 ? '+' : '') + val.toFixed(1));
  }
  document.getElementById('legendTicks').innerHTML = 
    ticks.map(t => `<span>${t}</span>`).join('');
}

function changeMapMonth(delta) {
  currentMapMonth += delta;
  if (currentMapMonth < 1) currentMapMonth = 12;
  if (currentMapMonth > 12) currentMapMonth = 1;
  document.getElementById('mapMonthSlider').value = currentMapMonth;
  updateMapUI();
  loadMapGeoTIFF();
}

document.getElementById('mapMonthSlider').addEventListener('input', function() {
  currentMapMonth = parseInt(this.value);
  updateMapUI();
  loadMapGeoTIFF();
});

document.getElementById('mapPrev').addEventListener('click', () => changeMapMonth(-1));
document.getElementById('mapNext').addEventListener('click', () => changeMapMonth(1));

// เพิ่ม map update เมื่อเปลี่ยน param/year
const origRenderAll = renderAll;
renderAll = function() {
  origRenderAll();
  if (leafletMap) {
    updateMapUI();
    loadMapGeoTIFF();
  }
};

// Init map หลัง DOM ready
setTimeout(() => {
  initLeafletMap();
  updateMapUI();
  loadMapGeoTIFF();
  setTimeout(() => leafletMap.invalidateSize(), 200);
}, 500);
'''

# แทรกก่อน </script> สุดท้าย
html = html.replace('</script>\n</body>\n</html>', MAP_JS + '\n</script>\n</body>\n</html>')

# บันทึกไฟล์
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ เพิ่ม Web GIS Raster Map (Fig. 6) เข้า index.html สำเร็จแล้ว")
print("📂 ไฟล์: ~/viirs-marine-dashboard/index.html")
print("🚀 เปิด: http://localhost:5001/")
