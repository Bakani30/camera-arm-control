# P000 — Camera gesture output
2026-09-18: ผู้ใช้อนุมัติเริ่มต้นแบบกล้องก่อนแขนและ AI retargeting
Windows + ASUS TUF A15; ทีมเรียนรู้และทำทีละช่วงร่วมกัน
ขอบเขต: มือเดียว แบ=01 กำ=10 ไม่ชัด=00 ภาพ/จุดมือ/CSV output changes
ไฟล์: camera_gestures/, requirements.txt, tests/test_state.py, docs/camera-gestures.md
ตรวจแล้ว: pure state unit tests 4 ผ่าน และ Python compile check ผ่านบน macOS
ยังไม่ผ่าน acceptance: กล้อง ASUS/Windows และความถูกต้องจำแนกมือจริง NOT RUN
งานต่อ: ติดตั้งบน Windows เก็บ pilot ตามคู่มือ ยังไม่ต่อแขนจริง
P001 feasibility ของซิม/BOM ไม่ถือว่าจบจากต้นแบบนี้

อัปเดตคู่มือทีม: เพิ่มรายการติดตั้ง การเข้าถึง Private repo วิธี clone/ZIP การตรวจติดตั้ง และการอัปเดต; Windows ASUS ยัง NOT RUN

## รุ่น diagnostic
ผู้ใช้รายงานรุ่นแรกเปิดใช้ได้ แต่ผลไม่นิ่ง; เพิ่ม observation.py แยกผลดิบ, ป้ายกำกับด้วยปุ่ม และ frames.jsonl ทุกเฟรม ไม่เปลี่ยนโมเดล/ตัวกรอง ไม่อ้างความแม่นยำเพิ่ม
ทดสอบ unit 7 ผ่านและ compile/help ผ่านบน macOS; ASUS รุ่นใหม่รอทีมตรวจตาม docs/mediapipe-team-test.md
