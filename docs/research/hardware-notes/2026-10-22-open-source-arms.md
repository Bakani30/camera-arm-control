# แขนกล Open Source ที่ปริ้น 3D + หาซื้ออะไหล่ + ดัดแปลงเป็นเวอร์ชันของทีมได้

วันที่ตรวจข้อมูล: 2026-10-22 (ข้อมูลใน GitHub ดึงผ่าน GitHub API / README / LICENSE ของ repo เจ้าของโปรเจกต์โดยตรง)

> ข้อมูลที่ไม่มีในแหล่งหลักเขียนว่า "ไม่ระบุ (not stated)" ไม่ได้เดา
> ไฟล์นี้ต่อจาก [08-HARDWARE-OPTIONS](../08-HARDWARE-OPTIONS.md) และ [09-HYBRID-SERVO-BUDGET](../09-HYBRID-SERVO-BUDGET.md) ส่วนที่ 1–6 ด้านล่างค้นแยกโดยไม่ได้อ่าน 08/09 ก่อน ส่วนที่ 0 รวมผลทั้งสองชุดแล้ว

---

## 0. ข้อสรุปตาม requirement ล่าสุด (2026-10-22, โรล C)

### Requirement ที่ยืนยันวันนี้
- งานหลัก: หยิบ–วางของเบา (บล็อก 4–5 ซม. ตาม roadmap)
- **งบต่อแขน 1 ตัว < 5,000 บาท** ค่าชิ้นส่วนทั้งหมด ไม่รวมเครื่องพิมพ์ — **แทนกรอบเดิม 10,000 บาท / มอเตอร์ ~3,000 บาท** ใน 09 และ P005 บันทึกเป็น D24
- Payload, ซอฟต์แวร์, ขนาด bed เครื่องพิมพ์: ยังไม่แน่ใจ
- คงเดิมจาก roadmap: ไม่ยกหนัก, เน้นหมุน/ตอบสนองเร็ว/แม่น, คุมข้อมือ (D04), แขนจริง 1 ตัว ไม่ต้องมี leader, แฝดซิม MuJoCo

### ตัดออกเพราะเกินงบ
AM-ARM200 (US$243), ElRobot (~US$220), Thor (~€350), Koch (follower US$278), PAROL6/AR4/OpenMANIPULATOR-X (หลักพัน USD) — ราคาจากผู้สร้างก่อนค่าส่งไทย ดูส่วน 2 และ 08

### ทางเลือกที่ยังอยู่ในงบ (ราคาร้านไทยจาก [servo-prices](2026-10-02-servo-prices.md) ตรวจ 2026-10-02, ไม่รวมค่าส่ง)

| ทางเลือก | รายการที่มีราคา | รวม (บาท) | เหลือให้ของที่ยังไม่ตีราคา |
|---|---|---:|---:|
| **A. PWM ล้วน 6 แกน + ก้าม** | TD8120MG×2 + MG996R×4 + MG90S×1 (1,735) + Nano (140) + PCA9685 (265) + PSU 5V 10A (325) | **2,465** | ~2,535 |
| **B. ผสม อ่านมุม 2 ข้อ** | SC15×2 + MG996R×4 + MG90S×1 (3,145) + Nano (140) + PCA9685 (265) + Bus adapter (345) + PSU 5V 10A (325) | **4,220** | ~780 |
| C. SO-101 follower ตาม BOM | US$121.94 parts-only (README) | ไม่ได้แปลงค่าเงิน ยังไม่รวมค่าส่ง/ภาษีนำเข้า, ราคา STS3215 ในไทยยังไม่รู้ | เสี่ยงเกินงบ |

ของที่ยังไม่ตีราคาในทุกทางเลือก: ปุ่มหยุดฉุกเฉิน, ฟิวส์/สายไฟ, ลูกปืน/สกรู/ฮอร์น, filament, อะไหล่, ค่าส่ง ทางเลือก B ถ้า SC15 ต้องใช้แรงดันต่างจาก MG996R ต้องมี PSU ตัวที่สอง (ดู servo-prices) ซึ่งอาจทำให้เกินงบ

