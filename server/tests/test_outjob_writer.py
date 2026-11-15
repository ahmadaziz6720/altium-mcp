"""Unit tests for outjob_writer and write_outjob (A12), no Altium needed.

From server/:  python -m unittest tests.test_outjob_writer -v
"""
import asyncio
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import outjob_writer as ow  # noqa: E402
from outjob_parser import layer_name, parse_outjob  # noqa: E402

# An OutJob as Altium writes one (keys of the AD25 examples): a printer and a
# generated-files container, a Gerber output going to the second
ALTIUM_FILE = r"""[OutputJobFile]
Version=1.0
Caption=

[OutputGroup1]
Name=
TargetOutputMedium=Fab data
VariantName=[No Variations]
OutputMedium1=Print Job
OutputMedium1_Type=Printer
OutputMedium1_Printer=
OutputMedium2=Fab data
OutputMedium2_Type=GeneratedFiles
OutputMedium3=PDF
OutputMedium3_Type=Publish
OutputType1=Gerber
OutputName1=Gerber Files
OutputCategory1=Fabrication
OutputDocumentPath1=
OutputVariantName1=
OutputEnabled1=1
OutputEnabled1_OutputMedium1=0
OutputEnabled1_OutputMedium2=1
OutputEnabled1_OutputMedium3=0
OutputDefault1=0
Configuration1_Name1=OutputConfigurationParameter1
Configuration1_Item1=AddToAllPlots.Set=SerializeLayerHash.Version~2,ClassName~TLayerToBoolean|GerberUnit=Imperial|LeadingAndTrailingZeroesMode=SuppressLeadingZeroes|NumberOfDecimals=5|OriginPosition=Relative|Plot.Set=SerializeLayerHash.Version~2,ClassName~TLayerToBoolean,16777217~1,16842751~1,16908289~1|Record=GerberView|Sorted=False
OutputType2=Schematic Print
OutputName2=Schematic Prints
OutputEnabled2=1
OutputEnabled2_OutputMedium1=0
OutputEnabled2_OutputMedium2=0
OutputEnabled2_OutputMedium3=1
OutputDefault2=0

[PublishSettings]
OutputFilePath2=
ReleaseManaged2=1
OutputBasePath2=Project Outputs
OutputPathOutputer2=[Output Type]
OutputFileName3=Docs.pdf

[GeneratedFilesSettings]
RelativeOutputPath2=Project Outputs
OpenOutputs2=1
AddToProject2=1
"""


def run(coro):
    return json.loads(asyncio.run(coro))


class LayerTest(unittest.TestCase):
    def test_every_name_goes_back_to_its_id(self):
        names = ow.COPPER + ["Top Overlay", "Bottom Overlay", "Top Paste", "Bottom Paste", "Top Solder",
                             "Bottom Solder", "Keep-Out Layer", "Mechanical 1", "Mechanical 32", "Top Pad Master"]
        for name in names:
            self.assertEqual(layer_name(ow.layer_id(name)), name)
        self.assertEqual(ow.layer_id("  top   OVERLAY "), 0x01030006)

    def test_copper_is_every_copper_layer_once(self):
        ids = ow.layer_ids(["copper", "Top Layer", "Top Overlay"])
        self.assertEqual(len(ids), 2 + ow.MID_LAYERS + ow.PLANES + 1)
        self.assertEqual(ids[0], 0x01000001)
        self.assertEqual(ids[-1], 0x01030006)

    def test_unknown_layers_refused(self):
        for bad in ("Mid Layer 31", "Internal Plane 0", "Mechanical 33", "Top Silk", ""):
            with self.assertRaises(ow.OutJobError, msg=bad):
                ow.layer_id(bad)
        with self.assertRaises(ow.OutJobError):
            ow.layer_ids("Top Layer")


