"""Small real arm spec (D32): the numbers every model of the real arm must match."""
import json
import math
from pathlib import Path
from types import SimpleNamespace

DEFAULT_SPEC = Path(__file__).with_name('small_arm_v1.json')
V0_SPEC = Path(__file__).with_name('small_arm_v0.json')  # the SO-101 reference, kept for its FK tests
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


def soft_range(spec, joint_name):
    """(lower, upper) in rad that the adapter clamps targets to: the joint limits tightened by soft_limits."""
    j = spec.joint(joint_name)
    soft = spec.raw.get('soft_limits', {}).get('joints', {}).get(joint_name, {})
    return max(j.lower, soft.get('lower', j.lower)), min(j.upper, soft.get('upper', j.upper))


def tcp_radius_m(spec, q):
    """Horizontal distance (m) from the shoulder_pan axis to the TCP; compare with soft_limits."""
    tx, ty, _ = forward_kinematics(spec, q)
    px, py, _ = spec.joint('shoulder_pan').origin_xyz
    return math.hypot(tx - px, ty - py)


def soft_limit_problems(spec, q, opening_mm=None):
    """Why the pose q (rad, missing = 0) breaks soft_limits; empty list means the adapter may send it.

    opening_mm is the finger opening; without it the floor check takes the worse of fully open and closed.
    """
    problems = []
    soft = spec.raw.get('soft_limits', {})
    for j in spec.joints:
        if j.name not in q:
            continue                    # no command for it; FK reads a missing joint as 0, inside every arm range
        lo, hi = soft_range(spec, j.name)
        v = q[j.name]
        if not lo - 1e-9 <= v <= hi + 1e-9:
            problems.append(f'{j.name}: {math.degrees(v):.1f} deg outside {math.degrees(lo):.1f}..{math.degrees(hi):.1f}')
    for pair in soft.get('pairs', []):
        total = sum(q.get(n, 0.0) for n in pair['joints'])
        if total > pair['max_sum'] + 1e-9:
            problems.append(f"{' + '.join(pair['joints'])}: {math.degrees(total):.1f} deg over {math.degrees(pair['max_sum']):.1f}")
    cap = soft.get('tcp_max_radius_from_pan_axis_m')
    if cap is not None and tcp_radius_m(spec, q) > cap:
        problems.append(f'TCP {tcp_radius_m(spec, q):.3f} m from the pan axis, over {cap} m')
    least = soft.get('tcp_min_radius_from_pan_axis_m')
    if least is not None and tcp_radius_m(spec, q) < least:
        problems.append(f'TCP {tcp_radius_m(spec, q):.3f} m from the pan axis, under {least} m')
    if 'floor' in soft:
        problems += _floor_problems(spec, q, opening_mm)
    return problems


def _point(spec, q, xyz):
    """A point given in gripper_link, in the base frame."""
    return forward_kinematics(SimpleNamespace(joints=spec.joints, tcp={**spec.tcp, 'origin_xyz': list(xyz)}), q)


def _distance_to_leg(x, y, angle_deg, leg):
    """Horizontal distance from (x, y), taken from the pan axis, to a leg's centre line."""
    c, s = math.cos(math.radians(angle_deg)), math.sin(math.radians(angle_deg))
    along = max(leg['root_radius_m'], min(leg['tip_radius_m'], x * c + y * s))
    return math.hypot(x - along * c, y - along * s)


def _floor_problems(spec, q, opening_mm):
    floor = spec.raw['soft_limits']['floor']
    table = spec.raw.get('gripper_kinematics')
    ends = (table['by_opening'][0]['opening_mm'], table['max_opening_mm'])
    px, py, _ = spec.joint('shoulder_pan').origin_xyz
    leg, drum = floor['legs'], floor['drum']
    problems = set()

    def check(name, xyz, radius, lowest):
        """radius is how far the part reaches sideways; lowest is the z of its bottom."""
        x, y = xyz[0] - px, xyz[1] - py
        if lowest < floor['table_z_m'] + floor['clearance_m']:
            problems.add(f'{name} {lowest * 1000:.0f} mm from the table')
        if lowest < leg['top_z_m'] + floor['clearance_m'] and any(
                _distance_to_leg(x, y, a, leg) <= leg['half_width_m'] + radius for a in leg['angles_deg']):
            problems.add(f'{name} {lowest * 1000:.0f} mm over a base leg')
        if lowest < drum['top_z_m'] + floor['clearance_m'] and math.hypot(x, y) <= drum['radius_m'] + radius:
            problems.add(f'{name} {lowest * 1000:.0f} mm over the base drum')

    for item in floor['frames']:
        c = forward_kinematics(spec, q, item['frame'])
        check(item['frame'], c, item['radius_m'], c[2] - item['radius_m'])
    origin = _point(spec, q, (0.0, 0.0, 0.0))
    ahead = _point(spec, q, (0.0, 0.0, -0.1))
    tool = [(a - b) / 0.1 for a, b in zip(ahead, origin)]
    sideways = math.sqrt(max(0.0, 1 - tool[2] ** 2))
    disc = floor['palm_disc']
    c = _point(spec, q, (0.0, 0.0, -disc['along_m']))
    check('palm', c, disc['radius_m'], c[2] - disc['radius_m'] * sideways)
    for opening in ends if opening_mm is None else (opening_mm,):
        along = fingertip_mm(spec, opening) / 1000
        reach = opening / 2000 + floor['finger_outer_past_half_opening_m']
        for name, at in (('fingers', along), ('finger roots', along - floor['finger_length_m'])):
            c = _point(spec, q, (0.0, 0.0, -at))
            check(name, c, reach, c[2] - reach * sideways)
    return sorted(problems)


