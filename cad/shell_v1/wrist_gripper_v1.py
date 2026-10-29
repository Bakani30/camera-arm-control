"""Print-ready wrist + gripper for shell v1 (4.1-style look, our own geometry).

Mechanism follows what the maker's exploded view shows (two meshing gears, two links per
finger, a cover plate on top); every size here is ours. Servo pockets take the envelope of
STS3032 and MG90S so the D24 budget choice between them does not change the print.

World frame = spec base_link at q = 0 (mm). Wrist = child of wrist_flex, gripper = child of
wrist_roll. `build(phi_deg)` poses the fingers by the crank angle phi (0 = cranks along +x).

Hardware: steel pins D3 (SUS304 rod, cut), M2 self-tapping screws, servo horns that come with
the servos. Values marked MEASURE are estimates to check against the real parts before printing.
"""
import math

import FreeCAD as App
import Part
from FreeCAD import Vector as V

import shell_v1_model as S

# Envelope of STS3032 (shop pages: 23.2 x 12.1 x 28.5) and MG90S (TowerPro: 22.8 x 12.2 x 28.5).
# Ear height, ear span/pitch and shaft offset are MG90S-class values: MEASURE both servos.
MS = dict(L=23.2, W=12.2, H=22.7, ear_lo=15.9, ear_t=2.5, ear_w=32.5, ear_pitch=27.8,
          top=28.5, shaft_off=5.9, horn_d=16.0, horn_t=2.0)
G = dict(clear=0.3, wall=2.4,
         pin_free=3.3, pin_press=2.9,      # D3 steel pin: turns in links, pressed in palm/cover
         m2_free=2.2, m2_pilot=1.6,        # M2 self-tapping into PLA
         module=1.0, teeth=14,             # gear pair: centre distance = module x teeth
         link=40.0, follower_off=(-5.0, 13.0),  # four-bar: link length, follower pivot from the gear axis
                                                  # (x back, z outward): keeps the two links >= 10 mm apart
         finger_inset=12.0, finger_t=9.0, finger_len=50.0,
         rib_h=1.2)
COLORS = dict(white=S.WHITE, grey=S.GREY, black=S.BLACK, steel=S.STEEL)


# ---------------------------------------------------------------- helpers
def poly_xz(points, y0, y1):
    """Closed polygon of (x, z) points extruded from y0 to y1 (same mapping as S.band_xz)."""
    pts = [V(x, z, 0) for x, z in points] + [V(points[0][0], points[0][1], 0)]
    solid = Part.Face(Part.makePolygon(pts)).extrude(V(0, 0, -(y1 - y0)))
    solid.rotate(V(0, 0, 0), V(1, 0, 0), 90)
    solid.translate(V(0, y0, 0))
    return solid


def hole_y(x, z, d, y0, y1):
    return S.cyl_y(x, z, d / 2, y0, y1)


def gear_xz(cx, cz, rot_deg, y0, y1, bore):
    """Involute spur gear (20 deg) in the x-z plane; rot_deg turns it from +x toward +z."""
    m, n = G["module"], G["teeth"]
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
    xy = [(cx + r * math.cos(a), cz + r * math.sin(a)) for r, a in pts]
    g = poly_xz(xy, y0, y1)
    return g.cut(hole_y(cx, cz, bore, y0 - 1, y1 + 1))


def micro_servo(base, axis, length_dir):
    """Micro servo envelope placed with its shaft at `base` (case bottom plane), pointing `axis`.

    length_dir: unit vector from the shaft toward the far end of the case is -length_dir.
    Returns case (with ears, boss), horn, pocket (case+clearance up to the ear plane, ears open
    above) and the two ear pilot-hole solids.
    """
    d, c = MS, G["clear"]
    X, Z = length_dir, axis
    Y = Z.cross(X)
    m = App.Matrix(X.x, Y.x, Z.x, base.x, X.y, Y.y, Z.y, base.y, X.z, Y.z, Z.z, base.z, 0, 0, 0, 1)

    def place(s):
        s = s.copy()
        s.transformShape(m)
        return s

    xc = -d["shaft_off"]
    body = Part.makeBox(d["L"], d["W"], d["H"], V(xc - d["L"] / 2, -d["W"] / 2, 0))
    ears = Part.makeBox(d["ear_w"], d["W"], d["ear_t"], V(xc - d["ear_w"] / 2, -d["W"] / 2, d["ear_lo"]))
    boss = Part.makeCylinder(2.5, d["top"] - d["H"], V(0, 0, d["H"]))
    case = body.fuse(ears).fuse(boss)
    horn = Part.makeCylinder(d["horn_d"] / 2, d["horn_t"], V(0, 0, d["top"]))
    pocket = Part.makeBox(d["L"] + 2 * c, d["W"] + 2 * c, d["ear_lo"] + c,
                          V(xc - d["L"] / 2 - c, -d["W"] / 2 - c, -c))
    pocket = pocket.fuse(Part.makeBox(d["ear_w"] + 2 * c, d["W"] + 2 * c, 40,
                                      V(xc - d["ear_w"] / 2 - c, -d["W"] / 2 - c, d["ear_lo"])))
    pilots = [Part.makeCylinder(G["m2_pilot"] / 2, 8, V(xc + s * d["ear_pitch"] / 2, 0, d["ear_lo"] - 8))
              for s in (-1, 1)]
    return place(case), place(horn), place(pocket), [place(p) for p in pilots]