class SettingsTest(unittest.TestCase):
    def test_gerber_keys(self):
        v = ow.gerber_values({"units": "mm", "format": "4:4", "zeroes": "suppress_leading", "origin": "absolute",
                              "board_profile": True, "layers": ["Top Layer"]})
        self.assertEqual(v["GerberUnit"], "Metric")
        self.assertEqual(v["NumberOfDecimals"], "4")
        self.assertEqual(v["LeadingAndTrailingZeroesMode"], "SuppressLeadingZeroes")
        self.assertEqual(v["OriginPosition"], "Absolute")
        self.assertEqual(v["PlotBoardProfile"], "True")
        self.assertTrue(v["Plot.Set"].endswith(",16777217~1"))

    def test_format_checked_against_units(self):
        with self.assertRaises(ow.OutJobError):
            ow.gerber_values({"units": "mm", "format": "2:5"})
        with self.assertRaises(ow.OutJobError):
            ow.drill_values({"units": "inch", "format": "4:4"})
        # a format alone is checked against the units the file has
        self.assertEqual(ow.gerber_values({"format": "2:4"}, current_units="inch"), {"NumberOfDecimals": "4"})
        with self.assertRaises(ow.OutJobError):
            ow.gerber_values({"format": "2:4"}, current_units="mm")
        # a change of units needs its format: the decimals mean another thing
        with self.assertRaises(ow.OutJobError):
            ow.gerber_values({"units": "inch"}, current_units="mm")
        self.assertEqual(ow.gerber_values({"units": "mm"}, current_units="mm"), {"GerberUnit": "Metric"})

    def test_drill_keys(self):
        v = ow.drill_values({"units": "inch", "format": "2:5", "zeroes": "keep", "origin": "absolute",
                             "separate_plated": True})
        self.assertEqual(v, {"Units": "Imperial", "NumberOfUnits": "2", "NumberOfDecimals": "5",
                             "ZeroesMode": "KeepLeadingAndTrailingZeroes", "OriginPosition": "Absolute",
                             "GenerateSeparatePlatedNonPlatedFiles": "True"})

    def test_pick_place_and_bom_keys(self):
        self.assertEqual(ow.pnp_values({"units": "mil", "formats": ["txt", "csv"]}),
                         {"Units": "Imperial", "GenerateCSVFormat": "True", "GenerateTextFormat": "True"})
        b = ow.bom_values({"format": "csv", "columns": ["Comment", "LCSC Part #"], "group_by": ["Comment"]})
        self.assertEqual(b, {"BatchMode": "0", "VisibleOrder": "Comment=100|LCSC Part #=100",
                             "GroupOrder": "Comment=True"})

    def test_bad_settings_refused(self):
        for kind, spec in (("gerber", {"unit": "mm"}), ("gerber", {"zeroes": "none"}),
                           ("gerber", {"board_profile": "yes"}), ("nc_drill", {"origin": "centre"}),
                           ("pick_place", {"formats": []}), ("pick_place", {"formats": ["pdf"]}),
                           ("bom", {"format": "docx"}), ("bom", {"columns": ["A", "a"]}),
                           ("bom", {"columns": ["A|B"]}), ("bom", {"columns": "Comment"}),
                           ("bom", {"group_by": ["X=Y"]})):
            fn = {"gerber": ow.gerber_values, "nc_drill": ow.drill_values, "pick_place": ow.pnp_values,
                  "bom": ow.bom_values}[kind]
            with self.assertRaises(ow.OutJobError, msg=(kind, spec)):
                fn(spec)

    def test_record_update_keeps_order(self):
        self.assertEqual(ow.update_record("A=1|B=2|Record=X", {"B": "3", "C": "4"}), "A=1|B=3|Record=X|C=4")
        self.assertEqual(ow.update_record("A= |B", {"A": "x"}), "A=x|B")


class PresetTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_preset_names_its_pages(self):
        p = ow.load_presets()["fab_jlcpcb"]
        self.assertEqual(p["service"], "JLCPCB")
        for kind in ("gerber", "nc_drill", "bom", "pick_place"):
            src = p["sources"][p[kind]["source"]]
            self.assertTrue(src["url"].startswith("https://jlcpcb.com/"), src)
            self.assertRegex(src["read"], r"^\d{4}-\d{2}-\d{2}$")
            for key in ow.SETTING_KEYS[kind]:
                if key in p[kind]:
                    self.assertTrue(key in p[kind].get("page_text", {}) or key in p[kind].get("decided", {})
                                    or (kind == "gerber" and key == "layers"), (kind, key))
        # the page's figures, as quoted
        g = p["gerber"]
        self.assertIn("4:4", g["page_text"]["format"])
        self.assertEqual((g["units"], g["format"]), ("mm", "4:4"))
        d = p["nc_drill"]
        self.assertIn("2:5", d["page_text"]["format"])
        self.assertEqual((d["units"], d["format"], d["zeroes"]), ("inch", "2:5", "keep"))

    def test_preset_written_reads_back(self):
        p = ow.load_presets()["fab_jlcpcb"]
        doc = ow.new_document(p["container"])
        specs = ow.preset_specs(p)
        done = ow.apply(doc, specs, p["container"], p["output_folder"])
        path = os.path.join(self.tmp, "J.OutJob")
        with open(path, "wb") as f:
            f.write(doc.text().encode("cp1252"))
        parsed = parse_outjob(path, include_raw=False)
        self.assertEqual(ow.compare(parsed, specs, done, p["output_folder"], None), [])
        by_type = {o["type"]: o for o in parsed["outputs"]}
        self.assertEqual(by_type["Gerber"]["gerber"]["units"], "Metric")
        self.assertTrue(by_type["Gerber"]["gerber"]["plot_board_profile"])
        self.assertEqual(by_type["BOM_PartType"]["bom"]["columns"], ["Comment", "Designator", "Footprint", "LCSC Part #"])
        self.assertFalse(by_type["BOM_PartType"]["bom"]["open_exported"])
        c = parsed["containers"][0]
        self.assertEqual((c["name"], c["type"], c["base_path"], c["release_managed"], c["add_to_project"],
                          c["open_outputs"]), ("JLCPCB Outputs", "GeneratedFiles", "JLCPCB", False, False, False))
        self.assertEqual([o["connected_containers"] for o in parsed["outputs"]], [["JLCPCB Outputs"]] * 4)
        text = doc.text()
        self.assertNotIn("\n\n\n", text)
        self.assertTrue(all(l.endswith("\r") or not l for l in text.split("\n")[:-1]), "CRLF line ends")


