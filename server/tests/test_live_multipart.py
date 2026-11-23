"""Live test of multi-part symbols in a running Altium Designer (A45): a part
entry's `part` in build_schematic and in edit_schematic's place_component, the
parts not placed named under `warnings`, and a pin map of the placed parts'
pins alone. What was placed is read from the saved .SchDoc, not from the
tools' results.

See tests/live_altium.py for how to run it. The symbol, six parts and a pin
they share, is made in a copy of the "SpiritLevel-SL1" example's library
(skipped when it is not there), and compiled into an integrated library of its
own. All is made in a temporary folder and closed at the end.
"""
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.live_altium import LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close, close_all_under, script, tool

if LIVE:
    import main
    import win32api
    from schdoc_reader import read_schdoc
    from schematic_check import Sheet
    from tests.test_live_libraries import uninstall
    from tests.test_live_symbol_footprint import save_library

SCHLIB = Path(r"C:\Users\Public\Documents\Altium\AD25\Examples\SpiritLevel-SL1\Libraries\SpiritLevel_2E.SchLib")
SYMBOL = "MULTIPART_TEST"
LETTERS = "ABCDEF"


def numbers(part):
    """The pins one placed part shows: its own two and the shared one."""
    return sorted([str(2 * part - 1), str(2 * part), "20"])


def saved(sheet):
    """The components of a saved sheet: sorted (designator, part, x, y,
    [(number, x, y) of the pins that part shows]), in mils."""
    out = []
    for c in Sheet(read_schdoc(sheet)).components.values():
        pins = sorted((p["name"], round(p["hot"][0], 2), round(p["hot"][1], 2)) for p in c["pins"])
        out.append((c["designator"], c["part"], *(round(v, 2) for v in c["location"]), pins))
    return sorted(out)


def map_pins(pin_map):
    """Every pin of a pin map: sorted (designator, number, x, y)."""
    return sorted((d, key.split("#")[0], round(p["x"], 2), round(p["y"], 2))
                  for d, pins in pin_map.items() for key, p in pins.items())


def file_pins(components):
    """The saved file's shown pins, in map_pins' form."""
    return sorted((d, *pin) for d, _, _, _, pins in components for pin in pins)


def focused_project():
    return script("ResultText := GetWorkspace.DM_FocusedProject.DM_ProjectFullPath;").strip()


def compiled_components(project):
    """The designators of a project's compiled components."""
    out = script(f"""var
    P : IProject;
    D : IDocument;
    I : Integer;
    S : String;
begin
P := GetWorkspace.DM_GetProjectFromPath('{project}');
P.DM_Compile;
D := P.DM_DocumentFlattened;
S := '';
for I := 0 to D.DM_ComponentCount - 1 do
    S := S + D.DM_Components(I).DM_PhysicalDesignator + '|';
ResultText := S;
end;""")
    return [d for d in out.strip().split("|") if d]


