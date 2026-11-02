# M0 Relative Mapping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** เปลี่ยนตำแหน่งมือเมตรจาก `MetricHand` เป็น `EndEffectorTarget` แบบ relative/clutch และแสดงจุดเป้าสดบน mock arm

**Architecture:** `RelativeMapper` เป็น logic ล้วน รับค่าต่อเฟรมแล้วคืนตำแหน่ง สถานะ และ grip ส่วน `MappingSession` ต่อ mapper เข้ากับสัญญา, `MockArm` และไฟล์ replay เพื่อให้ `app.py` แก้น้อยและทดสอบได้โดยไม่มีกล้อง

**Tech Stack:** Python 3.11, unittest, OpenCV, MediaPipe, `arm_contracts` v0.1

**Spec:** `docs/superpowers/specs/2026-11-01-m0-relative-mapping-design.md`

## Global Constraints
- ค่าใน `MappingConfig`: start `(0.25, 0.0, 0.12)`, box min `(0.18, -0.12, 0.04)`, box max `(0.33, 0.12, 0.20)`, gain แนวขวาง/ดิ่ง `0.5`, gain แกนลึก `0.2`, deadband `0.015`, τ `80`/`120` ms, jump `0.15` ม./เฟรม, เพดาน `0.25` ม./วิ, gap `500` ms
- แกน: `Δy_robot = -g·Δx_hand`, `Δz_robot = -g·Δy_hand`, `Δx_robot = -g_depth·Δz_m`
- `orientation_wxyz` เป็น `null`, `frame` เป็น `robot_base`, `robot_id` เป็น `small_arm`, ห้ามใช้ `mode="fine"`
- `source` เป็น `live` จากกล้อง และ `script` จากข้อมูลจำลอง
- ไม่แก้ `camera_gestures/metric.py`, `camera_gestures/control.py`, `camera_gestures/replay.py`, `docs/interfaces/`
- ไม่สั่งแขนจริง ไม่เพิ่ม AI (D22) ไม่เพิ่ม dependency
- ไม่ใส่ `--mapping` แล้ว app ต้องทำงานเหมือนเดิม
- โค้ด, code comment และ commit เป็นภาษาอังกฤษ ทุก commit ลงท้ายด้วย `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`
- คำสั่งเทสต์บนเครื่องนี้ใช้ venv ที่มี cv2: `../camera-arm-control/.venv/bin/python` (เรียกย่อว่า `$PY`)

## Review Focus
1. มือถูกเลือกข้างใหม่ (ปุ่ม L/H) ระหว่างตาม: ต้องออกเป็น `enabled=false` ทันที — Task 3
2. กล้องตกเหลือ 10 fps: ยังตามได้ ไม่ถูกนับเป็นเฟรมกระโดด และไม่เกินเพดานความเร็ว — Task 1
3. มือสั่นตอนจุดชนมุมกล่อง: จุดต้องไม่เกินกล่องและไม่แกว่ง — Task 1
4. ปิดโปรแกรมก่อนเริ่มตาม: ไฟล์ replay ยังอ่านได้ — Task 2
5. มือชี้เข้ากล้อง: `HandControl` ยัง ACTIVE แต่ `MetricHand` ใช้ไม่ได้ ต้องส่ง `hold` — Task 3

---

### Task 0: เตรียม branch

ผู้ใช้เลือกให้ commit งานค้าง P002 ก่อนแยก branch ผู้ทำต้องแจ้ง GUNGUN ก่อนเริ่ม เพราะเป็นเลน A

**Files:** `camera_gestures/calibration.py`, `tests/test_metric.py`, `docs/camera-gestures.md`, spec, plan นี้

- [ ] **Step 1:** ดู `git diff` ของ 3 ไฟล์ P002 และรัน `$PY -m unittest discover -s tests` ต้องผ่าน 264 ตัว
- [ ] **Step 2:** commit 3 ไฟล์บน `a/metric-mapping` ถ้า diff ทำมากกว่าข้อความนี้ ให้ปรับข้อความให้ตรง

