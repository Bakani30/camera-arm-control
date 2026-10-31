"""Cable length and slack across each joint of shell v1, from the routing features in the CAD.

Run: freecadcmd cable_check.py (writes out/motion/cable_check.json)
A span is a straight line between the last fixing point on each side of a joint, plus MARGIN_MM. It gives a cable length
and how far a slack loop may bulge. It does not prove bend radius or strain: cable stiffness, fatigue and real connector
positions are not modelled, so this has no pass or fail.
"""
import json
import math
import os
import sys

os.environ["MOTION_SCENARIOS"] = "none"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import motion_test as T  # noqa: E402

B, M, WG = T.B, T.M, T.WG
import links_v1 as LK  # noqa: E402
V, Part = T.V, T.Part
MARGIN_MM = 20.0
EFFECTIVE = ("E_mid_compensated", "D_survey_compensated")


def clamp_slots():
    d = B.STS
    top = B.PAN.z + B.P["turntable_t"]
    along = B.unit(B.SH, V(B.PAN.x - 30, 0, top + 8))
    centre, angle = LK.servo_frame("sts", (B.SH.x, B.SH.z), along)
    y_back = B.SH_FACE - d["H"]
    return [LK.local(Part.Vertex(V(x, y_back - 2, 0)), centre, angle).Point for x in (-d["L"] / 2 - 4, d["L"] / 2 + 4)]


def upper_slot(t):
    mid_x, mid_z = LK.upper_mid()
    if t <= 0.5:
        x, z = B.SH.x + (mid_x - B.SH.x) * 2 * t, B.SH.z + (mid_z - B.SH.z) * 2 * t
    else:
        x, z = mid_x + (B.EL.x - mid_x) * (2 * t - 1), mid_z + (B.EL.z - mid_z) * (2 * t - 1)
    return V(x, B.FRONT[0], z)


def forearm_exit(from_elbow_mm):
    e, w = B.EL, B.WF
    length = math.hypot(w.x - e.x, w.z - e.z)
    t = from_elbow_mm if from_elbow_mm >= 0 else length + from_elbow_mm
    r = LK.H["tube_r"]
    yc = B.BACK[1] - r
    return V(e.x + (w.x - e.x) / length * t, yc - r, e.z + (w.z - e.z) / length * t)


def wrist_neck():
    d, c, w = WG.MS, WG.G["clear"], WG.G["wall"]
    x_b = B.WR.x - d["top"] - d["horn_t"]
    return V((B.WF.x + x_b) / 2, WG.wrist_horn_face(), (B.WF.z + B.WR.z - 3) / 2 - 8)


def palm_exit():
    layout = WG.layout()
    return V(layout["gx"], layout["cy"], layout["cz"] - 25)


def arc_for(chord, length):
    """Sagitta and radius of a circular arc of this length over this chord."""
    if length <= chord + 1e-6:
        return 0.0, math.inf
    lo, hi = 1e-6, math.pi - 1e-6              # half angle
    for _ in range(80):
        mid = (lo + hi) / 2
        if length * math.sin(mid) / mid > chord:
            lo = mid
        else:
            hi = mid
    radius = length / (2 * lo)
    return radius * (1 - math.cos(lo)), radius


def task_range(joint):
    values = []
    for name in EFFECTIVE:
        path = os.path.join(HERE, "out", "motion", name + ".json")
        if not os.path.exists(path):
            continue
        for move in json.load(open(path))["moves"]:
            if move["task"]:
                values += [s["q_deg"][joint] for s in move["samples"] if not s["unreachable"]]
    return (min(values), max(values)) if values else None


def inside_length(a, b, shapes):
    """Length of the straight line inside each part: the cable has to go round these instead."""
    line = Part.makeLine(a, b)
    return {name: round(line.common(shape).Length, 1) for name, shape in shapes.items()}


