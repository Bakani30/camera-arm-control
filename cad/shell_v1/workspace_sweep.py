"""Part overlap over the poses the spec soft limits allow, with the wrist and pan included.

Run: freecadcmd workspace_sweep.py (writes out/motion/workspace_sweep.json; SWEEP_STEP_DEG sets the grid)
check_shell_v1.py sweeps shoulder x elbow only; the motion test found a collision that sweep cannot see.
Grid: shoulder x elbow x wrist_flex at each finger opening, with the pan at 0 and over a leg (36 deg).
SWEEP_RANDOM=n instead checks n random allowed poses, wrist roll included, to test limits tuned on the grid.
"""
import json
import math
import os
import random
import sys

os.environ["MOTION_SCENARIOS"] = "none"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import motion_test as T  # noqa: E402

B, M = T.B, T.M
OPENINGS = (57, 0)
PANS = (0.0, 36.0)


def grid(lo, hi, step):
    first = math.ceil(lo / step) * step
    return sorted({round(lo, 1), round(hi, 1), *range(int(first), int(hi) + 1, step)})


def random_sweep(arm, wanted, seed=20261031):
    rng = random.Random(seed)
    table = {"fixture_table": T.fixtures(M.SURVEY_LAYOUT, "none")["fixture_table"]}
    limits = {j: T.arm_spec.soft_range(B.SPEC, j) for j in M.ARM_JOINTS}
    tried, drawn, hits = 0, 0, []
    while tried < wanted:
        drawn += 1
        q = {j: rng.uniform(*limits[j]) for j in M.ARM_JOINTS}
        opening = rng.choice((57, 40, 20, 0))
        if T.arm_spec.soft_limit_problems(B.SPEC, q, opening):
            continue
        tried += 1
        pose = {k: math.degrees(v) for k, v in q.items()}
        posed = {n: B.posed(s, n, pose) for n, s in arm.shapes(opening).items()}
        posed.update(table)
        found = T.overlaps(posed, opening)
        if found:
            hits.append(dict(opening=opening, q={k: round(v, 1) for k, v in pose.items()}, pairs=sorted({a + "/" + b for a, b, _ in found})))
        if tried % 100 == 0:
            print("tried", tried, "of", drawn, "drawn, hits", len(hits), flush=True)
    with open(os.path.join(HERE, "out", "motion", "workspace_random.json"), "w") as f:
        json.dump(dict(seed=seed, drawn=drawn, tried=tried, hits=hits), f)
    print("random allowed poses", tried, "of", drawn, "drawn, with overlap", len(hits), flush=True)
    if hits:
        os._exit(1)


def main():
    step = int(os.environ.get("SWEEP_STEP_DEG", "15"))
    wanted = int(os.environ.get("SWEEP_RANDOM", "0"))
    if wanted:
        random_sweep(T.Arm(), wanted)
        return
    arm = T.Arm()
    table = {"fixture_table": T.fixtures(M.SURVEY_LAYOUT, "none")["fixture_table"]}
    ranges = {j: [math.degrees(v) for v in T.arm_spec.soft_range(B.SPEC, j)] for j in M.PITCH_JOINTS}
    tried, hits = 0, []
    for opening in OPENINGS:
        shapes = arm.shapes(opening)
        for lift in grid(*ranges["shoulder_lift"], step):
            for elbow in grid(*ranges["elbow_flex"], step):
                for wrist in grid(*ranges["wrist_flex"], step):
                    q = dict(shoulder_lift=lift, elbow_flex=elbow, wrist_flex=wrist)
                    for pan in PANS:
                        pose = dict(q, shoulder_pan=pan)                # the legs make the limits depend on the pan
                        if T.arm_spec.soft_limit_problems(B.SPEC, {k: math.radians(v) for k, v in pose.items()}, opening):
                            continue
                        tried += 1
                        posed = {n: B.posed(s, n, pose) for n, s in shapes.items()}
                        posed.update(table)
                        found = T.overlaps(posed, opening)
                        if found:
                            hits.append(dict(opening=opening, q=pose, pitch=lift + elbow + wrist,
                                             radius_mm=round(T.arm_spec.tcp_radius_m(B.SPEC, {k: math.radians(v) for k, v in pose.items()}) * 1000),
                                             tcp_z_mm=round(T.arm_spec.forward_kinematics(B.SPEC, {k: math.radians(v) for k, v in pose.items()})[2] * 1000),
                                             pairs=sorted({a + "/" + b for a, b, _ in found})))
                    if tried % 200 < len(PANS):
                        print("tried", tried, "hits", len(hits), flush=True)
    out = dict(step_deg=step, tried=tried, hits=hits)
    with open(os.path.join(HERE, "out", "motion", "workspace_sweep.json"), "w") as f:
        json.dump(out, f)
    print("allowed poses", tried, "with overlap", len(hits), flush=True)
    if hits:
        os._exit(1)


main()