# ---------------------------------------------------------------- wrist (child of wrist_flex)
def build_wrist():
    WF, WR, cy, cz = S.WF, S.WR, S.WR.y, S.WR.z
    d, c, w = MS, G["clear"], G["wall"]
    y_h0 = S.BACK[1] + S.MG["boss"] + S.MG["horn_t"]           # sits on the MG996R horn
    y_top = cy + d["W"] / 2 + c + w
    x_b = WR.x - d["top"] - d["horn_t"]                          # roll servo case bottom
    x_ear = x_b + d["ear_lo"]                                    # ears seat on the cage front
    zc = cz - d["shaft_off"]
    case, horn, pocket, pilots = micro_servo(V(x_b, cy, cz), V(1, 0, 0), V(0, 0, 1))

    hub = S.cyl_y(WF.x, WF.z, 20.0, y_h0, y_top)
    neck = S.band_xz([(WF.x, WF.z), (x_b - c - w, cz - 3)], 14.0, y_h0, y_top)
    cage = S.box(x_b - c - w, x_ear, cy - d["W"] / 2 - c - w, y_top,
                 zc - d["ear_w"] / 2 - 1, zc + d["ear_w"] / 2 + 1)
    dome = Part.makeSphere(22.0, V(x_ear - 12, (y_h0 + y_top) / 2, cz - 4))
    dome = dome.common(S.box(x_b - 30, x_ear, y_h0, y_top, cz - 40, cz + 30))
    body = S.soften(hub.fuse(neck).fuse(cage).fuse(dome).removeSplitter(), 2.0)
    body = body.cut(pocket)
    for p in pilots:
        body = body.cut(p)
    # horn interface: centre access + 4 x M2 through the hub with counterbores (horn hole radius MEASURE)
    body = body.cut(hole_y(WF.x, WF.z, 6.5, y_h0 - 1, y_top + 1))
    for k in range(4):
        a = math.radians(45 + 90 * k)
        hx, hz = WF.x + 7.5 * math.cos(a), WF.z + 7.5 * math.sin(a)
        body = body.cut(hole_y(hx, hz, G["m2_free"], y_h0 - 1, y_top + 1))
        body = body.cut(hole_y(hx, hz, 4.2, y_h0 + 4, y_top + 1))
    # zip-tie slot on the neck for the roll and gripper cables
    nx, nz = (WF.x + x_b) / 2, (WF.z + cz - 3) / 2 - 8
    body = body.cut(S.box(nx - 4, nx + 4, y_h0 - 1, y_top + 1, nz - 0.9, nz + 0.9))
    # servo cable leaves the far end of the case
    body = body.cut(S.box(x_b - c - w - 1, x_b + 8, cy - 3, cy + 3, zc - d["L"] / 2 - c - w - 2, zc - d["L"] / 2))
    return {"wrist": (body, S.WHITE), "servo_wrist_roll": (case, S.BLACK), "horn_wrist_roll": (horn, S.STEEL)}


# ---------------------------------------------------------------- gripper (child of wrist_roll)
def layout():
    WR, cy, cz = S.WR, S.WR.y, S.WR.z
    rp = G["module"] * G["teeth"] / 2
    L = dict(x0=WR.x, cy=cy, cz=cz, gx=WR.x + 9.8, g_up=cz + rp, g_dn=cz - rp, rp=rp)
    fdx, fdz = G["follower_off"]
    L["fol"] = {1: (L["gx"] + fdx, L["g_up"] + fdz), -1: (L["gx"] + fdx, L["g_dn"] - fdz)}
    L["y_bot"] = cy - 14.0                                         # gripper servo case bottom
    L["y_ear"] = L["y_bot"] + MS["ear_lo"]                         # palm front face
    L["y_horn"] = L["y_bot"] + MS["top"] + MS["horn_t"]            # top of the servo horn
    L["gear"] = (L["y_horn"], L["y_horn"] + 4.0)
    L["link"] = (L["gear"][1], L["gear"][1] + 3.0)
    L["cover"] = (L["link"][1] + 0.5, L["link"][1] + 3.0)
    L["root"] = (L["gear"][0] + 0.2, L["gear"][1] - 0.2)
    L["palm"] = (cy - 16.7, L["y_ear"])
    L["posts"] = [(L["gx"] + 14.0, cz)]
    return L


