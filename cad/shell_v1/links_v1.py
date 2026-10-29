"""Print-ready column, upper link and forearm for shell v1 (4.1-style look, our own geometry).

What changes from the concept parts in shell_v1_model:
- column and turntable are one print (turntable from base_v1: lazy-susan disc + boss down to the
  pan horn); the pan horn screws into the boss from below, the shoulder
  STS3215 slides in from the back and a clamp plate holds it;
- the upper link takes both STS3215 horns on its back face; screws reach the horns through the rings;
- the forearm is a round tube like the 4.1, split along its length into a front and a back half
  that clamp the elbow STS3215 and the wrist MG996R, with a cable channel and exits.

STS3215 horn screw pattern (4 holes on r 7, M3) is an estimate: MEASURE the horns before printing.
"""
import math

import Part
from FreeCAD import Vector as V

import shell_v1_model as S

H = dict(r=7.0, n=4, free=3.4, pilot=2.5, access=6.0,   # STS3215 horn screws (MEASURE), M3 self-tapping
         tube_r=18.5, split_gap=0.0, channel_r=9.0, screw_cb=6.0)
SH, EL, WF, PAN = S.SH, S.EL, S.WF, S.PAN


def horn_holes(c, y0, y1, d, angle0=45.0):
    holes = None
    for k in range(H["n"]):
        a = math.radians(angle0 + 360.0 / H["n"] * k)
        h = S.cyl_y(c[0] + H["r"] * math.cos(a), c[1] + H["r"] * math.sin(a), d / 2, y0, y1)
        holes = h if holes is None else holes.fuse(h)
    return holes


def servo_frame(kind, shaft, along):
    """Centre (x, z) of a servo case and its rotation (deg about y), as S.servo_y places it."""
    d = S.SERVOS[kind]
    n = math.hypot(*along)
    ux, uz = along[0] / n, along[1] / n
    return (shaft[0] + ux * d["shaft_off"], shaft[1] + uz * d["shaft_off"]), math.degrees(math.atan2(uz, ux))


def local(shape, centre, ang):
    shape.rotate(V(0, 0, 0), V(0, 1, 0), -ang)
    shape.translate(V(centre[0], 0, centre[1]))
    return shape


# ---------------------------------------------------------------- column + turntable (child of shoulder_pan)
def build_column():
    parts = S.build_column()
    import base_v1
    col = parts.pop("column")[0]
    parts.pop("turntable")
    tt = base_v1.turntable()                                      # rides on the lazy susan
    top = PAN.z + S.P["turntable_t"]
    body = tt.fuse(col).removeSplitter()
    # pan horn: screws come up through the horn into the disc; centre screw reached from the top
    body = body.cut(Part.makeCylinder(H["access"] / 2, 300, V(PAN.x, S.Y0, PAN.z - 1)))
    for k in range(H["n"]):
        a = math.radians(45 + 90 * k)
        body = body.cut(Part.makeCylinder(H["pilot"] / 2, 5, V(PAN.x + H["r"] * math.cos(a),
                                                              S.Y0 + H["r"] * math.sin(a), PAN.z - 0.1)))
    # shoulder servo: slides in from the back, 7 mm of it stays outside; the clamp holds it there
    d = S.STS
    along = S.unit(SH, V(PAN.x - 30, 0, top + 8))
    centre, ang = servo_frame("sts", (SH.x, SH.z), along)
    y_back = S.SH_FACE - d["H"]                                   # servo bottom face
    plate = Part.makeBox(d["L"] + 18, 2.5, d["W"] + 19, V(-d["L"] / 2 - 9, y_back - 2.5, -d["W"] / 2 - 9.5))
    clamp = plate
    screws = None
    for s in (-1, 1):
        zc = s * (d["W"] / 2 + 6.5)
        leg = Part.makeBox(8, S.BACK[0] - y_back + 2.5, 6, V(-4, y_back - 2.5, zc - 3))
        clamp = clamp.fuse(leg)
        hole = Part.makeCylinder(H["free"] / 2, 30, V(0, y_back - 5, zc), V(0, 1, 0))
        pilot = Part.makeCylinder(H["pilot"] / 2, 12, V(0, S.BACK[0] - 0.1, zc), V(0, 1, 0))
        clamp = clamp.cut(hole)
        screws = pilot if screws is None else screws.fuse(pilot)
    clamp = S.soften(clamp.removeSplitter(), 0.8)
    for x in (-d["L"] / 2 - 4, d["L"] / 2 + 4):                  # zip-tie slots: bus cable to the next servo
        clamp = clamp.cut(Part.makeBox(1.8, 6, 4, V(x - 0.9, y_back - 4, -2)))
    clamp = local(clamp, centre, ang)
    body = body.cut(local(screws, centre, ang))
    parts["column"] = (body, S.WHITE)
    parts["servo_clamp_shoulder"] = (clamp, S.WHITE)
    return parts


