"""Live test of create_pcb_rule's rule kinds, its priority and the
fabricator presets (A14), in a running Altium Designer.

It drives Altium, so it is not in the offline set CI runs. With Altium open:

    set ALTIUM_LIVE=1
    python -m unittest tests.test_live_create_pcb_rule -v      (from server/)

It runs this checkout's scripts and works on copies of the 2-layer
SpiritLevel-SL1 board of the examples Altium installs, in a temporary
folder, closed unsaved. Each rule made is read back three ways: the tool's
result, Altium's own descriptor through get_pcb_rules, and the rule's
properties read through a board iterator by a script of this test, again
after a save, a close and a reopen of the copy.
"""
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import win32api

from tests.live_altium import (LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close, close_all_under,
                               modified, open_board, script, tool)

if LIVE:
    import main  # noqa: E402

EXAMPLES = Path(r"C:\Users\Public\Documents\Altium\AD25\Examples")
SL1 = EXAMPLES / "SpiritLevel-SL1" / "SL1 Xilinx Spartan-IIE PQ208 Rev1.02.PcbDoc"

U = 10000           # internal units per mil
MM = U / 0.0254     # internal units per mm


def save(path):
    out = script(f"Obj1 := Client.GetDocumentByPath('{path}');\n"
                 "ResultText := BoolToStr(Obj1.DoFileSave(''), True);").strip()
    if out != "True":
        raise AssertionError(f"could not save {path}")


# Each rule's properties, read by this test through a board iterator: one
# line per rule, name|kind|priority|scope1|scope2|comment|key=value;...
# (internal units)
READ_RULES = r"""var
    B : IPCB_Board;
    It : IPCB_BoardIterator;
    R : IPCB_Rule;
    K : Integer;
    S, P : String;
begin
B := PCBServer.GetPCBBoardByPath('@BOARD@');
S := '';
It := B.BoardIterator_Create;
It.AddFilter_ObjectSet(MkSet(eRuleObject));
It.AddFilter_LayerSet(AllLayers);
It.AddFilter_Method(eProcessAll);
R := It.FirstPCBObject;
while R <> nil do
begin
    K := R.RuleKind;
    P := '';
    if K = eRule_Clearance then P := 'gap=' + IntToStr(R.Gap)
    else if K = eRule_MaxMinWidth then
        P := 'min=' + IntToStr(R.MinWidth(eTopLayer)) + ';max=' + IntToStr(R.MaxWidth(eTopLayer)) +
             ';preferred=' + IntToStr(R.FavoredWidth(eTopLayer)) + ';bottom_min=' + IntToStr(R.MinWidth(eBottomLayer))
    else if K = eRule_MaxMinHoleSize then P := 'min=' + IntToStr(R.MinLimit) + ';max=' + IntToStr(R.MaxLimit)
    else if K = eRule_DifferentialPairsRouting then
        P := 'min_gap=' + IntToStr(R.MinGap(eTopLayer)) + ';max_gap=' + IntToStr(R.MaxGap(eTopLayer)) +
             ';preferred_gap=' + IntToStr(R.PreferedGap(eTopLayer)) + ';min_width=' + IntToStr(R.MinWidth(eTopLayer)) +
             ';max_width=' + IntToStr(R.MaxWidth(eTopLayer)) + ';preferred_width=' + IntToStr(R.PreferedWidth(eTopLayer)) +
             ';max_uncoupled_length=' + IntToStr(R.MaxUncoupledLength) +
             ';bottom_min_gap=' + IntToStr(R.MinGap(eBottomLayer)) + ';bottom_preferred_width=' + IntToStr(R.PreferedWidth(eBottomLayer))
    else if K = eRule_MaxMinLength then P := 'min=' + IntToStr(R.MinLimit) + ';max=' + IntToStr(R.MaxLimit)
    else if K = eRule_MatchedLengths then P := 'tolerance=' + IntToStr(R.Tolerance)
    else if K = eRule_RoutingLayers then
        P := 'top=' + BoolToStr(R.RoutingLayers(eTopLayer), True) + ';bottom=' + BoolToStr(R.RoutingLayers(eBottomLayer), True)
    else if K = eRule_PowerPlaneConnectStyle then
        P := 'connect_style=' + IntToStr(R.PlaneConnectStyle) + ';expansion=' + IntToStr(R.ReliefExpansion) +
             ';conductor_width=' + IntToStr(R.ReliefConductorWidth) + ';air_gap=' + IntToStr(R.ReliefAirGap) +
             ';entries=' + IntToStr(R.ReliefEntries)
    else if K = eRule_ComponentClearance then P := 'gap=' + IntToStr(R.Gap) + ';vertical_gap=' + IntToStr(R.VerticalGap)
    else if K = eRule_SilkToSolderMaskClearance then P := 'gap=' + IntToStr(R.SilkToMaskGap)
    else if K = eRule_SilkToSilkClearance then P := 'gap=' + IntToStr(R.SilkToSilkClearance)
    else if K = eRule_HoleToHoleClearance then P := 'gap=' + IntToStr(R.Gap)
    else if K = eRule_MinimumAnnularRing then P := 'min=' + IntToStr(R.Minimum)
    else if K = eRule_MinimumSolderMaskSliver then P := 'gap=' + IntToStr(R.MinSolderMaskSliver);
    S := S + R.Name + '|' + IntToStr(K) + '|' + IntToStr(R.Priority) + '|' + R.Scope1Expression + '|' +
         R.Scope2Expression + '|' + R.Comment + '|' + P + #13#10;
    R := It.NextPCBObject;
end;
B.BoardIterator_Destroy(It);
ResultText := S;
end;"""


