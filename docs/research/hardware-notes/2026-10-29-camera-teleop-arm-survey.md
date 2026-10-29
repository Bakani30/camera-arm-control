# แขนที่ใช้กับการคุมด้วยกล้อง/มือ: งานวิจัยและชุมชนออกแบบอย่างไร และผลต่อแขน H1

ตรวจ 2026-10-29 · สำรวจเว็บเท่านั้น (paper, repo, docs ทางการ, หน้าผู้ผลิต/ร้าน) · ซิม/กล้อง/ฮาร์ดแวร์: **NOT RUN**

คำถาม: แขนที่ถูกคุมด้วย hand tracking จากกล้องหรือ vision teleop ในงานที่สำเร็จ มีลักษณะร่วมอะไร และควรปรับแขนจริงของทีมอย่างไร
- **H1** ในบันทึกนี้ = แขนจริงขนาดเล็กของทีม: แบบ B (`cad/shell_v1`) บนจลนศาสตร์ spec v0 (SO-101, ลิงก์ ~113/135 mm, tool ~98 mm), STS3215 ที่ฐาน/ไหล่/ศอก, MG996R ที่ wrist_flex, STS3032 ที่ wrist_roll + ก้ามสองนิ้วขนาน
- โจทย์: หยิบบล็อก 40 mm ที่ ~25 cm, วางถาดด้านข้าง ~25 cm, กดปุ่ม ~20 cm; เกณฑ์หลักคือ**แม่นและตอบสนองถูกต้อง** ไม่ต้องการระยะเอื้อมไกล งบต่อแขน < ~5,700 บาท

ป้าย: **[ข้อเท็จจริง]** = มีแหล่งกำกับ · **[ข้อประเมิน]** = ความเห็นผู้เขียน ยังไม่ทดลอง

## 1. สรุปสั้น
1. **[ข้อเท็จจริง] การ map แบบ relative/clutch เป็นแนวหลัก** ทั้งงานวิจัยและ LeRobot: จับจุดอ้างอิงตอนเริ่ม/ตอนกด engage แล้วส่งการเคลื่อนที่สัมพัทธ์ + clamp workspace + จำกัดก้าวต่อเฟรม [S1,S2,S4,S5,S7,S8] การ map แบบ absolute 1:1 พบในงานที่มีกล้อง depth และแขนใหญ่ และงานที่ใช้แขนเล็กเจอปัญหาระยะเอื้อมไม่เท่ามือ [S6,S10]
2. **[ข้อเท็จจริง] แขน 5 DOF ใช้ IK ที่ให้ตำแหน่งมาก่อน ทิศทางเป็นแค่เป้าอ่อน** (LeRobot SO-101: `orientation_weight=0.01`) [S8]; งาน SO-101 ที่พยายามตามทิศมือเต็ม 6D ได้ error ทิศเฉลี่ย ~163° [S6] งานต้นทุนต่ำบางงานล็อก wrist pitch ไว้ที่ 0 เลย [S12]
3. **[ข้อเท็จจริง] แขนต้นทุนต่ำที่ทำงานได้ดีเกือบทั้งหมดใช้ servo ที่อ่านมุมกลับได้** (STS3215 ใน SO-101, Dynamixel ใน Koch/PincherX) [S12,S22,S23]; หลักฐานตรงที่สุดคือ uArm Swift (potentiometer, repeatability 5 mm) เทียบ Swift Pro (encoder 12 bit, 0.2 mm) [S19]
4. **[ข้อเท็จจริง] ทุกระบบกรองสัญญาณสองชั้น**: กรองจุดมือ (EMA/One Euro/Kalman) + กรองหรือจำกัดคำสั่งแขน และทิ้งเฟรมที่กระโดด [S2,S6,S7,S9,S10,S11,S24]
5. **[ข้อเท็จจริง] อัตราและ latency**: MediaPipe บน CPU ~23–35 ms/เฟรม [S1,S6]; loop ควบคุม 25–60 Hz [S1,S2,S4,S5]; คนเริ่มทำงานแย่ลงชัดที่ delay 200–300 ms [S27]
6. **[ข้อเท็จจริง] แกนลึก (depth) จากกล้องเดียวคือจุดอ่อนที่สุด**: z ของ MediaPipe อ้างอิงข้อมือ ไม่ใช่ระยะจากกล้อง [S28]; งานกล้องเดียวรายงาน depth ambiguity [S2]; error ระดับระบบที่รายงานอยู่ราว 3.6–7 cm [S6,S10,S13]
7. **[ข้อประเมิน] ผลต่อ H1**: ไม่ต้องเพิ่มระยะเอื้อม; ลงทุนที่ (ก) wrist_flex แบบมี readback และช่วงมุมพอให้ก้มตรงลงที่ 20–25 cm (ข) ลดความคลอนข้อ (ค) ก้ามสองนิ้วขนานที่อ้ากว้างกว่าบล็อกพอรับ error ของ mapping (ง) จัดจุดงานไว้กลาง workspace ห่างแกนฐานและขอบเอื้อม

