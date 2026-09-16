#!/usr/bin/env python3
"""
Update figure numbers after reordering:
- Map (old Fig. 6) → Fig. 1
- Old Fig. 1 → Fig. 2
- Old Fig. 2 → Fig. 3
- Old Fig. 3 → Fig. 4
- Old Fig. 4 → Fig. 5
- Old Fig. 5 → Fig. 6
"""

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# แทนที่หมายเลข Fig แบบระวัง (ทำทีละตัวเพื่อไม่ให้สับสน)
# ใช้ placeholder ชั่วคราว

# Step 1: เปลี่ยน Fig. 6 (Map) → FIG_NEW_1
content = content.replace('Fig. 6', 'FIG_NEW_1')

# Step 2: เปลี่ยน Fig. 1-5 → FIG_TEMP_X
content = content.replace('Fig. 1', 'FIG_TEMP_2')
content = content.replace('Fig. 2', 'FIG_TEMP_3')
content = content.replace('Fig. 3', 'FIG_TEMP_4')
content = content.replace('Fig. 4', 'FIG_TEMP_5')
content = content.replace('Fig. 5', 'FIG_TEMP_6')

# Step 3: แทนที่ placeholder ด้วยหมายเลขจริง
content = content.replace('FIG_NEW_1', 'Fig. 1')
content = content.replace('FIG_TEMP_2', 'Fig. 2')
content = content.replace('FIG_TEMP_3', 'Fig. 3')
content = content.replace('FIG_TEMP_4', 'Fig. 4')
content = content.replace('FIG_TEMP_5', 'Fig. 5')
content = content.replace('FIG_TEMP_6', 'Fig. 6')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ อัปเดตหมายเลข Figure แล้ว:")
print("   - แผนที่ (Map) → Fig. 1")
print("   - Monthly Mean Time Series → Fig. 2")
print("   - Scatter Plot → Fig. 3")
print("   - Monthly Anomaly → Fig. 4")
print("   - Inter-annual Trend → Fig. 5")
print("   - Inverse Relationship → Fig. 6")
