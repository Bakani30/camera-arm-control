---
name: research-workflow
description: Plan and update the camera arm control research project while preserving confirmed scope, open decisions, and evidence boundaries.
---
# Research workflow
หา project root จาก AGENTS.md; path ด้านล่างอ้างจาก root

อ่าน docs/current-state.md และ docs/research/03-DECISIONS-GLOSSARY.md ก่อนเปลี่ยนแผน อ่าน master/roadmap เฉพาะหัวข้อที่เกี่ยวข้อง

- แยก confirmed, proposed, measured และ unresolved ให้เห็น
- เปลี่ยน requirement ตามคำสั่งล่าสุดแล้วบันทึกสิ่งที่แทนที่; ไม่ยืนยันเทคโนโลยีจากชื่อในรายการแนะนำ
- งาน AI ต้องเริ่มจาก baseline failure และเลือกหนึ่งปัญหาที่วัดได้ ไม่เพิ่ม AI เพื่อให้ชื่อโครงการดูใหม่
- ส่งข้อเสนอพร้อมเกณฑ์ผ่าน ทรัพยากร และผลต่อเวลา/งบ
- เมื่อได้รับคำสั่ง implementation ให้ทำงานที่ได้รับ ไม่ใช้เอกสารเก่าที่บอก “ยังไม่เริ่ม” เป็นการห้ามถาวร
- เก็บเนื้อหาวิจัยใน docs/research; current-state เก็บความคืบหน้า ไม่ทำสำเนา master ใหม่ทุกครั้ง

งานแรกดู docs/tasks/P001-feasibility.md การทดลองใช้ skill experiment-evidence; การแบ่งงานใช้ agent-orchestration เฉพาะเมื่อเกี่ยวข้อง
