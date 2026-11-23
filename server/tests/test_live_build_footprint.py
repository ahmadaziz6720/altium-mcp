"""Live test of the footprint build_schematic gives a part, in a running Altium
Designer (A27): a part whose library symbol has a current footprint already,
placed with `footprint`, is left with the footprint given as its only current
one. The one the library marked loses its mark; when the symbol already holds a
model of that name it is that model that is made current, not a second one
added.

The models are read through Altium from the sheet, and from the saved sheet
file as ISCURRENT=T records. See tests/live_altium.py for how to run it. The
libraries are copies of two of the "SpiritLevel-SL1" example's (skipped when
they are not there); everything is made in a temporary folder and closed
unsaved at the end.
"""
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.live_altium import (LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close_all_under, tool)
from tests.test_live_build_focus import drop_unsaved
from tests.test_live_symbol_footprint import JUMPER, PCBLIB, PINS, SCHLIB, read_model_list, save_library

if LIVE:
    import main
    import win32api


def footprints(sheet, designator="U1"):
    """The footprints of a placed part, in the order Altium gives them:
    [(name, current)]. Read from the sheet Altium holds."""
    return [(name, current) for kind, name, _, current in read_model_list(sheet, designator, in_library=False)
            if kind == "PCBLIB"]


def current_in_file(path):
    """The footprint models of the saved sheet marked IsCurrent=T, by name: its
    records are text between a length and a NUL, with keys in mixed case."""
    text = Path(path).read_bytes().decode("latin-1")
    found = []
    for record in text.split("|RECORD=")[1:]:
        fields = {}
        for field in record.split("\x00")[0].split("|")[1:]:
            key, _, value = field.partition("=")
            fields[key.lower()] = value
        if fields.get("modeltype") == "PCBLIB" and fields.get("iscurrent") == "T":
            found.append(fields.get("modelname"))
    return found


@unittest.skipUnless(LIVE, SKIP_REASON)
@unittest.skipUnless(SCHLIB.exists() and PCBLIB.exists(), "Altium's example libraries are not there")
class LiveBuildFootprintTest(unittest.TestCase):
    def setUp(self):
        check_scripts_are_this_checkouts()
        self.tmp = Path(win32api.GetLongPathName(tempfile.mkdtemp(prefix="buildfp_live_")))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.addCleanup(close_all_under, str(self.tmp))
        self.lib = self.tmp / "Parts.SchLib"
        self.fp = self.tmp / "Footprints.PcbLib"
        shutil.copyfile(SCHLIB, self.lib)
        shutil.copyfile(PCBLIB, self.fp)

    def build(self, symbol, footprint=None, **args):
        part = {"designator": "U1", "symbol_library": str(self.lib), "symbol": symbol, "x": 1000, "y": 1000}
        if footprint:
            part["footprint"] = footprint
        out = tool(main.build_schematic(None, [part], **args))
        self.assertTrue(out.get("success"), out)
        self.addCleanup(drop_unsaved, out["sheet"])
        return out

    def two_footprint_symbol(self, name):
        """A symbol of the library with two footprints, the second the current one."""
        spec = self.tmp / "spec.txt"
        spec.write_text("\n".join([f"LIBRARY|{self.lib}", f"SYMBOL|{name}|Two|1"] + ["PIN|" + p for p in PINS] +
                                  [f"FOOTPRINT|HDR1X2|{self.fp}", f"FOOTPRINT|NT|{self.fp}|1"]) + "\n",
                        encoding="utf-8")
        out = tool(main.create_symbols_batch(None, str(spec)))
        self.assertEqual((out["created"], out["problems"]), (1, []), out)
        save_library(self.lib)
        close_all_under(str(self.tmp))

    def test_the_footprint_given_is_the_only_current_one(self):
        # The symbol's own footprint is current; a build gave it a second
        out = self.build(JUMPER, "NT")
        self.assertEqual(footprints(out["sheet"]), [("HDR1X2", False), ("NT", True)],
                         "the part has two current footprints, or the wrong one")

    def test_a_footprint_the_symbol_has_is_made_current_not_added(self):
        self.two_footprint_symbol("FPBUILD_A")
        # the library's current one is NT; HDR1X2 is asked for, in another case
        out = self.build("FPBUILD_A", "hdr1x2")
        self.assertEqual(sorted(footprints(out["sheet"])), [("HDR1X2", True), ("NT", False)],
                         "a second model was added, or both are current")
        # and the one it already has current, asked for, stays the only one
        out = self.build("FPBUILD_A", "NT")
        self.assertEqual(sorted(footprints(out["sheet"])), [("HDR1X2", False), ("NT", True)])

    def test_the_saved_sheet_has_one_current_footprint(self):
        project = self.tmp / "Target.PrjPcb"
        self.assertTrue(tool(main.create_project(None, str(project))).get("success"))
        sheet = self.tmp / "Built.SchDoc"
        self.build(JUMPER, "NT", project_path=str(project), sheet_path=str(sheet))
        self.assertEqual(current_in_file(sheet), ["NT"], "the saved sheet marks more than one footprint current")

    def test_a_symbol_without_a_footprint_takes_the_one_given(self):
        spec = self.tmp / "spec.txt"
        spec.write_text("\n".join([f"LIBRARY|{self.lib}", "SYMBOL|FPBUILD_B|Plain|1"] +
                                  ["PIN|" + p for p in PINS]) + "\n", encoding="utf-8")
        out = tool(main.create_symbols_batch(None, str(spec)))
        self.assertEqual((out["created"], out["problems"]), (1, []), out)
        save_library(self.lib)
        close_all_under(str(self.tmp))
        out = self.build("FPBUILD_B", "NT")
        self.assertEqual(footprints(out["sheet"]), [("NT", True)])

    def test_without_footprint_the_library_one_stays_current(self):
        out = self.build(JUMPER)
        self.assertEqual(footprints(out["sheet"]), [("HDR1X2", True)])
