"""Shared helpers for the FreeCAD side of the bench (run under freecadcmd).

Importing this puts cad/shell_v1 on sys.path and drops cached copies of the shell modules,
so every script builds from the files on disk.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHELL = os.path.normpath(os.path.join(HERE, "..", "shell_v1"))
REF = os.path.join(HERE, "results", "freecad_ref.json")
STEP_DIR = os.path.join(HERE, "out", "step")
sys.path.insert(0, SHELL)
for _name in ("shell_v1_model", "base_v1", "links_v1", "wrist_gripper_v1", "arm_spec"):
    sys.modules.pop(_name, None)


def measure(shape):
    """Volume, area, bbox, COM and closure of one shape; a compound's COM is volume-weighted over its solids."""
    solids = shape.Solids
    vol = sum(s.Volume for s in solids)
    if solids and vol > 0:
        com = [sum(s.Volume * s.CenterOfMass[i] for s in solids) / vol for i in range(3)]
    else:
        com = None
    bb = shape.BoundBox
    # BoundBox can be loose on curved faces (several mm on upper_link and wrist); the pre-registered check
    # uses it, the tight box is kept beside it for the exploratory column of compare.py
    ob = shape.optimalBoundingBox(True, False)
    return {
        "volume_mm3": vol,
        "area_mm2": shape.Area,
        "bbox": {"min": [bb.XMin, bb.YMin, bb.ZMin], "max": [bb.XMax, bb.YMax, bb.ZMax]},
        "bbox_optimal": {"min": [ob.XMin, ob.YMin, ob.ZMin], "max": [ob.XMax, ob.YMax, ob.ZMax]},
        "bbox_diag_mm": math.dist([bb.XMin, bb.YMin, bb.ZMin], [bb.XMax, bb.YMax, bb.ZMax]),
        "center_of_mass": com,
        "closed": bool(shape.Shells) and all(sh.isClosed() for sh in shape.Shells),
        "valid": shape.isValid(),
        "solids": len(solids),
        "shells": len(shape.Shells),
        "faces": len(shape.Faces),
    }


def load_ref():
    if os.path.exists(REF):
        with open(REF) as f:
            return json.load(f)
    return {}


def save_ref(ref):
    os.makedirs(os.path.dirname(REF), exist_ok=True)
    with open(REF, "w") as f:
        json.dump(ref, f, indent=1, sort_keys=True)
