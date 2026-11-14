"""Live test of the footprint models of a library symbol in a running Altium
Designer (A16): a FOOTPRINT record in create_symbols_batch's spec (SYMBOL and
EDITSYMBOL) and the footprints argument of create_schematic_symbol link the
symbol to PCB footprints. A symbol can carry several; one is the current one.
The result lists the models read back from the symbol in the library, and the
test reads them again through Altium after the library is saved, closed and
opened anew, and from a part placed with build_schematic that is given no
footprint.

See tests/live_altium.py for how to run it. Everything is made in a
temporary folder and closed unsaved at the end; it uses copies of a symbol
library and a footprint library of the "SpiritLevel-SL1" example Altium
installs (skipped when they are not there).
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.live_altium import (LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close, close_all_under,
                               script, tool)

if LIVE:
    import main
    import win32api

LIBS = Path(r"C:\Users\Public\Documents\Altium\AD25\Examples\SpiritLevel-SL1\Libraries")
SCHLIB = LIBS / "SpiritLevel_2E.SchLib"
PCBLIB = LIBS / "Spirit_Level_Project.PcbLib"
# A symbol of the example that has a footprint of its own, a 3D model and a
# simulation model
JUMPER = "Jumper, 2-Pin"

PINS = ["1|A|eElectricPassive|eRotate180|0|0", "2|B|eElectricPassive|eRotate0|600|0"]


def open_library(path):
    script(f"Obj1 := Client.OpenDocument('SchLib', '{path}');\n"
           "Client.ShowDocument(Obj1);\nSleep(800);\nResultText := 'open';")


def save_library(path):
    out = script(f"Obj1 := Client.GetDocumentByPath('{path}');\n"
                 "Obj1.SetModified(True);\n"
                 "ResultText := BoolToStr(Obj1.DoFileSave(''), True);").strip()
    if out != "True":
        raise AssertionError(f"could not save {path}")


def read_models(path, symbol, in_library=True):
    """The models a symbol carries, read through Altium from the file at
    path (opened when it is not): {(type, name): (library file, current)},
    the library file as Altium stores it."""
    dtype = "ISch_Lib" if in_library else "ISch_Document"
    if in_library:
        open_part = ("Obj1 := Client.OpenDocument('SchLib', '%s');\nClient.ShowDocument(Obj1);\nSleep(800);\n"
                     "D := SchServer.GetCurrentSchDocument;\nIt := D.SchLibIterator_Create;\n" % path)
    else:
        open_part = ("D := SchServer.GetSchDocumentByPath('%s');\nIt := D.SchIterator_Create;\n" % path)
    out = script("""var
    D : %s;
    It, It2 : ISch_Iterator;
    C : ISch_Component;
    Im : ISch_Implementation;
    S : String;
    Found : Boolean;
begin
%s
It.AddFilter_ObjectSet(MkSet(eSchComponent));
S := '';
Found := False;
C := It.FirstSchObject;
while C <> nil do
begin
  if (C.LibReference = '%s') or (C.Designator.Text = '%s') then
  begin
    Found := True;
    It2 := C.SchIterator_Create;
    It2.AddFilter_ObjectSet(MkSet(eImplementation));
    Im := It2.FirstSchObject;
    while Im <> nil do
    begin
      S := S + Im.ModelType + '|' + Im.ModelName + '|' + Im.ExportToParameters + #13#10;
      Im := It2.NextSchObject;
    end;
    C.SchIterator_Destroy(It2);
  end;
  C := It.NextSchObject;
