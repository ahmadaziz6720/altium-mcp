"""Live test of where build_schematic's new sheet goes, in a running Altium
Designer (A26): Altium puts a new sheet into the focused project, which is
to be left as it was found, its documents and its modified flag, with
project_path, without it, and when parts are missing.

See tests/live_altium.py for how to run it. The focused project is always
one of the test's own, checked before every build; the library is a copy of
one of the "SpiritLevel-SL1" example's (skipped when it is not there). All
is closed unsaved at the end.
"""
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.live_altium import LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close_all_under, modified, script, tool

if LIVE:
    import main
    import win32api

EXAMPLES = Path(r"C:\Users\Public\Documents\Altium\AD25\Examples")
SCHLIB = EXAMPLES / "SpiritLevel-SL1" / "Libraries" / "SpiritLevel_2E.SchLib"
SHEET = EXAMPLES / "Mini PC" / "Mini PC - WiFi" / "Connector_WiFi.SchDoc"


def focused_project():
    return script("ResultText := GetWorkspace.DM_FocusedProject.DM_ProjectFullPath;").strip()


def documents(project=None):
    """What a project lists (Free Documents when none), lower case, but
    ActiveBOM's virtual document."""
    which = f"GetWorkspace.DM_GetProjectFromPath('{project}')" if project else "GetWorkspace.DM_FreeDocumentsProject"
    out = script(f"""var
    P : IProject;
    I : Integer;
    S : String;
begin
P := {which};
S := '';
for I := 0 to P.DM_LogicalDocumentCount - 1 do
    S := S + P.DM_LogicalDocuments(I).DM_FullPath + '|';
ResultText := S;
end;""")
    return sorted(p.lower() for p in out.strip().split("|") if p and not p.lower().endswith(".virtualbom"))


def drop_unsaved(name):
    """Close a sheet never saved and take its entry out of Free Documents,
    which keeps it after the close. Only a bare name: never a saved document."""
    if "\\" in name:
        return
    script(f"""var
    D : IServerDocument;
begin
D := Client.GetDocumentByPath('{name}');
if D <> nil then
begin
    if UpperCase(D.FileName) = UpperCase('{name}') then
    begin
        D.SetModified(False);
        Client.CloseDocument(D);
    end;
end;
GetWorkspace.DM_FreeDocumentsProject.DM_RemoveSourceDocument('{name}');
ResultText := 'dropped';
end;""")


@unittest.skipUnless(LIVE, SKIP_REASON)
@unittest.skipUnless(SCHLIB.exists() and SHEET.exists(), f"Altium's examples are not at {EXAMPLES}")
class LiveBuildFocusTest(unittest.TestCase):
    def setUp(self):
        check_scripts_are_this_checkouts()
        self.tmp = Path(win32api.GetLongPathName(tempfile.mkdtemp(prefix="focus_live_")))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.addCleanup(close_all_under, str(self.tmp))
        # A project closed before its sheets stays listed in the workspace: theirs first
        self.addCleanup(self.close_sheets)
        self.lib = self.tmp / "Parts.SchLib"
        shutil.copyfile(SCHLIB, self.lib)
        self.target = self.tmp / "Target.PrjPcb"
        self.assertTrue(tool(main.create_project(None, str(self.target))).get("success"))
        self.other = self.tmp / "Other.PrjPcb"
        self.assertTrue(tool(main.create_project(None, str(self.other))).get("success"))
        self.other_sheet = self.tmp / "Other.SchDoc"
        shutil.copyfile(SHEET, self.other_sheet)
        self.assertTrue(tool(main.add_project_document(None, str(self.other), str(self.other_sheet))).get("success"))
        self.file_before = self.other.read_bytes()
        self.focus()
        self.listed_before = documents(self.other)
        self.free_before = documents()
        self.assertFalse(modified(str(self.other)), "the focused project is modified before the test")

    def close_sheets(self):
        for path in self.tmp.glob("*.SchDoc"):
            close_all_under(str(path))

    def focus(self):
        """The test's own project in focus: no build runs with another there."""
        script(f"Obj1 := Client.OpenDocument('SCH', '{self.other_sheet}');\n"
               "Client.ShowDocument(Obj1);\nResultText := 'shown';")
        focused = focused_project()
        if focused.lower() != str(self.other).lower():
            self.fail(f"not run: the focused project is not the test's: {focused}")

    def build(self, symbol="RES", **args):
        self.focus()
        out = tool(main.build_schematic(None, [{"designator": "R1", "symbol_library": str(self.lib),
                                               "symbol": symbol, "x": 1000, "y": 1000}], **args))
        # A failure's details are JSON inside its error text
        name = re.search(r'"sheet": *"([^"\\/]+)"', json.dumps(out).replace('\\"', '"'))
        if name:
            self.addCleanup(drop_unsaved, name.group(1))
        return out, name.group(1).lower() if name else ""

    def assert_as_found(self):
        self.assertEqual((modified(str(self.other)), documents(self.other)), (False, self.listed_before),
                         "the focused project is not as it was found (modified, its documents)")
        self.assertEqual(self.other.read_bytes(), self.file_before, "the focused project's file was written")

    def test_without_project_path_the_sheet_is_a_free_document(self):
        out, sheet = self.build()
        self.assertTrue(out.get("success"), out)
        self.assert_as_found()
        self.assertIn(sheet, documents())
        self.assertEqual(out["detached_from"].lower(), str(self.other).lower())

    def test_into_a_project_with_another_in_focus(self):
        saved = self.tmp / "Built.SchDoc"
        out, _ = self.build(project_path=str(self.target), sheet_path=str(saved))
        self.assertTrue(out.get("success"), out)
        self.assert_as_found()
        self.assertEqual(documents(self.target), [str(saved).lower()])
        # The build opens the test's library, a free document of its own
        self.assertEqual([d for d in documents() if d != str(self.lib).lower()], self.free_before,
                         "Free Documents holds the sheet, or its unsaved name")
        self.assertEqual(out["sheet"].lower(), str(saved).lower())
        self.assertEqual(out["detached_from"].lower(), str(self.other).lower())
        self.assertNotIn("detached_from", out["project"])

    def test_a_failure_leaves_the_sheet_out_of_the_focused_project(self):
        for args in ({}, {"project_path": str(self.target), "sheet_path": str(self.tmp / "Failed.SchDoc")}):
            out, sheet = self.build(symbol="NO_SUCH_SYMBOL", **args)
            self.assertFalse(out.get("success"), out)
            self.assert_as_found()
            self.assertIn(sheet, documents())
            self.assertIn("free document", out["error"])
            self.assertEqual(documents(self.target), [])

    def test_a_free_sheet_stays_out_of_the_next_builds_project(self):
        out, free = self.build()
        self.assertTrue(out.get("success"), out)
        saved = self.tmp / "Next.SchDoc"
        out, _ = self.build(project_path=str(self.target), sheet_path=str(saved))
        self.assertTrue(out.get("success"), out)
        self.assert_as_found()
        self.assertEqual(documents(self.target), [str(saved).lower()])
        self.assertIn(free, documents())
