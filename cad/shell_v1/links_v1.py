"""Print-ready column, upper link and forearm for shell v1 (4.1-style look, our own geometry).

What changes from the concept parts in shell_v1_model:
- column and turntable are one print (turntable from base_v1: lazy-susan disc + boss down to the
  pan horn); the pan horn screws into the boss from below, the shoulder
  STS3215 slides in from the back and a clamp plate holds it;
- the upper link takes both STS3215 horns on its back face; screws reach the horns through the rings;
- the forearm is a round tube like the 4.1, split along its length into a front and a back half
  that clamp the elbow and wrist-flex STS3215s, with a cable channel and exits.

STS3215 horn screw pattern (4 holes on r 7, M3) is an estimate: MEASURE the horns before printing.
"""
import math
import os

import Part
from FreeCAD import Vector as V

import shell_v1_model as S

H = dict(r=7.0, n=4, free=3.4, pilot=2.5, access=6.0,   # STS3215 horn screws (MEASURE), M3 self-tapping
         tube_r=18.5, split_gap=0.0, channel_r=9.0, screw_cb=6.0, exit_len=6.0)
SH, EL, WF, PAN = S.SH, S.EL, S.WF, S.PAN

# Two-point support for every STS3215 joint (H1): a 6806 bearing (30 x 42 x 7, MEASURE price/fit)
# sits in the part bolted to the horn; its inner race rides on a collar that grows out of the part
# holding the servo body, around the horn. A spigot inside the collar carries the horn screws.
# The wrist-flex joint is off by default: its load is small (~1.5 kg.cm) and a 6806 (~22 g) at the
# arm's end adds ~0.7 kg.cm at the shoulder; turn it on if the measurement gate shows wrist play.
BR = dict(bore=30.0, od=42.0, w=7.0, spigot_r=11.5, collar_in=11.75, collar_step=16.5,
          flange_r=27.0, flange_t=5.0, pin_d=3.2, pin_r=26.0, rib_r=0.8, rib_in=0.45,
          wrist_bearing=False)


def bearing_seat(c, y_back):
    """Cut for the outer race + collar clearance, in the horn-side part whose back face is y_back."""
    outer = S.cyl_y(c[0], c[1], BR["od"] / 2, y_back - 1, y_back + BR["w"])
    return outer.cut(S.cyl_y(c[0], c[1], BR["spigot_r"], y_back - 2, y_back + BR["w"] + 1))


def collar(c, y_face, y_back):
    """Collar on the servo-side part (face y_face) carrying the inner race up to y_back + w."""
    tube = S.cyl_y(c[0], c[1], BR["bore"] / 2, y_face - 0.5, y_back + BR["w"])
    step = S.cyl_y(c[0], c[1], BR["collar_step"], y_face - 0.5, y_back - 0.1)
    return tube.fuse(step).cut(S.cyl_y(c[0], c[1], BR["collar_in"], y_face - 1, y_back + BR["w"] + 1))


def bearing_dummy(c, y_back):
    return S.cyl_y(c[0], c[1], BR["od"] / 2, y_back, y_back + BR["w"]).cut(
        S.cyl_y(c[0], c[1], BR["bore"] / 2, y_back - 1, y_back + BR["w"] + 1))


def flange(c, y_face):
    """Lip on the servo-side face that takes the calibration pin."""
    return S.cyl_y(c[0], c[1], BR["flange_r"], y_face - BR["flange_t"], y_face)


def pin_hole(p, y0, y1):
    return S.cyl_y(p[0], p[1], BR["pin_d"] / 2, y0, y1)


def toward(a, b, r):
    dx, dz = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dz)
    return (a[0] + dx / n * r, a[1] + dz / n * r)


