# P006-M0 — Relative mapping จากมือไปจุดเป้าบน mock arm
- ID / วันที่ / สถานะ: P006-M0 / 2026-11-01 / โค้ด + เทสต์เสร็จใน `a/relative-mapping`; กล้องจริง NOT RUN; ยังไม่ merge
- คำขอและผลที่ต้องได้: กด C แล้วขยับมือ จุดเป้าบน mock arm ตามสด และบันทึก `ee_target` ทุกรอบ ดู [design](../superpowers/specs/2026-11-01-m0-relative-mapping-design.md)
- Owner / บทบาท / เหตุผลที่แยกงาน: เลน A; ก้าวแรกของ P006 และเป็น M0 ตาม roadmap ข้อ 7
- แหล่งข้อกำหนดที่ต้องอ่าน: design ด้านบน, D18, D20, `docs/interfaces/contracts-v0.1.md` ข้อ 2 และ 6
- Owned files (exact paths): `camera_gestures/mapping.py`, `camera_gestures/mapping_session.py`, `camera_gestures/mapping_report.py`, `camera_gestures/app.py`, `tests/test_mapping.py`, `tests/test_mapping_session.py`, `tests/test_mapping_app.py`, `tests/test_mapping_report.py`
- แก้นอกเลน A แบบเพิ่มความสามารถ ไม่เปลี่ยนสัญญา: `arm_contracts/replay.py` (`ReplayWriter`), `arm_contracts/mock_arm.py` (`render` รับกล่องและจุดเป้า), `tests/test_contract_tools.py`
- Read-only / ห้ามแตะ: `docs/interfaces/`, `camera_gestures/metric.py`, `camera_gestures/control.py`, `camera_gestures/replay.py`, โค้ดซิมของ B
- Baseline: `a/metric-mapping` ที่ `b71c03d`; เทสต์ฐานผ่าน 264 ตัว
- Dependencies / interface version: P002 (ยังไม่ merge และรอผลกล้องจริง), ภาษากลาง v0.1
- เกณฑ์ยอมรับ: เทสต์ทั้งชุดผ่าน และเกณฑ์กล้องจริงในตาราง design ผ่านครบบน Windows พร้อมบันทึกผลแนบ PR
- วิธีตรวจ / environment: `python -m unittest discover -s tests -v`; ขั้นตอนกล้องอยู่ใน `docs/camera-gestures.md`; สรุปตัวเลขด้วย `python -m camera_gestures.mapping_report`
- Authorization ที่มี / action ที่ยังไม่ได้รับ: แก้โค้ดในขอบเขตนี้; ไม่สั่งแขนจริง ไม่ merge จนกล้องจริงผ่าน
- ความเสี่ยงและเงื่อนไขคืนผู้คุมงาน: ถ้าเกณฑ์ไม่ผ่าน ให้รายงานผลก่อนปรับเกณฑ์

## ผลส่งกลับ
- เปลี่ยนอะไร: เพิ่ม mapper, session, รายงาน และ `--mapping relative`; ไม่ใส่ flag โปรแกรมทำงานเหมือนเดิม
- ต่างจาก design: ไฟล์ที่ OS ตัดกลางบรรทัดยังอ่านด้วย `read_replay` ไม่ได้ เพราะ reader ตั้งใจ raise; writer flush ทีละบรรทัดแทน
- ตรวจอะไร: เทสต์ทั้งชุด รวม `tests/test_mapping_app.py` ที่รัน `app.main` ด้วยกล้อง, recognizer และคีย์บอร์ดปลอม
- ยังไม่ตรวจ / ข้อจำกัด: **กล้องจริง, มือจริง, Windows และซิม NOT RUN**; เกณฑ์ตัวเลขเป็นค่าเริ่มต้นชั่วคราว; ผลรอบนี้เทียบกับ bubble ไม่ได้เพราะยังใช้ EMA (roadmap ข้อ 7); ก่อนต่อแขนจริงต้องตัดสินวิธีรับตำแหน่งแขนและแก้สัญญา
- หลักฐาน / artifact: `tests/test_mapping*.py`; ผลกล้องจริงให้บันทึกด้วย `docs/templates/experiment-record.md`
- งานต่อ: ทดสอบกล้องจริง แล้วทำ bubble + One Euro ใน P006
