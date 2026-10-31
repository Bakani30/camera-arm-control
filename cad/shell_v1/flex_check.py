"""How far the printed links bend under the task loads: FEM (gmsh + CalculiX from the FreeCAD install).

Run: freecadcmd flex_check.py (writes out/motion/flex_check.json; run motion_test.py first for its poses)
Each link is clamped at its proximal joint with a rigid distal joint. Six unit loads give its compliance, then every
task pose adds up the link deflections at the TCP. E_MPA stands in for a printed part: results scale with 1/E.
Conservative: the servos inside the links add no stiffness, and a link's own weight is applied at its distal joint.
Not modelled: bearings, servo backlash and compliance, the screwed split of the forearm, layer direction.
The forearm uses a simplified shape (see simple_forearm); the other links use the CAD part.
"""
import json
import math
import os
import re
import shutil
import subprocess
import sys

os.environ["MOTION_SCENARIOS"] = "none"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import motion_test as T  # noqa: E402
import links_v1 as LK  # noqa: E402

B, M, WG, V, Part, App = T.B, T.M, T.WG, T.V, T.Part, T.App
E_MPA = 2100.0     # PLA ~3500 MPa x ~0.6 for walls and 20% infill (assumed)
POISSON = 0.35
MESH_TRIES = (("del2d", 1.25, 5), ("meshadapt", 1.25, 5), ("auto", 2.5, 5), ("auto", 1.5, 5), ("auto", 2.5, 7))
WORK = os.path.join(HERE, "out", "motion", "fem")
SCENES = ("D_survey_compensated", "E_mid_compensated")


def tool(name):
    return shutil.which(name) or os.path.join(App.getHomePath(), "bin", name)


def read_mesh(inp):
    """Nodes and second-order tetrahedra from a gmsh .inp file; surface and line elements are dropped."""
    nodes, elements, section = {}, [], None
    for line in open(inp):
        if line.startswith("*"):
            head = line.upper()
            section = "n" if head.startswith("*NODE") else "e" if "C3D10" in head else None
        elif section == "n":
            f = line.split(",")
            nodes[int(f[0])] = tuple(float(v) for v in f[1:4])
        elif section == "e":
            elements.append([int(v) for v in line.replace(",", " ").split()])
    used = {n for e in elements for n in e[1:]}
    return {k: v for k, v in nodes.items() if k in used}, elements