class EditTest(unittest.TestCase):
    def setUp(self):
        self.doc = ow.IniDoc(ALTIUM_FILE)
        self.before = self.doc.text()

    def test_edit_changes_only_what_is_asked(self):
        done = ow.apply(self.doc, {"gerber": {"units": "mm", "format": "4:4"}})
        self.assertEqual(done["container"], "Fab data")
        self.assertFalse(done["outputs"]["gerber"]["added"])
        self.assertFalse(done["outputs"]["gerber"]["connected_now"])
        old, new = self.before.split("\r\n"), self.doc.text().split("\r\n")
        changed = [(a, b) for a, b in zip(old, new) if a != b]
        self.assertEqual(len(old), len(new))
        self.assertEqual(len(changed), 1)
        self.assertIn("GerberUnit=Metric", changed[0][1])
        self.assertIn("NumberOfDecimals=4", changed[0][1])
        self.assertIn("OriginPosition=Relative", changed[0][1], "not asked, kept")

    def test_missing_output_added_and_connected_after_the_others(self):
        done = ow.apply(self.doc, {"nc_drill": {"units": "mm", "format": "4:3"}}, output_folder="Fab")
        n = done["outputs"]["nc_drill"]["index"]
        self.assertEqual(n, 3)
        self.assertTrue(done["outputs"]["nc_drill"]["added"])
        self.assertEqual(self.doc.get("OutputGroup1", "OutputType3"), "NC Drill")
        self.assertEqual(self.doc.get("OutputGroup1", "OutputEnabled3_OutputMedium2"), "2")
        self.assertEqual(self.doc.get("OutputGroup1", "OutputEnabled3_OutputMedium1"), "0")
        self.assertEqual(self.doc.get("PublishSettings", "OutputBasePath2"), "Fab")
        self.assertEqual(self.doc.get("PublishSettings", "ReleaseManaged2"), "0")
        self.assertEqual(self.doc.get("PublishSettings", "OutputPathOutputer2"), "")
        self.assertEqual(self.doc.get("GeneratedFilesSettings", "RelativeOutputPath2"), "Fab")
        # the new output's lines follow the last output's
        lines = self.doc.section("OutputGroup1")
        self.assertLess(lines.index("OutputDefault2=0"), lines.index("OutputType3=NC Drill"))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "x.OutJob")
            with open(path, "w", encoding="cp1252", newline="") as f:
                f.write(self.doc.text())
            parsed = parse_outjob(path)
            self.assertEqual(ow.compare(parsed, {"nc_drill": {"units": "mm", "format": "4:3"}}, done, "Fab", None), [])
            self.assertEqual(parsed["outputs"][2]["connected_containers"], ["Fab data"])

    def test_new_container_connects_every_output_to_nothing(self):
        done = ow.apply(self.doc, {"pick_place": {"units": "mm"}}, container="Assembly")
        self.assertTrue(done["container_added"])
        self.assertEqual(done["container_index"], 4)
        self.assertEqual(self.doc.get("OutputGroup1", "OutputMedium4_Type"), "GeneratedFiles")
        self.assertEqual(self.doc.get("OutputGroup1", "OutputEnabled1_OutputMedium4"), "0")
        self.assertEqual(self.doc.get("OutputGroup1", "OutputEnabled3_OutputMedium4"), "1")
        self.assertEqual(self.doc.get("GeneratedFilesSettings", "AddToProject4"), "0")

    def test_a_refused_request_leaves_the_document_as_it_was(self):
        for kwargs in ({"specs": {"gerber": {"units": "mm", "format": "4:4"}, "bom": {"format": "doc"}}},
                       {"specs": {"gerber": {"format": "4:4"}}},  # the file is in inches
                       {"specs": {"gerber": {}}, "container": "PDF"},
                       {"specs": {"drill": {}}},
                       {"specs": {}, "output_folder": "a|b"}):
            specs = kwargs.pop("specs")
            with self.assertRaises(ow.OutJobError, msg=specs):
                ow.apply(self.doc, specs, **kwargs)
            self.assertEqual(self.doc.text(), self.before)

    def test_board_document_on_board_outputs(self):
        done = ow.apply(self.doc, {"gerber": {"origin": "absolute"}, "bom": {"format": "csv"}},
                        board_document="Main.PcbDoc")
        self.assertEqual(self.doc.get("OutputGroup1", "OutputDocumentPath1"), "Main.PcbDoc")
        bom_n = done["outputs"]["bom"]["index"]
        self.assertEqual(self.doc.get("OutputGroup1", f"OutputDocumentPath{bom_n}"), "")

    def test_compare_names_what_the_file_does_not_hold(self):
        done = ow.apply(self.doc, {"gerber": {"units": "mm", "format": "4:4"}})
        tampered = self.doc.text().replace("GerberUnit=Metric", "GerberUnit=Imperial")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "x.OutJob")
            with open(path, "w", encoding="cp1252", newline="") as f:
                f.write(tampered)
            diffs = ow.compare(parse_outjob(path), {"gerber": {"units": "mm", "format": "4:4"}}, done, None, None)
        self.assertEqual(len(diffs), 1)
        self.assertIn("gerber units", diffs[0])


