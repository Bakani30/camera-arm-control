# R001 — สำรวจฐานแขนพิมพ์เองเพื่อวิจัย
- วันที่: 2026-10-02 / สถานะ: ค้น วิเคราะห์ และรวมผลแล้ว; ยังไม่เลือกรุ่น/ทดลอง
- คำขอ: ผู้ใช้ให้ค้นเพิ่มจาก Hugging Face และแหล่งอื่นโดยใช้ subagent; ส่งรายชื่อตัวเลือกพร้อมหลักฐานและข้อประเมินสำหรับการดัดแปลง
- ขอบเขต: งานวิจัยกล้อง RGB ควบคุมแขน มือเดียวก่อน งานจริงลูกบล็อก; งบฮาร์ดแวร์รวม 10,000 บาท มีเครื่องพิมพ์ 3D ทีม 3 คน 6–8 เดือน ใช้ ASUS ทุกส่วนรวมซิม M1 พัฒนา/ML ไม่ซิม
- ผู้ใช้ยืนยัน: ไม่บังคับโอเพ่นซอร์ส ขอใช้วิจัยได้ มีไฟล์พิมพ์ และใช้เป็นฐานปรับแต่ง/เสริมได้ ไม่จำเป็นต้องทำตามแบบ/BOM เดิม
- Baseline: HEAD 63b12ec610130ce3d38cca3e45953eb44092d9f1; มีการแก้ docs/current-state.md, docs/research/03-DECISIONS-GLOSSARY.md, docs/tasks/P001-feasibility.md และไฟล์ใหม่ docs/research/07-HARDWARE-COMPARISON.md จากการวางแผนก่อนหน้า ต้องรักษาไว้
- Integration owner: root; root เป็นผู้แก้ current-state, packet นี้ และ docs/research/08-HARDWARE-OPTIONS.md
- งานค้นเพิ่มของ root: AM-ARM200 และ PingTi Arm; owned file docs/research/hardware-notes/2026-10-02-extended-lerobot.md เพื่อไม่ซ้อนงาน hf_options

## งานอิสระและ ownership
| Owner | คำถาม | Owned file |
|---|---|---|
| hf_options | นอกจาก SO-101 มีฐานแขนใน Hugging Face/LeRobot ใดที่พิมพ์และเชื่อมควบคุมได้ | docs/research/hardware-notes/2026-10-02-huggingface.md |
| diy_options | ฐาน DIY หลายแกน เช่น Thor, PAROL6, Moveo, AR4, ARCTOS เหมาะกับงบ/เวลาหรือไม่ | docs/research/hardware-notes/2026-10-02-diy-arms.md |
| budget_options | แบบประหยัด MeArm, EEZYbotARM, LittleArm, UMIRobot มีไฟล์/การควบคุม/ข้อจำกัดอะไร | docs/research/hardware-notes/2026-10-02-budget-arms.md |

แต่ละ agent อ่าน AGENTS.md, docs/current-state.md และ docs/research/07-HARDWARE-COMPARISON.md ตามจำเป็น เขียนได้เฉพาะ owned file; ไม่แก้โค้ด/ไฟล์ผู้อื่น ไม่ย้อนงานเดิม และไม่แตก subagent ต่อ

## เกณฑ์ยอมรับและวิธีตรวจ
- ใช้แหล่งหลัก: ผู้สร้างโครงการ GitHub/Hugging Face เอกสารผลิตภัณฑ์/แบบ/ไลเซนส์/บทความของผู้สร้าง มี URL รองรับข้อเท็จจริง
- แต่ละรุ่น: ลิงก์ไฟล์ STL/CAD, จำนวนแกนแขนแยกจากก้ามและจำนวนมอเตอร์, hardware/controller/interface, feedback, ซิม/URDF/MJCF, ราคาพร้อมฐาน/สกุลเงิน/สิ่งที่ไม่รวม, สิทธิ์ใช้งาน, ความยากในการดัดแปลง
- ไม่ถือว่ามีไฟล์หรือโค้ดเท่ากับทดสอบ Windows/กล้อง/ML/contact สำเร็จ; แยกต้นฉบับกับแบบดัดแปลง ราคา BOM กับชุดขาย และ feedback ข้อต่อกับความแม่นยำปลายแขน
- คืน 2–3 รุ่นที่ควรศึกษาต่อและตัวที่ควรพัก พร้อมเหตุผลตามหลักฐาน; ข้อมูลไม่พบระบุว่ายังไม่ยืนยัน
- Stop rule: หากไม่มี CAD/ราคา/ข้อมูลสำคัญหลังค้นแหล่งหลักแบบเจาะจง ให้ระบุ unresolved และส่งกลับ ไม่เดาและไม่ค้นไม่สิ้นสุด
- Authorization: ค้นเว็บ วิเคราะห์ และเขียนบันทึกเท่านั้น ไม่มีสิทธิ์ซื้อ ส่งข้อความผู้ขาย ติดตั้ง พิมพ์ หรือขยับฮาร์ดแวร์
- Verification: root ตรวจ claim สำคัญจาก source ที่ agent ส่งกลับและตรวจเอกสาร ไม่มีการทดสอบ runtime/ฮาร์ดแวร์จากงานนี้

