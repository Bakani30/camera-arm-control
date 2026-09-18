---
name: experiment-evidence
description: Design, record, and review reproducible camera arm control experiments, including fair baseline comparisons and limits on simulation and AI claims.
---
# Experiment evidence
หา project root จาก AGENTS.md; path ด้านล่างอ้างจาก root

อ่าน docs/workflows/experiments.md และหัวข้อเกี่ยวข้องใน docs/research/02-EXPERIMENTS-ROADMAP.md ใช้ docs/templates/experiment-record.md เก็บหลักฐาน

ก่อนรัน ระบุคำถาม config วิธีวัดและเกณฑ์สำเร็จ ถ้าขาดเครื่อง/data ให้ทำ protocol และติดป้าย NOT RUN ไม่กรอกผลสมมติ

ก่อนสรุป ตรวจว่า baseline และ AI ใช้เงื่อนไขเทียบกันได้ แยก train/test จริง รวม failed runs และระบุ n ของผู้ใช้/session/trial ให้ถูกต้อง

แยก multi-model support จาก unseen-robot learning, simulation จาก physical validation, smoothness จาก accuracy และ compute time จาก end-to-end latency

ส่งผลพร้อม artifact/config/environment และข้อจำกัด ถ้าหลักฐานไม่รองรับ hypothesis ให้รายงานผลลบ ไม่เปลี่ยน metric ย้อนหลังเพื่อให้ผ่าน
