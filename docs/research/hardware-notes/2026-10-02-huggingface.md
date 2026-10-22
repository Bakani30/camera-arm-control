# ฐานแขนจาก Hugging Face / LeRobot

ตรวจแหล่งหลัก 2026-10-02 · R001 · **สำรวจเอกสารเท่านั้น; ทุกการทดลอง NOT RUN**

เกณฑ์: กล้อง RGB มือเดียว → หยิบ–วางบล็อกเริ่ม 4–5 ซม.; น้ำหนัก/วัสดุยังไม่ล็อก มีเครื่องพิมพ์ งบฮาร์ดแวร์รวม 10,000 บาท ทีม 3 คน 6–8 เดือน ASUS ทำทุกส่วนรวมซิม; M1 พัฒนา/ML ไม่ซิม ราคาต่างประเทศด้านล่างไม่ใช่ราคาส่งถึงไทย และไม่แปลงเงินบาทโดยเดา

[รายการ HF](https://huggingface.co/docs/lerobot/en/third_party_robots) แยก core-supported กับ community plugin; ชื่ออยู่ในรายการไม่รับรอง Windows หรือการหยิบบล็อกของทีม

## 1. ElRobot — ตัวเลือกใหม่ที่ควรศึกษาต่อ

- **แบบ/แกน:** [STL](https://github.com/norma-core/norma-core/tree/main/hardware/elrobot/STL), [STEP](https://github.com/norma-core/norma-core/tree/main/hardware/elrobot/STEP), คู่มือ PDF ใน [README/BOM ผู้สร้าง](https://github.com/norma-core/norma-core/blob/main/hardware/elrobot/README.md); แขน **7 แกน + ก้าม 1**, ST3215 12V **8 ตัว** ไม่ใช่ 6+1 ตามบางเว็บรวบรวม ตรวจ URDF พบมอเตอร์ 01–07 ก่อนฐานก้าม; มอเตอร์ 08 ขับเฟืองและขาก้าม mimic สองข้าง
- **ควบคุม/feedback:** Waveshare Bus Servo Adapter A หรือบอร์ด Seeed; USB→serial motor bus มี [Station/Python API](https://github.com/norma-core/norma-core/blob/main/software/station/bin/station/README.md) และ [driver อ่าน RAM มอเตอร์](https://github.com/norma-core/norma-core/blob/main/software/drivers/st3215/src/port.rs) แยกข้อมูลรับกลับจากคำสั่ง ซอฟต์แวร์ผู้สร้างรองรับ macOS/Linux; Windows ยัง **Planned** ไม่พบ core LeRobot adapter เฉพาะ ElRobot ที่ยืนยันแล้ว
- **ซิม/ราคา/สิทธิ์:** [URDF + meshes](https://github.com/norma-core/norma-core/tree/main/hardware/elrobot/simulation) มี inertia/collision และ mimic; ยังไม่พบ MJCF/contact task บล็อกพร้อมใช้ README ประเมิน **~US$220/arm**, ไม่ใช่ยอด BOM ส่งไทยครบ; มอเตอร์ 8×~US$22 และกล้อง/PSU/บอร์ดมีรายการแยก ต้องตรวจการรวมยอดและกรณีซื้อสองแพ็กหกตัว ชิ้นพิมพ์ follower ~360g ตามผู้สร้าง [ไลเซนส์ hardware Apache-2.0](https://github.com/norma-core/norma-core/blob/main/hardware/elrobot/LICENSE); root monorepo MIT อย่าใช้แทนไลเซนส์โฟลเดอร์แบบ
- **ประเมิน:** แก้ปลายนิ้ว/ฐานง่ายกว่ารื้อข้อต่อ เพราะมี STEP และก้ามขนาน; การเปลี่ยนความยาว/มอเตอร์ต้องปรับ IK, limits และ URDF ความยากรวม **กลาง–สูงจาก integration บน Windows** ไม่มีผลความแม่นยำหลังดัดแปลง

## 2. Koch v1.1 — ตัวเทียบที่มีซิมและ feedback ชัด

- [แบบ follower STL/STEP/SolidWorks](https://github.com/jess-moss/koch-v1-1/tree/main/hardware/follower) พร้อม [BOM](https://github.com/jess-moss/koch-v1-1): **แขน 5 แกน + ก้าม 1**, XL430-W250 สองตัว + XL330-M288 สี่ตัว; Waveshare USB serial board มี 12V PSU และ voltage reducer เพราะใช้มอเตอร์ต่างแรงดัน
- [LeRobot source](https://github.com/huggingface/lerobot/blob/main/src/lerobot/robots/koch_follower/koch_follower.py) มี `get_observation` อ่าน `Present_Position` และ `send_action` เขียน `Goal_Position`; เป็นมุมมอเตอร์ที่อ่านกลับ ไม่ใช่ค่าที่สั่งหรือ ground truth ปลายแขน
- [MuJoCo Menagerie](https://github.com/google-deepmind/mujoco_menagerie/tree/main/low_cost_robot_arm) มี MJCF Koch v1.1, collision fingertips และ position actuators; limits เป็นค่าประมาณ ต้องใส่บล็อกและปรับฟิสิกส์เอง ยังไม่ทดลอง contact บน ASUS
- BOM follower **US$278** รวมรายการบอร์ด/PSU/reducer/สาย/เครื่องมือ ไม่รวมชิ้นพิมพ์ ส่งไทย ภาษี กล้อง/อะไหล่; leader อีก US$199 ไม่จำเป็นสำหรับกล้องควบคุมแขนเดียว Repo/โมเดล Apache-2.0; ใช้วิจัย/แก้แบบได้ โดยรักษาไลเซนส์/notice และบอกการแก้เมื่อแจก
- **ประเมิน:** ดัดแปลง **กลาง**; แบบครบแต่ระบบไฟซับซ้อนกว่า SO-101 งบเหลือสำหรับส่ง/อุปกรณ์ยังไม่ยืนยัน และ 5 แกนยังไม่เพิ่ม orientation อิสระครบ 6 มิติ

## 3. SO-100 — ตัวสำรองรุ่นเดิม ไม่ได้เพิ่มความหลากหลายมาก

[STL SO100](https://github.com/TheRobotStudio/SO-ARM100/tree/main/STL/SO100), [STEP](https://github.com/TheRobotStudio/SO-ARM100/tree/main/STEP/SO100), [BOM แขนเดียว US$123](https://github.com/TheRobotStudio/SO-ARM100/blob/main/SO100.md): 5 แกน + ก้าม, STS3215 หกตัว, USB serial board/PSU; ไม่รวมพิมพ์/ส่งไทย/ภาษี ใช้ [SO follower API](https://github.com/huggingface/lerobot/blob/main/src/lerobot/robots/so_follower/so_follower.py) อ่าน `Present_Position`; Apache-2.0 มี [Simulation ใน repo](https://github.com/TheRobotStudio/SO-ARM100/tree/main/Simulation) แต่ต้องตรวจโมเดลตรง SO100 ไม่ยก SO101 มาแทน ดัดแปลง **กลาง**; ผู้สร้างระบุเอกสาร SO100 **deprecated** และ SO101 ปรับสาย/ประกอบง่ายกว่า จึงพิจารณาเฉพาะมีอุปกรณ์เดิมหรือราคาจัดหาได้เปรียบจริง

## 4. Hope Jr arm + hand — พักฐานจริง; ศึกษาโครงสร้างภายหลัง

[STL](https://github.com/TheRobotStudio/HOPEJr/tree/main/Arm/3dprint%20files) / [STEP](https://github.com/TheRobotStudio/HOPEJr/tree/main/Arm/STEP) มีแบบแขน **7 แกน/7 มอเตอร์** และมือหลายนิ้ว **16 SCS0009** แยกจากแขน; ไม่ใช่ก้ามหนึ่งช่อง [BOM](https://github.com/TheRobotStudio/HOPEJr/blob/main/Arm/BOM.md) ระบุ SM8512BL×1, STS3250×2, STS3215×4 แต่ [LeRobot arm source](https://github.com/huggingface/lerobot/blob/main/src/lerobot/robots/hope_jr/hope_jr_arm.py) ใช้ SM8512BL×1 + STS3250×6: **ต้องปิดความขัดแย้ง BOM/code**

URT-1 USB board สำหรับแขน, Waveshare สำหรับมือ, PSU 12V/5A และ 5V/4A; API อ่าน `Present_Position` ไม่ใช่ feedback ท่านิ้ว/แรงสัมผัสที่ปลายเอ็นโดยตรง [HF docs](https://huggingface.co/docs/lerobot/en/hope_jr) ระบุ record/replay/train ยัง experimental ต้นทุนครบแขน+มือส่งไทย **unresolved**; BOM ไม่มีราคารวม ไม่ใช้ราคาหุ่น humanoid ทั้งตัวแทน ตรวจ tree พบ URDF ใน `Humanoid/` แต่ยังไม่ยืนยันซิมตรง `Arm/` รุ่นนี้และ contact มือ [Repo](https://github.com/TheRobotStudio/HOPEJr) ไม่มี root/Arm LICENSE ที่ตรวจพบ; `Humanoid/LICENSE` ไม่ใช่หลักฐานสิทธิ์ทุกแบบ Arm ความยาก **สูง** จากเอ็น/มือ/หลาย bus; ยังไม่ผ่านเกณฑ์แบบพร้อมวิจัย

## 5. OpenArm — เกินงบฐานแรกชัดเจน

[CAD/STL/STEP และ release ผู้สร้าง](https://github.com/enactic/openarm_hardware) มีทั้งพิมพ์และโครงอลูมิเนียม/สเตนเลส; 7 แกน + ก้าม รวม 8 มอเตอร์ Damiao ต่อแขน [LeRobot API](https://github.com/huggingface/lerobot/blob/main/src/lerobot/robots/openarm_follower/openarm_follower.py) ผ่าน CAN/CAN-FD อ่านตำแหน่ง และ optional velocity/torque จาก motor state ไม่ใช่ load cell ปลายแขน มี [URDF](https://github.com/enactic/openarm_description) และ [MJCF/collision](https://github.com/enactic/openarm_mujoco)

[HF](https://huggingface.co/docs/lerobot/en/openarm) ระบุ **US$6,500 ระบบสองแขน** ไม่ใช่ราคาหนึ่งแขน ไม่ใช่ใบเสนอราคาส่งไทย; hardware ใช้ CERN-OHL-S-2.0 อนุญาตแก้แบบแต่มีเงื่อนไข source/การส่งต่อ; software Apache-2.0 **Linux only**, Windows ยังไม่ทดสอบตาม HF ความยาก **สูง** และการพิมพ์ casing ไม่ได้ลดราคามอเตอร์/ชิ้นโลหะให้เข้ากับงบเรา

## 6. Nextis AIRA-3D — พักเพราะมอเตอร์แพง

[STEP follower](https://github.com/robertorobotics/Nextis-AIRA-3D/tree/main/hardware/step/follower) ดาวน์โหลดได้; ใน tree ที่ตรวจไม่พบชุด STL จึงต้อง export จาก STEP [README](https://github.com/robertorobotics/Nextis-AIRA-3D) เรียก 7DoF แต่หมายถึง **แขน 6 แกน + ก้าม 1** Damiao 7 ตัว ผ่าน USB-CAN, MIT impedance control; [API](https://github.com/robertorobotics/Nextis-AIRA-3D/blob/main/src/lerobot_robot_aira/robots/aira_follower.py) อ่าน `sync_read_position` และส่ง target มุม Force feedback ยังเป็นแผน ไม่ใช่สิ่งที่ผ่านแล้ว

[BOM](https://github.com/robertorobotics/Nextis-AIRA-3D/blob/main/hardware/BOM.md) มอเตอร์ follower **~US$1,515** ยังไม่รวมบอร์ด/PSU/พิมพ์/อุปกรณ์; README full teleop kit **€2,000–2,500 / US$2,200–2,750** รวมส่ง/ภาษีตามประมาณการผู้สร้าง ไม่รับรองปลายทางไทย Apache-2.0; plugin early access ยังไม่ทดสอบครบโดยชุมชน ไม่พบ URDF/MJCF/contact task ใน repo ที่ตรวจ ความยาก **สูง**; เปลี่ยนเซอร์โวราคาต่ำคือการออกแบบ transmission/mount/control ใหม่ ไม่ใช่รับสมรรถนะเดิมมา

## ข้อเสนอและช่องว่างที่ต้องปิด

1. **คง SO-101 เป็น baseline เทียบตาม 07; เพิ่ม ElRobot เป็นตัวเลือกนำใหม่** เมื่ออยากได้ 7 แกน ต้องประเมิน adapter Windows, ก้าม 4–5 ซม., โหลดและ BOM จริงก่อนเลือกรุ่น
2. **Koch v1.1 เป็นตัวเทียบมี feedback/contact model** หาก BOM ส่งถึงไทยเหลืองบ; ไม่เสนอซื้อ leader เพิ่มโดยไม่มีเหตุผล
3. **SO100 สำรองตามราคา/อุปกรณ์ที่มี**; พัก Hope Jr, OpenArm, AIRA สำหรับแขนจริงแรก

[LeKiwi](https://huggingface.co/docs/lerobot/en/lekiwi) เป็น mobile manipulator เพิ่มฐานล้อให้แขน SO100/SO101 จึงไม่เป็นแขนใหม่สำหรับโต๊ะ; Reachy 2/Unitree G1/Earth Rover พักจากการคัดฐานแขนโต๊ะ รายการ StarAI/NexArm มี plugin แต่ยังไม่ยืนยัน printable CAD/license ของฮาร์ดแวร์ จึงไม่ยก software license มาอนุญาตแบบ

SO-ARM107: [repo ผู้สร้างที่ index ชี้](https://github.com/ajinkyagorad/SO-ARM107) ได้ 404 ทั้งเว็บ/API/raw; ค้นชื่อเจาะจงไม่พบแหล่งผู้สร้างใหม่ → **unresolved และหยุดค้น** ส่วนลิงก์ ElRobot เก่า 404 แต่พบ monorepo ผู้สร้างข้างต้นแล้ว

ตรวจเอกสาร: เปิดแหล่งหลักและเทียบ README/BOM/license/code; ตรวจ GitHub tree และอ่าน ElRobot URDF (7 joints ก่อนก้าม; สอง jaw mimic มอเตอร์ 08) ไม่ติดตั้ง/ซื้อ/พิมพ์/ติดต่อผู้ขาย ไม่ทดสอบ Windows/ซิม/กล้อง/ML/ฮาร์ดแวร์ ค่า readback มอเตอร์ไม่รับรองความแม่นยำปลายแขน การปรับแบบต้องประเมินและวัดใหม่
