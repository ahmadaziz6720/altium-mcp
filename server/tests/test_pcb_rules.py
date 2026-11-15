"""Unit tests for pcb_rules (pure Python, no Altium needed).

Run from server/:  python -m unittest tests.test_pcb_rules -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from pcb_rules import (BINARY_KINDS, RULE_KINDS, SHORT_DESCRIPTORS, compact_rule, compare_values,  # noqa: E402
                       decode_values, encode_values)


class EncodeTest(unittest.TestCase):
    def test_mils_become_internal_units(self):
        self.assertEqual(encode_values("clearance", {"gap_mils": 8}), ("gap=80000", ""))
        self.assertEqual(encode_values("clearance", {"gap_mils": 7.874}), ("gap=78740", ""))

    def test_width_needs_all_three_and_min_not_above_max(self):
        self.assertEqual(encode_values("width", {"min_mils": 6, "max_mils": 40, "preferred_mils": 10}),
                         ("min=60000;max=400000;preferred=100000", ""))
        self.assertIn("needs", encode_values("width", {"min_mils": 6})[1])
        self.assertIn("larger", encode_values("width", {"min_mils": 50, "max_mils": 40, "preferred_mils": 45})[1])

    def test_mask_expansion_may_be_negative_gap_may_not(self):
        self.assertEqual(encode_values("solder_mask_expansion", {"expansion_mils": -2}), ("expansion=-20000", ""))
        self.assertIn("negative", encode_values("clearance", {"gap_mils": -1})[1])

    def test_polygon_connect(self):
        self.assertEqual(encode_values("polygon_connect", {"connect_style": "Relief", "entries": 2,
                                                           "air_gap_mils": 12}),
                         ("connect_style=relief;air_gap=120000;entries=2", ""))
        self.assertEqual(encode_values("polygon_connect", {"connect_style": "direct"}),
                         ("connect_style=direct", ""))
        self.assertIn("one of", encode_values("polygon_connect", {"connect_style": "thermal"})[1])
        self.assertIn("2 or 4", encode_values("polygon_connect", {"connect_style": "relief",
                                                                  "entries": 2.5})[1])
        self.assertIn("2 or 4", encode_values("polygon_connect", {"connect_style": "relief", "entries": 3})[1])

    def test_preferred_between_min_and_max(self):
        self.assertIn("between", encode_values("width", {"min_mils": 6, "max_mils": 10, "preferred_mils": 20})[1])
        self.assertIn("between", encode_values("width", {"min_mils": 6, "max_mils": 10, "preferred_mils": 5})[1])

    def test_via_holes_inside_their_range_and_smaller_than_the_via(self):
        via = {"min_diameter_mils": 18, "max_diameter_mils": 40, "preferred_diameter_mils": 20,
               "min_hole_mils": 8, "max_hole_mils": 20, "preferred_hole_mils": 10}
        self.assertEqual(encode_values("routing_via", via)[1], "")
        self.assertIn("between", encode_values("routing_via", dict(via, preferred_hole_mils=25))[1])
        self.assertIn("smaller than preferred_diameter",
                      encode_values("routing_via", dict(via, preferred_hole_mils=20))[1])

    def test_unknown_kind_and_key(self):
        self.assertIn("unknown rule_type", encode_values("fanout", {})[1])
        self.assertIn("not gap", encode_values("clearance", {"gap": 8})[1])
        self.assertIn("must be a number", encode_values("clearance", {"gap_mils": "eight"})[1])

    def test_every_kind_has_values(self):
        for kind, spec in RULE_KINDS.items():
            self.assertTrue(spec, kind)



class NewKindsTest(unittest.TestCase):
    """The kinds added for A14: their values, checks and Altium's read-back."""

    def test_differential_pair(self):
        dp = {"min_gap_mils": 5, "max_gap_mils": 9, "preferred_gap_mils": 7, "min_width_mils": 4,
              "max_width_mils": 8, "preferred_width_mils": 6}
        self.assertEqual(encode_values("differential_pair", dp),
                         ("min_gap=50000;max_gap=90000;preferred_gap=70000;min_width=40000;max_width=80000;"
                          "preferred_width=60000", ""))
        self.assertTrue(encode_values("differential_pair", dict(dp, max_uncoupled_length_mils=500))[0]
                        .endswith(";max_uncoupled_length=5000000"))
        self.assertIn("needs min_width_mils", encode_values("differential_pair", {
            k: v for k, v in dp.items() if k != "min_width_mils"})[1])
        self.assertIn("min_gap_mils is larger", encode_values("differential_pair", dict(dp, min_gap_mils=10))[1])
        self.assertIn("preferred_width_mils must be between",
                      encode_values("differential_pair", dict(dp, preferred_width_mils=9))[1])

    def test_length_and_matched_length(self):
        self.assertEqual(encode_values("length", {"min_mils": 100, "max_mils": 2000}),
                         ("min=1000000;max=20000000", ""))
        self.assertIn("larger", encode_values("length", {"min_mils": 3000, "max_mils": 2000})[1])
        self.assertEqual(encode_values("matched_length", {"tolerance_mils": 25}), ("tolerance=250000", ""))
        self.assertIn("negative", encode_values("matched_length", {"tolerance_mils": -1})[1])

    def test_routing_layers(self):
        self.assertEqual(encode_values("routing_layers", {"layers": ["Top Layer", " Bottom Layer"]}),
                         ("layers=Top Layer,Bottom Layer", ""))
        for bad, words in (("Top Layer", "a list"), ([], "a list"), ([""], "non-empty"), (["A,B"], "holds one of"),
                           (["A;B"], "holds one of"), (["Top", "top"], "named twice"), ([3], "non-empty")):
            self.assertIn(words, encode_values("routing_layers", {"layers": bad})[1], bad)

    def test_plane_connect(self):
        self.assertEqual(encode_values("plane_connect", {"connect_style": "Relief", "expansion_mils": 15,
                                                         "conductor_width_mils": 12, "air_gap_mils": 11,
                                                         "entries": 2}),
                         ("connect_style=relief;expansion=150000;conductor_width=120000;air_gap=110000;entries=2",
                          ""))
        self.assertEqual(encode_values("plane_connect", {"connect_style": "none"}), ("connect_style=none", ""))
        self.assertIn("negative", encode_values("plane_connect", {"connect_style": "direct",
                                                                  "expansion_mils": -1})[1])
        self.assertIn("2 or 4", encode_values("plane_connect", {"connect_style": "relief", "entries": 3})[1])

    def test_one_gap_kinds(self):
        for kind, key in (("component_clearance", "gap_mils"), ("silk_to_solder_mask", "gap_mils"),
                          ("silk_to_silk", "gap_mils"), ("hole_to_hole", "gap_mils"),
                          ("solder_mask_sliver", "gap_mils"), ("annular_ring", "min_mils")):
            text, error = encode_values(kind, {key: 8})
            self.assertEqual(error, "", kind)
            self.assertTrue(text.endswith("=80000"), kind)
            self.assertIn("negative", encode_values(kind, {key: -0.1})[1], kind)
            self.assertIn("needs", encode_values(kind, {})[1], kind)
        self.assertEqual(encode_values("component_clearance", {"gap_mils": 20, "vertical_gap_mils": 30}),
                         ("gap=200000;vertical_gap=300000", ""))

    def test_not_a_number_or_a_unit_mistake(self):
        for v in (True, float("nan"), float("inf"), None, "x"):
            self.assertIn("must be a number", encode_values("hole_to_hole", {"gap_mils": v})[1], v)
        self.assertIn("unit mistake", encode_values("length", {"min_mils": 0, "max_mils": 2e6})[1])
        self.assertIn("is an object", encode_values("clearance", [8])[1])

    def test_every_kind_has_a_short_descriptor(self):
        self.assertEqual(set(SHORT_DESCRIPTORS), set(RULE_KINDS))
        self.assertTrue(BINARY_KINDS <= set(RULE_KINDS))


