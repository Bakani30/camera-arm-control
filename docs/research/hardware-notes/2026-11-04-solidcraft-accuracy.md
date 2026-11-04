# ความแม่นของ SolidCraft เทียบ FreeCAD บนชิ้นแขน shell_v1 (งาน A)

วันที่ 2026-11-04 · โรล C · bench ซอฟต์แวร์ล้วน ไม่ได้พิมพ์ชิ้น ไม่ได้วัดของจริง · ทุกผลเป็น **ผลเทียบ CAD กับ CAD ไม่ใช่ผลฮาร์ดแวร์** · แผน pre-registered v1 (2026-11-03) + amendment v2 (2026-11-04) อยู่นอก repo ที่ `input/ideas/solidcraft-accuracy-bench-plan.md` · สคริปต์และผลอยู่ใน `cad/solidcraft_bench/`

## ข้อเสนอ

**ใช้ SolidCraft เป็น CAD หลักได้ และเปิดงาน B (ย้าย shell_v1 มาเป็น script แบบ parametric) ได้** ชิ้นที่สร้างใหม่ใน SolidCraft ทั้ง 6 ชิ้นได้ volume, area, COM และ bbox ตรงกับ FreeCAD ภายใน 0.1% ทั้งที่ค่าปกติและหลังเปลี่ยน parameter. ทีมตัดสินเลิกใช้ FreeCAD แล้ว (2026-11-04) งาน B ต้องออกแบบหลบข้อจำกัด 3 ข้อด้านล่าง ไม่ใช่ลอกลำดับ feature ของ FreeCAD ทุกบรรทัด

ข้อจำกัดที่งาน B ต้องรู้ (SolidCraft 0.30.1):
1. **fillet มุมที่ขอบเว้ามาเจอขอบนูนไม่ได้** (`not supported yet: a blend ending in an earlier round`). เช่น ขาที่ต่อกับแผ่นของ `servo_clamp_shoulder` → ออกแบบให้มุมแบบนี้คม หรือหลีกเลี่ยงรูปทรงแบบนี้
2. **boolean ที่ผิวโค้งตัดกันที่มุมตื้นอาจ fail เมื่อเปลี่ยน parameter** (`the exact fallback ... takes planar faces only`). เช่น ท่อ r 20.3 ตัดกับ hub r 20 ใน `forearm_core_front` → สลับลำดับ feature (ตัดก่อนแล้วค่อย join) และต้องลองเปลี่ยนค่าที่จะเปลี่ยนจริงทุกครั้ง ก่อนบอกว่า script ใช้ได้
3. **import STEP แล้ว body เปิด 3/44 ชิ้น** (`base_lid`, `column`, `gripper_cover`) ทั้งที่ไฟล์ STEP ถูกต้อง → ถ้าต้องรับ STEP จากที่อื่น ต้องเช็ก `closed` ทุกชิ้น. งาน B ควรสร้างใหม่ ไม่ใช่ import

## ผล

| hypothesis | ชิ้น | เกณฑ์ | ผล | ไฟล์ |
|---|---|---|---|---|
| H1 import STEP | 44 ชิ้นของ `build_all()` | v1 (`BoundBox`) | **ตก** 39/44, 3 body เปิด | `results/compare_import.md` |
| H1 | 44 ชิ้น | v2 (tight bbox), exploratory | ตก 41/44, 3 body เปิด | — |
| H2 สร้างใหม่ | turntable, servo_clamp_shoulder, forearm_core_front × 2 ค่า | v1 | **ตก** 4/6: turntable ตกเพราะ `BoundBox` ของ FreeCAD หลวมเท่านั้น | `results/compare_rebuild.md` |
| H2 | 3 ชิ้นเดิม | v2, exploratory | 6/6 | `results/compare_rebuild_v2.md` |
| **H2v2 สร้างใหม่ (ผลยืนยันของ v2)** | ชิ้น held-out ที่สุ่มได้: gripper_pad_up, gripper_gear_crank_up, base_tray × 2 ค่า | v2 | **ยืนยัน 6/6** | `results/compare_heldout.md` |

- เกณฑ์ต่อ body: volume และ area ต่างไม่เกิน 0.2%, bbox ทุกขอบต่างไม่เกิน 0.05 mm, COM ห่างไม่เกิน 0.2% ของเส้นทแยง bbox
- v2 เปลี่ยนเฉพาะ bbox: เทียบกับ `optimalBoundingBox` แทน `BoundBox`. ผู้ใช้ตัดสินหลังเห็นว่า `BoundBox` หลวม 5.8–10.8 mm บนผิวโค้ง (turntable, upper_link, wrist). ผลของชิ้นที่วัดไปก่อนเปลี่ยนจึงเป็น exploratory. ผลยืนยันมาจากชิ้น held-out ที่สุ่มก่อนล็อก v2
- ใน 41 ชิ้นที่ import แล้วปิดทั้งสองฝั่ง ค่าต่างสูงสุด: volume 0.0101%, area 0.0086%, COM 0.00035%
- ชิ้นที่สร้างใหม่ทั้ง 6 ชิ้น (12 key) ค่าต่างสูงสุด: volume 0.021% (clamp ที่ไม่มี fillet ขอบเว้า), area 0.097% (clamp), COM 0.0018%, tight bbox 0.0007 mm

