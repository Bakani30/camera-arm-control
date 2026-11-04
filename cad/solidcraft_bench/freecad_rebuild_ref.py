"""FreeCAD reference for the three parts the bench rebuilds in SolidCraft, at the default parameters
and with one parameter changed per part.

Run: freecadcmd cad/solidcraft_bench/freecad_rebuild_ref.py
Adds keys to results/freecad_ref.json:
  turntable, turntable@tt_r=+5               base_v1.turntable() (in build_all() it is fused into column)
  servo_clamp_shoulder_local, ...@L=+2       links_v1.build_column() clamp in its own frame (before local());
                                             "_local" keeps it apart from the build_all() entry, which sits in the arm frame
  forearm_core_front, ...@tube_r=+2          a subset of links_v1.build_forearm(), see forearm_core_front()
Held-out parts of plan v2, built by their own builder ("_local" keeps them apart from build_all()):
  gripper_pad_up_local, ...@top=+2           wrist_gripper_v1.build_gripper(), MS["top"] +2
  gripper_gear_crank_up_local, ...@link=+2   wrist_gripper_v1.build_gripper(), G["link"] +2
  base_tray_local, ...@r=+2                  base_v1.build_base(), B["r"] +2
Each entry also lists the soften() calls behind it: the radius asked for and the one OCC took
(r, r/2 or None = left sharp), which the SolidCraft rebuild has to copy.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fc_common as C  # noqa: E402

SOFTEN_LOG = []
INPUTS = {}   # geometry the last build derived from the parameters (forearm only)


def fresh(overrides=None):
    """Re-import the shell modules (their dicts are module globals) and apply {(module, dict, key): delta}."""
    for name in ("shell_v1_model", "base_v1", "links_v1", "wrist_gripper_v1"):
        sys.modules.pop(name, None)
    import shell_v1_model as S
    import base_v1 as BV
    import links_v1 as LK
    import wrist_gripper_v1 as WG
    mods = {"S": S, "BV": BV, "LK": LK, "WG": WG}
    for (mod, dname, key), delta in (overrides or {}).items():
        getattr(mods[mod], dname)[key] += delta
    original = S.soften

    def soften(shape, r):
        out = original(shape, r)
        used = None
        if len(out.Faces) != len(shape.Faces):
            used = r
            try:
                first = shape.makeFillet(r, shape.Edges)
                if not first.isValid():
                    used = r / 2
            except Exception:
                used = r / 2
        SOFTEN_LOG.append({"asked_mm": r, "used_mm": used})
        return out

    S.soften = soften
    return S, BV, LK, WG


def turntable(overrides=None):
    S, BV, LK, WG = fresh(overrides)
    return BV.turntable()


def servo_clamp_shoulder(overrides=None):
    S, BV, LK, WG = fresh(overrides)
    LK.local = lambda shape, centre, ang: shape     # keep the clamp in its own frame
    return LK.build_column()["servo_clamp_shoulder"][0]


def forearm_core_front(overrides=None):
    """Tube (r - 0.2) + both hubs, softened 2 mm, cable channel cut, then the front half (y >= yc).

    Same lines as links_v1.build_forearm() up to soften() plus its channel cut and split. Left out:
    flanges, servo frames, pockets, collars, crush ribs, servo windows, pin holes, screws, vents, and
    the cable exits (they only cut the back half, y < yc).
    """
    S, BV, LK, WG = fresh(overrides)
    import Part
    from FreeCAD import Vector as V
    H, EL, WF = LK.H, LK.EL, LK.WF
    y_front = S.BACK[1]
    r = H["tube_r"]
    yc = y_front - r
    e, w = (EL.x, EL.z), (WF.x, WF.z)
    L = math.hypot(w[0] - e[0], w[1] - e[1])
    u = ((w[0] - e[0]) / L, (w[1] - e[1]) / L)
    tube = Part.makeCylinder(r - 0.2, L, V(e[0], yc, e[1]), V(u[0], 0, u[1]))
    tube = tube.fuse(S.cyl_y(e[0], e[1], 20.0, yc - r, y_front)).fuse(S.cyl_y(w[0], w[1], r, yc - r, y_front))
    tube = S.soften(tube.removeSplitter(), 2.0)
    t0, t1 = 30.0, L - 30.0
    p0 = V(e[0] + u[0] * t0, yc, e[1] + u[1] * t0)
    tube = tube.cut(Part.makeCylinder(H["channel_r"], t1 - t0, p0, V(u[0], 0, u[1])))
    front = tube.common(S.box(-500, 500, yc, 500, -500, 500))
    INPUTS.update({"e": e, "w": w, "L": L, "u": u, "yc": yc, "y_front": y_front, "r": r,
                   "channel_r": H["channel_r"], "t0": t0, "t1": t1})
    return front


def gripper_pad_up(overrides=None):
    S, BV, LK, WG = fresh(overrides)
    return WG.build_gripper(S.P["jaw_open_deg"])[0]["gripper_pad_up"][0]


def gripper_gear_crank_up(overrides=None):
    S, BV, LK, WG = fresh(overrides)
    return WG.build_gripper(S.P["jaw_open_deg"])[0]["gripper_gear_crank_up"][0]


def base_tray(overrides=None):
    S, BV, LK, WG = fresh(overrides)
    return BV.build_base()["base_tray"][0]


CASES = [
    ("turntable", turntable, None),
    ("turntable@tt_r=+5", turntable, {("BV", "B", "tt_r"): 5.0}),
    ("servo_clamp_shoulder_local", servo_clamp_shoulder, None),
    ("servo_clamp_shoulder_local@L=+2", servo_clamp_shoulder, {("S", "STS", "L"): 2.0}),
    ("forearm_core_front", forearm_core_front, None),
    ("forearm_core_front@tube_r=+2", forearm_core_front, {("LK", "H", "tube_r"): 2.0}),
    ("gripper_pad_up_local", gripper_pad_up, None),
    ("gripper_pad_up_local@top=+2", gripper_pad_up, {("WG", "MS", "top"): 2.0}),
    ("gripper_gear_crank_up_local", gripper_gear_crank_up, None),
    ("gripper_gear_crank_up_local@link=+2", gripper_gear_crank_up, {("WG", "G", "link"): 2.0}),
    ("base_tray_local", base_tray, None),
    ("base_tray_local@r=+2", base_tray, {("BV", "B", "r"): 2.0}),
]


def main():
    ref = C.load_ref()
    for key, build, overrides in CASES:
        del SOFTEN_LOG[:]
        INPUTS.clear()
        shape = build(overrides)
        m = C.measure(shape)
        m["source"] = "freecad_rebuild_ref.%s()" % build.__name__
        m["overrides"] = {"%s.%s[%s]" % k: d for k, d in (overrides or {}).items()}
        m["soften_calls"] = list(SOFTEN_LOG)
        if INPUTS:
            m["geometry_inputs"] = dict(INPUTS)
        ref[key] = m
        print("%-32s vol %10.2f mm3  faces %3d  valid %s  closed %s  soften %s"
              % (key, m["volume_mm3"], m["faces"], m["valid"], m["closed"], m["soften_calls"]))
    C.save_ref(ref)
    print("->", C.REF)


main()
