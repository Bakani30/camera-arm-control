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
| TensorFlow | เฉพาะเมื่อทดลองตัวจำแนก keypoint | โหลดโมเดลท่ามือของ Kazuhito แยกจากตัวหลัก; ติดตั้งใน environment แยก |
| โมเดล keypoint ของ Kazuhito | เฉพาะเมื่อทดลอง keypoint | ดาวน์โหลดด้วยคำสั่งเฉพาะ ตรวจ SHA-256 ก่อนใช้ |

ใช้ installer จากเว็บไซต์ผู้พัฒนา Python, Git และ Visual Studio Code โดยตรง ตอนติดตั้ง Python ติ๊ก **Add python.exe to PATH** และติดตั้ง Python Launcher เพื่อใช้คำสั่ง `py` เลือก Python 3.11 สำหรับต้นแบบนี้ ไม่ใช้เวอร์ชันอื่นแทนโดยอัตโนมัติ

สำหรับโปรแกรมหลักใช้ Python, Git (หรือ ZIP), dependencies จาก `requirements.txt` และโมเดล Gesture Recognizer เท่านั้น

ทดลองตัวจำแนก keypoint เพิ่มเติม ให้สร้าง environment แยก `.venv-keypoint` และติดตั้ง `requirements-keypoint.txt`; TensorFlow ใช้พื้นที่และเวลาติดตั้งเพิ่ม ไม่กระทบ environment หลัก

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

## ทดลองอ่านท่าด้วย keypoint (ไม่บังคับ)

ทำหลังเปิดโปรแกรมหลักได้แล้ว ใช้ environment แยก:

```powershell
py -3.11 -m venv .venv-keypoint
.\.venv-keypoint\Scripts\python.exe -m pip install -r requirements-keypoint.txt
.\.venv-keypoint\Scripts\python.exe -m camera_gestures.download_keypoint
.\.venv-keypoint\Scripts\python.exe -m camera_gestures.app --classifier keypoint
```

หากยังไม่ได้ดาวน์โหลดโมเดล MediaPipe ให้รัน `.\.venv-keypoint\Scripts\python.exe -m camera_gestures.download_model` ด้วย ปุ่ม L/H เลือกมือซ้าย/ขวา, C ตั้งอ้างอิง, R คืนศูนย์, Space พัก กล้องตรวจสองมือแต่ใช้มือด้านที่เลือกเท่านั้น ดู [คู่มือ keypoint, เข้า–ออก และการกลับเข้ากรอบ](keypoint-trial.md)

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
โปรแกรมหลักเปิดด้วย MediaPipe Gesture Recognizer ตามเดิม ไม่มี TensorFlow
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

## แปลงตำแหน่งมือเป็นเมตร (P002)
ปรับเทียบกล้องครั้งเดียวต่อกล้องและความละเอียด ใช้ checkerboard 9×6 จุดมุมใน บนกระดาษหรือจอมือถือ ถือหลายตำแหน่งแล้ว**เอียงให้ชัดราว 30–40° ทุกทิศ** กด Space เก็บภาพจนครบ 15 ภาพ ภาพที่ถือตรงอย่างเดียวทำให้ค่า `f` เพี้ยนได้มาก แม้ `rms` ต่ำ:

```powershell
.\.venv\Scripts\python.exe -m camera_gestures.calibration --width 1280 --height 720 --square-mm 25
```

ผลอยู่ที่ `logs/camera_calibration.json` และจอพิมพ์ `f`, ความไม่แน่นอน และมุมเอียงสูงสุด ถ้าขึ้น `WARNING` ให้เก็บใหม่ รันซ้ำอีกรอบแล้วเทียบค่า `f` ถ้ายังต่างกันเกิน 3% ทั้งที่เอียงพอแล้ว กล้องอาจ autofocus ให้แจ้ง C ก่อนใช้ค่าตายตัว

วัดฝ่ามือจากรอยพับข้อมือถึงโคนนิ้วกลาง เป็นเมตร แล้วเปิดโปรแกรม:

```powershell
.\.venv\Scripts\python.exe -m camera_gestures.app --calibration logs/camera_calibration.json --palm-length-m 0.09
```

