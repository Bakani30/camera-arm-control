# Hand Axis Bench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** วัดจากกล้องจริงว่าระยะเอื้อม ก้ม-เงย และบิดข้อมืออ่านได้นิ่งแค่ไหน และกวนกันแค่ไหน ก่อนแก้ mapper

**Architecture:** แยก 3 ไฟล์: estimator ล้วน, รายงานจาก JSONL ล้วน, และ capture ที่ import `cv2`/`mediapipe` เฉพาะใน `main` ตามแบบ `app.py` การ capture เก็บ landmark ดิบทุกเฟรม ส่วนการคำนวณทุกวิธีทำตอนสร้างรายงาน จึงเพิ่มวิธีใหม่แล้วคำนวณจากไฟล์เดิมได้โดยไม่ต้องวัดซ้ำ

**Tech Stack:** Python 3, `unittest`, MediaPipe Tasks 0.10.21, OpenCV 4.11 (ตาม `requirements.txt`)

**Spec:** `docs/superpowers/specs/2026-11-01-five-axis-hand-control-design.md` ขั้นที่ 1 เท่านั้น แผนขั้นที่ 2-3 เขียนหลังผู้ใช้ดูผลวัด

## Global Constraints

- เครื่องมือไม่แก้ `camera_gestures/mapping.py` ไม่ส่ง `ee_target` และไม่สั่งฮาร์ดแวร์
- Branch `a/hand-axis-bench` แตกจาก `a/relative-mapping` เพราะ `metric.py` และ `calibration.py` ยังไม่อยู่บน `main`
- ห้าม commit, push หรือเปิด PR จนกว่าผู้ใช้สั่ง ขั้น "Commit" ในแผนให้ถามก่อนทุกครั้ง
- ไม่เพิ่มส่วน learning หรือ AI (D22)
- ค่าคงที่: `SCALES = (0.5, 1.0, 1.25)`, `WORKSPACE_M = (0.15, 0.24, 0.16)`, `HAND_STROKE_M = (0.30, 0.62, 0.31)` เรียงแกน เอื้อม, ซ้าย-ขวา, ขึ้น-ลง และ `base_gain = max(WORKSPACE_M[i]/HAND_STROKE_M[i])`
- เกณฑ์เป็นค่าเริ่มต้นตาม spec ประเมินที่สเกล 1 และรายงานสเกล 0.5, 1.25 ด้วย: A SD ≤ 3 มม.; B 15 ซม. ±25%; C, D, E แต่ละแกน ≤ 10 มม.; F กวนกัน ≤ 25%
- ผลทุกไฟล์ต้องบอกเครื่อง กล้อง ไฟล์ calibration และระยะฝ่ามือ ไฟล์ `camera_provisional_f900.json` ต้องถูกทำป้าย `provisional`
- Test รันด้วย `python -m unittest tests.test_hand_axis -v`; ไฟล์เทสต์นี้ห้าม import `cv2`, `numpy`, `mediapipe`

## Review Focus

- มือหายบางช่วงใน trial: ต้องไม่นับเป็นผ่าน รายงาน `lost_pct` และ trial ที่หายเกิน 10% เป็น `invalid`
- ผู้ใช้ไม่ถือท่ากลางช่วงแรกของ trial: baseline เชื่อไม่ได้ ถ้า SD ของระยะใน 1 วินาทีแรกเกิน 10 มม. ที่สเกล 1 ให้เป็น `invalid`
- มีมือที่สองหรือ handedness ไม่แน่ใจ: ใช้ `extract_selected` ไม่สลับไปมืออีกข้าง และนับเป็นมือหาย
- FPS ต่ำจาก inference ช้า: รายงาน `median_fps` และ trial ที่ต่ำกว่า 12 FPS เป็น `invalid` เพราะ SD ของตัวกรองจะดูดีเกินจริง
- ปิดโปรแกรมกลาง trial หรือบรรทัดสุดท้ายขาด: รายงานต้องอ่านส่วนที่ครบ และทำป้าย trial ที่ไม่จบเป็น `incomplete`

---

### Task 1: Estimators

**Files:**
- Create: `camera_gestures/axis_estimators.py`
- Test: `tests/test_hand_axis.py`

