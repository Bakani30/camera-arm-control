# H1: refuted

ผ่าน 39/44 part (88.6%)

ปิดใน FreeCAD แต่เปิดใน SolidCraft: base_lid, column, gripper_cover

## สรุปผล H1 (2026-11-03)

**ตัดสินตามเกณฑ์ที่ล็อกไว้: H1 ตก** ผ่าน 39/44 part (88.6%, ต่ำกว่า 95%) และมี 3 part ที่ปิดใน FreeCAD แต่เปิดใน SolidCraft. ข้อหลังข้อเดียวก็พอให้ H1 ตก

**สาเหตุของ 5 part ที่ไม่ผ่าน**
- `base_lid`, `column`, `gripper_cover`: SolidCraft 0.30.1 import แล้วได้ body เปิด วัด volume กับ COM ไม่ได้
  - ไฟล์ STEP ไม่ผิด: FreeCAD อ่านกลับแล้วได้ closed + valid, volume และจำนวน face เท่าเดิม
  - ใน SolidCraft มี face ชนิด `other` (2, 4, 20 face) และจำนวน face ที่แสดงน้อยกว่าที่ kernel นับ (`column` 72 จาก 77) → ปัญหาอยู่ที่ importer ของ SolidCraft
- `upper_link`, `wrist`: volume, area, COM ตรง (≤ 0.001%) แต่ bbox ต่าง 6.2 และ 10.8 mm
  - `BoundBox` ของ FreeCAD หลวมบนผิวโค้ง. `optimalBoundingBox()` ของ FreeCAD ตรงกับ bbox ของ SolidCraft ทุกชิ้น (ต่างสูงสุด 0.00015 mm)
  - เข้ากฎที่ล็อกไว้ "ref ของ FreeCAD ผิด ไม่นับเป็น fail ของ SolidCraft" ตามหลัก แต่กฎเขียนไว้สำหรับกรณี volume/area/COM เลยยังนับ fail ในผลหลัก

**ผล exploratory** (ใช้ `optimalBoundingBox` แทน `BoundBox`, ไม่ใช่ผลที่ pre-register): ผ่าน 41/44 = 93.2% ยังต่ำกว่า 95% และ 3 body เปิดยังอยู่ → H1 ตกเหมือนเดิม

**ใน 41 part ที่ปิดทั้งสองฝั่ง** ค่าต่างสูงสุด: volume 0.0101%, area 0.0086%, COM 0.00035% ของเส้นทแยง bbox — ต่ำกว่าเกณฑ์ 0.2% ราว 20 เท่า

**ความหมาย:** ชิ้นที่ SolidCraft อ่านได้ ค่าแม่นมาก. ปัญหาคือ importer ทำ body บางชิ้นเปิด (3/44 ≈ 7%) ถ้าจะใช้ STEP จาก FreeCAD ต่อใน SolidCraft ต้องเช็ก `closed` ทุกชิ้น. H2 (สร้างใหม่ใน SolidCraft) ไม่ผ่าน importer ตัวนี้ เลยยังต้องวัดแยก

เกณฑ์: volume ≤ 0.2%, area ≤ 0.2%, bbox ≤ 0.05 mm ทุกขอบ (เทียบ BoundBox ของ FreeCAD), COM ≤ 0.2% ของเส้นทแยง bbox; ตัวหนา = ไม่ผ่าน

คอลัมน์ bbox (optimalBoundingBox) = เทียบกับ optimalBoundingBox ของ FreeCAD, exploratory ไม่ใช้ตัดสิน

