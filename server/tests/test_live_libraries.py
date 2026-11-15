"""Live test of parts from integrated libraries in a running Altium Designer
(A15): build_schematic and edit_schematic's place_component take a part from
an .IntLib as they take one from a .SchLib, and get_installed_libraries lists
the libraries Altium has installed. Each placed part is read back through
Altium: its designator, library reference, the library it is linked to, its
place, and the footprints it carries, compared with the same symbol in the
library the integrated library was compiled from.

See tests/live_altium.py for how to run it. Everything is made in a
temporary folder and closed unsaved at the end. The integrated library is
compiled there from copies of the libraries of the "SpiritLevel-SL1" example
Altium installs (Altium installs a library it compiles; the test uninstalls
it again), and a copy of the "Atmel QTouch" integrated library Altium ships
is used as it comes (skipped when they are not there).
"""
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.live_altium import LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close, close_all_under, script, tool

if LIVE:
    import main
    import win32api
    from tests.test_live_symbol_footprint import read_models

EXAMPLE_LIBS = Path(r"C:\Users\Public\Documents\Altium\AD25\Examples\SpiritLevel-SL1\Libraries")
SCHLIB = EXAMPLE_LIBS / "SpiritLevel_2E.SchLib"
PCBLIB = EXAMPLE_LIBS / "Spirit_Level_Project.PcbLib"
QTOUCH = Path(r"C:\Users\Public\Documents\Altium\AD25\Library\QTouch\Atmel QTouch.IntLib")
# A symbol of the example with a footprint of its own
JUMPER = "Jumper, 2-Pin"


def installed():
    """The libraries Altium has installed, read through Altium, lower case."""
    out = script("IntMan := IntegratedLibraryManager;\nS1 := '';\n"
                 "for I1 := 0 to IntMan.InstalledLibraryCount - 1 do\n"
                 "    S1 := S1 + IntMan.InstalledLibraryPath(I1) + '|';\nResultText := S1;")
    return [p.lower() for p in out.strip().split("|") if p]


def uninstall(path):
    script(f"IntMan := IntegratedLibraryManager;\nIntMan.UninstallLibrary('{path}');\nResultText := 'done';")


def compile_intlib(folder):
    """An .IntLib compiled by Altium from copies of the example's symbol and
    footprint libraries, uninstalled again; returns its path."""
    shutil.copyfile(SCHLIB, folder / "Parts.SchLib")
    shutil.copyfile(PCBLIB, folder / "Parts.PcbLib")
    pkg = folder / "Parts.LibPkg"
    pkg.write_text("[Design]\r\nVersion=1.0\r\n\r\n[Document1]\r\nDocumentPath=Parts.SchLib\r\n\r\n"
                   "[Document2]\r\nDocumentPath=Parts.PcbLib\r\n", encoding="ascii")
    out = script(f"Obj1 := GetWorkspace.DM_OpenProject('{pkg}', True);\n"
                 "Obj1.DM_Compile;\nResultText := Obj1.DM_GetOutputPath;").strip()
    intlib = Path(out) / "Parts.IntLib"
    uninstall(intlib)
    script(f"Obj1 := GetWorkspace.DM_GetProjectFromPath('{pkg}');\n"
           "if Obj1 <> nil then GetWorkspace.DM_CloseProject(Obj1.DM_ProjectFullPath);\nResultText := 'closed';")
    if not intlib.is_file():
        raise AssertionError(f"Altium compiled no integrated library from {pkg}")
    return intlib


def placed(sheet):
    """The components on an open sheet, read through Altium: {designator:
    {lib_ref, library, design_item_id, x, y, orientation, mirrored, comment}},
    x and y in mils."""
    out = script(f"""var
    D : ISch_Document;
    It : ISch_Iterator;
    C : ISch_Component;
    S : String;
begin
D := SchServer.GetSchDocumentByPath('{sheet}');
S := '';
It := D.SchIterator_Create;
It.AddFilter_ObjectSet(MkSet(eSchComponent));
C := It.FirstSchObject;
while C <> nil do
begin
    S := S + C.Designator.Text + '|' + C.LibReference + '|' + C.SourceLibraryName + '|' + C.DesignItemId + '|' +
         IntToStr(C.Location.X) + '|' + IntToStr(C.Location.Y) + '|' + IntToStr(C.Orientation) + '|' +
         BoolToStr(C.IsMirrored, True) + '|' + C.Comment.Text + #13#10;
    C := It.NextSchObject;
end;
D.SchIterator_Destroy(It);
ResultText := S;
end;""")
    parts = {}
    for line in out.splitlines():
        if not line.strip():
            continue
        des, ref, lib, item, x, y, rot, mir, comment = line.split("|", 8)
        parts[des] = {"lib_ref": ref, "library": lib, "design_item_id": item, "x": int(x) / 10000,
                      "y": int(y) / 10000, "orientation": int(rot), "mirrored": mir == "True", "comment": comment}
    return parts


