# สถานะปัจจุบัน
วันที่ 2026-09-18

## ทำแล้ว
- มีฐานเอกสารวิจัย 6 ไฟล์จาก research-handoff รุ่น 1.0
- จัดโครงสร้างโปรเจกต์ กติกา agent, skills และวิธีแบ่งงาน/บันทึกการทดลอง

## ยังไม่ทำหรือยังไม่ยืนยัน
- มี implementation เฉพาะต้นแบบ gesture output; ยังไม่มี dataset, benchmark หรือผลการขยับแขนจริง
- เลือกเริ่มกล้อง ASUS TUF A15 บน Windows และทดลอง MediaPipe Gesture Recognizer; ยังไม่ยืนยันคุณภาพกล้องจริง ซิม และวิธี AI retargeting
- ยังไม่ตรวจ Windows/driver/runtime ของเครื่องแล็บและ BOM ปัจจุบัน
- ยังไม่ล็อก units/frame/quaternion/clock ของ interface จริง

## ถัดไป
P001: ตรวจความเป็นไปได้ของต้นแบบหนึ่งชุดบนเครื่องแล็บ ก่อนสร้างระบบหลายรุ่น ดู docs/tasks/P001-feasibility.md

การเขียนเอกสารนี้ไม่ใช่การทำ P001 สำเร็จ บทบาท agent ใน workflow เป็นหน้าที่ ไม่ใช่ agent ที่รันค้างอยู่

## ต้นแบบกล้อง 2026-09-18
- เพิ่ม P000: กล้อง/ท่ามือ/รหัส 01 10 00 พร้อม CSV และคู่มือ Windows
- ผู้ใช้รายงานว่าเปิดใช้รุ่นแรกบน Windows ASUS ได้แล้ว แต่การอ่านมือยังไม่คงที่; ยังไม่มีหลักฐานรอบทดลองให้วิเคราะห์
- รุ่น diagnostic เพิ่ม RAW/Filtered และ log ทุกเฟรม; unit tests 10 ผ่านบน macOS รุ่นใหม่นี้ยังไม่ทดสอบกล้อง ASUS
- ถัดไปทดลอง diagnostic บน ASUS ก่อนเชื่อมแขน ดู docs/mediapipe-team-test.md

- รวมงานทีมจาก origin/main: คงรหัสยืนยันขณะยังพบมือ และ CSV ทุกเฟรม; diagnostic แสดง RAW เพื่อไม่ให้เข้าใจการค้างรหัสว่าโมเดลอ่านถูกเสมอ

## ตรวจรวมอัปเดตหลัก
- fetch แล้ว local main และ origin/main ตรงกันที่ 947bf06 ก่อนปรับเอกสาร ไม่มี remote branch อื่นหรือ open PR
- Windows GitHub Actions ของรุ่นรวม 947bf06 ผ่าน: ติดตั้ง dependencies, unit tests, compile และ CLI help ไม่ได้ทดสอบ webcam
- งานทีมคงรหัสระหว่างเปลี่ยนท่า + งาน RAW/Filtered/ป้ายกำกับ/JSONL รวมแล้ว
- ปรับ README ให้ตรงกับพฤติกรรมคงรหัส ไม่เปลี่ยน logic
