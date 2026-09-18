# ส่งทีม: ตรวจ MediaPipe ก่อนฝึกเพิ่ม

## อัปเดตและเปิด
เปิด PowerShell ในโฟลเดอร์โปรเจกต์ (เก็บงานที่แก้ในเครื่องก่อน pull):

```powershell
git pull --ff-only
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m camera_gestures.app
```

หากยังไม่มีโมเดล รัน ` .\.venv\Scripts\python.exe -m camera_gestures.download_model` ก่อนเปิด

## ดูอะไรบนจอ
- RAW: ท่าที่โมเดลอ่านและคะแนนก่อนกรอง ไม่ใช่ probability ที่ผ่าน calibration
- Filtered output: 01/10/00 หลัง threshold และช่วงรอท่าเดิม 250 ms
- Hand/present: พบจุดมือหรือไม่ และซ้าย/ขวาที่โมเดลรายงาน
- Inference: เวลารันโมเดล ไม่ใช่ latency ทั้งระบบ; stale คือใช้เวลาประมวลผลเกิน 500 ms
- จุดมือ: ดูว่าเกาะมือจริงหรือหาย/กระโดด

## ขั้นทดลองร่วมกัน
ใช้กล้อง แสง และตำแหน่งเดิมตลอดหนึ่งรอบ มือเดียวในภาพ กดปุ่มเมื่อหน้าต่างกล้องมี focus:

| ปุ่ม | ป้ายกำกับข้อมูลตั้งแต่เฟรมถัดไป |
|---|---|
| 1 | แบมือ Open_Palm |
| 2 | กำมือ Closed_Fist |
| 0 | ท่าอื่น Other |
| N | ไม่มีมือ No_hand |
| U | ไม่กำกับ unlabeled |

ป้ายเป็นคำตอบที่ผู้ทดลองป้อน ไม่ใช่คำทำนาย และยังอาจผิดได้ อย่าใช้ label โดยไม่ตรวจข้อมูลซ้ำ ก่อนเปลี่ยนท่ากด U เมื่อเข้าท่าและนิ่งแล้วจึงกด 1/2/0/N ทำแต่ละท่าค้าง 3 วินาที 10 รอบต่อคน ท่าอื่นลองชูนิ้วชี้และงอนิ้วบางส่วน เวลาหมุนมือให้แยกเป็นรอบทดสอบใหม่

ส่งไฟล์ชื่อ session เดียวกันทั้งหมดใน logs/:
- .frames.jsonl: ทุกเฟรม มีเวลา จุดมือ normalized x/y/z ผลดิบ คะแนน ป้ายคนกำกับ และรหัสหลังกรอง; ไม่ใช่ระยะจริงในโลก
- .csv: เหตุการณ์รหัสเปลี่ยนเหมือนรุ่นเดิม
- .json: environment/config และ SHA256 โมเดล

ส่งผ่านช่องทางภายในทีม ไม่ commit logs ลง repository โดยอัตโนมัติ ไม่บันทึกภาพ/วิดีโอ การกดป้ายไม่เปลี่ยนคำสั่ง output

## ตีความก่อนแก้
- present=False หรือจุดมือหลุด: ตรวจแสง ขนาดมือในภาพ การบัง และ detector ก่อนฝึกตัวจำแนก
- จุดมือนิ่ง แต่ RAW เปลี่ยนผิดท่า: พิจารณาปรับตัวจำแนก/เก็บข้อมูลฝึก
- RAW ถูก แต่ output สลับกับ 00: ตรวจคะแนนและช่วงรอจาก log ก่อนปรับ threshold/dwell
- inference สูงหรือ stale: ตรวจความเร็วเครื่องแยกจากความถูกต้องโมเดล

รุ่นนี้เป็น diagnostic baseline ไม่ใช่ผลพิสูจน์ว่าแม่นขึ้น และไม่ใช่การรันโค้ดตัวอย่างทางการแบบแยกชุด ยังไม่มีการ benchmark เปรียบเทียบอิสระกับ sample upstream

## ฐานโอเพนซอร์ส
ใช้ MediaPipe Tasks GestureRecognizer ผ่าน package; โค้ดแสดงผล/บันทึกเป็นของโปรเจกต์ ไม่ได้คัดลอก repository อื่นเข้ามา
- ตัวอย่างทางการ Apache-2.0: https://github.com/google-ai-edge/mediapipe-samples
- API: https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer/python
- แนวทางเก็บข้อมูล/ฝึกเพิ่มเติม (ยังไม่ได้รวม): https://github.com/kinivi/hand-gesture-recognition-mediapipe

ยังไม่ติดตั้ง Dex Retargeting หรือ WiLoR ลง environment นี้ ไม่มีการเปลี่ยนวิธี AI retargeting ของโครงงาน
