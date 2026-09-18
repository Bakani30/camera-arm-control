# การพัฒนาระบบควบคุมแขนกลผ่านกล้อง

ฐานงานร่วมสำหรับทีมและ AI · 2026-09-18

สถานะ: มีต้นแบบกล้องแปลงท่ามือเป็นรหัส ยังไม่เชื่อมแขนและยังไม่ทดสอบกล้อง ASUS จริง

**ทีม Windows เริ่มที่นี่: [รายการติดตั้ง + วิธีติดตั้งทีละขั้น](docs/camera-gestures.md)**

## ทีม Windows: เริ่มต้นแบบกล้อง

ติดตั้ง Git และ Python 3.11 (64-bit) แล้วเปิด PowerShell:

```powershell
git clone https://github.com/Bakani30/camera-arm-control.git
cd camera-arm-control
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m camera_gestures.download_model
.\.venv\Scripts\python.exe -m camera_gestures.app
```

Repository เป็น Private ต้องได้รับสิทธิ์และเข้าสู่ระบบ GitHub ก่อน clone หรือใช้ Code > Download ZIP แล้วแตกไฟล์ เปิด PowerShell ในโฟลเดอร์และเริ่มที่คำสั่งสร้าง venv

แบมือ `01` · กำมือ `10` · ไม่ชัด `00` · กด Q/Esc เพื่อออก

อัปเดตครั้งถัดไปด้วย `git pull` แล้วติดตั้ง requirements ซ้ำ ห้ามนำ `.venv` จาก Mac ไปใช้บน Windows

## เริ่มใช้งาน
1. เปิดโฟลเดอร์นี้เป็น workspace แล้วอ่าน [AGENTS.md](AGENTS.md)
2. อ่าน [สถานะปัจจุบัน](docs/current-state.md) และ [ข้อสรุปโครงการ](docs/research/03-DECISIONS-GLOSSARY.md)
3. เลือกงานจาก [backlog](docs/backlog.md); งานแรกเตรียมไว้ใน [P001](docs/tasks/P001-feasibility.md)
4. อ่าน skill ที่ตรงกับงานจาก AGENTS; ทำงานเฉพาะที่ได้รับมอบหมาย

เอกสารวิจัยฉบับเต็ม: [Research master](docs/research/01-RESEARCH-MASTER.md) · [แผนทดลอง](docs/research/02-EXPERIMENTS-ROADMAP.md) · [สรุปอาจารย์](docs/research/04-ADVISOR-SUMMARY.md)

## โครงสร้าง
- `AGENTS.md`: กติกาและแผนที่เอกสารสำหรับทุก agent
- `.agents/skills/`: วิธีทำงานเฉพาะโครงการ ใช้ SKILL.md ตามมาตรฐาน
- `docs/research/`: ฐานข้อกำหนดวิจัยที่ย้ายมาจาก research-handoff
- `docs/current-state.md`: สิ่งที่ทำแล้วจริงและสิ่งที่ยังไม่รู้
- `docs/backlog.md`, `docs/tasks/`: งานและขอบเขตความรับผิดชอบ
- `docs/workflows/`: วิธีแบ่งงาน ทดลอง และส่งต่อ
- `docs/templates/`: แบบฟอร์มงานและผลทดลอง

เอกสารในโฟลเดอร์นี้เป็นฐานแก้ไขต่อจากนี้; research-handoff เดิมเป็น snapshot ก่อนจัดโปรเจกต์ ไม่ต้องแก้สองชุดพร้อมกัน ไม่มี runtime หรือ agent daemon ถูกติดตั้ง การมี SKILL.md ไม่ได้รับประกันว่าเครื่องมือทุกตัวจะโหลดอัตโนมัติ; หากไม่พบให้ชี้ path โดยตรง

ตัวอย่างเริ่มเซสชั่น: “อ่าน AGENTS.md และ docs/current-state.md แล้วทำ P001 เฉพาะข้อมูลที่ตรวจได้ บันทึกสิ่งที่ยังต้องตรวจบนเครื่องแล็บ”

แนวทางที่ปรับจาก Rally: [ที่มาและขอบเขตการปรับใช้](docs/workflows/rally-adaptation.md)
