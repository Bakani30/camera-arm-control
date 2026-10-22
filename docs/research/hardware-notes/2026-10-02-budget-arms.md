# ฐานแขนราคาประหยัด: MeArm / EEZYbotARM / LittleArm / UMIRobot

ตรวจแหล่งหลัก 2026-10-02 · R001 · สำรวจเอกสารเท่านั้น · ทุกการทดลอง **NOT RUN**

## ข้อเสนอ

**UMIRobot น่าศึกษาสำหรับแขนวิจัยงบจำกัดแบบมีเงื่อนไข; EEZYbotARM Mk2 และ MeArm printable เป็นตัวเลือกต้นแบบหยิบ–วางราคาประหยัดเท่านั้น** สองรุ่นหลังไม่มีข้อมืออิสระ จึงใช้แทนเป้าหมาย wrist retargeting เดิมไม่ได้โดยอัตโนมัติ การเพิ่มข้อมือเป็นงานออกแบบใหม่ทั้งโหลด มอเตอร์ kinematics และซิม ไม่ใช่เพิ่ม STL แล้วพร้อมใช้

งบ 10,000 บาทเป็นงบฮาร์ดแวร์ทั้งหมด มีเครื่องพิมพ์ แต่ยังต้องนับวัสดุพิมพ์ PSU จุดยึด อะไหล่ ค่าส่ง/ภาษี และเครื่องมือวัด บล็อก 4–5 ซม. เป็นขนาดเริ่มต้นเดิม วัสดุ/น้ำหนักยังเปิดอยู่ ราคาด้านล่างต่างปีและต่างฐาน **ยังจัดลำดับต้นทุนส่งถึงไทยไม่ได้**

## ตัวเลือกที่ควรตรวจต่อ

