"""Print-ready base for shell v1: drum + lid + board tray + five slot-in legs (4.1-style look).

The turntable rides on the 4" (100 mm) lazy-susan bearing from the D28 BOM, so the drum grows to
D150 (the spec v0 base diameter); the pan STS3215 stands in a cradle with its horn face at the spec
pan origin height. Electronics (bus adapter, Nano, PCA9685/buck) go on a perforated tray. The 12 V
PSU and the E-stop stay outside the drum.

Lazy-susan sizes and hole positions, the DC jack and USB cut-outs are estimates: MEASURE.
"""
import math

import Part
from FreeCAD import Vector as V

import shell_v1_model as S

B = dict(r=75.0, h=56.0, wall=3.0, lid_t=3.0, floor=3.0,
         ls_side=100.0, ls_t=8.0, ls_hole=62.0,           # lazy susan 4": MEASURE
         ls_bottom_xy=40.0, ls_top_r=44.0, ls_access_d=9.0,
         tt_r=70.0, tt_t=6.0, tt_boss_r=15.0,
         lid_boss_r=66.0,
         legs=5, leg_tip_r=170.0, sock_len=20.0, tongue_w=16.0, tongue_h=10.0,
         leg_w_root=20.0, leg_w_tip=5.0, leg_h_root=14.0, leg_h_tip=4.0,
         tray_z=8.0, tray_t=2.5, tray_pitch=10.0, tray_hole=2.6,
         m3_free=3.4, m3_pilot=2.5)
PAN = S.PAN
CX, CY = PAN.x, S.Y0
Z_LID = B["h"] - B["lid_t"]                     # lid sits on the wall top
Z_TT = B["h"] + B["ls_t"]                       # turntable bottom = top of the lazy susan


def at(r, deg, z=0.0):
    a = math.radians(deg)
    return V(CX + r * math.cos(a), CY + r * math.sin(a), z)


def zcyl(r, z0, z1, x=CX, y=CY):
    return Part.makeCylinder(r, z1 - z0, V(x, y, z0))


def leg_angles():
    return [180 + 360.0 / B["legs"] * k for k in range(B["legs"])]


def pan_servo_box(grow=0.0, z0=None, z1=None):
    d = S.STS
    face = PAN.z - d["boss"] - d["horn_t"]
    z0 = face - d["H"] if z0 is None else z0
    z1 = face if z1 is None else z1
    return S.box(CX - d["shaft_off"] - d["L"] / 2 - grow, CX - d["shaft_off"] + d["L"] / 2 + grow,
                 CY - d["W"] / 2 - grow, CY + d["W"] / 2 + grow, z0, z1)


def wall_cut(deg, shape):
    """Shape built with x = 0 at the drum's outer wall (x < 0 inside), turned to the angle `deg`."""
    shape = shape.copy()
    shape.translate(V(B["r"], 0, 0))
    return socket_frame(shape, deg)


def socket_frame(shape, deg):
    shape.rotate(V(0, 0, 0), V(0, 0, 1), deg)
    shape.translate(V(CX, CY, 0))
    return shape