## 2. หลักฐานรายแหล่ง

### 2.1 งานวิจัย vision teleop (แขนอุตสาหกรรม)
| แหล่ง | แขน / ก้าม | กล้อง | mapping แขน | กรอง / อัตรา / latency | สาเหตุปัญหาที่รายงาน | ตัวเลข |
|---|---|---|---|---|---|---|
| AnyTeleop [S1] | xArm6 + Allegro | RealSense 1 ตัว (มีโหมด RGB ล้วน) | fusion ส่ง **relative motion** ของกล้องที่มั่นใจสุด; ไม่ระบุ scale แขน; CuRobo วางแผนเลี่ยงชน | ไม่มี filter แยก ใช้เทอม smoothness; pose 26–35 ms, retarget ~9 ms, motion ~8 ms; EE pose ~25 Hz → joint 120 Hz; ไม่รายงาน end-to-end | มือหลุดตอนขยับเร็ว (ต้องช้าลง), มือตั้งฉากกล้องแล้ว self-occlusion; RGB ล้วนตำแหน่ง error มากกว่า depth | สำเร็จ 0.6–1.0 ต่องาน (10 ครั้ง/งาน) |
| Robotic Telekinesis [S2] | xArm6 + Allegro | RGB ตัวเดียว ไม่ calibrate | **relative ต่อลำตัว** (ลำตัวหุ่นสมมติสูงกว่าฐาน 25 cm); IK แบบ Selectively Damped Least Squares | ตัด outlier ที่กระโดด + EMA α=0.25 (α ต่ำ = หน่วง); ทั้งระบบ ~25 Hz | depth ambiguity, ฝ่ามือขนานกล้อง, ของเล็กลื่น; ผู้ทดลองไม่รู้สึกหน่วง/สั่น | สำเร็จ 0.3–0.9 (10 ครั้ง/งาน, timeout 1 นาที) |
| DexPilot [S3] | KUKA iiwa7 + Allegro | RealSense D415 ×4 | ลงทะเบียนพิกัดกล้อง→หุ่นจากท่าเริ่มต้น (absolute ใน studio); RMP + impedance 200 Hz | low-pass ลำดับหนึ่งที่มุม retarget; ส่งมุมมือ 30 Hz; **latency ทั้งระบบ ~1 s** ซึ่งผู้เขียนระบุว่าควรลด | depth ต้องอยู่ใน ~1 m, ไม่มี tactile ทำให้งานละเอียดยาก | peg-in-hole สำเร็จ "ราว 10%" |
| Bunny-VisionPro [S4] | xArm7 ×2 + Ability hand | Vision Pro (ไม่ใช่ webcam) | **relative** จากเฟรมตอน init; IK รวม cost singularity (manipulability) + self-collision | IK+collision+singularity ~16 ms; โมดูลแขน > 60 Hz | finger occlusion → คำสั่งกระตุก; AnyTeleop+ ขยับข้อแรงเกิน | ชนะ baseline 9/10 งาน |
| Open-TeleVision [S5] | แขน 7 DOF (H1, GR-1 ใช้ gripper) | Vision Pro/stereo | ตำแหน่ง **relative ต่อหัว**, ทิศตามข้อมือเทียบ init; CLIK (Pinocchio) + SE(3) filter + nullspace offset ใกล้ singular | teleop 60 Hz | IK fail ใกล้ขีด manipulability; ภาพ mono ทำงานช้าลงและสำเร็จน้อยลง | ผู้ใช้ 4 คน: stereo สำเร็จ 100%, mono 50–100% |