### ข้อเสนอ
1. **ชุดขับ: เริ่มที่ทางเลือก A (PWM ล้วน, ~2,465 บาท)** เหลืองบพอสำหรับความปลอดภัยและอะไหล่ ข้อเสีย: ไม่มีมุมวัดกลับ ต้องวัดตำแหน่งปลายแขนจากภายนอก (ArUco ตาม roadmap ชั้น C อยู่แล้ว) ทางเลือก B ใช้เมื่อทีมยืนยันว่าต้อง readback และ BOM จริงยังไม่เกิน 5,000
2. **ฐานแบบโครง:** เลือกจากสองตัว
   - **UMIRobot** — ใช้ MG996R อยู่แล้ว ([บทความ BOM](https://arxiv.org/html/2301.06668v2)), มี URDF, งานแก้น้อยสุด แต่ 5 แกน และ CAD เป็น **CC BY-NC-ND 4.0** ([ผู้สร้าง](https://mmmarinho.github.io/UMIRobot/)) แก้ใช้ภายในได้ แต่ **เผยแพร่แบบที่แก้แล้วไม่ได้**
   - **SO-101 ดัดแปลงใส่เซอร์โว PWM** — Apache-2.0 + STEP ([repo](https://github.com/TheRobotStudio/SO-ARM100)) ทำ "เวอร์ชันของทีม" แล้วเผยแพร่ได้ แต่ต้องออกแบบที่ยึดเซอร์โว/ฮอร์นใหม่ และโมเดลซิม/LeRobot เดิมใช้ต่อทันทีไม่ได้ (ดู 09)
   - ถ้าทีมต้องการเผยแพร่แบบของตัวเอง → SO-101 ดัดแปลง; ถ้าใช้ภายในและอยากประกอบเร็ว → UMIRobot
3. **ทั้งสองฐานเป็น 5 แกน** ขัดกับ D04 (คุมข้อมือเต็ม) ทีมต้องตัดสินว่ายอม 5 แกน หรือเพิ่มข้อมือเอง (งานออกแบบ + มอเตอร์เพิ่ม 1 ตัว ~175–480 บาท)
4. EEZYbotARM/MeArm (3 แกน + ก้าม) ถูกที่สุดแต่ไม่มีข้อมือ ใช้เป็นต้นแบบฝึกเท่านั้น

### ต้องตอบก่อนปิด P005
- บล็อกจริงหนักกี่กรัม → ใช้คำนวณแรงบิดไหล่/ข้อศอก
- ยอม 5 แกนหรือไม่ (D04)
- จะเผยแพร่แบบที่แก้หรือไม่ (ตัดสิน UMIRobot vs SO-101)
- ขนาด bed เครื่องพิมพ์ (SO-101 ต้อง ≥ 220×220 mm)
- งบ 5,000 รวมค่าส่งและปุ่มหยุดฉุกเฉินด้วยหรือไม่

---

## 1. สรุปและข้อเสนอแนะ

1. **License สำคัญไม่แพ้ราคา** ถ้าทีมจะ "ออกแบบเป็นเวอร์ชันของเราเอง" และอาจขายหรือใช้เชิงพาณิชย์:
   - **ปลอดภัยที่สุด (อนุญาตแก้ไข + ใช้เชิงพาณิชย์):** SO-ARM100/101 (Apache-2.0), Koch v1.1 (Apache-2.0), BCN3D Moveo (MIT), Thor (CC-BY-SA-4.0, ต้องเผยแพร่งานดัดแปลงด้วย license เดียวกัน), PAROL6 (GPL-3.0, copyleft)
   - **มีข้อจำกัดหนัก:** **Annin AR4** license เป็น "Non-Commercial", ห้าม redistribute ไฟล์ออกแบบ และห้าม rebrand ([LICENSE.txt](https://github.com/Annin-Robotics/ar4-hmi/blob/main/LICENSE.txt)) ถ้าจะทำเวอร์ชันของทีมแล้วแจกจ่ายต่อ ไม่เหมาะ
   - **EEZYbotARM MK2:** ตัวต้นฉบับบน Thingiverse เป็น CC BY-NC (ไม่ใช่เชิงพาณิชย์) อ้างจากผลค้นหาของ Thingiverse ไม่ได้เปิดหน้าไฟล์ตรง ๆ จึงถือเป็น "ยังไม่ยืนยันเต็ม"
2. **งบน้อย / เน้นเริ่มเร็ว / เน้น AI-learning (LeRobot):** **SO-ARM101** ดีที่สุดในชุดนี้ ชิ้นส่วนอะไหล่รวมราว **$122 (follower เดียว)** ตาม BOM ใน repo (ไม่รวมชิ้นส่วนปริ้น), มีไฟล์ STEP, repo active (commit ล่าสุด 2026-10-06), รองรับ LeRobot โดยตรง ข้อเสีย: payload/reach ไม่ระบุใน repo และเป็น hobby-grade servo
3. **ต้องการแขน 6 DOF ปริ้นเองเกือบทั้งตัว ใช้ stepper + ROS2:** **Thor** (hardware ราว €350, payload 750 g, source เป็น FreeCAD + STEP) แต่ repo commit ล่าสุด 2025-05-09 และ release ล่าสุด 2021 (ความเคลื่อนไหวช้าลง)
4. **ต้องการสไตล์แขน industrial ที่ทำงานหนักกว่า:** AR4 (spec ดีที่สุด แต่ license ห้ามเชิงพาณิชย์ และราคา kit เริ่ม $1,189 + มอเตอร์ $699) หรือ PAROL6 (GPL-3.0, partial kit €1,188.81) ทั้งคู่แพงกว่า SO-101 หลายเท่า
5. **ไม่แนะนำเป็นฐานของงานใหม่:** BCN3D Moveo (commit ล่าสุด 2016, CAD เป็น SolidWorks) ใช้ศึกษาได้ แต่ไม่ได้ดูแลต่อ

คำแนะนำเบื้องต้น (ขึ้นกับคำตอบข้อ 7 ท้ายเอกสาร): ถ้างานเป็นงานเบา (หยิบของน้ำหนักไม่เกินไม่กี่ร้อยกรัม, ทำ teleoperation / imitation learning) เริ่มที่ **SO-ARM101**; ถ้าต้อง 6 DOF แบบ industrial-style ราคาต่ำ เริ่มที่ **Thor**

---

## 2. ตารางเปรียบเทียบ

ค่าทั้งหมดมาจากแหล่งหลักที่ลิงก์ไว้ในหัวข้อรายตัว (หัวข้อ 3) "not stated" = แหล่งหลักไม่ระบุ

| | SO-ARM101 (SO-100/101) | Thor | PAROL6 | Annin AR4 (MK5) | Koch v1.1 | BCN3D Moveo | OpenMANIPULATOR-X | EEZYbotARM MK2 |
|---|---|---|---|---|---|---|---|---|
| License | Apache-2.0 | CC-BY-SA-4.0 | GPL-3.0 | Non-Commercial custom (ห้าม redistribute/rebrand) | Apache-2.0 | MIT | ไม่ระบุ license ของ hardware ในหน้า e-Manual | CC BY-NC (ตามผลค้น Thingiverse, ยังไม่ยืนยันตรง) |
| แก้ไข + เชิงพาณิชย์ | ได้ | ได้ (share-alike) | ได้ (copyleft) | ห้ามเชิงพาณิชย์ | ได้ | ได้ | ไม่ชัด | ห้ามเชิงพาณิชย์ |
| DOF | 6 มอเตอร์ในแขน follower (ตาม LeRobot docs) | 6 | 6 | 6 | not stated (ใช้ 6 มอเตอร์) | not stated | 5 (4 + gripper) | not stated |
| Payload | not stated | 750 g (รวม end effector) | not stated | 4.15 lb (~1.88 kg) | not stated | not stated | 500 g | not stated |
| Reach | not stated | สูงสุด 625 mm (ความสูงเมื่อเหยียด, ไม่ใช่ reach) | not stated | 24.75 in (~629 mm) | not stated | not stated | 380 mm | not stated |
| Repeatability | not stated | not stated | not stated | 0.25 mm | not stated | not stated | < 0.2 mm | not stated |
| Actuator | Feetech STS3215 serial bus servo | Stepper NEMA + ปริ้นเฟือง/สายพาน GT2 (+ MG995 1 ตัว) | Stepper NEMA 17 + planetary gearbox | Stepper + ชิ้นโครงอะลูมิเนียม machined | Dynamixel XL330/XL430 | Stepper (ดู BOM PDF) | Dynamixel XM430-W350-T | hobby servo (ไม่ได้ยืนยันจากแหล่งหลัก) |
| ชิ้นส่วนปริ้น | ปริ้นเกือบทั้งตัว ไฟล์ STL รวมเป็นไฟล์เดียวต่อแขน | 49 ไฟล์ STL (ชิ้นหลักปริ้นทั้งหมด) | ปริ้นเป็นหลัก มีโฟลเดอร์ Print table | ปริ้นแค่ฝาครอบ/spacer (โครงเป็นอะลูมิเนียม) | ปริ้น (hardware folder) | ปริ้นโครงสร้าง | ปริ้นบางส่วน (มี STL ให้) | ปริ้นทั้งตัว |
| Bed ขั้นต่ำ | 220x220 mm (ไฟล์ Ender) หรือ 205x250 mm (ไฟล์ Prusa) | not stated (มีไฟล์แยกสำหรับชิ้นใหญ่ใน mods/) | มีโฟลเดอร์ SMALL_PRINT_BED, ขนาดตัวเลข not stated | not stated | not stated | not stated | not stated | not stated |
| CAD ต้นทาง | STEP (+ STL) | FreeCAD (.FCStd ใน freecad-src) + STEP | STL ใน repo; STEP ขายแยก €27.37 | ไม่พบ STEP/CAD ใน GitHub (ดาวน์โหลดผ่านเว็บ, ห้าม redistribute) | SolidWorks + STEP + STL | SolidWorks (.SLDPRT/.SLDASM) + STL | STL (ลิงก์ดาวน์โหลดของ ROBOTIS) | Onshape (ตามผลค้น) |
| ราคา BOM (ระบุสกุลเงิน) | $121.94 follower เดียว / $229.88 สองแขน (ตาม README, ไม่รวมชิ้นปริ้น) | "ต่ำกว่า €350" (ไม่รวมเครื่องพิมพ์) | BOM ใน repo ไม่มีราคา; partial kit €1,188.81 | Combo kit เริ่ม $1,189 + มอเตอร์ $699 | follower $278, leader $199 (USD) | BOM PDF ไม่ได้ดึงราคา | $1,416.60-$1,629.09 USD (ชุดสำเร็จรูป ไม่รวม power/controller) | not stated |
| ที่ซื้อ | Seeed, WowRobo, RobotEd, Robonine ฯลฯ + Alibaba/Amazon (ดู README) | AliExpress, StepperOnline, PCBWay | Source Robotics, StepperOnline ฯลฯ | Annin Robotics + StepperOnline | ROBOTIS, Amazon | ดู BOM PDF | ROBOTIS | not stated |
| เอกสารสร้าง | มี (README + LeRobot docs) | มี (thor.angel-lm.com) | มี (Building instructions + docs) | มี (Build manual + course) | มี (README + วิดีโอ) | มี (User manual) | มี (ROBOTIS e-Manual, กำลังย้าย) | not stated |
| Commit ล่าสุด | 2026-10-06 | 2025-05-09 | 2026-10-02 | ar4-hmi: 2025-11-20 (ROS driver: 2026-06-09) | 2024-09-17 | 2016-10-03 | 2026-10-19 (ROS 2 packages) | n/a |
| Software | LeRobot (Hugging Face) | G-code (GRBL/RRF), ROS2 + MoveIt2 | Commander, Python API, ROS2/MoveIt | Python HMI, ROS 2 driver | not stated ใน README (ไม่ได้ตรวจ LeRobot support) | Arduino firmware; ROS ชุมชน | ROS 2, Dynamixel SDK, Arduino, LeRobot | not stated |

---

## 3. บันทึกรายตัว

### 3.1 SO-ARM100 / SO-ARM101 (TheRobotStudio + Hugging Face LeRobot)
- Repo: https://github.com/TheRobotStudio/SO-ARM100 (7,836 stars, ไม่ archived)
- License: Apache-2.0 https://github.com/TheRobotStudio/SO-ARM100/blob/main/LICENSE
- Commit ล่าสุด 2026-10-06, open issues 88 (ผ่าน GitHub API) แสดงว่ายังดูแลต่อ SO-100 ถูกระบุว่า deprecated, ให้ใช้ SO-101 https://github.com/TheRobotStudio/SO-ARM100#readme
- Actuator: follower ใช้ Feetech STS3215 6 ตัว (เกียร์ 1/345), leader ใช้เกียร์ 3 แบบ https://huggingface.co/docs/lerobot/so101 ; รุ่น 7.4V stall torque 16.5 kg.cm, รุ่น 12V 30 kg.cm (README ข้างบน)
- Payload / reach / repeatability: not stated ใน README
- ชิ้นส่วนปริ้น: README ให้ไฟล์ STL ที่จัดวางแล้วเป็น "ไฟล์เดียวต่อแขน" สำหรับ bed 220x220 mm (Ender) หรือ 205x250 mm (Prusa/UP); แนะนำ PLA+ nozzle 0.4 mm ชั้น 0.2 mm infill 15% https://github.com/TheRobotStudio/SO-ARM100#printing-the-parts
- CAD: โฟลเดอร์ `STEP/SO101` (เช่น `SO101 Assembly.step`) https://github.com/TheRobotStudio/SO-ARM100/tree/main/STEP/SO101 จึงแก้ไขได้ใน CAD ทั่วไป
- BOM (ตาม README, USD, ค่าที่ README แสดงในวันที่ตรวจ ไม่มีวันที่กำกับ): ชุด follower เดียว $121.94 / €124.3 ; ชุดสองแขน (follower+leader) $229.88 / €226.3 ราคานี้ **เป็น parts-only ไม่รวมชิ้นส่วนปริ้น** และเป็นราคาโดยประมาณของผู้จัดทำ README ซึ่งบอกว่า "ราคาแตกต่างตามพื้นที่" https://github.com/TheRobotStudio/SO-ARM100#sourcing-parts
- Vendor kit (ต่างจาก parts-only): README ลิสต์ Seeed, WowRobo, RobotEd, Robonine, ForgeMotion Labs, Autodiscovery ฯลฯ ราคาจากผลค้นหาหน้า Seeed (ยังไม่ได้เปิดหน้าตรงเพราะบล็อกการดึง และราคาต่างกันตามหน้า ให้เช็กตอนซื้อ): SO-ARM101 Pro servo motor kit ราว $277.99 (หน้าอื่นเห็น $249.90), รุ่น assembled $299.00, ชิ้นส่วนปริ้นแยกราว $29.90-$30.99 https://www.seeedstudio.com/SO-101-Low-Cost-AI-Arm-Kit-Pro-p-6427.html . หน้า SO-ARM100 รุ่นเก่าของ Seeed ระบุว่า Discontinued https://www.seeedstudio.com/SO-ARM100-Low-Cost-AI-Arm-Kit.html
- Software: LeRobot (repo https://github.com/huggingface/lerobot, Apache-2.0, 28,383 stars, commit ล่าสุด 2026-10-21) มีขั้นตอน setup/calibrate/teleop ใน https://huggingface.co/docs/lerobot/so101 ; ROS/ROS2 ตรง ๆ: not stated ใน README (มีโฟลเดอร์ Simulation ใน repo)
- ข้อควรระวัง: ไม่เหมาะกับงานที่ต้องการแรง/ความแม่นยำสูง (ไม่มีตัวเลขยืนยันจากแหล่งหลัก); บอร์ด/มอเตอร์เป็น serial bus servo ไม่ใช่ industrial

### 3.2 Thor (AngelLM)
- Repo: https://github.com/AngelLM/Thor (1,624 stars)
- License: CC-BY-SA-4.0 ใช้ได้รวมเชิงพาณิชย์ แต่ต้องให้เครดิตและเผยแพร่งานดัดแปลงด้วย license เดียวกัน https://thor.angel-lm.com/faq/
- Spec จาก README: 6 DOF, สูงเมื่อเหยียด 625 mm, payload สูงสุด 750 g (รวม end effector), stepper + เฟืองปริ้น + สายพาน GT2, ซอฟต์แวร์ FreeCAD/KiCAD/GRBL/RRF/ROS2 https://github.com/AngelLM/Thor#readme (reach/repeatability: not stated)
- ชิ้นส่วนปริ้น: 49 ไฟล์ STL และ 49 ไฟล์ STEP ใน repo; ตาราง quantity + วัสดุ (PLA เป็นหลัก ชิ้นใกล้มอเตอร์ใช้ ABS), ใช้ฟิลาเมนต์ PLA/PETG 3-4 kg https://thor.angel-lm.com/documentation/bom/ ; คำแนะนำปริ้น layer 0.3 mm, ชิ้นใหญ่ (Articulation 2) ถ้า bed ไม่พอมีเวอร์ชันแยกชิ้นในโฟลเดอร์ `mods` https://thor.angel-lm.com/documentation/3d-printing-guide/ ; bed ขั้นต่ำเป็นตัวเลข: not stated
- CAD: โฟลเดอร์ `freecad-src` (FreeCAD) และ `step` https://github.com/AngelLM/Thor/tree/main
- BOM: "Hardware cost below 350€" (README), FAQ: ราว 350€ ไม่รวมเครื่องพิมพ์ ราคานี้เป็น parts-only ไม่มีวันที่กำกับ https://thor.angel-lm.com/faq/ ; ลิงก์ซื้อส่วนใหญ่เป็น AliExpress/StepperOnline และ PCB จาก PCBWay https://thor.angel-lm.com/documentation/bom/
- ความเคลื่อนไหว: commit ล่าสุด 2025-05-09, release ล่าสุด v2.1.1 วันที่ 2021-09-23 (GitHub API), open issues 5 ถือว่า "พอมีการดูแลแต่ช้า"
- Software: G-code (GRBL/RRF) ผ่านโปรแกรม Asgard, ROS2 + MoveIt2 ที่ repo แยก https://github.com/AngelLM/Thor-ROS
- ข้อควรระวัง: เฟืองปริ้น 3D ย่อมมี backlash/สึกหรอ (นี่เป็นข้อสังเกตเชิงวิศวกรรมทั่วไป ไม่ใช่ตัวเลขจาก repo)

### 3.3 PAROL6 (Source Robotics)
- Repo: https://github.com/Source-Robotics/PAROL6-Desktop-robot-arm (เดิม PCrnjak/...; 3,393 stars), commit ล่าสุด 2026-10-02
- License: GPL-3.0 https://github.com/Source-Robotics/PAROL6-Desktop-robot-arm/blob/main/LICENSE ; README ย้ำว่า "Control software, GUI, and robots STL files are open-source" (STEP ไม่อยู่ใน repo)
- DOF: 6 https://source-robotics.github.io/PAROL-docs/ ; payload/reach/repeatability: not stated ในหน้า docs ที่ตรวจและหน้าร้าน (เจ้าของโปรเจกต์อาจมีหน้า spec แยก ไม่พบ)
- Actuator: NEMA 17 stepper 6 ตัว + planetary gearbox (EG series) + สายพาน HTD3 https://github.com/Source-Robotics/PAROL6-Desktop-robot-arm/blob/main/BOM/BOM.md
- CAD: repo มี STL อย่างเดียว; **ไฟล์ STEP ขายที่ €27.37** https://source-robotics.com/products/parol6-step-files (ผลดึงจากหน้าแรกของร้าน, สกุลเงิน EUR)
- ราคา: BOM ใน repo เป็นลิงก์ซื้อ ไม่มีราคา ; ราคา vendor partial kit €1,188.81, screw kit €58,31, control board เริ่ม €236,81 (หน้าแรก source-robotics.com, ตามที่ดึงได้ ณ วันที่ตรวจ) ถือเป็น kit ไม่ใช่ parts-only
- ซอฟต์แวร์: Commander GUI, Python API, ROS2/MoveIt (ลิงก์ใน README)
- ข้อควรระวัง: README มีคำเตือนเรื่องแรงดันไฟฟ้าอันตราย (ไฟล์ SAFETY_WARNING_AND_DISCLAIMER.md)
- Thailand: ในตัวเลือกประเทศของร้าน ไม่เห็นประเทศไทย ยังไม่ยืนยันการจัดส่ง

### 3.4 Annin Robotics AR4 (MK5)
- เว็บเจ้าของ: https://www.anninrobotics.com/ ; Spec บนหน้าแรก: 6 DOF, reach 24.75 in, payload 4.15 lb, repeatability 0.25 mm, มวล 27 lb, กำลัง 198 W
- **License:** "Open Source Non-Commercial License Agreement" ห้ามใช้เชิงพาณิชย์, ห้าม redistribute ไฟล์ออกแบบ, ห้าม rebrand https://github.com/Annin-Robotics/ar4-hmi/blob/main/LICENSE.txt (LICENSE นี้อยู่ใน repo `ar4-hmi`; ส่วน `ar4_ros_driver` เป็น MIT https://github.com/Annin-Robotics/ar4_ros_driver) สรุป: ไม่เหมาะกับ "ทำเวอร์ชันของทีมเอง" ถ้ามีแผนแจกจ่ายหรือขาย
- โครงสร้างหลักเป็นอะลูมิเนียม machined 26 ชิ้น ปริ้นเฉพาะฝาครอบ (หน้า shop) ดังนั้นไม่ใช่แขนที่ปริ้นเองทั้งตัว
- ราคา (USD, vendor kit, หน้า shop https://www.anninrobotics.com/shop): Combo kit เริ่ม $1,189, มอเตอร์/ไดรเวอร์/PSU จาก StepperOnline $699, servo gripper kit $74.50 ; รวมขั้นต่ำประมาณ $1,888 (ผลรวมของเราเอง ไม่ใช่ตัวเลขของผู้ขาย)
- CAD: ดาวน์โหลดผ่านหน้า Downloads (มี STL ของ MK5, build manual, DH parameters) ไม่พบไฟล์ STEP/CAD ต้นทางใน GitHub https://www.anninrobotics.com/downloads
- Software: Python HMI, Teensy/Arduino sketch, ROS 2 (repo ar4_ros_driver commit ล่าสุด 2026-06-09)
- Thailand: ไม่ยืนยัน (หน้า FAQ มีหัวข้อ International Shipping แต่เนื้อหาเป็น accordion ดึงไม่ได้)

### 3.5 Koch v1.1 (jess-moss) และ Low-Cost Robot ต้นฉบับ (Alexander Koch)
- Repo: https://github.com/jess-moss/koch-v1-1 (735 stars), Apache-2.0, commit ล่าสุด 2024-09-17 (หยุดนิ่งแล้ว); ต้นฉบับ https://github.com/AlexanderKoch-Koch/low_cost_robot (MIT, commit ล่าสุด 2024-09-21)
- Actuator: Dynamixel XL330/XL430 ; CAD: มีโฟลเดอร์ SolidWorks, STEP, STL ใน `hardware/follower` และ `hardware/leader` https://github.com/jess-moss/koch-v1-1/tree/main/hardware
- BOM (USD, README): leader $199, follower $278 (รวมเป็นชุด teleop ราว $477 ตามผลรวมของเรา) ; README ไม่มีวันที่ราคา ; payload/reach/DOF: not stated ; ขนาด bed: not stated (แนะนำเครื่องระดับ Ender 3/Prusa Mini+/Bambu P1)
- ความเกี่ยวข้อง: SO-101 พัฒนาต่อยอดแนวคิด leader-follower เดียวกัน และมี community/LeRobot ใหญ่กว่า จึงมักเลือก SO-101 แทนในงานใหม่ (นี่เป็นความเห็นเรา ไม่ใช่ข้อความในแหล่งหลัก)

### 3.6 BCN3D Moveo
- Repo: https://github.com/BCN3D/BCN3D-Moveo, MIT (Copyright 2016 BCN3D Technologies) https://github.com/BCN3D/BCN3D-Moveo/blob/master/LICENSE
- **Commit ล่าสุด 2016-10-03 ถือว่าไม่ได้ดูแลต่อ** (open issues 47)
- CAD เป็น SolidWorks (.SLDPRT/.SLDASM), มี STL, BOM เป็น PDF (`BCN3D Moveo BOM.pdf`), firmware, user manual ทั้งหมดอยู่ใน repo ; payload/reach/DOF/ราคา: not stated ใน README ; BCN3D ระบุว่าไม่ขายเชิงพาณิชย์ แต่เปิดไฟล์ให้ดัดแปลงได้
- ใช้เป็นแหล่งศึกษาได้ แต่ ROS มาจาก repo ชุมชน (เช่น jesseweisberg/moveo_ros) ซึ่งไม่ใช่แหล่งหลักของโปรเจกต์

### 3.7 ROBOTIS OpenMANIPULATOR-X (และ ROBOTIS OpenMANIPULATOR ROS 2)
- Spec จาก e-Manual: 5 DOF (4 + gripper), payload 500 g, reach 380 mm, repeatability < 0.2 mm, Dynamixel XM430-W350-T, น้ำหนัก 0.70 kg https://emanual.robotis.com/docs/en/platform/openmanipulator_x/specification/
- หน้า overview ระบุเป็น open-source hardware มีไฟล์ STL ให้ปริ้นส่วนใหญ่ แต่ **ไม่ระบุ license ของ hardware** และ e-Manual กำลังย้ายไปเว็บใหม่ (ลิงก์อาจหาย) https://emanual.robotis.com/docs/en/platform/openmanipulator_x/overview/
- Repo ROS 2: https://github.com/ROBOTIS-GIT/open_manipulator Apache-2.0, commit ล่าสุด 2026-10-19 (ซอฟต์แวร์ active; README กล่าวถึง LeRobot/Physical AI)
- ราคาชุดสำเร็จรูป (vendor, ไม่ใช่ parts-only): ผลค้นหาแสดง $1,629.09 บน robotis.us (สถานะ sold out) และ $1,416.60 บน en.robotis.com ; ไม่รวม power supply และ controller https://www.robotis.us/openmanipulator-x-rm-x52-tnm/ , https://en.robotis.com/shop_en/item.php?it_id=905-0024-000 (ยังไม่ได้เปิดหน้าตรง)
- เหมาะกับงานที่ต้องการ ROS-first และ hardware เสถียร แต่แพงกว่า SO-101 หลายเท่า และแก้ไข hardware ต้องสร้างจาก STL

### 3.8 EEZYbotARM MK2
- ต้นฉบับ: Thingiverse https://www.thingiverse.com/thing:1454048/files (โดย daGHIZmo) ผลค้นหาระบุ license CC BY-NC และมี source บน Onshape ; ไม่ได้เปิดหน้าตรงเพื่อยืนยันและไม่พบเว็บ eezyrobots.it ในผลค้น
- DOF/payload/reach/ราคา: not stated (ไม่ได้ตรวจจากแหล่งหลัก) ; ไม่มี repo GitHub ของเจ้าของที่ยืนยันได้ ; ชุมชนมี repo ซอฟต์แวร์อิสระ ไม่ใช่แหล่งหลัก
- เหมาะกับการเรียนรู้/งานเบามาก ข้อจำกัด license NC ทำให้ไม่เหมาะกับการต่อยอดเชิงพาณิชย์

### 3.9 ตัวที่ตรวจแล้วไม่ได้นำเข้า / ไม่พบแหล่งหลัก
- **uArm:** ไม่ได้ตรวจ ไม่ยืนยันว่าเป็น open-source เต็มรูปแบบ (ไม่ได้ค้นเพิ่ม)
- **Poppy Ergo Jr:** repo `poppy-project/poppy-ergo-jr` พบ commit ล่าสุด 2022-05-30 และไม่มี license ที่ GitHub API ตรวจพบ จึงไม่นำเข้า
- **SO-100 (รุ่นเก่า):** README ระบุ deprecated

---

## 4. การจัดซื้อและการจัดส่งสำหรับผู้ซื้อในประเทศไทย

สถานะรวม: **ยังยืนยันจากแหล่งหลักได้เพียงบางส่วน** หน้าเว็บของ Seeed และ StepperOnline ตอบ HTTP 403 เมื่อดึงตรง จึงอาศัยข้อความที่ผลค้นหาสรุปจากหน้าทางการ ควรเช็กตอน checkout

| ผู้ขาย | สถานะ Thailand | แหล่ง |
|---|---|---|
| Seeed Studio (SO-ARM101 kit) | ส่งจากคลังจีนได้ น่าจะรวมไทย: โปรโมชันปี 2025 ลิสต์ Thailand ใน YanWen Express (7-15 วัน, เงื่อนไข <500 USD และ <30 kg); คลัง DE ส่งเฉพาะ EU, คลัง US ส่งเฉพาะ US ; ข้อมูลล่าสุดปี 2025 จึงระดับ "ยืนยันบางส่วน" | https://www.seeedstudio.com/blog/2025/06/05/free-shipping-is-back-faster-global-delivery-now-available/ , https://www.seeedstudio.com/us_warehouse , https://www.seeedstudio.com/eu_warehouse |
| StepperOnline (มอเตอร์ Thor/PAROL6/AR4) | ไทยอยู่ในรายชื่อประเทศ "Tax-Inclusive" (เก็บภาษีนำเข้าตอน checkout เริ่ม 2026-01-15) ; ลูกค้านอก US/UK/EU/AU/RU เลือกคลังจีน ; ขนส่ง DHL/FedEx/UPS 3-10 วันทำการ | https://www.omc-stepperonline.com/import-tax-vat , https://www.omc-stepperonline.com/shipping-policy |
| ROBOTIS (Dynamixel / OM-X / Koch) | ไม่พบตัวแทนในไทยจากผลค้น และไม่พบข้อความเรื่องการส่งไทย: unverified | https://www.robotis.us/ |
| Source Robotics (PAROL6) | ไม่เห็นไทยในตัวเลือกประเทศ ; shipping policy ไม่ได้ดึงเนื้อหา: unverified | https://source-robotics.com |
| Annin Robotics (AR4) | unverified (FAQ มีหัวข้อ International Shipping แต่ดึงเนื้อหาไม่ได้) | https://www.anninrobotics.com/faq |
| WowRobo / RobotEd / Robonine / ForgeMotion | unverified (หน้าร้านเข้าไม่ได้หรือไม่ได้ตรวจ) | https://github.com/TheRobotStudio/SO-ARM100#kits |

หมายเหตุ: README ของ SO-ARM100 ระบุว่ามีลิงก์ซื้อเฉพาะ US, EU, CN, JP ยังไม่มีลิงก์เฉพาะประเทศไทย และรับ PR เพิ่มประเทศได้ ส่วนภาษีนำเข้า/ศุลกากรไทยไม่ได้ตรวจ

---

## 5. คำถามที่ทีมต้องตอบเพื่อเลือกตัวที่ "เหมาะกับโปรเจกต์"

1. **Payload:** ต้องยกน้ำหนักสูงสุดเท่าไหร่ (รวม gripper/เครื่องมือ) ถ้าเกิน ~500 g ตัดกลุ่ม servo เล็ก (SO-101, Koch) ออกก่อน ถ้าเกิน ~1 kg ต้องดู AR4/PAROL6 และต้องหาตัวเลข payload จริงที่ยืนยันได้
2. **Reach และพื้นที่ทำงาน:** ต้องเอื้อมไกลกี่ mm และ workspace เป็นโต๊ะเล็กหรือหน้างานจริง
3. **ความแม่นยำ / repeatability:** ต้องการระดับ mm หรือ sub-mm (AR4 ระบุ 0.25 mm, OM-X < 0.2 mm ; ตัวอื่นไม่ระบุ)
4. **DOF และ use case:** ต้องการ 5 หรือ 6 DOF, ทำ pick-and-place, teleoperation / imitation learning (LeRobot) หรือ motion planning แบบ industrial
5. **ROS / ซอฟต์แวร์:** ทีมใช้ ROS 2/MoveIt, LeRobot (Python) หรือ Arduino/G-code เป็นหลัก ซึ่งกำหนดว่าควรเลือกมอเตอร์แบบ serial-bus servo, Dynamixel หรือ stepper
6. **งบและจำนวนตัว:** งบรวมเท่าไหร่ และต้องการกี่ตัว (SO-101 ต้องมีทั้ง leader+follower ถ้าทำ teleop ราว $230 ตาม BOM; Thor ราว €350; AR4/PAROL6/OM-X เกินหลักพัน)
7. **Licensing:** จะขาย แจกจ่าย หรือเปิดเผยการออกแบบของทีมหรือไม่ ถ้าจะปิดซอร์สหรือขาย ให้ตัด Thor (share-alike), PAROL6 (GPL) และ AR4/EEZYbotARM (non-commercial) ออกหรือขอคำปรึกษากฎหมายก่อน เหลือ SO-101/Koch/Moveo (Apache/MIT) ที่ยืดหยุ่นที่สุด
8. **CAD ที่ทีมใช้:** ทีมใช้ Fusion/SolidWorks/FreeCAD อะไร (SO-101 และ Koch มี STEP ; Thor มี FreeCAD+STEP ; Moveo เป็น SolidWorks ; PAROL6 ต้องซื้อ STEP ; AR4 ไม่พบ STEP)
9. **เครื่องพิมพ์:** bed ขนาดเท่าไหร่ และพิมพ์วัสดุอะไรได้ (SO-101 ต้อง bed ≥ 205x250 mm หรือ 220x220 mm)
10. **ช่องทางซื้อในไทย:** ยอมสั่งจากต่างประเทศ (จีน/US/EU) และรับค่าส่ง/ภาษีนำเข้าได้ไหม หรือต้องการซื้อในไทย ซึ่งยังไม่ได้ตรวจร้านในประเทศ

---

## 6. สิ่งที่ยังไม่ได้ตรวจ / ข้อจำกัดของงานนี้

- ไม่ได้ลงมือทดสอบสร้างหรือวัดค่าจริง (payload, reach, repeatability) ตัวเลขทั้งหมดมาจากเจ้าของโปรเจกต์
- ราคา vendor (Seeed, ROBOTIS) บางส่วนได้จากสรุปผลค้นหา ไม่ได้เปิดหน้าตรง ราคาเปลี่ยนได้ ต้องเช็กตอนซื้อ
- ราคา BOM ใน README ของ SO-101/Koch ไม่ระบุวันที่ ใช้ตามที่เห็น ณ วันที่ตรวจ 2026-10-22
- ไม่ได้ตรวจ uArm, Poppy Ergo Jr เชิงลึก, และไม่ได้ตรวจร้านค้าในประเทศไทย
- ขนาด bed และจำนวนชิ้นปริ้นที่แน่นอนของ PAROL6, AR4, Koch, Moveo ไม่ได้ดึงมา (not stated ในตาราง)