**Interfaces:**
- Consumes: รูปแบบ landmark ของ `observation.extract`: 21 จุด `[x, y, z]` แบบ normalized
- Produces:
  - `reach_2d(points, width, height, focal_px, palm_m) -> float | None`
  - `reach_z(points, width, height, focal_px, palm_m, z_gain=1.0) -> float | None` คือสูตร `palm_length_px` ตอนนี้
  - `reach_z_perspective(points, width, height, focal_px, palm_m, principal_px, z_gain=1.0) -> float | None`
  - `reach_bones(points, width, height, focal_px, palm_m, palm_width_m) -> float | None`
  - `REACH_METHODS: dict[str, callable]` key คือ `2d`, `z`, `z_perspective`, `bones` โดยรับ `(points, ctx, z_gain=1.0)` และ `ctx` เป็น `BenchContext(width, height, focal_px, palm_m, palm_width_m, principal_px)`
  - `position_m(points, ctx, z_m, point) -> tuple[float, float]` โดย `point` เป็น `wrist` หรือ `center`
  - `hand_angles(points) -> tuple[float, float] | None` คืน `(pitch_deg, roll_deg)`: pitch บวกเมื่อนิ้วเอียงเข้ากล้อง โดยใช้ 3D ของ 0→9, roll ใช้ 3D ของ 5→17
  - `base_gain() -> float`

- [ ] **Step 1: เขียนเทสต์ด้วยมือสังเคราะห์**

Helper `synthetic_hand(x, y, z, pitch=0, roll=0, width=1280, height=720, f=900, z_scale=1.0)` คืน 21 จุด โดยจุด 0, 5, 9, 17 ในกรอบมือคือ `(0,0,0)`, `(-.022,.088,0)`, `(0,.09,0)`, `(.028,.078,0)` เมตร จุดอื่นเท่าจุด 0 หมุน roll รอบแกน y ก่อน แล้ว pitch รอบแกน x ผ่านข้อมือ โดย pitch บวกทำให้นิ้วเข้ากล้อง `z` ของ landmark คือ `(Zi-Zw)*f/Zw/width*z_scale`

```python
G = base_gain()
def err_mm(method, pitch=30, roll=0, z_gain=1.0, z_scale=1.0):
    flat = synthetic_hand(0, 0, .5, z_scale=z_scale)
    bent = synthetic_hand(0, 0, .5, pitch=pitch, roll=roll, z_scale=z_scale)
    return G*abs(REACH_METHODS[method](flat, CTX, z_gain)-REACH_METHODS[method](bent, CTX, z_gain))*1000

def test_values_match_the_design_table(self):
    self.assertAlmostEqual(G, .516, places=2)
    self.assertAlmostEqual(err_mm('2d', pitch=-30), 66.7, delta=1)
    self.assertAlmostEqual(err_mm('2d', pitch=30), 13.1, delta=1)
    self.assertAlmostEqual(err_mm('z', pitch=30), 18.0, delta=1)
    self.assertAlmostEqual(err_mm('z_perspective'), 0, delta=.5)
    self.assertAlmostEqual(err_mm('z_perspective', pitch=-30, z_scale=.9), 8.1, delta=1)
    self.assertLess(err_mm('z_perspective', pitch=-30), .5)

def test_reach_is_true_when_flat(self):
    for name in REACH_METHODS:
        self.assertAlmostEqual(REACH_METHODS[name](synthetic_hand(.05, -.02, .4), CTX), .4, delta=.002)

def test_angles_recover_pose(self):
    pitch, roll = hand_angles(synthetic_hand(0, 0, .5, pitch=30))
    self.assertAlmostEqual(pitch, 30, delta=3)   # perspective reads about 27.7
    self.assertAlmostEqual(abs(hand_angles(synthetic_hand(0, 0, .5, roll=45))[1]), 45, delta=3)

def test_pointing_at_camera_returns_none(self):
    self.assertIsNone(REACH_METHODS['2d'](synthetic_hand(0, 0, .5, pitch=89.9), CTX))
```

`CTX = BenchContext(1280, 720, 900., .09, math.hypot(.05, .01), (640., 360.))` และ `err_mm` เทียบกับ `z_gain=1` ยกเว้นระบุ

- [ ] **Step 2: รันแล้วต้องล้มเหลว**

Run: `python -m unittest tests.test_hand_axis -v`
Expected: FAIL ด้วย `ModuleNotFoundError: camera_gestures.axis_estimators`