| part | ผล | volume | area | bbox | COM | bbox (optimalBoundingBox) | หมายเหตุ |
|---|---|---|---|---|---|---|---|
| base_drum | pass | 0.0039% | 0.0009% | 0.0000 mm | 0.0004% | 0.0000 mm |  |
| base_lazy_susan | pass | 0.0038% | 0.0031% | 0.0000 mm | 0.0000% | 0.0000 mm |  |
| base_leg_1 | pass | 0.0006% | 0.0016% | 0.0001 mm | 0.0001% | 0.0001 mm |  |
| base_leg_2 | pass | 0.0006% | 0.0016% | 0.0001 mm | 0.0001% | 0.0001 mm |  |
| base_leg_3 | pass | 0.0006% | 0.0016% | 0.0001 mm | 0.0001% | 0.0001 mm |  |
| base_leg_4 | pass | 0.0006% | 0.0016% | 0.0002 mm | 0.0001% | 0.0002 mm |  |
| base_leg_5 | pass | 0.0006% | 0.0017% | 0.0002 mm | 0.0001% | 0.0002 mm |  |
| base_lid | **fail** | — | **4.2789%** | **6.1794 mm** | — | 0.0000 mm | เปิดใน SolidCraft |
| base_tray | pass | 0.0018% | 0.0006% | 0.0000 mm | 0.0000% | 0.0000 mm |  |
| bearing_elbow | pass | 0.0088% | 0.0060% | 0.0000 mm | 0.0000% | 0.0000 mm |  |
| bearing_shoulder | pass | 0.0088% | 0.0060% | 0.0000 mm | 0.0000% | 0.0000 mm |  |
| column | **fail** | — | **2.3284%** | **5.7675 mm** | — | 0.0000 mm | เปิดใน SolidCraft |
| forearm_back | pass | 0.0007% | 0.0008% | 0.0001 mm | 0.0001% | 0.0001 mm |  |
| forearm_front | pass | 0.0010% | 0.0012% | 0.0001 mm | 0.0003% | 0.0001 mm |  |
| gripper_backcrank_dn | pass | 0.0005% | 0.0006% | 0.0000 mm | 0.0000% | 0.0000 mm |  |
| gripper_backcrank_up | pass | 0.0005% | 0.0006% | 0.0000 mm | 0.0000% | 0.0000 mm |  |
| gripper_backfollower_dn | pass | 0.0005% | 0.0006% | 0.0000 mm | 0.0000% | 0.0000 mm |  |
| gripper_backfollower_up | pass | 0.0005% | 0.0006% | 0.0000 mm | 0.0000% | 0.0000 mm |  |
| gripper_cover | **fail** | — | **10.9865%** | **0.4120 mm** | — | 0.0000 mm | เปิดใน SolidCraft |
| gripper_finger_dn | pass | 0.0001% | 0.0002% | 0.0000 mm | 0.0000% | 0.0000 mm |  |
| gripper_finger_up | pass | 0.0001% | 0.0002% | 0.0000 mm | 0.0000% | 0.0000 mm |  |
| gripper_follower_dn | pass | 0.0005% | 0.0006% | 0.0000 mm | 0.0000% | 0.0000 mm |  |
| gripper_follower_up | pass | 0.0005% | 0.0006% | 0.0000 mm | 0.0000% | 0.0000 mm |  |
| gripper_gear_crank_dn | pass | 0.0007% | 0.0002% | 0.0000 mm | 0.0000% | 0.0000 mm |  |
| gripper_gear_crank_up | pass | 0.0005% | 0.0001% | 0.0000 mm | 0.0003% | 0.0000 mm |  |
| gripper_pad_dn | pass | 0.0000% | 0.0000% | 0.0000 mm | 0.0000% | 0.0000 mm |  |
| gripper_pad_up | pass | 0.0000% | 0.0000% | 0.0000 mm | 0.0000% | 0.0000 mm |  |
| gripper_palm | pass | 0.0007% | 0.0009% | 0.0000 mm | 0.0000% | 0.0000 mm |  |
| gripper_pins | pass | 0.0101% | 0.0035% | 0.0000 mm | 0.0000% | 0.0000 mm |  |
| horn_elbow | pass | 0.0029% | 0.0024% | 0.0000 mm | 0.0001% | 0.0000 mm |  |
| horn_gripper | pass | 0.0087% | 0.0086% | 0.0000 mm | 0.0000% | 0.0000 mm |  |
| horn_pan | pass | 0.0082% | 0.0060% | 0.0000 mm | 0.0000% | 0.0000 mm |  |
| horn_shoulder | pass | 0.0029% | 0.0024% | 0.0000 mm | 0.0001% | 0.0000 mm |  |
| horn_wrist_flex | pass | 0.0029% | 0.0024% | 0.0000 mm | 0.0001% | 0.0000 mm |  |
| horn_wrist_roll | pass | 0.0087% | 0.0086% | 0.0000 mm | 0.0000% | 0.0000 mm |  |
| servo_clamp_shoulder | pass | 0.0006% | 0.0024% | 0.0000 mm | 0.0000% | 0.0000 mm |  |
| servo_elbow | pass | 0.0000% | 0.0000% | 0.0000 mm | 0.0000% | 0.0000 mm |  |
| servo_gripper | pass | 0.0002% | 0.0001% | 0.0000 mm | 0.0001% | 0.0000 mm |  |
| servo_pan | pass | 0.0000% | 0.0000% | 0.0000 mm | 0.0000% | 0.0000 mm |  |
| servo_shoulder | pass | 0.0000% | 0.0000% | 0.0000 mm | 0.0000% | 0.0000 mm |  |
| servo_wrist_flex | pass | 0.0000% | 0.0000% | 0.0000 mm | 0.0000% | 0.0000 mm |  |
| servo_wrist_roll | pass | 0.0002% | 0.0001% | 0.0000 mm | 0.0001% | 0.0000 mm |  |
| upper_link | **fail** | 0.0007% | 0.0008% | **6.2479 mm** | 0.0000% | 0.0000 mm |  |
| wrist | **fail** | 0.0003% | 0.0006% | **10.7789 mm** | 0.0000% | 0.0000 mm |  |
