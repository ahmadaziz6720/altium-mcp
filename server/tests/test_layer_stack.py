"""Unit tests for layer_stack and set_pcb_layer_stackup's side before and
after Altium (pure Python, no Altium needed: the bridge is faked).

Run from server/:  python -m unittest tests.test_layer_stack -v
"""
import asyncio
import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import main  # noqa: E402
import layer_stack as ls  # noqa: E402


def mask(name):
    return {"layer_name": name, "material_type": "Dielectric", "dielectric_type": "Surface Material",
            "dielectric_material": "Solder Resist", "dielectric_height_mils": 0.4, "dielectric_height_um": 10.16,
            "dielectric_constant": 3.5, "layer_order": 0}


def cu(name, layer_id, mils=1.4, ctype=None):
    ctype = ctype or ("Plane" if layer_id.startswith("Internal") else "Signal")
    return {"layer_name": name, "layer_id": layer_id, "material_type": "Copper", "copper_type": ctype,
            "copper_thickness_mils": mils, "copper_thickness_um": mils * 25.4, "layer_order": 0}


def diel(name, mils=12.6, kind="Core", material="FR-4", dk=4.8):
    return {"layer_name": name, "material_type": "Dielectric", "dielectric_type": kind,
            "dielectric_material": material, "dielectric_height_mils": mils, "dielectric_height_um": mils * 25.4,
            "dielectric_constant": dk, "layer_order": 0}


def numbered(layers):
    for i, l in enumerate(layers, 1):
        l["layer_order"] = i
    return layers


# What get_pcb_layer_stackup gives for a new 2-layer board and a 4-layer one
READ_2 = numbered([mask("Top Solder"), cu("Top Layer", "Top Layer"), diel("Dielectric 1"),
                   cu("Bottom Layer", "Bottom Layer"), mask("Bottom Solder")])
READ_4 = numbered([mask("Top Solder"), cu("Top Layer", "Top Layer"), diel("D1", 5, "PrePreg"),
                   cu("In1", "Mid Layer 1"), diel("D2", 40), cu("In2", "Mid Layer 2"), diel("D3", 5, "PrePreg"),
                   cu("Bottom Layer", "Bottom Layer"), mask("Bottom Solder")])


def parsed(layers):
    out, error = ls.parse_layers(layers)
    assert error is None, error
    return out


def board(layers):
    """The board's read as the tool passes it to plan."""
    return [{k: v for k, v in l.items() if k in ("material_type", "layer_name", "layer_id", "copper_type")}
            for l in layers]


class PresetTest(unittest.TestCase):
    def test_names_are_matched_loosely(self):
        for name in ("4_layer_1.6mm_7628", "4-layer 1.6 mm 7628", "4 LAYER 1.6MM 7628"):
            layers, error = ls.preset(name)
            self.assertIsNone(error, name)
            self.assertEqual(sum(1 for l in layers if l["material_type"] == "Copper"), 4)

    def test_unknown_preset_lists_the_presets(self):
        layers, error = ls.preset("6-layer")
        self.assertIsNone(layers)
        self.assertIn("2_layer_1.6mm", error)
        self.assertIn("4_layer_1.6mm_7628", error)

    def test_thicknesses(self):
        """1.6 mm of copper and dielectric in each, the masks on top of that."""
        for name in ls.PRESETS:
            layers = parsed(ls.preset(name)[0])
            body = [l for l in layers if l.get("dielectric_type") != "Surface Material"]
            total = sum(l.get("copper_thickness_mils", 0) + l.get("dielectric_height_mils", 0) for l in body)
            self.assertAlmostEqual(total * 0.0254, 1.6, places=4, msg=name)
            self.assertEqual(len(layers) - len(body), 2, name)

    def test_four_layer_build(self):
        layers = parsed(ls.preset("4_layer_1.6mm_7628")[0])
        self.assertEqual([l.get("copper_thickness_mils") for l in layers if l["material_type"] == "Copper"],
                         [1.378, 0.689, 0.689, 1.378])
        inner = [l for l in layers[2:-2] if l["material_type"] == "Dielectric"]
        self.assertEqual([(l["dielectric_type"], l["dielectric_height_mils"], l["dielectric_constant"]) for l in inner],
                         [("PrePreg", 7.874, 4.4), ("Core", 43.1102, 4.6), ("PrePreg", 7.874, 4.4)])
        self.assertEqual({l["copper_type"] for l in layers if l["material_type"] == "Copper"}, {"Signal"})
        self.assertFalse(any("layer_name" in l for l in layers), "presets set no layer names")

    def test_a_preset_is_a_valid_stack(self):
        for name in ls.PRESETS:
            top, coppers, gaps, bottom, error = ls.split(parsed(ls.preset(name)[0]))
            self.assertIsNone(error, name)
            self.assertEqual((len(top), len(bottom), len(gaps)), (1, 1, len(coppers) - 1))

    def test_a_preset_is_a_copy(self):
        layers = ls.preset("2_layer_1.6mm")[0]
        layers[1]["copper_thickness_mils"] = 99
        self.assertEqual(ls.preset("2_layer_1.6mm")[0][1]["copper_thickness_mils"], 1.378)


