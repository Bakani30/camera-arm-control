"""Write rebuild/gripper_gear_crank_up.json: the upper gear + crank of the gripper as a SolidCraft script.

Run (plain Python, from the repo root): python cad/solidcraft_bench/rebuild/make_gear_crank.py
The involute tooth outline is wrist_gripper_v1.gear_xz() with the same points (module 1, 14 teeth,
20 deg, turned -56 deg = jaw_open_deg 34 - 90), sketched as one closed polyline on the XZ plane.
Those points are numbers, so the gear does not follow parameters; the crank, its end hole and the
centre holes do (link, phi). The layout numbers come from arm_spec, as shell_v1_model.joint_frames().
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(HERE, "gripper_gear_crank_up.json")


def wrist_roll():
    sys.path.insert(0, REPO)
    import arm_spec
    s = arm_spec.load_spec()
    rot, pos = [[1, 0, 0], [0, 1, 0], [0, 0, 1]], [0.0, 0.0, 0.0]
    for j in s.joints:
        pos = [p + d for p, d in zip(pos, arm_spec._apply(rot, j.origin_xyz))]
        rot = arm_spec._matmul(rot, arm_spec._rpy(*j.origin_rpy))
        if j.name == "wrist_roll":
            return [c * 1000 for c in pos]
    raise SystemExit("no wrist_roll joint in arm_spec")


def gear_points(cx, cz, rot_deg, m=1.0, n=14):
    """Same outline as wrist_gripper_v1.gear_xz(), as (x, z) points."""
    rp = m * n / 2
    rb, ra, rf = rp * math.cos(math.radians(20)), rp + m, rp - 1.25 * m
    inv = lambda a: math.tan(a) - a  # noqa: E731
    half_base = math.pi / (2 * n) + inv(math.radians(20))
    flank = []
    for i in range(7):
        r = rb + (ra - rb) * i / 6
        flank.append((r, half_base - inv(math.acos(rb / r))))
    pts = []
    for k in range(n):
        c = 2 * math.pi * k / n + math.radians(rot_deg)
        pts.append((rf, c - half_base - 0.08))
        pts += [(r, c - a) for r, a in flank]
        pts += [(r, c + a) for r, a in reversed(flank)]
        pts.append((rf, c + half_base + 0.08))
    return [(cx + r * math.cos(a), cz + r * math.sin(a)) for r, a in pts]


def shoelace(pts):
    return abs(sum(x0 * z1 - x1 * z0 for (x0, z0), (x1, z1) in zip(pts, pts[1:] + pts[:1]))) / 2


def main():
    wr = wrist_roll()
    cy, cz = wr[1], wr[2]
    gx, gz = wr[0] + 9.8, cz + 7.0                # layout(): gx = WR.x + 9.8, g_up = cz + rp
    y_horn = cy - 14.0 + 28.5 + 2.0               # y_bot + MS top + MS horn_t
    pts = gear_points(gx, gz, 34.0 - 90.0)
    p = lambda name, expr, comment=None: {"command": "parameters.add", "params": dict(  # noqa: E731
        {"name": name, "expression": expr}, **({"comment": comment} if comment else {}))}
    commands = [
        p("gx", "%r mm" % gx, "gear axis x (layout gx = WR.x + 9.8)"),
        p("gz", "%r mm" % gz, "gear axis z (layout g_up = WR.z + rp)"),
        p("y_horn", "%r mm" % y_horn, "top of the gripper servo horn = gear bottom"),
        p("gear_t", "4 mm"),
        p("link_t", "3 mm"),
        p("link", "40 mm", "crank length (wrist_gripper_v1.G link)"),
        p("phi", "34 deg", "jaw_open_deg"),
        p("band", "4 mm", "crank half width"),
        p("boss_r", "6 mm"),
        p("bore_d", "5 mm", "horn bore"),
        p("pin_free", "3.3 mm"),
        p("m2_free", "2.2 mm"),
        p("m2_off", "5.5 mm"),
        {"command": "sketch.create", "params": {"plane": "XZ", "offset": "y_horn", "name": "GearSketch"}},
        {"command": "sketch.line", "params": {"points": [[x, -z] for x, z in pts], "closed": True}},
        {"command": "sketch.constraint.fix", "params": {"entities": ["l%d" % (k + 1) for k in range(len(pts))],
                                                        "fixed": True}},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.extrude", "params": {"sketch": "GearSketch", "distance": "gear_t", "operation": "new",
                                                "name": "Gear", "body_name": "GearCrank"}},
        {"command": "sketch.create", "params": {"plane": "XZ", "offset": "y_horn + gear_t", "name": "CrankSketch"}},
        # band_xz() = this strip + a round cap at each end; the cap on the gear axis lies inside Boss
        # (slot sketches take only numeric points, so the strip is drawn as a polyline of expressions)
        {"command": "sketch.line", "params": {"closed": True, "points": [
            ["gx - band * sin(phi)", "-(gz + band * cos(phi))"],
            ["gx + link * cos(phi) - band * sin(phi)", "-(gz + link * sin(phi) + band * cos(phi))"],
            ["gx + link * cos(phi) + band * sin(phi)", "-(gz + link * sin(phi) - band * cos(phi))"],
            ["gx + band * sin(phi)", "-(gz - band * cos(phi))"]]}},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.extrude", "params": {"sketch": "CrankSketch", "distance": "link_t", "operation": "join",
                                                "targets": ["GearCrank"], "name": "Crank"}},
        {"command": "solid.cylinder", "params": {"radius": "band", "height": "link_t", "axis": "Y",
                                                 "base": ["gx + link * cos(phi)", "y_horn + gear_t", "gz + link * sin(phi)"],
                                                 "operation": "join", "targets": ["GearCrank"], "name": "EndCap"}},
        {"command": "solid.cylinder", "params": {"radius": "boss_r", "height": "link_t", "axis": "Y",
                                                 "base": ["gx", "y_horn + gear_t", "gz"], "operation": "join",
                                                 "targets": ["GearCrank"], "name": "Boss"}},
        {"command": "solid.cylinder", "params": {"diameter": "pin_free", "height": "gear_t + link_t + 2 mm", "axis": "Y",
                                                 "base": ["gx + link * cos(phi)", "y_horn - 1 mm", "gz + link * sin(phi)"],
                                                 "operation": "cut", "targets": ["GearCrank"], "name": "EndHole"}},
        {"command": "solid.cylinder", "params": {"diameter": "bore_d", "height": "gear_t + link_t + 2 mm", "axis": "Y",
                                                 "base": ["gx", "y_horn - 1 mm", "gz"], "operation": "cut",
                                                 "targets": ["GearCrank"], "name": "Bore"}},
    ]
    for s, name in ((-1, "HornScrewBack"), (1, "HornScrewFront")):
        commands.append({"command": "solid.cylinder", "params": {
            "diameter": "m2_free", "height": "gear_t + link_t + 2 mm", "axis": "Y",
            "base": ["gx %s m2_off" % ("-" if s < 0 else "+"), "y_horn - 1 mm", "gz"],
            "operation": "cut", "targets": ["GearCrank"], "name": name}})
    with open(OUT, "w") as f:
        json.dump({"commands": commands}, f, indent=1)
    print("->", OUT, len(pts), "gear points")
    print("gear outline area %.4f mm2 -> gear prism %.4f mm3 (no holes)" % (shoelace(pts), shoelace(pts) * 4.0))


if __name__ == "__main__":
    main()