- [ ] **Step 3: เขียน `axis_estimators.py`**

`reach_z_perspective`: กำหนด `dz` เป็น z ของจุด 9 ลบจุด 0 ในหน่วยพิกเซลคูณ `z_gain` และ `g = 1 + dz/focal_px` แล้ว:

```text
Z = palm_m / hypot((u9-cx)/f*g - (u0-cx)/f, (v9-cy)/f*g - (v0-cy)/f, dz/f)
```

`reach_bones` ใช้ `F / max(projected_0_9/palm_m, projected_5_17/palm_width_m)` ทุกวิธีใช้ guard เดียวกับ `palm_measure` และ reuse `_usable` กับ `palm_center_px` จาก `metric.py`

- [ ] **Step 4: รันแล้วต้องผ่าน**

Run: `python -m unittest tests.test_hand_axis -v`
Expected: PASS

- [ ] **Step 5: Commit (ถามผู้ใช้ก่อน)**

```bash
git add camera_gestures/axis_estimators.py tests/test_hand_axis.py
git commit -m "Add hand reach and angle estimators for the axis bench"
```

### Task 2: รายงานจากไฟล์วัด

**Files:**
- Create: `camera_gestures/axis_report.py`
- Test: `tests/test_hand_axis.py`

**Interfaces:**
- Consumes: Task 1 ทั้งหมด; ไฟล์ JSONL บรรทัดแรก `{"kind":"header", "width", "height", "focal_px", "principal_px", "palm_length_m", "palm_width_m", "calibration", "provisional", "platform", "camera", "note"}` บรรทัดต่อไป `{"kind":"frame", "trial", "t_ms", "hand_present", "gesture", "landmarks", "world_landmarks"}` และ `{"kind":"trial_end", "trial"}` เมื่อ trial จบครบเวลา
- Produces:
  - `read_log(path) -> (header, list[frame], set[completed_trial])` ข้ามบรรทัดสุดท้ายที่ JSON ไม่ครบ
  - `fit_z_gain(frames, ctx) -> float` หา `z_gain` ใน 0 ถึง 1.5 ที่ทำให้ `reach_z_perspective` ของเฟรมใน trial `C` แกว่งน้อยสุด แบบ grid ทีละ 0.05 ค่านี้คือ "z ตรงจริง"
  - `summarize(header, frames, completed) -> dict` โครง `{"header":..., "z_gain_fit":..., "trials":{trial:{"status":"ok|invalid|incomplete", "lost_pct", "median_fps", "methods":{method:{"point":{point:{"scale":{scale:{"reach_mm","lateral_mm","vertical_mm","passed"}}}}}}}}}`
  - `format_table(summary) -> str`
  - CLI: `python -m camera_gestures.axis_report logs/<stem>.axis_bench.jsonl` พิมพ์ตารางและเขียน `<stem>.axis_summary.json`

กติกาคำนวณ: แปลงทุกเฟรมเป็นตำแหน่ง, กรอง EMA τ 120 ms, baseline คือ median ของ 1 วินาทีแรก, ค่าเพี้ยนคือ peak ของ `|gain*(ค่า-baseline)|`, ชุด A ใช้ SD ตลอด trial, ชุด B ใช้ (max-min) ของระยะ เทียบ `gain*0.30`, ชุด F ใช้ (ช่วงของแกนที่ไม่ได้สั่ง)/(ช่วงของแกนที่สั่ง) ชื่อ trial: `A_near`, `A_mid`, `A_far`, `B`, `C`, `D`, `E`, `F_pitch`, `F_roll`

- [ ] **Step 1: เขียนเทสต์**