### 2.2 MediaPipe / กล้องทั่วไป กับแขนเล็กหรือแขนต้นทุนต่ำ
| แหล่ง | แขน / actuator / ก้าม | mapping | กรอง / อัตรา | ปัญหา | ตัวเลข |
|---|---|---|---|---|---|
| Hand shadowing SO-ARM101 [S6] | SO-101 (STS3215), ก้าม SO-101 | **absolute 1:1 หน่วยเมตร** หลัง deproject ด้วย RGB-D; IK DLS (PyBullet) ใช้ 5 ข้อ เน้นตำแหน่ง; ก้ามจากมุมนิ้วโป้ง–ชี้ ถ้านิ้วหายใช้ค่าล่าสุด | EMA จุดมือ α=0.8 + EMA ผล IK α=0.5 (ลด jerk 57–68%); MediaPipe 23 ms, IK 80 ms (offline ~5 FPS) | **ระยะแขน ~300 mm vs มือคน ~600 mm** ต้องย้ายตะกร้า; occlusion; error ทิศ ~163° เพราะ 5 DOF | IK position error เฉลี่ย 36.4 mm; หยิบ–วางบนโต๊ะ 86.7% (130/150); นอกสถานที่ 9.3% |
| LeRobot phone → SO-100/101 [S7] | SO-100/101 | กดค้างปุ่มเพื่อ enable, **กดครั้งแรกจับ reference**, ส่ง delta → `EEReferenceAndDelta`; IK Placo | `EEBoundsAndSafety` clamp workspace + `max_ee_step_m=0.10`; ก้ามแบบความเร็ว | มอบหน้าที่ให้ผู้ใช้กลับแกนเองถ้ารู้สึกกลับทิศ | — |
| LeRobot Isaac Teleop → SO-101 [S8] | SO-101 | **clutch**: ทุกครั้งที่ engage จับจุดเริ่มจาก FK ของ**มุมที่วัดได้จริง** (ไม่กระโดด); ปล่อย = แขนค้าง | IK Placo `orientation_weight=0.01` (5 DOF จึงตามทิศได้บางส่วน "โดยตั้งใจ"), warm start จากคำตอบก่อน; z ต่ำสุด 0 (โต๊ะ); ก้ามตามแรงกดแบบต่อเนื่อง | — | — |
| ThinkRobotics SO-101 hand tracking [S9] | SO-101 | MediaPipe → PoseStamped → MoveIt bridge | One Euro filter ลด jitter (ไม่บอกค่า) | ไม่รายงาน | ไม่มี |
| Spot shared control [S10] | Spot arm 6 DOF, jaw gripper | **absolute** ผ่าน calibration คงที่ | median depth 5×5, EMA α=0.5, ทิ้งเฟรมที่กระโดด > 25 cm; กล้อง 30 Hz แต่ loop ~5 Hz | error โตตามความเร็วข้อมือ (แขนตามไม่ทัน) | error ตำแหน่งเฉลี่ย 0.07 m (OptiTrack) |
| Arm occlusion correction [S11] | TIAGo Pro | relative ต่อลำตัว; BioIK | ตัด landmark visibility < 0.7, Kalman/EKF | self-occlusion ทำ depth ผิด; Kalman drift ตอน occlusion นาน | depth RMSE ดิบ 28–35 cm → 2–5 cm หลังแก้ |
| ICINCO 2025 [S12] | PincherX-100 (Dynamixel) 4 DOF + ก้าม | **map เชิงเส้นพิกัดภาพ → มุมข้อ**: x→ฐาน, y→ศอก, **ขนาดมือ (ข้อมือ–โคนนิ้วกลาง) → ไหล่**; **wrist pitch ล็อก 0** | ท่า activation ก่อนสั่ง; ก้ามปิดเมื่อนิ้วโป้ง–ชี้ < 35 px; สั่งด้วย move time 0.3 s แบบไม่รอจบ | — | เล่นซ้ำงานที่สอน 98% (50 รอบ) — วัดการเล่นซ้ำ ไม่ใช่ teleop สด |
| Biomimetics 2026 [S13] | แขน 5 ข้อ + ก้าม ต้นทุนต่ำ, กล้อง laptop | map descriptor มือ → คำสั่งระดับข้อ | — | jitter, depth ambiguity จากกล้องเดียว | ผู้ทดลอง 42 คน สำเร็จ 88%; error วาง 6.73 ± 3.11 cm (ตัวเลขจากบทคัดย่อ/ผลค้นหา เปิดฉบับเต็มไม่ได้: 403) |

