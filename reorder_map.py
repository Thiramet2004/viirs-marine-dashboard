#!/usr/bin/env python3
"""
Reorder index.html to move Map (Fig. 6) to the top (after Stats, before Fig. 1)
"""

# อ่านไฟล์
with open('index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# หาตำแหน่ง
map_start = None
map_end = None
fig1_line = None

for i, line in enumerate(lines):
    if '<!-- Fig 6: Interactive Raster Map -->' in line:
        map_start = i
    if map_start is not None and map_end is None:
        if '</div>' in line and i > map_start + 30:  # หา closing div ของ map section
            # ตรวจสอบว่าเป็น closing div ของ chart-panel หรือไม่
            if i == 219 - 1:  # บรรทัด 219 (0-indexed = 218)
                map_end = i + 1
                break
    if '<!-- Fig 1: Main overlay -->' in line:
        fig1_line = i

# ถ้าหาไม่เจอให้ใช้ค่าที่รู้
if map_start is None:
    map_start = 178  # บรรทัด 179 (0-indexed)
if map_end is None:
    map_end = 219  # บรรทัด 219 (0-indexed)
if fig1_line is None:
    fig1_line = 139  # บรรทัด 140 (0-indexed)

print(f"Map section: lines {map_start+1} to {map_end}")
print(f"Fig 1 starts at: line {fig1_line+1}")

# ตัดส่วน map ออกมา
map_section = lines[map_start:map_end]

# ลบ map จากตำแหน่งเดิม
new_lines = lines[:map_start] + lines[map_end:]

# หาตำแหน่ง Fig 1 ใหม่หลังจากลบ map
fig1_new = None
for i, line in enumerate(new_lines):
    if '<!-- Fig 1: Main overlay -->' in line:
        fig1_new = i
        break

# แทรก map ก่อน Fig 1
if fig1_new is not None:
    final_lines = new_lines[:fig1_new] + ['\n'] + map_section + ['\n'] + new_lines[fig1_new:]
else:
    print("ERROR: ไม่พบ Fig 1")
    exit(1)

# เขียนไฟล์ใหม่
with open('index.html', 'w', encoding='utf-8') as f:
    f.writelines(final_lines)

print("✅ ย้าย Map (Fig. 6) ไปด้านบนสำเร็จ (หลัง Stats, ก่อน Fig. 1)")