```python
def test_clean_c_trial_passes_with_perspective(self):
    s = summarize(HEADER, frames_for('C', pitch_wave(30)), {'C'})
    row = s['trials']['C']['methods']['z_perspective']['wrist']['scale']['1.0']
    self.assertLess(row['reach_mm'], 1)
    self.assertTrue(row['passed'])

def test_2d_fails_the_same_trial(self):
    s = summarize(HEADER, frames_for('C', pitch_wave(30)), {'C'})
    self.assertFalse(s['trials']['C']['methods']['2d']['wrist']['scale']['1.0']['passed'])

def test_fit_finds_the_z_scale(self):
    frames = frames_for('C', pitch_wave(30), z_scale=.7)
    self.assertAlmostEqual(fit_z_gain(frames, CTX), 1/.7, delta=.1)

def test_hand_loss_over_ten_percent_is_invalid(self): ...   # 15% of frames hand_present False: status == 'invalid', lost_pct == 15
def test_baseline_not_held_is_invalid(self): ...            # hand moves 5 cm in reach during the first second
def test_low_fps_is_invalid(self): ...                      # t_ms step 100 (10 FPS)
def test_unfinished_trial_is_incomplete(self): ...          # 'C' not in completed
def test_read_log_skips_truncated_last_line(self): ...      # file ends in '{"kind":"fr'
def test_provisional_is_printed(self): ...                  # 'provisional' in format_table(...) for a provisional header
def test_sd_trial_and_stroke_trial(self): ...               # A with constant pose reports 0 SD; B of 30 cm reports 15 cm x gain/base within 25%
```

`frames_for` สร้างเฟรม 30 FPS จาก `synthetic_hand` และเริ่มด้วยท่ากลาง 1 วินาที

- [ ] **Step 2: รันแล้วต้องล้มเหลว**

Run: `python -m unittest tests.test_hand_axis -v`
Expected: FAIL ด้วย `ModuleNotFoundError: camera_gestures.axis_report`

- [ ] **Step 3: เขียน `axis_report.py` ตาม Interfaces**

- [ ] **Step 4: รันแล้วต้องผ่าน**

Run: `python -m unittest tests.test_hand_axis -v`
Expected: PASS

- [ ] **Step 5: Commit (ถามผู้ใช้ก่อน)**

```bash
git add camera_gestures/axis_report.py tests/test_hand_axis.py
git commit -m "Report hand axis noise and crosstalk from bench logs"
```

### Task 3: เครื่องมือ capture

**Files:**
- Create: `camera_gestures/axis_bench.py`
- Modify: `docs/camera-gestures.md` เพิ่มหัวข้อวิธีวัด
- Test: `tests/test_hand_axis.py`

**Interfaces:**
- Consumes: `axis_report` รูปแบบไฟล์; `observation.extract_selected`; `calibration.load_calibration` และ `require_resolution`; `download_model` ค่า `MODEL`
- Produces:
  - `TRIALS: tuple[Trial, ...]` โดย `Trial(name, seconds, prompt)` ลำดับ: `A_near` 10, `A_mid` 10, `A_far` 10, `B` 30, `C` 15, `D` 15, `E` 30, `F_pitch` 12, `F_roll` 12 วินาที
  - `TrialRunner(trials)` เมธอด `press(key, now_ms)`, `tick(now_ms) -> str | None`, `state` เป็น `waiting|neutral|running|done`, `current`
  - CLI: `python -m camera_gestures.axis_bench --calibration PATH --palm-length-m M --palm-width-m M [--hand Right] [--camera 0] [--model PATH] [--note TEXT]`
  - ไฟล์ `logs/<UTC stem>.axis_bench.jsonl` ตามรูปแบบใน Task 2 flush ทุกเฟรม

Prompt บนจอเป็นภาษาไทยไม่ได้ เพราะ `cv2.putText` ไม่รองรับ ใช้ภาษาอังกฤษสั้นๆ แล้วเอกสารมีคำแปล ลำดับใน trial: กด Space → ถือท่ากลาง 1 วินาที → ทำท่าตาม prompt จนหมดเวลา → รอ Space รอบถัดไป กด `R` ทำ trial เดิมซ้ำ โดยเฟรมของรอบเก่าถูกแทนในไฟล์ด้วยชื่อ `<trial>#retry<N>` เพื่อไม่ทิ้งข้อมูล กด `Q` หรือ Esc จบ

- [ ] **Step 1: เขียนเทสต์ของ `TrialRunner` และ import ของไฟล์**

