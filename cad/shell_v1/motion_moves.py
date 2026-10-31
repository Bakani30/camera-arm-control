"""Task moves for the motion test: top-down IK and paths, with no FreeCAD needed (motion_test.py runs them on the CAD).

Coordinates are the spec base frame in metres: x forward, y left, z up. In the shell, z = 0 is the table.
SURVEY_LAYOUT comes from the camera-teleop survey: block ~25 cm, tray ~25 cm to the side, button ~20 cm from
the pan axis. Tray and button sizes are assumptions until the real ones exist.
"""
import math
from dataclasses import dataclass, field, replace
from types import SimpleNamespace

import arm_spec
from arm_spec import forward_kinematics, soft_limit_problems

SPEC_V0_TCP_M = (-0.0079, -0.000218121, -0.0981274)  # SO-101 point that spec v0 used; off the roll axis
SHELL_TCP_M = (0.0, 0.0, -0.098)  # on the roll axis at the v0 distance, without the opening correction
TOOL_BACK_M = 0.05
ARM_JOINTS = ('shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex', 'wrist_roll')
PITCH_JOINTS = ('shoulder_lift', 'elbow_flex', 'wrist_flex')
IK_TOLERANCE_M = 2e-5
IK_ITERATIONS = 20
IK_MAX_STEP_RAD = 0.25
IK_DAMPING = 1e-6
JACOBIAN_STEP_RAD = 1e-5

PAN_X = 0.0388353
BLOCK_SIZE = 0.040
OPEN_MM, HOLD_MM, CLOSED_MM = 57.0, 40.0, 0.0
TRAY_SIDE, TRAY_WALL_H, TRAY_FLOOR = 0.120, 0.025, 0.003  # assumed
BUTTON_D, BUTTON_H, BUTTON_TRAVEL = 0.030, 0.025, 0.003   # assumed
BUTTON_FORCE_N = 5.0                                      # assumed
FINGERTIP_PAST_TCP = 0.002
_SPEC = arm_spec.load_spec()
PAD_CENTER_BEHIND_TIP_MM = _SPEC.raw['gripper_kinematics']['pad_center_behind_tip_mm']
GRASP_Z = BLOCK_SIZE / 2
PLACE_Z = TRAY_FLOOR + 0.005 + BLOCK_SIZE / 2
PRESS_Z = BUTTON_H + FINGERTIP_PAST_TCP - BUTTON_TRAVEL


def polar(radius_m, angle_deg):
    """Table position from the pan axis; 0 deg is forward, positive is the robot's left."""
    return (PAN_X + radius_m * math.cos(math.radians(angle_deg)), radius_m * math.sin(math.radians(angle_deg)))


@dataclass(frozen=True)
class Layout:
    block_xy: tuple
    tray_xy: tuple
    button_xy: tuple
    above_z: float


SURVEY_LAYOUT = Layout(polar(0.25, 0), polar(0.25, 90), polar(0.20, -45), 0.10)


class Unreachable(Exception):
    pass


@dataclass(frozen=True)
class Pose:
    xyz: tuple
    pitch_deg: float = 90.0    # 0 = tool level, 90 = straight down
    roll_deg: float = 0.0
    opening_mm: float = OPEN_MM


@dataclass(frozen=True)
class Move:
    name: str
    start: Pose
    goal: Pose
    task: bool = True            # part of the pick, place and press sequence
    block: str = 'table'         # table, carried, tray or none
    force_n: float = 0.0         # upward reaction at the TCP (pressing the button)
    pan_sweep_deg: tuple = None  # joint-space sweep of the pan instead of a straight TCP path
    arc: bool = False            # go round the pan axis instead of straight across it


@dataclass
class Sample:
    q: dict
    opening_mm: float
    limit_problems: list = field(default_factory=list)
    unreachable: bool = False


@dataclass
class Plan:
    move: Move
    samples: list
    time_s: float
    slowest_joint: str
    max_step_deg: float = 0.0


def fingertip_mm(opening_mm):
    return arm_spec.fingertip_mm(_SPEC, opening_mm)


def pad_center_tcp(opening_mm):
    return arm_spec.tcp_xyz_for_opening(_SPEC, opening_mm)


def _with_tcp(spec, tcp):
    if tcp is None:
        return spec
    return SimpleNamespace(joints=spec.joints, tcp={**spec.tcp, 'origin_xyz': list(tcp)})


def tcp_position(spec, q, tcp=None):
    """TCP in metres, for the spec TCP or another point given in gripper_link."""
    return forward_kinematics(_with_tcp(spec, tcp), q)