### 2.3 Maker และแขนการศึกษา
- **[ข้อเท็จจริง] maker บน GitHub**: ESP32 + PCA9685 + servo PWM 6 ตัว กรองด้วย EMA ไม่มีตัวเลขความแม่น [S14]; อีกโปรเจกต์ใช้ EMA α=0.25–0.35 + deadzone แต่ "ยังไม่ต่อฮาร์ดแวร์จริง" [S15] รูปแบบที่พบบ่อยคือ PWM servo ไม่มี readback และไม่วัดผล
- **[ข้อเท็จจริง] myPalletizer 260** (4 แกน เอื้อม 260 mm) คุมด้วย MediaPipe จาก webcam [S17]; บทความสรุปมือสองระบุว่า latency และ jitter จำกัดให้ใช้กับงานที่ยอมตำแหน่งหยาบได้ [S16]
- **[ข้อเท็จจริง] สเปกแขนการศึกษา**: Dobot Magician 4 แกน เอื้อม 320 mm, repeatability ±0.2 mm [S18]; uArm Swift Pro 4 DOF ระยะทำงาน 50–320 mm, 0.2 mm ด้วย encoder 12 bit เทียบ Swift ธรรมดา 5 mm ด้วย potentiometer [S19]; myCobot 280 6 DOF รัศมี 280 mm, ±0.5 mm [S20]; UFACTORY Lite 6 เอื้อม 440 mm, 0.5 mm [S21]
- **[ข้อประเมิน]** Dobot Magician และ uArm ใช้โครง parallelogram ที่ทำให้หน้าเครื่องมือขนานพื้นเสมอ จึงจับแบบคว่ำลง (top-down) ได้ทั้ง workspace ด้วย 4 แกน ข้อนี้มาจากรูปทรงที่รู้กันทั่วไป **ยังไม่พบเอกสารผู้ผลิตยืนยัน** (เปิดคู่มือ uArm/Dobot ไม่ได้: 503/connection refused)

### 2.4 ฐานความรู้ด้านการควบคุม
- **[ข้อเท็จจริง] position vs rate**: position control ดีกว่า rate control เมื่อ workspace ของแขนเล็กหรือใกล้เคียงพื้นที่มือคน แต่ข้อได้เปรียบหายไปเมื่อแขนช้า [S25]
- **[ข้อเท็จจริง] Bubble technique** (position ในฟอง, rate นอกฟอง): เร็วและแม่นกว่า scaling และ clutching ในงานทดลองของผู้คิดค้น [S26] — ต้นแบบของ D18/D26
- **[ข้อเท็จจริง] One Euro filter**: low-pass ที่ cutoff ปรับตามความเร็ว ลด jitter ตอนช้าและลดหน่วงตอนเร็ว ตั้ง 2 ค่า (`min_cutoff`, `beta`) [S24]