```python
def test_runner_walks_each_trial(self):
    r = TrialRunner((Trial('C', 15, 'x'),))
    self.assertEqual(r.state, 'waiting')
    r.press(' ', 0); self.assertEqual(r.state, 'neutral')
    self.assertIsNone(r.tick(999))
    r.tick(1000); self.assertEqual(r.state, 'running')
    self.assertEqual(r.tick(16000), 'C')   # returns the finished trial once
    self.assertEqual(r.state, 'done')

def test_retry_keeps_the_old_frames_under_a_new_name(self):
    r = TrialRunner((Trial('C', 15, 'x'),))
    r.press(' ', 0); r.tick(1000)
    r.press('r', 2000)
    self.assertEqual(r.retired, ['C#retry1'])
    self.assertEqual(r.state, 'waiting')

def test_module_needs_no_camera_libraries_to_import(self):
    import camera_gestures.axis_bench
    self.assertNotIn('cv2', vars(camera_gestures.axis_bench))
```

- [ ] **Step 2: รันแล้วต้องล้มเหลว**

Run: `python -m unittest tests.test_hand_axis -v`
Expected: FAIL ด้วย `ModuleNotFoundError: camera_gestures.axis_bench`

- [ ] **Step 3: เขียน `axis_bench.py`**

ตั้งค่า `GestureRecognizer` แบบเดียวกับ `app.py` (`VIDEO`, `num_hands=2`) แต่ไม่ใช้ `HandControl` และเก็บ `result.hand_world_landmarks` ของมือที่เลือกในเฟรมเดียวกัน ต้องแสดงสถานะบนจอ: ชื่อ trial, prompt, เวลาที่เหลือ, `HAND LOST` เมื่อไม่มีมือ และป้าย `PROVISIONAL` ถ้าชื่อไฟล์ calibration มีคำว่า `provisional`

- [ ] **Step 4: รันเทสต์ทั้งชุด**

Run: `python -m unittest discover -s tests -v`
Expected: ผ่านทั้งหมดบนเครื่องที่ติดตั้ง `requirements.txt` แล้ว

- [ ] **Step 5: เขียนหัวข้อวิธีวัดใน `docs/camera-gestures.md`**

ต้องมี: คำสั่ง, วิธีวัดความยาวฝ่ามือ (ข้อมือถึงโคนนิ้วกลาง) และความกว้าง (โคนนิ้วชี้ถึงโคนนิ้วก้อย) ด้วยไม้บรรทัด, คำแปล prompt ทุก trial, ข้อห้ามปรับค่าฝ่ามือจากผลชุด B และบอกชัดว่าเครื่องมือไม่ขยับแขน

- [ ] **Step 6: Commit (ถามผู้ใช้ก่อน)**

```bash
git add camera_gestures/axis_bench.py tests/test_hand_axis.py docs/camera-gestures.md
git commit -m "Add guided real-camera bench for hand axes"
```

### Task 4: ผู้ใช้วัดและสรุปผล

งานนี้ต้องให้ผู้ใช้ทำท่าหน้ากล้อง agent ห้ามรายงานผลจากข้อมูลสังเคราะห์ว่าเป็นผลกล้องจริง

**Files:**
- Create: `docs/research/hardware-notes/2026-11-XX-hand-axis-bench-results.md`
- Modify: `docs/backlog.md`, `docs/current-state.md`

- [ ] **Step 1: ผู้ใช้วัดบน Mac**

```bash
python -m camera_gestures.axis_bench --calibration logs/camera_calibration_run4.json --palm-length-m <วัดจริง> --palm-width-m <วัดจริง> --note "mac first pass"
```

- [ ] **Step 2: สร้างรายงาน**

```bash
python -m camera_gestures.axis_report logs/<stem>.axis_bench.jsonl
```

Expected: ตารางครบ 9 trial พร้อม `z_gain_fit` ถ้ามี `invalid` ให้ผู้ใช้วัด trial นั้นซ้ำ

- [ ] **Step 3: ผู้ใช้ calibrate และวัดซ้ำบน ASUS ก่อนสรุป gain สุดท้าย**

- [ ] **Step 4: เขียนบันทึกผลแล้วส่งให้ผู้ใช้ตัดสิน**

บันทึกต้องแยกผล Mac กับ ASUS และระบุว่าวัดจากคนเดียว เลือกวิธีที่ง่ายที่สุดที่ผ่าน C และ D ถ้าไม่มีวิธีผ่าน ให้เสนอทางออกตามหัวข้อ "ทางออกเมื่อไม่ผ่าน" ใน spec โดยไม่เปลี่ยนการตัดสินใจเอง D20 แก้ได้เมื่อผลผ่านเท่านั้น แล้วจึงเขียนแผนขั้นที่ 2-3
