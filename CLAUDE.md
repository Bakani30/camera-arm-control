# CLAUDE.md — Camera Arm Control

@AGENTS.md

## เริ่มทุกเซสชัน
1. **หาโรลของผู้ใช้:** เทียบ `git config user.name` หรือ `gh api user -q .login` กับ `docs/team/roster.md` ถ้าไม่พบ ให้ถามว่าผู้ใช้ถือโรล A, B หรือ C แล้วเสนอให้เพิ่มชื่อใน roster ผ่าน PR
2. **โหลดภาพรวม:** อ่าน `docs/roadmap.md` และการ์ดโรลของผู้ใช้ใน `docs/team/roles.md` และ `docs/current-state.md`
3. **บอกผู้ใช้สั้นๆ:** โรลของเขา, งานที่ ready ของโรลนั้นใน `docs/backlog.md`, และ sprint ปัจจุบันตามเส้นเวลาใน roadmap
4. ทำงานในเลนของโรลนั้นเป็นหลัก ถ้างานต้องแก้ไฟล์ของเลนอื่นหรือภาษากลาง (`docs/interfaces/`) ให้บอกผู้ใช้ว่าต้องคุยกับเจ้าของเลน หรือรอวันจันทร์ตาม `docs/team/working-agreement.md`

## สไตล์การตอบ (ทั้งทีม)
- ตอบภาษาไทยด้วยสไตล์ pordee: โหลดสกิล `pordee:pordee` ในข้อความแรกของเซสชัน แล้วใช้ทุกข้อความ
- ถ้าไม่มีปลั๊กอิน pordee ให้ตอบไทยกระชับตามหลักเดียวกัน: ไม่มีคำลงท้ายสุภาพ ไม่มีคำฟุ่มเฟือย ประโยคสั้น ศัพท์เทคนิคคงภาษาอังกฤษ
- ผู้ใช้สั่ง "หยุดพอดี" หรือ "พูดปกติ" ให้กลับเป็นภาษาไทยปกติจนจบเซสชัน
- คำเตือนความปลอดภัย, ขั้นตอนที่ลำดับสำคัญ, และคำสั่งที่ย้อนไม่ได้ ให้เขียนไทยปกติเต็มประโยค
- โค้ด, ชื่อไฟล์, commit message, PR description และ code comment เป็นภาษาอังกฤษ

## สกิลที่ใช้ในโปรเจคนี้
สกิลอยู่ใน `.claude/skills/` (ใช้ได้ทันทีเมื่อเปิด repo) และในปลั๊กอินที่ `.claude/settings.json` เปิดไว้ ถ้าไม่แน่ใจว่าใช้สกิลไหน ใช้ `ask-matt`

| สถานการณ์ | สกิล |
|---|---|
| เริ่มฟีเจอร์หรืองานใหม่ที่ยังไม่ชัด | `superpowers:brainstorming` แล้ว `superpowers:writing-plans` |
| เขียนโค้ดหรือแก้บั๊กแบบ test-first | `tdd` หรือ `superpowers:test-driven-development` |
| บั๊กยาก, ผลแปลก, ช้าผิดปกติ | `diagnosing-bugs` หรือ `superpowers:systematic-debugging` |
| ก่อนบอกว่างานเสร็จ | `superpowers:verification-before-completion` |
| ทดลองไอเดียแบบทิ้งได้ | `prototype` |
| ออกแบบโมดูลหรือ interface | `codebase-design` |
| ศัพท์ของโปรเจค, บันทึก decision | `domain-modeling` (ใช้ `docs/research/03-DECISIONS-GLOSSARY.md` แทน CONTEXT.md/ADR) |
| ทดสอบแผนให้แน่น | `grilling`, `grill-me`, `grill-with-docs` |
| แตกงานเป็น issue / spec / ticket | `to-spec`, `to-tickets`, `triage`, `wayfinder` (ตั้งค่าที่ `docs/agents/issue-tracker.md`) |
| ลงมือทำจาก spec หรือ ticket | `implement` |
| รีวิว diff ก่อน PR | `spec-review` |
| merge conflict | `resolving-merge-conflicts` |
| เรียนเรื่องใหม่ เช่น IK, MuJoCo, OpenCV calibration | `teach` |
| ค้นแหล่งหลักแล้วสรุป | `research` |
| ส่งต่องานให้เซสชันอื่น | `handoff` |
| แก้ CLAUDE.md, AGENTS.md หรือสกิล | `writing-for-agents` |
| งานวิจัย, การทดลอง, การแบ่งงาน | สกิลโปรเจคใน `.agents/skills/` ตามตารางใน AGENTS.md |

## แบ่งงานและ PR
- **หนึ่ง PR หนึ่งเรื่อง:** แยก PR เมื่อเป็นเรื่องอื่น ไฟล์อื่น และไม่ต้อง deploy พร้อมกัน ส่วนฟีเจอร์เดียวข้ามหลายชั้น, การแก้บั๊กกับเทสต์ของมัน และงานที่ต้องส่งพร้อมกัน ให้อยู่ PR เดียวกัน
- **เจองานนอกเรื่องระหว่างทำ:** ถ้าเรื่องเดียวกันหรือไฟล์เดียวกัน ให้รวมใน PR ปัจจุบัน ถ้าไม่ใช่ ให้เสนอเป็นงานแยก แล้วทำงานเดิมต่อ
- **ชื่อ branch:** `<โรล>/<เรื่อง>` เช่น `a/metric-mapping`
- ห้าม commit, push หรือเปิด PR จนกว่าผู้ใช้สั่ง
- ก่อนเปิด PR ต้องรัน `python -m unittest discover -s tests -v` ผ่าน และแนบผลใน PR

## ฮาร์ดแวร์
ห้ามรันโค้ดที่ขยับแขนจริงเอง ให้บอกคำสั่งให้ผู้ใช้รัน โดยมีคนคุมหน้างาน ปุ่มหยุดอยู่ในมือ และพื้นที่ปลอดคน การผ่านในซิมไม่ได้แปลว่าอนุญาตให้ขยับแขนจริง
