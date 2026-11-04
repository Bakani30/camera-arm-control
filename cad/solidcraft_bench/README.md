# SolidCraft accuracy bench (งาน A)

2026-11-03 · โรล C · เทียบ volume, area, bbox และ COM ของชิ้น shell_v1 ระหว่าง SolidCraft กับ FreeCAD ก่อนย้าย CAD หลักไป SolidCraft

แผน pre-registered (เกณฑ์, hypothesis H1/H2, stop criterion): `input/ideas/solidcraft-accuracy-bench-plan.md` ในโฟลเดอร์ outputs ของทีม (นอก repo)

## เวอร์ชันที่ล็อก
| เครื่องมือ | เวอร์ชัน | ที่อยู่ (macOS) |
|---|---|---|
| SolidCraft | 0.30.1 | `/Applications/SolidCraft.app`, CLI `/opt/homebrew/bin/solidcraft-cli` |
| FreeCAD | 1.1.4 (Revision 20260928) | `/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd` |
| repo | origin/main 32748c2 | `cad/shell_v1/` |
| Python | 3.14.3 (สคริปต์เทียบใช้ stdlib อย่างเดียว) | |

เปลี่ยนเวอร์ชันกลางทาง = จดใน Deviations Log ของแผนและวัดใหม่ทั้งหมด

## เกณฑ์ต่อ body
- volume, area: ต่างไม่เกิน 0.2% ของค่า FreeCAD
- bbox: ทั้ง 6 ขอบต่างไม่เกิน 0.05 mm. แผน v1 เทียบกับ `BoundBox`, แผน v2 (2026-11-04) เทียบกับ `optimalBoundingBox` เพราะ `BoundBox` หลวมบนผิวโค้ง (`compare.py --bbox optimal`)
- COM: ห่างไม่เกิน 0.2% ของเส้นทแยง bbox ของ FreeCAD

## ไฟล์
- `results/`: ค่าที่วัดได้ (JSON) และตารางเทียบ (`compare_*.md`)
- `rebuild/`: SolidCraft JSON script ของชิ้นที่สร้างใหม่ (turntable, servo_clamp_shoulder, forearm_core_front)
- `out/`: STEP รายชิ้นที่ FreeCAD export (ไม่เข้า git)

## รัน (จาก root ของ repo)
```
freecadcmd cad/solidcraft_bench/freecad_measure.py      # Task 1: results/freecad_ref.json + out/step/<part>.step (~10 s)
freecadcmd cad/solidcraft_bench/freecad_rebuild_ref.py  # Task 2 + 12: the 3 rebuild parts and the 3 held-out parts, + one changed parameter each
python3 cad/solidcraft_bench/solidcraft_import.py       # Task 3: results/solidcraft_import.json (~20 s, needs solidcraft-cli on PATH)
python3 cad/solidcraft_bench/compare.py cad/solidcraft_bench/results/freecad_ref.json \
  cad/solidcraft_bench/results/solidcraft_import.json cad/solidcraft_bench/results/compare_import.md \
  --hypothesis H1 --notes cad/solidcraft_bench/results/compare_import_notes.md   # Task 4
python3 -m unittest cad/solidcraft_bench/test_compare.py
python3 cad/solidcraft_bench/rebuild/make_gear_crank.py   # writes rebuild/gripper_gear_crank_up.json (224-point gear outline)
python3 cad/solidcraft_bench/rebuild/make_base_tray.py    # writes rebuild/base_tray.json (225 switched grid circles)
python3 cad/solidcraft_bench/solidcraft_rebuild.py [part ...]   # Task 5-7, 13: results/solidcraft_rebuild.json
python3 cad/solidcraft_bench/compare.py cad/solidcraft_bench/results/freecad_ref.json \
  cad/solidcraft_bench/results/solidcraft_rebuild.json cad/solidcraft_bench/results/compare_rebuild.md \
  --hypothesis H2 --notes cad/solidcraft_bench/results/compare_rebuild_notes.md   # Task 8 (v1)
python3 cad/solidcraft_bench/compare.py cad/solidcraft_bench/results/freecad_ref.json \
  cad/solidcraft_bench/results/solidcraft_rebuild.json cad/solidcraft_bench/results/compare_rebuild_v2.md \
  --hypothesis H2 --bbox optimal --exploratory --notes cad/solidcraft_bench/results/compare_rebuild_v2_notes.md
python3 cad/solidcraft_bench/compare.py cad/solidcraft_bench/results/freecad_ref.json \
  cad/solidcraft_bench/results/solidcraft_rebuild.json cad/solidcraft_bench/results/compare_heldout.md \
  --hypothesis H2v2 --bbox optimal --notes cad/solidcraft_bench/results/compare_heldout_notes.md \
  --keys gripper_pad_up_local,gripper_pad_up_local@top=+2,gripper_gear_crank_up_local,gripper_gear_crank_up_local@link=+2,base_tray_local,base_tray_local@r=+2   # Task 14
```

## ผล
- **H1 (import): ตก** — 39/44 ผ่าน, 3 ชิ้นเปิดใน SolidCraft (ดู `results/compare_import.md`). เกณฑ์ v2 แบบ exploratory: 41/44 ยังตก
- **H2 (rebuild 3 ชิ้น): ตก** ตามเกณฑ์ v1 — 4/6, turntable ตกเพราะ `BoundBox` หลวมอย่างเดียว. เกณฑ์ v2 แบบ exploratory: 6/6 (ดู `results/compare_rebuild.md`, `compare_rebuild_v2.md`)
- **H2v2 (rebuild ชิ้น held-out, ผลยืนยันของแผน v2): ยืนยัน** — 6/6, `gripper_pad_up`, `gripper_gear_crank_up`, `base_tray` (ดู `results/compare_heldout.md`)
- 2026-11-04 ทีมเลิกใช้ FreeCAD. ref ใน `results/freecad_ref.json` บันทึกครบแล้ว ส่วนที่เหลือของ bench ใช้แค่ SolidCraft
`fc_common.py` เก็บโค้ดวัดฝั่ง FreeCAD ที่ใช้ร่วมกัน. รัน Task 1 ก่อน Task 2 เพราะทั้งคู่เขียนลง `freecad_ref.json`
`freecadcmd` บน macOS อยู่ที่ `/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd`
