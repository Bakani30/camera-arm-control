# ที่มาวิธีทำงาน
ตรวจต้นฉบับในเครื่องวันที่ 2026-09-18 ที่ /Users/mr.coresynapse/Downloads/rally

| แหล่งที่อ่าน | หลักที่นำมาปรับ |
|---|---|
| AGENTS.md §§2–4,7 | navigation ตามงาน, authority, ขอบเขตไฟล์, ตรวจผลก่อนจบ |
| skills/agent-orchestration/SKILL.md | bounded discovery, shared-worktree ownership, independent review, handoff |
| skills/agent-orchestration/references/task-packet.md | packet ระบุ baseline/acceptance/dependencies/stop rule |
| CONTEXT.md | เจ้าของงานชัด คนรับผิดชอบผล AI และทีมขนานจากข้อตกลงร่วม |
| CLAUDE.md | เปรียบเทียบกติกา runtime; ไม่ยก delegation-first เก่ามาทับ Codex root |

นำแนวคิดมาร่างใหม่สำหรับโครงการวิจัย ไม่คัด stack, ข้อมูลระบบ, remote identifiers, secrets หรือคำสั่ง deploy ของ Rally ไม่ติดตั้ง Hermes/Graft ไม่ผูก agent role กับ model preset ของ Rally และไม่อ้างว่าบทบาทเหล่านั้นพร้อมใช้ในเครื่องนี้

โครงสร้างใช้ root AGENTS.md และ .agents/skills/*/SKILL.md พร้อมเอกสารอ้างอิงภายใน จึงย้ายทั้งโฟลเดอร์ได้ ไม่ต้องพึ่ง path ของ Rally เพื่อทำงานต่อ
