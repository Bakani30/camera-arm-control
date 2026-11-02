# P002 — ปรับเทียบกล้องและแปลงมือเป็นหน่วยเมตร
- ID / วันที่ / สถานะ: P002 / 2026-10-22 / โค้ด + เทสต์ใน `a/metric-mapping`; รอทดสอบกล้องจริง (sprint 1, 2–13 พ.ย.)
- คำขอและผลที่ต้องได้: ตำแหน่งมือเป็นหน่วยเมตรที่ไม่เพี้ยนตาม aspect ratio และไม่เปลี่ยน gain ตามระยะ Z เป็นฐานของ bubble ใน P006
- Owner / บทบาท / เหตุผลที่แยกงาน: โรล A; งานในเลนมือ→เป้าหมาย ทดสอบได้ด้วยกล้องหรือไฟล์ replay ไม่ต้องมีแขน
- แหล่งข้อกำหนดที่ต้องอ่าน: docs/roadmap.md ข้อ 4–5, docs/interfaces/contracts-v0.1.md (ภาษากลาง 1), D18 D20 ใน docs/research/03-DECISIONS-GLOSSARY.md
- Owned files (exact paths): `camera_gestures/target.py`, `camera_gestures/depth.py`, `camera_gestures/control.py`, ไฟล์ใหม่สำหรับ calibration ใน `camera_gestures/`, tests ที่เกี่ยวข้องใน `tests/`
- Read-only / ห้ามแตะ: โค้ดภาษากลางของ C (ขอแก้ผ่านวันจันทร์), โค้ดซิมของ B
- Baseline: main หลัง merge PR นี้; tests เดิม 21 ตัวผ่านด้วย `python -m unittest discover -s tests -v`
- Dependencies / interface version: ภาษากลาง 1 v0.1 (ใช้ร่างได้ก่อน C ล็อก)
- เกณฑ์ยอมรับ:
  - ปรับเทียบกล้องด้วย checkerboard (OpenCV) ได้ค่า `f` และบันทึกลงไฟล์ calibration พร้อมความละเอียดภาพที่ใช้
  - ล็อกความละเอียดภาพ และบันทึกค่า `f` + ความละเอียดลง metadata ของ log ทุกรอบ
  - รับความยาวฝ่ามือของผู้ใช้ (ม.) ครั้งเดียว แล้วคำนวณ `Z ≈ f·L / palm_px`, `ΔX = Δu·Z/f`, `ΔY = Δv·Z/f`
  - ใช้จุดกลางฐานฝ่ามือ (landmark 0, 5, 9, 17) แทน wrist
  - ชดเชยการเอียงมือใน `palm_scale` ด้วย 3D landmark (D20)
  - เทสต์ใหม่: ขยับ 5 ซม. ที่ระยะต่างกันได้ ΔX ใกล้กัน; aspect ratio ไม่ทำให้ X/Y ต่างกัน
- วิธีตรวจ / environment: unit tests บนเครื่องใดก็ได้ + ทดสอบกล้องจริงบน Windows ของตัวเอง บันทึกผลด้วย docs/templates/experiment-record.md
- Authorization ที่มี / action ที่ยังไม่ได้รับ: แก้โค้ดในเลน A ได้; ยังไม่สั่งแขนจริง
- ความเสี่ยงและเงื่อนไขคืนผู้คุมงาน: ถ้าค่า `f` เปลี่ยนเมื่อกล้อง autofocus หรือเปลี่ยนความละเอียด ให้แจ้ง C ก่อนตั้งค่าตายตัว

## ผลส่งกลับ
- เปลี่ยนอะไร: เพิ่ม `camera_gestures/calibration.py` (ปรับเทียบ checkerboard, ไฟล์ค่า f + ความละเอียด) และ `camera_gestures/metric.py` (จุดกลางฐานฝ่ามือ, ความยาวฝ่ามือชดเชยเอียงด้วย z, ตำแหน่งเมตร); `--calibration` + `--palm-length-m` ใน app; log และ replay เก็บค่า metric; ไม่มี 2 ค่านี้ โปรแกรมทำงานเหมือนเดิม
- ต่างจากร่างแพ็กเกจ 3 จุด:
  - ใช้ `X=(u-cx)·Z/f` แล้วคิดผลต่าง แทน `ΔX=Δu·Z/f` เพราะสูตรเดิมอ่านการดันมือเข้ากล้องเป็นการขยับด้านข้างเมื่อมือไม่อยู่กลางภาพ ถ้า Z คงที่ได้ค่าเท่าเดิม แต่ noise ของ Z จะเข้า X/Y ตามระยะห่างจากกลางภาพ ต้องวัดบนกล้องจริง
  - ใช้ความยาวข้อมือถึงโคนนิ้วกลาง (landmark 0–9) แทน `palm_scale` เพราะ `palm_scale` เป็นค่าเฉลี่ยเรขาคณิตของกว้างกับยาว เทียบกับความยาวที่วัดด้วยไม้บรรทัดตรงๆ ไม่ได้
  - ชดเชยเอียงและจุดกลางฝ่ามืออยู่ในเส้นทาง metric ใหม่ `palm_scale`, `RelativeDepth` และ `ScreenTarget` ยังเดิม เพื่อให้ replay และ log เก่าเทียบได้ตรง P006 ค่อยย้ายไปใช้เส้นทางใหม่
- ตรวจอะไร คำสั่งและผล: `python -m unittest discover -s tests` ผ่านทั้งหมดบน macOS Python 3.11 (ข้อมูลมือและ checkerboard จำลอง); ลองทำลายโค้ด 7 จุดแล้วเทสต์จับได้ครบ; รัน app ด้วยกล้องปลอมภาพดำผ่าน MediaPipe จริง: metadata บันทึก f, ความละเอียด, principal point ครบ แต่ไม่มีมือในภาพ
- ยังไม่ตรวจ / ข้อจำกัด: **กล้องจริงและ Windows NOT RUN**; ยังไม่รู้ว่า z ของ MediaPipe แม่นพอชดเชยเอียงจริงไหม, Z บนมือจริงผิดกี่ % และ autofocus เปลี่ยน f ไหม; ไม่แก้ distortion, ไม่มี filter (P006); เกณฑ์ "ปรับเทียบด้วย checkerboard" ผ่านแค่กับข้อมูลจำลอง
- หลักฐาน / artifact: `tests/test_metric.py`; ทดสอบกล้องจริงให้บันทึกด้วย docs/templates/experiment-record.md
- งานต่อ: P006
