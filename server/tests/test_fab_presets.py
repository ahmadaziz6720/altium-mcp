"""Unit tests for the fabricator presets (A14): the data files, the priority
each rule is given, create_pcb_rule's priority and read-back, and
create_pcb_rules_preset with the bridge faked. No Altium needed.

Run from server/:  python -m unittest tests.test_fab_presets -v
"""
import asyncio
import json
import os
import re
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import main  # noqa: E402
import pcb_rules  # noqa: E402

PRESETS = pcb_rules.load_presets()


def figures_in(text):
    """The figures a page text gives."""
    return {float(m) for m in re.findall(r"\d+(?:\.\d+)?", text)}


class PresetFileTest(unittest.TestCase):
    def test_presets_there(self):
        self.assertIn("jlcpcb_2layer_1oz", PRESETS)
        self.assertIn("jlcpcb_multilayer_1oz", PRESETS)

    def test_each_names_its_page_and_date(self):
        for name, build in PRESETS.items():
            self.assertTrue(build["source"].startswith("https://"), name)
            self.assertRegex(build["read"], r"^\d{4}-\d{2}-\d{2}$", name)
            self.assertTrue(build["fabricator"], name)

    def test_every_rule_encodes_and_has_its_row(self):
        for name, build in PRESETS.items():
            names = [r["name"] for r in build["rules"]]
            self.assertEqual(len(names), len(set(names)), name)
            for rule in build["rules"]:
                self.assertIn(rule["rule_type"], pcb_rules.RULE_KINDS, rule["name"])
                self.assertTrue(rule["page_row"] and rule["page_text"], rule["name"])
                values = pcb_rules.preset_rule_values(rule)
                if rule["rule_type"] == "width":
                    self.assertEqual(rule["needs"], ["preferred_mils", "max_mils"])
                    values.update(preferred_mils=10, max_mils=100)
                self.assertEqual(pcb_rules.encode_values(rule["rule_type"], values)[1], "", rule["name"])
                self.assertTrue(rule["name"].startswith("JLCPCB_"), rule["name"])

    def test_each_figure_is_on_the_page_or_its_working_given(self):
        """A rule's mm figure is in its quoted page text, or the rule says how it was derived."""
        for name, build in PRESETS.items():
            for rule in build["rules"]:
                for key, value in rule["values_mm"].items():
                    if rule.get("derived"):
                        continue
                    self.assertIn(value, figures_in(rule["page_text"]), f"{rule['name']} {key}")

    def test_figures_as_the_page_gave_them(self):
        two = {r["name"]: r["values_mm"] for r in PRESETS["jlcpcb_2layer_1oz"]["rules"]}
        self.assertEqual(two["JLCPCB_2L_1oz_Clearance"], {"gap": 0.10})
        self.assertEqual(two["JLCPCB_2L_1oz_HoleSize"], {"min": 0.15, "max": 6.3})
        self.assertEqual(two["JLCPCB_2L_1oz_PadAnnularRing"], {"min": 0.18})
        ml = {r["name"]: r["values_mm"] for r in PRESETS["jlcpcb_multilayer_1oz"]["rules"]}
        self.assertEqual(ml["JLCPCB_ML_1oz_Clearance"], {"gap": 0.09})
        self.assertEqual(ml["JLCPCB_ML_1oz_PadAnnularRing"], {"min": 0.15})

    def test_mm_to_mils(self):
        values = pcb_rules.preset_rule_values({"values_mm": {"gap": 0.254}})
        self.assertAlmostEqual(values["gap_mils"], 10.0)
        self.assertEqual(pcb_rules.encode_values("clearance", pcb_rules.preset_rule_values(
            {"values_mm": {"gap": 0.10}})), ("gap=39370", ""))


def board_rule(name, kind, priority, f1="All", f2="All", unary=False):
    return {"name": name, "rule_kind": pcb_rules.SHORT_DESCRIPTORS[kind], "priority": priority,
            "filter1": f1, "filter2": f2, "unary": unary}