def _gripper_value(spec, opening_mm, key):
    rows = spec.raw['gripper_kinematics']['by_opening']
    if not rows[0]['opening_mm'] <= opening_mm <= rows[-1]['opening_mm']:
        raise ValueError(f"opening {opening_mm} mm is outside {rows[0]['opening_mm']}..{rows[-1]['opening_mm']} mm")
    for a, b in zip(rows, rows[1:]):
        if opening_mm <= b['opening_mm']:
            f = (opening_mm - a['opening_mm']) / (b['opening_mm'] - a['opening_mm'])
            return a[key] + (b[key] - a[key]) * f


def fingertip_mm(spec, opening_mm):
    """Fingertip distance along the tool from the wrist_roll joint: the four-bar moves it as the fingers open."""
    return _gripper_value(spec, opening_mm, 'fingertip_mm')


def crank_rad(spec, opening_mm):
    """Gripper servo angle for a finger opening."""
    return math.radians(_gripper_value(spec, opening_mm, 'crank_deg'))


def tcp_xyz_for_opening(spec, opening_mm):
    """The pad centre in gripper_link (m) at this opening; spec.tcp holds the value at the holding width."""
    behind = spec.raw['gripper_kinematics']['pad_center_behind_tip_mm']
    return (0.0, 0.0, -(fingertip_mm(spec, opening_mm) - behind) / 1000)


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
    for name, soft in spec.raw.get('soft_limits', {}).get('joints', {}).items():
        try:
            j = spec.joint(name)
        except KeyError:
            problems.append(f'{name}: soft limit names a joint the spec does not have')
            continue
        lo, hi = soft.get('lower', j.lower), soft.get('upper', j.upper)
        if lo < j.lower - 1e-9 or hi > j.upper + 1e-9 or lo >= hi:
            problems.append(f'{name}: soft limits {math.degrees(lo):.1f}..{math.degrees(hi):.1f} deg must sit inside the joint limits')
    names = {j.name for j in spec.joints}
    for pair in spec.raw.get('soft_limits', {}).get('pairs', []):
        missing = [n for n in pair['joints'] if n not in names]
        if missing:
            problems.append(f"soft limit pair names joints the spec does not have: {', '.join(missing)}")
    soft = spec.raw.get('soft_limits', {})
    if soft.get('tcp_min_radius_from_pan_axis_m', 0) >= soft.get('tcp_max_radius_from_pan_axis_m', math.inf):
        problems.append('soft limit TCP radius: the minimum must be under the maximum')
    problems += _gripper_problems(spec)
    for item in soft.get('floor', {}).get('frames', []):
        if not any(j.child == item['frame'] for j in spec.joints):
            problems.append(f"soft limit floor names a frame the spec does not have: {item['frame']}")
    pan = spec.joint('shoulder_pan')
    if abs(math.degrees(pan.upper - pan.lower) - BASE_PAN_RANGE_DEG) > 0.01:
        problems.append(f'shoulder_pan: range must be {BASE_PAN_RANGE_DEG} deg (D25)')
    return problems


def _gripper_problems(spec):
    table = spec.raw.get('gripper_kinematics')
    if table is None:
        return []
    problems = []
    rows = table['by_opening']
    openings = [r['opening_mm'] for r in rows]
    if openings != sorted(openings):
        return ['gripper_kinematics.by_opening must be sorted by opening_mm']
    j = spec.joint('gripper')
    for r in rows:
        if not j.lower - 1e-4 <= math.radians(r['crank_deg']) <= j.upper + 1e-4:
            problems.append(f"gripper crank {r['crank_deg']} deg at {r['opening_mm']} mm is outside the joint limits")
    held = tcp_xyz_for_opening(spec, table['holding_opening_mm'])
    if math.dist(held, spec.tcp['origin_xyz']) > 1e-4:
        problems.append(f"tcp origin {spec.tcp['origin_xyz']} is not the table value {held} at the holding width")
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
