# BOM แขนที่ทีมออกแบบ CAD เอง: ตีราคา actuator + ฮาร์ดแวร์ งบ < 5,000 บาท (อยากได้ ≤ 4,000)

ตรวจราคา 2026-10-22 · อ่านหน้าร้าน/หน้าผู้ผลิตแบบ read-only เท่านั้น ไม่ได้ซื้อ ไม่ได้หยิบลงตะกร้า ไม่ได้ login และไม่ได้ติดต่อผู้ขาย · การประกอบ การพิมพ์ การวัดกระแส และการวัดแรงบิด **NOT RUN** · ทุกตัวเลขแรงบิดเป็น **ค่าประมาณจากโมเดล ไม่ใช่ผลวัด**

ขอบเขตล่าสุด: **5 แกนแขน + ก้าม = 6 actuator** ตาม layout SO-101 (shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper) ตัด wrist yaw ออก (แทนแผน 6 แกน + ก้าม = 7 actuator ที่ใช้ก่อนหน้า; D04 ใช้เฉพาะแกนที่แขนมีตาม D25) · ฐาน (shoulder_pan) ต้องหมุนได้ครบรอบ · ให้ความสำคัญกับ**การเคลื่อนที่ที่นุ่ม** · งบ D24 < 5,000 บาท/แขน ไม่รวมเครื่องพิมพ์ ต่อจาก [servo-prices](2026-10-02-servo-prices.md) และ [am-arm200-vs-so101](2026-10-22-am-arm200-vs-so101.md)

สัญลักษณ์: ✅ = ราคาจากหน้าผู้ขายพร้อม URL ตรวจ 2026-10-22 · ⚠️ = มีราคาแต่มีเงื่อนไข (marketplace ที่ไม่ใช่ร้านทางการ ราคาก่อนภาษี หรือช่วงราคา) · ❌ = หาราคาไม่ได้ ไม่เติมด้วยการเดา

---

## สรุป

| ทางเลือก | actuator (ฐาน / ไหล่ / ศอก / ข้อมือ / ก้าม) | readback | รวม (บาท) | ≤ 5,000 | ≤ 4,000 | สถานะ |
|---|---|---|---:|---|---|---|
| **A** bus ทั้งหมด 12V | STS3215 12V ×6 | 6/6 | **5,990.33** | ❌ เกิน 990.33 | ❌ เกิน 1,990.33 | incomplete |
| A2 bus ทั้งหมด 7.4V | STS3215 7.4V ×6 | 6/6 | **5,700.35** | ❌ เกิน 700.35 | ❌ | incomplete |
| **B** hybrid | STS3215 12V ×3 (ฐาน/ไหล่/ศอก) + MG996R ×3 | 3/6 | **4,964.44** | ✅ เหลือ 35.56 | ❌ เกิน 964.44 | incomplete |
| **C** PWM ทั้งหมด | DS3218MG Pro 360 + DS3218MG ×3 + MG996R ×2 | 0/6 | **4,163.00** | ✅ เหลือ 837.00 | ❌ เกิน 163.00 | incomplete |
| C′ (C ที่ปรับน้อยสุดให้ผ่าน 4,000) | wrist_flex DS3218MG → MG996R | 0/6 | **3,903.00** | ✅ เหลือ 1,097.00 | ✅ เหลือ 97.00 | incomplete |

"incomplete" ทุกแถวเพราะยังไม่มี: **อากรขาเข้า** ของ servo ที่นำเข้า (A/A2/B; ไม่รู้พิกัดและอัตรา), ค่าส่งจาก Kacha (สกรู) และ Lazada (แป้นหมุน) และสาย USB (เพลา/ลูกปืนรับเพลาท้ายของ B ตีราคาแล้ว 2026-10-24) ปุ่ม E-stop อยู่ในทุกทางเลือก ไม่ได้ตัดของด้านความปลอดภัยออกเพื่อให้ราคาลง

**การเปลี่ยนที่น้อยที่สุดเพื่อให้ผ่านงบ**
- A → 5,000: ใช้ bus servo ไม่ได้ทั้ง 6 ตัว ต้องย้าย wrist_flex, wrist_roll และ gripper ไปเป็น PWM ซึ่งก็คือทาง B แม้ใช้รุ่น 7.4V (A2) ก็ยังเกิน 700 บาท
- B → 4,000: ไม่มีทางผ่านถ้ายังเก็บ bus servo 3 ตัว แค่ตัดส่วนกลางของ bus (adapter 345 + bus servo 1 ตัว ≈ 751) ก็ยังไม่พอ จึงต้องไปเป็น C′
- C → 4,000: เปลี่ยน wrist_flex จาก DS3218MG (435) เป็น MG996R (175) ประหยัด 260 บาท ได้ C′ = 3,903

**ข้อเสนอ (ผู้ตัดสินคือทีม):** ถ้าความนุ่มคืออันดับหนึ่ง **ให้ใช้ B** เพราะสามข้อที่รับโหลดมากที่สุด (ฐาน ไหล่ ศอก) ได้ encoder 4096 step, ตั้ง acceleration ได้ในตัว servo และอ่านตำแหน่งกลับได้ แต่ B เหลือ margin เพียง 35.56 บาท (แก้ 2026-10-24 หลังตีราคาชุดลูกปืนรับเพลาจริง) และยังไม่รวมอากร จึง**มีโอกาสเกิน 5,000 จริง** ทาง C/C′ ผ่านงบแน่กว่าแต่ไม่มี readback เลย และแรงบิดไหล่ของ DS3218 ที่ 5V เสี่ยงมาก (ดู §1)

