"""Compare SolidCraft measurements with the FreeCAD reference under the pre-registered criteria.

Run: python cad/solidcraft_bench/compare.py <ref.json> <sc.json> <out.md> [--hypothesis H1|H2|H2v2]
Only keys present in <sc.json> are compared. The tolerances below are frozen by the
pre-registered plan (input/ideas/solidcraft-accuracy-bench-plan.md); do not tune them.
--bbox boundbox (default, plan v1) checks the bbox against FreeCAD's BoundBox; --bbox optimal (plan v2,
amendment of 2026-11-04) checks it against bbox_optimal, the tight optimalBoundingBox(). The offset from
the other box is reported as an exploratory column that never decides a pass.
--notes FILE puts a hand-written section under the verdict, so re-running keeps it.
--exploratory labels the verdict line, for a rule chosen after the data were seen.
--keys a,b,... compares only those keys of <sc.json> (the held-out parts of plan v2).
"""
import argparse
import json
import math

VOL_TOL = 0.002      # |V_sc - V_fc| / V_fc
AREA_TOL = 0.002     # |A_sc - A_fc| / A_fc
BBOX_MM = 0.05       # every one of the 6 bbox bounds
COM_FRAC = 0.002     # |COM_sc - COM_fc| / FreeCAD bbox diagonal
H1_PASS_SHARE = 0.95


def _rel(ref, sc):
    if sc is None or not ref:
        return None
    return abs(sc - ref) / abs(ref)


def _bbox_offset(a, b):
    if not (a and b and a.get("min") and b.get("min")):
        return None
    return max(abs(x - y) for key in ("min", "max") for x, y in zip(a[key], b[key]))


def check_part(ref, sc, bbox="boundbox"):
    """Per-metric result for one part: {pass, opened, error?, checks: {name: {value, limit, pass}}}.

    bbox: "boundbox" (plan v1) or "optimal" (plan v2) picks the reference box the bbox check uses.
    """
    if bbox == "optimal" and not ref.get("bbox_optimal"):
        raise ValueError("--bbox optimal needs bbox_optimal in the FreeCAD reference")
    ref_box = ref["bbox_optimal"] if bbox == "optimal" else ref["bbox"]
    if "error" in sc:
        return {"pass": False, "opened": False, "error": sc["error"], "checks": {}}
    opened = ref.get("closed", False) and not sc.get("closed", False)
    vol = _rel(ref["volume_mm3"], sc.get("volume_mm3") if sc.get("closed") else None)
    area = _rel(ref["area_mm2"], sc.get("area_mm2"))
    box_off = _bbox_offset(ref_box, sc.get("bbox"))
    com = None
    if ref.get("center_of_mass") and sc.get("center_of_mass"):
        com = math.dist(ref["center_of_mass"], sc["center_of_mass"]) / ref["bbox_diag_mm"]
    checks = {
        "volume": {"value": vol, "limit": VOL_TOL},
        "area": {"value": area, "limit": AREA_TOL},
        "bbox": {"value": box_off, "limit": BBOX_MM},
        "com": {"value": com, "limit": COM_FRAC},
    }
    for c in checks.values():
        c["pass"] = c["value"] is not None and c["value"] <= c["limit"]
    return {"pass": all(c["pass"] for c in checks.values()), "opened": opened, "checks": checks,
            "bbox_optimal_mm": _bbox_offset(ref.get("bbox_optimal"), sc.get("bbox")),
            "bbox_boundbox_mm": _bbox_offset(ref["bbox"], sc.get("bbox"))}


def compare_all(ref, sc, bbox="boundbox"):
    return {name: check_part(ref[name], rec, bbox) for name, rec in sorted(sc.items())}


def verdict_h1(results):
    """H1: at least 95% of parts pass, and no part that is closed in FreeCAD opens in SolidCraft."""
    n = len(results)
    passed = sum(r["pass"] for r in results.values())
    opened = sorted(name for name, r in results.items() if r["opened"])
    share = passed / n if n else 0.0
    ok = share >= H1_PASS_SHARE and not opened
    return {"verdict": "confirmed" if ok else "refuted", "passed": passed, "total": n,
            "share": share, "opened": opened}


def verdict_h2(results):
    """H2: every rebuilt key (default and changed parameter) passes."""
    failed = sorted(name for name, r in results.items() if not r["pass"])
    return {"verdict": "confirmed" if not failed else "refuted", "passed": len(results) - len(failed),
            "total": len(results), "failed": failed}