def span(arm, name, joint, a, part_a, b, part_b, near=()):
    lo, hi = (math.degrees(v) for v in T.arm_spec.soft_range(B.SPEC, joint))
    shapes = arm.shapes(40)
    rows = []
    for k in range(25):
        angle = lo + (hi - lo) * k / 24
        q = {joint: angle}
        pa, pb = arm.point(a, part_a, q), arm.point(b, part_b, q)
        solids = {n: B.posed(shapes[n], n, q) for n in (part_a, part_b, *near)}
        inside = inside_length(pa, pb, solids)
        through = sum(inside.values())
        chord = (pb - pa).Length
        rows.append(dict(angle=round(angle, 1), chord=round(chord, 1), through=round(through, 1), inside=inside,
                         route=round(chord + (math.pi / 2 - 1) * through, 1)))
    task = task_range(joint)
    in_task = [r for r in rows if task and task[0] <= r["angle"] <= task[1]]
    length = max(r["route"] for r in rows) + MARGIN_MM     # going round a part costs about pi/2 of the part's width
    tight = min(rows, key=lambda r: r["route"])
    sagitta, radius = arc_for(tight["route"], length)
    task_rows = in_task or rows
    task_length = max(r["route"] for r in task_rows) + MARGIN_MM
    task_sag, task_radius = arc_for(min(r["route"] for r in task_rows), task_length)
    return dict(span=name, joint=joint, soft_range_deg=[round(lo, 1), round(hi, 1)], task_range_deg=task,
                chord_min=min(r["chord"] for r in rows), chord_max=max(r["chord"] for r in rows), route_max=max(r["route"] for r in rows),
                cable_mm=round(length, 1), task_cable_mm=round(task_length, 1), task_sagitta_mm=round(task_sag, 1),
                worst_sagitta_mm=round(sagitta, 1),
                rows=rows)


def main():
    arm = T.Arm()
    first = upper_slot(0.3)
    slot = min(clamp_slots(), key=lambda p: (p - first).Length)
    spans = [
        span(arm, "column to upper link", "shoulder_lift", slot, "column", first, "upper_link", ("servo_shoulder", "servo_clamp_shoulder", "horn_shoulder")),
        span(arm, "upper link to forearm", "elbow_flex", upper_slot(0.7), "upper_link", forearm_exit(45.0), "forearm_back", ("forearm_front", "servo_elbow", "horn_elbow")),
        span(arm, "forearm to wrist", "wrist_flex", forearm_exit(-45.0), "forearm_back", wrist_neck(), "wrist", ("forearm_front", "servo_wrist_flex", "horn_wrist_flex")),
        span(arm, "wrist to palm", "wrist_roll", wrist_neck(), "wrist", palm_exit(), "gripper_palm", ("servo_wrist_roll", "horn_wrist_roll")),
    ]
    roll_span = (wrist_neck() - palm_exit()).Length
    z_top = T.BV.Z_TT if hasattr(T.BV, "Z_TT") else None
    out = dict(spans=spans, margin_mm=MARGIN_MM,
               pan=dict(wrap_radius_mm=B.P["cable_hole_r"], wrap_length_mm=round(2 * math.pi * B.P["cable_hole_r"], 1),
                        annulus_mm=[T.BV.B["tt_boss_r"], T.BV.B["ls_hole"] / 2], hole_d_mm=B.P["cable_hole_d"],
                        coil_height_mm=T.BV.B["ls_t"], turntable_z=z_top),
               roll_twist=dict(span_mm=round(roll_span, 1), deg_per_mm_task=round(90 / roll_span, 2),
                               deg_per_mm_spec=round(math.degrees(B.SPEC.joint("wrist_roll").upper) / roll_span, 2)),
               forearm_exit_slot_mm=(8.0, 8.0 + LK.H["exit_len"]), forearm_channel_d_mm=2 * LK.H["channel_r"])
    with open(os.path.join(HERE, "out", "motion", "cable_check.json"), "w") as f:
        json.dump(out, f, indent=1)
    for s in spans:
        print("%-24s %-14s chord %5.1f..%5.1f route max %5.1f cable %5.1f (task %5.1f) bulge %5.1f (task %5.1f)" % (
            s["span"], s["joint"], s["chord_min"], s["chord_max"], s["route_max"], s["cable_mm"], s["task_cable_mm"],
            s["worst_sagitta_mm"], s["task_sagitta_mm"]))
        worst = max(s["rows"], key=lambda r: r["through"])
        print("   most inside parts at %.1f deg: %s" % (worst["angle"], {k: v for k, v in worst["inside"].items() if v}))
    print(json.dumps({k: out[k] for k in ("pan", "roll_twist", "forearm_exit_slot_mm", "forearm_channel_d_mm")}))


main()
