"""Live test of edit_schematic's set_footprint, in a running Altium Designer
(A56): a placed part is given a footprint and the library it links to. The
footprint given becomes the part's only current one, linked to that library;
one the part has already is linked anew, not added a second time; the part's
other models (3D, simulation) are left as they were.

The part is placed with build_schematic on a sheet saved into a project of
its own. Its models are read through Altium from the sheet, and from the saved
sheet file. See tests/live_altium.py for how to run it. The libraries are
copies of two of the "SpiritLevel-SL1" example's (skipped when they are not
there); everything is made in a temporary folder and closed at the end.
"""
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.live_altium import LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close_all_under, tool
from tests.test_live_symbol_footprint import JUMPER, PCBLIB, SCHLIB, read_model_list

if LIVE:
    import main
    import win32api
    from schdoc_reader import read_schdoc


def models(sheet, designator="U1"):
    """The models of a placed part, read through Altium from the sheet:
    sorted (type, name, library file in upper case, current)."""
    return sorted((kind, name, library.upper(), current)
                  for kind, name, library, current in read_model_list(sheet, designator, in_library=False))


def footprints(sheet, designator="U1"):
    return [(name, library, current) for kind, name, library, current in models(sheet, designator)
            if kind == "PCBLIB"]


def saved_footprints(path):
    """The footprint models of the saved sheet (its implementation records):
    sorted (name, library file in upper case, current)."""
    found = []
    for r in read_schdoc(path)[1:]:
        if r and r.get("RECORD") == "45" and r.get("MODELTYPE", "").upper() == "PCBLIB":
            found.append((r.get("MODELNAME", ""), r.get("MODELDATAFILE0", "").upper(), r.get("ISCURRENT") == "T"))
    return sorted(found)


@unittest.skipUnless(LIVE, SKIP_REASON)
@unittest.skipUnless(SCHLIB.exists() and PCBLIB.exists(), "Altium's example libraries are not there")
class LiveSetFootprintTest(unittest.TestCase):
    def setUp(self):
        check_scripts_are_this_checkouts()
        self.tmp = Path(win32api.GetLongPathName(tempfile.mkdtemp(prefix="setfp_live_")))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.addCleanup(close_all_under, str(self.tmp))
        # The sheet before its project
        self.sheet = self.tmp / "Placed.SchDoc"
        self.addCleanup(close_all_under, str(self.sheet))
        self.lib = self.tmp / "Parts.SchLib"
        self.other = self.tmp / "Other.PcbLib"
        shutil.copyfile(SCHLIB, self.lib)
        shutil.copyfile(PCBLIB, self.other)
        project = self.tmp / "Target.PrjPcb"
        self.assertTrue(tool(main.create_project(None, str(project))).get("success"))
        part = {"designator": "U1", "symbol_library": str(self.lib), "symbol": JUMPER, "x": 1000, "y": 1000}
        out = tool(main.build_schematic(None, [part], project_path=str(project), sheet_path=str(self.sheet)))
        self.assertTrue(out.get("success"), out)
        self.before = models(self.sheet)
        # The part as its library symbol gives it: HDR1X2, current, and models of other kinds
        self.assertEqual([(n, c) for n, _, c in footprints(self.sheet)], [("HDR1X2", True)])
        self.assertTrue([m for m in self.before if m[0] != "PCBLIB"], self.before)

    def set_footprint(self, *operations):
        return tool(main.edit_schematic(None, str(self.sheet), list(operations), save=True))

    def others(self, found):
        return [m for m in found if m[0] != "PCBLIB"]

    def test_the_footprint_set_is_the_only_current_one_and_linked(self):
        out = self.set_footprint({"op": "set_footprint", "designator": "U1", "footprint": "NT",
                                  "library": str(self.other)})
        self.assertTrue(out.get("success"), out)
        self.assertEqual(out.get("applied"), 1, out)
        found = footprints(self.sheet)
        self.assertEqual([(n, c) for n, _, c in found], [("HDR1X2", False), ("NT", True)],
                         "not the footprint given as the only current one")
        self.assertEqual(found[1][1], str(self.other).upper(), "the footprint is not linked to the library given")
        self.assertEqual(self.others(models(self.sheet)), self.others(self.before), "other models changed")
        self.assertEqual(saved_footprints(self.sheet), [found[0], ("NT", str(self.other).upper(), True)],
                         "the saved sheet does not hold the footprint given, linked to its library, "
                         "as the only current one")

    def test_a_footprint_the_part_has_is_linked_anew_not_added(self):
        out = self.set_footprint({"op": "set_footprint", "designator": "u1", "footprint": "hdr1x2",
                                  "library": str(self.other)},
                                 {"op": "set_footprint", "designator": "U9", "footprint": "NT",
                                  "library": str(self.other)})
        self.assertEqual(out.get("applied"), 1, out)
        self.assertEqual(len(out.get("errors", [])), 1, out)
        self.assertIn("no component U9", out["errors"][0])
        self.assertEqual(footprints(self.sheet), [("HDR1X2", str(self.other).upper(), True)],
                         "a second model was added, or the library was not changed")
        self.assertEqual(saved_footprints(self.sheet), [("HDR1X2", str(self.other).upper(), True)])
        self.assertEqual(self.others(models(self.sheet)), self.others(self.before), "other models changed")

    def test_back_to_the_first_one(self):
        self.set_footprint({"op": "set_footprint", "designator": "U1", "footprint": "NT",
                            "library": str(self.other)})
        out = self.set_footprint({"op": "set_footprint", "designator": "U1", "footprint": "HDR1X2",
                                  "library": str(self.other)})
        self.assertTrue(out.get("success"), out)
        self.assertEqual([(n, c) for n, _, c in footprints(self.sheet)], [("HDR1X2", True), ("NT", False)])
        self.assertEqual([(n, c) for n, _, c in saved_footprints(self.sheet)], [("HDR1X2", True), ("NT", False)])


if __name__ == "__main__":
    unittest.main()