class ReadBackTest(unittest.TestCase):
    def test_decode_in_the_callers_keys(self):
        self.assertEqual(decode_values("differential_pair", "min_gap=50000;max_uncoupled_length=5000000"),
                         {"min_gap_mils": 5, "max_uncoupled_length_mils": 500})
        self.assertEqual(decode_values("clearance", "gap=39370"), {"gap_mils": 3.937})
        self.assertEqual(decode_values("routing_layers", "layers=Top Layer"), {"layers": ["Top Layer"]})
        self.assertEqual(decode_values("routing_layers", "layers="), {"layers": []})
        self.assertEqual(decode_values("plane_connect", "connect_style=direct;entries=4"),
                         {"connect_style": "direct", "entries": 4})

    def test_compare(self):
        self.assertEqual(compare_values("clearance", "gap=80000", "gap=80000"), [])
        self.assertEqual(compare_values("clearance", "gap=80000", "gap=100000"),
                         ["gap_mils: sent 8, Altium has 10"])
        self.assertEqual(compare_values("routing_layers", "layers=top layer", "layers=Top Layer"), [])
        self.assertEqual(compare_values("routing_layers", "layers=Top Layer", "layers=Top Layer,Bottom Layer"),
                         ["layers: sent ['Top Layer'], Altium has ['Top Layer', 'Bottom Layer']"])
        self.assertEqual(compare_values("plane_connect", "connect_style=relief", "connect_style=relief;entries=4"),
                         [])
        self.assertEqual(compare_values("hole_to_hole", "gap=1", ""), ["gap_mils: not read back"])
        self.assertIn("per-layer", compare_values("width", "min=1", "min=1;layers_differ=width")[0])


