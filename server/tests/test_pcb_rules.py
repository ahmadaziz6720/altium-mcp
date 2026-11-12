"""Unit tests for pcb_rules (pure Python, no Altium needed).

Run from server/:  python -m unittest tests.test_pcb_rules -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from pcb_rules import RULE_KINDS, compact_rule, encode_values  # noqa: E402


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
