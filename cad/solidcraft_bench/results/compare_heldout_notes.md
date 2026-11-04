## สรุปผล H2v2 (2026-11-04, แผน v2 pre-registered)

**ตัดสินตามเกณฑ์ v2 ที่ล็อกไว้: H2v2 ยืนยัน** ผ่าน 6/6 key ของชิ้น held-out 3 ชิ้นที่สุ่มก่อนล็อก (`random.Random(20261104)`) ทั้งค่าปกติและหลังเปลี่ยน parameter ที่ใหญ่สุด +2 mm. rebuild หลังเปลี่ยนค่าไม่มี error หรือ warning. ทุกชิ้นเสร็จในงบ

**ค่าต่างสูงสุดใน 6 key:** volume 0.0019%, area 0.0005%, COM 0.0003% ของเส้นทแยง bbox, bbox 0.0005 mm. ต่ำกว่าเกณฑ์อย่างน้อย 100 เท่า

**ผลรอง (บันทึก ไม่ใช้ตัดสิน)**

| ชิ้น | feature ครบ | ลำดับเหมือน FreeCAD | warning ของ kernel | รอบแก้ | เวลา | face SC / FC |
|---|---|---|---|---|---|---|
| `gripper_pad_up` | ครบ | เหมือน | ไม่มี | 0 | ~5 นาที | 46 / 46 |
| `gripper_gear_crank_up` | ครบ (แถบ + cap แทน slot) | เหมือน | ไม่มี | 1 | ~20 นาที | 276 / 259 |
| `base_tray` | ครบ | เหมือน | ไม่มี | 0 | ~25 นาที | 154 / 160 |

- `gripper_gear_crank_up`: `sketch.slot.*` ไม่รับ expression เลยวาดแถบเป็น polyline + cylinder ปลาย. ฟันเฟือง 224 จุดเป็นตัวเลขจาก generator (`rebuild/make_gear_crank.py`) จึงไม่ follow module/จำนวนฟัน
- `base_tray`: expression ไม่มี `if`/ตัวเปรียบเทียบ. grid ที่มีเงื่อนไขทำด้วยสวิตช์ `max(0, sign(lim − d))` ต่อวง (`rebuild/make_base_tray.py`). topology เปลี่ยนเมื่อ `r` +2 (รูเพิ่ม 8, รอยบากกลายเป็นรูปิด) แล้วยังตรง
- ชิ้นที่ยากที่สุดของ v1 (fillet มุมเว้า-นูน, ผิวโค้งตัดกันมุมตื้น) ไม่มีในชิ้น held-out: pad, gear crank, tray ไม่มี fillet. ผลนี้จึงยืนยันความแม่นของ booleans, sketch, pattern และ expression แต่ไม่ได้ทดสอบ fillet ซ้ำ
