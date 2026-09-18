# ต้นแบบกล้องแปลงท่ามือเป็นรหัส

Windows + กล้อง ASUS TUF A15; ใช้ Python 3.11 แบบ 64-bit

## รายการที่ทีมต้องติดตั้ง

| รายการ | จำเป็นไหม | ใช้ทำอะไร |
|---|---|---|
| Python 3.11.x สำหรับ Windows 64-bit | จำเป็น | รันโปรแกรมและสร้าง environment |
| Git for Windows | จำเป็นสำหรับวิธี clone/pull | ดาวน์โหลดและอัปเดตโค้ด; ถ้าใช้ ZIP ไม่ต้องมี Git |
| Visual Studio Code (VS Code) | แนะนำ | เปิดโฟลเดอร์และแก้โค้ด |
| ส่วนขยาย Python ของ Microsoft ใน VS Code | แนะนำเมื่อใช้ VS Code | ช่วยเลือก Python และรันโค้ด |
| MediaPipe, OpenCV, NumPy | จำเป็น; ติดตั้งผ่านคำสั่งด้านล่าง | จำแนกท่ามือ เปิดกล้อง และจัดการภาพ |
| โมเดล Gesture Recognizer | จำเป็น; ดาวน์โหลดผ่านคำสั่งด้านล่าง | โมเดลสำเร็จรูปสำหรับตรวจท่ามือ |

ใช้ installer จากเว็บไซต์ผู้พัฒนา Python, Git และ Visual Studio Code โดยตรง ตอนติดตั้ง Python ติ๊ก **Add python.exe to PATH** และติดตั้ง Python Launcher เพื่อใช้คำสั่ง `py` เลือก Python 3.11 สำหรับต้นแบบนี้ ไม่ใช้เวอร์ชันอื่นแทนโดยอัตโนมัติ

ยังไม่ต้องติดตั้ง GitHub Desktop, CUDA, Arduino IDE หรือซิม ส่วนผู้วางแผน/แจกงานใช้ GitHub ผ่านเบราว์เซอร์ได้ ไม่ต้องติดตั้งชุดพัฒนาถ้าไม่ได้รันโปรแกรม

## เตรียมบัญชีและดาวน์โหลดโค้ด

- [ ] มีบัญชี GitHub และรับคำเชิญเข้า repository แล้ว (เป็น Private)
- [ ] ติดตั้ง Python และ Git แล้ว ปิดและเปิด PowerShell ใหม่
- [ ] ตรวจคำสั่งต่อไปนี้: ต้องเห็น Python 3.11.x และเวอร์ชัน Git

```powershell
py -3.11 --version
git --version
```

เปิด PowerShell ในตำแหน่งที่จะเก็บโปรเจกต์:

```powershell
git clone https://github.com/Bakani30/camera-arm-control.git
cd camera-arm-control
```

ถ้า Git ขอเข้าสู่ระบบ ให้ใช้บัญชีที่มีสิทธิ์ repository หากไม่ใช้ Git ให้เปิด repository ในเบราว์เซอร์ เลือก **Code > Download ZIP** แตกไฟล์ แล้วเปิด PowerShell ภายในโฟลเดอร์ที่มี `requirements.txt`

## ติดตั้งครั้งแรก

รันทีละบรรทัดจากโฟลเดอร์โปรเจกต์ ไม่ต้อง activate environment และไม่ต้องเปลี่ยน PowerShell execution policy:


```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m camera_gestures.download_model
.\.venv\Scripts\python.exe -m camera_gestures.app
```

ต้องใช้อินเทอร์เน็ตตอนติดตั้งและดาวน์โหลดโมเดล หลังจากนั้นประมวลผลในเครื่อง ไม่ส่งภาพออก ไม่มีการบันทึกภาพหรือวิดีโออัตโนมัติ

สร้าง `.venv` ใหม่ในแต่ละเครื่อง ห้ามคัดลอก `.venv` ของ Mac มาใช้บน Windows ถ้าใช้ VS Code ให้เปิดโฟลเดอร์โปรเจกต์ แล้วเลือก **Python: Select Interpreter** เป็น `.venv\Scripts\python.exe`

## เปิดครั้งถัดไปและอัปเดต

เปิด PowerShell ในโฟลเดอร์โปรเจกต์แล้วรัน:

```powershell
.\.venv\Scripts\python.exe -m camera_gestures.app
```

ถ้ารับโค้ดมาด้วย Git ให้อัปเดตเมื่อทีมแจ้งว่ามีรุ่นใหม่ (ถ้ามีงานแก้ในเครื่อง ให้เก็บงานก่อน):