- จอแสดง `Metres: X Y Z` และ `frames.jsonl` เก็บ `metric_position_m`, `metric_z_m`, `metric_active` ส่วน JSON ของ session เก็บ `focal_px`, ความละเอียด, `principal_px`, `palm_length_m`
- โปรแกรมปฏิเสธถ้ากล้องให้ความละเอียดไม่ตรงไฟล์ปรับเทียบ
- X/Y เริ่มจาก 0 ที่จุดกดเริ่ม ค้างค่าเมื่อมือหายหรือพัก และไม่กระโดดตอนมือกลับเข้า; `R` กลับไป 0
- ยังไม่มี filter และยังไม่ใช่เป้าหมายแขน งานนี้เป็นฐานของ bubble ใน P006

## คุมจุดเป้าบน mock arm (P006-M0)
ขั้นตอนนี้ไม่ขยับแขนจริง ใช้ไฟล์ปรับเทียบและขนาดฝ่ามือจาก P002:

```powershell
.\.venv\Scripts\python.exe -m camera_gestures.app --mapping relative --calibration logs/camera_calibration.json --palm-length-m 0.11
```

- กด C เริ่มตาม, Space พัก, R เริ่มตามและพาจุดกลับกลางกล่อง
- ขยับมือ 10 ซม. จุดไป 5 ซม. แนวขวาง/ดิ่ง แกนลึกช้ากว่า (10 ซม. ไปราว 2 ซม.)
- สุดระยะมือแล้วเอามือออกจากกรอบ เข้าใหม่ จุดจะตามต่อจากเดิมโดยไม่กระโดด
- กำมือปิดก้าม แบมือเปิดก้าม ก้ามค้างระหว่างพัก และไม่เปลี่ยนในเฟรมแรกที่กลับมาตาม
- ผลอยู่ที่ `logs/<เวลา>.ee_target.jsonl` สรุปตัวเลขด้วยคำสั่งนี้ เอามือออกจากกรอบคั่นแต่ละรอบเพื่อแยกรอบ:

```powershell
.\.venv\Scripts\python.exe -m camera_gestures.mapping_report logs/<เวลา>.ee_target.jsonl --targets
```

วิธีเก็บผลให้ตัวเลขไม่เพี้ยน:
- **มือนิ่ง:** วางมือนิ่งก่อน แล้วกด Space ตามด้วย C เริ่มรอบ และกด Space ก่อนยกมือออก ถ้าไม่ทำ ช่วงมือเข้าและออกจากกรอบจะถูกนับรวมใน `std`
- **ลากไปเป้า:** เปิดโปรแกรมใหม่สำหรับรอบนี้โดยเฉพาะ ไล่เป้าตามเลข 1–5 บน mock arm แล้วใช้ `--targets` เวลาเป้าแรกนับจากกด C

ลำดับการทดสอบตามเกณฑ์ใน [design](superpowers/specs/2026-11-01-m0-relative-mapping-design.md) บันทึกผลด้วย `docs/templates/experiment-record.md` ระบุเครื่อง กล้อง `f` และขนาดฝ่ามือ ถ้าไม่ผ่านให้รายงานก่อนปรับเกณฑ์ ผลรอบนี้เทียบกับ bubble ไม่ได้

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

## วัดระยะเอื้อม ก้ม และบิดข้อมือ
เครื่องมือนี้บันทึก landmark ดิบจากกล้องจริงเพื่อดูว่าแต่ละแกนนิ่งแค่ไหนและกวนกันแค่ไหน ไม่ส่งคำสั่งแขนและไม่ขยับฮาร์ดแวร์ รายละเอียดอยู่ใน `docs/superpowers/specs/2026-11-01-five-axis-hand-control-design.md`

ไม่ต้องวัดมือด้วยไม้บรรทัด โปรแกรมอ่านสัดส่วนฝ่ามือจากท่าแบมือช่วงเริ่มแต่ละชุด เปลี่ยนคนก็แค่เริ่มใหม่ด้วยท่าเดิม ความยาวฝ่ามือใช้ค่าคงที่ 10 ซม. ค่าที่ผิดจะคูณทุกแกนเท่ากัน จึงเหมือนเลือกสเกลต่างไปเล็กน้อยและไม่ทำให้ทิศเพี้ยน ตัวเลข mm ในรายงานจึงเป็นค่าโดยประมาณ

```bash
python -m camera_gestures.axis_bench --calibration logs/camera_calibration_run4.json --note "mac first pass"
python -m camera_gestures.axis_report logs/<stem>.axis_bench.jsonl
```

`logs/` ไม่อยู่ใน git ไฟล์ calibration จึงอยู่เฉพาะ worktree ที่สร้างมันไว้ ถ้าอยู่ที่อื่นให้ระบุ path เต็ม ถ้าไม่ใส่ `--calibration` โปรแกรมจะใช้ f ประมาณและทำป้าย provisional ถ้าต้องการระยะจริงให้เพิ่ม `--palm-length-m` กับ `--palm-width-m` ที่วัดด้วยไม้บรรทัด ถ้า calibration มีคำเตือน รายงานจะพิมพ์ไว้ด้านบน