def rules_on(board):
    """name -> {"kind", "priority", "scope1", "scope2", "comment", "props": {key: int or bool}}"""
    out = {}
    for line in script(READ_RULES.replace("@BOARD@", board)).splitlines():
        if not line.strip():
            continue
        name, kind, prio, s1, s2, comment, props = line.split("|", 6)
        values = {}
        for item in filter(None, props.split(";")):
            k, v = item.split("=", 1)
            values[k] = v == "True" if v in ("True", "False") else int(v)
        out[name] = {"kind": int(kind), "priority": int(prio), "scope1": s1, "scope2": s2,
                     "comment": comment, "props": values}
    return out


def kind_order(rules, kind):
    """The names of one kind's rules, highest priority first."""
    same = sorted((r["priority"], n) for n, r in rules.items() if r["kind"] == kind)
    return [n for _, n in same]


def in_mils(text):
    """A descriptor with its millimetre figures given in mils (a metric board's)."""
    def mils(m):
        v = float(m.group(1)) / 0.0254
        return f"{round(v)}mil" if abs(v - round(v)) < 0.05 else f"{v:.1f}mil"
    return re.sub(r"(\d+(?:\.\d+)?)mm", mils, text)


def descriptors():
    """name -> get_pcb_rules entry (constraint without its scope, its figures in mils)."""
    out = tool(main.get_pcb_rules(None))
    if not isinstance(out, list):
        raise AssertionError(out)
    for r in out:
        r["constraint"] = in_mils(r["constraint"])
    return {r["name"]: r for r in out}