```bash
git add camera_gestures/calibration.py tests/test_metric.py docs/camera-gestures.md
git commit -m "Report calibration quality and warn on weak views (P002)"
```

- [ ] **Step 3:** แยก branch และ commit เอกสาร ห้าม add `docs/research/hardware-notes/2026-11-01-hand-scale-reference-survey.md` เพราะไม่อยู่ในงานนี้

```bash
git switch -c a/relative-mapping
git add docs/superpowers/specs/2026-11-01-m0-relative-mapping-design.md docs/superpowers/plans/2026-11-01-m0-relative-mapping.md
git commit -m "Add M0 relative mapping design and plan"
```

---

### Task 1: `RelativeMapper`

**Files:**
- Create: `camera_gestures/mapping.py`
- Test: `tests/test_mapping.py`

**Interfaces:**
- Produces:
  - `MappingConfig` (frozen dataclass): `start_m, box_min_m, box_max_m, gain_lateral, gain_depth, depth_deadband_m, tau_lateral_ms, tau_depth_ms, jump_m, max_speed_mps, max_gap_ms`
  - `MapperOutput = namedtuple('position_m grip mode enabled')`
  - `Ema(tau_ms)` มี `reset(value)` และ `update(value, dt_ms) -> float`
  - `RelativeMapper(config=MappingConfig(), filter_factory=Ema)`; `filter_factory(tau_ms)` คืน filter ที่มีเมธอดเดียวกับ `Ema`
  - `RelativeMapper.update(armed, position_m, z_m, active, code, now_ms) -> MapperOutput`
  - `RelativeMapper.reset() -> None`
  - `GRIP_BY_CODE = {'01': 0.0, '10': 1.0}`
  - `DRAG_TARGETS_M = ((0.25, 0.0, 0.12), (0.30, 0.08, 0.12), (0.30, -0.08, 0.12), (0.22, 0.06, 0.07), (0.28, -0.06, 0.17))`

- [ ] **Step 1: เขียนเทสต์ที่ fail**

ใช้ helper นี้ โดยตั้ง τ เป็น 0 ใน `MappingConfig` เมื่อเทสต์ไม่ได้ทดสอบ filter `Ema` ที่ τ ≤ 0 คืนค่าเข้าโดยตรง

```python
def run(mapper, frames, start=0, dt=33):
    """frames: (x, y, z) in metres, or None for a frame with no usable hand."""
    out = None
    for i, f in enumerate(frames):
        pos, z = (f[:2], f[2]) if f else ((0., 0.), None)
        out = mapper.update(True, pos, z, f is not None, '00', start + i * dt)
    return out
```

ชื่อเทสต์และสิ่งที่ตรวจ:

| เทสต์ | อินพุต | ต้องได้ |
|---|---|---|
| `test_axes_and_gain` | ทีละแกนจากจุดเริ่ม: x มือ +0.04, y มือ +0.04, `z_m` +0.055 | y −0.02, z −0.02, x −0.008 (`z_m` ขยับ 0.055 หัก deadband 0.015 เหลือ 0.04 × 0.2) |
| `test_first_frame_after_loss_does_not_move` | ตาม, `None`, กลับมาที่ `(0.3, 0.3, 0.7)` | ตำแหน่งเท่าเดิมในเฟรมที่กลับมา และ mode `track` |
| `test_gap_reanchors_even_when_active` | `now` ข้าม 900 ms และ `z` เปลี่ยน 0.5→0.6 โดย `active=True` (ไม่ถึงเกณฑ์ jump) | จุดไม่ขยับ, mode `track` |
| `test_clamp_has_no_windup` | มือลากเกินขอบ y 0.2 ม. แล้วถอย 0.01 | จุดอยู่ในกล่องตลอด และขยับกลับทันทีเมื่อถอย |
| `test_corner_noise_stays_in_box` | จุดอยู่มุมกล่อง มือสั่น ±2 มม. 100 เฟรม | ทุกแกนอยู่ในกล่อง |
| `test_speed_cap` | มือกระโดด 0.14 ม. ที่ dt 33 และ 100 ms | ก้าวต่อเฟรม ≤ `0.25 * dt / 1000` |
| `test_low_frame_rate_tracks` | มือ 0.5 ม./วิ ที่ 10 fps นาน 0.5 วิ | ทุกเฟรมเป็น `track` และจุดขยับ |
| `test_jump_frame_holds` | Δ มือ 0.2 ม. ในเฟรมเดียว แนวขวางหรือแกนลึก | เฟรมนั้น `hold`, เฟรมถัดไป `track` ที่จุดเดิม |
| `test_invalid_values_hold` | `nan`, `inf`, `z_m=None` ขณะ `active=True` | `hold`, ไม่ raise |
| `test_slow_depth_motion_passes_deadband` | Δz 1 มม./เฟรม 100 เฟรม | x ขยับราว `-0.2*(0.1-0.015)` |
| `test_depth_deadband_does_not_jump` | z กลับทิศ | ก้าว x ต่อเฟรมไม่เกิน `0.2 * Δz` ของเฟรมนั้น |
| `test_lag_is_dropped_on_loss` | ตามไม่ทัน แล้ว `None` แล้วกลับมานิ่ง 10 เฟรม | จุดไม่ขยับ |
| `test_reset_during_pause_moves_only_on_track` | ขยับจุดออก, `None`, `reset()`, `None` อีก, แล้วมีมือ | ระหว่าง `None` ตำแหน่งเดิม, หลังมีมือเลื่อนกลับไม่เกินเพดาน |
| `test_not_armed_is_disabled` | `armed=False` | `enabled=False`, mode `hold`, ตำแหน่งเดิม |
| `test_grip_holds_outside_tracking` | พักพร้อม code `10`→`01` แล้วกลับมา code `01` | grip ไม่เปลี่ยนจนกว่า code ต่างจากเฟรมแรกที่กลับมา |
| `test_ema_is_swappable` | `filter_factory` ที่บันทึกการเรียก | ถูกเรียกด้วย τ 80 และ 120 และ reset ตอนจับ reference |
| `test_same_frames_same_output` | เฟรมชุดเดียวกัน 2 mapper | ผลเท่ากันทุกตัว |

- [ ] **Step 2:** รัน `$PY -m unittest tests.test_mapping -v` ต้อง FAIL ด้วย `ModuleNotFoundError`
- [ ] **Step 3: เขียน `camera_gestures/mapping.py`** ห้าม import cv2, mediapipe, arm_contracts ลำดับต่อเฟรมเป็นดังนี้

```text
dt = now - last; gap = last is set and not 0 <= dt <= max_gap
if gap: dt = 0; reference = None; if tracking: desired = emitted
valid = armed and active and finite(position_m, z_m)
if valid and reference is set: valid = no jump versus the previous raw frame
if not valid: if tracking: desired = emitted; tracking = False; reference = None; return hold
if reference is None: set reference, reset filters, held_z = z, latch code  # a gap frame lands here and tracks without moving
else: filter, take deltas, move held_z by backlash, desired = clip(desired + mapped deltas)
    update grip when code differs from the latched code
emitted moves toward desired by at most max_speed * dt / 1000
tracking = True; return track
```

ตอน `armed=False` คืน `enabled=False` นอกนั้นเมื่อไม่ valid คืน `enabled=True, mode='hold'`

