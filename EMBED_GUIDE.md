# 🔗 Embed Guide

วิธีฝัง VIIRS Marine Dashboard ในเว็บอื่น (เช่น Marine GIS Portal) ด้วย `<iframe>`
ใช้ URL ของ GitHub Pages ได้ทันที ไม่ต้องตั้ง server

## แบบที่ 1: หน้าเต็ม

```html
<iframe
  src="https://thiramet2004.github.io/viirs-marine-dashboard/"
  width="100%" height="1400" frameborder="0" loading="lazy"
  style="border:1px solid #e2e8f0;border-radius:8px"
  title="VIIRS Marine Dashboard"></iframe>
```

## แบบที่ 2: เฉพาะแผนที่ (Fig. 1)

```html
<iframe
  src="https://thiramet2004.github.io/viirs-marine-dashboard/?mode=map"
  width="100%" height="900" frameborder="0" loading="lazy"
  title="VIIRS Marine Dashboard – แผนที่"></iframe>
```

## แบบที่ 3: เฉพาะกราฟ

```html
<iframe
  src="https://thiramet2004.github.io/viirs-marine-dashboard/?mode=charts"
  width="100%" height="2200" frameborder="0" loading="lazy"
  title="VIIRS Marine Dashboard – กราฟ"></iframe>
```

## แบบที่ 4: หน้ารายปี

```html
<iframe
  src="https://thiramet2004.github.io/viirs-marine-dashboard/yearly/"
  width="100%" height="1500" frameborder="0" loading="lazy"
  title="VIIRS Marine Dashboard – รายปี"></iframe>
```

## หน้า embed พร้อมแถบลิงก์ (`embed_dashboard.html`)

`embed_dashboard.html` ห่อหน้าหลักไว้ใน iframe พร้อมข้อความ "เปิดในหน้าต่างใหม่" และตั้งความสูงให้ตามโหมด

| URL parameter | ผล |
|---------------|----|
| (ไม่มี) | หน้าเต็ม |
| `?mode=map` | เฉพาะแผนที่ |
| `?mode=charts` | เฉพาะกราฟ |
| `&standalone=true` | ซ่อนแถบข้อความด้านบน |

```html
<iframe
  src="https://thiramet2004.github.io/viirs-marine-dashboard/embed_dashboard.html?mode=map&standalone=true"
  width="100%" height="700" frameborder="0" loading="lazy"></iframe>
```

`?mode=` ใช้ได้กับหน้าหลักโดยตรงด้วย (แบบที่ 2 และ 3) จึงไม่จำเป็นต้องผ่าน `embed_dashboard.html`

## ความสูงที่แนะนำ

ความสูงของ iframe ต้องกำหนดเอง เพราะหน้าที่ฝังไม่ได้แจ้งความสูงกลับมา

| เนื้อหา | จอคอมพิวเตอร์ | มือถือ |
|---------|---------------|--------|
| แผนที่ (`?mode=map`) | 900 px | 700 px |
| หน้าเต็ม | 1400 px ขึ้นไป (มี scroll ใน iframe) | 1200 px ขึ้นไป |

แผนที่ Fig. 1 สูงประมาณ 82% ของความสูง iframe (560–900 px) และ 70% บนมือถือ

## WordPress (shortcode)

```php
function viirs_dashboard_shortcode($atts) {
    $atts = shortcode_atts(['mode' => '', 'height' => '900'], $atts);
    $url = 'https://thiramet2004.github.io/viirs-marine-dashboard/';
    if (in_array($atts['mode'], ['map', 'charts'], true)) {
        $url .= '?mode=' . $atts['mode'];
    }
    return '<iframe src="' . esc_url($url) . '" width="100%" height="' . intval($atts['height'])
         . '" frameborder="0" loading="lazy" title="VIIRS Marine Dashboard"></iframe>';
}
add_shortcode('viirs_dashboard', 'viirs_dashboard_shortcode');
```

ใช้: `[viirs_dashboard mode="map" height="900"]`

## ใช้กับ server ของตัวเอง

ถ้ารัน `server.py` เอง (ดู README) ให้เปลี่ยน URL เป็น domain ของ server เช่น
`https://marine-dashboard.example.org/?mode=map` โดย `server.py` เปิด CORS ให้ทุก origin อยู่แล้ว

## แก้ปัญหา

- **iframe ว่าง** – ตรวจว่า URL เป็น `https://` และเว็บปลายทางไม่ได้ตั้ง Content-Security-Policy ที่ห้าม `frame-src`
  ไปยัง `thiramet2004.github.io`
- **แผนที่ไม่เต็มกรอบหลังเปลี่ยนขนาด iframe** – รีโหลดหน้า (Leaflet คำนวณขนาดตอนโหลด)
- **ยังเห็นหน้าเก่า** – กด Ctrl+F5