# What each new kind is given, and what its properties must read back as
NEW_KINDS = [
    ("differential_pair", "A14_DP", {"min_gap_mils": 5, "max_gap_mils": 9, "preferred_gap_mils": 7,
                                     "min_width_mils": 4, "max_width_mils": 8, "preferred_width_mils": 6,
                                     "max_uncoupled_length_mils": 500}, "InDifferentialPairClass('All')", "All",
     {"min_gap": 5 * U, "max_gap": 9 * U, "preferred_gap": 7 * U, "min_width": 4 * U, "max_width": 8 * U,
      "preferred_width": 6 * U, "max_uncoupled_length": 500 * U, "bottom_min_gap": 5 * U,
      "bottom_preferred_width": 6 * U}),
    ("length", "A14_Len", {"min_mils": 100, "max_mils": 2000}, "InNet('VCC')", "All",
     {"min": 100 * U, "max": 2000 * U}),
    ("matched_length", "A14_Match", {"tolerance_mils": 25}, "InNetClass('All Nets')", "All",
     {"tolerance": 25 * U}),
    ("routing_layers", "A14_Layers", {"layers": ["Top Layer"]}, "InNet('GND')", "All",
     {"top": True, "bottom": False}),
    ("plane_connect", "A14_Plane", {"connect_style": "relief", "expansion_mils": 15, "conductor_width_mils": 12,
                                    "air_gap_mils": 11, "entries": 2}, "All", "All",
     {"connect_style": 0, "expansion": 15 * U, "conductor_width": 12 * U, "air_gap": 11 * U, "entries": 2}),
    ("component_clearance", "A14_Comp", {"gap_mils": 20, "vertical_gap_mils": 30}, "All", "All",
     {"gap": 20 * U, "vertical_gap": 30 * U}),
    ("silk_to_solder_mask", "A14_SilkMask", {"gap_mils": 6}, "IsPad", "All", {"gap": 6 * U}),
    ("silk_to_silk", "A14_SilkSilk", {"gap_mils": 5}, "All", "All", {"gap": 5 * U}),
    ("hole_to_hole", "A14_HoleHole", {"gap_mils": 8}, "All", "All", {"gap": 8 * U}),
    ("annular_ring", "A14_Ring", {"min_mils": 7}, "IsVia", "All", {"min": 7 * U}),
    ("solder_mask_sliver", "A14_Sliver", {"gap_mils": 4}, "All", "All", {"gap": 4 * U}),
]

# Altium's descriptor of each, read through get_pcb_rules (scope cut off)
CONSTRAINTS = {
    "A14_Len": "Length Constraint (Min=100mil) (Max=2000mil)",
    "A14_Match": "Matched Lengths(Tolerance=25mil)",
    "A14_Comp": "Component Clearance Constraint ( Horizontal Gap = 20mil, Vertical Gap = 30mil )",
    "A14_SilkMask": "Silk To Solder Mask (Clearance=6mil)",
    "A14_SilkSilk": "Silk to Silk (Clearance=5mil)",
    "A14_HoleHole": "Hole To Hole Clearance (Gap=8mil)",
    "A14_Ring": "Minimum Annular Ring (Minimum=7mil)",
    "A14_Sliver": "Minimum Solder Mask Sliver (Gap=4mil)",
}


