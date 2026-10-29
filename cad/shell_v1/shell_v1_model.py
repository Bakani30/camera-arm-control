"""Shell v1: arm outer shape in the style of FABRI CREATOR Brazo Robotico 4.1 (look only).

Joint axes come from arm_spec/small_arm_v0.json (SO-101 kinematics) so FK stays the same.
Every size here is ours; nothing is measured from the maker's STL/STEP files.
Library module; build with `python run_shell_v1.py` (any OS) or `freecadcmd build_shell_v1.py`.
Writes shell_v1.FCStd, out/shell_v1.step and per-part STL to out/.

Units: mm, base_link frame of the spec at q = 0 (upper arm up, forearm pointing +x).
Status: concept for look and packaging. Not checked for strength, printability or the
idle-side support of each joint.
"""
import json
import math
import os
import sys

import FreeCAD as App
import MeshPart
import Part
from FreeCAD import Vector as V

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "out")
sys.path.insert(0, REPO)
import arm_spec  # noqa: E402

# ---------------------------------------------------------------- parameters
P = dict(
    clearance=0.3,
    wall=3.0,
    link_t=28.0,          # link thickness along the joint axis (y)
    ring_od=50.0,         # tube knuckle outer diameter (houses a 6806 bearing, see links_v1)
    ring_bore=26.0,       # blind bore seen from the outside face
    ring_floor=10.5,      # bearing seat (7) + floor (3.5) on the horn side
    upper_halfwidth=19.0,
    fore_halfwidth=16.0,
    drum_d=120.0, drum_h=56.0,
    turntable_d=96.0, turntable_t=6.0,
    leg_r_out=160.0, leg_w_root=22.0, leg_w_tip=6.0, leg_t=14.0, legs=5,
    cable_hole_d=14.0, cable_hole_r=24.0,
    jaw_open_deg=34.0,     # crank angle the fingers are drawn at (see wrist_gripper_v1)
)

# Actuator sizes. STS3215: 45.2 x 24.7 x 35 (Waveshare ST3215 wiki); MG996R: 40.7 x 19.7 x 42.9
# with 36.5 case height and 54.5 ears 27 mm from the bottom (presentation model v0 values).
# Shaft offset from case centre: MG996R 10.2 (v0 note), STS3215 11.0 (estimate, measure).
# STS3032 (wrist roll, gripper): 23.2 x 12.1 x 28.5 overall from shop pages; the split into a 22.5 case
# + 6 boss, ears 32.2 wide 16 mm up, shaft offset 5.9 and the 16 mm horn are micro-servo estimates: measure.
STS = dict(L=45.2, W=24.7, H=35.0, boss=4.0, shaft_off=11.0, horn_d=22.0, horn_t=3.0)
MG = dict(L=40.7, W=19.7, H=36.5, boss=6.4, shaft_off=10.2, horn_d=22.0, horn_t=3.0,
          ear_w=54.5, ear_z=27.0, ear_t=2.5)
SC = dict(L=23.2, W=12.1, H=22.5, boss=6.0, shaft_off=5.9, horn_d=16.0, horn_t=2.5,
          ear_w=32.2, ear_z=16.0, ear_t=2.5)
SERVOS = {"sts": STS, "mg": MG, "sc": SC}

# Colours follow the maker's 3D view (reel): only the curved upper link is navy.
NAVY = (0.13, 0.17, 0.42)
WHITE = (0.93, 0.93, 0.90)
GREY = (0.72, 0.73, 0.76)
BLACK = (0.08, 0.08, 0.09)
STEEL = (0.75, 0.76, 0.78)


# ---------------------------------------------------------------- joint frames from the spec
def joint_frames():
    s = arm_spec.load_spec()
    rot, pos, out = [[1, 0, 0], [0, 1, 0], [0, 0, 1]], [0.0, 0.0, 0.0], {}
    for j in s.joints:
        pos = [p + d for p, d in zip(pos, arm_spec._apply(rot, j.origin_xyz))]
        rot = arm_spec._matmul(rot, arm_spec._rpy(*j.origin_rpy))
        out[j.name] = (V(*[c * 1000 for c in pos]), V(*arm_spec._apply(rot, j.axis)))
    tcp = arm_spec.forward_kinematics(s, {})
    return out, V(*[c * 1000 for c in tcp]), s