class PlanPrioritiesTest(unittest.TestCase):
    def test_above_the_catch_all_below_narrower_rules(self):
        existing = [board_rule("Gnd", "clearance", 1, "InNet('GND')"), board_rule("Clearance", "clearance", 2)]
        new = [{"name": "F", "rule_type": "clearance", "scope1": "All", "scope2": "All"}]
        self.assertEqual(pcb_rules.plan_priorities(existing, new), [2])

    def test_same_scope_counts_as_taken_over(self):
        existing = [board_rule("Silk", "silk_to_solder_mask", 1, "IsPad", "All")]
        new = [{"name": "F", "rule_type": "silk_to_solder_mask", "scope1": "ispad", "scope2": " All"}]
        self.assertEqual(pcb_rules.plan_priorities(existing, new), [1])

    def test_lowest_when_nothing_to_take_over(self):
        existing = [board_rule("A", "annular_ring", 1, "IsVia", unary=True)]
        new = [{"name": "F", "rule_type": "annular_ring", "scope1": "IsPad", "scope2": "All"}]
        self.assertEqual(pcb_rules.plan_priorities(existing, new), [2])
        self.assertEqual(pcb_rules.plan_priorities([], new), [1])

    def test_preset_rules_in_their_order(self):
        existing = [board_rule("HoleToHoleClearance", "hole_to_hole", 1)]
        new = [{"name": "V", "rule_type": "hole_to_hole", "scope1": "IsVia", "scope2": "IsVia"},
               {"name": "A", "rule_type": "hole_to_hole", "scope1": "All", "scope2": "All"}]
        # V above the board's catch-all; A above it too, below V
        self.assertEqual(pcb_rules.plan_priorities(existing, new), [1, 2])

    def test_replace_takes_the_old_one_out_first(self):
        existing = [board_rule("F", "clearance", 1), board_rule("Clearance", "clearance", 2)]
        new = [{"name": "F", "rule_type": "clearance", "scope1": "All", "scope2": "All"}]
        self.assertEqual(pcb_rules.plan_priorities(existing, new, replace=True), [1])

    def test_unary_rule_ignores_filter2(self):
        self.assertTrue(pcb_rules.is_catch_all({"filter1": "All", "filter2": "IsPad", "unary": True}))
        self.assertFalse(pcb_rules.is_catch_all({"filter1": "All", "filter2": "IsPad", "unary": False}))


def run(coro_fn, replies, **kwargs):
    calls = []

    async def fake(command, params):
        calls.append((command, params))
        reply = replies[len(calls) - 1]
        return reply(params) if callable(reply) else reply

    with mock.patch.object(main.altium_bridge, "execute_command", fake):
        out = json.loads(asyncio.run(coro_fn(None, **kwargs)))
    return out, calls


def made(params, priority=None, read_back=None):
    """Altium's answer to create_pcb_rule: the values stored as sent."""
    return {"success": True, "result": {
        "success": True, "name": params["rule_name"], "descriptor": "D", "scope1": params["scope1"],
        "scope2": params["scope2"], "priority": priority or params["priority"] or 1, "other_rules_of_kind": 1,
        "enabled": True, "replaced": False, "comment": params["comment"],
        "read_back": params["values"] if read_back is None else read_back, "board": "b.PcbDoc"}}


class CreateRuleToolTest(unittest.TestCase):
    def test_priority_sent_and_read_back(self):
        out, calls = run(main.create_pcb_rule, [made], rule_type="hole_to_hole", name="H",
                         values={"gap_mils": 8}, priority=3)
        self.assertTrue(out["success"], out)
        self.assertEqual(calls[0][1]["priority"], 3)
        self.assertEqual(out["read_back"], {"gap_mils": 8})
        self.assertNotIn("warning", out)

    def test_altium_storing_another_value_fails_the_call(self):
        out, _ = run(main.create_pcb_rule, [lambda p: made(p, read_back="gap=100000")], rule_type="hole_to_hole",
                     name="H", values={"gap_mils": 8})
        self.assertFalse(out["success"])
        self.assertEqual(out["differences"], ["gap_mils: sent 8, Altium has 10"])

    def test_priority_not_reached_fails_the_call(self):
        out, _ = run(main.create_pcb_rule, [lambda p: made(p, priority=1)], rule_type="clearance", name="C",
                     values={"gap_mils": 8}, priority=2)
        self.assertFalse(out["success"])
        self.assertIn("priority: asked 2, Altium has 1", out["error"])

    def test_bad_priority_refused_before_altium(self):
        for bad in (-1, True, 1.5, "2"):
            out, calls = run(main.create_pcb_rule, [], rule_type="clearance", name="C", values={"gap_mils": 8},
                             priority=bad)
            self.assertFalse(out["success"], bad)
            self.assertEqual(calls, [], bad)

    def test_catch_all_at_one_warns(self):
        out, _ = run(main.create_pcb_rule, [made], rule_type="clearance", name="C", values={"gap_mils": 8})
        self.assertIn("overrides", out["warning"])
        out, _ = run(main.create_pcb_rule, [made], rule_type="annular_ring", name="R", values={"min_mils": 4},
                     scope2="IsPad")
        self.assertIn("overrides", out["warning"], "a unary rule's scope2 does not narrow it")


