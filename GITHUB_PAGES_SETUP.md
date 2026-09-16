# 🌐 GitHub Pages Setup Guide

## ⚠️ ข้อจำกัดสำคัญ

**GitHub Pages รองรับเฉพาะ Static Files เท่านั้น** (HTML/CSS/JS)

Dashboard แบบเต็มรูปแบบ **ไม่สามารถ** รันบน GitHub Pages ได้เพราะ:
- ❌ ต้องใช้ Flask Server (Python backend)
- ❌ ต้องประมวลผล GeoTIFF แบบเรียลไทม์
- ❌ ต้องเข้าถึงไฟล์ข้อมูล 277 MB

## ✅ สิ่งที่ทำได้บน GitHub Pages

1. **Landing Page** - แสดงข้อมูลและคู่มือ
2. **Documentation** - README และ Embed Guide
3. **Static Demo** - แผนที่ธรรมดา (ไม่มีข้อมูล GeoTIFF)

## 🚀 Enable GitHub Pages

### ขั้นตอนที่ 1: เปิดใน GitHub Settings

1. ไปที่ https://github.com/Thiramet2004/viirs-marine-dashboard
2. คลิก **Settings** (ด้านบน)
3. คลิก **Pages** (เมนูซ้าย)
4. ใน **Source** เลือก:
   - Branch: `main`
   - Folder: `/docs`
5. คลิก **Save**

### ขั้นตอนที่ 2: รอ Deployment

GitHub จะสร้างเว็บไซต์ให้อัตโนมัติ (ใช้เวลา 1-2 นาที)

### ขั้นตอนที่ 3: เข้าถึงเว็บไซต์

URL จะเป็น:
```
https://thiramet2004.github.io/viirs-marine-dashboard/
```

## 📄 หน้าที่มีบน GitHub Pages

| URL | เนื้อหา |
|-----|---------|
| `https://thiramet2004.github.io/viirs-marine-dashboard/` | Landing page พร้อมคู่มือ |
| `https://github.com/Thiramet2004/viirs-marine-dashboard/blob/main/README.md` | README.md |
| `https://github.com/Thiramet2004/viirs-marine-dashboard/blob/main/EMBED_GUIDE.md` | Embed Guide |

## 🎯 วิธีใช้ Dashboard จริง

Dashboard แบบเต็มรูปแบบ **ต้อง deploy แบบอื่น**:

### Option 1: รัน Local (แนะนำสำหรับทดสอบ)

```bash
# Clone repo
git clone https://github.com/Thiramet2004/viirs-marine-dashboard.git
cd viirs-marine-dashboard

# Install dependencies
pip3 install flask flask-cors rasterio geopandas

# Run server
python3 server.py

# Open browser
open http://localhost:5001
```

### Option 2: Deploy บน Server

**ใช้ VPS/Cloud Server** เช่น:
- DigitalOcean
- AWS EC2
- Google Cloud
- Azure
- Heroku
- Railway.app

**ขั้นตอน:**

1. **Setup Server**
   ```bash
   # SSH to server
   ssh user@your-server.com
   
   # Clone repo
   git clone https://github.com/Thiramet2004/viirs-marine-dashboard.git
   cd viirs-marine-dashboard
   
   # Install Python dependencies
   pip3 install flask flask-cors rasterio geopandas gunicorn
   ```