@unittest.skipUnless(LIVE, SKIP_REASON)
@unittest.skipUnless(SCHLIB.exists(), f"Altium's example library is not at {SCHLIB}")
class LiveMultiPartTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        check_scripts_are_this_checkouts()
        # Altium is given the long path: the one it reports back
        cls.tmp = Path(win32api.GetLongPathName(tempfile.mkdtemp(prefix="multipart_live_")))
        cls.addClassCleanup(shutil.rmtree, cls.tmp, ignore_errors=True)
        cls.addClassCleanup(close_all_under, str(cls.tmp))
        cls.lib = cls.tmp / "Multi.SchLib"
        shutil.copyfile(SCHLIB, cls.lib)
        # Each part's pins at a height of its own, so a wrong part shows in the places
        pins = []
        for part in range(1, 7):
            pins += [f"PIN|{2 * part - 1}|IN{part}|eElectricInput|eRotate180|0|{-100 * part}|{part}",
                     f"PIN|{2 * part}|OUT{part}|eElectricOutput|eRotate0|400|{-100 * part}|{part}"]
        pins.append("PIN|20|VCC|eElectricPower|eRotate90|200|100|0")
        spec = cls.tmp / "spec.txt"
        # LIBRARY: nothing is made unless that copy is the focused library
        spec.write_text("\n".join([f"LIBRARY|{cls.lib}", f"SYMBOL|{SYMBOL}|Six parts|6", *pins]) + "\n",
                        encoding="utf-8")
        out = tool(main.create_symbols_batch(None, str(spec)))
        if out.get("created") != 1 or out.get("failed") or out.get("problems"):
            raise AssertionError(f"the test's symbol was not made: {out}")
        save_library(cls.lib)
        pkg = cls.tmp / "Multi.LibPkg"
        pkg.write_text("[Design]\r\nVersion=1.0\r\n\r\n[Document1]\r\nDocumentPath=Multi.SchLib\r\n",
                       encoding="ascii")
        output = script(f"Obj1 := GetWorkspace.DM_OpenProject('{pkg}', True);\n"
                        "Obj1.DM_Compile;\nResultText := Obj1.DM_GetOutputPath;").strip()
        cls.intlib = Path(output) / "Multi.IntLib"
        # Altium installs a library it compiles
        uninstall(cls.intlib)
        close_all_under(str(cls.tmp))
        if not cls.intlib.is_file():
            raise AssertionError(f"Altium compiled no integrated library from {pkg}")

    def setUp(self):
        self.folder = self.tmp / self._testMethodName
        self.project = self.folder / "Multi.PrjPcb"
        self.assertTrue(tool(main.create_project(None, str(self.project))).get("success"))
        self.sheet = self.folder / "Multi.SchDoc"
        self.addCleanup(close_all_under, str(self.folder))

    def build(self, entries, library=None, **args):
        parts = [dict({"designator": "U1", "symbol_library": str(library or self.lib), "symbol": SYMBOL}, **e)
                 for e in entries]
        # A new sheet goes into the focused project before build_schematic takes
        # it out (A26): never into a project that is not the test's
        focused = focused_project()
        self.assertTrue(focused == "Free Documents" or focused.lower().startswith(str(self.tmp).lower()),
                        f"not run: the focused project is not the test's: {focused}")
        with mock.patch.object(main, "_data_dir", return_value=self.folder / "data"):
            out = tool(main.build_schematic(None, parts, project_path=str(self.project),
                                            sheet_path=str(self.sheet), **args))
        if not out.get("success"):
            # A build with a part missing leaves its sheet open, unsaved
            unsaved = re.search(r'"sheet": *"([^"\\/]+)"', json.dumps(out).replace('\\"', '"'))
            if unsaved:
                self.addCleanup(close, unsaved.group(1))
        return out

    def edit(self, operations):
        return tool(main.edit_schematic(None, str(self.sheet), operations, save=True))

    def assert_unplaced(self, out, letters, designator="U1"):
        warnings = [w for w in out.get("warnings", []) if w.startswith(f"{designator} ")]
        self.assertEqual(len(warnings), 1, f"silent on parts {', '.join(letters)} of {designator}, "
                                           f"which are not placed: {json.dumps(out)}")
        self.assertIn(", ".join(letters), warnings[0])
        for placed in set(LETTERS) - set(letters):
            self.assertNotRegex(warnings[0].split(":", 1)[1], rf"\b{placed}\b")

    def test_no_part_places_a_and_names_the_others(self):
        out = self.build([{"x": 2000, "y": 5000}])
        self.assertTrue(out.get("success"), out)
        self.assert_unplaced(out, "BCDEF")
        got = saved(self.sheet)
        self.assertEqual([c[:4] for c in got], [("U1", 1, 2000, 5000)])
        self.assertEqual(sorted(n for n, _, _ in got[0][4]), numbers(1))
        self.assertEqual(map_pins(out["pin_map"]), file_pins(got), "pin_map has pins of parts not placed")
        self.assertEqual(out["pins"], 3)

    def test_six_parts_by_letter_and_number_each_at_its_own_place(self):
        entries = [{"x": 2000, "y": 6000},
                   {"x": 4000, "y": 6000, "part": "B"},
                   {"x": 6000.5, "y": 6000, "part": "c", "orientation": 1},
                   {"x": 2000, "y": 3000, "part": 4, "mirror": 1},
                   {"x": 4000, "y": 3000, "part": "5", "orientation": 2},
                   {"x": 6000, "y": 3000, "part": "F", "orientation": 3, "mirror": 1}]
        out = self.build(entries)
        self.assertTrue(out.get("success"), out)
        got = saved(self.sheet)
        self.assertEqual([c[:4] for c in got],
                         [("U1", n, e["x"], e["y"]) for n, e in enumerate(entries, 1)], "not the parts asked")
        for c in got:
            self.assertEqual(sorted(n for n, _, _ in c[4]), numbers(c[1]))
        self.assertEqual(map_pins(out["pin_map"]), file_pins(got))
        self.assertNotIn("warnings", out)
        self.assertEqual(compiled_components(self.project), ["U1"], "the parts are not one component")

    def test_with_wires_the_warning_and_the_count_of_placed_pins(self):
        out = self.build([{"x": 2000, "y": 5000}, {"x": 4000, "y": 5000, "part": "D"},
                          {"designator": "U2", "x": 6000, "y": 5000, "part": "B"}],
                         wires=[[1000, 1000, 2000, 1000]])
        self.assertTrue(out.get("success"), out)
        self.assert_unplaced(out, "BCEF")
        self.assert_unplaced(out, "ACDEF", "U2")
        self.assertEqual(out["pin_counts"], {"U1": 6, "U2": 3})
        written = json.loads(Path(out["pin_map_file"]).read_text(encoding="utf-8"))["pin_map"]
        self.assertEqual(map_pins(written), file_pins(saved(self.sheet)))

    def test_a_symbol_shown_at_another_part_still_places_a(self):
        shown = self.folder / "Shown.SchLib"
        shutil.copyfile(self.lib, shown)
        part = script(f"""var
    D : ISch_Lib;
    S : IServerDocument;
    It : ISch_Iterator;
    C : ISch_Component;
begin
S := Client.OpenDocument('SchLib', '{shown}');
Client.ShowDocument(S);
D := SchServer.GetSchDocumentByPath('{shown}');
It := D.SchLibIterator_Create;
It.AddFilter_ObjectSet(MkSet(eSchComponent));
C := It.FirstSchObject;
while C <> nil do
begin
    if C.LibReference = '{SYMBOL}' then
    begin
        D.CurrentSchComponent := C;
        C.CurrentPartID := 3;
        ResultText := IntToStr(C.CurrentPartID);
    end;
    C := It.NextSchObject;
end;
D.SchIterator_Destroy(It);
end;""")
        self.assertEqual(part.strip(), "3")
        out = self.build([{"x": 2000, "y": 5000}], library=shown)
        self.assertTrue(out.get("success"), out)
        got = saved(self.sheet)
        self.assertEqual([c[:2] for c in got], [("U1", 1)])
        self.assertEqual(sorted(n for n, _, _ in got[0][4]), numbers(1), "the pins are not part A's")
        self.assertEqual(map_pins(out["pin_map"]), file_pins(got))
        self.assert_unplaced(out, "BCDEF")

    def test_a_part_the_symbol_does_not_have_is_not_placed(self):
        for library in (self.lib, self.intlib):
            out = self.build([{"x": 2000, "y": 5000, "part": "G"},
                              {"designator": "R1", "symbol": "RES", "symbol_library": str(self.lib),
                               "x": 1000, "y": 1000, "part": "B"}], library=library)
            self.assertFalse(out.get("success"), out)
            text = json.dumps(out).replace('\\"', '"')
            self.assertIn(f"{SYMBOL} has no part G (its parts are A to F)", text)
            self.assertIn("RES has no part B (it has one part)", text)
            self.assertIn('"parts": 0,', text)
            self.assertIn('"pins": 0,', text, "a refused part was left on the sheet")

    def test_parts_from_an_intlib(self):
        out = self.build([{"x": 2000, "y": 5000}, {"x": 4000, "y": 5000, "part": "C", "orientation": 1}],
                         library=self.intlib)
        self.assertTrue(out.get("success"), out)
        self.assert_unplaced(out, "BDEF")
        got = saved(self.sheet)
        self.assertEqual([c[:4] for c in got], [("U1", 1, 2000, 5000), ("U1", 3, 4000, 5000)])
        for c in got:
            self.assertEqual(sorted(n for n, _, _ in c[4]), numbers(c[1]))
        self.assertEqual(map_pins(out["pin_map"]), file_pins(got))

    def test_place_component_takes_a_part(self):
        self.assertTrue(self.build([{"designator": "R1", "symbol": "RES", "x": 1000, "y": 1000}]).get("success"))
        place = {"op": "place_component", "symbol": SYMBOL, "designator": "U7", "y": 5000}
        out = self.edit([dict(place, library=str(self.lib), x=2000)])
        self.assertEqual(out.get("applied"), 1, out)
        self.assert_unplaced(out, "BCDEF", "U7")
        out = self.edit([dict(place, library=str(self.lib), x=4000, part="b", rotation=90),
                         dict(place, library=str(self.intlib), x=6000, part=6, mirror=True)])
        self.assertEqual(out.get("applied"), 2, out)
        # what is already on the sheet counts as placed
        self.assert_unplaced(out, "CDE", "U7")
        got = [c for c in saved(self.sheet) if c[0] == "U7"]
        self.assertEqual([c[:4] for c in got],
                         [("U7", 1, 2000, 5000), ("U7", 2, 4000, 5000), ("U7", 6, 6000, 5000)])
        for c in got:
            self.assertEqual(sorted(n for n, _, _ in c[4]), numbers(c[1]))
        out = self.edit([dict(place, library=str(self.intlib), x=8000, part="G"),
                         dict(place, library=str(self.lib), x=8000, part="H")])
        self.assertEqual(out.get("applied"), 0, out)
        self.assertEqual(len([e for e in out.get("errors", []) if "has no part" in e]), 2, out)
        self.assertEqual([c for c in saved(self.sheet) if c[0] == "U7"], got, "a refused part was left on the sheet")

    def test_parts_by_the_build_and_by_place_component_compile_as_one(self):
        # A77: the two tools filled a placed part's library fields differently
        out = self.build([{"x": 2000, "y": 5000, "part": "B"}])
        self.assertTrue(out.get("success"), out)
        out = self.edit([{"op": "place_component", "library": str(self.lib), "symbol": SYMBOL,
                          "designator": "U1", "x": 4000, "y": 5000, "part": "C"}])
        self.assertEqual(out.get("applied"), 1, out)
        fields = sorted((r.get("CURRENTPARTID"), r.get("DESIGNITEMID"), r.get("SOURCELIBRARYNAME"),
                         r.get("LIBRARYPATH"), r.get("LIBREFERENCE"))
                        for r in read_schdoc(self.sheet) if r and r.get("RECORD") == "1")
        self.assertEqual(len(fields), 2, fields)
        self.assertEqual(compiled_components(self.project), ["U1"],
                         f"the parts are not one component; their library fields "
                         f"(part, DESIGNITEMID, SOURCELIBRARYNAME, LIBRARYPATH, LIBREFERENCE): {fields}")
        self.assertEqual(fields[0][1:], fields[1][1:], "the two tools fill the library fields differently")

    def test_an_edit_with_a_refused_part_is_one_undo_step(self):
        self.assertTrue(self.build([{"designator": "R1", "symbol": "RES", "x": 1000, "y": 1000}]).get("success"))
        place = {"op": "place_component", "library": str(self.intlib), "symbol": SYMBOL, "designator": "U7",
                 "y": 5000}
        out = self.edit([dict(place, x=2000, part="B"), dict(place, x=4000, part="G")])
        self.assertEqual(out.get("applied"), 1, out)
        self.assertEqual([c[:2] for c in saved(self.sheet)], [("R1", 1), ("U7", 2)])
        script(f"Obj1 := Client.GetDocumentByPath('{self.sheet}');\nClient.ShowDocument(Obj1);\n"
               "ResetParameters;\nRunProcess('Sch:Undo');\n"
               "Obj1.SetModified(True);\nObj1.DoFileSave('');\nResultText := 'undone';")
        self.assertEqual([c[:2] for c in saved(self.sheet)], [("R1", 1)],
                         "one undo did not take back the whole edit")


if __name__ == "__main__":
    unittest.main()