```powershell
git pull --ff-only
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## ตรวจว่าติดตั้งเสร็จ

- [ ] โปรแกรมเปิดภาพจากกล้องได้
- [ ] แบมือค้างแสดง `01`; กำมือค้างแสดง `10`
- [ ] นำมือออกจากภาพแล้วกลับเป็น `00`
- [ ] กด Q/Esc แล้วโปรแกรมปิดและเปิดใหม่ได้
- [ ] ส่งผลทดสอบและข้อความ error (ถ้ามี) กลับผู้วางแผน พร้อมรุ่นเครื่องและเวอร์ชัน Python

รายการนี้คือเกณฑ์ให้ทีมตรวจเอง ยังไม่ใช่ผลยืนยันจากเครื่อง ASUS

## ใช้งาน
- แบมือ `Open_Palm`: `01`
- กำมือ `Closed_Fist`: `10`
- หากยังตรวจจับเจอมือได้ในกล้อง: ค้างค่าเดิมไว้เสมอ ไม่ตัดเป็น `00` แม้กำลังขยับนิ้วหรือทำท่าอื่น
- ไม่พบมือ (นำมือออกจากกล้องเกิน drop_ms): `00`
- รอท่าใหม่ต่อเนื่อง 250 ms และ score >=0.7 ก่อนเปลี่ยนรหัสเป็น `01`/`10`; ค่าเริ่มทดลอง ปรับได้
- `Q` หรือ `Esc` ปิดโปรแกรม
- แสดงจุดมือ ภาพกลับซ้ายขวาเหมือนกระจก รหัส และเวลาประมวลผลโมเดล (ไม่ใช่ latency ทั้งระบบ)
- ใช้มือเดียวในภาพ โปรแกรมไม่ได้รับรองการเลือกคน/มือเมื่อมีหลายมือ

```powershell
.\.venv\Scripts\python.exe -m camera_gestures.app --camera 1
.\.venv\Scripts\python.exe -m camera_gestures.app --threshold 0.8 --dwell-ms 350 --drop-ms 300
.\.venv\Scripts\python.exe -m camera_gestures.app --changes-only
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

ถ้าเปิดกล้องไม่ได้: ปิด Camera/Teams/Zoom ตรวจ Settings > Privacy & security > Camera และสิทธิ์ desktop apps แล้วลอง camera index อื่น

รุ่น diagnostic เพิ่ม RAW/Filtered และ log ทุกเฟรม ดู [คู่มือส่งผลทีม](mediapipe-team-test.md)

## Log และข้อจำกัด
`logs/` มี CSV บันทึกผลการตรวจจับทุกเฟรมเป็นค่าเริ่มต้น (หรือระบุ `--changes-only` เพื่อบันทึกเฉพาะตอนรหัสเปลี่ยน) รวมเริ่ม/จบ และ JSON ข้อมูล environment/config ต่อ session รหัสเป็นข้อความสองหลัก หากเปิดใน Excel ให้ตั้งคอลัมน์เป็น Text เพื่อรักษาเลข 0 นำหน้า
Timestamp คือเวลารับเฟรมในโปรแกรม ไม่ใช่เวลา exposure ของกล้อง; FPS ใน JSON คือค่าที่ driver รายงาน อาจเป็น 0 หรือไม่ตรงอัตราจริง
คะแนนไม่ใช่ probability ที่ผ่าน calibration ใช้ .frames.jsonl ที่มี hand_present ประกอบการวิเคราะห์ทุกเฟรม

ตราบใดที่กล้องยังตรวจจับเจอมือได้ (hand landmarks detected) output จะค้างค่าเดิมไว้เสมอและไม่ตัดเป็น 00 โดยจะตัดกลับเป็น 00 เฉพาะเมื่อไม่พบมือในกล้องต่อเนื่องเกิน drop_ms (เริ่มต้น 250 ms), ผลโมเดลที่ใช้เกิน 500 ms ถูกถือเป็นไม่พบมือและผ่านช่วง drop เช่นกัน, ช่องว่าง observation >500 ms รีเซ็ตกลับเป็น 00 ทันที อย่างไรก็ตาม synchronous camera read/inference อาจค้างได้ ไม่มี independent watchdog จึงห้ามใช้ต้นแบบนี้สั่งฮาร์ดแวร์โดยตรง `00` ไม่ได้หมายถึงเปิดก้ามหรือตัดไฟ

## ทดลองบน ASUS — ยัง NOT RUN
แสงคงที่ ไม่ย้อนแสง เห็นมือและข้อมือครบ เริ่มทีละมือ:
1. แบมือค้าง 2 วินาที 10 รอบ: ควรได้ 01 หลังช่วงรอ
2. กำมือค้าง 2 วินาที 10 รอบ: ควรได้ 10 หลังช่วงรอ
3. นำมือออก: ได้ 00 หลัง drop_ms; ท่าอื่นขณะยังพบมือจะคงรหัสล่าสุด ให้ดู RAW ประกอบ
4. สลับกำ–แบเร็ว: ไม่ควรปล่อยรหัสที่ยังไม่ผ่านช่วงรอ
5. หมุนมือ/บังนิ้ว: บันทึกการทายผิด ไม่ถือ 00 ทุกกรณีเป็นสิ่งที่โมเดลรับประกัน
6. ปิดหน้าต่างและเปิดใหม่: กล้องต้องถูกคืนและใช้งานได้
บันทึกรหัสเครื่อง แสง ระยะมือ ผลแต่ละรอบ และไฟล์ log ก่อนปรับ threshold

อ้างอิง API/โมเดล: https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer/python
