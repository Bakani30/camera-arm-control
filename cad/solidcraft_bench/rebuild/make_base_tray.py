"""Write rebuild/base_tray.json: the perforated electronics tray of the base as a SolidCraft script.

Run (plain Python, from the repo root): python cad/solidcraft_bench/rebuild/make_base_tray.py
Same cuts as base_v1.build_base() for "base_tray": disc, pan servo cut-out, hole grid, lid boss
clearances, tie bar notch at 288 deg, four M3 holes. base_v1 keeps a grid hole only where
hypot(x, y) < r - wall - 6; SolidCraft expressions have no comparison or if(), so every grid circle
gets the switch on = max(0, sign(lim - d)) and a hole that is off moves `far` along x, out of the
part, where its cut removes nothing. The grid spans -K..K pitches, enough for r up to about 90 mm.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(HERE, "base_tray.json")
K = 7


def pan_x():
    sys.path.insert(0, REPO)
    import arm_spec
    s = arm_spec.load_spec()
    rot, pos = [[1, 0, 0], [0, 1, 0], [0, 0, 1]], [0.0, 0.0, 0.0]
    for j in s.joints:
        pos = [p + d for p, d in zip(pos, arm_spec._apply(rot, j.origin_xyz))]
        rot = arm_spec._matmul(rot, arm_spec._rpy(*j.origin_rpy))
        if j.name == "shoulder_pan":
            return pos[0] * 1000
    raise SystemExit("no shoulder_pan joint in arm_spec")


def main():
    p = lambda name, expr, comment=None, unit=None: {"command": "parameters.add", "params": dict(  # noqa: E731
        {"name": name, "expression": expr}, **({"comment": comment} if comment else {}),
        **({"unit": unit} if unit is not None else {}))}
    cut = lambda name, **kw: {"command": "solid.cylinder", "params": dict(  # noqa: E731
        height="tray_t + 2 mm", base=kw.pop("base"), operation="cut", targets=["Tray"], name=name, **kw)}
    commands = [
        p("cx", "%r mm" % pan_x(), "pan axis x (base_v1.CX = PAN.x); CY = 0"),
        p("r", "75 mm", "drum outer radius (base_v1.B r)"),
        p("wall", "3 mm"),
        p("tray_z", "8 mm"),
        p("tray_t", "2.5 mm"),
        p("pitch", "10 mm"),
        p("hole_d", "2.6 mm"),
        p("lid_boss_r", "66 mm"),
        p("boss_clear_r", "5.8 mm", "5 + clearance + 0.5"),
        p("m3_free", "3.4 mm"),
        p("m3_r", "55 mm"),
        p("sts_l", "45.2 mm"),
        p("sts_w", "24.7 mm"),
        p("shaft_off", "11 mm"),
        p("grow", "5.3 mm", "pan servo cut-out margin: clearance + 3 + 2"),
        p("lim", "r - wall - 6 mm", "grid holes only inside this radius"),
        p("far", "1000 mm", "where a grid hole that is off goes"),
        p("tie_a", "288 deg", "tie bar notch angle"),
        {"command": "solid.cylinder", "params": {"radius": "r - wall - 2 mm", "height": "tray_t",
                                                 "base": ["cx", 0, "tray_z"], "operation": "new",
                                                 "name": "Disc", "body_name": "Tray"}},
        {"command": "solid.box", "params": {"length": "sts_l + 2 * grow", "width": "sts_w + 2 * grow",
                                            "height": "tray_t + 2 mm",
                                            "corner": ["cx - shaft_off - sts_l / 2 - grow", "-sts_w / 2 - grow",
                                                       "tray_z - 1 mm"],
                                            "operation": "cut", "targets": ["Tray"], "name": "ServoCutout"}},
        {"command": "sketch.create", "params": {"plane": "XY", "offset": "tray_z - 1 mm", "name": "GridSketch"}},
    ]
    for i in range(-K, K + 1):
        for j in range(-K, K + 1):
            off = "(1 - max(0, sign(lim - sqrt((%d * pitch)^2 + (%d * pitch)^2)))) * far" % (i, j)
            commands.append({"command": "sketch.circle.center", "params": {
                "center": ["cx + %d * pitch + %s" % (i, off), "%d * pitch" % j], "diameter": "hole_d"}})
    commands += [
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.extrude", "params": {"sketch": "GridSketch", "distance": "tray_t + 2 mm",
                                                "operation": "cut", "targets": ["Tray"], "name": "Grid"}},
        cut("LidBossClear", radius="boss_clear_r", base=["cx + lid_boss_r", 0, "tray_z - 1 mm"]),
        {"command": "solid.pattern.circular", "params": {"features": ["LidBossClear"],
                                                         "axis": {"origin": ["cx", 0, 0], "dir": [0, 0, 1]},
                                                         "count": 4, "name": "LidBossClears"}},
        {"command": "sketch.create", "params": {"plane": "XY", "offset": "tray_z - 1 mm", "name": "TieSketch"}},
    ]
    # wall_cut(288, box(-wall - 13, 1, -12, 12)): x from the drum's outer wall, turned to tie_a
    corners = [("r - wall - 13 mm", "-12 mm"), ("r + 1 mm", "-12 mm"), ("r + 1 mm", "12 mm"), ("r - wall - 13 mm", "12 mm")]
    commands.append({"command": "sketch.line", "params": {"closed": True, "points": [
        ["cx + (%s) * cos(tie_a) - (%s) * sin(tie_a)" % (lx, ly), "(%s) * sin(tie_a) + (%s) * cos(tie_a)" % (lx, ly)]
        for lx, ly in corners]}})
    commands += [
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.extrude", "params": {"sketch": "TieSketch", "distance": "tray_t + 2 mm",
                                                "operation": "cut", "targets": ["Tray"], "name": "TieNotch"}},
        cut("M3Hole", diameter="m3_free", base=["cx + m3_r * cos(45 deg)", "m3_r * sin(45 deg)", "tray_z - 1 mm"]),
        {"command": "solid.pattern.circular", "params": {"features": ["M3Hole"],
                                                         "axis": {"origin": ["cx", 0, 0], "dir": [0, 0, 1]},
                                                         "count": 4, "name": "M3Holes"}},
    ]
    with open(OUT, "w") as f:
        json.dump({"commands": commands}, f, indent=1)
    on = sum(1 for i in range(-K, K + 1) for j in range(-K, K + 1) if math.hypot(i * 10, j * 10) < 66)
    on2 = sum(1 for i in range(-K, K + 1) for j in range(-K, K + 1) if math.hypot(i * 10, j * 10) < 68)
    print("->", OUT, "grid circles", (2 * K + 1) ** 2, "on at r 75:", on, "on at r 77:", on2)


if __name__ == "__main__":
    main()
