# ค่าอ้างอิง FK ของ SO-101 สำหรับเทสต์สเปกแขนจริง
วันที่ 2026-10-23 · โรล C · ใช้เป็นคำตอบที่รู้ค่าใน `tests/test_arm_spec.py` (D32) · ค่าคำนวณจาก URDF ไม่ใช่ค่าวัด

## ที่มา
- URDF: [`Simulation/SO101/so101_new_calib.urdf`](https://raw.githubusercontent.com/TheRobotStudio/SO-ARM100/a758567c3978dfeefe282ede0500085a48fe8f78/Simulation/SO101/so101_new_calib.urdf) ที่ commit `a758567c39` (Apache-2.0)
- คำนวณด้วยสคริปต์ numpy ด้านล่าง ซึ่งอ่าน URDF ตรงๆ แยกจากโค้ด `arm_spec` จึงใช้เป็นค่าอ้างอิงอิสระได้
- จุดปลาย (TCP) = link `gripper_frame_link` ของ URDF ปลายนิ้วจริงจาก mesh ยื่นออกไปอีกไม่กี่ mm
- มุมที่ไม่ระบุ = 0 rad

## ผล
| ท่า (องศา) | ตำแหน่ง `gripper_frame_link` ในเฟรมฐาน (m) |
|---|---|
| ทุกข้อ 0 | (0.39136, −0.00001, 0.22647) |
| shoulder_pan 90 | (0.03883, −0.35253, 0.22647) |
| shoulder_pan −45, shoulder_lift 30, elbow_flex −60, wrist_flex 40, wrist_roll 70 | (0.31391, 0.26441, 0.24158) |

เอื้อมแนวนอนไกลสุดจากจุดกำเนิด `upper_arm_link` (แกนไหล่) ถึง TCP: ค้นแบบตาราง shoulder_lift × elbow_flex × wrist_flex (61 × 61 × 31 จุดในขีดจำกัด URDF) ได้ **410.8 mm** ที่ shoulder_lift 76.7°, elbow_flex −74.2°, wrist_flex −6.3° (ค่าสูงสุดจริงอาจมากกว่านี้เล็กน้อยระหว่างจุดตาราง) ตัวเลข ~417 mm ในโน้ตก่อนหน้าวัดถึงปลายนิ้วจาก mesh จึงไม่ใช่จุดเดียวกัน

## สคริปต์
รันด้วย `python -I fk_reference.py so101_new_calib.urdf` (ต้องมี numpy)

```python
import math, sys, xml.etree.ElementTree as ET
import numpy as np

U = ET.parse(sys.argv[1]).getroot()

def rpy(r, p, y):
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)
    return np.array([[cy*cp, cy*sp*sr - sy*cr, cy*sp*cr + sy*sr],
                     [sy*cp, sy*sp*sr + cy*cr, sy*sp*cr - cy*sr],
                     [-sp, cp*sr, cp*cr]])

def axang(a, t):
    a = np.array(a) / np.linalg.norm(a)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(t)*K + (1 - math.cos(t))*K@K

J = {}
for j in U.findall('joint'):
    o, ax = j.find('origin'), j.find('axis')
    J[j.find('child').get('link')] = dict(
        name=j.get('name'), parent=j.find('parent').get('link'), type=j.get('type'),
        xyz=[float(v) for v in o.get('xyz').split()], rpy=[float(v) for v in o.get('rpy').split()],
        axis=[float(v) for v in ax.get('xyz').split()])

def position(link, q):
    chain, l = [], link
    while l in J:
        chain.append(J[l]); l = J[l]['parent']
    R, p = np.eye(3), np.zeros(3)
    for jt in reversed(chain):
        p = p + R @ np.array(jt['xyz']); R = R @ rpy(*jt['rpy'])
        if jt['type'] == 'revolute':
            R = R @ axang(jt['axis'], q.get(jt['name'], 0))
    return p

deg = math.radians
print(position('gripper_frame_link', {}))
print(position('gripper_frame_link', {'shoulder_pan': deg(90)}))
print(position('gripper_frame_link', {'shoulder_pan': deg(-45), 'shoulder_lift': deg(30),
      'elbow_flex': deg(-60), 'wrist_flex': deg(40), 'wrist_roll': deg(70)}))
q = {'shoulder_lift': deg(76.7), 'elbow_flex': deg(-74.2), 'wrist_flex': deg(-6.3)}
t, s = position('gripper_frame_link', q), position('upper_arm_link', q)
print(math.hypot(t[0] - s[0], t[1] - s[1]))
```
