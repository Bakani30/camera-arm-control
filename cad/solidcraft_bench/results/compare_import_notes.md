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