class ToolTest(unittest.TestCase):
    """write_outjob in main.py, files only."""

    @classmethod
    def setUpClass(cls):
        import main
        cls.main = main

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.path = os.path.join(self.tmp, "Fab.OutJob")

    def call(self, **kw):
        return run(self.main.write_outjob(None, kw.pop("outjob_path", self.path), **kw))

    def test_new_file_from_preset_then_edited(self):
        out = self.call(preset="fab_jlcpcb")
        self.assertTrue(out["success"], out)
        self.assertTrue(out["created"])
        self.assertEqual(out["differences"], [])
        self.assertEqual(out["output_folder"], "JLCPCB")
        self.assertIn("jlcpcb.com", json.dumps(out["preset"]["sources"]))
        self.assertEqual(len(out["settings"]["outputs"]), 4)
        again = self.call(preset="fab_jlcpcb")
        self.assertFalse(again["success"])
        self.assertIn("exists", again["error"])
        out = self.call(gerber={"layers": ["Top Layer", "Bottom Layer"]}, output_folder="other")
        self.assertTrue(out["success"], out)
        self.assertFalse(out["created"])
        g = {o["type"]: o for o in out["settings"]["outputs"]}["Gerber"]["gerber"]
        self.assertEqual([l["name"] for l in g["plotted_layers"]], ["Top Layer", "Bottom Layer"])
        self.assertEqual(g["units"], "Metric", "kept from the preset")
        self.assertEqual(out["output_folder"], "other")
        out = self.call(preset="fab_jlcpcb", overwrite=True, pick_place={"units": "mil"})
        self.assertTrue(out["success"], out)
        p = {o["type"]: o for o in out["settings"]["outputs"]}["Pick Place"]["pick_place"]
        self.assertEqual(p["Units"], "Imperial", "a group given with a preset goes over the preset's")

    def test_refusals(self):
        self.assertIn("needs a preset", self.call(gerber={"units": "mm", "format": "4:4"})["error"])
        self.assertIn("unknown preset", self.call(preset="nope")["error"])
        self.assertIn(".OutJob", self.call(outjob_path=os.path.join(self.tmp, "x.txt"), preset="fab_jlcpcb")["error"])
        self.assertIn(".OutJob", self.call(outjob_path="Fab.OutJob", preset="fab_jlcpcb")["error"])
        self.call(preset="fab_jlcpcb")
        before = Path(self.path).read_bytes()
        self.assertIn("nothing to change", self.call()["error"])
        out = self.call(gerber={"units": "inch"})
        self.assertFalse(out["success"])
        self.assertEqual(Path(self.path).read_bytes(), before, "a refused edit writes nothing")

    def test_an_altium_file_is_edited_in_place(self):
        with open(self.path, "w", encoding="cp1252", newline="\r\n") as f:
            f.write(ALTIUM_FILE)
        before = Path(self.path).read_bytes().decode("cp1252").split("\r\n")
        out = self.call(gerber={"units": "mm", "format": "4:4"})
        self.assertTrue(out["success"], out)
        after = Path(self.path).read_bytes().decode("cp1252").split("\r\n")
        self.assertEqual(len(before), len(after))
        self.assertEqual(sum(a != b for a, b in zip(before, after)), 1)


if __name__ == "__main__":
    unittest.main()