def crush_ribs(kind, shaft, face_y, along, y_min, far_x=None):
    """Four ribs on the long walls of a servo pocket, 0.15 mm into the case: a press fit that prints.

    y_min: the part's back face; ribs stop 0.5 mm inside it where the servo sticks out of the part.
    far_x: where along the case the far pair sits (default a quarter of its length), to clear a window.
    """
    d = S.SERVOS[kind]
    centre, ang = servo_frame(kind, shaft, along)
    ribs = None
    zc = d["W"] / 2 + S.P["clearance"] + BR["rib_r"] - BR["rib_in"]
    y0 = max(face_y - d["H"] + 1, y_min + 0.5)
    for x in (-d["L"] / 4, d["L"] / 4 if far_x is None else far_x):
        for z in (-zc, zc):
            r = Part.makeCylinder(BR["rib_r"], face_y - 1 - y0, V(x, y0, z), V(0, 1, 0))
            ribs = r if ribs is None else ribs.fuse(r)
    return local(ribs, centre, ang)


def upper_mid():
    return (min(SH.x, EL.x) - 22, (SH.z + EL.z) / 2)


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
    body = tt.fuse(col).fuse(flange((SH.x, SH.z), S.BACK[1])).removeSplitter()
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
    for z in (-6.0, 0.0, 6.0):                                    # vents over the servo's back (item 7)
        clamp = clamp.cut(Part.makeBox(d["L"] - 12, 6, 2.2, V(-d["L"] / 2 + 6, y_back - 4, z - 1.1)))
    clamp = local(clamp, centre, ang)
    body = body.cut(local(screws, centre, ang))
    body = body.fuse(collar((SH.x, SH.z), S.BACK[1], S.FRONT[0])).removeSplitter()
    body = body.cut(S.servo_y("sts", (SH.x, SH.z), S.SH_FACE, +1, along)[2])   # collar keeps off the servo
    body = body.fuse(crush_ribs("sts", (SH.x, SH.z), S.SH_FACE, along, S.BACK[0]))  # ribs last: they reach into the pocket
    body = body.cut(pin_hole(toward((SH.x, SH.z), upper_mid(), BR["pin_r"]), S.BACK[1] - BR["flange_t"] - 6, S.BACK[1] + 1))
    body = body.cut(base_v1.pan_pin_hole())
    parts["column"] = (body, S.WHITE)
    parts["servo_clamp_shoulder"] = (clamp, S.WHITE)
    return parts


# ---------------------------------------------------------------- upper link (child of shoulder_lift)
def build_upper():
    parts = S.build_upper()
    link = parts["upper_link"][0]
    y0, y1 = S.FRONT
    # lighten: pockets 10 mm deep from both faces along the curve, an I-beam with an 8 mm web
    # (the front one reads as the 4.1's long groove); rings and cable-tie slots stay solid
    mid = upper_mid()
    spine = S.arc_xz((SH.x, SH.z), mid, (EL.x, EL.z))
    for ya, yb in ((y1 - 10, y1 + 1), (y0 - 1, y0 + 10)):
        pocket = S.band_xz(spine, 14.0, ya, yb)
        for c in (SH, EL):
            pocket = pocket.cut(S.cyl_y(c.x, c.z, 31.0, ya - 1, yb + 1))
        link = link.cut(pocket)
    for c in (SH, EL):
        link = link.cut(bearing_seat((c.x, c.z), y0))
        link = link.cut(horn_holes((c.x, c.z), y0 - 1, y1 + 1, H["free"]))   # heads sit in the ring bore
        link = link.cut(S.cyl_y(c.x, c.z, H["access"] / 2, y0 - 1, y1 + 1))
    link = link.cut(pin_hole(toward((SH.x, SH.z), mid, BR["pin_r"]), y0 - 1, y1 + 1))
    link = link.cut(pin_hole(toward((EL.x, EL.z), mid, BR["pin_r"]), y0 - 1, y1 + 1))
    # zip-tie slots along the curve: the cable bundle runs outside on the back edge like on the 4.1
    mid_x, mid_z = mid
    for t in (0.3, 0.5, 0.7):
        a = (SH.x + (mid_x - SH.x) * 2 * t, SH.z + (mid_z - SH.z) * 2 * t) if t <= 0.5 else \
            (mid_x + (EL.x - mid_x) * (2 * t - 1), mid_z + (EL.z - mid_z) * (2 * t - 1))
        link = link.cut(S.box(a[0] - 1.5, a[0] + 1.5, y0 - 1, y1 + 1, a[1] - 4, a[1] + 4))
    return {"upper_link": (link, S.NAVY),
            "bearing_shoulder": (bearing_dummy((SH.x, SH.z), y0), S.STEEL),
            "bearing_elbow": (bearing_dummy((EL.x, EL.z), y0), S.STEEL)}