2. **Run with Gunicorn**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5001 server:app
   ```

3. **Setup Nginx (แนะนำ)**
   ```nginx
   server {
       listen 80;
       server_name marine-dashboard.your-domain.com;
       
       location / {
           proxy_pass http://localhost:5001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

4. **Setup SSL (Let's Encrypt)**
   ```bash
   sudo certbot --nginx -d marine-dashboard.your-domain.com
   ```

5. **Embed Code (Production)**
   ```html
   <iframe 
     src="https://marine-dashboard.your-domain.com/embed_dashboard.html?standalone=true" 
     width="100%" 
     height="1200px" 
     frameborder="0"
   ></iframe>
   ```

### Option 3: Docker

1. **สร้าง Dockerfile**
   ```dockerfile
   FROM python:3.9
   WORKDIR /app
   COPY . .
   RUN pip install flask flask-cors rasterio geopandas gunicorn
   EXPOSE 5001
   CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "server:app"]
   ```

2. **Build & Run**
   ```bash
   docker build -t viirs-dashboard .
   docker run -p 5001:5001 viirs-dashboard
   ```

### Option 4: Railway.app (PaaS - ง่ายที่สุด)

1. สมัคร https://railway.app
2. Connect GitHub repository
3. Railway จะ auto-detect Python และ deploy อัตโนมัติ
4. ได้ URL: `https://your-app.railway.app`

## 🌐 Embed Code

### สำหรับ Local Development

```html
<!-- Full Dashboard -->
<iframe 
  src="http://localhost:5001/embed_dashboard.html?standalone=true" 
  width="100%" 
  height="1200px" 
  frameborder="0"
></iframe>

<!-- Map Only -->
<iframe 
  src="http://localhost:5001/embed_dashboard.html?mode=map&standalone=true" 
  width="100%" 
  height="600px" 
  frameborder="0"
></iframe>
```

### สำหรับ Production

```html
<!-- เปลี่ยน URL เป็น domain จริง -->
<iframe 
  src="https://marine-dashboard.your-domain.com/embed_dashboard.html?standalone=true" 
  width="100%" 
  height="1200px" 
  frameborder="0"
></iframe>
```

## 📊 ข้อมูลที่ต้องการ

Dashboard ต้องการ:
- ✅ ไฟล์ GeoTIFF 192 ไฟล์ (277 MB) - มีใน repo แล้ว
- ✅ Marine Zones Shapefiles - ต้องอยู่ที่ `/Volumes/New Volume/04_VIIRS_Monthly/EEZ_MarineZone/`
- ✅ Python 3.9+ และ dependencies

## ❓ FAQ

### Q: ทำไมไม่ deploy บน GitHub Pages ได้?
A: GitHub Pages รองรับเฉพาะ static files ไม่สามารถรัน Python/Flask server ได้

### Q: มีทางเลือกอื่นไหม?
A: ใช่ สามารถ deploy บน:
- **Railway.app** (ง่ายที่สุด, ฟรี)
- **Heroku** (ฟรีถูกยกเลิก แต่มี paid plans)
- **DigitalOcean/AWS** (ต้อง setup เอง แต่ยืดหยุ่นที่สุด)
- **Google Cloud Run** (serverless, จ่ายตามใช้)

### Q: ต้นทุนเท่าไหร่?
A:
- **Railway.app:** ฟรี 500 ชั่วโมง/เดือน (พอใช้งาน dev)
- **DigitalOcean Droplet:** $5-10/เดือน
- **AWS EC2 t2.micro:** ฟรี 1 ปีแรก, หลังจากนั้น ~$10/เดือน
- **Google Cloud Run:** จ่ายตามใช้, ~$5-20/เดือน

### Q: Dashboard ใช้ทรัพยากรมากไหม?
A:
- **RAM:** ~500 MB (ขั้นต่ำ 1 GB แนะนำ)
- **CPU:** 1 core พอ
- **Storage:** 300 MB (code + data)
- **Bandwidth:** ขึ้นกับการใช้งาน (~1-2 GB/เดือนถ้าไม่ค่อยมีคนใช้)

## 🔗 Links

- **GitHub Pages (Landing):** https://thiramet2004.github.io/viirs-marine-dashboard/
- **GitHub Repository:** https://github.com/Thiramet2004/viirs-marine-dashboard
- **README:** https://github.com/Thiramet2004/viirs-marine-dashboard/blob/main/README.md
- **Embed Guide:** https://github.com/Thiramet2004/viirs-marine-dashboard/blob/main/EMBED_GUIDE.md

---

**สรุป:** 
- ✅ GitHub Pages = Landing page + Documentation
- ❌ GitHub Pages ≠ Full Dashboard (ต้องใช้ server deployment)
- 🎯 แนะนำ: Deploy บน Railway.app หรือ VPS