## ผลส่งกลับ
- Agent ทั้งสามส่งรายงานครบใน owned files; root รวมใน docs/research/08-HARDWARE-OPTIONS.md และเพิ่ม source notes AM-ARM200/PingTi
- ข้อเสนอ shortlist: SO-101, AM-ARM200, ElRobot; Thor/UMIRobot เป็นสำรองตามข้อแลกเปลี่ยน รายชื่อยังไม่ใช่ผู้ใช้เลือกรุ่นแล้ว
- ตรวจ claim สำคัญจาก primary source: AM BOM/URDF/readback, ElRobot ราคา/Windows Planned, UMI commanded-state แทน measured angle, Thor CAD/ราคา/แกน; ข้อมูลขัดกันหรือเข้าถึงไม่ได้บันทึก unresolved
- ตรวจเอกสารและลิงก์ภายในโดย root; ไม่ซื้อ/ติดตั้ง/ติดต่อ/พิมพ์/ทดลอง ผล runtime/contact/hardware ทั้งหมด NOT RUN
- ผลตรวจ: git diff --check ผ่าน; ตรวจ UTF-8/newline/whitespace ของรายงาน/packet 6 ไฟล์และลิงก์ภายใน 7 จุดผ่าน การตรวจนี้เป็น document verification ไม่ใช่ runtime test
- งานต่อ: BOM ส่งถึงไทยของแบบที่จะสร้างจริงและความเข้ากันได้กับบล็อก ก่อนเลือกรุ่นและจุดดัดแปลง

## Follow-up: งบมอเตอร์ผสม 2026-10-02
- ผู้ใช้ยืนยัน 3,000 บาท ± เฉพาะมอเตอร์ อุปกรณ์อื่นแยก; งบฮาร์ดแวร์รวมเดิม 10,000 บาทไม่ถูกแทนที่ ช่วง ± ยังไม่ล็อก
- ใช้ agent budget_options เดิมค้นราคาไทยแบบเจาะจง; ownership เพิ่มเฉพาะ docs/research/hardware-notes/2026-10-02-servo-prices.md ไม่แก้ไฟล์ผู้อื่นหรือแตก agent ต่อ
- root ตรวจหน้าร้าน MG996R/TD8120MG/MG90S/SC15 และ primary SC15 feedback/limits; รวมใน docs/research/09-HYBRID-SERVO-BUDGET.md และอัปเดต decision/current-state/ลิงก์รายงานรวม
- ผลค้น: ชุดผสม 7 มอเตอร์ 3,050/3,145 บาท หรือ 6 มอเตอร์ 2,970 บาท; root เพิ่ม PWM ล้วน 7 มอเตอร์ 1,735 บาทเป็นฐานเทียบ ทุกชุดเป็น arithmetic ตามราคา SKU ไม่มีผลรับโหลด/ความแม่นยำ
- ข้อจำกัด: variant/ช่วงมุมบางหน้าร้านไม่ตรงผู้ผลิต, readback มีเพียง bus joints, ก้าม micro/แรงบิดข้อต่อยังไม่ยืนยัน; ราคาไทย STS3215/DS3218 ตรง variant ยัง unresolved จบค้นตาม stop rule
- ตรวจเอกสาร/arithmetic/ลิงก์ภายในเท่านั้น ไม่ทดสอบ runtime; การประกอบ ซิม ฮาร์ดแวร์ ML integration และหยิบ–วาง NOT RUN
- งานต่อ: geometry/โหลดและจำนวนแกนที่โจทย์ต้องใช้ → เลือกข้อที่ควรวัด/แรงบิด → BOM ทั้งแขนและการแก้แบบก่อนตัดสินรุ่น
- Steering ล่าสุด: ผู้ใช้เน้นการหมุน/ตอบสนองเร็ว/แม่นผ่านกล้อง ไม่ยกของหนัก; root ปรับเกณฑ์ในรายงานงบเป็นช่วงหมุน/latency ทั้งระบบ/ความคลาดเคลื่อนปลายแขน/repeatability และยังคำนวณโหลดโครงเอง ไม่ถือว่า readback เท่ากับผลแม่นยำ
- ผลตรวจ follow-up: git diff --check ผ่าน; ตรวจ UTF-8/newline/whitespace ของเอกสาร 4 ไฟล์ ลิงก์ภายใน 9 จุดและ arithmetic 4 ชุดผ่าน เป็น document verification เท่านั้น
