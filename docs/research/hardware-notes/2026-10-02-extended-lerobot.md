# ตัวเลือกเพิ่มในระบบ LeRobot — ตรวจโดย root
วันที่ 2026-10-02 / ค้นเอกสารและอ่าน source เท่านั้น / runtime และฮาร์ดแวร์ NOT RUN

## AM-ARM200 — ควรเทียบต่อหากต้องการแขน 6 แกน
- แบบพิมพ์ [STL](https://github.com/liyiteng/AM-ARM/tree/main/am-arm200/stl) และแบบแก้ [STP](https://github.com/liyiteng/AM-ARM/tree/main/am-arm200/stp) มีจริงใน tree; repo Apache-2.0
- แขน 6 แกน + ก้ามหนึ่งแกน ยืนยันจาก joint list ใน [URDF](https://github.com/liyiteng/AM-ARM/blob/main/am-arm200/urdf/urdf/am-arm200.urdf) และ definition `am-follower-6dof` ใน [software fork](https://github.com/liyiteng/lerobot_alohamini/blob/main/src/lerobot/robots/so_follower/so_follower.py)
- [BOM แบบละเอียด](https://github.com/liyiteng/AM-ARM/blob/main/am-arm200/bom.md) ระบุ follower US$243.33: STS3215 12V สี่ตัว + STS3095 12V สามตัว, controller, PSU 12V 4A, cable ฯลฯ บางรายการสกรู/insert ไม่มีราคา และชิ้นพิมพ์ไม่ตีราคา จึงไม่ถือเป็นต้นทุนครบส่งไทย
- [README](https://github.com/liyiteng/AM-ARM) อ้างโหลด 1 กก./เอื้อม 52 ซม.; ยังไม่ใช่ผลวัดของทีม และไม่ใช้เป็นข้อสรุปของแบบที่เปลี่ยนมอเตอร์/โครง
- ซอฟต์แวร์ `lerobot_alohamini` มี definition มอเตอร์สามข้อต่อแรก STS3095, wrist สามแกน STS3215 และก้าม STS3215; อ่าน `Present_Position` และสั่ง `Goal_Position` ต้องใช้ fork/adapter ที่ตรง revision ไม่ถือว่าปัจจุบัน upstream รองรับแบบเดียวกันทั้งหมด
- พบ URDF จริง แม้ README ยังเขียน “URDF files coming soon”; source มี package mesh paths และทุก movable joint มี effort/velocity เป็นศูนย์ จึงเป็นข้อมูลเริ่มต้นที่ต้องตรวจ/ปรับก่อนใช้ซิม ไม่ใช่หลักฐานว่าจำลอง contact หรือแรงมอเตอร์สมจริงแล้ว
- ความขัดแย้งในเอกสาร: README บอก STS3095 อัตราทด 1/399 แต่ BOM ละเอียดบอก 1/345 ต้องเลือก part/revision ให้ชัดก่อนจัดหา
- **ข้อประเมิน:** มีฐาน CAD/โค้ด/แกนข้อมือที่น่าสนใจ แต่ค่า drive parts และงานปรับซิมสูงกว่า SO-101; ต้องทำ BOM ส่งไทยให้ครบก่อนยืนยันผ่านงบ 10,000 บาท

ตรวจ hardware tree/URDF ที่ commit `5b03af1ef6c80595bd988e0137cf8e7c35811eb6` (2026-06-18); อ่าน software จาก main ณ วันตรวจ ไม่ได้ติดตั้งหรือรัน

## PingTi Arm — เหมาะศึกษาหากต้องการระยะเอื้อมยาว
- [ผู้สร้างและ repo](https://github.com/nomorewzx/PingTi-Arm): มี [STL](https://github.com/nomorewzx/PingTi-Arm/tree/main/stl_3d_printing), [Fusion source](https://github.com/nomorewzx/PingTi-Arm/tree/main/fusion), URDF และไลเซนส์ Apache-2.0
- [URDF ที่ตรวจ](https://github.com/nomorewzx/PingTi-Arm/blob/main/Simulation/PingTi_Arm_v3/urdf/PingTi_Arm_v3.urdf) มี base yaw, shoulder pitch, elbow pitch, wrist pitch, wrist roll และก้าม: **5 แกนแขน + ก้าม**; จำนวนมอเตอร์มากกว่าแกนอิสระ ไม่ใช่แขน 6 แกนจากการนับมอเตอร์
- [BOM ผู้สร้าง](https://github.com/nomorewzx/PingTi-Arm/blob/main/docs/BOM_List.md) ใช้ STS3250 สองตัว + STS3215 12V หกตัว รวมที่เผยแพร่ US$261.09; ตารางไม่รวมวัสดุพิมพ์/PSU/ส่งไทย ตัวเลขรวมและรายการต้องจัดยอดใหม่ก่อนจัดซื้อ ไม่ใช้ตัวเลข US$150–200 จากเว็บไซต์รวมโครงการเป็นราคาผู้สร้าง
- BOM ระบุข้อจำกัดของ controller บางรุ่นในการขับแปดมอเตอร์ จึงต้องตรวจบอร์ดและการจ่ายไฟของชุดจริง ไม่เลือกเพียงเพราะชื่อ motor family ตรง SO-101
- มี [pingti_lerobot_bridge](https://github.com/nomorewzx/pingti_lerobot_bridge) และ variant standard/Lite ตาม README ปัจจุบัน; compatibility ของ revision ที่จะใช้ยังต้องตรวจ เคยมี [issue](https://github.com/nomorewzx/PingTi-Arm/issues/3) เรื่อง LeRobot API เปลี่ยน แต่ไม่ใช้ issue เก่าตัดสินว่า main ปัจจุบันยังเสีย
- README อังกฤษอ้าง 600 มม./500 กรัม ส่วนจีนอ้าง 660 มม./550 กรัม เป็นข้อมูลผู้สร้างที่ขัดกัน ต้องยึด revision แบบจริงและทดสอบโหลด/ระยะ ไม่รวม claim สองภาษาเป็นสเปกเดียว
- พบ URDF และ mesh assets; คู่มือ URDF อ้าง path เก่าที่ต่างจาก tree ปัจจุบัน ต้องแก้ทางโหลด/ตรวจ limits และ contact ก่อนเรียกพร้อมซิม
- **ข้อประเมิน:** มีประโยชน์ถ้าต้องเอื้อมไกล แต่เป็น 5 แกนเช่น SO-101 พร้อม drive parts และโครงใหญ่ขึ้น จึงพักไว้หลังโจทย์ระยะเอื้อมลูกบล็อกชัดเจน

ตรวจ hardware tree/URDF ที่ commit `9108729b79bc3509642386bb42948859ef4cbaf5` (2025-12-08); อ่าน bridge README จาก main ณ วันตรวจ ไม่ได้ทดลอง

## วิธีตรวจ
- ค้นเว็บใช้เว็บรวมเป็นทางหา repo แล้วอ้างข้อเท็จจริงจากผู้สร้างเท่านั้น
- ใช้ GitHub API ดู tree/commit และอ่าน raw Markdown/Python/URDF; parse XML เพื่อแยก joint ที่ไม่ fixed ไม่ใช่การรันซิม
- ไม่ดาวน์โหลด/เผยแพร่ CAD ของผู้สร้างใหม่ ไม่ติดตั้ง dependencies ไม่ซื้อหรือส่งข้อความ