class ParseLayersTest(unittest.TestCase):
    def test_the_read_is_taken_as_it_is(self):
        out = parsed(READ_4)
        self.assertEqual(len(out), 9)
        self.assertEqual(out[3], {"material_type": "Copper", "layer_name": "In1", "layer_id": "Mid Layer 1",
                                  "copper_type": "Signal", "copper_thickness_mils": 1.4})
        self.assertEqual(out[2]["dielectric_type"], "PrePreg")
        self.assertNotIn("layer_order", out[0])

    def test_micrometres_alone(self):
        out = parsed([{"material_type": "Copper", "copper_thickness_um": 35}])
        self.assertEqual(out[0]["copper_thickness_mils"], 1.378)

    def test_mils_and_micrometres_must_agree(self):
        layer = cu("Top Layer", "Top Layer", 1.4)
        layer["copper_thickness_mils"] = 2.0
        out, error = ls.parse_layers([layer])
        self.assertIsNone(out)
        self.assertIn("disagree", error)

    def test_rounded_to_altiums_unit(self):
        out = parsed([{"material_type": "Dielectric", "dielectric_height_mils": 7.874015748}])
        self.assertEqual(out[0]["dielectric_height_mils"], 7.874)

    def test_spellings(self):
        out = parsed([{"material_type": "dielectric", "dielectric_type": "prepreg"},
                      {"material_type": "COPPER", "copper_type": "plane"},
                      {"material_type": "Copper", "layer_id": "Internal Plane 2"}])
        self.assertEqual(out[0], {"material_type": "Dielectric", "dielectric_type": "PrePreg"})
        self.assertEqual(out[1]["copper_type"], "Plane")
        self.assertEqual(out[2]["copper_type"], "Plane", "the kind follows the layer_id")

    def test_refusals(self):
        cases = [
            ([], "list"),
            (["x"], "not an object"),
            ([{"material_type": "Air"}], "material_type"),
            ([{"material_type": "Copper", "thickness": 1}], "unknown key"),
            ([{"material_type": "Copper", "dielectric_constant": 4}], "unknown key"),
            ([{"material_type": "Copper", "copper_thickness_mils": 0}], "outside"),
            ([{"material_type": "Copper", "copper_thickness_mils": 35}], "outside"),
            ([{"material_type": "Copper", "copper_thickness_mils": "1.4"}], "number"),
            ([{"material_type": "Dielectric", "dielectric_height_mils": 1600}], "outside"),
            ([{"material_type": "Dielectric", "dielectric_constant": 0.5}], "outside"),
            ([{"material_type": "Dielectric", "dielectric_type": "Glass"}], "dielectric_type"),
            ([{"material_type": "Dielectric", "dielectric_material": "FR-4|x"}], "'|'"),
            ([{"material_type": "Copper", "layer_name": "a;b"}], "';'"),
            ([{"material_type": "Copper", "layer_name": "  "}], "empty"),
            ([{"material_type": "Copper", "copper_type": "Mixed"}], "copper_type"),
            ([{"material_type": "Copper", "layer_id": "Mid Layer 1", "copper_type": "Plane"}], "Signal layer"),
        ]
        for layers, words in cases:
            out, error = ls.parse_layers(layers)
            self.assertIsNone(out, layers)
            self.assertIn(words, error, layers)


