"""FreeCAD reference for the SolidCraft bench: measure every shell_v1 part and export one STEP per part.

Run: freecadcmd cad/solidcraft_bench/freecad_measure.py
Writes results/freecad_ref.json and out/step/<part>.step (out/ is not in git).
Builds the parts with shell_v1_model.build_all(), the same call build_shell_v1.py makes,
so nothing is read back from shell_v1.FCStd.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fc_common as C  # noqa: E402
import shell_v1_model  # noqa: E402


def main():
    os.makedirs(C.STEP_DIR, exist_ok=True)
    parts, _ = shell_v1_model.build_all()
    ref = C.load_ref()
    for name, (shape, _color) in parts.items():
        m = C.measure(shape)
        m["source"] = "shell_v1_model.build_all()"
        ref[name] = m
        shape.exportStep(os.path.join(C.STEP_DIR, name + ".step"))
        print("%-26s vol %10.1f mm3  solids %d  closed %s" % (name, m["volume_mm3"], m["solids"], m["closed"]))
    C.save_ref(ref)
    print("parts", len(parts), "->", C.REF)


main()