def _fmt(c, pct):
    if c["value"] is None:
        return "—"
    text = "%.4f%%" % (c["value"] * 100) if pct else "%.4f mm" % c["value"]
    return text if c["pass"] else "**%s**" % text


def to_markdown(results, verdict, hypothesis, notes=None, bbox="boundbox", exploratory=False):
    lines = []
    if verdict:
        lines.append("# %s: %s%s" % (hypothesis, verdict["verdict"], " (exploratory)" if exploratory else ""))
        lines.append("")
        lines.append("ผ่าน %d/%d part (%.1f%%)" % (verdict["passed"], verdict["total"],
                                                   100.0 * verdict["passed"] / max(verdict["total"], 1)))
        if verdict.get("opened") is not None:
            lines.append("")
            lines.append("ปิดใน FreeCAD แต่เปิดใน SolidCraft: %s" % (", ".join(verdict["opened"]) or "ไม่มี"))
        if verdict.get("failed"):
            lines.append("")
            lines.append("ไม่ผ่าน: %s" % ", ".join(verdict["failed"]))
        lines.append("")
    if notes:
        lines.append(notes.rstrip("\n"))
        lines.append("")
    main_box, other_box, other_key = (("optimalBoundingBox", "BoundBox", "bbox_boundbox_mm") if bbox == "optimal"
                                      else ("BoundBox", "optimalBoundingBox", "bbox_optimal_mm"))
    lines.append("เกณฑ์: volume ≤ %.1f%%, area ≤ %.1f%%, bbox ≤ %.2f mm ทุกขอบ (เทียบ %s ของ FreeCAD), COM ≤ %.1f%% ของเส้นทแยง bbox; ตัวหนา = ไม่ผ่าน"
                 % (VOL_TOL * 100, AREA_TOL * 100, BBOX_MM, main_box, COM_FRAC * 100))
    lines.append("")
    lines.append("คอลัมน์ bbox (%s) = เทียบกับ %s ของ FreeCAD, exploratory ไม่ใช้ตัดสิน" % (other_box, other_box))
    lines.append("")
    lines.append("| part | ผล | volume | area | bbox | COM | bbox (%s) | หมายเหตุ |" % other_box)
    lines.append("|---|---|---|---|---|---|---|---|")
    for name, r in results.items():
        if "error" in r:
            lines.append("| %s | fail | — | — | — | — | — | error: %s |" % (name, r["error"].splitlines()[-1][:80]))
            continue
        c = r["checks"]
        note = "เปิดใน SolidCraft" if r["opened"] else ""
        opt = r.get(other_key)
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
            name, "pass" if r["pass"] else "**fail**", _fmt(c["volume"], True), _fmt(c["area"], True),
            _fmt(c["bbox"], False), _fmt(c["com"], True), "—" if opt is None else "%.4f mm" % opt, note))
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ref")
    ap.add_argument("sc")
    ap.add_argument("out")
    ap.add_argument("--hypothesis", choices=["H1", "H2", "H2v2"])
    ap.add_argument("--notes", help="markdown file placed under the verdict")
    ap.add_argument("--bbox", choices=["boundbox", "optimal"], default="boundbox",
                    help="reference box for the bbox check: boundbox (plan v1) or optimal (plan v2)")
    ap.add_argument("--keys", help="comma-separated keys of <sc.json> to compare (default: all)")
    ap.add_argument("--exploratory", action="store_true",
                    help="label the verdict exploratory (rule chosen after seeing these data)")
    a = ap.parse_args()
    with open(a.ref) as f:
        ref = json.load(f)
    with open(a.sc) as f:
        sc = json.load(f)
    if a.keys:
        wanted = a.keys.split(",")
        absent = sorted(set(wanted) - set(sc))
        if absent:
            raise SystemExit("not in %s: %s" % (a.sc, ", ".join(absent)))
        sc = {k: sc[k] for k in wanted}
    missing = sorted(set(sc) - set(ref))
    if missing:
        raise SystemExit("no FreeCAD reference for: %s" % ", ".join(missing))
    results = compare_all(ref, sc, a.bbox)
    verdict = {"H1": verdict_h1, "H2": verdict_h2, "H2v2": verdict_h2}[a.hypothesis](results) if a.hypothesis else None
    notes = None
    if a.notes:
        with open(a.notes, encoding="utf-8") as f:
            notes = f.read()
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(to_markdown(results, verdict, a.hypothesis, notes, a.bbox, a.exploratory))
    if verdict:
        print(json.dumps(verdict, ensure_ascii=False))
    print("->", a.out)


if __name__ == "__main__":
    main()