- [ ] **Step 4:** รันเทสต์ซ้ำ ต้อง PASS ทุกตัว
- [ ] **Step 5: เพิ่ม `test_drag_targets_stay_within_the_soft_limits`** ในคลาสที่มี `assertReachable` (`tests/test_contract_tools.py:133`) ตรวจ `DRAG_TARGETS_M` ทุกจุดว่าถึงได้และอยู่ในกล่อง และเพิ่มเทสต์ว่าจุดใกล้ฐานสุดของกล่อง `hypot(0.18 - pan_x, 0)` ≥ `tcp_min_radius_from_pan_axis_m` และจุดไกลสุด `hypot(0.33 - pan_x, 0.12)` ≤ `tcp_max_radius_from_pan_axis_m`
- [ ] **Step 6:** รัน `$PY -m unittest tests.test_mapping tests.test_contract_tools` ต้องผ่าน
- [ ] **Step 7: Commit** ด้วยข้อความ `Add relative hand-to-target mapper (M0)`

---

### Task 2: `ReplayWriter` แบบเขียนทีละบรรทัด

**Files:**
- Modify: `arm_contracts/replay.py`
- Test: `tests/test_contract_tools.py` (คลาส `ReplayFileTests`)

**Interfaces:**
- Produces: `ReplayWriter(path, kind, camera=None, notes='', created=None)` มี `write(message)`, `close()` และเป็น context manager

- [ ] **Step 1: เขียนเทสต์ที่ fail**
  - `test_writer_output_reads_back`: เขียน 3 ข้อความ ปิดไฟล์ แล้ว `read_replay` ได้ครบและ header ตรง
  - `test_writer_keeps_lines_without_close`: เขียน 2 ข้อความ ไม่ปิด อ่านไฟล์ ต้องได้ 2 ข้อความ
  - `test_writer_with_no_messages_reads_back`: ปิดทันที `read_replay` คืน `[]`
  - `test_writer_refuses_out_of_order_seq`: seq ซ้ำ ต้อง raise `ContractError`
- [ ] **Step 2:** รัน `$PY -m unittest tests.test_contract_tools.ReplayFileTests -v` ต้อง FAIL
- [ ] **Step 3:** เขียนคลาส ใช้ `Receiver(KINDS[kind], None)` ตรวจแบบเดียวกับ `write_replay`, `newline='\n'`, flush ทุกบรรทัด และแยกการสร้าง header เป็น helper ที่ใช้ร่วมกับ `write_replay`
- [ ] **Step 4:** รันซ้ำ ต้อง PASS
- [ ] **Step 5: Commit** ด้วยข้อความ `Add streaming replay writer`

ข้อจำกัดที่ต้องบันทึก: ไฟล์ที่ล่มจะเหลือบรรทัดเต็มเพราะ flush ทีละบรรทัด ถ้า OS ตัดกลางบรรทัด `read_replay` ยัง raise พร้อมเลขบรรทัดตามเดิม ไม่แก้ให้ข้าม

---

### Task 3: `MappingSession`

**Files:**
- Create: `camera_gestures/mapping_session.py`
- Test: `tests/test_mapping_session.py`

**Interfaces:**
- Consumes: `RelativeMapper`, `ReplayWriter`, `EndEffectorTarget`, `MockArm`
- Produces:
  - `MappingSession(arm, writer=None, config=MappingConfig(), source='live')`
  - `.step(control, metric, code, now_ms) -> EndEffectorTarget` อัปเดต mapper, ส่งเข้า `arm.receive`, เขียนไฟล์
  - `.reset() -> None` เรียกตอนกด R
  - `.log_fields() -> dict` คืน `armed`, `mapping_reset`, `mapping_position_m`, `mapping_mode`, `mapping_enabled`, `mapping_grip`
  - `targets_from_records(records, config=MappingConfig()) -> list[EndEffectorTarget]` คำนวณซ้ำจาก frame log ด้วย `source='script'`

