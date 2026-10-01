# 🌐 GitHub Pages

Dashboard ทั้งหมดรันบน GitHub Pages ได้เต็มรูปแบบ ไม่ต้องใช้ server: หน้าเว็บอ่าน GeoTIFF, `stats.json`
และขอบเขต EEZ เป็นไฟล์ static แล้ววาดแผนที่และกราฟในเบราว์เซอร์เอง

| หน้า | URL |
|------|-----|
| รายเดือน (หน้าหลัก) | https://thiramet2004.github.io/viirs-marine-dashboard/ |
| รายปี | https://thiramet2004.github.io/viirs-marine-dashboard/yearly/ |
| สำหรับ embed (iframe) | https://thiramet2004.github.io/viirs-marine-dashboard/embed_dashboard.html |

## ทำงานอย่างไร

- GitHub Pages เสิร์ฟโฟลเดอร์ `docs/` จาก branch `main` (Settings → Pages → Branch `main`, Folder `/docs`)
- `docs/` มีเฉพาะหน้าเว็บและไฟล์เล็ก ส่วนข้อมูล raster (ประมาณ 450 MB) อยู่ใน `data/` ของ repo
  และหน้าเว็บดึงผ่าน `https://raw.githubusercontent.com/Thiramet2004/viirs-marine-dashboard/main/data/...`
- เมื่อเปิดบน `localhost` (รัน `server.py`) หน้าเดียวกันจะใช้ `/api/...` ของ server แทน

| ไฟล์ใน `docs/` | สำเนาของ |
|----------------|----------|
| `docs/index.html` | `index.html` (ไฟล์เดียวกันทุกตัวอักษร) |
| `docs/yearly/index.html` | `yearly/index.html` (ต่างจาก `index_yearly.html` ที่ server ใช้ แค่ path ของลิงก์และรูปเป็นแบบ `../`) |
| `docs/embed_dashboard.html` | `embed_dashboard.html` |
| `docs/data/marine_zones.geojson` | `data/marine_zones.geojson` (ขอบเขต 7 เขตจาก `E:\SST_Chlor\EEZ_MarineZone`) |
| `docs/assets/` | `assets/` (โลโก้ อว./GISTDA และ favicon) |
| `docs/favicon.ico` | `favicon.ico` |

## อัปเดตข้อมูลหรือหน้าเว็บ

```bash
# 1) สร้างข้อมูลใหม่ (เมื่อมีเดือนใหม่) – ดู README หัวข้อ "Updating Data"
python build_dashboard_data.py

# 2) ถ้าแก้หน้าเว็บ ให้คัดลอกไปที่ docs/
cp index.html docs/index.html
cp yearly/index.html docs/yearly/index.html
cp embed_dashboard.html docs/embed_dashboard.html

# 3) push แล้ว GitHub Pages จะ build เอง (ประมาณ 1 นาที)
git add -A
git commit -m "Update data"
git push origin main
```

ตรวจสถานะการ build:

```bash
gh api repos/Thiramet2004/viirs-marine-dashboard/pages/builds/latest --jq '.status + " " + .commit'
```

ถ้า build ไม่เริ่มเอง สั่งได้ด้วย `gh api -X POST repos/Thiramet2004/viirs-marine-dashboard/pages/builds`

## แก้ปัญหา

- **ยังเห็นหน้าเก่า / favicon เก่า** – กด Ctrl+F5 (เบราว์เซอร์และ CDN ของ GitHub เก็บ cache ไว้ไม่กี่นาที)
- **แผนที่ขึ้น "กำลังโหลด GeoTIFF..." นาน** – ไฟล์มาจาก raw.githubusercontent.com (ประมาณ 1 MB ต่อเดือน)
  ปกติใช้ 1–3 วินาที ถ้าช้ามากมักเป็นเครือข่ายชั่วคราว
- **ลิงก์ไปหน้ารายปีเป็น 404** – ลิงก์ในหน้าต้องเป็น `yearly/` (relative) ไม่ใช่ `/yearly`
  เพราะเว็บอยู่ใต้ `/viirs-marine-dashboard/`
- **หน้าใน `docs/` ไม่ตรงกับไฟล์หลัก** – คัดลอกตามขั้นตอนที่ 2 ใหม่

## รันบนเครื่อง (ทางเลือก)

```bash
pip install -r requirements.txt
python server.py            # http://localhost:5001  (เฉพาะเครื่องนี้)
VIIRS_HOST=0.0.0.0 python server.py   # ให้เครื่องอื่นในเครือข่ายเข้าได้
```

ถ้าจะใช้ server บนเครื่องจริงแทน GitHub Pages ให้รันหลัง reverse proxy (เช่น nginx) และอย่าเปิด
`VIIRS_DEBUG=1` บนเครือข่ายที่คนอื่นเข้าถึงได้