## ชิ้นที่ไม่ผ่านหรือมีเงื่อนไข

| ชิ้น | ผล | สาเหตุ |
|---|---|---|
| `base_lid`, `column`, `gripper_cover` (import) | body เปิด | importer ของ SolidCraft: มี face ชนิด `other` และจำนวน face น้อยกว่าที่ kernel นับ. FreeCAD อ่าน STEP เดียวกันกลับมาได้ปิดและ valid |
| `upper_link`, `wrist` (import) | ตก bbox v1 | `BoundBox` ของ FreeCAD หลวม 6.2 และ 10.8 mm. tight bbox ต่าง ≤ 0.00015 mm |
| `turntable` (สร้างใหม่) | ตก bbox v1 | `BoundBox` หลวม 5.77 และ 6.18 mm. volume, area, COM ต่าง ≤ 0.001% |
| `servo_clamp_shoulder` | ผ่านตัวเลข แต่ fillet ไม่ครบ | ขอบเว้า 6 เส้นยังคม (ข้อจำกัดข้อ 1). volume ที่ขาด 1.40 mm³ คือเนื้อของ fillet ที่ไม่ได้ทำ |
| `forearm_core_front` | ผ่านหลังสลับลำดับ | ลำดับแบบ FreeCAD error เมื่อ `tube_r` +2 (ข้อจำกัดข้อ 2). join ต้องให้ kernel ขยับ tool 0.0003 mm |

## บทเรียนสำหรับงาน B และ D (คู่มือทีม)

- **flow ที่ใช้ได้:**
  1. อ่านขนาดจาก source
  2. คำนวณ volume และ bbox ด้วยมือก่อน
  3. ทำ `batch` พร้อม `expect` ทีละ stage
  4. ใช้ `check_parameters` ลองค่าที่จะเปลี่ยน
  5. บันทึกเป็น JSON script แล้วรันซ้ำด้วย `solidcraft-cli eval --json-out`
- **ชิ้นที่มีจุดเยอะหรือทำซ้ำเยอะ:** ใช้ Python ล้วนเขียน JSON script. ตัวอย่างคือ `rebuild/make_gear_crank.py` (เฟือง involute 224 จุด) และ `rebuild/make_base_tray.py` (grid 225 รู). ชิ้นแบบนี้ CLI ใช้ 1–10 วินาที
- **expression:** มี `sqrt`, `cos`, `sin`, `max`, `floor`, `sign`, `abs` (มุมต้องใส่ `deg`) แต่ไม่มี `if` หรือตัวเปรียบเทียบ. เงื่อนไขเปิด/ปิด feature ให้ใช้ `max(0, sign(...))` เป็นสวิตช์ แล้วย้าย feature ที่ปิดออกไปนอกชิ้น
- **trap ที่เจอ:**
  - `sketch.slot.*` รับจุดเป็นตัวเลขเท่านั้น → วาดเป็น polyline ที่จุดเป็น expression
  - จุดใน `sketch.line` ที่เป็นตัวเลขไม่ fix ให้เอง (dof ไม่เป็น 0) → ใช้ `sketch.constraint.fix`
  - fillet ขอบล่างของ disc หลัง join boss แล้ว fail (`the blend is taller than the walls`) → fillet ขอบ disc ก่อน join
  - ชื่อ parameter ห้ามชนกับชื่อหน่วย (`m`)
- **การเช็กโดยไม่มี FreeCAD:** ใช้ค่า analytic (ทุก stage ที่คำนวณ analytic ใน bench ต่างไม่เกิน 0.006%) และ bbox ที่คำนวณมือ. ทั้งสองอย่างเช็กผ่าน `expect` ของ `batch` ได้เลย

## environment

- SolidCraft 0.30.1 (`/Applications/SolidCraft.app`, CLI `solidcraft-cli`; MCP รันแบบ headless)
- FreeCAD 1.1.4 (Revision 20260928): ใช้สร้าง ref เท่านั้น. ref ทั้งหมดบันทึกไว้ใน `results/freecad_ref.json`. ทีมไม่ใช้ FreeCAD ต่อแล้ว
- source `cad/shell_v1/` ที่ origin/main 32748c2, Python 3.14.3, macOS (Darwin 25.5), branch `c/solidcraft-bench`
- เวลาที่ใช้สร้างแต่ละชิ้น 5–30 นาที รอบแก้ 0–3 รอบ (ดูตารางต่อชิ้นใน `results/compare_rebuild.md` และ `results/compare_heldout.md`)

## ยังไม่ได้ทดสอบ

- fillet ในชิ้น held-out: ทั้ง 3 ชิ้นไม่มี fillet. ข้อจำกัดข้อ 1 จึงมาจากชิ้นเดียว (clamp)
- assembly, joint, interference, export URDF ไป MuJoCo (งาน C)
- ชิ้นที่พิมพ์จริงจาก STL ของ SolidCraft เทียบกับชิ้นจาก FreeCAD (ยังไม่มีงบ)
