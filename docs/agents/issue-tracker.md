# Issue tracker สำหรับ agent
ไฟล์นี้คือการตั้งค่าที่สกิล `to-spec`, `to-tickets`, `triage`, `spec-review`, `wayfinder` และ `implement` อ่าน (แทนคำสั่ง `/setup-matt-pocock-skills`)

## ที่เก็บงาน
- GitHub Issues ของ `Bakani30/camera-arm-control` (repo private)
- ใช้ `gh` CLI: `gh issue list`, `gh issue view <n>`, `gh issue create`, `gh pr view <n>`
- ทุก issue ต้องเขียนว่า "เสร็จแปลว่าอะไร" และระบุโรลด้วย label เลน
- การสร้าง issue, comment หรือเปลี่ยน label เป็นการเผยแพร่ ให้ถามผู้ใช้ก่อนทุกครั้ง

## Label
| บทบาทในสกิล | label จริง |
|---|---|
| category `bug` | `bug` |
| category `enhancement` | `enhancement` |
| state `needs-triage` | `needs-triage` |
| state `needs-info` | `needs-info` |
| state `ready-for-agent` | `ready-for-agent` |
| state `ready-for-human` | `ready-for-human` |
| state `wontfix` | `wontfix` |

label เลนของโปรเจคนี้ (ใส่เพิ่มจาก category/state): `lane:A` มือ→เป้าหมาย · `lane:B` เป้าหมาย→ซิม · `lane:C` ภาษากลาง + แขนจริง · `team` งานร่วม

ถ้า label ยังไม่มีใน repo ให้เสนอคำสั่ง `gh label create` ให้ผู้ใช้อนุมัติก่อน

## ศัพท์และการตัดสินใจ
- อภิธานศัพท์และ decision log (ทำหน้าที่แทน `CONTEXT.md` และ ADR): `docs/research/03-DECISIONS-GLOSSARY.md`
- ภาพรวมและเส้นเวลา: `docs/roadmap.md`
- สัญญาข้อมูลระหว่างเลน: `docs/interfaces/`
- เรื่องที่ตัดออกแล้ว (ใช้แทน `.out-of-scope/`): หัวข้อ "ขอบเขต" ใน `docs/roadmap.md` และ decision D19 D22
