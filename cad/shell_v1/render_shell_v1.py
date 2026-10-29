# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "numpy-stl", "matplotlib"]
# ///
"""Quick shaded render of the shell STL export (painter's algorithm, no FreeCAD GUI needed).

    uv run render_shell_v1.py out/ready renders front34,back34 --prefix ready_

Views: iso, side, front, top, back34, front34. Painter's sorting can show small artefacts where
faces cross; use the FreeCAD GUI for an exact view.
"""
import argparse
import json
import os

import matplotlib
import numpy as np
from stl import mesh

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402

VIEWS = {"iso": (35, -60), "side": (0, -90), "front": (0, 0), "top": (90, -90),
         "back34": (25, 130), "front34": (22, 55)}


def load(src):
    colors = json.load(open(os.path.join(src, "colors.json")))
    tris, cols = [], []
    for name, c in colors.items():
        p = os.path.join(src, name + ".stl")
        if os.path.exists(p):
            m = mesh.Mesh.from_file(p)
            tris.append(m.vectors)
            cols.append(np.tile(np.array(c), (len(m.vectors), 1)))
    return np.concatenate(tris), np.concatenate(cols)


def render(T, C, view, path):
    el, az = np.radians(VIEWS[view][0]), np.radians(VIEWS[view][1])
    fwd = -np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
    right = np.cross(fwd, [0, 0, 1])
    if np.linalg.norm(right) < 1e-6:
        right = np.array([1.0, 0, 0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    P = np.stack([T @ right, T @ up], -1)
    depth = (T @ fwd).mean(1)
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    nn = np.linalg.norm(n, axis=1)
    nn[nn == 0] = 1
    n /= nn[:, None]
    light = np.array([0.4, -0.6, 0.7])
    light /= np.linalg.norm(light)
    shade = 0.35 + 0.65 * np.clip(np.abs(n @ light), 0, 1)
    order = np.argsort(-depth)
    fig, ax = plt.subplots(figsize=(8, 8), dpi=110)
    ax.add_collection(PolyCollection(P[order], facecolors=np.clip(C[order] * shade[order, None], 0, 1),
                                     edgecolors="none"))
    ax.set_xlim(P[..., 0].min() - 10, P[..., 0].max() + 10)
    ax.set_ylim(P[..., 1].min() - 10, P[..., 1].max() + 10)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("#1d1f24")
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print("wrote", path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("views", nargs="?", default="iso")
    ap.add_argument("--prefix", default="")
    a = ap.parse_args()
    T, C = load(a.src)
    os.makedirs(a.out, exist_ok=True)
    for v in a.views.split(","):
        render(T, C, v, os.path.join(a.out, a.prefix + v + ".png"))


if __name__ == "__main__":
    main()