## 3. ตารางรูปแบบร่วม
| ลักษณะ | พบใน | ข้อสรุป |
|---|---|---|
| mapping relative / clutch + reference latch | S1,S2,S4,S5,S7,S8 | มาตรฐานของ vision/XR teleop; absolute ใช้เมื่อมี depth + calibration [S3,S6,S10] |
| clamp workspace + จำกัดก้าวต่อเฟรม | S7,S8,S10 | ทุกระบบที่ใช้กับแขนจริงมี |
| IK เน้นตำแหน่ง, ทิศเป็นเป้าอ่อน (แขน < 6 DOF) | S6,S8 | 5 DOF ตามทิศมือเต็มไม่ได้; ระบบง่ายล็อก pitch [S12] |
| ป้องกัน singularity / ชน ใน IK | S1,S4,S5 | แขนใหญ่ใช้ cost หรือ nullspace; แขนเล็กใช้ DLS [S2,S6] |
| กรองจุดมือ + กรองคำสั่ง + ทิ้ง outlier | S2,S6,S9,S10,S11,S14,S15 | EMA α 0.25–0.8 หรือ One Euro หรือ Kalman |
| loop ≥ 25 Hz | S1,S2,S4,S5 | ระบบ 5 Hz [S10] รายงานว่าแขนตามไม่ทัน |
| actuator มี readback | S6–S8,S12,S19,S22,S23 | clutch ของ LeRobot ต้องใช้มุมวัดจริง [S8] |
| ก้ามขนาน/jaw คุมด้วย pinch ต่อเนื่องหรือ threshold | S5,S6,S8,S10,S12 | ต่อเนื่อง [S6,S8] หรือสองสถานะ [S12]; ต้องมีค่าเมื่อนิ้วหาย [S6] |
| การวัดผล = success rate ต่องาน (5–50 ครั้ง) | S1–S6,S12,S13 | ตัวเลข mm วัดเทียบ mocap มีน้อย [S10,S11] |

