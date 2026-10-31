"""Run the task moves on the shell v1 CAD and report the errors of each move. Geometry and estimates, no hardware.

Run: freecadcmd motion_test.py (writes out/motion/<scenario>.json; MOTION_SCENARIOS and MOTION_SAMPLES narrow a run)

Each sample checks: IK reach and soft limits, part overlap (table, block, tray, button included), near misses,
joint torque (static, and with the acceleration cap), base tipping, and how far the fingers sit from the commanded TCP.
Masses: printed parts = solid x MASS_FILL (assumed, not sliced or weighed); the block is assumed to weigh BLOCK_G.
Not checked: cable strain, link flex, servo backlash, anything measured on a real part.
"""
import itertools
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
for _name in ("shell_v1_model", "base_v1", "links_v1", "wrist_gripper_v1", "arm_spec", "motion_moves"):
    sys.modules.pop(_name, None)
import FreeCAD as App  # noqa: E402
import Part  # noqa: E402
import shell_v1_model as B  # noqa: E402
import base_v1 as BV  # noqa: E402
import wrist_gripper_v1 as WG  # noqa: E402
import arm_spec  # noqa: E402
import motion_moves as M  # noqa: E402

V = App.Vector
OVERLAP_MM3 = 1.0
GRIP_CONTACT_MM3 = 100.0  # a pad on the block at the holding width: ~0.1 mm over the pad area
NEAR_MM = 3.0
TIP_MARGIN_MM = 20.0
MASS_FILL = 0.45
PLA_G_MM3 = 1.24e-3
BLOCK_G = 50.0
FIXED_G = {"servo_pan": 55, "servo_shoulder": 55, "servo_elbow": 55, "servo_wrist_flex": 55, "servo_wrist_roll": 20,
           "servo_gripper": 20, "base_lazy_susan": 70, "gripper_pins": 2, "bearing_shoulder": 22, "bearing_elbow": 22,
           "bearing_wrist_flex": 22}
CARRIER = {"shoulder_pan": "servo_pan", "shoulder_lift": "column", "elbow_flex": "upper_link",
           "wrist_flex": "forearm_front", "wrist_roll": "wrist"}
MID_LAYOUT = M.Layout(M.polar(0.20, 0), M.polar(0.20, 72), M.polar(0.16, -45), 0.07)
SCENARIOS = {  # name: (layout, tcp, moves)
    "A_survey_spec_tcp": (M.SURVEY_LAYOUT, M.SPEC_V0_TCP_M, M.move_list),
    "B_survey_shell_tcp": (M.SURVEY_LAYOUT, M.SHELL_TCP_M, M.move_list),
    "C_mid_shell_tcp": (MID_LAYOUT, M.SHELL_TCP_M, M.move_list),
    "D_survey_compensated": (M.SURVEY_LAYOUT, M.pad_center_tcp, M.compensated_move_list),
    "E_mid_compensated": (MID_LAYOUT, M.pad_center_tcp, M.compensated_move_list),
}


def tool_point(tcp, opening_mm):
    """The commanded TCP on the shell at q = 0: on the roll axis, where the fingers are."""
    point = tcp(opening_mm) if callable(tcp) else tcp
    return V(B.WR.x - point[2] * 1000, B.WR.y, B.WR.z)


def centered_box(cx, cy, z0, side, height, angle_deg):
    box = Part.makeBox(side, side, height, V(cx - side / 2, cy - side / 2, z0))
    box.rotate(V(cx, cy, z0), V(0, 0, 1), angle_deg)
    return box


def layout_angle(xy):
    return math.degrees(math.atan2(xy[1], xy[0] - M.PAN_X))