| ฐาน | ไฟล์/แกน/ฮาร์ดแวร์ | การเชื่อมและ feedback | ต้นทุน/สิทธิ์/ข้อแลกเปลี่ยน |
|---|---|---|---|
| **UMIRobot** | ผู้สร้างลิงก์ [STL แขน](https://www.thingiverse.com/thing:4797804) และ [ก้ามตัวอย่าง](https://www.thingiverse.com/thing:6107830); แขน 5 ข้อต่อ + ก้าม 1 รวม 6 มอเตอร์: MG996R ×4 และ microservo ×2 ตาม BOM บทความ; Arduino UNO + PCB แยกไฟเซอร์โว [U1,U2] | [Python API](https://github.com/mmmarinho/umirobot-py) ผ่าน USB serial มี `set_qd()/update()/get_q()`; ผู้สร้างรายงาน GUI ทดสอบ Windows 10/11 และ Intel/M1 แต่ไม่ใช่ผลบน ASUS ทีม [U3] **`get_q()` ไม่ใช่มุมวัดจริง**: firmware คืน `curr_pos_` ที่สั่งเซอร์โว; potentiometer inputs แยกจาก servo state [U4] | BOM ประมาณ **US$70 ในบทความ 2023** รวม filament 146 g, UNO, PCB, potentiometers, PSU, servos, สกรู/สาย; ไม่มีราคาขายปัจจุบันหรือค่าส่งไทย และก้ามทีม/การดัดแปลงต้องคิดใหม่ [U2] แขน 5 แกนยังไม่กำหนด pose 6 มิติอิสระครบ; มีฐาน kinematic control ให้ศึกษา |
| **EEZYbotARM Mk2** | [คู่มือผู้สร้างพร้อม `EBAmk2_stlfiles.zip`](https://www.instructables.com/EEZYbotARM-Mk2-3D-Printed-Robot/) และ [Thingiverse](https://www.thingiverse.com/thing:1454048); ผู้สร้างเผยแพร่ source CAD บน Onshape และระบุให้ copy/modify โดยรักษา license/credit; MG995 หรือ MG946 ×3 + SG90 ก้าม ×1 = **แขน 3 แกน + ก้าม** ไม่ใช่ข้อมือ 4 แกน [E1] | ผู้สร้างใช้ Pololu Mini Maestro USB; มี Arduino/Bluetooth ทางเลือก [E1] Maestro มี serial protocol/ปรับ speed–acceleration แต่ `Get Position` ช่อง servo คืนค่าพัลส์ที่ส่ง ไม่ใช่ encoder มุมจริง [E2] ไม่พบ URDF/MJCF/contact scene จากผู้สร้างที่ตรวจ | STL ไม่มีราคาซื้อในคู่มือ; **BOM รวมปัจจุบัน unresolved** ต้องจัดหา bearing 606zz, ลูกเหล็ก 6 mm, สกรู/นอต และ controller/PSU ด้วย [E1] ควรตรวจเป็นต้นแบบโต๊ะเพราะมี CAD และก้ามถอดเปลี่ยน; license เต็มของไฟล์ยัง unresolved ห้ามถือว่าไม่มีเงื่อนไข |
| **MeArm printable fork** | ต้นฉบับ [MeArm](https://github.com/MeArm/MeArm) เป็น DXF สำหรับ laser-cut แผ่น 3 mm; แยกจาก [fork ของ jakub.milkowsky บน MakerWorld](https://makerworld.com/en/models/86531?from=search) ที่ผู้แก้ระบุแปลงสำหรับ 3D printing/Fusion360 และรู M2.5 [M1,M2] รวม 4 เซอร์โว = **แขน 3 แกน + ก้าม** [M3] | [Arduino IK library](https://github.com/MeArm/MeArm-Arduino) มี `moveToXYZ/openClaw/closeClaw` พิกัด mm; การเชื่อม PC ต้องทำ serial adapter/firmware ให้ตรง ไม่มี measured joint feedback จาก library ที่ตรวจ; `getX/Y/Z` เป็น state คำนวณ ไม่ใช่การวัดปลายแขน [M3] ไม่พบ contact sim ของ fork | [Maker Kit](https://shop.mearm.com/products/mearm-maker-kit-cut-your-own) **£32.99 GBP** ณ ตรวจ รวม 4 metal-gear servos, PCB/cable, สกรู/นอต/เครื่องมือ; ไม่รวมโครง/controller/PSU/ค่าส่งไทย [M4] ต้นฉบับ hardware **CC BY-SA 3.0**; fork แสดง **CC Attribution-Noncommercial** ต้องตรวจเงื่อนไขฉบับเต็ม/ความสอดคล้องกับต้นฉบับก่อนเผยแพร่แบบแก้ ไม่ยก license ของต้นฉบับมาแทน fork |

**UMIRobot license สำคัญ:** เว็บผู้สร้างระบุ mechanical **CC BY-NC-ND 4.0**, software GPLv3 และแบบก้ามนักศึกษายังเป็นสิทธิ์นักศึกษา [U1] CC ข้อ 2(a)(1) อนุญาตสร้าง/ทำซ้ำงานดัดแปลงเพื่อ noncommercial แต่ไม่อนุญาต Share งานดัดแปลง [U5] จึงศึกษาฐานเพื่อทดลองภายในได้ภายใต้เงื่อนไข; การแจก CAD/STL ที่แก้ใน repo วิจัยต้องปิดข้อสิทธิ์ก่อน ไม่เหมารวมว่าการเขียนผลทดลองทุกชนิดถูกห้าม และไม่สมมติว่าก้ามตัวอย่างใช้ license เดียวกัน

**ซิม UMIRobot:** มี [CoppeliaSim scenes และ URDF](https://github.com/mmmarinho/umirobot/tree/main/models) จริง [U6] ไม่ใช่เพียงรูป 3D; ตรวจ URDF พบ collision/inertial และ 5 revolute joints แต่ mesh paths เป็น `file:///Users/user/Desktop/URDF/...` และไม่มี gripper ต้องแก้ path/ก้าม/actuation ก่อนทดลอง contact ลูกบล็อก ไม่มี MJCF ที่ยืนยันจากชุดนี้ ซิมตามแผนต้องทดลองบน ASUS; M1 ไม่รันซิม

## ตัวที่พัก

- **EEZYbotARM Mk1:** [คู่มือผู้สร้าง](https://www.instructables.com/EEZYbotARM/) ใช้ MG90S และก้าม MG90S/SG90; อ่านขั้นประกอบยืนยันฐาน/แขน/ก้าม แต่ไฟล์ [Thingiverse](https://www.thingiverse.com/thing:1015238) และ license/BOM รวมยังตรวจไม่ครบ ข้อได้เปรียบเหนือ Mk2 สำหรับบล็อกจริงยังไม่ยืนยัน ไม่มีข้อมืออิสระ
- **EEZYbotARM Mk3:** พบ [หน้าต้นฉบับผู้สร้าง](https://www.thingiverse.com/thing:2838859) แต่เว็บหลัก/Thingiverse อ่านเนื้อหาไม่ได้จากเครื่องมือครั้งนี้ หยุดที่ **unresolved** สำหรับจำนวนแกน/มอเตอร์/BOM/controller/homing/feedback/license/ไฟล์ครบ ไม่ใช้รายละเอียดจากเว็บคัดลอกเป็นหลักฐาน
- **LittleArm / 2C:** [ผู้สร้างรุ่นแรก](https://hackaday.io/project/12593-3d-printed-arduino-robot-arm) มี STL 4 ชิ้นดาวน์โหลดและราคาเก่า **<US$40 ปี 2016** ไม่ใช่ BOM วันนี้หรือชุดไฟล์ก้ามครบ; [2C](https://hackaday.io/project/27318-littlearm-2c-3d-printed-robot-arm) ระบุ MG90S ×4, Nano, HC-06, PCB และ core files ต้องซื้อ เว็บ download ปัจจุบันอ่านไม่ได้ สิทธิ์ CAD/contact sim unresolved
- **LittleArm Big:** [ผู้สร้าง](https://hackaday.io/project/26008-littlearm-big) ระบุ **5 แกน + ก้าม**, reach 11.5 in, payload 0.25 lb (~113 g; คำกล่าวผู้สร้าง); [firmware](https://github.com/slantconcepts/LittleArm-Big/blob/master/LittleArmBIG_Sketch/LittleArmBIG_Sketch.ino) มี 6 servo objects รับ 6 มุม+delay ผ่าน serial 9600 และ ack `d`; `Servo.read()` ไม่ใช่ encoder feedback โค้ด GPLv3 แต่ CAD/license/ราคาชุดปัจจุบันยัง unresolved: ลิงก์ STL ไป `littlearmrobot.com/downloads.html` ใช้งานไม่ได้ในการตรวจนี้ **พักแม้มีแกนข้อมือ** จนยืนยันไฟล์จริง ไม่เสนอจาก showcase อย่างเดียว

## หลักฐานและงานต่อ

U1 [เว็บผู้สร้าง/ไฟล์/สิทธิ์](https://mmmarinho.github.io/UMIRobot/) · U2 [บทความ/BOM/DH](https://arxiv.org/html/2301.06668v2) · U3 [Python README](https://github.com/mmmarinho/umirobot-py) · U4 [servo read source](https://github.com/mmmarinho/umirobot-arduino/blob/main/src/UMIServo/UMIServo.cpp), [state collection](https://github.com/mmmarinho/umirobot-arduino/blob/main/src/UMIRobot.cpp) · U5 [CC legal code](https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode.en) · U6 [URDF source](https://github.com/mmmarinho/umirobot/blob/main/models/urdf/UMIRobot.urdf)

E1 [Mk2 ผู้สร้าง/STL/CAD/BOM](https://www.instructables.com/EEZYbotARM-Mk2-3D-Printed-Robot/) · E2 [Pololu serial/readback](https://www.pololu.com/docs/0J40/5.e) · M1 [ต้นฉบับ/CC BY-SA](https://github.com/MeArm/MeArm) · M2 [fork ผู้แก้](https://makerworld.com/en/models/86531?from=search) · M3 [IK/แกน](https://github.com/MeArm/MeArm-Arduino) · M4 [ราคาชุด/สิ่งไม่รวม](https://shop.mearm.com/products/mearm-maker-kit-cut-your-own)

ตรวจเว็บและ source/API trees แบบ read-only; ไม่ดาวน์โหลด archive มาประกอบ/ทดสอบ โมเดล Thingiverse/MakerWorld บางหน้าอ่านไม่ได้ จึงแยกหลักฐานว่าผู้สร้างให้ลิงก์จากการยืนยันว่า archive ครบ เปิด CAD ได้ หรือพิมพ์ได้จริง

ถัดไปเมื่ออนุมัติช่วงตรวจแบบ: เลือกฐานตามท่าข้อมือที่จำเป็น → ตรวจสิทธิ์ไฟล์ฉบับที่จะใช้ → BOM ส่งถึงไทย → ก้ามเปิดครอบคลุมบล็อก/โหลด/พื้นที่ → validate model บน ASUS → วัดตำแหน่งจากภายนอก สำหรับ hobby PWM servos ต้องคิดต้นทุนเพิ่มหากต้องการมุมวัดจริง ไม่มีผลความแม่นยำ/latency/หยิบ–วาง/contact/tracking loss ในรายงานนี้
