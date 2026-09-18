# วิธีรักษาหลักฐานการทดลอง

ใช้ docs/templates/experiment-record.md หนึ่งชุดต่อ run หรือกลุ่ม run ที่ config เดียวกัน

1. ตั้งคำถามที่ตอบได้และแยก pilot จาก main test
2. ล็อก robot profile, task, camera/calibration, method, environment และ input ก่อนเทียบ
3. เทียบ B0 baseline, B1 baseline+filter, A1 AI ด้วย backend/limits/task เดียวกัน การ replay เทียบการแปลงคำสั่งได้ แต่ไม่แทนการทดสอบ closed-loop ทั้งหมด
4. ฝึก/validation/test แยก session; ถ้าอ้าง unseen robot ต้องกัน robot จริงจากการฝึกและการจูน
5. แยก target tracking error, task success, smoothness, dropout และ latency; ระบุ timestamp จุดเริ่ม/จบ และ clock สำหรับทุก latency
6. ค่าเป้าหมายเทียบ state ซิมไม่ใช่ความถูกต้องของ hand pose; ค่า state ที่อนุมานไม่ใช่ sensor measurement
7. เก็บ failed runs และเกณฑ์ exclude ที่กำหนดก่อน ห้ามเลือกเฉพาะคลิปสำเร็จ
8. รายงานจำนวน trial/session/user, spread และข้อจำกัดตามข้อมูลจริง เกณฑ์ตัวเลขและจำนวน sample ล็อกหลัง pilot ก่อน main test

ยังไม่มีที่เก็บข้อมูลจริง; สร้าง artifacts ตามงานเมื่อเริ่มทดลอง ไม่เก็บวิดีโอ/น้ำหนักโมเดลขนาดใหญ่ใน git โดยปริยาย เก็บ manifest และ checksum ให้ทำซ้ำได้
