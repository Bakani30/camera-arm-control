---
name: agent-orchestration
description: Scope subagent assignments, coordinate file ownership, and prepare evidence-backed handoffs in the camera arm control project.
---
# Agent orchestration
หา project root จาก AGENTS.md; path ด้านล่างอ้างจาก root

อ่าน docs/workflows/agent-work.md และใช้ docs/templates/task-packet.md เมื่อแบ่งงาน

1. ระบุ uncertainty/outcome และงานที่ทำอิสระได้ก่อนเลือก worker งานเล็กทำตรงได้
2. ส่งบริบทเท่าที่จำเป็น พร้อม exact owned files, baseline, acceptance, verification, dependencies และ stop rule
3. บอก worker ว่ามีผู้อื่นใน workspace ห้ามย้อนงานอื่น Child ไม่ spawn ต่อ ใช้ role/model ที่ runtime มีจริงและอนุญาต ไม่สร้างชื่อ preset ขึ้นเอง
4. ผู้คุมงานเก็บ shared contracts และ integration owner หนึ่งคน
5. เมื่อผลกลับ ตรวจหลักฐานและผลต่อส่วนเชื่อมก่อนรับ เปลี่ยน ownership ผ่านผู้คุมงาน
6. ส่งต่องานด้วยสถานะจริงและ next step ใน packet; current-state อัปเดตเฉพาะความคืบหน้าสำคัญ

หาก runtime ไม่รองรับ delegation ให้ทำตาม packet แบบ solo และระบุว่าไม่มี independent agent review คำอธิบายบทบาทไม่ใช่การติดตั้ง agent