def fixtures(layout, block_state, button_pressed=False):
    """Scene solids in mm; z = 0 is the table the shell stands on. A pressed button has moved down by its travel."""
    side = M.BLOCK_SIZE * 1000
    tray_side, wall, floor = M.TRAY_SIDE * 1000, M.TRAY_WALL_H * 1000, M.TRAY_FLOOR * 1000
    tx, ty = (v * 1000 for v in layout.tray_xy)
    angle = layout_angle(layout.tray_xy)
    tray = centered_box(tx, ty, 0, tray_side, wall, angle).cut(
        centered_box(tx, ty, floor, tray_side - 4, wall, angle))
    bx, by = (v * 1000 for v in layout.button_xy)
    button_h = (M.BUTTON_H - (M.BUTTON_TRAVEL if button_pressed else 0)) * 1000 - (0.1 if button_pressed else 0)
    scene = {
        "fixture_table": Part.makeBox(1600, 1600, 20, V(-800, -800, -20)),
        "fixture_tray": tray,
        "fixture_button": Part.makeCylinder(M.BUTTON_D * 500, button_h, V(bx, by, 0)),
    }
    if block_state == "table":
        kx, ky = (v * 1000 for v in layout.block_xy)
        scene["fixture_block"] = centered_box(kx, ky, 0, side, side, layout_angle(layout.block_xy))
    elif block_state == "tray":
        scene["fixture_block"] = centered_box(tx, ty, floor, side, side, angle)
    return scene


def carried_block(center):
    half = M.BLOCK_SIZE * 500
    return Part.makeBox(2 * half, 2 * half, 2 * half, V(center.x - half, center.y - half, center.z - half))


class Arm:
    def __init__(self):
        self.parts, _ = B.build_all()
        self.gripper = {}
        self.mass = {n: self._mass(n, s) for n, (s, _) in self.parts.items()}
        self.rated = {j: B.SPEC.actuator(j)["rated_torque_kgcm"] for j in B.ORDER}
        self.accel = {j: math.radians(B.SPEC.accel_cap_dps2(j)) for j in B.ORDER}

    @staticmethod
    def _mass(name, shape):
        volume = sum(s.Volume for s in shape.Solids)
        com = V(0, 0, 0)
        for s in shape.Solids:
            com += s.CenterOfMass * (s.Volume / volume)
        if name in FIXED_G:
            return FIXED_G[name], com
        if name.startswith("horn_"):
            return 4.0, com
        return volume * PLA_G_MM3 * MASS_FILL, com

    def shapes(self, opening_mm):
        """Parts for a finger opening; only the gripper changes, so it is built once per opening."""
        key = round(opening_mm)
        if key not in self.gripper:
            self.gripper[key] = WG.build_gripper(WG.phi_for_opening(key))[0]
        return {**{n: s for n, (s, _) in self.parts.items()}, **{n: s for n, (s, _) in self.gripper[key].items()}}

    def point(self, p, part, q_deg):
        return B.posed(Part.Vertex(p), part, q_deg).Point

    def axis(self, joint, q_deg):
        origin, direction = B.J[joint]
        a = self.point(origin, CARRIER[joint], q_deg)
        return a, (self.point(origin + direction, CARRIER[joint], q_deg) - a).normalize()

    def loads(self, q_deg, block_g, force_n, tool):
        """{joint: (static, with acceleration)} in kg.cm: gravity and the TCP force, then the inertia at the cap."""
        tcp = self.point(tool, "gripper_palm", q_deg)
        out = {}
        for joint in B.ORDER:
            o, a = self.axis(joint, q_deg)
            tau, inertia = 0.0, 0.0
            for name, (m, c) in self.mass.items():
                if joint not in B.moved_by(name):
                    continue
                r = self.point(c, name, q_deg) - o
                tau += r.cross(V(0, 0, -m * 9.81e-3)).dot(a)
                inertia += m * (r - a * r.dot(a)).Length ** 2
            r = tcp - o
            tau += r.cross(V(0, 0, force_n - block_g * 9.81e-3)).dot(a)
            inertia += block_g * (r - a * r.dot(a)).Length ** 2
            static = abs(tau) / 9.81 / 10
            dynamic = inertia * 1e-9 * self.accel[joint] * 100 / 9.81  # g mm2 -> kg m2; N m -> kg cm
            out[joint] = (round(static, 2), round(static + dynamic, 2))
        return out

    def sensitivity_mm_per_01deg(self, q_deg, tool):
        """TCP movement if every joint is off by 0.1 degree (root sum of squares)."""
        tcp = self.point(tool, "gripper_palm", q_deg)
        total = 0.0
        for joint in B.ORDER:
            o, a = self.axis(joint, q_deg)
            total += (a.cross(tcp - o).Length * math.radians(0.1)) ** 2
        return round(math.sqrt(total), 3)

    def tip_margin_mm(self, q_deg, block_g, tool):
        """Distance from the whole machine's CoM to the leg-tip outline, without the clamp; negative tips over."""
        total, moment = 0.0, V(0, 0, 0)
        for name, (m, c) in self.mass.items():
            total += m
            moment += self.point(c, name, q_deg) * m
        tcp = self.point(tool, "gripper_palm", q_deg)
        total += block_g
        moment += tcp * block_g
        com = moment * (1.0 / total)
        radius = math.hypot(com.x - B.PAN.x, com.y - B.PAN.y)
        angle = math.degrees(math.atan2(com.y - B.PAN.y, com.x - B.PAN.x)) % 360
        tips = sorted((180 + 72 * k) % 360 for k in range(BV.B["legs"]))
        lower = max([t for t in tips if t <= angle] or [tips[-1] - 360])
        half = math.radians(36.0)
        edge = BV.B["leg_tip_r"] * math.cos(half) / math.cos(math.radians(angle - lower) - half)
        return round(edge - radius, 1)


