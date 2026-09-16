# 📌 VIIRS Dashboard Embedding Guide

คู่มือการนำ Dashboard ไปใส่ใน Marine GIS Portal หรือเว็บไซต์อื่นๆ

## 🎯 วิธีการ Embed

### แบบที่ 1: Embed Dashboard เต็มรูปแบบ (แนะนำ)

แสดงทั้งแผนที่ + กราฟทั้งหมด 6 รูป

```html
<iframe 
  src="http://localhost:5001/embed_dashboard.html" 
  width="100%" 
  height="1200px" 
  frameborder="0"
  style="border: 1px solid #e2e8f0; border-radius: 8px;"
  title="VIIRS Marine Dashboard"
></iframe>
```

**ใช้เมื่อไร:**
- ต้องการแสดงข้อมูลครบถ้วน
- มีพื้นที่หน้าเว็บเพียงพอ (แนะนำ 1200-1400px สูง)
- ต้องการให้ผู้ใช้วิเคราะห์ข้อมูลเชิงลึก

---

### แบบที่ 2: Embed เฉพาะแผนที่ (Map Only)

แสดงเฉพาะ Fig. 1 Interactive Raster Map

```html
<iframe 
  src="http://localhost:5001/embed_dashboard.html?mode=map" 
  width="100%" 
  height="600px" 
  frameborder="0"
  style="border: 1px solid #e2e8f0; border-radius: 8px;"
  title="VIIRS Satellite Map"
></iframe>
```

**ใช้เมื่อไร:**
- ต้องการแสดงเฉพาะแผนที่
- ประหยัดพื้นที่หน้าเว็บ
- ใช้ในหน้า Gallery หรือ Map Viewer

---

### แบบที่ 3: Embed เฉพาะกราฟ (Charts Only)

แสดงเฉพาะกราฟวิเคราะห์ทางสถิติ (Fig. 2-6)

```html
<iframe 
  src="http://localhost:5001/embed_dashboard.html?mode=charts" 
  width="100%" 
  height="800px" 
  frameborder="0"
  style="border: 1px solid #e2e8f0; border-radius: 8px;"
  title="VIIRS Statistical Analysis"
></iframe>
```

**ใช้เมื่อไร:**
- ต้องการแสดงเฉพาะข้อมูลสถิติ
- ใช้ในหน้ารายงาน (Report)
- ต้องการกราฟแยกจากแผนที่

---

### แบบที่ 4: Standalone (ไม่แสดง Notice)

เหมือนแบบอื่นแต่ซ่อน notice bar ที่บอกให้เปิดหน้าใหม่

```html
<iframe 
  src="http://localhost:5001/embed_dashboard.html?standalone=true" 
  width="100%" 
  height="1200px" 
  frameborder="0"
  title="VIIRS Marine Dashboard"
></iframe>
```

---

## 🔗 URL Parameters

คุณสามารถควบคุมการแสดงผลด้วย URL parameters:

| Parameter | Values | Description |
|-----------|--------|-------------|
| `mode` | `map`, `charts`, หรือไม่ระบุ | เลือกโหมดแสดงผล |
| `standalone` | `true`, `false` | ซ่อน/แสดง notice bar |

**ตัวอย่าง:**
```
http://localhost:5001/embed_dashboard.html?mode=map&standalone=true
```

---

## 🎨 Responsive Design

Dashboard ปรับขนาดอัตโนมัติตามหน้าจอ แนะนำให้ใช้:

```html
<div style="max-width: 1400px; margin: 0 auto; padding: 20px;">
  <iframe 
    src="http://localhost:5001/embed_dashboard.html" 
    width="100%" 
    height="1200px" 
    frameborder="0"
    style="border: 1px solid #e2e8f0; border-radius: 8px;"
  ></iframe>
</div>
```

### Mobile Responsive

```html
<style>
  .dashboard-container {
    width: 100%;
    max-width: 1400px;
    margin: 0 auto;
  }
  
  .dashboard-container iframe {
    width: 100%;
    height: 1200px;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
  }
  
  @media (max-width: 768px) {
    .dashboard-container iframe {
      height: 1600px; /* เพิ่มความสูงสำหรับมือถือ */
    }
  }
</style>

<div class="dashboard-container">
  <iframe src="http://localhost:5001/embed_dashboard.html"></iframe>
</div>
```

---

## 🚀 Production Deployment

เมื่อ deploy จริง ให้เปลี่ยน URL จาก `localhost` เป็น domain จริง:

```html
<!-- Development -->
<iframe src="http://localhost:5001/embed_dashboard.html"></iframe>

<!-- Production -->
<iframe src="https://marine-dashboard.your-domain.com/embed_dashboard.html"></iframe>
```

### ขั้นตอน Deploy

1. **อัปโหลดโค้ดไปยัง Server**
   ```bash
   # ใช้ Git
   git clone https://github.com/Thiramet2004/viirs-marine-dashboard.git
   cd viirs-marine-dashboard
   
   # หรือ rsync
   rsync -avz viirs-marine-dashboard/ user@server:/var/www/marine-dashboard/
   ```

2. **ติดตั้ง Dependencies**
   ```bash
   pip3 install flask flask-cors rasterio geopandas numpy pandas
   ```

3. **Run Server (Production)**
   ```bash
   # ใช้ gunicorn (แนะนำ)
   pip3 install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5001 server:app
   
   # หรือใช้ systemd service
   sudo systemctl start viirs-dashboard
   ```

