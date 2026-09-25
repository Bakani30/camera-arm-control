# P000 — Camera gesture output
2026-09-18: ผู้ใช้อนุมัติเริ่มต้นแบบกล้องก่อนแขนและ AI retargeting
Windows + ASUS TUF A15; ทีมเรียนรู้และทำทีละช่วงร่วมกัน
ขอบเขต: มือเดียว แบ=01 กำ=10 ไม่ชัด=00 ภาพ/จุดมือ/CSV all frames (ค้างค่าเดิมตราบใดที่ตรวจเจอมือ + drop timeout เมื่อมือหลุด)
ไฟล์: camera_gestures/, requirements.txt, tests/test_state.py, docs/camera-gestures.md
ตรวจแล้ว: pure state unit tests 7 ผ่าน และ Python compile check ผ่านบน Windows
ยังไม่ผ่าน acceptance: กล้อง ASUS/Windows และความถูกต้องจำแนกมือจริง NOT RUN
งานต่อ: ติดตั้งบน Windows เก็บ pilot ตามคู่มือ ยังไม่ต่อแขนจริง
P001 feasibility ของซิม/BOM ไม่ถือว่าจบจากต้นแบบนี้

อัปเดตคู่มือทีม: เพิ่มรายการติดตั้ง การเข้าถึง Private repo วิธี clone/ZIP การตรวจติดตั้ง และการอัปเดต; Windows ASUS ยัง NOT RUN

## รุ่น diagnostic
ผู้ใช้รายงานรุ่นแรกเปิดใช้ได้ แต่ผลไม่นิ่ง; เพิ่ม observation.py แยกผลดิบ, ป้ายกำกับด้วยปุ่ม และ frames.jsonl ทุกเฟรม ไม่เปลี่ยนโมเดล/ตัวกรอง ไม่อ้างความแม่นยำเพิ่ม
ทดสอบ unit 7 ผ่านและ compile/help ผ่านบน macOS; ASUS รุ่นใหม่รอทีมตรวจตาม docs/mediapipe-team-test.md

ตรวจอัปเดตหลัก: fetch และตรวจ branch/PR แล้วไม่มีงานค้างรวม รุ่น 947bf06 ผ่าน Windows CI (ไม่มีกล้อง) ปรับ README ให้ตรงกับพฤติกรรมคงรหัส; unit suite ปัจจุบัน 10 รายการ

ทดลอง keypoint: เพิ่มตัวเลือก classifier จาก Kazuhito พร้อม normalize/checksum/license ใช้ environment แยก ค่าเริ่มต้นยังเป็น MediaPipe; unit tests 12 ผ่าน รอผลกล้องใกล้–ไกลจริง ดู docs/keypoint-trial.md

เพิ่ม target.py/display.py และ tests/test_target.py: bounding box, ชื่อท่าปัจจุบัน, target 2D กรองตามเวลาและ calibrate/pause/loss policy; ทดสอบรวม 15 ผ่าน ยังไม่เชื่อมซิมหรือฮาร์ดแวร์

ผู้ใช้ยืนยัน XY ผ่านตามการทดลอง; เพิ่ม depth proxy จากขนาดฝ่ามือ พร้อมแถบและ logging, tests รวม 18 ผ่าน รอทดลองเข้า–ออก/กำ–แบ/เอียงบนกล้องจริง ยังไม่ใช่ metric depth

เพิ่ม selected-hand (คนเดียว Left/Right) และ HandControl: auto-reanchor XYZ ในเฟรมแรกหลังกลับเข้าโดยรักษาเป้าหมาย, C rebase, R reset XYZ, Space manual pause; tests 21 ผ่านบน macOS ยังรอทดสอบกล้องกรณีสองมือ/กลับเข้า

คู่มือติดตั้งเพิ่ม optional TensorFlow/keypoint model ใน .venv-keypoint และปุ่มควบคุมมือ/ศูนย์/พัก สำหรับแจกทีม Windows
