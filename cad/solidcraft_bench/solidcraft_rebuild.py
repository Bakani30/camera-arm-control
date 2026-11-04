"""SolidCraft side of the rebuild bench: run each rebuild/<part>.json with solidcraft-cli and measure it.

Run (plain Python): python cad/solidcraft_bench/solidcraft_rebuild.py [part ...]
Writes results/solidcraft_rebuild.json (keys as in freecad_ref.json). Each part runs twice: as
scripted, and with one parameter changed by a parameters.change step appended to the script,
the same change freecad_rebuild_ref.py makes. Parts not named keep their earlier results.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from solidcraft_import import merge  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "solidcraft_rebuild.json")

# script -> [(result key, None or (parameter, new expression))]
CASES = {
    "turntable": [("turntable", None), ("turntable@tt_r=+5", ("tt_r", "75 mm"))],
    "servo_clamp_shoulder": [("servo_clamp_shoulder_local", None),
                             ("servo_clamp_shoulder_local@L=+2", ("L", "47.2 mm"))],
    "forearm_core_front": [("forearm_core_front", None),
                           ("forearm_core_front@tube_r=+2", ("tube_r", "20.5 mm"))],
    # held-out parts of plan v2
    "gripper_pad_up": [("gripper_pad_up_local", None), ("gripper_pad_up_local@top=+2", ("top", "30.5 mm"))],
    "gripper_gear_crank_up": [("gripper_gear_crank_up_local", None),
                              ("gripper_gear_crank_up_local@link=+2", ("link", "42 mm"))],
    "base_tray": [("base_tray_local", None), ("base_tray_local@r=+2", ("r", "77 mm"))],
}


def run_case(cli, script, change, tmp):
    with open(os.path.join(HERE, "rebuild", script + ".json")) as f:
        commands = json.load(f)["commands"]
    if change:
        commands = commands + [{"command": "parameters.change",
                                "params": {"name": change[0], "expression": change[1]}}]
    src = os.path.join(tmp, "script.json")
    out = os.path.join(tmp, "eval.json")
    with open(src, "w") as f:
        json.dump({"commands": commands}, f)
    t0 = time.monotonic()
    proc = subprocess.run([cli, "eval", src, "--json-out", out], capture_output=True, text=True)
    seconds = time.monotonic() - t0
    if proc.returncode != 0:
        return {"error": (proc.stderr or proc.stdout).strip()[-2000:], "seconds": seconds}
    with open(out, encoding="utf-8") as f:
        data = json.load(f)
    rec = merge(data["bodies"])
    rec["timeline_errors"] = [t for t in data.get("timeline", []) if t.get("error") or t.get("warning")]
    rec["seconds"] = seconds
    return rec


def main():
    cli = shutil.which("solidcraft-cli")
    if not cli:
        sys.exit("solidcraft-cli not on PATH")
    version = subprocess.run([cli, "--version"], capture_output=True, text=True).stdout.strip()
    names = sys.argv[1:] or sorted(CASES)
    result = {}
    if os.path.exists(OUT):
        with open(OUT) as f:
            result = json.load(f)
    with tempfile.TemporaryDirectory() as tmp:
        for script in names:
            for key, change in CASES[script]:
                rec = run_case(cli, script, change, tmp)
                rec["source"] = "%s eval rebuild/%s.json%s" % (
                    version, script, " + parameters.change %s = %s" % change if change else "")
                result[key] = rec
                if "error" in rec:
                    print("%-34s ERROR %s" % (key, rec["error"].splitlines()[-1] if rec["error"] else ""))
                else:
                    print("%-34s vol %10.2f mm3  faces %3d  closed %s  timeline issues %d  %.1f s"
                          % (key, rec["volume_mm3"], rec["faces"], rec["closed"], len(rec["timeline_errors"]),
                             rec["seconds"]))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(result, f, indent=1, sort_keys=True)
    print("->", OUT)


if __name__ == "__main__":
    main()
