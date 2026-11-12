"""Live test of get_pcb_rules in a running Altium Designer (A7): each rule's
scope is given once, in filter1 (and filter2 for a binary rule), and the
constraint without it.

See tests/live_altium.py for how to run it. It reads the rules of a new
board, Altium's defaults.
"""
import unittest

from tests.live_altium import LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close, new_board, tool

if LIVE:
    import main


@unittest.skipUnless(LIVE, SKIP_REASON)
class LivePcbRulesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        check_scripts_are_this_checkouts()

    def test_new_board_rules(self):
        name = new_board()
        try:
            rules = tool(main.get_pcb_rules(None))
        finally:
            close(name)
        self.assertIsInstance(rules, list)
        by_name = {r["name"]: r for r in rules}
        for r in rules:
            self.assertNotIn("descriptor", r)
            self.assertNotIn("unary", r)
            self.assertIn("constraint", r)
            self.assertFalse(r["constraint"].endswith(f"({r['filter1']})"), r)

        clearance = by_name["Clearance"]
        self.assertEqual(clearance["constraint"], "Clearance Constraint (Gap=10mil)")
        self.assertEqual((clearance["filter1"], clearance["filter2"]), ("All", "All"))

        mask = by_name["SilkToSolderMaskClearance"]
        self.assertEqual(mask["constraint"], "Silk To Solder Mask (Clearance=10mil)")
        self.assertEqual((mask["filter1"], mask["filter2"]), ("IsPad", "All"))

        width = by_name["Width"]
        self.assertEqual(width["constraint"], "Width Constraint (Min=10mil) (Max=10mil) (Preferred=10mil)")
        self.assertNotIn("filter2", width, "a unary rule has one scope")

        self.assertEqual(by_name["Fanout_Small"]["constraint"], "Fanout Control Rule")
        self.assertEqual(by_name["Fanout_Small"]["filter1"], "(CompPinCount < 5)")


if __name__ == "__main__":
    unittest.main()
