"""Entry point for freecadcmd / the FreeCAD GUI: builds shell v1 (see shell_v1_model.py)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# a long-running FreeCAD GUI keeps old copies of these modules; always build from the files on disk
for _name in ("shell_v1_model", "base_v1", "links_v1", "wrist_gripper_v1", "arm_spec"):
    sys.modules.pop(_name, None)
import shell_v1_model  # noqa: E402

shell_v1_model.main()
