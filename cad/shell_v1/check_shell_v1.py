"""Checks for shell v1: joint axes vs the spec FK, and part overlap while each joint sweeps its range.

Run: freecadcmd check_shell_v1.py (or python run_shell_v1.py --check)
Overlap = volume of the boolean common of two parts on different links (mm3); > 1 mm3 counts.
Single-joint sweeps from q = 0 plus a few combined poses; not a full workspace search.
"""
import itertools
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import shell_v1_model as B  # noqa: E402
import arm_spec  # noqa: E402

LIMIT_MM3 = 1.0
STEP_DEG = 10


def fk_check():
    """Shell joint origins are taken from the spec, so FK must match exactly."""
    bad = 0
    for q in ({}, {"shoulder_lift": math.radians(-60), "elbow_flex": math.radians(45)},
              {"shoulder_pan": math.radians(90), "wrist_flex": math.radians(30)}):
        tcp = arm_spec.forward_kinematics(B.SPEC, q, frame="gripper_link")
        q_deg = {k: math.degrees(v) for k, v in q.items()}
        p = B.Part.Vertex(B.J["wrist_roll"][0])
        p = B.posed(p, "gripper_palm", q_deg).Point
        err = math.dist([c * 1000 for c in tcp], [p.x, p.y, p.z])
        print("FK wrist_roll origin %s: shell vs spec %.4f mm" % (q_deg, err))
        bad += err > 0.01
    return bad


def overlaps(parts, q_deg):
    posed = {n: B.posed(s, n, q_deg) for n, (s, c) in parts.items()}
    hits = []
    for a, b in itertools.combinations(posed, 2):
        if B.moved_by(a) == B.moved_by(b):
            continue
        sa, sb = posed[a], posed[b]
        if not sa.BoundBox.intersect(sb.BoundBox):
            continue
        v = sa.common(sb).Volume
        if v > LIMIT_MM3:
            hits.append((a, b, round(v, 1)))
    return hits


def gripper_sweep():
    """Crank from closed (fingers' teeth touching) to fully open: overlaps between gripper parts."""
    import wrist_gripper_v1 as WG
    lo, hi = WG.phi_for_opening(0.0), 64.0
    angles = [lo] + list(range(int(lo) // 5 * 5 + 5, int(hi) + 1, 5))
    bad = 0
    for phi in angles:
        g, info = WG.build_gripper(phi)
        hits = []
        for a, b in itertools.combinations(g, 2):
            sa, sb = g[a][0], g[b][0]
            if sa.BoundBox.intersect(sb.BoundBox):
                v = sa.common(sb).Volume
                if v > LIMIT_MM3:
                    hits.append((a, b, round(v, 1)))
        bad += bool(hits)
        print("gripper crank %5.1f deg, opening %5.1f mm: %s" % (phi, info["opening_mm"], hits or "clear"))
    return bad


def soft_box_sweep(parts, step=10):
    """Shoulder x elbow grid of poses the spec soft limits allow (wrist 0, pan 0): any overlap counts."""
    lo_s, hi_s = (math.degrees(v) for v in arm_spec.soft_range(B.SPEC, "shoulder_lift"))
    lo_e, hi_e = (math.degrees(v) for v in arm_spec.soft_range(B.SPEC, "elbow_flex"))
    grid = lambda lo, hi: sorted({round(lo, 1), round(hi, 1), *range(int(math.ceil(lo / step) * step), int(hi) + 1, step)})
    hits, tried = [], 0
    for sl in grid(lo_s, hi_s):
        for el in grid(lo_e, hi_e):
            q = {"shoulder_lift": sl, "elbow_flex": el}
            if arm_spec.soft_limit_problems(B.SPEC, {k: math.radians(v) for k, v in q.items()}):
                continue                                   # the adapter never sends this pose
            tried += 1
            h = overlaps(parts, q)
            if h:
                hits.append((sl, el, sorted({a + "/" + b for a, b, v in h})[:4]))
    print("soft-limit sweep shoulder %.0f..%.0f x elbow %.0f..%.0f step %d: %d allowed poses, %d colliding"
          % (lo_s, hi_s, lo_e, hi_e, step, tried, len(hits)))
    for sl, el, names in hits:
        print("   shoulder %6.1f elbow %6.1f: %s" % (sl, el, names))
    return len(hits)


def main():
    parts, _ = B.build_all()
    fails = fk_check()
    grip_bad = gripper_sweep()
    lim = {j.name: (math.degrees(j.lower), math.degrees(j.upper)) for j in B.SPEC.joints}
    report = {}
    for jn in ["shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "shoulder_pan"]:
        lo, hi = lim[jn]
        bad = []
        a = math.ceil(lo / STEP_DEG) * STEP_DEG
        angles = sorted({round(x, 1) for x in (lo, hi, *range(int(a), int(hi) + 1, STEP_DEG))})
        if jn == "shoulder_pan":
            angles = [-180, -90, 90, 180]
        for ang in angles:
            h = overlaps(parts, {jn: ang})
            if h:
                bad.append((round(ang, 1), h))
        report[jn] = bad
        free = [x for x in angles if x not in [b[0] for b in bad]]
        print("%s: %d/%d poses clear; clear angles %s" % (jn, len(angles) - len(bad), len(angles), free))
        for ang, h in bad:
            print("   %6.1f deg: %s" % (ang, h))
    for q in ({"shoulder_lift": -45, "elbow_flex": 55, "wrist_flex": 70},
              {"shoulder_lift": 30, "elbow_flex": -60, "wrist_flex": 40, "wrist_roll": 70}):
        print("combined %s: %s" % (q, overlaps(parts, q) or "clear"))
    soft_bad = soft_box_sweep(parts)
    print("FK mismatches:", fails, "| gripper poses with overlaps:", grip_bad, "| allowed poses with overlaps:", soft_bad)


main()