def footprints(models):
    """The footprints of read_models' result: {name: current}."""
    return {name: v[1] for (kind, name), v in models.items() if kind == "PCBLIB"}


@unittest.skipUnless(LIVE, SKIP_REASON)
class LiveIntLibTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        check_scripts_are_this_checkouts()
        for f in (SCHLIB, PCBLIB, QTOUCH):
            if not f.is_file():
                raise unittest.SkipTest(f"{f} is not installed")
        # Altium is given the long path: the one it reports back
        cls.tmp = Path(win32api.GetLongPathName(tempfile.mkdtemp(prefix="intlib_live_")))
        cls.addClassCleanup(shutil.rmtree, cls.tmp, ignore_errors=True)
        cls.addClassCleanup(close_all_under, str(cls.tmp))
        cls.intlib = compile_intlib(cls.tmp)
        cls.addClassCleanup(uninstall, cls.intlib)
        cls.qtouch = cls.tmp / "QTouch.IntLib"
        shutil.copyfile(QTOUCH, cls.qtouch)
        cls.schlib = cls.tmp / "Parts.SchLib"
        # The footprints the symbol carries in the library the IntLib was
        # compiled from
        cls.jumper_footprints = footprints(read_models(cls.schlib, JUMPER))
        close_all_under(str(cls.tmp))

    def test_build_schematic_from_intlibs(self):
        parts = [{"designator": "J1", "symbol_library": str(self.intlib), "symbol": JUMPER, "x": 1000, "y": 2000,
                  "orientation": 1, "mirror": 1, "comment": "Link"},
                 {"designator": "S1", "symbol_library": str(self.qtouch), "symbol": "QTouchButton",
                  "x": 3000, "y": 2000},
                 # a part from a .SchLib between them, as before
                 {"designator": "R1", "symbol_library": str(self.schlib), "symbol": "RES", "x": 2000, "y": 1000},
                 {"designator": "J2", "symbol_library": str(self.intlib), "symbol": JUMPER, "x": 1500.5,
                  "y": 1000}]
        out = tool(main.build_schematic(None, parts))
        self.assertTrue(out.get("success"), out)
        sheet = out["sheet"]
        self.addCleanup(close, sheet)
        self.assertEqual(out["parts"], 4, out)
        self.assertEqual(sorted(out["pin_map"]), ["J1", "J2", "R1", "S1"], out)
        got = placed(sheet)
        self.assertEqual(sorted(got), ["J1", "J2", "R1", "S1"], got)
        self.assertEqual(got["J1"]["lib_ref"], JUMPER)
        self.assertEqual(got["J1"]["library"].lower(), "parts.intlib")
        self.assertEqual(got["J1"]["design_item_id"], JUMPER, "the part is not linked to its IntLib entry")
        self.assertEqual((got["J1"]["x"], got["J1"]["y"], got["J1"]["orientation"], got["J1"]["mirrored"]),
                         (1000, 2000, 1, True))
        self.assertEqual(got["J1"]["comment"], "Link")
        self.assertEqual((got["J2"]["x"], got["J2"]["y"]), (1500.5, 1000))
        self.assertEqual((got["S1"]["lib_ref"], got["S1"]["library"].lower()), ("QTouchButton", "qtouch.intlib"))
        self.assertEqual(got["R1"]["lib_ref"], "RES")
        self.assertTrue(self.jumper_footprints, "the example's symbol has no footprint to compare")
        self.assertEqual(footprints(read_models(sheet, "J1", in_library=False)), self.jumper_footprints,
                         "the part placed from the IntLib does not carry its footprints")

    def test_part_missing_from_an_intlib_is_reported(self):
        parts = [{"designator": "U1", "symbol_library": str(self.intlib), "symbol": "NO_SUCH_PART",
                  "x": 1000, "y": 1000},
                 {"designator": "J1", "symbol_library": str(self.intlib), "symbol": JUMPER, "x": 2000, "y": 1000}]
        out = tool(main.build_schematic(None, parts))
        # The bridge's failure comes back as the error text, the build's
        # result in it, as for a part missing from a .SchLib
        text = json.dumps(out).replace('\\"', '"')
        sheet = re.search(r'"sheet": "([^"]+)"', text)
        if sheet:
            self.addCleanup(close, sheet.group(1))
        self.assertFalse(out.get("success"), out)
        self.assertRegex(text, r'"missing_parts": \["U1: NO_SUCH_PART not found in ', out)
        self.assertIn('"parts": 1,', text, out)
        # an IntLib that is not there is refused before Altium is called
        out = tool(main.build_schematic(None, [dict(parts[1], symbol_library=str(self.tmp / "None.IntLib"))]))
        self.assertFalse(out.get("success"), out)

    def test_edit_schematic_places_from_an_intlib(self):
        prj = self.tmp / "Edit.PrjPcb"
        self.assertTrue(tool(main.create_project(None, str(prj)))["success"])
        sheet = self.tmp / "Edit.SchDoc"
        out = tool(main.build_schematic(None, [{"designator": "R1", "symbol_library": str(self.schlib),
                                                "symbol": "RES", "x": 1000, "y": 1000}],
                                        project_path=str(prj), sheet_path=str(sheet)))
        self.assertTrue(out.get("success"), out)
        ops = [{"op": "place_component", "library": str(self.intlib), "symbol": JUMPER, "designator": "J5",
                "x": 50.8, "y": 25.4, "rotation": 90, "mirror": True, "comment": "Placed"},
               {"op": "place_component", "library": str(self.qtouch), "symbol": "SmallQTouchWheel",
                "designator": "S5", "x": 76.2, "y": 25.4},
               {"op": "place_component", "library": str(self.intlib), "symbol": "NO_SUCH_PART",
                "designator": "U9", "x": 10, "y": 10}]
        out = tool(main.edit_schematic(None, str(sheet), ops, unit="mm", save=True))
        self.assertEqual(out.get("applied"), 2, out)
        self.assertEqual(len(out.get("errors", [])), 1, out)
        self.assertIn("NO_SUCH_PART", out["errors"][0])
        got = placed(sheet)
        self.assertEqual(sorted(got), ["J5", "R1", "S5"], got)
        self.assertEqual((got["J5"]["lib_ref"], got["J5"]["library"].lower(), got["J5"]["design_item_id"]),
                         (JUMPER, "parts.intlib", JUMPER))
        self.assertEqual((got["J5"]["x"], got["J5"]["y"], got["J5"]["orientation"], got["J5"]["mirrored"]),
                         (2000, 1000, 1, True))
        self.assertEqual(got["J5"]["comment"], "Placed")
        self.assertEqual(got["S5"]["library"].lower(), "qtouch.intlib")
        self.assertEqual(footprints(read_models(str(sheet), "J5", in_library=False)), self.jumper_footprints)
        # saved: the file holds the parts after Altium opens it anew
        close_all_under(str(self.tmp))
        script(f"Obj1 := Client.OpenDocument('SCH', '{sheet}');\nResultText := 'open';")
        self.assertEqual(sorted(placed(sheet)), ["J5", "R1", "S5"])

    def test_an_edit_placing_from_an_intlib_is_one_undo_step(self):
        prj = self.tmp / "Undo.PrjPcb"
        self.assertTrue(tool(main.create_project(None, str(prj)))["success"])
        sheet = self.tmp / "Undo.SchDoc"
        out = tool(main.build_schematic(None, [{"designator": "R1", "symbol_library": str(self.schlib),
                                                "symbol": "RES", "x": 1000, "y": 1000}],
                                        project_path=str(prj), sheet_path=str(sheet)))
        self.assertTrue(out.get("success"), out)
        ops = [{"op": "place_component", "library": str(self.qtouch), "symbol": "QTouchButton",
                "designator": "S1", "x": 3000, "y": 1000},
               {"op": "add_wire", "points": [[100, 100], [500, 100]]}]
        out = tool(main.edit_schematic(None, str(sheet), ops))
        self.assertEqual(out.get("applied"), 2, out)
        self.assertEqual(sorted(placed(sheet)), ["R1", "S1"])
        script(f"Obj1 := Client.GetDocumentByPath('{sheet}');\nClient.ShowDocument(Obj1);\n"
               "ResetParameters;\nRunProcess('Sch:Undo');\nResultText := 'undone';")
        wires = script(f"""var
    D : ISch_Document;
    It : ISch_Iterator;
    O : ISch_GraphicalObject;
    N : Integer;
begin
D := SchServer.GetSchDocumentByPath('{sheet}');
N := 0;
It := D.SchIterator_Create;
It.AddFilter_ObjectSet(MkSet(eWire));
O := It.FirstSchObject;
while O <> nil do
begin
    N := N + 1;
    O := It.NextSchObject;
end;
D.SchIterator_Destroy(It);
ResultText := IntToStr(N);
end;""").strip()
        self.assertEqual((sorted(placed(sheet)), wires), (["R1"], "0"),
                         "one undo did not take back the whole edit, the placed part with it")

    def test_get_installed_libraries(self):
        self.assertNotIn(str(self.qtouch).lower(), installed())
        script(f"IntMan := IntegratedLibraryManager;\nIntMan.InstallLibrary('{self.qtouch}');\nResultText := 'done';")
        self.addCleanup(uninstall, self.qtouch)
        self.assertIn(str(self.qtouch).lower(), installed(), "the test could not install the library")
        out = tool(main.get_installed_libraries(None))
        self.assertTrue(out.get("success"), out)
        listed = {lib["path"].lower(): lib for lib in out["installed"]}
        self.assertEqual(sorted(listed), sorted(installed()))
        self.assertEqual(listed[str(self.qtouch).lower()]["kind"], "IntLib")
        uninstall(self.qtouch)
        out = tool(main.get_installed_libraries(None))
        self.assertNotIn(str(self.qtouch).lower(), [lib["path"].lower() for lib in out["installed"]])


if __name__ == "__main__":
    unittest.main()