def gmsh(source, inp, *options):
    if os.path.exists(inp):
        os.remove(inp)
    # straight-sided second-order elements: curved ones on small fillets invert and stop the solver
    run = subprocess.run([tool("gmsh"), source, "-3", "-order", "2", "-setnumber", "Mesh.SecondOrderLinear", "1",
                          *options, "-format", "inp", "-o", inp, "-v", "1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return run.returncode == 0 and os.path.exists(inp)


def mesh(shape, name):
    step = os.path.join(WORK, name + ".step")
    inp = os.path.join(WORK, name + "_mesh.inp")
    shape.exportStep(step)
    for algo, least, most in MESH_TRIES:           # small fillet faces can defeat one setting and not another
        if gmsh(step, inp, "-algo", algo, "-clmax", str(most), "-clmin", str(least)):
            nodes, elements = read_mesh(inp)
            if elements:
                print("%s meshed from the solid: %s, %.2f to %.1f mm" % (name, algo, least, most), flush=True)
                return nodes, elements
    raise RuntimeError("%s: gmsh could not mesh it" % name)


def lines_of(ids, per=12):
    ids = sorted(ids)
    return "\n".join(", ".join(str(i) for i in ids[k:k + per]) + "," for k in range(0, len(ids), per))


def compliance(name, nodes, elements, fixed, rigid, ref):
    """6 x 6 matrix: (ux, uy, uz, rx, ry, rz) at ref for unit (Fx, Fy, Fz, Mx, My, Mz), in mm, rad, N, N mm."""
    if not fixed or not rigid or set(fixed) & set(rigid):
        raise ValueError("%s: bad supports, %d fixed and %d rigid nodes" % (name, len(fixed), len(rigid)))
    r1, r2 = max(nodes) + 1, max(nodes) + 2
    text = ["*NODE"] + ["%d, %.6f, %.6f, %.6f" % (k, *v) for k, v in nodes.items()]
    text += ["%d, %.6f, %.6f, %.6f" % (r1, ref.x, ref.y, ref.z), "%d, %.6f, %.6f, %.6f" % (r2, ref.x, ref.y, ref.z)]
    text += ["*ELEMENT, TYPE=C3D10, ELSET=EALL"] + [", ".join(str(v) for v in e) for e in elements]
    text += ["*NSET, NSET=FIXED", lines_of(fixed), "*NSET, NSET=RIGID", lines_of(rigid), "*NSET, NSET=REF", "%d, %d" % (r1, r2)]
    text += ["*MATERIAL, NAME=PLA", "*ELASTIC", "%g, %g" % (E_MPA, POISSON), "*SOLID SECTION, ELSET=EALL, MATERIAL=PLA"]
    text += ["*RIGID BODY, NSET=RIGID, REF NODE=%d, ROT NODE=%d" % (r1, r2), "*BOUNDARY", "FIXED, 1, 3"]
    for node, dof in [(r1, 1), (r1, 2), (r1, 3), (r2, 1), (r2, 2), (r2, 3)]:
        text += ["*STEP", "*STATIC", "*CLOAD, OP=NEW", "%d, %d, 1.0" % (node, dof), "*NODE PRINT, NSET=REF", "U", "*END STEP"]
    job = os.path.join(WORK, name)
    with open(job + ".inp", "w") as f:
        f.write("\n".join(text) + "\n")
    subprocess.run([tool("ccx"), "-i", name], cwd=WORK, check=True, stdout=subprocess.DEVNULL, env=dict(os.environ, OMP_NUM_THREADS="4"))
    values = {r1: [], r2: []}
    for line in open(job + ".dat"):
        f = line.split()
        if len(f) == 4 and re.fullmatch(r"\d+", f[0]) and int(f[0]) in values:
            values[int(f[0])].append([float(v) for v in f[1:4]])
    if len(values[r1]) != 6 or len(values[r2]) != 6:
        raise RuntimeError("%s: expected 6 steps in %s.dat" % (name, job))
    return [[*values[r1][k], *values[r2][k]] for k in range(6)]  # row k = response to load k


def validate_solver():
    """A cantilever with a known answer, so the supports and units are proven before the arm is trusted."""
    length, width, height = 200.0, 20.0, 10.0
    bar = Part.makeBox(length, width, height)
    nodes, elements = mesh(bar, "bar")
    fixed = [k for k, v in nodes.items() if v[0] < 0.01]     # the mesher's geometry repair leaves small offsets
    rigid = [k for k, v in nodes.items() if v[0] > length - 0.01]
    c = compliance("bar", nodes, elements, fixed, rigid, V(length, width / 2, height / 2))
    expected = length ** 3 / (3 * E_MPA * width * height ** 3 / 12)
    got = c[2][2]
    print("cantilever check: %.5f mm/N, beam theory %.5f (%.1f%% off)" % (got, expected, 100 * (got / expected - 1)), flush=True)
    if abs(got / expected - 1) > 0.06:
        raise RuntimeError("cantilever check failed")
    return dict(fem=got, beam=expected)


def radial(p, centre):
    return math.hypot(p[0] - centre.x, p[2] - centre.z)


def simple_forearm():
    """Tube, hubs, channel, servo pockets, and option C's frames. The full part will not mesh: its tube meets the hubs almost tangent."""
    y_front = B.BACK[1]
    r = LK.H["tube_r"]
    yc = y_front - r
    e, w = (B.EL.x, B.EL.z), (B.WF.x, B.WF.z)
    length = math.hypot(w[0] - e[0], w[1] - e[1])
    u = ((w[0] - e[0]) / length, (w[1] - e[1]) / length)
    tube = Part.makeCylinder(r - 0.2, length, V(e[0], yc, e[1]), V(u[0], 0, u[1]))
    tube = tube.fuse(B.cyl_y(e[0], e[1], 20.0, yc - r, y_front)).fuse(B.cyl_y(w[0], w[1], r, yc - r, y_front)).removeSplitter()
    back = (-u[0], -u[1])
    if LK.FOREARM_FRAMES:
        tube = tube.fuse(LK.servo_box(e, u, y_front)).fuse(LK.servo_box(w, back, y_front)).removeSplitter()
    tube = tube.cut(B.servo_y("sts", e, y_front, +1, u)[2]).cut(B.servo_y("sts", w, y_front, +1, back)[2])
    start = V(e[0] + u[0] * 30, yc, e[1] + u[1] * 30)
    tube = tube.cut(Part.makeCylinder(LK.H["channel_r"], length - 60, start, V(u[0], 0, u[1]))).removeSplitter()
    if LK.FOREARM_FRAMES:
        tube = tube.cut(LK.servo_window(e, u, y_front)).cut(LK.servo_window(w, back, y_front)).removeSplitter()
    return tube


def links(arm):
    shapes = arm.parts
    forearm = simple_forearm()
    x_roll_cage = B.WR.x - 30.0
    table = T.BV.Z_TT + T.BV.B["tt_t"]
    return [
        dict(name="column", shape=shapes["column"][0], carrier="column", own=("column", "servo_shoulder", "servo_clamp_shoulder"),
             next="shoulder_lift", ref=B.SH, fixed=lambda p: p[2] <= table, rigid=lambda p: radial(p, B.SH) <= 26.0),
        dict(name="upper_link", shape=shapes["upper_link"][0], carrier="upper_link", own=("upper_link", "horn_shoulder", "bearing_shoulder", "bearing_elbow", "horn_elbow"),
             next="elbow_flex", ref=B.EL, fixed=lambda p: radial(p, B.SH) <= 26.0, rigid=lambda p: radial(p, B.EL) <= 26.0),
        dict(name="forearm", shape=forearm, carrier="forearm_front", own=("forearm_front", "forearm_back", "servo_elbow", "servo_wrist_flex"),
             next="wrist_flex", ref=B.WF, fixed=lambda p: radial(p, B.EL) <= 24.0, rigid=lambda p: radial(p, B.WF) <= 24.0),
        dict(name="wrist", shape=shapes["wrist"][0], carrier="wrist", own=("wrist", "servo_wrist_roll", "horn_wrist_flex"),
             next="wrist_roll", ref=B.WR, fixed=lambda p: radial(p, B.WF) <= 20.0, rigid=lambda p: p[0] >= x_roll_cage),
    ]


def matvec(r, v):
    return V(r[0].x * v.x + r[1].x * v.y + r[2].x * v.z, r[0].y * v.x + r[1].y * v.y + r[2].y * v.z,
             r[0].z * v.x + r[1].z * v.y + r[2].z * v.z)


def tcp_deflection(arm, link_data, q_deg, block_g, force_n, tool_q0):
    """Displacement (world, mm) of the TCP from every link's bend, plus each link's share."""
    tcp = arm.point(tool_q0, "gripper_palm", q_deg)
    total, shares = V(0, 0, 0), {}
    for link in link_data:
        carrier = link["carrier"]
        origin = arm.point(V(0, 0, 0), carrier, q_deg)
        basis = [arm.point(e, carrier, q_deg) - origin for e in (V(1, 0, 0), V(0, 1, 0), V(0, 0, 1))]
        ref = arm.point(link["ref"], carrier, q_deg)
        force, moment = V(0, 0, 0), V(0, 0, 0)
        for name, (m, c) in arm.mass.items():
            if link["next"] in B.moved_by(name) or name in link["own"]:
                f = V(0, 0, -m * 9.81e-3)
                force += f
                moment += (arm.point(c, name, q_deg) - ref).cross(f)
        f = V(0, 0, force_n - block_g * 9.81e-3)
        force += f
        moment += (tcp - ref).cross(f)
        local = [force.dot(basis[0]), force.dot(basis[1]), force.dot(basis[2]), moment.dot(basis[0]), moment.dot(basis[1]), moment.dot(basis[2])]
        response = [sum(link["c"][k][i] * local[k] for k in range(6)) for i in range(6)]
        u = matvec(basis, V(*response[:3]))
        theta = matvec(basis, V(*response[3:]))
        move = u + theta.cross(tcp - ref)
        total += move
        shares[link["name"]] = round(move.Length, 3)
    return total, shares


def main():
    os.makedirs(WORK, exist_ok=True)
    check = validate_solver()
    arm = T.Arm()
    data = []
    for link in links(arm):
        nodes, elements = mesh(link["shape"], link["name"])
        fixed = [k for k, v in nodes.items() if link["fixed"](v)]
        rigid = [k for k, v in nodes.items() if link["rigid"](v)]
        link["c"] = compliance(link["name"], nodes, elements, fixed, rigid, link["ref"])
        print("%-11s %6d nodes %6d elements, fixed %d, rigid %d, solids %d, valid %s" % (link["name"], len(nodes), len(elements), len(fixed), len(rigid), len(link["shape"].Solids), link["shape"].isValid()), flush=True)
        data.append(link)
    out = dict(E_MPa=E_MPA, cantilever=check, scenes={},
               compliance={d["name"]: d["c"] for d in data})
    for scene in SCENES:
        report = json.load(open(os.path.join(HERE, "out", "motion", scene + ".json")))
        rows = []
        for move in report["moves"]:
            if not move["task"]:
                continue
            block_g = T.BLOCK_G if move["block"] == "carried" else 0.0
            force = M.BUTTON_FORCE_N if move["name"].startswith("10") else 0.0
            for i, s in enumerate(move["samples"]):
                if s["unreachable"]:
                    continue
                q = s["q_deg"]
                tool_q0 = T.tool_point(M.pad_center_tcp, s["opening_mm"])
                loaded, shares = tcp_deflection(arm, data, q, block_g, force, tool_q0)
                unloaded, _ = tcp_deflection(arm, data, q, 0.0, 0.0, tool_q0)
                rows.append(dict(move=move["name"], sample=i, total_mm=round(loaded.Length, 3), z_mm=round(loaded.z, 3),
                                 load_change_mm=round((loaded - unloaded).Length, 3), shares=shares))
        worst = max(rows, key=lambda r: r["total_mm"])
        change = max(rows, key=lambda r: r["load_change_mm"])
        out["scenes"][scene] = dict(worst=worst, worst_load_change=change, rows=rows)
        print(scene, "worst", worst, "| largest change from block or press", change["move"], change["load_change_mm"], flush=True)
    with open(os.path.join(HERE, "out", "motion", "flex_check.json"), "w") as f:
        json.dump(out, f)
    print("done", flush=True)


main()