class SplitTest(unittest.TestCase):
    def test_shape(self):
        top, coppers, gaps, bottom, error = ls.split(parsed(READ_4))
        self.assertIsNone(error)
        self.assertEqual([c["layer_name"] for c in coppers], ["Top Layer", "In1", "In2", "Bottom Layer"])
        self.assertEqual([g["layer_name"] for g in gaps], ["D1", "D2", "D3"])
        self.assertEqual((len(top), len(bottom)), (1, 1))

    def test_one_dielectric_between_coppers(self):
        two = parsed([cu("A", "Top Layer"), diel("x"), diel("y"), cu("B", "Bottom Layer")])
        self.assertIn("2 dielectrics between A and B", ls.split(two)[4])
        none = parsed([cu("A", "Top Layer"), cu("B", "Bottom Layer")])
        self.assertIn("no dielectric between A and B", ls.split(none)[4])

    def test_two_coppers_at_least(self):
        self.assertIn("1 copper layer", ls.split(parsed([mask("m"), cu("A", "Top Layer"), mask("n")]))[4])
        self.assertIn("no copper", ls.split(parsed([mask("m")]))[4])


class PlanTest(unittest.TestCase):
    def test_read_set_back_changes_no_layer(self):
        for read in (READ_2, READ_4):
            plan, error = ls.plan(parsed(read), board(read))
            self.assertIsNone(error)
            self.assertEqual((plan["remove"], plan["add"], plan["structural"]), ([], [], False))
            self.assertEqual([e.get("layer_id") for e in plan["final"] if e["material_type"] == "Copper"],
                             [c["layer_id"] for c in read if c["material_type"] == "Copper"])

    def test_two_to_four(self):
        plan, error = ls.plan(parsed(ls.preset("4_layer_1.6mm_7628")[0]), board(READ_2))
        self.assertIsNone(error)
        self.assertEqual(plan["remove"], [])
        self.assertEqual([(a["index"], a["copper_type"], a["above"]) for a in plan["add"]],
                         [(1, "Signal", "Bottom Layer"), (2, "Signal", "Bottom Layer")])
        self.assertEqual(len(plan["final"]), 9)

    def test_four_to_two(self):
        plan, error = ls.plan(parsed(ls.preset("2_layer_1.6mm")[0]), board(READ_4))
        self.assertIsNone(error)
        self.assertEqual([r["layer_id"] for r in plan["remove"]], ["Mid Layer 1", "Mid Layer 2"])
        self.assertEqual(plan["add"], [])

    def test_a_preset_on_a_board_of_its_size_keeps_the_layers(self):
        plan, error = ls.plan(parsed(ls.preset("4_layer_1.6mm_7628")[0]), board(READ_4))
        self.assertIsNone(error)
        self.assertEqual((plan["remove"], plan["add"]), ([], []))

    def test_a_plane_added_between_kept_layers(self):
        layers = [dict(l) for l in READ_4]
        layers[5:5] = [{"material_type": "Copper", "copper_type": "Plane", "layer_name": "GND"},
                       {"material_type": "Dielectric", "dielectric_height_mils": 10}]
        plan, error = ls.plan(parsed(layers), board(READ_4))
        self.assertIsNone(error)
        self.assertEqual(plan["remove"], [])
        self.assertEqual([(a["copper_type"], a["above"], a["layer_name"]) for a in plan["add"]],
                         [("Plane", "Mid Layer 2", "GND")])
        self.assertEqual(ls.encode(plan).split(";")[0], "A|P|Mid Layer 2")

    def test_layer_left_out_is_removed(self):
        layers = [l for l in READ_4 if l["layer_name"] not in ("In1", "D2")]
        plan, error = ls.plan(parsed(layers), board(READ_4))
        self.assertIsNone(error)
        self.assertEqual([r["layer_id"] for r in plan["remove"]], ["Mid Layer 1"])

    def test_entries_without_layer_id_take_the_next_layer_of_their_kind(self):
        read = numbered([mask("t"), cu("Top Layer", "Top Layer"), diel("a"), cu("P1", "Internal Plane 1"),
                         diel("b"), cu("S1", "Mid Layer 1"), diel("c"), cu("Bottom Layer", "Bottom Layer"),
                         mask("b")])
        layers = [{"material_type": "Copper"}, {"material_type": "Dielectric"},
                  {"material_type": "Copper", "copper_type": "Signal"}, {"material_type": "Dielectric"},
                  {"material_type": "Copper"}]
        plan, error = ls.plan(parsed(layers), board(read))
        self.assertIsNone(error)
        self.assertEqual([r["layer_id"] for r in plan["remove"]], ["Internal Plane 1"])
        self.assertEqual(plan["add"], [])
        # the surfaces left out are kept as they are
        self.assertEqual(plan["final"][0], {"material_type": "Dielectric", "keep": True})
        self.assertEqual(ls.encode(plan).split(";")[1], "D|||||")

    def test_a_layer_id_not_on_the_board_is_a_new_layer(self):
        layers = [dict(l) for l in READ_2]
        layers[3:3] = [cu("x", "Mid Layer 7"), diel("y")]
        plan, error = ls.plan(parsed(layers), board(READ_2))
        self.assertIsNone(error)
        self.assertEqual([(a["copper_type"], a["above"]) for a in plan["add"]], [("Signal", "Bottom Layer")])

    def test_refusals(self):
        reordered = [dict(l) for l in READ_4]
        reordered[3], reordered[5] = reordered[5], reordered[3]
        twice = [dict(l) for l in READ_4]
        twice[5] = dict(twice[3])
        plane_top = [dict(l) for l in READ_2]
        plane_top[1] = {"material_type": "Copper", "copper_type": "Plane"}
        wrong_top = [dict(l) for l in READ_2]
        wrong_top[1] = cu("x", "Mid Layer 1")
        no_mask_below = READ_2[:-1] + [mask("a"), mask("b")]
        cases = [(reordered, READ_4, "not reordered"), (twice, READ_4, "given twice"),
                 (plane_top, READ_2, "cannot be a plane"), (wrong_top, READ_2, "always Altium's Top Layer"),
                 (no_mask_below, READ_2, "surface layers")]
        for layers, read, words in cases:
            plan, error = ls.plan(parsed(layers), board(read))
            self.assertIsNone(plan, words)
            self.assertIn(words, error)

    def test_board_with_two_dielectrics_in_a_gap_is_refused(self):
        read = numbered([cu("Top Layer", "Top Layer"), diel("a"), diel("b"), cu("Bottom Layer", "Bottom Layer")])
        plan, error = ls.plan(parsed(READ_2[1:4]), board(read))
        self.assertIsNone(plan)
        self.assertIn("the board's stack has 2 dielectrics", error)

    def test_too_many_layers(self):
        layers = [cu("Top Layer", "Top Layer")]
        for _ in range(31):
            layers += [diel("d"), {"material_type": "Copper"}]
        layers += [diel("d"), cu("Bottom Layer", "Bottom Layer")]
        plan, error = ls.plan(parsed(layers), board(READ_2[1:4]))
        self.assertIsNone(plan)
        self.assertIn("at most 30", error)