end;
D.SchIterator_Destroy(It);
if not Found then S := 'NOT FOUND';
ResultText := S;
end;""" % (dtype, open_part, symbol, symbol))
    if out.strip() == "NOT FOUND":
        raise AssertionError(f"{symbol} is not in {path}")
    models = {}
    for line in out.splitlines():
        if not line.strip():
            continue
        kind, name, params = line.split("|", 2)
        rec = dict(p.split("=", 1) for p in params.split("|") if "=" in p)
        models[(kind.upper(), name)] = (rec.get("MODELDATAFILE0", ""), rec.get("ISCURRENT") == "T")
    return models


class _Temp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        check_scripts_are_this_checkouts()

    def setUp(self):
        # Altium is given the long path: the one it reports back
        self.tmp = Path(win32api.GetLongPathName(tempfile.mkdtemp(prefix="footprint_live_")))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        # Everything opened under it, closed unsaved
        self.addCleanup(close_all_under, str(self.tmp))
        self.lib = self.tmp / "Parts.SchLib"
        self.fp = self.tmp / "Footprints.PcbLib"
        shutil.copyfile(SCHLIB, self.lib)
        shutil.copyfile(PCBLIB, self.fp)

    def pcb_models(self, models):
        """Only the footprints (PCBLIB models) of a models dict, by name."""
        return {name: v for (kind, name), v in models.items() if kind == "PCBLIB"}

    def reopen(self):
        """Save the symbol library, close it, and read it from the file."""
        save_library(self.lib)
        close_all_under(str(self.tmp))


@unittest.skipUnless(LIVE, SKIP_REASON)
@unittest.skipUnless(SCHLIB.exists() and PCBLIB.exists(), f"Altium's example libraries are not at {LIBS}")
class LiveSymbolFootprintTest(_Temp):
    def batch(self, lines):
        spec = self.tmp / "spec.txt"
        spec.write_text("\n".join([f"LIBRARY|{self.lib}"] + lines) + "\n", encoding="utf-8")
        return tool(main.create_symbols_batch(None, str(spec)))

    def test_batch_symbol_with_two_footprints(self):
        out = self.batch(["SYMBOL|FPTEST_A|Two footprints|1"] +
                         ["PIN|" + p for p in PINS] +
                         [f"FOOTPRINT|HDR1X2|{self.fp}", f"FOOTPRINT|NT|{self.fp}|1"])
        self.assertEqual(out["created"], 1, out)
        self.assertEqual(out["failed"], [], out)
        self.assertEqual(out["problems"], [], out)
        # The result is the symbol's models read from the library, the one
        # asked to be current marked
        models = out["footprints"][0]
        self.assertEqual(models["symbol"], "FPTEST_A")
        self.assertEqual({m["model"]: (m["library"].lower(), m["current"]) for m in models["models"]},
                         {"HDR1X2": (str(self.fp).lower(), False), "NT": (str(self.fp).lower(), True)}, out)
        # and so is the library Altium holds, and the file it saves
        read = self.pcb_models(read_models(self.lib, "FPTEST_A"))
        self.assertEqual({n: (v[0].lower(), v[1]) for n, v in read.items()},
                         {"HDR1X2": (str(self.fp).lower(), False), "NT": (str(self.fp).lower(), True)})
        self.reopen()
        read = self.pcb_models(read_models(self.lib, "FPTEST_A"))
        self.assertEqual({n: (v[0].lower(), v[1]) for n, v in read.items()},
                         {"HDR1X2": (str(self.fp).lower(), False), "NT": (str(self.fp).lower(), True)},
                         "the saved library lost the models")

    def test_first_footprint_is_current_when_none_says_so(self):
        out = self.batch(["SYMBOL|FPTEST_B|First|1"] + ["PIN|" + p for p in PINS] +
                         [f"FOOTPRINT|NT|{self.fp}", f"FOOTPRINT|HDR1X2|{self.fp}"])
        self.assertEqual(out["problems"], [], out)
        self.assertEqual({m["model"]: m["current"] for m in out["footprints"][0]["models"]},
                         {"NT": True, "HDR1X2": False}, out)

    def test_footprint_without_a_library_is_a_link_by_name(self):
        out = self.batch(["SYMBOL|FPTEST_C|By name|1"] + ["PIN|" + p for p in PINS] + ["FOOTPRINT|HDR1X2"])
        self.assertEqual(out["problems"], [], out)
        self.assertEqual(out["footprints"][0]["models"], [{"model": "HDR1X2", "library": "", "current": True}], out)
        self.reopen()
        read = self.pcb_models(read_models(self.lib, "FPTEST_C"))
        self.assertEqual(read, {"HDR1X2": ("", True)})

    def test_editsymbol_adds_and_replaces_without_touching_other_models(self):
        before = read_models(self.lib, JUMPER)
        own = self.pcb_models(before)
        self.assertEqual(list(own), ["HDR1X2"], "the example symbol changed")
        others = {k: v for k, v in before.items() if k[0] != "PCBLIB"}
        self.assertTrue(others, "the example symbol has a 3D and a simulation model")

        # An added footprint is not current: the symbol has one already
        out = self.batch([f"EDITSYMBOL|{JUMPER}", f"FOOTPRINT|NT|{self.fp}"])
        self.assertEqual(out["edited"], 1, out)
        self.assertEqual(out["problems"], [], out)
        self.assertEqual({m["model"]: m["current"] for m in out["footprints"][0]["models"]},
                         {"HDR1X2": True, "NT": False}, out)
        # The same name again changes it, it does not add one; asked current,
        # it takes the mark from the other
        out = self.batch([f"EDITSYMBOL|{JUMPER}", f"FOOTPRINT|NT|{self.fp}|1"])
        self.assertEqual(out["problems"], [], out)
        self.assertEqual({m["model"]: m["current"] for m in out["footprints"][0]["models"]},
                         {"HDR1X2": False, "NT": True}, out)
        self.reopen()
        after = read_models(self.lib, JUMPER)
        self.assertEqual({n: v[1] for n, v in self.pcb_models(after).items()}, {"HDR1X2": False, "NT": True})
        self.assertEqual({k: v for k, v in after.items() if k[0] != "PCBLIB"}, others,
                         "the 3D and simulation models were changed")

    def test_refused_records_change_nothing(self):
        for bad, text in ((["SYMBOL|FPTEST_X|x|1"] + ["PIN|" + p for p in PINS] +
                           [f"FOOTPRINT|A|{self.fp}|1", f"FOOTPRINT|B|{self.fp}|1"], "current"),
                          (["SYMBOL|FPTEST_X|x|1"] + ["PIN|" + p for p in PINS] +
                           [f"FOOTPRINT|A|{self.tmp / 'None.PcbLib'}"], "not a file"),
                          (["SYMBOL|FPTEST_X|x|1"] + ["PIN|" + p for p in PINS] +
                           [f"FOOTPRINT|A|{self.lib}"], ".PcbLib")):
            out = self.batch(bad)
            self.assertFalse(out.get("success"), out)
            self.assertIn(text, out["error"])
        # nothing reached the library: the symbol was never made
        open_library(self.lib)
        with self.assertRaises(AssertionError):
            read_models(self.lib, "FPTEST_X")

    def test_create_schematic_symbol_with_footprints(self):
        open_library(self.lib)
        out = tool(main.create_schematic_symbol(None, "FPTEST_D", "One tool call", PINS,
                                                footprints=[f"HDR1X2|{self.fp}", f"NT|{self.fp}|1"]))
        self.assertEqual(out.get("component_name"), "FPTEST_D", out)
        self.assertEqual(out.get("problems"), [], out)
        self.assertEqual({m["model"]: (m["library"].lower(), m["current"]) for m in out["footprints"]},
                         {"HDR1X2": (str(self.fp).lower(), False), "NT": (str(self.fp).lower(), True)}, out)
        self.reopen()
        read = self.pcb_models(read_models(self.lib, "FPTEST_D"))
        self.assertEqual({n: (v[0].lower(), v[1]) for n, v in read.items()},
                         {"HDR1X2": (str(self.fp).lower(), False), "NT": (str(self.fp).lower(), True)})

    def test_symbol_without_footprints_says_so(self):
        open_library(self.lib)
        out = tool(main.create_schematic_symbol(None, "FPTEST_E", "No footprint", PINS))
        self.assertEqual(out.get("component_name"), "FPTEST_E", out)
        self.assertEqual(out.get("footprints", []), [], out)

    def test_other_records_and_symbols_without_footprints_are_as_before(self):
        out = self.batch(["SYMBOL|FPTEST_G|With a parameter|1"] + ["PIN|" + p for p in PINS] +
                         ["SYMPARAM|MPN|ABC-123|0", f"FOOTPRINT|HDR1X2|{self.fp}", "DESCRIPTION|Described",
                          "SYMBOL|FPTEST_H|Plain|1"] + ["PIN|" + p for p in PINS])
        self.assertEqual((out["created"], out["failed"], out["problems"]), (2, [], []), out)
        self.assertEqual([f["symbol"] for f in out["footprints"]], ["FPTEST_G"], "only FPTEST_G has footprints")
        got = tool(main.get_symbol_primitives(None, str(self.lib), "FPTEST_G"))
        text = json.dumps(got)
        self.assertIn("ABC-123", text, "the SYMPARAM before the footprint was lost")
        self.assertIn("Described", text, "the DESCRIPTION after the footprint was lost")
        # a batch of symbols with no FOOTPRINT record has no footprints in its result
        out = self.batch(["SYMBOL|FPTEST_I|Plain|1"] + ["PIN|" + p for p in PINS])
        self.assertNotIn("footprints", out)

    def test_a_placed_part_carries_the_library_footprint(self):
        out = self.batch(["SYMBOL|FPTEST_F|Placed|1"] + ["PIN|" + p for p in PINS] +
                         [f"FOOTPRINT|HDR1X2|{self.fp}"])
        self.assertEqual(out["problems"], [], out)
        self.reopen()
        built = tool(main.build_schematic(None, [{"designator": "U1", "symbol_library": str(self.lib),
                                                  "symbol": "FPTEST_F", "x": 1000, "y": 1000}]))
        self.assertTrue(built.get("success"), built)
        sheet = built["sheet"]
        self.addCleanup(close, sheet)
        placed = self.pcb_models(read_models(sheet, "U1", in_library=False))
        self.assertEqual({n: v[1] for n, v in placed.items()}, {"HDR1X2": True},
                         "the placed part did not take the library's footprint")