## 4. ผลต่อ H1: คง / เปลี่ยน / เพิ่ม
| เรื่อง | ข้อเสนอ | เหตุผลและแหล่ง |
|---|---|---|
| DOF | **คง 5 DOF + ก้าม** | SO-101 5 DOF ใช้กับ teleop จริงได้ [S6,S8]; งานจับ/วาง/กดปุ่มไม่ต้องการทิศเต็ม [ข้อประเมิน] |
| ทิศของก้าม | **เพิ่มโหมดก้มตรงลง (top-down) ใน IK** แทนการตามทิศมือ: pitch ปลายคงที่ (เช่น −90° สำหรับหยิบ/วาง, ค่าคงที่อีกค่าสำหรับกดปุ่ม), roll จากฟอง D26 | ทิศมือจาก 5 DOF ได้ error ~163° [S6]; LeRobot ให้น้ำหนักทิศแค่ 0.01 [S8]; ICINCO ล็อก pitch แล้วยังหยิบ–วางได้ [S12]; แขน parallelogram ได้ top-down ฟรีจากกลไก [ข้อประเมิน] |
| wrist_flex | **เปลี่ยน MG996R → servo bus ที่มี readback** (STS3215 หรือรุ่นในตระกูล STS) ก่อนเรื่องอื่น; ตรวจว่าช่วงมุมพอให้ top-down ทั้ง 20–25 cm | MG996R ไม่มี readback, deadband ~5 µs [S30], ช่วง 159° ก้มตรงลงไม่ได้ทุกระยะ (บันทึก A/B §3); clutch แบบ LeRobot จับ home จากมุมวัดจริง [S8]; uArm pot vs encoder = 5 mm vs 0.2 mm [S19]; STS3215 = 4096 step/รอบ (0.088°) [S29] — ต้องผ่านการตัดสินงบ D24 |
| ความคลอนและความแข็งของลิงก์ | **เพิ่ม** ลูกปืน/เพลาฝั่ง idle และจุดยึด servo ให้แน่นก่อนล็อกแบบ B | งานต้นทุนต่ำแทบไม่วัด backlash (ช่องว่าง); ระบบตัดสินที่ success rate [ข้อประเมิน]; ด่านวัดในบันทึก A/B §4 ยังเป็นทางที่ถูก |
| เป้าความแม่นของแขนล้วน | **ตั้งเป้า repeatability ระดับไม่กี่ mm ไม่ใช่ sub-mm** | error ระดับระบบจากกล้องเดียว 3.6–7 cm [S6,S10,S13] ใหญ่กว่า error แขนหลายเท่า; แขนการศึกษาราคาสูงยังอยู่ที่ 0.2–0.5 mm [S18–S21] [ข้อประเมิน]; ผูกกับ D17 ชั้น A |
| ก้าม | **คงก้ามสองนิ้วขนาน (แบบ B)**; อ้าสุด ~57 mm (current-state 2026-10-29) เผื่อบล็อก 40 mm ราว 8 mm ต่อข้าง | ช่องเผื่อนี้ต้องรับ error ตำแหน่งที่เหลือหลังโหมดละเอียด [ข้อประเมิน]; ก้ามคุมต่อเนื่องจาก pinch + ค่าเมื่อนิ้วหาย [S6,S8] ตรงกับ D19; STS3032 มี readback ใช้จำกัดแรงบีบได้ [ข้อประเมิน] |
| ระยะเอื้อม / ตำแหน่งงาน | **คงความยาวลิงก์ SO-101** และวางบล็อก/ถาด/ปุ่มกลาง workspace: ไม่ยืดสุด ไม่ใกล้แกนฐาน | งานมือสเกล 1:1 กับแขนเล็กเจอปัญหาระยะ [S6]; mapping relative ไม่ต้องการระยะเพิ่ม [S7,S8]; singularity/IK fail ที่ขอบ [S4,S5]; 20–25 cm อยู่ราว 58–72% ของระยะสุด ~346 mm (วัดจากแกนไหล่) [ข้อประเมิน จากผลรวมลิงก์] |
| อัตราคำสั่ง | **เป้า camera 30 fps, คำสั่งแขน ≥ 25–30 Hz ผ่าน sync-write, end-to-end < 200 ms** | loop 25–60 Hz ในงานที่สำเร็จ [S1,S2,S4,S5]; 5 Hz ตามไม่ทัน [S10]; delay 200–300 ms ทำให้แย่ลง [S27]; latency 1 s ถูกระบุว่าเป็นปัญหา [S3] |
| การกรอง | **One Euro ที่จุดมือ + เพดานความเร็ว/ความเร่ง D32 ที่แขน + ทิ้งเฟรมกระโดด + จำกัดก้าวต่อเฟรม** | S2,S6,S7,S10,S24; EMA α ต่ำเพิ่มหน่วงชัด [S2] |

## 5. วิธี map มือที่เปลี่ยนสิ่งที่แขนต้องมี
- **relative/clutch ทำให้ระยะเอื้อมไม่สำคัญ แต่ความซ้ำได้สำคัญขึ้น** [ข้อประเมิน]: ผู้ใช้ปิดลูปด้วยตาและขยับเพิ่มทีละนิด ความคลอนและ deadband ของข้อจะรู้สึกเป็น "ขยับแล้วไม่ไป" หรือ "เลยแล้วถอย" มากกว่าเป็น error คงที่; สอดคล้องกับ hybrid bubble D18 และผล [S25,S26]
- **clutch ต้องอ่านมุมจริงทุกข้อ** [S8] ถ้า wrist_flex ไม่มี readback จุด engage จะอิงคำสั่งล่าสุด ซึ่งเพี้ยนเมื่อ servo ถูกดันหรือหลุดขั้น [ข้อประเมิน]
- **ทิศแบบเป้าอ่อนหรือคงที่** ทำให้ wrist_flex ต้องมีช่วงมุมพอสำหรับท่าคงที่ที่เลือก มากกว่าตามมือได้ทุกทิศ [S6,S8]
- **depth ไม่แม่น** (ขนาดฝ่ามือเป็น proxy [S12]; z เป็นค่าสัมพัทธ์ [S28]) → Z gain ต่ำ/deadband ตาม D20 และก้ามที่ทน error แนวดิ่ง: ปลายนิ้วยาวพอและพื้นผิวไม่ลื่น [ข้อประเมิน]
- **ปุ่มกด**: งานที่ต้องกดใช้แรงแนวดิ่ง แขน 5 DOF + ท่าคงที่ (ปลายชี้ลง) ลดผลของทิศมือที่แกว่ง [ข้อประเมิน]; ยังไม่พบงานกล้อง+มือที่วัดการกดปุ่มด้วยแขนเล็กโดยตรง

