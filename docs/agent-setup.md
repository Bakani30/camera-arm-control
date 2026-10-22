# ตั้งค่า Claude Code ให้ทำงานแบบเดียวกันทั้งทีม
ทำครั้งเดียวต่อเครื่อง (Windows)

## 1. สิ่งที่ต้องมี
- Git, Python 3.11 64-bit (ตามคู่มือหลักใน README)
- [Claude Code](https://claude.com/claude-code) ล็อกอินบัญชีของตัวเอง
- **Node.js LTS** (ปลั๊กอิน pordee ใช้ hook ที่รันด้วย `node`)
- GitHub CLI `gh` แล้วรัน `gh auth login` (สกิลงานทีมใช้ GitHub Issues)

## 2. เปิด repo ครั้งแรก
```powershell
git pull --ff-only
claude
```
- Claude Code จะถามว่าเชื่อถือโฟลเดอร์นี้ไหม และจะเสนอติดตั้ง marketplace + ปลั๊กอินที่ `.claude/settings.json` เปิดไว้ (superpowers, pordee) ให้ตอบตกลง
- ถ้าไม่ถาม ให้พิมพ์ `/plugin` แล้วติดตั้ง `superpowers` จาก `claude-plugins-official` และ `pordee` จาก marketplace `kerlos/pordee`
- สกิลใน `.claude/skills/` ใช้ได้ทันทีโดยไม่ต้องติดตั้ง

## 3. เพิ่มชื่อตัวเองใน roster
แก้ `docs/team/roster.md` ใส่ชื่อ, GitHub และผลของ `git config user.name` ในแถวโรลของตัวเอง แล้วส่ง PR ให้ C อนุมัติ หลังจากนั้น Claude จะรู้เองว่าคุณถือโรลไหนตั้งแต่ข้อความแรก

## 4. เช็กว่าใช้ได้
พิมพ์ในเซสชันใหม่: `ฉันเป็นโรลอะไร และงานแรกของฉันคืออะไร`

Claude ควรตอบเป็นไทยสั้นๆ บอกโรล, งาน ready ของโรลนั้นจาก `docs/backlog.md` และ sprint ปัจจุบัน ถ้าตอบไม่ได้ ให้เช็กว่าเปิด Claude ในโฟลเดอร์ repo และมีชื่อใน roster แล้ว

## ไฟล์ที่ควบคุมพฤติกรรม Claude ใน repo นี้
| ไฟล์ | หน้าที่ |
|---|---|
| `CLAUDE.md` | ขั้นตอนเริ่มเซสชัน, สไตล์ตอบ, ตารางสกิล, กติกา PR และฮาร์ดแวร์ |
| `AGENTS.md` | กติกาโครงการสำหรับทุก agent (Claude, Codex ฯลฯ) |
| `.claude/settings.json` | ปลั๊กอินและสิทธิ์คำสั่งที่ใช้ร่วมกัน |
| `.claude/skills/` | สกิลวิศวกรรมที่คัดมาให้ทีม |
| `.agents/skills/` | สกิลเฉพาะโครงการ (วิจัย, การทดลอง, การแบ่งงาน) |
| `docs/agents/issue-tracker.md` | ตั้งค่า GitHub Issues และ label ให้สกิลงานทีม |

การตั้งค่าส่วนตัว (เช่นสไตล์อื่น หรือสิทธิ์เพิ่มเติม) ให้ใส่ใน `.claude/settings.local.json` ซึ่งไม่ถูก commit