# ---------------------------------------------------------------- upper link (child of shoulder_lift)
def build_upper():
    parts = S.build_upper()
    link = parts["upper_link"][0]
    y0, y1 = S.FRONT
    for c in (SH, EL):
        link = link.cut(horn_holes((c.x, c.z), y0 - 1, y1 + 1, H["free"]))   # heads sit in the ring bore
        link = link.cut(S.cyl_y(c.x, c.z, H["access"] / 2, y0 - 1, y1 + 1))
    # zip-tie slots along the curve: the cable bundle runs outside on the back edge like on the 4.1
    mid_x, mid_z = min(SH.x, EL.x) - 22, (SH.z + EL.z) / 2
    for t in (0.3, 0.5, 0.7):
        a = (SH.x + (mid_x - SH.x) * 2 * t, SH.z + (mid_z - SH.z) * 2 * t) if t <= 0.5 else \
            (mid_x + (EL.x - mid_x) * (2 * t - 1), mid_z + (EL.z - mid_z) * (2 * t - 1))
        link = link.cut(S.box(a[0] - 1.5, a[0] + 1.5, y0 - 1, y1 + 1, a[1] - 4, a[1] + 4))
    return {"upper_link": (link, S.NAVY)}


# ---------------------------------------------------------------- forearm tube (child of elbow_flex)
def build_forearm():
    y_front = S.BACK[1]                                            # horn faces of both servos
    r = H["tube_r"]
    yc = y_front - r
    e, w = (EL.x, EL.z), (WF.x, WF.z)
    L = math.hypot(w[0] - e[0], w[1] - e[1])
    u = ((w[0] - e[0]) / L, (w[1] - e[1]) / L)
    n = (-u[1], u[0])
    # tube 0.2 mm inside the hub faces: a tube tangent to the flat hub faces breaks the OCC fuse
    tube = Part.makeCylinder(r - 0.2, L, V(e[0], yc, e[1]), V(u[0], 0, u[1]))
    tube = tube.fuse(S.cyl_y(e[0], e[1], 20.0, yc - r, y_front)).fuse(S.cyl_y(w[0], w[1], r, yc - r, y_front))
    tube = S.soften(tube.removeSplitter(), 2.0)

    e_case, e_horn, e_pocket = S.servo_y("sts", e, y_front, +1, u)
    w_case, w_horn, w_pocket = S.servo_y("mg", w, y_front, +1, (-u[0], -u[1]))
    tube = tube.cut(e_pocket).cut(w_pocket)
    t0, t1 = 30.0, L - 34.0                                        # channel overlaps both pockets
    p0 = V(e[0] + u[0] * t0, yc, e[1] + u[1] * t0)
    tube = tube.cut(Part.makeCylinder(H["channel_r"], t1 - t0, p0, V(u[0], 0, u[1])))
    for t in (45.0, L - 45.0):                                     # cable exits on the back
        tube = tube.cut(S.cyl_y(e[0] + u[0] * t, e[1] + u[1] * t, 4.0, yc - r - 1, yc))

    # split along the tube; M3 screws from the back half into the front half
    front = tube.common(S.box(-500, 500, yc, 500, -500, 500))
    back = tube.common(S.box(-500, 500, -500, yc, -500, 500))
    screw_pts = [(e[0] - 16 * u[0], e[1] - 16 * u[1])]
    for t, s in ((L / 2, 1), (L / 2, -1)):
        screw_pts.append((e[0] + u[0] * t + n[0] * 13 * s, e[1] + u[1] * t + n[1] * 13 * s))
    for s in (1, -1):
        screw_pts.append((w[0] + n[0] * 14 * s, w[1] + n[1] * 14 * s))
    for x, z in screw_pts:
        front = front.cut(S.cyl_y(x, z, H["pilot"] / 2, yc - 0.1, yc + 14))
        back = back.cut(S.cyl_y(x, z, H["free"] / 2, yc - r - 1, yc + 0.1))
        back = back.cut(S.cyl_y(x, z, H["screw_cb"] / 2, yc - r - 1, yc - r + 3))
    return {"forearm_front": (front, S.GREY), "forearm_back": (back, S.GREY),
            "servo_elbow": (e_case, S.BLACK), "horn_elbow": (e_horn, S.STEEL),
            "servo_wrist_flex": (w_case, S.BLACK), "horn_wrist_flex": (w_horn, S.STEEL)}


PRINTED = ["column", "servo_clamp_shoulder", "upper_link", "forearm_front", "forearm_back"]