## 6. ช่องว่าง
- ไม่พบงานกล้องเดียว + MediaPipe ที่รายงาน **backlash หรือ repeatability ของแขน** แยกจาก error ทั้งระบบ; การแยก 4 ชั้นตาม D17 จึงเป็นของใหม่ต้องวัดเอง
- ไม่พบตัวเลข **end-to-end latency** ของระบบ webcam → servo bus; มีแต่เวลาต่อโมดูล [S1,S4,S6]
- ไม่มีตัวเลขความแม่น depth ของ MediaPipe เป็น mm เทียบ mocap ที่อ่านได้ในรอบนี้ (GMH-D [S31] มีแต่บทคัดย่อ)
- ยังไม่ยืนยันว่า wrist_flex ของ spec v0 (และถ้าเปลี่ยนเป็น STS) ทำ top-down ได้ที่ 20–25 cm กับความสูงฐานจริง ต้องรัน IK กวาดจุดงาน
- ราคา STS3215 ในไทยสำหรับ wrist_flex และผลต่องบ D24 ยังเปิด (บันทึก A/B §5)
- สเปกแขนการศึกษา myCobot/Dobot บางค่ามาจากหน้าร้าน ไม่ใช่ datasheet ผู้ผลิต; การเป็น parallelogram ยังไม่มีเอกสารยืนยัน