def tool_direction(spec, q):
    """Unit vector the fingers point along; the spec TCP lies along gripper_link -z."""
    x, y, z = spec.tcp['origin_xyz']
    tip = forward_kinematics(spec, q)
    back = forward_kinematics(_with_tcp(spec, (x, y, z + TOOL_BACK_M)), q)
    return tuple((a - b) / TOOL_BACK_M for a, b in zip(tip, back))


def _solve3(a, b):
    """Gaussian elimination with pivoting for the 3 x 3 IK step."""
    m = [row[:] + [v] for row, v in zip(a, b)]
    for i in range(3):
        pivot = max(range(i, 3), key=lambda r: abs(m[r][i]))
        m[i], m[pivot] = m[pivot], m[i]
        if abs(m[i][i]) < 1e-12:
            raise Unreachable('singular IK step')
        for r in range(3):
            if r != i:
                f = m[r][i] / m[i][i]
                m[r] = [x - f * y for x, y in zip(m[r], m[i])]
    return [m[i][3] / m[i][i] for i in range(3)]


def _newton(spec, pose, tcp, start):
    """Pan, lift and elbow from a start guess, wrist tied to the pitch; None if it does not converge."""
    pitch, roll = math.radians(pose.pitch_deg), math.radians(pose.roll_deg)

    def full(values):
        return dict(shoulder_pan=values[0], shoulder_lift=values[1], elbow_flex=values[2],
                    wrist_flex=pitch - values[1] - values[2], wrist_roll=roll)

    def residual(values):
        return [a - b for a, b in zip(tcp_position(spec, full(values), tcp), pose.xyz)]

    v = list(start)
    for _ in range(IK_ITERATIONS):
        r = residual(v)
        if max(abs(c) for c in r) < IK_TOLERANCE_M:
            return full(v)
        columns = []
        for i in range(3):
            moved = v[:]
            moved[i] += JACOBIAN_STEP_RAD
            columns.append([(a - b) / JACOBIAN_STEP_RAD for a, b in zip(residual(moved), r)])
        jac = [[columns[c][row] for c in range(3)] for row in range(3)]
        jtj = [[sum(jac[k][i] * jac[k][j] for k in range(3)) + (IK_DAMPING if i == j else 0) for j in range(3)]
               for i in range(3)]
        jtr = [-sum(jac[k][i] * r[k] for k in range(3)) for i in range(3)]
        try:
            step = _solve3(jtj, jtr)
        except Unreachable:
            return None
        largest = max(abs(s) for s in step)
        scale = min(1.0, IK_MAX_STEP_RAD / largest) if largest else 1.0
        v = [a + scale * s for a, s in zip(v, step)]
    return None


def _distance(a, b):
    return sum(abs(a[name] - b[name]) for name in a)


def _wrap(angle):
    return (angle + math.pi) % (2 * math.pi) - math.pi


def _plane_angle(v):  # angle in the arm plane; positive tilts forward down, like the pitch joints
    return math.atan2(-v[1], v[0])


def _rotated(v, angle):
    return v[0] * math.cos(angle) + v[1] * math.sin(angle), -v[0] * math.sin(angle) + v[1] * math.cos(angle)


def _branches(spec, pose, tcp):
    """Both elbow solutions from the link vectors at q = 0, as (pan, lift, elbow) starts for Newton."""
    points = [forward_kinematics(spec, {}, frame) for frame in ('upper_arm_link', 'lower_arm_link', 'wrist_link')]
    points.append(tcp_position(spec, {}, tcp))
    plane = [(p[0], p[2]) for p in points]
    a, b, c = [(q[0] - p[0], q[1] - p[1]) for p, q in zip(plane, plane[1:])]
    pan = -math.atan2(pose.xyz[1], pose.xyz[0] - PAN_X)
    radius = math.hypot(pose.xyz[0] - PAN_X, pose.xyz[1])
    tip = _rotated(c, math.radians(pose.pitch_deg))
    d = (radius + PAN_X - plane[0][0] - tip[0], pose.xyz[2] - plane[0][1] - tip[1])
    la, lb = math.hypot(*a), math.hypot(*b)
    cosine = (d[0] ** 2 + d[1] ** 2 - la ** 2 - lb ** 2) / (2 * la * lb)
    if abs(cosine) > 1:
        return []
    starts = []
    for sign in (-1, 1):
        elbow = _wrap(sign * math.acos(cosine) + _plane_angle(a) - _plane_angle(b))
        turned = _rotated(b, elbow)
        lift = _wrap(_plane_angle(d) - _plane_angle((a[0] + turned[0], a[1] + turned[1])))
        starts.append((pan, lift, elbow))
    return starts