def bbox_gap(a, b):
    gaps = (a.XMin - b.XMax, b.XMin - a.XMax, a.YMin - b.YMax, b.YMin - a.YMax, a.ZMin - b.ZMax, b.ZMin - a.ZMax)
    return max(gaps)


def group(name):
    return "fixture" if name.startswith("fixture") else tuple(B.moved_by(name))


def pairs(posed):
    """Part pairs that can matter: different links, and at least one moving."""
    for a, b in itertools.combinations(posed, 2):
        ga, gb = group(a), group(b)
        if ga == gb or (ga in ("fixture", ()) and gb in ("fixture", ())):
            continue
        if {a, b} & {"carried_block"} and (a.startswith("gripper") or b.startswith("gripper")):
            continue                                   # the fingers hold it on purpose
        yield a, b


def is_grip(a, b):
    names = {a, b}
    return "fixture_block" in names and any(n.startswith("gripper") for n in names)


def overlaps(posed, opening_mm):
    hits = []
    holding = opening_mm <= M.HOLD_MM + 0.5
    for a, b in pairs(posed):
        if bbox_gap(posed[a].BoundBox, posed[b].BoundBox) > 0:
            continue
        volume = posed[a].common(posed[b]).Volume
        if volume > (GRIP_CONTACT_MM3 if holding and is_grip(a, b) else OVERLAP_MM3):
            hits.append((a, b, round(volume, 1)))
    return hits


def near_misses(posed, baseline, opening_mm):
    out = []
    holding = opening_mm <= M.HOLD_MM + 0.5
    for a, b in pairs(posed):
        if (a, b) in baseline or bbox_gap(posed[a].BoundBox, posed[b].BoundBox) > NEAR_MM:
            continue
        if {a, b} == {"fixture_table", "carried_block"} or (holding and is_grip(a, b)):
            continue                                   # it was just on the table, or the fingers are on it
        distance = posed[a].distToShape(posed[b])[0]
        if 0 < distance < NEAR_MM:
            out.append((a, b, round(distance, 2)))
    return out


def design_contacts(arm):
    """Pairs already closer than NEAR_MM at q = 0: joints and fits by design, not near misses."""
    posed = dict(arm.shapes(32))
    close = set()
    for a, b in pairs(posed):
        if bbox_gap(posed[a].BoundBox, posed[b].BoundBox) <= NEAR_MM and posed[a].distToShape(posed[b])[0] < NEAR_MM:
            close.add((a, b))
    return close


def static_layout_problems(layout, arm):
    """Fixtures placed on top of the base or its legs: the layout itself is wrong."""
    scene = fixtures(layout, "table")
    hits = []
    for name, shape in scene.items():
        if name == "fixture_table":
            continue
        for part, (fixed, _) in arm.parts.items():
            if B.moved_by(part):
                continue
            if bbox_gap(shape.BoundBox, fixed.BoundBox) <= 0 and shape.common(fixed).Volume > OVERLAP_MM3:
                hits.append((name, part))
    return hits


