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
- เพิ่ม P000: กล้อง/ท่ามือ/รหัส 01 10 00 พร้อม CSV บันทึกทุกเฟรม (ค้างค่าเดิมขณะเปลี่ยนท่า + drop timeout)
- unit tests 6 ผ่าน; Windows และกล้อง ASUS NOT RUN
- ถัดไปทดลอง P000 บน ASUS ก่อนเชื่อมแขน ดู docs/camera-gestures.md