def solve_ik(spec, pose, tcp=None, seed=None):
    """Joint angles (rad) that put the TCP at pose.xyz with a fixed tool pitch. Raises Unreachable.

    With a seed, takes the elbow branch nearest to it. Without one, the branch that breaks the
    fewest soft limits, then the elbow-up one.
    """
    found = [q for start in _branches(spec, pose, tcp) for q in [_newton(spec, pose, tcp, start)] if q]
    if not found:
        raise Unreachable(f'no IK solution for {pose.xyz} at pitch {pose.pitch_deg}')
    if seed:
        # keep the pan on the seed's side of the wrap, or a path past +-180 deg reads as a full turn back
        turns = round((seed['shoulder_pan'] - found[0]['shoulder_pan']) / (2 * math.pi))
        for q in found:
            q['shoulder_pan'] += turns * 2 * math.pi
        return min(found, key=lambda q: _distance(q, seed))
    return min(found, key=lambda q: (len(soft_limit_problems(spec, q, pose.opening_mm)), q['elbow_flex']))


def joint_time_s(travel_deg, speed_dps, accel_dps2):
    """Time of a trapezoid speed profile over travel_deg; short moves never reach the speed cap."""
    if travel_deg <= 0:
        return 0
    if travel_deg >= speed_dps ** 2 / accel_dps2:
        return travel_deg / speed_dps + speed_dps / accel_dps2
    return 2 * math.sqrt(travel_deg / accel_dps2)


def _timing(spec, samples):
    times = {}
    for name in ARM_JOINTS:
        travel = sum(abs(a.q[name] - b.q[name]) for a, b in zip(samples, samples[1:]))
        times[name] = joint_time_s(math.degrees(travel), spec.speed_cap_dps(name), spec.accel_cap_dps2(name))
    slowest = max(times, key=times.get)
    return times[slowest], slowest


def _lerp(a, b, f):
    return a + (b - a) * f


def _arc_point(a, b, f):
    """Between two points going round the pan axis the short way, radius and height changing evenly."""
    ra, rb = math.hypot(a[0] - PAN_X, a[1]), math.hypot(b[0] - PAN_X, b[1])
    ta = math.atan2(a[1], a[0] - PAN_X)
    turn = _wrap(math.atan2(b[1], b[0] - PAN_X) - ta)
    radius, angle = _lerp(ra, rb, f), ta + turn * f
    return (PAN_X + radius * math.cos(angle), radius * math.sin(angle), _lerp(a[2], b[2], f))


def _pose_at(move, f):
    a, b = move.start, move.goal
    xyz = _arc_point(a.xyz, b.xyz, f) if move.arc else tuple(_lerp(p, g, f) for p, g in zip(a.xyz, b.xyz))
    return Pose(xyz, _lerp(a.pitch_deg, b.pitch_deg, f), _lerp(a.roll_deg, b.roll_deg, f),
                _lerp(a.opening_mm, b.opening_mm, f))


def plan_move(spec, move, samples=9, tcp=None):
    """TCP path sampled evenly (or a pan sweep). tcp is None, a point in gripper_link, or a function of the opening.
    A sample IK cannot reach keeps the last angles and is marked, and any before the first reachable one
    sit at q = 0. Do not read collisions from marked samples."""
    out, q = [], None
    for i in range(samples):
        f = i / (samples - 1)
        pose = _pose_at(move, f)
        unreachable = False
        try:
            q = solve_ik(spec, pose, tcp(pose.opening_mm) if callable(tcp) else tcp, q)
        except Unreachable:
            unreachable = True
            if q is None:
                q = dict(shoulder_pan=-math.atan2(pose.xyz[1], pose.xyz[0] - PAN_X), shoulder_lift=0.0, elbow_flex=0.0,
                         wrist_flex=0.0, wrist_roll=math.radians(pose.roll_deg))
        posed = dict(q)
        if move.pan_sweep_deg:
            posed['shoulder_pan'] = math.radians(_lerp(*move.pan_sweep_deg, f))
        out.append(Sample(posed, pose.opening_mm, soft_limit_problems(spec, posed, pose.opening_mm), unreachable))
    time_s, slowest = _timing(spec, out)
    steps = [abs(a.q[n] - b.q[n]) for a, b in zip(out, out[1:]) if not (a.unreachable or b.unreachable) for n in a.q]
    return Plan(move, out, time_s, slowest, math.degrees(max(steps, default=0.0)))


READY = Pose((0.25, 0.0, 0.16), pitch_deg=60.0)