- [ ] **Step 1: เขียนเทสต์ที่ fail** ใช้ `HandControl`, `MetricHand` จริงกับ `PalmMeasure` จำลอง และ `MockArm` จริง
  - `test_messages_pass_the_receiver`: ทุกข้อความ `arm.problem is None` และ `orientation_wxyz is None`
  - `test_palm_unusable_holds_while_control_is_active`: `control.update(wrist, scale, now, None)` ได้ `hold` แม้ `control.status` เป็น `ACTIVE`
  - `test_hand_switch_disables_at_once`: `control.select('Left')` ระหว่างตาม เฟรมถัดไป `enabled=False`
  - `test_loss_turns_to_hold_in_the_same_frame`: เฟรมแรกที่ไม่มีมือเป็น `hold`
  - `test_mock_follows_and_freezes`: `arm.position` ขยับตอนตาม และค้างตอนพัก
  - `test_reset_key_then_tracking_slides_back`: ทำลำดับเดียวกับ `handle_key('r', ...)` แล้วเรียก `.reset()` จุดเลื่อนกลับไม่เกินเพดาน และไม่มีเฟรมที่จุดกระโดด
  - `test_records_recompute_to_the_same_targets`: เก็บ `log_fields` กับ `metric_*`, `output`, `receipt_ms` ของแต่ละเฟรม แล้ว `targets_from_records` ให้ `position_m`, `mode`, `enabled`, `grip` เท่าเดิมทุกตัว
- [ ] **Step 2:** รัน `$PY -m unittest tests.test_mapping_session -v` ต้อง FAIL
- [ ] **Step 3:** เขียนโมดูล `seq` เริ่มที่ 1 และเพิ่มทีละ 1 ต่อข้อความ, `t_ms=now_ms`, ปัดตำแหน่งเป็น 6 ตำแหน่งเหมือน `scripted.py`, `mapping_reset` เป็น `True` ในเฟรมแรกหลัง `.reset()`
- [ ] **Step 4:** รันซ้ำ ต้อง PASS
- [ ] **Step 5: Commit** ด้วยข้อความ `Connect the mapper to the contract, mock arm and replay file`

---

### Task 4: แสดงสดใน app

**Files:**
- Modify: `arm_contracts/mock_arm.py` (`render`)
- Modify: `camera_gestures/app.py`
- Test: `tests/test_contract_tools.py` (คลาส `MockArmTests`)

**Interfaces:**
- Consumes: `MappingSession`, `MappingConfig`, `DRAG_TARGETS_M`, `ReplayWriter`
- Produces: `render(arm, box=None, marks=())` โดย `box=(min_m, max_m)` และ `marks` เป็นตำแหน่งสำหรับวาดพร้อมเลขลำดับ; CLI `--mapping relative`

- [ ] **Step 1: เขียนเทสต์ที่ fail**
  - `test_render_default_is_unchanged`: `render(arm)` เท่ากับ `render(arm, box=None, marks=())`
  - `test_render_draws_box_and_marks`: ส่ง `box` และ `marks` แล้วภาพต่างจากเดิม
- [ ] **Step 2:** รัน `$PY -m unittest tests.test_contract_tools.MockArmTests -v` ต้อง FAIL
- [ ] **Step 3:** แก้ `render` แล้วรันซ้ำ ต้อง PASS
- [ ] **Step 4: แก้ `app.py`** เพิ่ม `--mapping` รับ `choices=['relative']` ถ้าไม่มี `--calibration` ให้ `parser.error`, สร้าง `ReplayWriter` ที่ `logs/<stem>.ee_target.jsonl` พร้อม `camera` (width, height, f_px) และ `notes` (classifier, palm_length_m), เรียก `session.step` ถัดจาก `step(...)`, รวม `log_fields()` ใน frame log, วาดหน้าต่าง `mock arm`, ปุ่ม `r` เรียก `session.reset()` ก่อน `handle_key`, ปิด writer ใน `finally`, เพิ่ม `mapping` ใน metadata
- [ ] **Step 5:** รัน `$PY -m camera_gestures.app --help` ต้องมี `--mapping` และ `$PY -m camera_gestures.app --mapping relative` ต้องจบด้วย error ว่าต้องใช้ `--calibration`
- [ ] **Step 6:** รัน `$PY -m unittest discover -s tests` ต้องผ่านทั้งหมด รวม replay เดิม
- [ ] **Step 7: Commit** ด้วยข้อความ `Show live mapped targets on the mock arm`

