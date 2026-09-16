#!/usr/bin/env python3
"""
fix_map_rgb.py
--------------
แก้ไข index.html ให้แสดง GeoTIFF RGB แบบถูกต้อง + เพิ่ม Marine Zones
"""

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# ลบ code เก่าที่ apply color palette ซ้ำ และแทนด้วย RGB rendering ตรงๆ
OLD_MAP_JS = '''async function loadMapGeoTIFF() {
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
}'''

NEW_MAP_JS = '''async function loadMapGeoTIFF() {
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

    console.log('GeoTIFF loaded:', georaster);

    // GeoTIFF นี้เป็น RGB 3-band แล้ว (SNAP export) ไม่ต้อง apply color palette
    // แค่แสดง RGB ตรงๆ โดย mask land (0,0,0) ออก
    const pixelValuesToColorFn = values => {
      const r = values[0];
      const g = values[1];
      const b = values[2];
      
      // Black pixels (0,0,0) = nodata/land → transparent
      if (r === 0 && g === 0 && b === 0) return null;
      
      return `rgb(${r},${g},${b})`;
    };

    currentMapLayer = new GeoRasterLayer({
      georaster: georaster,
      opacity: 0.80,
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
}'''

html = html.replace(OLD_MAP_JS, NEW_MAP_JS)

# เพิ่ม Marine Zones overlay
ADD_ZONES_CODE = '''
// =============================================
// MARINE ZONES OVERLAY
// =============================================

let marineZonesLayer = null;

async function loadMarineZones() {
  try {
    const response = await fetch(`${API_BASE}/geojson/marine_zones`);
    if (!response.ok) {
      console.warn('Marine zones not available:', response.status);
      return;
    }
    
    const geojson = await response.json();
    
    marineZonesLayer = L.geoJSON(geojson, {
      style: {
        color: '#fbbf24',
        weight: 2,
        opacity: 0.8,
        fill: false,
        dashArray: '5, 5'
      },
      onEachFeature: function(feature, layer) {
        if (feature.properties) {
          let popupContent = '<div style="font-size:0.85rem;font-weight:600;color:#1e3a5f">';
          popupContent += 'Marine Zone</div>';
          if (feature.properties.ZONE_NAME || feature.properties.name) {
            popupContent += '<div style="font-size:0.75rem;margin-top:4px">';
            popupContent += feature.properties.ZONE_NAME || feature.properties.name;
            popupContent += '</div>';
          }
          layer.bindPopup(popupContent);
        }
      }
    }).addTo(leafletMap);
    
    console.log('Marine zones loaded');
  } catch (error) {
    console.warn('Could not load marine zones:', error);
  }
}

// Load zones after map init
setTimeout(() => loadMarineZones(), 1000);
'''

# แทรกก่อน </script> ปิด
html = html.replace('</script>\n</body>\n</html>', ADD_ZONES_CODE + '\n</script>\n</body>\n</html>')

# บันทึก
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ แก้ไข index.html เสร็จแล้ว")
print("   - แสดง GeoTIFF RGB แบบถูกต้อง (ไม่ apply color ซ้ำ)")
print("   - Mask land (black pixels) ออก")
print("   - เพิ่ม Marine Zones overlay (เส้นเหลือง)")
print("\n🔄 Restart Flask server แล้ว refresh browser")