ใช้มือซ้ายหรือขวาก็ได้ แต่ต้องมีมือเดียวในภาพ รายงานบอกว่าแต่ละชุดใช้มือข้างไหน ถ้าต้องการจำกัดข้างให้ใส่ `--hand Left` หรือ `--hand Right` ค่าที่รายงานใช้ตัดสินไม่ขึ้นกับทิศบวกลบของ roll แต่ขั้นควบคุมจริงยังต้องกลับทิศ roll ของมือซ้าย ถ้ายังไม่เห็นมือ จอจะบอกสาเหตุพร้อมค่าความสว่างของภาพ และ Space จะไม่เริ่มชุดจนกว่าจะเห็นมือ

แต่ละชุดเริ่มด้วยการกด Space แล้วถือท่ากลาง 1 วินาที ท่ากลางคือแบมือตรงหันฝ่ามือเข้ากล้อง นิ้วชี้ขึ้น ระหว่างรอ จอบอกเลขขั้น ระยะมือจากกล้องโดยประมาณ และผลของชุดที่เพิ่งจบว่าใช้ได้หรือไม่ ถ้าขึ้น `NOT VALID` ให้กด R เพื่อทำชุดนั้นซ้ำ กด R ซ้ำจะไม่ย้อนไปชุดก่อนหน้า และกด Q หรือ Esc เพื่อจบ ถ้าเลยชุดที่ต้องการไปแล้วให้เปิดรอบใหม่ด้วย `--only E,F_pitch` ซึ่งได้ไฟล์ log แยก:

| ชุด | ข้อความบนจอ | ทำอะไร |
|---|---|---|
| `A_near` | Hold open palm still, about 30 cm from camera | ถือนิ่ง อ่านระยะจากจอให้ได้ราว 30 ซม. |
| `A_mid` | Hold open palm still, about 50 cm from camera | ถือนิ่ง อ่านระยะจากจอให้ได้ราว 50 ซม. |
| `A_far` | Hold open palm still, about 70 cm from camera | ถือนิ่ง อ่านระยะจากจอให้ได้ราว 70 ซม. |
| `B` | Push hand toward camera and back, slowly, 3 times | ยื่นมือเข้าหากล้องแล้วถอยออก 3 รอบ ระยะเท่าไรก็ได้ รายงานบอกช่วงที่อ่านได้และแสดง `not judged` เสมอ เพราะชุดนี้ไม่มีเกณฑ์ผ่าน |
| `C` | Rest elbow, wrist still. Tip +-30 deg, then as far as tracking holds | วางศอก ตรึงข้อมือ ก้ม-เงย ±30° แล้วจนสุดเท่าที่ยังอ่านได้ |
| `D` | Rest elbow, wrist still. Twist +-45 deg | วางศอก ตรึงข้อมือ บิด ±45° |
| `E` | Rest elbow, wrist still. Fist, open: 10 times | วางศอก มือนิ่ง สลับกำ-แบ 10 รอบ |
| `F_pitch` | FOLD fingers toward camera and back. No twist | ก้มอย่างเดียว ไม่บิด |
| `F_roll` | TURN wrist like a door knob. No folding | บิดอย่างเดียว ไม่ก้ม |

ชุดจะถูกทำป้าย `invalid` พร้อมเหตุผล ถ้ามือหายเกิน 10%, ต่ำกว่า 12 FPS, ไม่ได้ถือท่ากลางให้นิ่งและตรงในวินาทีแรก หรือขยับน้อยเกินไปสำหรับชุด C, D, E และ F ชุดที่ `invalid` หรือไม่จบจะแสดง `not judged` ไม่ใช่ผ่านหรือไม่ผ่าน ให้วัดซ้ำ ส่วนชุดที่ไม่ได้วัดจะอยู่ในบรรทัด `not run`

แถว `z_perspective_fit` คำนวณด้วย z gain ที่หาจากชุด C จึงเป็นแค่ตัวบอกแนวโน้ม โดยเฉพาะในชุด C เอง เพราะใช้ข้อมูลชุดเดียวกับที่ใช้หาค่า เกณฑ์ทั้งหมดเป็นค่าเริ่มต้น และผลจากคนเดียวยังไม่ใช่ค่าสุดท้ายของทีม
