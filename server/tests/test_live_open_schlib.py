"""Live test of how a .SchLib is opened, in a running Altium Designer (A70):
run_altium_script's OpenSchDoc helper opens a .SchLib as a library (kind
SCHLIB, ObjectId 33), not as a schematic sheet (kind SCH, ObjectId 32), and
create_symbols_batch, finding the library open as a sheet, says so instead
of only "could not open and focus".

A copy of the "SpiritLevel-SL1" example's library is used (skipped when it is
not there), in a temporary folder, closed unsaved. See tests/live_altium.py
for how to run it.
"""
import asyncio
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.live_altium import LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close, close_all_under, script, tool

if LIVE:
    import main
    import win32api

EXAMPLES = Path(r"C:\Users\Public\Documents\Altium\AD25\Examples")
SCHLIB = EXAMPLES / "SpiritLevel-SL1" / "Libraries" / "SpiritLevel_2E.SchLib"
E_SCH_LIB = "33"


@unittest.skipUnless(LIVE, SKIP_REASON)
@unittest.skipUnless(SCHLIB.exists(), f"Altium's examples are not at {EXAMPLES}")
class LiveOpenSchLibTest(unittest.TestCase):
    def setUp(self):
        check_scripts_are_this_checkouts()
        self.tmp = Path(win32api.GetLongPathName(tempfile.mkdtemp(prefix="openschlib_live_")))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.addCleanup(close_all_under, str(self.tmp))
        self.lib = self.tmp / "Parts.SchLib"
        shutil.copyfile(SCHLIB, self.lib)

    def kind_open(self):
        """What Altium reports for the open library: its document kind and
        the ObjectId of the document the schematic server holds for it."""
        return script(f"Obj1 := Client.GetDocumentByPath('{self.lib}');\n"
                      f"Obj2 := SchServer.GetSchDocumentByPath('{self.lib}');\n"
                      "ResultText := Obj1.Kind + '|' + IntToStr(Obj2.ObjectId);").strip()

    def test_the_helper_opens_a_schlib_as_a_library(self):
        out = script(f"Obj1 := OpenSchDoc('{self.lib}');\n"
                     "ResultText := IntToStr(Obj1.ObjectId);").strip()
        self.assertEqual((out, self.kind_open()), (E_SCH_LIB, "SCHLIB|" + E_SCH_LIB),
                         "OpenSchDoc did not open the .SchLib as a library (ObjectId 33, kind SCHLIB)")

    def test_the_helper_still_opens_a_sheet_as_a_sheet(self):
        sheet = EXAMPLES / "Mini PC" / "Mini PC - WiFi" / "Connector_WiFi.SchDoc"
        if not sheet.exists():
            self.skipTest("the example sheet is not there")
        copy = self.tmp / "Sheet.SchDoc"
        shutil.copyfile(sheet, copy)
        out = script(f"Obj1 := OpenSchDoc('{copy}');\nResultText := IntToStr(Obj1.ObjectId);").strip()
        self.assertEqual(out, "32")

    def test_the_helper_says_so_when_the_schlib_is_open_as_a_sheet(self):
        script(f"Obj1 := Client.OpenDocument('SCH', '{self.lib}');\nClient.ShowDocument(Obj1);\n"
               "ResultText := 'shown';")
        out = json.loads(asyncio.run(main.run_altium_script(
            None, f"Obj1 := OpenSchDoc('{self.lib}');\nResultText := IntToStr(Obj1.ObjectId);", 180)))
        self.assertIn("is open as a schematic sheet, not a library", json.dumps(out), out)

    def test_the_batch_tool_names_the_kind_it_found(self):
        # The library open as a sheet, as the helper used to leave it
        script(f"Obj1 := Client.OpenDocument('SCH', '{self.lib}');\nClient.ShowDocument(Obj1);\n"
               "ResultText := 'shown';")
        self.assertEqual(self.kind_open().split("|")[1], "32", "the test could not open the library as a sheet")
        spec = self.tmp / "spec.txt"
        spec.write_text(f"LIBRARY|{self.lib}\nSYMBOL|OPENKIND_1|x|1\n"
                        "PIN|1|A|eElectricPassive|eRotate180|0|0\n", encoding="utf-8")
        out = tool(main.create_symbols_batch(None, str(spec)))
        text = json.dumps(out)
        self.assertIn("could not open and focus", text.lower(), out)
        self.assertIn("nothing was created or edited", text, out)
        self.assertIn("open as kind SCH (a schematic sheet", text, out)
        close(str(self.lib))


if __name__ == "__main__":
    unittest.main()