class PresetToolTest(unittest.TestCase):
    RULES = {"success": True, "result": [board_rule("Clearance", "clearance", 1),
                                         board_rule("HoleToHoleClearance", "hole_to_hole", 1),
                                         board_rule("SilkToSolderMaskClearance", "silk_to_solder_mask", 1,
                                                    "IsPad", "All"),
                                         board_rule("Width", "width", 1, unary=True)]}

    def test_unknown_preset_lists_them(self):
        out, calls = run(main.create_pcb_rules_preset, [], preset="acme")
        self.assertFalse(out["success"])
        self.assertIn("jlcpcb_2layer_1oz", out["error"])
        self.assertEqual(calls, [])

    def test_dry_run_reads_only(self):
        out, calls = run(main.create_pcb_rules_preset, [self.RULES], preset="jlcpcb_2layer_1oz", dry_run=True,
                         board_path="C:\\b.PcbDoc")
        self.assertTrue(out["success"], out)
        self.assertEqual([c[0] for c in calls], ["get_pcb_rules"])
        self.assertEqual(out["source"], "https://jlcpcb.com/capabilities/pcb-capabilities")
        self.assertEqual(out["read"], "2026-11-15")
        self.assertEqual([s["rule_type"] for s in out["skipped"]], ["width"])
        by = {r["name"]: r for r in out["rules"]}
        self.assertEqual(by["JLCPCB_2L_1oz_Clearance"]["priority"], 1)
        self.assertEqual((by["JLCPCB_2L_1oz_ViaHoleToHole"]["priority"], by["JLCPCB_2L_1oz_HoleToHole"]["priority"]),
                         (1, 2))
        self.assertEqual(by["JLCPCB_2L_1oz_SilkToPad"]["priority"], 1)
        self.assertEqual((by["JLCPCB_2L_1oz_ViaAnnularRing"]["priority"],
                          by["JLCPCB_2L_1oz_PadAnnularRing"]["priority"]), (1, 2))
        self.assertAlmostEqual(by["JLCPCB_2L_1oz_Clearance"]["values"]["gap_mils"], 3.937, places=3)
        self.assertIn("jlcpcb.com/capabilities/pcb-capabilities read 2026-11-15",
                      by["JLCPCB_2L_1oz_Clearance"]["comment"])
        self.assertTrue(out["not_set"])

    def test_made_in_order_with_width(self):
        replies = [self.RULES] + [made] * 9
        out, calls = run(main.create_pcb_rules_preset, replies, preset="jlcpcb_2layer_1oz",
                         width_preferred_mils=10, width_max_mils=100, board_path="C:\\b.PcbDoc")
        self.assertTrue(out["success"], out)
        self.assertEqual(out["skipped"], [])
        sent = [c[1] for c in calls[1:]]
        self.assertEqual([c[0] for c in calls[1:]], ["create_pcb_rule"] * 9)
        width = [p for p in sent if p["rule_kind"] == "width"][0]
        self.assertEqual(width["values"], "min=39370;max=1000000;preferred=100000")
        self.assertEqual(width["priority"], 1)
        self.assertTrue(all(p["board_path"] == "C:\\b.PcbDoc" for p in sent))

    def test_names_taken_refuse_everything(self):
        rules = {"success": True, "result": self.RULES["result"] + [board_rule("JLCPCB_2L_1oz_Clearance",
                                                                              "clearance", 2)]}
        out, calls = run(main.create_pcb_rules_preset, [rules], preset="jlcpcb_2layer_1oz")
        self.assertFalse(out["success"])
        self.assertIn("JLCPCB_2L_1oz_Clearance", out["error"])
        self.assertEqual(len(calls), 1)

    def test_a_failure_stops_and_says_what_was_made(self):
        replies = [self.RULES, made, {"success": False, "error": "boom"}]
        out, calls = run(main.create_pcb_rules_preset, replies, preset="jlcpcb_2layer_1oz")
        self.assertFalse(out["success"])
        self.assertEqual(len(out["rules"]), 2)
        self.assertIn("boom", out["error"])
        self.assertEqual(len(calls), 3)


if __name__ == "__main__":
    unittest.main()