def run_move(arm, move, layout, tcp, samples, baseline):
    plan = M.plan_move(B.SPEC, move, samples, tcp)
    scene = fixtures(layout, move.block, move.force_n > 0 or move.name.startswith("11_"))
    block_g = BLOCK_G if move.block == "carried" else 0.0
    rows = []
    for index, sample in enumerate(plan.samples):
        q_deg = {k: math.degrees(v) for k, v in sample.q.items()}
        row = dict(q_deg={k: round(v, 2) for k, v in q_deg.items()}, opening_mm=round(sample.opening_mm, 1),
                   unreachable=sample.unreachable, limits=sample.limit_problems)
        if not sample.unreachable:
            tool = tool_point(tcp, sample.opening_mm)
            parts = arm.shapes(sample.opening_mm)
            posed = {n: B.posed(s, n, q_deg) for n, s in parts.items()}
            posed.update(scene)
            if move.block == "carried":
                posed["carried_block"] = B.posed(carried_block(tool_point(tcp, M.HOLD_MM)), "gripper_palm", q_deg)
            row["overlaps"] = overlaps(posed, sample.opening_mm)
            if index in (0, samples // 2, samples - 1):
                row["near"] = near_misses(posed, baseline, sample.opening_mm)
            row["loads"] = arm.loads(q_deg, block_g, move.force_n, tool)
            row["tip_margin_mm"] = arm.tip_margin_mm(q_deg, block_g, tool)
            row["sensitivity_mm"] = arm.sensitivity_mm_per_01deg(q_deg, tool)
            finger = arm.point(tool, "gripper_palm", q_deg)
            fixed_tcp = tcp(sample.opening_mm) if callable(tcp) else tcp
            commanded = V(*[c * 1000 for c in M.tcp_position(B.SPEC, sample.q, fixed_tcp)])
            row["tcp_to_fingers_mm"] = round((finger - commanded).Length, 2)
            row["finger_center_mm"] = [round(finger.x, 1), round(finger.y, 1), round(finger.z, 1)]
        rows.append(row)
    return dict(name=move.name, task=move.task, time_s=round(plan.time_s, 2), slowest=plan.slowest_joint,
                block=move.block, samples=rows)


def summarize(arm, result):
    reachable = [s for s in result["samples"] if not s["unreachable"]]
    worst = {}
    for joint in B.ORDER:
        values = [s["loads"][joint] for s in reachable]
        if values:
            worst[joint] = (max(v[0] for v in values), max(v[1] for v in values))
    errors = dict(
        unreachable=sum(s["unreachable"] for s in result["samples"]),
        limits=sorted({p.split(":")[0] for s in reachable for p in s["limits"]}),
        overlaps=sorted({"%s/%s" % (a, b) for s in reachable for a, b, _ in s["overlaps"]}),
        near=sorted({"%s/%s %.1f" % (a, b, d) for s in reachable for a, b, d in s.get("near", [])}),
        over_rated=sorted(j for j, v in worst.items() if v[0] > arm.rated[j]),
        over_rated_moving=sorted(j for j, v in worst.items() if v[1] > arm.rated[j]),
        low_tip_margin=min([s["tip_margin_mm"] for s in reachable] or [None], key=lambda v: 1e9 if v is None else v),
    )
    result["worst_loads"] = worst
    result["errors"] = errors
    return errors


def main():
    wanted = os.environ.get("MOTION_SCENARIOS")
    if wanted == "none":                               # imported by another script for its helpers
        return
    samples = int(os.environ.get("MOTION_SAMPLES", "9"))
    out_dir = os.path.join(HERE, "out", "motion", "tube" if os.environ.get("SHELL_FOREARM") == "tube" else "")
    os.makedirs(out_dir, exist_ok=True)
    arm = Arm()
    baseline = design_contacts(arm)
    print("design contacts ignored for near misses:", len(baseline), flush=True)
    for name, (layout, tcp, moves) in SCENARIOS.items():
        if wanted and name not in wanted.split(","):
            continue
        report = dict(scenario=name, layout_problems=static_layout_problems(layout, arm), moves=[])
        print("==", name, "layout problems:", report["layout_problems"], flush=True)
        for move in moves(layout):
            result = run_move(arm, move, layout, tcp, samples, baseline)
            errors = summarize(arm, result)
            report["moves"].append(result)
            print("%-26s %5.2fs %s" % (move.name, result["time_s"], json.dumps(errors)), flush=True)
        with open(os.path.join(out_dir, name + ".json"), "w") as f:
            json.dump(report, f)
    print("done", flush=True)


main()