class EncodeTest(unittest.TestCase):
    def test_records(self):
        plan, _ = ls.plan(parsed(ls.preset("4_layer_1.6mm_7628")[0]), board(READ_2))
        recs = ls.encode(plan).split(";")
        self.assertEqual(recs[:2], ["A|S|Bottom Layer", "A|S|Bottom Layer"])
        self.assertEqual(recs[2], "D||3|Solder Resist|4000|35000")
        self.assertEqual(recs[3], "C||13780")
        self.assertEqual(recs[4], "D||2|FR-4 7628|78740|44000")
        self.assertEqual(recs[6], "D||1|FR-4|431102|46000")
        self.assertEqual(len(recs), 2 + 9)

    def test_removals_first_and_values_left_out(self):
        layers = [{"material_type": "Copper", "layer_name": "Top"}, {"material_type": "Dielectric"},
                  {"material_type": "Copper"}]
        plan, _ = ls.plan(parsed(layers), board(READ_4))
        self.assertEqual(ls.encode(plan),
                         "R|Mid Layer 1;R|Mid Layer 2;D|||||;C|Top|;D|||||;C||;D|||||")


class CompareTest(unittest.TestCase):
    def test_equal_on_the_keys_given(self):
        asked = [{"material_type": "Copper", "copper_thickness_mils": 1.4},
                 {"material_type": "Dielectric"},
                 {"material_type": "Copper", "layer_name": "Bottom Layer", "copper_type": "Signal"}]
        self.assertEqual(ls.compare(asked, READ_2[1:4]), [])

    def test_differences(self):
        asked = [{"material_type": "Copper", "copper_thickness_mils": 1.378},
                 {"material_type": "Dielectric", "dielectric_material": "FR-4", "dielectric_constant": 4.6},
                 {"material_type": "Copper"}]
        diffs = ls.compare(asked, READ_2[1:4])
        self.assertEqual([(d["entry"], d["key"]) for d in diffs],
                         [(1, "copper_thickness_mils"), (2, "dielectric_constant")])
        self.assertEqual(ls.compare(asked, READ_2)[0]["key"], "layers")
        swapped = [{"material_type": "Dielectric"}, {"material_type": "Copper"}, {"material_type": "Copper"}]
        self.assertEqual(ls.compare(swapped, READ_2[1:4])[0]["key"], "material_type")

    def test_value_changes_for_a_dry_run(self):
        layers = parsed(READ_2)
        layers[2]["dielectric_constant"] = 4.2
        plan, _ = ls.plan(layers, board(READ_2))
        self.assertEqual([(c["entry"], c["key"], c["from"], c["to"])
                          for c in ls.value_changes(plan["final"], READ_2, plan["structural"])],
                         [(3, "dielectric_constant", 4.8, 4.2)])
        # with layers added only the outer coppers and surfaces are compared
        plan, _ = ls.plan(parsed(ls.preset("4_layer_1.6mm_7628")[0]), board(READ_2))
        keys = {(c["layer_name"], c["key"]) for c in ls.value_changes(plan["final"], READ_2, True)}
        self.assertIn(("Top Layer", "copper_thickness_mils"), keys)
        self.assertFalse(any(name == "Dielectric 1" for name, _ in keys))


