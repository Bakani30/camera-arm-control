# H2: refuted

ผ่าน 4/6 part (66.7%)

ไม่ผ่าน: turntable, turntable@tt_r=+5

## สรุปผล H2 (2026-11-04)

**ตัดสินตามเกณฑ์ v1 ที่ล็อกไว้: H2 ตก** ผ่าน 4/6 key. ส่วนที่ตกคือ `turntable` ทั้งสองเคส และตกเพราะ bbox อย่างเดียว

**ผลตามเกณฑ์ v2 (exploratory, เปลี่ยนกฎหลังเห็นข้อมูล):** ใช้ tight bbox (`optimalBoundingBox`) แล้วผ่าน 6/6 ดู `compare_rebuild_v2.md`. ผลยืนยันของ v2 มาจากชิ้น held-out 3 ชิ้น (Task 12–14) ไม่ใช่จากตารางนี้

**สาเหตุที่ turntable ตก:** `BoundBox` ของ FreeCAD หลวม 5.77 mm (และ 6.18 mm ตอน `tt_r` +5) บนผิวโค้ง. ถ้าเทียบกับ tight box จะต่างแค่ 0.00001 mm. volume, area, COM ต่างไม่เกิน 0.001%. ตามกฎที่ล็อกไว้ "bbox > 1 mm = สร้างผิด" ข้อนี้ชี้ผิดทาง: ถ้าวัดด้วยค่า analytic, script ถูกต้อง (disc + boss 93,490.28 vs 93,493.80 mm³)

**ผ่านเกณฑ์ตัวเลข แต่สร้างไม่เหมือน FreeCAD ทุกอย่าง:**
- `servo_clamp_shoulder_local`: SolidCraft 0.30.1 fillet ขอบเว้า 6 เส้นตรงที่ขาชนแผ่นไม่ได้ (`not supported yet: a blend ending in an earlier round`) เลยปล่อยคม. volume ต่าง 1.40 mm³ ตรงกับเนื้อของ fillet ที่ขาด, face 86 vs 100
- `forearm_core_front`: ถ้าทำตามลำดับ feature แบบ FreeCAD พอเปลี่ยน `tube_r` +2 แล้ว error (`the exact fallback ... takes planar faces only`). ต้องตัดครึ่งก่อนแล้วค่อย join hub และ kernel ต้องขยับ hub 0.0003 mm (`tool_nudge`) ถึงจะ join ได้

**บันทึกต่อชิ้น**

| ชิ้น | batch/check | รอบแก้ | เวลา | เปลี่ยน parameter | error ที่เจอ |
|---|---|---|---|---|---|
| turntable | 4 | 1 | ~25 นาที | `tt_r` +5 ผ่าน | `the blend is taller than the walls` (fillet ขอบล่างหลัง join boss → แก้ด้วยการ fillet ก่อน join) |
| servo_clamp_shoulder | 7 | 3 (ครบงบ) | ~30 นาที | `L` +2 ผ่าน | `a blend ending in an earlier round`, `the ball doesn't fit along the edge` (มุมเว้า-นูน → ปล่อยขอบเว้าคม) |
| forearm_core_front | 6 | 2 | ~25 นาที | `tube_r` +2 ผ่านหลังสลับลำดับ | `boolean Cut/Intersect: ... exact fallback ... takes planar faces only` (ผิวโค้งตัดกันที่มุมตื้น) |

เกณฑ์: volume ≤ 0.2%, area ≤ 0.2%, bbox ≤ 0.05 mm ทุกขอบ (เทียบ BoundBox ของ FreeCAD), COM ≤ 0.2% ของเส้นทแยง bbox; ตัวหนา = ไม่ผ่าน

คอลัมน์ bbox (optimalBoundingBox) = เทียบกับ optimalBoundingBox ของ FreeCAD, exploratory ไม่ใช้ตัดสิน

| part | ผล | volume | area | bbox | COM | bbox (optimalBoundingBox) | หมายเหตุ |
|---|---|---|---|---|---|---|---|
| forearm_core_front | pass | 0.0044% | 0.0021% | 0.0007 mm | 0.0007% | 0.0007 mm |  |
| forearm_core_front@tube_r=+2 | pass | 0.0084% | 0.0025% | 0.0003 mm | 0.0018% | 0.0003 mm |  |
| servo_clamp_shoulder_local | pass | 0.0207% | 0.0965% | 0.0000 mm | 0.0002% | 0.0000 mm |  |
| servo_clamp_shoulder_local@L=+2 | pass | 0.0201% | 0.0939% | 0.0000 mm | 0.0002% | 0.0000 mm |  |
| turntable | **fail** | 0.0007% | 0.0009% | **5.7675 mm** | 0.0000% | 0.0000 mm |  |
| turntable@tt_r=+5 | **fail** | 0.0007% | 0.0009% | **6.1794 mm** | 0.0000% | 0.0000 mm |  |