4. **Setup Nginx Reverse Proxy** (แนะนำ)
   ```nginx
   server {
       listen 80;
       server_name marine-dashboard.your-domain.com;
       
       location / {
           proxy_pass http://localhost:5001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       # Cache static files
       location ~* \.(tif|geojson)$ {
           proxy_pass http://localhost:5001;
           proxy_cache_valid 200 1d;
       }
   }
   ```

5. **อัปเดต URL ใน HTML**
   ```html
   <iframe src="https://marine-dashboard.your-domain.com/embed_dashboard.html"></iframe>
   ```

---

## 🔐 CORS Configuration

ถ้า embed จากโดเมนอื่น ให้แก้ไข `server.py`:

```python
from flask_cors import CORS

# Allow specific domains
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://marinegis.dmcr.go.th",
            "https://your-portal.com"
        ]
    }
})
```

---

## 📱 WordPress Integration

ถ้าใช้ WordPress ให้ใช้ shortcode:

1. **สร้าง Custom Shortcode** (ใน `functions.php`):

```php
function viirs_dashboard_shortcode($atts) {
    $atts = shortcode_atts(array(
        'mode' => 'full',
        'height' => '1200px',
        'width' => '100%'
    ), $atts);
    
    $url = 'https://marine-dashboard.your-domain.com/embed_dashboard.html';
    if ($atts['mode'] !== 'full') {
        $url .= '?mode=' . $atts['mode'];
    }
    
    return '<iframe src="' . $url . '" 
            width="' . $atts['width'] . '" 
            height="' . $atts['height'] . '" 
            frameborder="0" 
            style="border: 1px solid #e2e8f0; border-radius: 8px;"></iframe>';
}
add_shortcode('viirs_dashboard', 'viirs_dashboard_shortcode');
```

2. **ใช้ใน Post/Page**:

```
[viirs_dashboard]

[viirs_dashboard mode="map" height="600px"]

[viirs_dashboard mode="charts" height="800px"]
```

---

## 🎯 ตัวอย่างใน Marine GIS Portal

### หน้า Dashboard หลัก

```html
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <title>VIIRS Marine Monitoring | Marine GIS Portal</title>
    <style>
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #0369a1 0%, #0c4a6e 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 24px;
        }
        
        .header h1 {
            margin: 0 0 8px 0;
            font-size: 2rem;
        }
        
        .header p {
            margin: 0;
            opacity: 0.9;
            font-size: 1rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌊 ระบบติดตามสิ่งแวดล้อมทางทะเล</h1>
            <p>ข้อมูลดาวเทียม VIIRS - อุณหภูมิผิวน้ำทะเลและคลอโรฟิลล์-เอ</p>
        </div>
        
        <iframe 
            src="https://marine-dashboard.your-domain.com/embed_dashboard.html?standalone=true" 
            width="100%" 
            height="1200px" 
            frameborder="0"
            style="border: 1px solid #e2e8f0; border-radius: 8px;"
            title="VIIRS Marine Dashboard"
        ></iframe>
    </div>
</body>
</html>
```

### หน้า Map Viewer

```html
<div class="map-viewer-section">
    <h2>แผนที่ดาวเทียมแบบ Interactive</h2>
    <iframe 
        src="https://marine-dashboard.your-domain.com/embed_dashboard.html?mode=map&standalone=true" 
        width="100%" 
        height="600px" 
        frameborder="0"
        style="border: 1px solid #e2e8f0; border-radius: 8px;"
    ></iframe>
</div>
```

### หน้า Reports

```html
<div class="analytics-section">
    <h2>การวิเคราะห์ทางสถิติ</h2>
    <iframe 
        src="https://marine-dashboard.your-domain.com/embed_dashboard.html?mode=charts&standalone=true" 
        width="100%" 
        height="800px" 
        frameborder="0"
        style="border: 1px solid #e2e8f0; border-radius: 8px;"
    ></iframe>
</div>
```

---

## 📊 SEO Optimization

เพิ่ม metadata สำหรับ SEO:

```html
<head>
    <meta name="description" content="ระบบติดตามสิ่งแวดล้อมทางทะเลด้วยข้อมูลดาวเทียม VIIRS - อุณหภูมิผิวน้ำทะเล (SST) และ คลอโรฟิลล์-เอ สำหรับอ่าวไทยและทะเลอันดามัน">
    <meta name="keywords" content="VIIRS, SST, Chlorophyll-a, Marine, Thailand, Satellite, Ocean, Temperature">
    
    <!-- Open Graph for social sharing -->
    <meta property="og:title" content="VIIRS Marine Dashboard - ระบบติดตามสิ่งแวดล้อมทางทะเล">
    <meta property="og:description" content="แดชบอร์ดข้อมูลดาวเทียม VIIRS แบบ Interactive">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://marine-dashboard.your-domain.com">
</head>
```

---

## 🐛 Troubleshooting

### ปัญหา: iframe ไม่แสดงผล

**สาเหตุ:** CORS policy blocking

**แก้ไข:**
```python
# ใน server.py
CORS(app, resources={r"/*": {"origins": "*"}})
```

### ปัญหา: แผนที่โหลดช้า

**แก้ไข:**
1. Enable nginx caching
2. Compress GeoTIFF files
3. Use CDN for static assets

### ปัญหา: ขนาด iframe ไม่พอดี

**แก้ไข:**
```javascript
// Auto-resize iframe
<script>
window.addEventListener('message', function(e) {
    if (e.data.type === 'resize') {
        document.getElementById('dashboardFrame').style.height = e.data.height + 'px';
    }
});
</script>
```

---

## 📞 Support

หากมีปัญหาหรือคำถาม:
- GitHub Issues: https://github.com/Thiramet2004/viirs-marine-dashboard/issues
- Email: [Your support email]

---

**Happy Embedding! 🎉**