---

### Task 5: รายงานผลการวัด และเอกสาร

**Files:**
- Create: `camera_gestures/mapping_report.py`
- Create: `docs/tasks/P006-m0-relative.md`
- Modify: `docs/backlog.md`, `docs/current-state.md`, `docs/camera-gestures.md`
- Test: `tests/test_mapping_report.py`

**Interfaces:**
- Consumes: `read_replay`, `DRAG_TARGETS_M`
- Produces:
  - `track_segments(messages) -> list[dict]` แต่ละช่วง `track` ติดกัน มี `seconds`, `net_m`, `std_mm`
  - `target_times(messages, targets, radius_m=0.01, dwell_ms=1000) -> list[float | None]` เวลาเป็นวินาทีของแต่ละเป้าตามลำดับ นับจากเป้าก่อนหน้าสำเร็จ
  - CLI `python -m camera_gestures.mapping_report logs/<run>.ee_target.jsonl [--targets]`

- [ ] **Step 1: เขียนเทสต์ที่ fail** ด้วยข้อความจาก `EndEffectorTarget` สร้างเอง
  - `test_segments_split_on_hold`: `track`×3, `hold`, `track`×2 ได้ 2 ช่วง และ `net_m` ถูกต้อง
  - `test_std_of_a_still_segment_is_zero`
  - `test_target_needs_the_full_dwell`: อยู่ในรัศมี 900 ms ไม่ผ่าน, 1000 ms ผ่าน
  - `test_target_not_reached_is_none`
- [ ] **Step 2:** รัน `$PY -m unittest tests.test_mapping_report -v` ต้อง FAIL
- [ ] **Step 3:** เขียนโมดูล แล้วรันซ้ำ ต้อง PASS
- [ ] **Step 4: เขียนเอกสาร** `P006-m0-relative.md` ตามรูปแบบ packet เดิม ระบุ owned files และสถานะ "โค้ดเสร็จ กล้องจริง NOT RUN"; `docs/backlog.md` เพิ่ม M0 เป็นก้าวแรกของ P006; `docs/current-state.md` เพิ่มหนึ่งรายการ; `docs/camera-gestures.md` เพิ่มคำสั่งรันและขั้นตอนจาก Task 6
- [ ] **Step 5:** รัน `$PY -m unittest discover -s tests -v` ต้องผ่านทั้งหมด
- [ ] **Step 6: Commit** ด้วยข้อความ `Add M0 measurement report and task packet`

---

### Task 6: ทดสอบกล้องจริง (ผู้ใช้เป็นคนทำ)

Agent ไม่ทำแทนและห้ามบันทึกผลจากข้อมูลจำลองว่าเป็นผลกล้องจริง ขั้นตอนนี้ไม่ขยับแขนจริง

- [ ] **Step 1:** บน Windows ปรับเทียบกล้องและวัดฝ่ามือตาม P002 แล้วรัน

```bash
python -m camera_gestures.app --mapping relative --calibration <file> --palm-length-m <m>
```

- [ ] **Step 2:** ทำเกณฑ์ตารางใน spec ทีละข้อ คั่นแต่ละรอบโดยเอามือออกจากกรอบ เพื่อให้ `track_segments` แยกรอบให้
- [ ] **Step 3:** รัน `python -m camera_gestures.mapping_report logs/<run>.ee_target.jsonl` และเติม `--targets` สำหรับเกณฑ์ลากไปเป้า
- [ ] **Step 4:** บันทึกด้วย `docs/templates/experiment-record.md` ระบุเครื่อง กล้อง f ขนาดฝ่ามือ และผลที่ไม่ผ่าน ถ้าไม่ผ่านให้รายงานก่อนปรับเกณฑ์
- [ ] **Step 5:** เปิด PR หลังเกณฑ์ผ่านครบเท่านั้น แนบผล `python -m unittest discover -s tests -v` และบันทึกการทดลอง ให้ GUNGUN รีวิว