**แหล่ง STS3215 ที่ถูกที่สุด**
- **ในไทย:** ไม่มีร้านไทยร้านไหนแสดงราคา STS3215 ([DroneTh](https://droneth.or.th/product/feetech-sts3215-74v-servo/) ยังให้ "สอบถามราคา") ตัวใกล้เคียงที่มีราคาคือ Waveshare **ST3215-HS 12V 20 kg·cm ราคา 945 บาท ที่ [ModuleMore](https://www.modulemore.com/product/2879/waveshare-st3215-hs-high-speed-bus-servo-20kg)** ส่วน ST3215 12V 30 kg·cm ราคา 1,485 บาทที่ [Arduitronics](https://www.arduitronics.com/product/5593/) **สินค้าหมด**
- **ต่างประเทศ:** [Feetech Official Store บน AliExpress](https://th.aliexpress.com/store/910341271) — **12V แพ็ก 6 ตัว 3,826.48 บาท (637.75/ตัว)** และ **7.4V แพ็ก 6 ตัว 3,466.68 บาท (577.78/ตัว)** ทั้งสองเป็นราคาก่อนภาษี ส่งฟรี ถ้าคิดต่อตัวโดยไม่นับค่าส่ง Waveshare ST3215-7.4V ที่ $16.31 (สั่ง 4 ตัวขึ้นไป) ≈ 550.97 บาทถูกกว่า แต่ค่าส่งมาไทยหาไม่ได้

---

## 1. แรงบิดที่ต้องการ (ยกมาจากโน้ตเดิม)

ที่มา: [am-arm200-vs-so101 §แรงบิด](2026-10-22-am-arm200-vs-so101.md) ท่าเหยียดแนวนอนพร้อมบล็อก 100 g
- **SO-101 ต้นฉบับ 5 แกน (ตรงกับ layout ปัจจุบัน) จาก MJCF ที่ใช้มวล STS3215:** ไหล่ ≈ **12.9 kg·cm** ศอก ≈ **7.6 kg·cm**
- **ค่า 6 แกนเดิมที่มี yaw:** ไหล่ 14.9–16.3, ศอก 8.9–9.9 kg·cm เป็นค่า**อนุรักษ์นิยม** สำหรับแขน 5 แกน ใช้เป็นเพดานบน

| มอเตอร์ที่ไหล่ | stall ตามผู้ผลิต | ไหล่ 12.9–16.3 คิดเป็น % ของ stall | เทียบ rated |
|---|---|---|---|
| STS3215 12V (C018) | 30 kg·cm @12V | 43–54% | rated 10 kg·cm → **เกิน rated 1.29–1.63 เท่า** |
| STS3215 7.4V (C001) | 19.5 @7.4V | 66–84% | rated 5 → เกิน 2.6–3.3 เท่า |
| ST3215-HS | 20 @12V | 65–82% | rated not stated |
| DS3218 | 18 @5V / 21.5 @6.8V | 72–91% @5V / 60–76% @6.8V | rated not stated |

ทุกตัวยังเกิน "rated ≈ 1/3 ของ stall" ของ Feetech เมื่อเหยียดสุด แต่ **C018 เหลือ margin มากที่สุด** จึงเลือก **12V** ให้ฐาน ไหล่ และศอกในทาง A/B ศอกที่ 7.6–9.9 kg·cm ยังต่ำกว่า rated ของ C018 (25–33% ของ stall) ต้องวัดจริงก่อนพิมพ์ชิ้นใหญ่

---

## 2. Actuator: ราคา

### ร้านไทย (บาท/ตัว ไม่มีร้านไหนให้ราคาแพ็กหลายตัว)

| รุ่นตามที่ร้านระบุ | บาท | สต็อก | สถานะ | URL |
|---|---:|---|---|---|
| Feetech STS3215 7.4V 19 kg·cm | ❌ ไม่แสดงราคา | — | ❌ | [DroneTh](https://droneth.or.th/product/feetech-sts3215-74v-servo/) |
| Waveshare ST3215-HS 20 kg·cm @12V, 106 RPM | 945 | in stock | ✅ | [ModuleMore 2879](https://www.modulemore.com/product/2879/waveshare-st3215-hs-high-speed-bus-servo-20kg) |
| Waveshare ST3215 30 kg·cm @12V | 1,485 | **หมด** | ✅ | [Arduitronics 5593](https://www.arduitronics.com/product/5593/) |
| Waveshare SC15 17 kg·cm @8.4V (ยังเท่ากับ 2026-10-02) | 1,185 | พร้อมส่ง | ✅ | [Arduitronics 5144](https://www.arduitronics.com/product/5144/) |
| DS3218MG 20 kg 180° (เฟืองโลหะ, digital, กันน้ำ) | 435 | พร้อมส่ง | ✅ | [Mikroelec 3421](https://www.mikroelec.com/product/3421/) |
| DS3218MG 20 kg 270° | 435 | พร้อมส่ง | ✅ | [Mikroelec 3422](https://www.mikroelec.com/product/3422/) |
| DS3218MG Pro 360° "ควบคุมตำแหน่งได้" | 735 | พร้อมส่ง | ✅ (สเปก 360° เป็นคำกล่าวของร้าน) | [Mikroelec 3424](https://www.mikroelec.com/product/3424/) |
| MG996R 0–180° (เท่าเดิม) | 175 | พร้อมส่ง | ✅ | [CyberTice 63](https://www.cybertice.com/product/63/) |
| TD-8120MG 0–270° (เท่าเดิม) | 480 | พร้อมส่ง | ✅ | [CyberTice 3787](https://www.cybertice.com/product/3787/) |
| MG90S (เท่าเดิม) | 75 | พร้อมส่ง | ✅ | [Arduitronics 53](https://www.arduitronics.com/product/53/) |

DS3218 ทุก listing ในไทย**ไม่ได้อ้างว่าเป็นของแท้ DSServo** ส่วน ST3020 (1,585) และ ST3025 (3,785) ที่ Arduitronics แพงเกินงบ

### นำเข้า (ร้านผู้ผลิตหรือร้านทางการ)

| รายการ | ราคา | ต่อตัว | สถานะ | URL |
|---|---|---|---|---|
| Feetech AliExpress, STS3215-12V แพ็ก 6 ตัว | 3,826.48 บาท ก่อนภาษี | 637.75 | ⚠️ ก่อนภาษี | [item 1005008670304643](https://th.aliexpress.com/item/1005008670304643.html) |
| ↳ แพ็ก 2 ตัว / 1 ตัว | 1,353.50 / 831.71 | 676.75 / 831.71 | ⚠️ | เดียวกัน |
| Feetech AliExpress, ST-3215-C018 12V ×1 | 702.05 | 702.05 | ⚠️ | [item 1005009981870399](https://th.aliexpress.com/item/1005009981870399.html) |
| ↳ C001 (มี 2 option ที่หน้าเว็บไม่ได้บอกว่าต่างกันอย่างไร) | 669.72 / 696.43 | — | ⚠️ | เดียวกัน |
| ↳ URT-1 debug board | 418.84 | — | ⚠️ | เดียวกัน |
| Feetech AliExpress, STS3215 7.4V แพ็ก 6 ตัว (ชื่อ listing ว่า "with URT-1" แต่ไม่ชัดว่ามีบอร์ดในแพ็กหรือไม่) | 3,466.68 | 577.78 | ⚠️ | [item 1005008393548554](https://th.aliexpress.com/item/1005008393548554.html) |
| Waveshare ST3215 12V 30 kg | $21.99 / $20.63 (สั่ง 4 ตัวขึ้นไป) | ≈ 696.91 บาทที่ 4+ | ✅ ค่าส่ง ❌ | [waveshare 22414](https://www.waveshare.com/st3215-servo.htm?sku=22414) |
| Waveshare ST3215-7.4V 19.5 kg | $16.99 / $16.31 (4+) | ≈ 550.97 | ✅ ค่าส่ง ❌ | [waveshare 33014](https://www.waveshare.com/st3215-servo.htm?sku=33014) |
| Waveshare ST3215-HS | $21.99 / $20.63 (4+) | ≈ 696.91 | ✅ ค่าส่ง ❌ | [waveshare HS](https://www.waveshare.com/st3215-hs-servo-motor.htm) |
| Waveshare SC15 | $17.99 / $16.97 (4+) | — | ✅ ค่าส่ง ❌ | [waveshare SC15](https://www.waveshare.com/sc15-servo.htm) |
| Seeed Feetech ST3215-C001 7.4V | $20.00 / $19.00 (10+) | ≈ 675.63 | ✅ ค่าส่ง ❌ | [Seeed 6338](https://www.seeedstudio.com/STS3215-19kg-cm-7-4V-Serial-Servo-p-6338.html) |
| Seeed Feetech ST3215-C047 12V 30 kg (Seeed ขาย 12V ในชื่อ C047 ไม่ใช่ C018) | $22.00 / $20.90 (10+) | ≈ 743.19 | ✅ ค่าส่ง ❌ | [Seeed 6340](https://www.seeedstudio.com/STS3215-30KG-Serial-Servo-p-6340.html) |
| Seeed FE-URT-1 | $10.00 | ≈ 337.81 | ✅ (สต็อกขัดกันเอง) | [Seeed 6705](https://www.seeedstudio.com/Feetech-FE-URT-1-p-6705.html) |

แปลง USD เป็นบาทด้วย 33.7814 (ดู §7) feetechrc.com ไม่มีหน้าร้านและไม่แสดงราคา หา Waveshare official store และ DSServo official store บน AliExpress ไม่เจอ (เจอแต่ reseller)

---

## 3. Actuator: มุม ความนุ่ม และ feedback (จากหน้าผู้ผลิต/datasheet)

| รุ่น | มุมใน position mode | ควบคุมตำแหน่งได้ครบช่วงหรือไม่ | ความละเอียดตำแหน่ง | ตั้ง speed/accel ในตัว servo | baud / update rate | เฟือง | feedback | ที่มา |
|---|---|---|---|---|---|---|---|---|
| STS3215 C001 7.4V / C018 12V | 360° (0–4095), mechanical limit: none | **ได้ครบ 360°** (mode 0) ส่วนหลายรอบ ±7 รอบอยู่ใน mode 3 (step) ซึ่งไม่จำจำนวนรอบหลังไฟดับ | 12-bit magnetic encoder, 0.088°/step | speed ได้ (ประมาณ 3073 step/s สูงสุด) และ ACC ได้ (0–150) ตาม [Waveshare ST3215 wiki](https://www.waveshare.com/wiki/ST3215_Servo); datasheet Feetech ระบุ PID ปรับได้ แต่ไม่ระบุ accel | 38,400 bps–1 Mbps (ค่าเริ่ม 1 Mbps); update rate not stated | ทองแดง (โลหะ), backlash ≤ 0.5° | position, speed, load, voltage, current, temperature | [C001](https://www.feetechrc.com/74v-19-kgcm-plastic-case-metal-tooth-magnetic-code-double-axis-ttl-series-steering-gear), [C018](https://www.feetechrc.com/525603) datasheet |
| Waveshare ST3215 (12V / 7.4V) | 360° (0~4095) | ได้ครบ | 360°/4096 | ตามแถวบน (wiki ST series) | 38.4k–1 Mbps | metal gear | position, load, speed, input voltage | [หน้าสินค้า](https://www.waveshare.com/st3215-servo.htm) |
| ST3215-HS | 360° (0~4095) | ได้ครบ | 360°/4096 | หน้าสินค้า not stated | 38.4k–1 Mbps | metal gear | เหมือนบน | [หน้าสินค้า](https://www.waveshare.com/st3215-hs-servo-motor.htm) |
| SC15 | **210°** (ผู้ผลิต) แต่ร้านไทยเขียน 180° | ได้ใน 210° ส่วน 360° มีแต่ motor mode ซึ่งไม่ควบคุมตำแหน่ง | 210°/1024 ≈ 0.21° | speed ได้; accel not stated | 38.4k–1 Mbps | metal gear | position, load, speed, input voltage | [wiki](https://www.waveshare.com/wiki/SC15_Servo) |
| DS3218 | 180° หรือ 270° แล้วแต่รุ่น (500–2500 µs) | ได้ในช่วงนั้น | deadband 3 µs (≈ 0.27° ที่ 180°, ≈ 0.41° ที่ 270°: คำนวณเอง) | not stated (PWM ไม่มี) | PWM 50–330 Hz | not stated ในเอกสารผู้ผลิต (ร้านเขียนว่า MG/เฟืองโลหะ) | ไม่มี | [DSServo datasheet](https://www.dsservo.com/d_file/DS3218%20datasheet.pdf) |
| DS3218MG Pro 360 | 360° "ควบคุมตำแหน่งได้" | **ตามคำกล่าวของร้านเท่านั้น** ไม่มีในเอกสารผู้ผลิต | not stated | not stated | not stated | ร้านเขียนว่าเฟืองโลหะ | ไม่มี | [Mikroelec 3424](https://www.mikroelec.com/product/3424/) |
| MG996R | ผู้ผลิตตอบว่า **0–159°** แต่ร้านเขียน 180° | ได้ในช่วงนั้น | deadband 1 µs (TowerPro); pulse range not stated | not stated | not stated | metal gear | ไม่มี | [TowerPro](https://towerpro.com.tw/product/mg996r/) |
| TD-8120MG | 270° (0.5–2.5 ms) ตามร้าน ไม่มีสเปกผู้ผลิต | ได้ในช่วงนั้น | not stated | not stated | not stated | ร้านเขียนว่าเฟืองโลหะ | ไม่มี | [CyberTice 3787](https://www.cybertice.com/product/3787/) |
| MG90S | ผู้ผลิต not stated (ร้านเขียน ≤ 180°) | — | deadband 1 µs | not stated | not stated | เฟือง aluminium 6061-T6 | ไม่มี | [TowerPro](https://towerpro.com.tw/product/mg90s-3/) |

**ผลต่อความนุ่ม:** STS/ST สร้าง trapezoid ramp เองในตัว servo (ตั้ง speed + ACC ต่อคำสั่ง) และอ่านตำแหน่งจริงกลับมาได้ ส่วน PWM ทุกตัวต้องให้ host ทำ interpolation เอง และไม่รู้ว่าข้อต่อไปถึงตำแหน่งแล้วหรือยัง ถ้าใช้ PCA9685 ที่ 50 Hz หนึ่ง step = 20 ms/4096 ≈ 4.88 µs ซึ่งหยาบกว่า deadband 3 µs ของ DS3218 (คำนวณเอง) การขับด้วย Nano โดยตรงจึงไม่แย่กว่า PCA9685 สำหรับข้อต่อไม่กี่ข้อ ยังไม่ได้วัดว่า jitter จริงเป็นเท่าไร (**NOT RUN**)

**ฐานหมุนครบรอบ:** ตัวที่ควบคุมตำแหน่งได้ครบ 360° ตามเอกสารผู้ผลิตมีแค่ STS3215/ST3215 (0–4095) DS3218 ปกติได้สูงสุด 270° ส่วน Pro 360 อ้าง 360° ตามร้านเท่านั้น สาย bus ที่ผ่านฐานต้องเผื่อให้บิดได้ ±180° แต่ไม่ต้องหมุนไม่จำกัดรอบ จึง**ไม่ต้องใช้ slip ring** (ดู §5)

---

## 4. Controller และไฟ

| รายการ | บาท | สถานะ | URL / หมายเหตุ |
|---|---:|---|---|
| Waveshare Bus Servo Adapter (A) | 345 (เท่าเดิม) | ✅ | [Arduitronics 6119](https://www.arduitronics.com/product/6119/) มี USB Type-C ให้ PC สั่งงานตรงได้โดยไม่ต้องมี MCU · หน้าผู้ผลิตเขียนว่า **"9~12.6V voltage input"** และไฟเข้าต้องตรงกับไฟ servo จึงเข้ากับ 12V ได้ แต่ยังไม่แน่ใจว่าใช้กับ 7.4V ได้หรือไม่ ([Waveshare $4.99](https://www.waveshare.com/bus-servo-adapter-a.htm)) |
| Feetech FE-URT-1 | ไม่มีร้านไทย | ❌ ไทย | Seeed $10 / AliExpress 418.84 (ดู §2) |
| Arduino Nano CH340 Type-C (ไม่มีสาย USB) | 140 | ✅ | [CyberTice 5696](https://www.cybertice.com/product/5696/) ใช้สร้าง PWM ใน B/C |
| PCA9685 | 265 | ✅ (ไม่ได้ใส่ใน BOM) | [Arduitronics 1589](https://www.arduitronics.com/product/1589/) |
| PSU 12V 10A (S-120-12) | 289 (ราคาปกติ 360) | ✅ | [ModuleMore 779](https://www.modulemore.com/product/779/) · มีตัวเลือก 320 ที่ [Arduitronics 2231](https://www.arduitronics.com/product/2231/) และ 365 ที่ [CyberTice 560](https://www.cybertice.com/product/560/) |
| PSU 12V 15A | 429 / 450 / 470 | ✅ | ModuleMore 1542 / CyberTice 886 / Arduitronics 2839 |
| PSU 5V 10A | 325 (เท่าเดิม) | ✅ | [CyberTice 559](https://www.cybertice.com/product/559/) |
| PSU 7.4–8.4V กระแสสูง | ไม่พบในร้านไทย | ❌ | ใช้ 12V + buck แทน |
| Buck XL4016 สูงสุด 8A | 95 | ✅ | [CyberTice 1290](https://www.cybertice.com/product/1290/) · ยังไม่รู้ประสิทธิภาพจริง |

**กระแสที่ใช้เลือก PSU** (ค่าจาก datasheet Feetech C018: idle 30 mA, เดินตัวเปล่า 180 mA, rated 900 mA ที่ 10 kg·cm, stall 2.7 A; C001 ที่ 7.4V: 6 / 150 / 650 mA / 2.5 A)
- **A (C018 ×6) ที่ 12V:**
  - หยุดนิ่งทั้งหมด: 6 × 0.03 = 0.18 A
  - เดินตัวเปล่าทั้งหมด: 6 × 0.18 = 1.08 A
  - ทุกตัวที่ rated: 6 × 0.9 = 5.4 A
  - **กรณีแย่ที่ยังเป็นไปได้:** ไหล่กับศอก stall (2 × 2.7) + อีก 4 ตัวที่ rated (4 × 0.9) = **9.0 A** จึงเลือก **12V 10A**
  - stall พร้อมกันทั้ง 6 ตัว = 16.2 A ให้ฟิวส์ 10A และ overload protection ของ servo เป็นตัวตัด (datasheet: เกิน 80% ของ stall นาน 2 วินาที servo จะเข้า protection)
- **A2 (C001 ×6) ที่ 7.4V:** 2 × 2.5 + 4 × 0.65 = **7.6 A** ใกล้เพดาน 8A ของ buck XL4016
- **B:**
  - ราง 12V: C018 ×3 → 2 × 2.7 + 0.9 = 6.3 A
  - ราง PWM ประมาณ 6V ผ่าน buck: MG996R ×3 ที่ stall 1.4 A (TowerPro) = 4.2 A ที่ 6V ≈ 2.3 A ด้าน 12V (**สมมติ**ประสิทธิภาพ 90%)
  - รวม ≈ **8.6 A** ใช้ 12V 10A ได้
- **C ที่ 5V:** stall ของ DS3218 ที่ 5V 1.8 A × 4 + MG996R 1.4 A × 2 = 10.0 A ถ้า stall ทั้งหมดพร้อมกัน ใช้ 5V 10A ได้ แต่กระแสตอนเดินของ DS3218 not stated

**rail:** bus กับ PWM ใช้รางไฟเดียวกันไม่ได้ C001 รับได้สูงสุด 7.4V และ DS3218/MG996R รับ ≤ 6.8V ใน B จึงแยกรางด้วย buck และต้องต่อ ground ร่วมระหว่าง adapter กับ Nano (ยังไม่ได้ตรวจวงจร)

---

## 5. ฮาร์ดแวร์ (ราคาไทย ตรวจ 2026-10-22)

| รายการ | ราคา | สถานะ | URL / หมายเหตุ |
|---|---|---|---|
| **E-stop LAY37-11ZS 22 mm มีกล่อง, กดล็อก หมุนคลาย, 1NO+1NC, 220V 10A** | 145 | ✅ | [CyberTice 5458](https://www.cybertice.com/product/5458) |
| E-stop LAY37-11ZS แบบ 2NC (ไม่มีกล่อง) | 55 | ✅ | [CyberTice 5538](https://www.cybertice.com/product/5538) |
| กระบอกฟิวส์ 5×20 แบบ inline มีสาย | 7 | ✅ | [CyberTice 1352](https://www.cybertice.com/product/1352) |
| ฟิวส์แก้ว 5×20 10A แพ็ก 10 ตัว (15A ราคาเดียวกัน) | 30 | ✅ | [Mikroelec 278](https://www.mikroelec.com/product/278) · ไม่ได้ระบุ fast/slow |
| lever connector 2 ทาง 32A (แบบ 223 ทั่วไป ไม่ใช่ WAGO) | 14/ตัว | ✅ | [CyberTice 5193](https://www.cybertice.com/product/5193) |
| DC jack 5.5×2.1 ตัวเมีย ขั้วสกรู | 10 | ✅ | [Mikroelec 696](https://www.mikroelec.com/product/696) · ไม่ได้ระบุพิกัดกระแส |
| สายซิลิโคน 18 AWG ยาว 30 cm | 9/เส้น | ✅ | [ModuleMore 1157](https://www.modulemore.com/product/1157) |
| สายซิลิโคน 22 AWG ยาว 30 cm | 4/เส้น | ✅ | [ModuleMore 1199](https://www.modulemore.com/product/1199) · 20 AWG ไม่พบ |
| สาย UL1007 18 AWG (PVC) ยาว 10 m | 90 / 110 | ✅ | Arduitronics 4370 / CyberTice 4316 (ตัวเลือกถ้าต้องเดินสายยาว) |
| ท่อหด ชุด 328 ชิ้น | 75 | ✅ | [CyberTice 2570](https://www.cybertice.com/product/2570) |
| สาย servo ต่อยาว 30 cm (หน้าร้านเขียน "หัวเดียว" ต้องตรวจว่าเป็นผู้-เมียหรือไม่) | 19 | ✅ | [CyberTice 5032](https://www.cybertice.com/product/5032) |
| สาย bus 5264 แบบ daisy-chain | ไม่พบในไทย | ❌ | datasheet ระบุว่า servo แต่ละตัวมีสาย 5264-3P ยาว 15 cm มาให้ ถ้าต้องการสายยาวกว่านี้ยังไม่มีแหล่ง |
| สกรู M2×6 หัวกลม SS304 | 0.8/ตัว | ✅ | [Kacha](https://www.kacha.co.th/product/button-head-socket-cap-screws/) · ขั้นต่ำ 20 บาท ค่าส่งคิดตอน checkout |
| สกรู M3 หัวจม SS304: ×8 0.6, ×12 1.0, ×20 1.2 | /ตัว | ✅ | [Kacha](https://www.kacha.co.th/product/hex-socket-head-cap-screws/) · ไม่พบชุดสกรูแบบกล่องในร้านไทย |
| น็อต M3 แพ็ก 20 ตัว | 8 | ✅ | [Mikroelec 1683](https://www.mikroelec.com/product/1683) |
| heat-set insert M3×4×4.5 ทองเหลือง | 1.20/ตัว | ✅ | [Mikroelec 1880](https://www.mikroelec.com/product/1880) · ไม่พบแพ็ก 50/100 ตัว |
| ลูกปืน 608ZZ (8×22×7) | 10 | ✅ | [Mikroelec 1392](https://www.mikroelec.com/product/1392) |
| ลูกปืน MR105ZZ (5×10×4) / 625ZZ / 688ZZ | 12 / 10 / 10 | ✅ | Mikroelec 1398 / 1394 / 1396 |
| ลูกปืนมีปีก F623ZZ (3×10×4) / F684ZZ (4×9×4) | 20 / 20 | ✅ (ตรวจ 2026-10-24) | [Mikroelec 1399](https://www.mikroelec.com/product/1399/f623zz-bearing-3-10-4mm-3mm-axis-flange) / [Mikroelec 1406](https://www.mikroelec.com/product/1406/f684zz-bearing-4-9-4mm-4mm-axis-flange) · 684ZZ แบบไม่มีปีกไม่มีขาย |
| ลูกปืน 623ZZ (3×10×4) | 10 | ✅ (ตรวจ 2026-10-24) | [Mikroelec 1876](https://www.mikroelec.com/product/1876/623zz-bearing-3-10-4mm-3mm-axis) |
| เพลาสแตนเลส SUS304 Ø3 ยาว 200 mm (ตัดเป็นเพลาสั้น) | 8 | ✅ (ตรวจ 2026-10-24) | [Mikroelec 1872](https://www.mikroelec.com/product/1872/sus304-stainless-steel-shaft-3mm-200mm) · **เพลา Ø4 ไม่พบ** ใน Mikroelec, CyberTice, Arduitronics; Kacha ไม่มีสลัก (dowel pin) หรือสกรูไหล่ |
| สกรู M3×16 หัวจม SS304 | 1.00/ตัว | ✅ (ตรวจ 2026-10-24, มีของ 2,643) | [Kacha](https://www.kacha.co.th/product/hex-socket-head-cap-screws/) |
| ลูกปืน 6802ZZ (15×24×5) / 6801ZZ (12×21×5) SBC | 58 / 48 | ✅ (48 อ่านจาก structured data) | [Duraprothai](https://www.duraprothai.com/product/193482-191429/) |
| 6701-2RS (12×18×4) | 40 | ⚠️ ยางกันฝุ่น ไม่ใช่ ZZ | [Duraprothai](https://www.duraprothai.com/product/210861-213474/) |
| **แป้นหมุน lazy susan 4" (100 mm) เหล็กชุบซิงค์** | 51 | ⚠️ ผู้ขายทั่วไปบน Lazada ไม่ได้ระบุพิกัดรับน้ำหนัก | [Lazada GBO](https://www.lazada.co.th/products/pdp-i2017306842.html) |
| แป้นหมุน SST-6 157×157 mm รุ่นหนา (ผู้ขายอ้าง 60–100 kg) | 130 | ⚠️ Lazada | [Lazada](https://www.lazada.co.th/products/pdp-i1912248686.html) |
| slip ring 6 สาย 2A/สาย (SparkFun, ไม่บังคับ) | 950 | ✅ | [Arduitronics 4181](https://www.arduitronics.com/product/4181) |
| slip ring 12 สาย 2A/สาย (SparkFun, ไม่บังคับ) | 1,155 | ✅ | [Arduitronics 4803](https://www.arduitronics.com/product/4803) |

**E-stop:** พิกัด 10A ที่ 220V **เท่ากับ** PSU 10A ไม่ได้สูงกว่า และหน้าร้านไม่ได้ระบุพิกัดตัด DC จึงเสนอให้ใส่ NC ไว้ฝั่ง **AC ขาเข้า PSU** ซึ่งกระแสต่ำกว่ามาก (120 W / 230 V ≈ 0.52 A ไม่รวม inrush; คำนวณเอง) ถ้าจะตัดฝั่ง DC ต้องหาสวิตช์ที่ระบุพิกัด DC ≥ 10A หรือใช้ relay/contactor (ยังไม่ได้ตีราคา) เมื่อตัดไฟ servo จะหมดแรงบิด แขนจะตกลงตามน้ำหนัก จึงต้องออกแบบท่าพักไว้ด้วย (**NOT RUN**)

**ลูกปืนรับเพลาด้านที่สอง (แก้ 2026-10-24):** ร่าง CAD v1 ใช้แผ่นท้าย + เพลาสั้น + ลูกปืนมีปีกที่ wrist_flex และ gripper (hardware-notes/2026-10-23-presentation-model-v0.md) ใช้ F623ZZ + เพลา SUS304 Ø3 (Mikroelec ร้านเดียว) ร่าง CAD เปลี่ยนเป็นชุดนี้แล้ว ส่วนชุด Ø4 (F684ZZ 20 บาท) หาเพลา Ø4 ในร้านที่ใช้ไม่ได้ ข้อความเดิม: STS3215 เป็น dual shaft ข้อต่อจึงรับด้วย bottom horn แบบ SO-101 ได้ ไม่ต้องใช้ลูกปืนเพิ่ม (ทาง A, และฐาน/ไหล่/ศอกของทาง B) PWM ที่มีเพลาเดียวต้องใช้ลูกปืน + pin ทุกข้อต่อแบบ clevis ใน BOM ใช้ **608ZZ** (ราคาต่ำสุด 10 บาท และมีขายมาก) ส่วน**เพลา/สกรู M8 หรือ M5 ยังไม่ได้ตีราคา** ถ้าจะให้ชิ้นเล็กลงใช้ MR105ZZ + สกรู M5 ได้

**slip ring:** ไม่ได้รวมใน BOM เพราะฐานหมุนครบ 360° ได้โดยปล่อยให้สายบิด ±180° และ 2A/สาย ไม่พอกับกระแสราง (6 สาย = 3 คู่ ≈ 6 A < 9 A ตาม §4) ถ้าต้องหมุนไม่จำกัดรอบจริง ต้องใช้รุ่นที่ทนกระแสสูงกว่านี้

---

## 6. Filament

| ยี่ห้อ 1 kg 1.75 mm | บาท | สถานะ | URL |
|---|---:|---|---|
| R3D PLA (ราคา 350–380 ตาม variant; BOM ใช้ 380 ซึ่งเป็นค่าสูงสุดที่แสดง) | 350–380 | ⚠️ ช่วงราคา | [Arduino4pro 3342](https://www.arduino4pro.com/product/3342) |
| Bambu PLA Basic Refill (ไม่มี spool; ราคาปกติ 590) | 450 | ✅ | [Siamreprap](https://siamreprap.bentoweb.com/en/product/1206312/Bambu-PLA-Basic-Refill) |
| eSUN ePLA / PLA+ (หลายสีหมด) | 469 | ✅ | [iget3dp](https://www.iget3dp.com/product/47) |

ใช้แทนสมมติฐานเดิม 400 บาท/kg ที่ยังไม่ได้ตรวจ

**ปริมาณ:**
- **ขอบบน:** ปริมาตรทึบของ SO-101 follower 571 cm³ × 1.24 g/cm³ (ความหนาแน่นจาก [Bambu PLA Basic TDS ผ่าน mirror](https://www.additive-x.com/shop/mpattachments/file/viewonline/id/494/product_id/2236); Bambu Studio ใช้ 1.26) = **708–719 g** ซึ่งน้อยกว่า 1 kg **จึงพอด้วย spool เดียว**
- **ค่าจริงที่ infill 15%:** README ของ SO-101 แนะนำ [PLA+, infill 15%](https://github.com/TheRobotStudio/SO-ARM100#printing-the-parts) แต่ไม่ได้บอกน้ำหนักที่ใช้ และไม่มีแหล่งที่ให้ตัวคูณ 15% → กรัมได้ (ขึ้นกับจำนวน wall/top layer) **จึงไม่คำนวณ** ให้ slice เพื่อดูตัวเลขจริง
- **ข้อควรระวัง:** CAD ของทีม (ฐาน turntable, ช่อง PWM, ช่องลูกปืน) จะทำให้ปริมาตรต่างจาก 571 cm³

---

## 7. ค่าใช้จ่ายนำเข้า

- **อัตราแลกเปลี่ยน:** ใช้ [ธปท. (thaifxrates.net, ER_XLS_EN.xls)](https://www.thaifxrates.net/) ณ 22 ต.ค. 2026 อัตราขายเฉลี่ยของธนาคารพาณิชย์ **33.7814 บาท/USD** (อัตรา interbank ถัวเฉลี่ย 33.650) ใช้ในการแปลง USD ทั้งหมด อัตราของบัตรจริงจะสูงกว่านี้
- **VAT 7%:** [เอกสารกรมศุลกากร มาตรการเพิ่มประสิทธิภาพการจัดเก็บรายได้ ปีงบประมาณ 2569](https://www.customs.go.th/data_files/8342f73dce85665090d55bb44eb9a0e4.pdf) ระบุว่าเก็บ VAT สินค้านำเข้ามูลค่าไม่เกิน 1,500 บาทแล้ว "ตั้งแต่วันที่ 5 กรกฎาคม 2567" **ทุกทางที่นำเข้าจึงบวก 7%** ฐานคือ CIF + อากร ซึ่งที่นี่ค่าส่งเป็น 0 จึงคิดจากราคาสินค้า หน้า AliExpress บอกว่าเป็นราคา "ก่อนภาษี" แต่ไม่ได้เข้าไปดูหน้า checkout ว่าเก็บ VAT ณ ตอนจ่ายหรือไม่
- **อากร:** เอกสารเดียวกันเสนอให้ลด de minimis จาก 1,500 บาทเหลือ 1 บาท โดยมีผล 1 ม.ค. 2569 ส่วน[ข่าว](https://www.bangkokbiznews.com/business/economic/1206273)รายงานว่าเริ่มเก็บแล้ว **แต่ยังไม่ได้อ่านประกาศฉบับจริง** อย่างไรก็ตาม order ในทาง A/A2/B มีมูลค่าเกิน 1,500 บาทอยู่แล้วจึงต้องเสียอากรตามพิกัด ยังไม่ได้ตรวจพิกัดและอัตรา (servo น่าจะอยู่ในหมวด 8501) รวมถึงสิทธิ ACFTA (Form E) ❌ **ทุกทางที่นำเข้าจึงไม่สมบูรณ์**
- **ค่าส่ง:**
  - Feetech AliExpress: แสดง "free shipping" ส่งจากจีน คาดว่าถึง 29 ต.ค.–9 พ.ย. ✅
  - Waveshare: [shipping policy](https://www.waveshare.com/shipping) ไม่มีอัตรา (คิดตามน้ำหนักและ courier ผู้ซื้อจ่ายภาษีเอง) ❌
  - Seeed: [policy](https://www.seeedstudio.com/get_help/ShippingOrder) แสดงราคาตอน checkout เท่านั้น เงื่อนไข DAP ❌
  - ผลคือราคา Waveshare และ Seeed ไม่สามารถนำไปเทียบเป็นยอดรวมได้

## 8. ค่าส่งของร้านไทย

| ร้าน | ค่าส่ง (บาท) | ส่งฟรี | ที่มา |
|---|---|---|---|
| Arduitronics | 50 / 70 (structured data ไม่ได้ระบุ carrier) | not stated | [how2order](https://www.arduitronics.com/how2order) EMS / Kerry |
| CyberTice | 50 / 70 | title เขียน "ส่งฟรี" แต่ไม่บอกเงื่อนไข | [how2order](https://www.cybertice.com/how2order) |
| ModuleMore | 40 / 65 / 72 (Kerry) | เกิน 900 | หน้าแรก |
| Mikroelec | 35 | ถึง 1,200 ("ตามเงื่อนไขที่แสดงตอน checkout") | [how2order](https://www.mikroelec.com/how2order) |
| Arduino4pro | 40–75 | — | structured data |
| Kacha / Lazada | ❌ คิดตอน checkout | — | — |

ใน BOM ใช้ค่า**สูงสุด**ของแต่ละร้าน

---

## 9. BOM ทั้งสามทาง

### ส่วนที่ทุกทางใช้ร่วมกัน = 940 บาท

| รายการ | จำนวน | บาท | สถานะ |
|---|---|---:|---|
| E-stop มีกล่อง CyberTice 5458 | 1 | 145 | ✅ |
| กระบอกฟิวส์ inline CyberTice 1352 | 1 | 7 | ✅ |
| ฟิวส์ 10A แพ็ก 10 Mikroelec 278 | 1 | 30 | ✅ |
| lever 2 ทาง CyberTice 5193 | 2 | 28 | ✅ |
| ซิลิโคน 18 AWG 30 cm ModuleMore 1157 | 6 | 54 | ✅ |
| ซิลิโคน 22 AWG 30 cm ModuleMore 1199 | 6 | 24 | ✅ |
| ท่อหด 328 ชิ้น CyberTice 2570 | 1 | 75 | ✅ |
| DC jack ขั้วสกรู Mikroelec 696 | 1 | 10 | ✅ |
| M2×6 (SO-101 ใช้ 4 ตัวต่อ STS3215; จำนวนประมาณจากแบบ) Kacha | 30 | 24 | ✅ |
| M3×8 / ×12 / ×20 Kacha (จำนวนประมาณจากแบบ) | 20 / 20 / 10 | 44 | ✅ |
| น็อต M3 แพ็ก 20 Mikroelec 1683 | 1 | 8 | ✅ |
| heat-set M3 Mikroelec 1880 | 50 | 60 | ✅ |
| แป้นหมุน 4" Lazada GBO | 1 | 51 | ⚠️ ผู้ขาย Lazada |
| PLA 1 kg R3D Arduino4pro 3342 | 1 | 380 | ⚠️ ค่าสูงสุดของช่วง |

### A: bus ทั้งหมด STS3215 12V ×6 — รวม 5,990.33 ❌

| รายการ | บาท | สถานะ |
|---|---:|---|
| STS3215-12V แพ็ก 6 ตัว (Feetech AliExpress) | 3,826.48 | ⚠️ ก่อนภาษี |
| VAT 7% | 267.85 | คำนวณ |
| อากร | ❌ | ยังไม่รู้ |
| Bus Servo Adapter (A) Arduitronics | 345 | ✅ |
| PSU 12V 10A ModuleMore | 289 | ✅ |
| ส่วนร่วม | 940 | ดูตารางบน |
| ค่าส่งไทย: Arduitronics 70 + ModuleMore 72 + CyberTice 70 + Mikroelec 35 + Arduino4pro 75 | 322 | ✅ (ยังไม่รวม Kacha/Lazada) |
| **รวม** | **5,990.33** | เกิน 5,000 ไป 990.33 |

- **ฐาน:** C018 เพราะควบคุมตำแหน่งได้ครบ 360° ตามผู้ผลิต และมี encoder
- **12V:** เหลือ margin ที่ไหล่มากที่สุด (§1)
- **host:** PC ต่อ USB-C เข้า adapter ได้เลยโดยไม่ต้องมี MCU
- **A2 (7.4V แพ็ก 6 ตัว 3,466.68 + VAT 242.67, ใช้ PSU 12V + buck 95 เพราะในไทยไม่มี PSU 7.4V):** รวม 5,700.35 ยังเกิน และ adapter (A) ระบุไฟเข้า 9–12.6V จึงอาจใช้กับ 7.4V ไม่ได้ ถ้าในแพ็กมี URT-1 มาให้ ตัด adapter ได้ 345 บาท ก็ยังเกิน

### B: hybrid — bus 12V ×3 + PWM ×3 — รวม 4,964.44 ✅ (5,000) ❌ (4,000)

| ข้อต่อ | actuator | บาท | สถานะ |
|---|---|---:|---|
| shoulder_pan (ฐาน) | STS3215-12V | ⎫ แพ็ก 2 ตัว 1,353.50 + C018 ×1 702.05 = 2,055.55 | ⚠️ ก่อนภาษี |
| shoulder_lift | STS3215-12V | ⎬ | |
| elbow_flex | STS3215-12V | ⎭ | |
| VAT 7% | | 143.89 | คำนวณ |
| wrist_flex / wrist_roll / gripper | MG996R ×3 CyberTice 63 | 525 | ✅ |

| อื่น ๆ | บาท | สถานะ |
|---|---:|---|
| Bus Servo Adapter (A) | 345 | ✅ |
| Nano (PWM 3 ช่อง) | 140 | ✅ |
| PSU 12V 10A | 289 | ✅ |
| Buck XL4016 สำหรับราง PWM ประมาณ 6V | 95 | ✅ |
| ชุดรับเพลาท้าย MG996R (ร่าง CAD v1, 2026-10-24): F623ZZ ×2 (40) + เพลา SUS304 Ø3 ×200 mm 1 เส้น (8) Mikroelec | 48 | ✅ แทน 608ZZ ×2 (20) เดิม |
| สกรู M3×16 ×4 ยึดปีกฝั่งไกลผ่านแผ่นท้าย (Kacha) | 4 | ✅ |
| สาย servo ต่อยาว 30 cm ×3 | 57 | ✅ |
| ส่วนร่วม | 940 | |
| ค่าส่ง (5 ร้านเหมือน A) | 322 | ✅ |
| อากร | ❌ | |
| **รวม** | **4,964.44** | เหลือ **35.56** ซึ่งอาจหมดไปกับอากร |

- **ฐาน:** C018 เพราะ PWM ที่มีเอกสารผู้ผลิตรองรับไปได้ไม่เกิน 270° และ C018 เดินนุ่มกว่า
- **ไหล่และศอก:** ใช้ bus เพราะรับแรงบิดมากที่สุด
- **ราง:** bus 12V และ PWM ประมาณ 6V ผ่าน buck แยกกัน ใช้ ground ร่วม
- **การสั่งงาน:** มี USB 2 พอร์ต คือ adapter และ Nano
- **ทางเลือก:** ถ้าเปลี่ยน wrist_flex เป็น DS3218MG (+260) จะเรียบขึ้น (deadband ตามผู้ผลิต 3 µs มีแรงบิดเหลือ) แต่ยอดรวม 5,192.44 จะเกินงบ

### C: PWM ทั้งหมด — รวม 4,163.00 ✅ (5,000) ❌ (4,000); C′ = 3,903.00 ✅ ทั้งสองระดับ

| ข้อต่อ | actuator | บาท | สถานะ |
|---|---|---:|---|
| shoulder_pan (ฐาน) | DS3218MG Pro 360° Mikroelec 3424 | 735 | ✅ (360° ตามคำกล่าวของร้าน) |
| shoulder_lift / elbow_flex / wrist_flex | DS3218MG 180° Mikroelec 3421 ×3 | 1,305 | ✅ |
| wrist_roll / gripper | MG996R ×2 | 350 | ✅ |
| Nano | | 140 | ✅ |
| PSU 5V 10A CyberTice 559 | | 325 | ✅ |
| 608ZZ ×4 (shoulder_lift, elbow, wrist_flex, gripper) | | 40 | ✅ (ยังไม่รวม pin) |
| สาย servo ต่อยาว ×4 | | 76 | ✅ |
| ส่วนร่วม | | 940 | |
| ค่าส่ง: Mikroelec 35 (ยอดเกิน 1,200 จึงอาจได้ส่งฟรี) + CyberTice 70 + ModuleMore 72 + Arduino4pro 75 | | 252 | ✅ |
| **รวม** | | **4,163.00** | |
| **C′:** เปลี่ยน wrist_flex เป็น MG996R (−260) | | **3,903.00** | เหลือ 97 จาก 4,000 |

- **ฐาน:** DS3218MG Pro เพราะเป็น PWM ตัวเดียวที่อ้าง 360° แบบควบคุมตำแหน่ง แต่ไม่มีเอกสารผู้ผลิต ถ้าไม่จริง ฐานจะหมุนได้แค่ 270° (DS3218 270°) และ**ไม่ผ่านข้อกำหนดหมุนครบรอบ**
- **ไหล่ที่ 5V:** DS3218 stall 18 kg·cm ต้องใช้ 72–91% ของ stall ซึ่ง**เสี่ยงที่สุดในสามทาง** ถ้าเปลี่ยนเป็น PSU 12V 10A + XL4016 ตั้ง 6.8V (+59 บาท) stall จะเป็น 21.5 (60–76%) แต่ buck มีเพดาน 8A
- **ไม่มี readback:** ทุกข้อเป็น command ไม่ใช่มุมที่วัดได้จริง ความนุ่มขึ้นกับ interpolation ฝั่ง host ทั้งหมด
- **เงินที่เหลือ** (837 บาทใน C) ใช้อัปเกรด E-stop เป็นรุ่นที่มีพิกัด DC หรือเพิ่ม relay ได้ แต่ยังไม่ได้ตีราคา

---

## 10. Gaps

1. **ราคา STS3215 ในไทย:** ไม่มีร้านไหนแสดง (DroneTh ให้ถามทาง LINE) ส่วน ST3215 12V ที่ Arduitronics ของหมด
2. **อากรขาเข้า servo:** ไม่รู้พิกัด/อัตรา/สิทธิ FTA ยังไม่ได้อ่านประกาศที่ยืนยันว่าเลิก de minimis แล้ว และยังไม่รู้ว่า AliExpress เก็บ VAT ตอน checkout หรือไม่
3. **ค่าส่ง Waveshare/Seeed มาไทย:** ต้อง checkout จึงเห็น ทำให้ราคาต่อตัวที่ถูกของ Waveshare ($16.31) ยังเทียบเป็นยอดรวมไม่ได้
4. **ค่าส่ง Kacha และ Lazada:** ยังไม่รู้
5. **ของที่ยังไม่มีราคา:** สาย USB, horn สำรอง, สาย bus 5264 ที่ยาวกว่า 15 cm, E-stop ที่มีพิกัด DC
6. **Bus Servo Adapter (A) กับ 7.4V:** หน้าผู้ผลิตเขียน 9–12.6V ยังไม่แน่ใจว่าใช้กับ servo 7.4V ได้
7. **DS3218MG Pro 360:** สเปกมาจากร้าน ไม่ใช่ผู้ผลิต และ DS3218 ทุก listing ไม่ได้อ้างของแท้
8. **AliExpress:** ราคาเปลี่ยนตาม session/คูปอง (BOM ใช้ราคาปกติ ไม่ใช้ราคาคูปองคนใหม่) และ C018 มีสองราคาใน listing ต่างกัน
9. **ความนุ่ม:** ยังไม่ได้ตรวจ jitter, ACC และ update rate จริงของทั้งสามทาง (**NOT RUN**)
10. **แรงบิด:** ยังเป็นค่าจากโมเดล ต้องวัดไหล่จริงก่อนสั่งพิมพ์ชิ้นใหญ่

ไม่ได้แก้ไฟล์อื่นใน repo และไม่ได้ git commit
