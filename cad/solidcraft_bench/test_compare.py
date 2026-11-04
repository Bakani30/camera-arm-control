"""Tests for compare.py: the four pre-registered checks and the H1 verdict.

Run: python -m unittest cad/solidcraft_bench/test_compare.py
"""
import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare  # noqa: E402


def box(lx=40.0, ly=30.0, lz=20.0):
    """Measurement record of an axis-aligned box from the origin."""
    return {
        "volume_mm3": lx * ly * lz,
        "area_mm2": 2 * (lx * ly + ly * lz + lx * lz),
        "bbox": {"min": [0.0, 0.0, 0.0], "max": [lx, ly, lz]},
        "bbox_diag_mm": (lx ** 2 + ly ** 2 + lz ** 2) ** 0.5,
        "center_of_mass": [lx / 2, ly / 2, lz / 2],
        "closed": True,
    }


class CheckPart(unittest.TestCase):
    def test_identical_box_passes(self):
        r = compare.check_part(box(), box())
        self.assertTrue(r["pass"])
        self.assertEqual(set(r["checks"]), {"volume", "area", "bbox", "com"})

    def test_volume_just_over_tolerance_fails(self):
        sc = box()
        sc["volume_mm3"] *= 1 + compare.VOL_TOL * 1.01
        r = compare.check_part(box(), sc)
        self.assertFalse(r["checks"]["volume"]["pass"])
        self.assertTrue(r["checks"]["area"]["pass"])
        self.assertFalse(r["pass"])

    def test_volume_within_tolerance_passes(self):
        sc = box()
        sc["volume_mm3"] *= 1 + compare.VOL_TOL * 0.99
        self.assertTrue(compare.check_part(box(), sc)["checks"]["volume"]["pass"])

    def test_bbox_edge_over_005_mm_fails(self):
        sc = copy.deepcopy(box())
        sc["bbox"]["max"][2] += 0.06
        r = compare.check_part(box(), sc)
        self.assertFalse(r["checks"]["bbox"]["pass"])
        self.assertAlmostEqual(r["checks"]["bbox"]["value"], 0.06)

    def test_com_offset_over_fraction_of_diagonal_fails(self):
        sc = copy.deepcopy(box())
        diag = box()["bbox_diag_mm"]
        sc["center_of_mass"][0] += compare.COM_FRAC * diag * 1.5
        self.assertFalse(compare.check_part(box(), sc)["checks"]["com"]["pass"])

    def test_open_body_fails_every_volume_check(self):
        sc = box()
        sc.update(closed=False, volume_mm3=0.0, center_of_mass=None)
        r = compare.check_part(box(), sc)
        self.assertFalse(r["pass"])
        self.assertFalse(r["checks"]["volume"]["pass"])
        self.assertFalse(r["checks"]["com"]["pass"])
        self.assertTrue(r["opened"])

    def test_optimal_bbox_offset_is_reported_but_does_not_decide(self):
        ref = box()
        ref["bbox"] = {"min": [-5.0, 0.0, 0.0], "max": [40.0, 30.0, 20.0]}   # loose box
        ref["bbox_optimal"] = box()["bbox"]
        r = compare.check_part(ref, box())
        self.assertFalse(r["checks"]["bbox"]["pass"])
        self.assertAlmostEqual(r["bbox_optimal_mm"], 0.0)
        self.assertFalse(r["pass"])

    def test_v2_optimal_bbox_decides(self):
        ref = box()
        ref["bbox"] = {"min": [-5.0, 0.0, 0.0], "max": [40.0, 30.0, 20.0]}   # loose box
        ref["bbox_optimal"] = box()["bbox"]
        r = compare.check_part(ref, box(), bbox="optimal")
        self.assertTrue(r["checks"]["bbox"]["pass"])
        self.assertAlmostEqual(r["checks"]["bbox"]["value"], 0.0)
        self.assertAlmostEqual(r["bbox_boundbox_mm"], 5.0)
        self.assertTrue(r["pass"])

    def test_v2_optimal_bbox_edge_over_005_mm_fails(self):
        ref = box()
        ref["bbox_optimal"] = copy.deepcopy(box()["bbox"])
        ref["bbox_optimal"]["min"][0] -= 0.06
        self.assertFalse(compare.check_part(ref, box(), bbox="optimal")["checks"]["bbox"]["pass"])

    def test_v2_without_optimal_bbox_in_ref_is_an_error(self):
        with self.assertRaises(ValueError):
            compare.check_part(box(), box(), bbox="optimal")

    def test_import_error_fails(self):
        r = compare.check_part(box(), {"error": "boom"})
        self.assertFalse(r["pass"])
        self.assertEqual(r["error"], "boom")


class VerdictH1(unittest.TestCase):
    def results(self, n_pass, n_fail, opened=0):
        out = {}
        for k in range(n_pass):
            out["p%d" % k] = {"pass": True, "opened": False}
        for k in range(n_fail):
            out["f%d" % k] = {"pass": False, "opened": k < opened}
        return out

    def test_95_percent_without_opened_confirms(self):
        self.assertEqual(compare.verdict_h1(self.results(19, 1))["verdict"], "confirmed")

    def test_below_95_percent_refutes(self):
        self.assertEqual(compare.verdict_h1(self.results(18, 2))["verdict"], "refuted")

    def test_one_opened_body_refutes_even_at_high_pass_rate(self):
        v = compare.verdict_h1(self.results(99, 1, opened=1))
        self.assertEqual(v["verdict"], "refuted")
        self.assertEqual(v["opened"], ["f0"])



class Markdown(unittest.TestCase):
    def test_exploratory_label_on_verdict_line(self):
        results = {"a": compare.check_part(box(), box())}
        verdict = compare.verdict_h2(results)
        text = compare.to_markdown(results, verdict, "H2", exploratory=True)
        self.assertEqual(text.splitlines()[0], "# H2: confirmed (exploratory)")
        self.assertEqual(compare.to_markdown(results, verdict, "H2").splitlines()[0], "# H2: confirmed")

if __name__ == "__main__":
    unittest.main()
