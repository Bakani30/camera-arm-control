"""Small real arm spec (D32): the numbers every model of the real arm must match."""
import json
import math
from pathlib import Path
from types import SimpleNamespace

DEFAULT_SPEC = Path(__file__).with_name('small_arm_v0.json')
BASE_PAN_RANGE_DEG = 360  # D25: the base turns a full circle
TRAVEL_SLACK_DEG = 1e-6  # float slack when comparing a joint range with actuator travel
SPEED_CAP_SLACK_DPS = 0.01  # speed caps must equal speed_cap_fraction x no-load speed


class Spec:
    def __init__(self, data):
        self.raw = data
        self.joints = [SimpleNamespace(**j) for j in data['joints']]
        self.actuators = data['actuators']
        self.tcp = data['tcp']
        self.speed_cap_fraction = data['speed_cap_fraction']

    def joint(self, name):
        for j in self.joints:
            if j.name == name:
                return j
        raise KeyError(f'no joint named {name!r}')

    def actuator(self, joint_name):
        return self.actuators[self.joint(joint_name).actuator]

    def speed_cap_dps(self, joint_name):
        return self.actuator(joint_name)['speed_cap_dps']

    def accel_cap_dps2(self, joint_name):
        return self.actuator(joint_name)['accel_cap_dps2']


def load_spec(path=DEFAULT_SPEC):
    return Spec(json.loads(Path(path).read_text(encoding='utf-8')))


def validate(spec):
    """Problems that break the decided rules (D25, D32); empty list means the spec is consistent."""
    problems = []
    for name, a in spec.actuators.items():
        expected = spec.speed_cap_fraction * a['no_load_speed_dps']
        if abs(a['speed_cap_dps'] - expected) > SPEED_CAP_SLACK_DPS:
            problems.append(f"{name}: speed cap {a['speed_cap_dps']} deg/s should be {expected:.2f} "
                            f"({spec.speed_cap_fraction} x no-load {a['no_load_speed_dps']})")
        if not a.get('accel_cap_dps2', 0) > 0:
            problems.append(f'{name}: needs a positive accel_cap_dps2 for trapezoid motion (D32)')
    for j in spec.joints:
        span = math.degrees(j.upper - j.lower)
        travel = spec.actuators[j.actuator]['travel_deg']
        if span > travel + TRAVEL_SLACK_DEG:
            problems.append(f'{j.name}: range {span:.2f} deg is wider than {j.actuator} travel {travel} deg')
    pan = spec.joint('shoulder_pan')
    if abs(math.degrees(pan.upper - pan.lower) - BASE_PAN_RANGE_DEG) > 0.01:
        problems.append(f'shoulder_pan: range must be {BASE_PAN_RANGE_DEG} deg (D25)')
    return problems


def _matmul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def _apply(m, v):
    return [sum(m[i][k] * v[k] for k in range(3)) for i in range(3)]


def _rpy(r, p, y):
    # URDF fixed-axis roll-pitch-yaw: R = Rz(y) Ry(p) Rx(r)
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)
    return [[cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
            [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
            [-sp, cp * sr, cp * cr]]


def _axis_angle(axis, t):
    n = math.sqrt(sum(a * a for a in axis))
    x, y, z = (a / n for a in axis)
    c, s, v = math.cos(t), math.sin(t), 1 - math.cos(t)
    return [[c + x * x * v, x * y * v - z * s, x * z * v + y * s],
            [y * x * v + z * s, c + y * y * v, y * z * v - x * s],
            [z * x * v - y * s, z * y * v + x * s, c + z * z * v]]


def forward_kinematics(spec, q, frame=None):
    """Position (m, base frame) of a link origin or the TCP (default) for joint angles q (rad, missing = 0)."""
    frame = frame or spec.tcp['name']
    by_child = {j.child: j for j in spec.joints}
    steps, link = [], frame
    if frame == spec.tcp['name']:
        steps.append((spec.tcp['origin_xyz'], spec.tcp['origin_rpy'], None, 0.0))
        link = spec.tcp['parent']
    while link in by_child:
        j = by_child[link]
        steps.append((j.origin_xyz, j.origin_rpy, j.axis, q.get(j.name, 0.0)))
        link = j.parent
    rot, pos = [[1, 0, 0], [0, 1, 0], [0, 0, 1]], [0.0, 0.0, 0.0]
    for xyz, rpy, axis, angle in reversed(steps):
        pos = [p + d for p, d in zip(pos, _apply(rot, xyz))]
        rot = _matmul(rot, _rpy(*rpy))
        if axis is not None:
            rot = _matmul(rot, _axis_angle(axis, angle))
    return tuple(pos)
