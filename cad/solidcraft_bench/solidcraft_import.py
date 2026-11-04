"""SolidCraft side of the import bench: measure every out/step/<part>.step with solidcraft-cli.

Run (plain Python, after freecad_measure.py): python cad/solidcraft_bench/solidcraft_import.py
Writes results/solidcraft_import.json in the same shape as freecad_ref.json.
A part that comes in as several bodies is merged: volume and area summed, bbox as the union,
COM volume-weighted, closed only if every body is closed.
"""
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
STEP_DIR = os.path.join(HERE, "out", "step")
OUT = os.path.join(HERE, "results", "solidcraft_import.json")


def merge(bodies):
    """One record from the bodies solidcraft-cli eval reports for a file."""
    closed = [b for b in bodies if b.get("closed")]
    vol = sum(b.get("volume_mm3") or 0.0 for b in closed)
    if closed and vol > 0:
        com = [sum((b.get("volume_mm3") or 0.0) * b["center_of_mass"][i] for b in closed) / vol for i in range(3)]
    else:
        com = None
    lo = [min(b["bbox"]["min"][i] for b in bodies) for i in range(3)] if bodies else None
    hi = [max(b["bbox"]["max"][i] for b in bodies) for i in range(3)] if bodies else None
    return {
        "volume_mm3": vol,
        "area_mm2": sum(b.get("area_mm2") or 0.0 for b in bodies),
        "bbox": {"min": lo, "max": hi},
        "bbox_diag_mm": math.dist(lo, hi) if bodies else None,
        "center_of_mass": com,
        "closed": bool(bodies) and len(closed) == len(bodies),
        "bodies": len(bodies),
        "faces": sum(b.get("faces") or 0 for b in bodies),
        "body_names": [b.get("name") for b in bodies],
    }


def eval_step(cli, path, tmp):
    out = os.path.join(tmp, "eval.json")
    t0 = time.monotonic()
    proc = subprocess.run([cli, "eval", path, "--json-out", out], capture_output=True, text=True)
    seconds = time.monotonic() - t0
    if proc.returncode != 0:
        return {"error": (proc.stderr or proc.stdout).strip()[-2000:], "seconds": seconds}
    with open(out, encoding="utf-8") as f:
        rec = merge(json.load(f)["bodies"])
    rec["seconds"] = seconds
    return rec


def main():
    cli = shutil.which("solidcraft-cli")
    if not cli:
        sys.exit("solidcraft-cli not on PATH")
    version = subprocess.run([cli, "--version"], capture_output=True, text=True).stdout.strip()
    files = sorted(f for f in os.listdir(STEP_DIR) if f.endswith(".step"))
    result = {}
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory() as tmp:
        for f in files:
            name = f[:-len(".step")]
            rec = eval_step(cli, os.path.join(STEP_DIR, f), tmp)
            rec["source"] = "%s eval out/step/%s" % (version, f)
            result[name] = rec
            if "error" in rec:
                print("%-26s ERROR %s" % (name, rec["error"].splitlines()[-1] if rec["error"] else ""))
            else:
                print("%-26s vol %10.1f mm3  bodies %d  closed %s  %.1f s"
                      % (name, rec["volume_mm3"], rec["bodies"], rec["closed"], rec["seconds"]))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(result, f, indent=1, sort_keys=True)
    print("parts %d in %.0f s -> %s" % (len(result), time.monotonic() - t0, OUT))


if __name__ == "__main__":
    main()