# ---------------------------------------------------------------- forearm tube (child of elbow_flex)
# STS3215's 35 x 24.7 section does not fit the round tube: its corners reach 3.7 mm past the surface.
# So the forearm has a frame round each servo, with side windows on purpose (option C, D38).
# SHELL_FOREARM=tube builds the plain tube the servos break through, only to compare.
FOREARM_FRAMES = os.environ.get("SHELL_FOREARM") != "tube"
# Distances along the case are from its centre; rib_x stays past the window so the far ribs keep their full length.
# Screws tie the two halves just past each frame; vents move onto the hub, away from the section the window thins.
FRAME = dict(wall=3.0, window_from=5.5, window_to=19.5, window_margin=8.0, window_r=3.0, rib_x=21.0,
             screw_t=41.0, screw_n=13.0, vent_t=3.0, vent_half=6.0)


def servo_box(shaft, along, y_front):
    """The frame round a servo case in the forearm, from its top face to just past its bottom."""
    d, g, w = S.STS, S.P["clearance"], FRAME["wall"]
    centre, ang = servo_frame("sts", shaft, along)
    box = Part.makeBox(d["L"] + 2 * (g + w), d["H"] + g + w, d["W"] + 2 * (g + w),
                       V(-d["L"] / 2 - g - w, y_front - d["H"] - g - w, -d["W"] / 2 - g - w))
    return local(box, centre, ang)


