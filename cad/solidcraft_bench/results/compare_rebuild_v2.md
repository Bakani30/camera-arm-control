# H2: confirmed (exploratory)

ผ่าน 6/6 part (100.0%)

**ผล exploratory:** ใช้เกณฑ์ v2 (tight bbox) กับ 3 ชิ้นที่วัดไปแล้วก่อนเปลี่ยนกฎ. ผลนี้ไม่ได้ยืนยัน H2v2 — ผลยืนยันมาจากชิ้น held-out ใน `compare_heldout.md`. ผลที่ตัดสินตามเกณฑ์ที่ล็อกไว้อยู่ใน `compare_rebuild.md`

เกณฑ์: volume ≤ 0.2%, area ≤ 0.2%, bbox ≤ 0.05 mm ทุกขอบ (เทียบ optimalBoundingBox ของ FreeCAD), COM ≤ 0.2% ของเส้นทแยง bbox; ตัวหนา = ไม่ผ่าน

คอลัมน์ bbox (BoundBox) = เทียบกับ BoundBox ของ FreeCAD, exploratory ไม่ใช้ตัดสิน

| part | ผล | volume | area | bbox | COM | bbox (BoundBox) | หมายเหตุ |
|---|---|---|---|---|---|---|---|
| forearm_core_front | pass | 0.0044% | 0.0021% | 0.0007 mm | 0.0007% | 0.0007 mm |  |
| forearm_core_front@tube_r=+2 | pass | 0.0084% | 0.0025% | 0.0003 mm | 0.0018% | 0.0003 mm |  |
| servo_clamp_shoulder_local | pass | 0.0207% | 0.0965% | 0.0000 mm | 0.0002% | 0.0000 mm |  |
| servo_clamp_shoulder_local@L=+2 | pass | 0.0201% | 0.0939% | 0.0000 mm | 0.0002% | 0.0000 mm |  |
| turntable | pass | 0.0007% | 0.0009% | 0.0000 mm | 0.0000% | 5.7675 mm |  |
| turntable@tt_r=+5 | pass | 0.0007% | 0.0009% | 0.0000 mm | 0.0000% | 6.1794 mm |  |