class ToolTest(unittest.TestCase):
    def run_tool(self, replies, **kwargs):
        calls = []

        async def fake(command, params):
            calls.append((command, params))
            return replies[len(calls) - 1]

        with mock.patch.object(main.altium_bridge, "execute_command", fake):
            out = json.loads(asyncio.run(main.set_pcb_layer_stackup(None, **kwargs)))
        return out, calls

    def test_refused_before_altium(self):
        for kwargs, words in (({}, "one of the two"),
                              ({"layers": READ_2, "preset": "2_layer_1.6mm"}, "one of the two"),
                              ({"preset": "8_layer"}, "no preset"),
                              ({"layers": [cu("a", "Top Layer"), cu("b", "Bottom Layer")]}, "no dielectric")):
            out, calls = self.run_tool([], **kwargs)
            self.assertFalse(out["success"])
            self.assertIn(words, out["error"])
            self.assertEqual(calls, [], kwargs)

    def test_layers_in_use_refuse_the_set(self):
        read = {"success": True, "result": {"board_name": "b.PcbDoc", "layers": READ_4}}
        refused = {"success": True, "result": "U|Mid Layer 1|In1|12|\nU|Mid Layer 2|In2|0|GND\nF|C:\\b.PcbDoc\n"}
        out, calls = self.run_tool([read, refused], preset="2_layer_1.6mm", board_path="C:\\b.PcbDoc")
        self.assertFalse(out["success"])
        self.assertEqual(out["layers_in_use"], [
            {"layer_id": "Mid Layer 1", "layer_name": "In1", "objects": 12, "net": None},
            {"layer_id": "Mid Layer 2", "layer_name": "In2", "objects": 0, "net": "GND"}])
        self.assertIn("In1 (Mid Layer 1, 12 objects)", out["error"])
        self.assertIn("net GND", out["error"])
        self.assertEqual([c[0] for c in calls], ["get_pcb_layer_stackup", "set_layer_stack"])
        self.assertEqual(calls[1][1]["stack_spec"].split(";")[:2], ["R|Mid Layer 1", "R|Mid Layer 2"])

    def test_set_and_read_back(self):
        read = {"success": True, "result": {"board_name": "b.PcbDoc", "layers": READ_2}}
        after = [dict(l) for l in READ_2]
        after[2] = dict(after[2], dielectric_constant=4.2)
        done = {"success": True, "result": "S|0\nK|1\nM|1\nF|C:\\b.PcbDoc\n"}
        reread = {"success": True, "result": {"board_name": "b.PcbDoc", "layers": after}}
        layers = [dict(l) for l in READ_2]
        layers[2]["dielectric_constant"] = 4.2
        out, calls = self.run_tool([read, done, reread], layers=layers)
        self.assertTrue(out["success"], out)
        self.assertEqual((out["changed"], out["board_modified"], out["added"], out["removed"], out["differences"]),
                         (1, True, [], [], []))
        self.assertEqual(out["stack"]["layers"], after)
        self.assertIs(calls[1][1]["dry_run"], False)

    def test_a_read_back_that_differs_is_a_failure(self):
        read = {"success": True, "result": {"board_name": "b.PcbDoc", "layers": READ_2}}
        done = {"success": True, "result": "S|0\nK|1\nM|1\nF|b\n"}
        layers = [dict(l) for l in READ_2]
        layers[2]["dielectric_constant"] = 4.2
        out, _ = self.run_tool([read, done, read], layers=layers)
        self.assertFalse(out["success"])
        self.assertEqual(out["differences"][0]["key"], "dielectric_constant")

    def test_dry_run_reports_and_reads_no_more(self):
        read = {"success": True, "result": {"board_name": "b.PcbDoc", "layers": READ_2}}
        checked = {"success": True, "result": "F|b\n"}
        out, calls = self.run_tool([read, checked], preset="4_layer_1.6mm_7628", dry_run=True)
        self.assertTrue(out["success"])
        self.assertTrue(out["dry_run"])
        self.assertEqual([a["copper_type"] for a in out["would_add"]], ["Signal", "Signal"])
        self.assertEqual(out["would_remove"], [])
        self.assertEqual(len(calls), 2)
        self.assertIs(calls[1][1]["dry_run"], True)

    def test_records(self):
        self.assertEqual(main._stack_records("U|Mid Layer 1|In1|3|\nK|2\n\nF|C:\\x|y.PcbDoc"),
                         {"U": [["Mid Layer 1", "In1", "3", ""]], "K": [["2"]], "F": [["C:\\x", "y.PcbDoc"]]})


if __name__ == "__main__":
    unittest.main()
