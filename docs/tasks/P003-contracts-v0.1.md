# P003 — ภาษากลาง v0.1
- ID / วันที่ / สถานะ: P003 / 2026-10-22 / โค้ดเสร็จในร่าง รอทีมเห็นชอบแล้วล็อก (เลยกำหนดสัปดาห์ 0)
- คำขอและผลที่ต้องได้: สัญญาข้อมูลระหว่างเลนที่ทุกคนใช้ได้ทันที เพื่อให้ A, B, C ทำงานพร้อมกันโดยใช้ของจำลองแทนเลนอื่น
- Owner / บทบาท / เหตุผลที่แยกงาน: โรล C เป็นเจ้าของ; ทั้งทีมร่วมร่างในสัปดาห์ 0; B ส่งรายชื่อข้อต่อและช่วงมุม
- แหล่งข้อกำหนดที่ต้องอ่าน: docs/interfaces/contracts-v0.1.md (ร่าง), docs/research/01-RESEARCH-MASTER.md ข้อ 8, docs/roadmap.md ข้อ 4–5
- Owned files (exact paths): `docs/interfaces/contracts-v0.1.md`, แพ็กเกจโค้ดสัญญาใหม่ (ชื่อโฟลเดอร์ตกลงในสัปดาห์ 0 เช่น `arm_contracts/`), `tests/test_contracts.py`
- Read-only / ห้ามแตะ: `camera_gestures/` (เลน A), โค้ดซิม (เลน B)
- Baseline: main หลัง merge PR นี้
- Dependencies / interface version: ไม่มี; เป็นจุดเริ่มของ v0.1
- เกณฑ์ยอมรับ:
  - ทั้งทีมเห็นชอบ spec ในวันพุธของสัปดาห์ 0 และ C ล็อกเป็น v0.1
  - โครงข้อมูลสำหรับ EndEffectorTarget, JointCommand, RobotState พร้อมอ่าน/เขียน JSON Lines
  - ตรวจค่า: ทุกตัวเลขเป็น finite, ค่าจับอยู่ใน 0–1, quaternion ปกติ, ชื่อข้อต่อตรงกับโปรไฟล์, เลขเวอร์ชันตรง, seq เพิ่มขึ้น
  - ไฟล์ replay ตัวอย่างหนึ่งชุด + สคริปต์สร้างคำสั่ง (วงกลม, สี่เหลี่ยม, จุดที่รู้ค่า)
  - แขนจำลองบนจอที่รับ EndEffectorTarget แล้ววาดจุด
  - ศุกร์สัปดาห์ 0: replay → mapping ปัจจุบัน → แขนจำลอง ต่อกันได้
- วิธีตรวจ / environment: `python -m unittest discover -s tests -v` + CI บน Windows
- Authorization ที่มี / action ที่ยังไม่ได้รับ: เปลี่ยนสัญญาหลังล็อกต้องผ่านวันจันทร์และขึ้นเลขเวอร์ชัน
- ความเสี่ยงและเงื่อนไขคืนผู้คุมงาน: ถ้าสัญญาผิดจะต้องแก้ทั้งสามเลน ให้ทำให้เล็กที่สุด เพิ่มฟิลด์ทีหลังได้ง่ายกว่าลบ

## ผลส่งกลับ
- เปลี่ยนอะไร: เพิ่ม `arm_contracts/` (messages, profiles, replay, scripted, mock_arm, from_camera_log, ไฟล์ sample), `tests/test_contracts.py`, `tests/test_contract_tools.py` และเติมร่างสัญญา (ข้อ 1, 3–9)
- ตรวจอะไร คำสั่งและผล: ดูผลล่าสุดใน PR; `python -m unittest discover -s tests -v` บน macOS Python 3.11; log จริง 2 ชุดจาก 2026-09-18 (2,952 และ 2,858 เฟรม) ผ่าน log → `ee_target` → แขนจำลอง: ไม่มีข้อความถูกปฏิเสธ และจุดไม่ขยับระหว่าง hold
- ยังไม่ตรวจ / ข้อจำกัด: ทีมยังไม่เห็นชอบ จึงยังไม่ล็อก v0.1; ยังไม่ได้เปิดหน้าต่างแขนจำลองบน Windows (เทสต์ใช้โหมด `--save`); mapping ใน `from_camera_log` เป็นค่าชั่วคราว ไม่ใช่หน่วยเมตรและไม่ใช่ผลความแม่น
- หลักฐาน / artifact: `arm_contracts/samples/demo.ee_target.jsonl`
- งานต่อ: P004, P006, P007