def move_list(layout=SURVEY_LAYOUT):
    above_block = Pose((*layout.block_xy, layout.above_z))
    at_block = Pose((*layout.block_xy, GRASP_Z))
    held = replace(at_block, opening_mm=HOLD_MM)
    lifted = Pose((*layout.block_xy, layout.above_z), opening_mm=HOLD_MM)
    above_tray = Pose((*layout.tray_xy, layout.above_z), opening_mm=HOLD_MM)
    in_tray = Pose((*layout.tray_xy, PLACE_Z), opening_mm=HOLD_MM)
    released = replace(in_tray, opening_mm=OPEN_MM)
    rose = Pose((*layout.tray_xy, layout.above_z))
    above_button = Pose((*layout.button_xy, layout.above_z), opening_mm=CLOSED_MM)
    pressed = Pose((*layout.button_xy, PRESS_Z), opening_mm=CLOSED_MM)
    return [
        Move('01_ready_to_above_block', READY, above_block),
        Move('02_descend_to_block', above_block, at_block),
        Move('03_close_on_block', at_block, held),
        Move('04_lift_block', held, lifted, block='carried'),
        Move('05_carry_to_tray', lifted, above_tray, block='carried'),
        Move('06_lower_into_tray', above_tray, in_tray, block='carried'),
        Move('07_open_release', in_tray, released, block='tray'),
        Move('08_rise_from_tray', released, rose, block='tray'),
        Move('09_go_to_button', rose, above_button, block='tray'),
        Move('10_press_button', above_button, pressed, block='tray', force_n=BUTTON_FORCE_N),
        Move('11_back_to_ready', pressed, READY, block='tray'),
        Move('12_roll_sweep_at_block', replace(at_block, roll_deg=-90.0), replace(at_block, roll_deg=90.0), task=False),
        Move('13_pan_sweep', READY, READY, task=False, block='none', pan_sweep_deg=(-179.9, 179.9)),
        Move('14_reach_near_table', READY, Pose((*polar(0.15, 0), GRASP_Z)), task=False, block='none'),
        Move('15_reach_far_table', READY, Pose((*polar(0.33, 0), GRASP_Z)), task=False, block='none'),
    ]


def compensated_move_list(layout=SURVEY_LAYOUT):
    """The same task with heights for a pad-centre TCP (pad_center_tcp) and arcs across the pan axis."""
    hover = BLOCK_SIZE + 0.005 + PAD_CENTER_BEHIND_TIP_MM / 1000 + 0.002  # open fingertips 7 mm over the block
    above_block = Pose((*layout.block_xy, hover))
    at_block = Pose((*layout.block_xy, GRASP_Z))
    held = replace(at_block, opening_mm=HOLD_MM)
    lifted = Pose((*layout.block_xy, hover), opening_mm=HOLD_MM)
    above_tray = Pose((*layout.tray_xy, hover), opening_mm=HOLD_MM)
    in_tray = Pose((*layout.tray_xy, PLACE_Z), opening_mm=HOLD_MM)
    released = replace(in_tray, opening_mm=OPEN_MM)
    rose = Pose((*layout.tray_xy, hover))
    tip_to_pad = PAD_CENTER_BEHIND_TIP_MM / 1000
    above_button = Pose((*layout.button_xy, BUTTON_H + 0.005 + tip_to_pad), opening_mm=CLOSED_MM)
    pressed = Pose((*layout.button_xy, BUTTON_H - BUTTON_TRAVEL + tip_to_pad), opening_mm=CLOSED_MM)
    return [
        Move('01_ready_to_above_block', READY, above_block),
        Move('02_descend_to_block', above_block, at_block),
        Move('03_close_on_block', at_block, held),
        Move('04_lift_block', held, lifted, block='carried'),
        Move('05_carry_to_tray', lifted, above_tray, block='carried', arc=True),
        Move('06_lower_into_tray', above_tray, in_tray, block='carried'),
        Move('07_open_release', in_tray, released, block='tray'),
        Move('08_rise_from_tray', released, rose, block='tray'),
        Move('09_go_to_button', rose, above_button, block='tray', arc=True),
        Move('10_press_button', above_button, pressed, block='tray', force_n=BUTTON_FORCE_N),
        Move('11_back_to_ready', pressed, READY, block='tray', arc=True),
        Move('12_roll_sweep_at_block', replace(at_block, roll_deg=-90.0), replace(at_block, roll_deg=90.0), task=False),
        Move('13_pan_sweep', READY, READY, task=False, block='none', pan_sweep_deg=(-179.9, 179.9)),
        Move('14_reach_near_table', READY, Pose((*polar(0.15, 0), GRASP_Z)), task=False, block='none'),
        Move('15_reach_far_table', READY, Pose((*polar(0.33, 0), GRASP_Z)), task=False, block='none'),
    ]