## แหล่งที่มา
1. S1 — [Qin et al., AnyTeleop (RSS 2023), arXiv 2307.04577](https://arxiv.org/html/2307.04577)
2. S2 — [Sivakumar et al., Robotic Telekinesis (RSS 2022), arXiv 2202.10448](https://arxiv.org/html/2202.10448)
3. S3 — [Handa et al., DexPilot (ICRA 2020), arXiv 1910.03135](https://arxiv.org/pdf/1910.03135)
4. S4 — [Ding et al., Bunny-VisionPro, arXiv 2407.03162](https://arxiv.org/html/2407.03162)
5. S5 — [Cheng et al., Open-TeleVision, arXiv 2407.01512](https://arxiv.org/html/2407.01512)
6. S6 — [Chiche et al., Vision-Based Hand Shadowing for Robotic Manipulation via Inverse Kinematics (SO-ARM101), arXiv 2603.11383](https://arxiv.org/html/2603.11383)
7. S7 — [LeRobot docs: Phone teleoperation](https://huggingface.co/docs/lerobot/en/phone_teleop)
8. S8 — [LeRobot docs: Isaac Teleop → SO-101](https://huggingface.co/docs/lerobot/en/isaac_teleop)
9. S9 — [ThinkRobotics: LeRobot SO101 Hand Tracking](https://thinkrobotics.com/blogs/learn/lerobot-so101-hand-tracking)
10. S10 — [A Vision-Based Shared-Control Teleoperation Scheme for Controlling the Robotic Arm of a Four-Legged Robot, arXiv 2508.14994](https://arxiv.org/html/2508.14994)
11. S11 — [Kwok, Koenig, Hu, Seeing Through Occlusion: Deterministic Arm Kinematic Correction for Robot Teleoperation, arXiv 2606.19240](https://arxiv.org/html/2606.19240)
12. S12 — [Michels et al., Real-Time Hand Gesture Control of a Robotic Arm with Programmable Motion Memory (ICINCO 2025)](https://www.scitepress.org/Papers/2025/137178/137178.pdf)
13. S13 — [Drăgoi et al., Interactive Teleoperation of an Articulated Robotic Arm Using Vision-Based Human Hand Tracking, Biomimetics 11(2):151](https://www.mdpi.com/2313-7673/11/2/151)
14. S14 — [GitHub raazankit/6dof-robotic-arm](https://github.com/raazankit/6dof-robotic-arm)
15. S15 — [GitHub RitvikAnish/Gesture-Controlled-Robotic-Arm](https://github.com/RitvikAnish/Gesture-Controlled-Robotic-Arm)
16. S16 — [Let's Data Science: Gesture Tracking Controls myPalletizer 260 (บทความมือสอง)](https://letsdatascience.com/news/gesture-tracking-controls-mypalletizer-260-without-controlle-f85144d6)
17. S17 — [Elephant Robotics บน Hackster: Control a Robot Arm with the Force — the Grogu Style](https://www.hackster.io/Elephant-Robotics-Official/control-a-robot-arm-with-the-force-the-grogu-style-3e196a) (เปิดตรงไม่ได้: 403)
18. S18 — [DOBOT Magician (หน้าผู้ผลิต)](https://www.dobot-robots.com/products/education/magician.html)
19. S19 — [uArm Swift / Swift Pro specifications (PDF บน Mouser)](https://www.mouser.com/datasheet/2/813/uArm-Swift-Specifications-en-1223866.pdf) (อ่านผ่านผลค้นหา เปิด PDF ตรง timeout)
20. S20 — [OpenELAB: myCobot 280 M5 guide (หน้าร้าน)](https://openelab.io/blogs/learn/mycobot-280-m5-python-ros-and-setup-guide)
21. S21 — [UFACTORY Lite 6 (หน้าผู้ผลิต)](https://ufactory.cc/lite-6-collaborative-robot)
22. S22 — [GitHub AlexanderKoch-Koch/low_cost_robot (Koch, Dynamixel XL430/XL330)](https://github.com/AlexanderKoch-Koch/low_cost_robot)
23. S23 — [GitHub TheRobotStudio/SO-ARM100 (SO-101, STS3215 1/345 ที่ follower)](https://github.com/TheRobotStudio/SO-ARM100)
24. S24 — [Casiez, Roussel, Vogel, 1€ Filter (CHI 2012)](https://cristal.univ-lille.fr/~casiez/1euro)
25. S25 — [Kim, Tendick, Ellis, Stark, A comparison of position and rate control for telemanipulations… (NASA NTRS)](https://ntrs.nasa.gov/citations/19890010493)
26. S26 — [Dominjon et al., Bubble technique (HCI museum) ](https://hci-museum.lisn.upsaclay.fr/bubble-technique) และ [การเปรียบเทียบ Scaling/Clutching/Bubble (HAL)](https://hal.archives-ouvertes.fr/hal-00750834)
27. S27 — [Chen et al., The Effects of Communication Delay on Human Performance… in Mobile Robot Teleoperation, arXiv 2508.18074](https://arxiv.org/abs/2508.18074)
28. S28 — [MediaPipe Hand Landmarker, Python guide (นิยาม z และ world landmarks)](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/python)
29. S29 — [Waveshare ST3215 Servo](https://www.waveshare.com/st3215-servo.htm) และ [DFRobot ST3215 (12 bit, 0.088°)](https://www.dfrobot.com/product-2962.html)
30. S30 — [TowerPro MG996R datasheet (สำเนาที่ Cornell)](https://people.ece.cornell.edu/land/courses/ece4760/FinalProjects/f2017/kmv48_rp625/kmv48_rp625/kmv48_rp625/MG996RTowerPro.pdf)
31. S31 — [Amprimo et al., validation of MediaPipe Hand and GMH-D, arXiv 2308.01088](https://arxiv.org/abs/2308.01088)
32. ไฟล์โปรเจกต์: `docs/research/03-DECISIONS-GLOSSARY.md` (D17–D22), `docs/research/hardware-notes/2026-10-29-arm-a-vs-b-accuracy.md`, `cad/shell_v1/README.md`, `arm_spec/small_arm_v0.json`, `docs/current-state.md` (ช่วงก้าม 0–57 mm)

แหล่งเว็บเปลี่ยนได้ บันทึกนี้สรุป ณ วันที่ตรวจ