@unittest.skipUnless(LIVE, SKIP_REASON)
class LiveCreatePcbRuleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        check_scripts_are_this_checkouts()

    def setUp(self):
        if not SL1.exists():
            self.skipTest(f"Altium's example board is not at {SL1}")
        # Altium is given the long path: the one it reports back
        self.tmp = Path(win32api.GetLongPathName(tempfile.mkdtemp(prefix="rules_live_")))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.addCleanup(close_all_under, str(self.tmp))

    def copy_of(self, name):
        board = str(self.tmp / name)
        shutil.copyfile(SL1, board)
        open_board(board)
        return board

    def reopen(self, board):
        save(board)
        close(board)
        open_board(board)

    def test_new_kinds(self):
        """Each new kind made, read back by its properties, by get_pcb_rules and after a reopen."""
        board = self.copy_of("kinds.PcbDoc")
        for kind, name, values, s1, s2, props in NEW_KINDS:
            out = tool(main.create_pcb_rule(None, kind, name, values, scope1=s1, scope2=s2, board_path=board))
            self.assertTrue(out.get("success"), f"{kind}: {out}")
            self.assertEqual(out.get("differences", []), [], out)
            self.assertEqual(out["read_back"], values, f"{kind}: the tool's read-back")
        self.assertTrue(modified(board))

        rules = rules_on(board)
        for kind, name, values, s1, s2, props in NEW_KINDS:
            self.assertIn(name, rules, kind)
            self.assertEqual(rules[name]["props"], props, f"{kind}: its properties")
            self.assertEqual(rules[name]["scope1"], s1, kind)
            self.assertEqual(rules[name]["priority"], 1, f"{kind}: a new rule is priority 1 by default")
        desc = descriptors()
        for name, constraint in CONSTRAINTS.items():
            self.assertEqual(desc[name]["constraint"], constraint, name)
        self.assertIn("Relief Connect", desc["A14_Plane"]["constraint"])
        self.assertIn("(Expansion=15mil) (Conductor Width=12mil) (Air Gap=11mil) (Entries=2)",
                      desc["A14_Plane"]["constraint"])
        self.assertIn("(Min=5mil) (Max=9mil) (Prefered=7mil)", desc["A14_DP"]["constraint"])

        self.reopen(board)
        again = rules_on(board)
        for kind, name, values, s1, s2, props in NEW_KINDS:
            self.assertEqual(again[name]["props"], props, f"{kind}: after a reopen")

        # Refused before Altium: a layer the board does not have, nothing added
        out = tool(main.create_pcb_rule(None, "routing_layers", "A14_Bad", {"layers": ["Mid Layer 7"]},
                                        board_path=board))
        self.assertFalse(out.get("success"), out)
        self.assertIn("Mid Layer 7", out["error"])
        self.assertNotIn("A14_Bad", rules_on(board))
        self.assertFalse(modified(board))

    def test_priority(self):
        """A rule put at a given priority, the others kept in their order, after a reopen too."""
        board = self.copy_of("priority.PcbDoc")
        before = kind_order(rules_on(board), 0)     # eRule_Clearance
        n = len(before)
        self.assertGreaterEqual(n, 1)
        low = tool(main.create_pcb_rule(None, "clearance", "A14_Low", {"gap_mils": 12}, scope1="InNet('GND')",
                                        priority=n + 1, board_path=board))
        self.assertTrue(low.get("success"), low)
        self.assertEqual(low["priority"], n + 1, low)
        mid = tool(main.create_pcb_rule(None, "clearance", "A14_Mid", {"gap_mils": 13}, scope1="InNet('VCC')",
                                        priority=2, board_path=board))
        self.assertTrue(mid.get("success"), mid)
        self.assertEqual(mid["priority"], 2, mid)
        self.assertNotIn("warning", mid, "a narrow rule below priority 1 overrides nothing it should warn of")
        wanted = before[:1] + ["A14_Mid"] + before[1:] + ["A14_Low"]
        rules = rules_on(board)
        self.assertEqual(kind_order(rules, 0), wanted)
        self.assertEqual([rules[nm]["priority"] for nm in wanted], list(range(1, n + 3)))
        self.assertEqual(rules["A14_Mid"]["props"], {"gap": 13 * U})
        desc = descriptors()
        self.assertEqual(desc["A14_Low"]["priority"], n + 2)
        self.assertEqual(desc["A14_Mid"]["priority"], 2)

        # Out of range: refused, nothing changed
        out = tool(main.create_pcb_rule(None, "clearance", "A14_Far", {"gap_mils": 9}, priority=n + 4,
                                        board_path=board))
        self.assertFalse(out.get("success"), out)
        self.assertIn("priority", out["error"])
        self.assertEqual(kind_order(rules_on(board), 0), wanted)

        self.reopen(board)
        again = rules_on(board)
        self.assertEqual(kind_order(again, 0), wanted, "after a reopen")
        self.assertEqual([again[nm]["priority"] for nm in wanted], list(range(1, n + 3)))

    def test_fabricator_preset(self):
        """JLCPCB's 2-layer minimums set at once, above the board's catch-all rules, after a reopen too."""
        board = self.copy_of("preset.PcbDoc")
        before = rules_on(board)

        dry = tool(main.create_pcb_rules_preset(None, "jlcpcb_2layer_1oz", board_path=board, dry_run=True))
        self.assertTrue(dry.get("success"), dry)
        self.assertTrue(dry["dry_run"])
        self.assertEqual(dry["source"], "https://jlcpcb.com/capabilities/pcb-capabilities")
        self.assertEqual(dry["read"], "2026-11-15")
        self.assertIn("width", [s["rule_type"] for s in dry["skipped"]], "width needs its preferred and max")
        self.assertEqual(rules_on(board), before, "a dry run changes nothing")
        self.assertFalse(modified(board))

        out = tool(main.create_pcb_rules_preset(None, "jlcpcb_2layer_1oz", board_path=board,
                                                width_preferred_mils=10, width_max_mils=100))
        self.assertTrue(out.get("success"), json.dumps(out, indent=1))
        self.assertEqual(out["skipped"], [])
        made = {r["name"]: r for r in out["rules"]}
        self.assertEqual([r["name"] for r in dry["rules"]],
                         [r["name"] for r in out["rules"] if r["rule_type"] != "width"])
        expect = {   # name -> (kind enum, props), from the page's figures in mm
            "JLCPCB_2L_1oz_Clearance": (0, {"gap": round(0.10 * MM)}),
            "JLCPCB_2L_1oz_Width": (2, {"min": round(0.10 * MM), "max": 100 * U, "preferred": 10 * U,
                                        "bottom_min": round(0.10 * MM)}),
            "JLCPCB_2L_1oz_HoleSize": (42, {"min": round(0.15 * MM), "max": round(6.3 * MM)}),
            "JLCPCB_2L_1oz_ViaHoleToHole": (52, {"gap": round(0.2 * MM)}),
            "JLCPCB_2L_1oz_HoleToHole": (52, {"gap": round(0.45 * MM)}),
            "JLCPCB_2L_1oz_ViaAnnularRing": (19, {"min": round(0.05 * MM)}),
            "JLCPCB_2L_1oz_PadAnnularRing": (19, {"min": round(0.18 * MM)}),
            "JLCPCB_2L_1oz_SilkToPad": (54, {"gap": round(0.15 * MM)}),
            "JLCPCB_2L_1oz_MaskSliver": (53, {"gap": round(0.10 * MM)}),
        }
        self.assertEqual(sorted(made), sorted(expect))
        rules = rules_on(board)
        for name, (kind, props) in expect.items():
            self.assertEqual(rules[name]["kind"], kind, name)
            self.assertEqual(rules[name]["props"], props, name)
            self.assertEqual(rules[name]["priority"], made[name]["priority"], name)
        # Each sits above its kind's catch-all rules and below the narrower ones the board had
        for name, (kind, _) in expect.items():
            order = kind_order(rules, kind)
            for other in order[order.index(name) + 1:]:
                if other.startswith("JLCPCB_"):
                    continue
                self.assertIn(other, before)
            for other in order[:order.index(name)]:
                if other.startswith("JLCPCB_"):
                    continue
                r, mine = before[other], rules[name]
                self.assertFalse(r["scope1"] == "All" and r["scope2"] in ("All", ""),
                                 f"{other}, a catch-all rule, stays above {name}")
                self.assertFalse((r["scope1"], r["scope2"]) == (mine["scope1"], mine["scope2"]),
                                 f"{other}, of the same scope, stays above {name}")
        self.assertLess(rules["JLCPCB_2L_1oz_ViaHoleToHole"]["priority"],
                        rules["JLCPCB_2L_1oz_HoleToHole"]["priority"])
        self.assertLess(rules["JLCPCB_2L_1oz_ViaAnnularRing"]["priority"],
                        rules["JLCPCB_2L_1oz_PadAnnularRing"]["priority"])
        for name in expect:
            self.assertIn("jlcpcb.com/capabilities/pcb-capabilities", rules[name]["comment"], name)
            self.assertIn("2026-11-15", rules[name]["comment"], name)

        # Again: refused by name, nothing changed
        again = tool(main.create_pcb_rules_preset(None, "jlcpcb_2layer_1oz", board_path=board,
                                                  width_preferred_mils=10, width_max_mils=100))
        self.assertFalse(again.get("success"), again)
        self.assertIn("JLCPCB_2L_1oz_Clearance", again["error"])
        self.assertEqual(rules_on(board), rules)

        self.reopen(board)
        after = rules_on(board)
        for name, (kind, props) in expect.items():
            self.assertEqual(after[name]["props"], props, f"{name} after a reopen")
            self.assertEqual(after[name]["priority"], rules[name]["priority"], f"{name} after a reopen")


if __name__ == "__main__":
    unittest.main()