def opening_mm(phi_deg):
    return 2 * (G["link"] * math.sin(math.radians(phi_deg)) + layout()["rp"] - G["finger_inset"]) - 2 * G["rib_h"]


def phi_for_opening(gap_mm):
    L = layout()
    s = (gap_mm / 2 + G["rib_h"] - L["rp"] + G["finger_inset"]) / G["link"]
    return math.degrees(math.asin(s))


def build_gripper(phi_deg=34.0):
    L = layout()
    cy, cz, gx = L["cy"], L["cz"], L["gx"]
    d, c = MS, G["clear"]
    phi = math.radians(phi_deg)
    parts = {}

    # palm: servo pocket (inserted from the front, ears on the front face), follower pin seats,
    # cover posts, horn interface on the back, cable exit through the bottom
    case, horn, pocket, pilots = micro_servo(V(gx, L["y_bot"], L["g_up"]), V(0, 1, 0), V(0, 0, 1))
    palm = S.soften(S.box(L["x0"], gx + 22, L["palm"][0], L["palm"][1], cz - 25, cz + 25), 2.0)
    for px, pz in L["posts"]:
        palm = palm.fuse(S.cyl_y(px, pz, 3.0, L["palm"][1] - 1, L["cover"][0]))
    palm = palm.removeSplitter().cut(pocket)
    for p in pilots:
        palm = palm.cut(p)
    for px, pz in L["posts"]:
        palm = palm.cut(hole_y(px, pz, G["m2_pilot"], L["cover"][0] - 8, L["cover"][0] + 1))
    for px, pz in L["fol"].values():
        palm = palm.cut(hole_y(px, pz, G["pin_press"], L["palm"][1] - 8, L["palm"][1] + 1))
    roll_access = Part.makeCylinder(3.25, 60, V(L["x0"] - 1, cy, cz), V(1, 0, 0))
    palm = palm.cut(roll_access)
    for k in range(4):                                         # horn pattern MEASURE
        a = math.radians(45 + 90 * k)
        palm = palm.cut(Part.makeCylinder(G["m2_pilot"] / 2, 6, V(L["x0"] - 0.1, cy + 7 * math.cos(a),
                                                                  cz + 7 * math.sin(a)), V(1, 0, 0)))
    palm = palm.cut(S.box(gx - 3, gx + 3, cy - 12, cy - 6, cz - 25, cz - 10))
    parts["gripper_palm"] = (palm, S.WHITE)
    parts["servo_gripper"] = (case, S.BLACK)
    parts["horn_gripper"] = (horn, S.STEEL)

    # gears + cranks: upper gear on the servo horn, lower gear on a pin from the cover; the lower
    # one is the mirror image turned half a tooth so the pair meshes
    half_tooth = 180.0 / G["teeth"]
    for name, gz, side in (("up", L["g_up"], 1), ("dn", L["g_dn"], -1)):
        rot = side * phi_deg - 90 * side + (half_tooth if side < 0 else 0)
        gear = gear_xz(gx, gz, rot, L["gear"][0], L["gear"][1], 5.0 if side > 0 else G["pin_free"])
        end = (gx + G["link"] * math.cos(phi), gz + side * G["link"] * math.sin(phi))
        crank = S.band_xz([(gx, gz), end], 4.0, L["link"][0], L["link"][1])
        crank = crank.fuse(S.cyl_y(gx, gz, 6.0, L["link"][0], L["link"][1]))
        gc = gear.fuse(crank).removeSplitter()
        gc = gc.cut(hole_y(end[0], end[1], G["pin_free"], L["gear"][0] - 1, L["link"][1] + 1))
        gc = gc.cut(hole_y(gx, gz, 5.0 if side > 0 else G["pin_free"], L["gear"][0] - 1, L["link"][1] + 1))
        if side > 0:                                           # screws into the servo horn: MEASURE
            for s in (-1, 1):
                gc = gc.cut(hole_y(gx + s * 5.5, gz, G["m2_free"], L["gear"][0] - 1, L["link"][1] + 1))
        parts["gripper_gear_crank_" + name] = (gc, S.GREY)

        fp = L["fol"][side]
        fend = (fp[0] + G["link"] * math.cos(phi), fp[1] + side * G["link"] * math.sin(phi))
        fol = S.band_xz([fp, fend], 4.0, L["link"][0], L["link"][1])
        for px, pz in (fp, fend):                              # round pivot bosses (4.1 look)
            fol = fol.fuse(S.cyl_y(px, pz, 4.5, L["link"][0], L["link"][1]))
        fol = fol.removeSplitter()
        for px, pz in (fp, fend):
            fol = fol.cut(hole_y(px, pz, G["pin_free"], L["link"][0] - 1, L["link"][1] + 1))
        parts["gripper_follower_" + name] = (fol, S.GREY)

        # finger: root plate under both link ends, then a tall plate forward of the palm
        ax, az = end
        bx, bz = fend
        inner = az - side * G["finger_inset"]
        outer = inner + side * G["finger_t"]
        x_start = ax + 7.0
        root = S.band_xz([(ax, az), (bx, bz)], 5.0, L["root"][0], L["root"][1])
        web = S.box(ax, x_start + 12, L["root"][0], L["root"][1], min(inner, az + 5 * side), max(inner, az + 5 * side))
        plate = S.box(x_start, x_start + G["finger_len"], cy - 10, L["root"][1], min(inner, outer), max(inner, outer))
        finger = S.soften(root.fuse(web).fuse(plate).removeSplitter(), 1.0)
        # V lightening groove on the outer face (4.1 look)
        groove = poly_xz([(x_start + 12, outer), (x_start + 40, outer), (x_start + 26, outer - side * 3.5)],
                         cy - 4, L["root"][1] - 3)
        finger = finger.cut(groove)
        # grip texture near the tip: comb ribs on the upper finger, saw teeth on the lower one
        tip0 = x_start + G["finger_len"] - 24
        for k in range(10):
            rx = tip0 + k * 2.4
            if side > 0:
                tooth = S.box(rx, rx + 1.2, cy - 10, L["root"][1], inner - G["rib_h"], inner)
            else:
                tooth = poly_xz([(rx, inner), (rx + 2.4, inner), (rx + 2.4, inner + G["rib_h"])], cy - 10, L["root"][1])
            finger = finger.fuse(tooth)
        for px, pz in (end, fend):
            finger = finger.cut(hole_y(px, pz, G["pin_free"], L["root"][0] - 1, L["root"][1] + 1))
        parts["gripper_finger_" + name] = (finger.removeSplitter(), S.WHITE)

    # cover plate: rounded outline over gears and pins, held by two posts and the pins
    pts = [L["fol"][-1], (gx + 6, L["g_dn"] - 3), L["posts"][0], (gx + 6, L["g_up"] + 3), L["fol"][1]]
    w = Part.makePolygon([V(x, z, 0) for x, z in pts] + [V(pts[0][0], pts[0][1], 0)])
    face = Part.Face(w.makeOffset2D(5.0, 0, False, False, False))
    cover = face.extrude(V(0, 0, -(L["cover"][1] - L["cover"][0])))
    cover.rotate(V(0, 0, 0), V(1, 0, 0), 90)
    cover.translate(V(0, L["cover"][0], 0))
    for px, pz in L["posts"]:
        cover = cover.cut(hole_y(px, pz, G["m2_free"], L["cover"][0] - 1, L["cover"][1] + 1))
    for px, pz in (L["fol"][1], L["fol"][-1], (gx, L["g_dn"])):
        cover = cover.cut(hole_y(px, pz, G["pin_press"], L["cover"][0] - 1, L["cover"][1] + 1))
    cover = cover.cut(hole_y(gx, L["g_up"], 6.0, L["cover"][0] - 1, L["cover"][1] + 1))
    parts["gripper_cover"] = (S.soften(cover, 0.8), S.WHITE)

    # steel pins (not printed)
    pins = None
    specs = [(*L["fol"][1], L["palm"][1] - 8, L["cover"][1]), (*L["fol"][-1], L["palm"][1] - 8, L["cover"][1]),
             (gx, L["g_dn"], L["gear"][0], L["cover"][1])]
    for gz, side in ((L["g_up"], 1), (L["g_dn"], -1)):
        fp = L["fol"][side]
        specs.append((gx + G["link"] * math.cos(phi), gz + side * G["link"] * math.sin(phi), L["root"][0], L["link"][1]))
        specs.append((fp[0] + G["link"] * math.cos(phi), fp[1] + side * G["link"] * math.sin(phi), L["root"][0], L["link"][1]))
    for px, pz, y0, y1 in specs:
        p = S.cyl_y(px, pz, 1.45, y0, y1)
        pins = p if pins is None else pins.fuse(p)
    parts["gripper_pins"] = (pins, S.STEEL)
    return parts, {"opening_mm": opening_mm(phi_deg), "pin_lengths_mm": sorted({round(s[3] - s[2], 1) for s in specs})}


PRINTED = ["wrist", "gripper_palm", "gripper_gear_crank_up", "gripper_gear_crank_dn", "gripper_follower_up",
           "gripper_follower_dn", "gripper_finger_up", "gripper_finger_dn", "gripper_cover"]