def _rule(descriptor, f1="All", f2="All", unary=False):
    return {"name": "R", "enabled": True, "priority": 1, "descriptor": descriptor, "rule_kind": "K",
            "filter1": f1, "filter2": f2, "unary": unary}


class CompactRuleTest(unittest.TestCase):
    """Descriptors as Altium Designer 25 gives them for its default rules."""

    def test_binary_rule_keeps_both_filters_and_drops_the_scope(self):
        out = compact_rule(_rule("Silk To Solder Mask (Clearance=10mil) (IsPad),(All)", "IsPad"))
        self.assertEqual(out["constraint"], "Silk To Solder Mask (Clearance=10mil)")
        self.assertEqual((out["filter1"], out["filter2"]), ("IsPad", "All"))
        self.assertNotIn("descriptor", out)
        self.assertNotIn("unary", out)

    def test_unary_rule_has_no_filter2(self):
        out = compact_rule(_rule("Width Constraint (Min=10mil) (Max=10mil) (Preferred=10mil) (All)", unary=True))
        self.assertEqual(out["constraint"], "Width Constraint (Min=10mil) (Max=10mil) (Preferred=10mil)")
        self.assertNotIn("filter2", out)

    def test_other_scope_forms(self):
        cases = [("Fanout Control Rule ( ((CompPinCount < 5)) )", "(CompPinCount < 5)", "Fanout Control Rule"),
                 ("Routing Layers(All)", "All", "Routing Layers"),
                 ("Un-Routed Net Constraint ( (All) )", "All", "Un-Routed Net Constraint"),
                 ("Component Clearance Constraint ( Horizontal Gap = 10mil, Vertical Gap = 10mil ) (All),(All) ",
                  "All", "Component Clearance Constraint ( Horizontal Gap = 10mil, Vertical Gap = 10mil )"),
                 ("Polygon Connect Rule(Relief Connect )(Conductor Width=10mil) (Entries=4) (All),(All)", "All",
                  "Polygon Connect Rule(Relief Connect )(Conductor Width=10mil) (Entries=4)")]
        for descriptor, f1, want in cases:
            self.assertEqual(compact_rule(_rule(descriptor, f1))["constraint"], want, descriptor)

    def test_descriptor_without_the_scope_is_kept_whole(self):
        for d in ("Silk primitive without silk layer", "Modified Polygon (Allow modified: No), (Allow shelved: No)",
                  "Clearance Constraint (Gap=10mil) (InNet('A')),(All)"):
            self.assertEqual(compact_rule(_rule(d))["constraint"], d)

    def test_rule_order_and_other_fields_kept(self):
        out = compact_rule(_rule("Clearance Constraint (Gap=10mil) (All),(All)"))
        self.assertEqual(list(out), ["name", "enabled", "priority", "rule_kind", "filter1", "constraint", "filter2"])


if __name__ == "__main__":
    unittest.main()