def build_base():
    parts = {}
    w, c = B["wall"], S.P["clearance"]
    d = S.STS
    face = PAN.z - d["boss"] - d["horn_t"]

    # ---- drum (cup): floor, wall, lid bosses, servo cradle, tray posts, leg sockets
    drum = zcyl(B["r"], 0, Z_LID).cut(zcyl(B["r"] - w, B["floor"], Z_LID + 1))
    for k in range(4):
        p = at(B["lid_boss_r"], 90 * k)
        drum = drum.fuse(zcyl(5.0, B["floor"], Z_LID, p.x, p.y))
    cradle = pan_servo_box(c + 3.0, B["floor"], face - 10.0).cut(pan_servo_box(c, face - d["H"], face))
    drum = drum.fuse(cradle)
    for k in range(4):
        p = at(55.0, 45 + 90 * k)
        drum = drum.fuse(zcyl(4.0, B["floor"], B["tray_z"], p.x, p.y))
    sock_outer = B["r"] + B["sock_len"]
    for deg in leg_angles():
        sock = Part.makeBox(sock_outer - (B["r"] - w), B["tongue_w"] + 2 * c + 2 * 2.5, B["tongue_h"] + c + 2.5,
                            V(B["r"] - w, -(B["tongue_w"] / 2 + c + 2.5), 0))
        drum = drum.fuse(socket_frame(sock, deg))
    drum = S.soften(drum.removeSplitter(), 1.0)
    for deg in leg_angles():
        slot = Part.makeBox(sock_outer - (B["r"] - w) + 1 - 0.5, B["tongue_w"] + 2 * c, B["tongue_h"] + c + 1,
                            V(B["r"] - w + 0.5, -(B["tongue_w"] / 2 + c), -1))
        screw = Part.makeCylinder(B["m3_free"] / 2, 10, V(B["r"] + B["sock_len"] / 2, 0, 0))
        drum = drum.cut(socket_frame(slot, deg)).cut(socket_frame(screw, deg))
    for k in range(4):                                       # lid screw pilots
        p = at(B["lid_boss_r"], 90 * k)
        drum = drum.cut(zcyl(B["m3_pilot"] / 2, Z_LID - 10, Z_LID + 1, p.x, p.y))
    for k in range(4):                                       # tray screw pilots
        p = at(55.0, 45 + 90 * k)
        drum = drum.cut(zcyl(B["m3_pilot"] / 2, B["tray_z"] - 5, B["tray_z"] + 1, p.x, p.y))
    drum = drum.cut(S.box(CX - d["shaft_off"] - d["L"] / 2 - c - 4, CX - d["shaft_off"] - d["L"] / 2 + 6,
                          CY - 4, CY + 4, face - d["H"] - 1, face - d["H"] + 8))   # servo cable out of the cradle
    # wall openings, all between the legs: DC jack, USB-C of the bus adapter, a gland for the
    # PSU / E-stop leads with a tie bar inside for strain relief (sizes MEASURE)
    drum = drum.cut(wall_cut(216, Part.makeCylinder(5.6, 4 * w, V(-2 * w, 0, 35), V(1, 0, 0))))
    drum = drum.cut(wall_cut(144, S.box(-2 * w, 2 * w, -6.5, 6.5, 26, 34)))
    drum = drum.cut(wall_cut(288, Part.makeCylinder(6.0, 4 * w, V(-2 * w, 0, 30), V(1, 0, 0))))
    bar = S.box(-w - 8, -w - 4, -9, 9, 16, 20)              # bridge: the zip tie loops round it
    drum = drum.fuse(wall_cut(288, bar.fuse(S.box(-w - 8, -w + 0.5, -9, -6, B["floor"], 20)).fuse(
        S.box(-w - 8, -w + 0.5, 6, 9, B["floor"], 20)))).removeSplitter()
    # table clamp lugs behind the arm (review item 5): the CoM sits ~120 mm out when the arm reaches
    # forward, so the back of the base is what lifts; an M6 bolt or a G-clamp pad goes through each lug
    for deg in (144, 216):
        lug = S.box(-2, 28, -13, 13, 0, 8)
        # gusset stays inside x <= 8 so an M6 washer (D12) or a clamp pad sits flat round the hole
        gusset = Part.Face(Part.makePolygon([V(0, -3, 8), V(0, -3, 20), V(8, -3, 8), V(0, -3, 8)])).extrude(V(0, 6, 0))
        lug = S.soften(lug.fuse(gusset).removeSplitter(), 1.0)
        lug = lug.cut(Part.makeCylinder(3.3, 20, V(18, 0, -1)))
        drum = drum.fuse(wall_cut(deg, lug))
    # fiducial pad at the front (review item 5): a flat face with a 0.6 mm recess for a 40 mm marker
    pad = S.box(-4, 3, -23, 23, 6, Z_LID - 1)
    pad = pad.cut(S.box(2.4, 4, -20.2, 20.2, 7.8, 48.2))          # 40.4 x 40.4 for a 40 mm marker
    drum = drum.fuse(wall_cut(0, pad)).removeSplitter()
    parts["base_drum"] = (drum, S.WHITE)

    # ---- lid: servo top passes through, lazy-susan bottom plate screws in, cable hole
    lid = zcyl(B["r"], Z_LID, B["h"])
    lid = S.soften(lid, 1.0)
    lid = lid.cut(pan_servo_box(c, Z_LID - 1, B["h"] + 1))
    lid = lid.cut(pan_pin_hole())
    # arm cables drop from the turntable hole (r 24, turns with the arm) into the annulus between the
    # boss (r 15) and the lazy-susan opening (r 31), wrap there over +-180 deg, and leave through
    # this fixed slot; keep a service loop of about one turn (~150 mm) in the drum
    slot = None
    for a in range(-30, 31, 5):
        p = at(S.P["cable_hole_r"], a)
        h = zcyl(S.P["cable_hole_d"] / 2, Z_LID - 1, B["h"] + 1, p.x, p.y)
        slot = h if slot is None else slot.fuse(h)
    lid = lid.cut(slot)
    for k in range(4):
        p = at(B["lid_boss_r"], 90 * k)
        lid = lid.cut(zcyl(B["m3_free"] / 2, Z_LID - 1, B["h"] + 1, p.x, p.y))
        lid = lid.cut(Part.makeCone(B["m3_free"] / 2, 3.2, 1.6, V(p.x, p.y, B["h"] - 1.6)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            lid = lid.cut(zcyl(B["m3_pilot"] / 2, Z_LID - 1, B["h"] + 1,
                               CX + sx * B["ls_bottom_xy"], CY + sy * B["ls_bottom_xy"]))
    parts["base_lid"] = (lid, S.WHITE)

    # ---- board tray: perforated plate on four posts, cut out around the servo cradle
    tray = zcyl(B["r"] - w - 2, B["tray_z"], B["tray_z"] + B["tray_t"])
    tray = tray.cut(pan_servo_box(c + 3.0 + 2.0, B["tray_z"] - 1, B["tray_z"] + B["tray_t"] + 1))
    holes = []
    n = int((B["r"] - w - 6) // B["tray_pitch"])
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            x, y = i * B["tray_pitch"], j * B["tray_pitch"]
            if math.hypot(x, y) < B["r"] - w - 6:
                holes.append(zcyl(B["tray_hole"] / 2, B["tray_z"] - 1, B["tray_z"] + B["tray_t"] + 1, CX + x, CY + y))
    tray = tray.cut(Part.makeCompound(holes))
    for k in range(4):                                       # clear the lid bosses and the tie bar
        p = at(B["lid_boss_r"], 90 * k)
        tray = tray.cut(zcyl(5.0 + c + 0.5, B["tray_z"] - 1, B["tray_z"] + B["tray_t"] + 1, p.x, p.y))
    tray = tray.cut(wall_cut(288, S.box(-w - 13, 1, -12, 12, B["tray_z"] - 1, B["tray_z"] + B["tray_t"] + 1)))
    for k in range(4):
        p = at(55.0, 45 + 90 * k)
        tray = tray.cut(zcyl(B["m3_free"] / 2, B["tray_z"] - 1, B["tray_z"] + B["tray_t"] + 1, p.x, p.y))
    parts["base_tray"] = (tray, S.GREY)

    # ---- legs: tongue into the socket (one M3 from the top), tapered blade outside
    for k, deg in enumerate(leg_angles()):
        t_in, t_out = B["r"] - w + 0.5 + c, sock_outer
        tongue = Part.makeBox(t_out - t_in, B["tongue_w"], B["tongue_h"], V(t_in, -B["tongue_w"] / 2, 0))
        r0, r1 = sock_outer, B["leg_tip_r"]
        w0, w1 = B["leg_w_root"], B["leg_w_tip"]
        blade = Part.Face(Part.makePolygon([V(r0, -w0 / 2, 0), V(r1, -w1 / 2, 0), V(r1 + w1, 0, 0),
                                            V(r1, w1 / 2, 0), V(r0, w0 / 2, 0), V(r0, -w0 / 2, 0)])
                          ).extrude(V(0, 0, B["leg_h_root"]))
        slope = Part.Face(Part.makePolygon([V(r0, -50, B["leg_h_root"]), V(r1 + w1 + 1, -50, B["leg_h_tip"]),
                                            V(r1 + w1 + 1, -50, 50), V(r0, -50, 50),
                                            V(r0, -50, B["leg_h_root"])])).extrude(V(0, 100, 0))
        leg = tongue.fuse(blade.cut(slope)).removeSplitter()
        leg = S.soften(leg, 0.8)
        leg = leg.cut(Part.makeCylinder(B["m3_pilot"] / 2, 8, V(B["r"] + B["sock_len"] / 2, 0, B["tongue_h"] - 7.9)))
        parts["base_leg_%d" % (k + 1)] = (socket_frame(leg, deg), S.WHITE)

    # ---- bought parts
    ls = S.box(CX - B["ls_side"] / 2, CX + B["ls_side"] / 2, CY - B["ls_side"] / 2, CY + B["ls_side"] / 2,
               B["h"], Z_TT).cut(zcyl(B["ls_hole"] / 2, B["h"] - 1, Z_TT + 1))
    parts["base_lazy_susan"] = (ls, S.STEEL)
    case = pan_servo_box()
    horn = zcyl(3.0, face, face + d["boss"]).fuse(zcyl(d["horn_d"] / 2, face + d["boss"], PAN.z))
    parts["servo_pan"] = (case, S.BLACK)
    parts["horn_pan"] = (horn, S.STEEL)
    return parts


def pan_pin_hole():
    """Calibration pin at q = 0: through the turntable, the lazy-susan opening and the lid."""
    return zcyl(1.6, Z_LID - 1, Z_TT + B["tt_t"] + 1, CX, CY + 27.0)


def turntable():
    """Disc on the lazy susan + boss down to the pan horn (fused into the column print)."""
    tt = zcyl(B["tt_r"], Z_TT, Z_TT + B["tt_t"]).fuse(zcyl(B["tt_boss_r"], PAN.z, Z_TT + 0.5))
    tt = S.soften(tt.removeSplitter(), 1.5)
    tt = tt.cut(zcyl(S.P["cable_hole_d"] / 2, PAN.z - 1, Z_TT + B["tt_t"] + 1, CX + S.P["cable_hole_r"], CY))
    for k in range(4):                                       # lazy-susan top plate screws (MEASURE)
        p = at(B["ls_top_r"], 90 * k)
        tt = tt.cut(zcyl(B["m3_pilot"] / 2, Z_TT - 1, Z_TT + 5, p.x, p.y))
    p = at(math.hypot(B["ls_bottom_xy"], B["ls_bottom_xy"]), 45)   # reach the bottom-plate screws from above
    tt = tt.cut(zcyl(B["ls_access_d"] / 2, Z_TT - 1, Z_TT + B["tt_t"] + 1, p.x, p.y))
    return tt


PRINTED = ["base_drum", "base_lid", "base_tray"] + ["base_leg_%d" % (k + 1) for k in range(B["legs"])]