def servo_window(shaft, along, y_front):
    """A rounded slot through both sides of the frame, past the hub so the hub keeps its screws."""
    d, g = S.STS, S.P["clearance"]
    half = max(d["W"] / 2 + g + FRAME["wall"], H["tube_r"]) + 1   # past the tube, or a strip of its wall stays across
    x0, x1 = FRAME["window_from"], FRAME["window_to"]
    y0, y1 = y_front - d["H"] + FRAME["window_margin"], y_front - FRAME["window_margin"]
    slot = Part.makeBox(x1 - x0, y1 - y0, 2 * half, V(x0, y0, -half))
    edges = [e for e in slot.Edges if abs(e.Vertexes[0].Z - e.Vertexes[-1].Z) > half]
    slot = slot.makeFillet(FRAME["window_r"], edges)
    centre, ang = servo_frame("sts", shaft, along)
    return local(slot, centre, ang)


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
    tube = tube.fuse(flange(e, y_front)).fuse(flange(w, y_front)).removeSplitter()

    if FOREARM_FRAMES:
        tube = tube.fuse(servo_box(e, u, y_front)).fuse(servo_box(w, (-u[0], -u[1]), y_front)).removeSplitter()

    e_case, e_horn, e_pocket = S.servo_y("sts", e, y_front, +1, u)
    w_case, w_horn, w_pocket = S.servo_y("sts", w, y_front, +1, (-u[0], -u[1]))
    tube = tube.cut(e_pocket).cut(w_pocket)
    import wrist_gripper_v1
    tube = tube.fuse(collar(e, y_front, S.FRONT[0]))
    if BR["wrist_bearing"]:
        tube = tube.fuse(collar(w, y_front, wrist_gripper_v1.wrist_horn_face()))
    tube = tube.removeSplitter().cut(e_pocket).cut(w_pocket)          # collars keep off the servos
    # ribs last: they reach into the pocket
    far_x = FRAME["rib_x"] if FOREARM_FRAMES else None
    tube = tube.fuse(crush_ribs("sts", e, y_front, u, yc - r, far_x)).fuse(crush_ribs("sts", w, y_front, (-u[0], -u[1]), yc - r, far_x))
    if FOREARM_FRAMES:
        tube = tube.cut(servo_window(e, u, y_front)).cut(servo_window(w, (-u[0], -u[1]), y_front))
    tube = tube.cut(pin_hole(toward(e, upper_mid(), BR["pin_r"]), y_front - BR["flange_t"] - 6, y_front + 1))
    tube = tube.cut(pin_hole(toward(w, (w[0] + u[0], w[1] + u[1]), BR["pin_r"]), y_front - BR["flange_t"] - 6, y_front + 1))
    t0, t1 = 30.0, L - 30.0                                        # channel overlaps both pockets
    p0 = V(e[0] + u[0] * t0, yc, e[1] + u[1] * t0)
    tube = tube.cut(Part.makeCylinder(H["channel_r"], t1 - t0, p0, V(u[0], 0, u[1])))
    for t in (45.0, L - 45.0):                                     # cable exits on the back: slots a plug can pass, MEASURE
        ends = [(e[0] + u[0] * (t + d), e[1] + u[1] * (t + d)) for d in (-H["exit_len"] / 2, H["exit_len"] / 2)]
        tube = tube.cut(S.band_xz(ends, 4.0, yc - r - 1, yc))

    # split along the tube; M3 screws from the back half into the front half
    front = tube.common(S.box(-500, 500, yc, 500, -500, 500))
    back = tube.common(S.box(-500, 500, -500, yc, -500, 500))
    screw_pts = [(e[0] - 16 * u[0], e[1] - 16 * u[1])]
    for t, s in ((L / 2, 1), (L / 2, -1)):
        screw_pts.append((e[0] + u[0] * t + n[0] * 13 * s, e[1] + u[1] * t + n[1] * 13 * s))
    for s in (1, -1):
        screw_pts.append((w[0] + n[0] * 15.5 * s, w[1] + n[1] * 15.5 * s))
        if FOREARM_FRAMES:
            for t in (FRAME["screw_t"], L - FRAME["screw_t"]):
                screw_pts.append((e[0] + u[0] * t + n[0] * FRAME["screw_n"] * s, e[1] + u[1] * t + n[1] * FRAME["screw_n"] * s))
    outside = back.BoundBox.YMin - 1                                # the frames stand proud of the tube's back
    for x, z in screw_pts:
        front = front.cut(S.cyl_y(x, z, H["pilot"] / 2, yc - 0.1, yc + 14))
        back = back.cut(S.cyl_y(x, z, H["free"] / 2, outside, yc + 0.1))
        back = back.cut(S.cyl_y(x, z, H["screw_cb"] / 2, outside, yc - r + 3))
    # vents in the back half over each servo (review item 7): the tube is closed and STS3215s run warm
    vent_t, vent_half = (FRAME["vent_t"], FRAME["vent_half"]) if FOREARM_FRAMES else (11.0, 8.0)
    for centre in ((e[0] + u[0] * vent_t, e[1] + u[1] * vent_t), (w[0] - u[0] * vent_t, w[1] - u[1] * vent_t)):
        for k in (-6.0, 0.0, 6.0):
            cxz = (centre[0] + n[0] * k, centre[1] + n[1] * k)
            a0 = (cxz[0] - u[0] * vent_half, cxz[1] - u[1] * vent_half)
            a1 = (cxz[0] + u[0] * vent_half, cxz[1] + u[1] * vent_half)
            back = back.cut(S.band_xz([a0, a1], 1.1, outside, yc - r + 5))
    return {"forearm_front": (front, S.GREY), "forearm_back": (back, S.GREY),
            "servo_elbow": (e_case, S.BLACK), "horn_elbow": (e_horn, S.STEEL),
            "servo_wrist_flex": (w_case, S.BLACK), "horn_wrist_flex": (w_horn, S.STEEL)}


PRINTED = ["column", "servo_clamp_shoulder", "upper_link", "forearm_front", "forearm_back"]