J, TCP_SPEC, SPEC = joint_frames()
PAN, SH, EL, WF, WR = (J[n][0] for n in
                       ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"))
Y0 = 0.0


# ---------------------------------------------------------------- helpers
def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl_y(cx, cz, r, y0, y1):
    return Part.makeCylinder(r, y1 - y0, V(cx, y0, cz), V(0, 1, 0))


def band_xz(points, half, y0, y1):
    """Rounded band around a polyline/arc in the x-z plane, extruded from y0 to y1.

    The outline is built in the XY plane (y standing for z) so offsets of a single
    straight segment still have a plane, then turned into x-z.
    """
    if isinstance(points, Part.Wire):
        face = Part.Face(points.makeOffset2D(half, 0, False, False, False))
    else:
        face = None
        for a, b in zip(points, points[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            n = math.hypot(dx, dy)
            nx, ny = -dy / n * half, dx / n * half
            quad = Part.Face(Part.makePolygon([V(a[0] + nx, a[1] + ny, 0), V(b[0] + nx, b[1] + ny, 0),
                                               V(b[0] - nx, b[1] - ny, 0), V(a[0] - nx, a[1] - ny, 0),
                                               V(a[0] + nx, a[1] + ny, 0)]))
            caps = [Part.Face(Part.Wire([Part.makeCircle(half, V(p[0], p[1], 0))])) for p in (a, b)]
            seg = quad.fuse(caps[0]).fuse(caps[1])
            face = seg if face is None else face.fuse(seg)
        face = face.removeSplitter()
    solid = face.extrude(V(0, 0, -(y1 - y0)))
    solid.rotate(V(0, 0, 0), V(1, 0, 0), 90)   # (x, y, z) -> (x, -z, y)
    solid.translate(V(0, y0, 0))
    return solid


def arc_xz(a, mid, b):
    """Arc through three (x, z) points, as an XY-plane wire for band_xz."""
    return Part.Wire([Part.Arc(V(a[0], a[1], 0), V(mid[0], mid[1], 0),
                               V(b[0], b[1], 0)).toShape()])


def soften(shape, r):
    """Fillet every edge; OCC sometimes returns an invalid solid, so retry smaller, else keep it sharp."""
    for radius in (r, r / 2):
        try:
            out = shape.makeFillet(radius, shape.Edges)
            if out.isValid():
                return out
        except Exception:
            pass
    return shape


def servo_y(kind, shaft, face_y, direction, along):
    """Servo dummy with its shaft on the y axis line through `shaft` (x, z).

    face_y: y of the case top face (shaft side); direction +1/-1: shaft points to +y/-y.
    along: unit (dx, dz) from the shaft toward the far end of the case.
    Returns (case, boss+horn, pocket) where pocket = case grown by the clearance.
    """
    d = SERVOS[kind]
    ux, uz = along
    n = math.hypot(ux, uz)
    ux, uz = ux / n, uz / n
    cx, cz = shaft[0] + ux * d["shaft_off"], shaft[1] + uz * d["shaft_off"]
    ang = math.degrees(math.atan2(uz, ux))
    y_lo, y_hi = (face_y - d["H"], face_y) if direction > 0 else (face_y, face_y + d["H"])

    def case(grow):
        b = Part.makeBox(d["L"] + 2 * grow, y_hi - y_lo + 2 * grow, d["W"] + 2 * grow,
                         V(-d["L"] / 2 - grow, y_lo - grow, -d["W"] / 2 - grow))
        if "ear_w" in d:
            ey = (y_lo + d["ear_z"]) if direction > 0 else (y_hi - d["ear_z"] - d["ear_t"])
            b = b.fuse(Part.makeBox(d["ear_w"] + 2 * grow, d["ear_t"] + 2 * grow, d["W"] + 2 * grow,
                                    V(-d["ear_w"] / 2 - grow, ey - grow, -d["W"] / 2 - grow)))
        b.rotate(V(0, 0, 0), V(0, 1, 0), -ang)
        b.translate(V(cx, 0, cz))
        return b

    boss_y0 = face_y if direction > 0 else face_y - d["boss"]
    horn_y0 = face_y + d["boss"] if direction > 0 else face_y - d["boss"] - d["horn_t"]
    boss = cyl_y(shaft[0], shaft[1], 2.5, boss_y0, boss_y0 + d["boss"])
    horn = cyl_y(shaft[0], shaft[1], d["horn_d"] / 2, horn_y0, horn_y0 + d["horn_t"])
    return case(0.0), boss.fuse(horn), case(P["clearance"])


def ring_knuckle(c, y0, y1, open_side):
    """Tube-look knuckle: solid disc with a blind bore from the outside face."""
    r = P["ring_od"] / 2
    disc = cyl_y(c[0], c[2], r, y0, y1)
    if open_side < 0:
        bore = cyl_y(c[0], c[2], P["ring_bore"] / 2, y0 - 1, y1 - P["ring_floor"])
    else:
        bore = cyl_y(c[0], c[2], P["ring_bore"] / 2, y0 + P["ring_floor"], y1 + 1)
    return disc, bore


def unit(a, b):
    dx, dz = b[0] - a[0], b[2] - a[2]
    n = math.hypot(dx, dz)
    return dx / n, dz / n


# ---------------------------------------------------------------- layout along y
# Side-by-side links like the 4.1: column and forearm on the back (-y), upper link in front.
# Shoulder and elbow servos sit in the back parts with shafts +y; their horns bolt to the upper link.
T = P["link_t"]
BACK = (-42.0, -42.0 + T)            # column, forearm: y -42 .. -14
SH_FACE = BACK[1]                    # shoulder servo face, shaft +y
HORN_GAP = STS["boss"] + STS["horn_t"]
FRONT = (SH_FACE + HORN_GAP + 0.5, SH_FACE + HORN_GAP + 0.5 + T)   # upper link: y -6.5 .. 21.5


def build_column():
    """Turntable + S-shaped column holding the shoulder servo (child of shoulder_pan)."""
    tt_z0 = PAN.z
    tt = Part.makeCylinder(P["turntable_d"] / 2, P["turntable_t"], V(PAN.x, Y0, tt_z0))
    tt = soften(tt, 2.0)
    tt = tt.cut(Part.makeCylinder(P["cable_hole_d"] / 2, 20, V(PAN.x + P["cable_hole_r"], Y0, tt_z0 - 5)))
    top = tt_z0 + P["turntable_t"]
    # S-curve: leave the turntable behind the pan axis, sweep back, then forward up to the shoulder
    along = unit(SH, V(PAN.x - 30, 0, top + 8))
    case, horn, pocket = servo_y("sts", (SH.x, SH.z), SH_FACE, +1, along)
    far = (SH.x + along[0] * (STS["shaft_off"] + STS["L"] / 2), SH.z + along[1] * (STS["shaft_off"] + STS["L"] / 2))
    spine = arc_xz((PAN.x + 6, top), (far[0] - 6, (top + far[1]) / 2 + 2), (SH.x, SH.z))
    col = band_xz(spine, 21.0, BACK[0], BACK[1])
    col = col.fuse(cyl_y(SH.x, SH.z, P["ring_od"] / 2, BACK[0], BACK[1]))
    foot = Part.makeCylinder(30, 4, V(PAN.x, Y0, top - 1))
    col = col.fuse(foot).removeSplitter()
    col = soften(col, 3.0)
    # nothing below the turntable top: the pan servo sits there and the column turns around it
    col = col.common(box(-500, 500, -500, 500, top - 1, 1000))
    col = col.cut(pocket)
    return {"turntable": (tt, WHITE), "column": (col, WHITE),
            "servo_shoulder": (case, BLACK), "horn_shoulder": (horn, STEEL)}


def build_upper():
    """Banana link shoulder -> elbow with tube rings at both ends open to the front (child of shoulder_lift).

    No servo inside: both horns (shoulder, elbow) bolt to its back face, so the rings stay clean.
    """
    mid_x = min(SH.x, EL.x) - 22
    spine = arc_xz((SH.x, SH.z), (mid_x, (SH.z + EL.z) / 2), (EL.x, EL.z))
    link = band_xz(spine, P["upper_halfwidth"], FRONT[0], FRONT[1])
    d1, b1 = ring_knuckle(SH, FRONT[0], FRONT[1], +1)
    d2, b2 = ring_knuckle(EL, FRONT[0], FRONT[1], +1)
    link = link.fuse(d1).fuse(d2).removeSplitter()
    link = soften(link, 3.0)
    link = link.cut(b1).cut(b2)
    return {"upper_link": (link, NAVY)}


CHAIN = {  # part -> the joint whose child link carries it (None = fixed base)
    "base_drum": None, "base_legs": None, "servo_pan": None, "horn_pan": "shoulder_pan",
    "column": "shoulder_pan", "servo_shoulder": "shoulder_pan", "servo_clamp_shoulder": "shoulder_pan",
    "horn_shoulder": "shoulder_lift", "upper_link": "shoulder_lift", "horn_elbow": "shoulder_lift",
    "servo_elbow": "elbow_flex", "forearm_front": "elbow_flex", "forearm_back": "elbow_flex",
    "servo_wrist_flex": "elbow_flex",
    "horn_wrist_flex": "wrist_flex", "wrist": "wrist_flex", "servo_wrist_roll": "wrist_flex",
    "bearing_shoulder": "shoulder_lift", "bearing_elbow": "shoulder_lift", "bearing_wrist_flex": "wrist_flex",
    "horn_wrist_roll": "wrist_roll",
}
ORDER = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]


def moved_by(part):
    """Joints that move this part: its own joint and every joint before it in the chain."""
    if part.startswith("base_") or part == "servo_pan":
        return []
    first = CHAIN.get(part, "wrist_roll")
    return [] if first is None else ORDER[:ORDER.index(first) + 1]


def posed(shape, part, q_deg):
    s = shape.copy()
    for jn in reversed(moved_by(part)):
        a = q_deg.get(jn, 0.0)
        if a:
            o, ax = J[jn]
            s.rotate(o, ax, a)
    return s


def build_all(phi_deg=None):
    """Every part at q = 0; print-ready parts come from links_v1 and wrist_gripper_v1."""
    import base_v1 as BV
    import links_v1 as LK
    import wrist_gripper_v1 as WG
    parts = {}
    for fn in (BV.build_base, LK.build_column, LK.build_upper, LK.build_forearm, WG.build_wrist):
        parts.update(fn())
    gp, info = WG.build_gripper(P["jaw_open_deg"] if phi_deg is None else phi_deg)
    parts.update(gp)
    return parts, info


def export_stl(shape, path):
    """Binary STL at 0.05 mm chord tolerance / 10 deg; Part.exportStl's default is ~10x larger on disk."""
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.05,
                                  AngularDeflection=math.radians(10), Relative=False)
    mesh.write(path)


def apply_colors(doc):
    """Copy each part's DisplayColor to its view (GUI only); saved files then open in colour."""
    if not App.GuiUp:
        return False
    for o in doc.Objects:
        if hasattr(o, "DisplayColor") and o.ViewObject is not None:
            o.ViewObject.ShapeColor = tuple(o.DisplayColor)[:3]
            o.ViewObject.Visibility = True
    return True


def main(poses=None):
    """Build, save shell_v1.FCStd and out/ (STEP, STL, colors.json); poses = {name: {joint: deg}}."""
    poses = poses if poses is not None else json.loads(os.environ.get("SHELL_POSES", "{}"))
    os.makedirs(OUT, exist_ok=True)
    parts, info = build_all()
    print("joint origins (mm):", {k: tuple(round(c, 1) for c in v[0]) for k, v in J.items()})
    print("spec TCP q=0:", tuple(round(c, 1) for c in TCP_SPEC))
    print("finger gap at crank %.0f deg: %.1f mm; steel pin lengths %s mm"
          % (P["jaw_open_deg"], info["opening_mm"], info["pin_lengths_mm"]))
    if "shell_v1" in App.listDocuments():
        App.closeDocument("shell_v1")
    doc = App.newDocument("shell_v1")
    for name, (shape, color) in parts.items():
        if not shape.isValid():
            print("WARN invalid shape", name)
        o = doc.addObject("Part::Feature", name)
        o.Shape = shape
        o.addProperty("App::PropertyColor", "DisplayColor", "Shell", "colour for viewers")
        o.DisplayColor = color
        o.addProperty("App::PropertyString", "MovedBy", "Shell", "joints that move this part")
        o.MovedBy = ",".join(moved_by(name))
        print("%-18s vol %8.1f cm3" % (name, shape.Volume / 1000))
        export_stl(shape, os.path.join(OUT, name + ".stl"))
    doc.recompute()
    colored = apply_colors(doc)
    doc.saveAs(os.path.join(HERE, "shell_v1.FCStd"))
    Part.export([o for o in doc.Objects], os.path.join(OUT, "shell_v1.step"))
    with open(os.path.join(OUT, "colors.json"), "w") as f:
        json.dump({n: c for n, (s, c) in parts.items()}, f, indent=1)
    # print-ready parts, in assembly orientation; mass = solid PLA upper bound
    import base_v1 as BV
    import links_v1 as LK
    import wrist_gripper_v1 as WG
    pdir = os.path.join(OUT, "print")
    os.makedirs(pdir, exist_ok=True)
    total = 0.0
    for name in BV.PRINTED + LK.PRINTED + WG.PRINTED:
        shape = parts[name][0]
        if len(shape.Solids) != 1:
            print("WARN %s has %d solids" % (name, len(shape.Solids)))
        export_stl(shape, os.path.join(pdir, name + ".stl"))
        grams = shape.Volume / 1000 * 1.24
        total += grams
        print("print %-24s %6.1f cm3  <= %5.1f g PLA" % (name, shape.Volume / 1000, grams))
    print("print total <= %.0f g PLA (solid; real prints with infill weigh less)" % total)
    for pname, q in poses.items():
        pdir = os.path.join(OUT, pname)
        os.makedirs(pdir, exist_ok=True)
        for name, (shape, color) in parts.items():
            export_stl(posed(shape, name, q), os.path.join(pdir, name + ".stl"))
        with open(os.path.join(pdir, "colors.json"), "w") as f:
            json.dump({n: c for n, (s, c) in parts.items()}, f, indent=1)
        print("pose", pname, q)
    print("saved", os.path.join(HERE, "shell_v1.FCStd"), "(with colours)" if colored else
          "(no GUI: run open_shell_v1.FCMacro in FreeCAD once to store colours)")
    return doc
