"""One command for shell v1 on macOS, Windows or Linux: build, check, render.

    python run_shell_v1.py                 # build + renders of the default poses
    python run_shell_v1.py --check         # also run check_shell_v1.py (~30 s)
    python run_shell_v1.py --no-render     # build only
    python run_shell_v1.py --open          # then open it in the FreeCAD GUI with colours
    python run_shell_v1.py --poses '{"ready": {"shoulder_lift": -15, "elbow_flex": 35}}'
    python run_shell_v1.py --no-build --no-render --motion   # the arm doing the task, with table, block, tray, button

Needs FreeCAD 1.1 (freecadcmd is found on PATH or in the usual install folders, or set
FREECADCMD). Renders need uv (https://docs.astral.sh/uv/); it fetches numpy-stl and matplotlib itself.
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_POSES = {
    "zero": {},
    "ready": {"shoulder_pan": 25, "shoulder_lift": -15, "elbow_flex": 35, "wrist_flex": 40, "wrist_roll": 20},
}
RENDER_VIEWS = {"zero": "side,front34", "ready": "front34,back34"}


def find_freecadcmd():
    candidates = [os.environ.get("FREECADCMD"), shutil.which("freecadcmd"), shutil.which("FreeCADCmd"),
                  "/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd"]
    for pattern in (r"C:\Program Files\FreeCAD*\bin\freecadcmd.exe", r"C:\Program Files\FreeCAD*\bin\FreeCADCmd.exe",
                    os.path.expandvars(r"%LOCALAPPDATA%\Programs\FreeCAD*\bin\freecadcmd.exe")):
        candidates += sorted(glob.glob(pattern), reverse=True)
    for c in candidates:
        if c and os.path.exists(c):
            return c
    sys.exit("freecadcmd not found: install FreeCAD 1.1 or set FREECADCMD to its path")


def find_freecad_gui(fc):
    """The GUI binary sits next to freecadcmd in every FreeCAD install."""
    folder = os.path.dirname(fc)
    for name in ("freecad", "FreeCAD", "freecad.exe", "FreeCAD.exe"):
        p = os.path.join(folder, name)
        if os.path.exists(p):
            return p
    return None


def run(cmd, env=None):
    print("$", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=HERE, env=env)
    if r.returncode:
        sys.exit(r.returncode)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--poses", help="JSON {name: {joint: deg}}; 'zero' is the q = 0 export in out/")
    ap.add_argument("--check", action="store_true", help="run the FK and collision checks")
    ap.add_argument("--no-build", action="store_true")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--open", action="store_true", help="open the result in the FreeCAD GUI (colours, visible)")
    ap.add_argument("--motion", action="store_true", help="open the motion test scene in the FreeCAD GUI and play the task")
    a = ap.parse_args()
    poses = json.loads(a.poses) if a.poses else DEFAULT_POSES
    fc = find_freecadcmd()
    if not a.no_build:
        env = dict(os.environ, SHELL_POSES=json.dumps({k: v for k, v in poses.items() if k != "zero"}))
        run([fc, "build_shell_v1.py"], env)
    if a.check:
        run([fc, "check_shell_v1.py"])
    if a.open:
        gui = find_freecad_gui(os.path.realpath(fc))
        if gui:
            print("$", gui, "open_shell_v1.FCMacro", flush=True)
            subprocess.Popen([gui, os.path.join(HERE, "open_shell_v1.FCMacro")], cwd=HERE)
        else:
            print("FreeCAD GUI not found next to", fc, "- open shell_v1.FCStd and run open_shell_v1.FCMacro")
    if a.motion:
        gui = find_freecad_gui(os.path.realpath(fc))
        if not gui:
            sys.exit("FreeCAD GUI not found next to %s" % fc)
        subprocess.Popen([gui, os.path.join(HERE, "open_motion_scene.FCMacro")], cwd=HERE)
    if not a.no_render:
        uv = shutil.which("uv")
        if not uv:
            print("uv not found: skipping renders (install uv or run render_shell_v1.py in a venv)")
            return
        os.makedirs(os.path.join(HERE, "renders"), exist_ok=True)
        for name in poses:
            src = "out" if name == "zero" else os.path.join("out", name)
            run([uv, "run", "--quiet", "render_shell_v1.py", src, "renders",
                 RENDER_VIEWS.get(name, "front34"), "--prefix", name + "_"])


if __name__ == "__main__":
    main()
