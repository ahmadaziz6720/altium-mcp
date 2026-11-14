"""Live test of run_drc in a running Altium Designer. A17: a check that
finds violations leaves a saved, unchanged board unmodified (Altium's check
marked it modified whenever it found any), and a board with unsaved changes
still modified. A18: a check answered before the dialog driver saw the
dialog close is still a check that ran. A19: a check of a board in a
freshly opened project leaves the project file unmodified too (the check
adds its report to the project's generated documents), a project with an
unsaved change stays marked, and get_project_info says which. A20: with
"rules" the report lists only the rules asked for. A5: a check leaves the
project folder as it found it (Altium's report, and the outputs folder it
made for it, are deleted once read, unless keep_report), and a compile
call leaves no file in it. A21: after copper under a pour was deleted,
Altium answers the Run press with a "Design Rule Check" message (Run DRC,
Cancel, Repour Polygons and Run DRC); the check presses Run DRC, leaves the
pours as they are and says the message was met.

See tests/live_altium.py for how to run it. It works on copies of the small
WiFi board of the "Mini PC" example Altium installs (skipped when it is not
there), given a via-to-via clearance rule it fails, and saved once; A19's
tests on a copy of the board's whole project folder.
"""
import asyncio
import json
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from tests.live_altium import (LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close, close_all_under,
                                listing, modified, open_board, open_project, script, tool)

if LIVE:
    import drc
    import main
    import win32api
    import win32con
    import win32gui

WIFI = Path(r"C:\Users\Public\Documents\Altium\AD25\Examples\Mini PC\Mini PC - WiFi\WiFi.PcbDoc")


@unittest.skipUnless(LIVE, SKIP_REASON)
@unittest.skipUnless(WIFI.exists(), f"Altium's example board is not at {WIFI}")
class LiveDrcTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        check_scripts_are_this_checkouts()

    def setUp(self):
        # Altium is given the long path: the one it reports back
        tmp = Path(win32api.GetLongPathName(tempfile.mkdtemp(prefix="drc_live_")))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.board = str(tmp / "drc.PcbDoc")
        shutil.copyfile(WIFI, self.board)
        open_board(self.board)
        # The board, and the reports the checks opened
        self.addCleanup(close_all_under, str(tmp))
        rule = tool(main.create_pcb_rule(None, "clearance", "LiveViaGap", {"gap_mils": 40}, "IsVia", "IsVia",
                                         board_path=self.board))
        self.assertTrue(rule.get("success"), rule)

    def save_and_reopen(self):
        saved = script(f"Obj1 := Client.GetDocumentByPath('{self.board}');\n"
                       "ResultText := BoolToStr(Obj1.DoFileSave(''), True);").strip()
        self.assertEqual(saved, "True")
        close(self.board)
        open_board(self.board)

    def test_check_leaves_a_saved_board_unmodified(self):
        self.save_and_reopen()
        self.assertFalse(modified(self.board), "the board is freshly opened")
        out = tool(main.run_drc(None, board_path=self.board))
        self.assertTrue(out["success"], out)
        self.assertTrue(out["ran"], out)
        self.assertGreater(out["violation_count"], 0, "the rule should fail on the board's vias")
        self.assertFalse(modified(self.board), "the check left the board modified")
        self.assertFalse(out["board_modified"])

    def test_ran_when_the_reply_beats_the_close_check(self):
        # A18: a small board is checked and answered within the quarter
        # second the driver waits after its press. The close is hidden from
        # the driver here, so it is always stopped with the press sent and
        # the close unseen, as it was then by chance.
        import drc
        with mock.patch.object(drc, "_is_open", return_value=True):
            out = tool(main.run_drc(None, board_path=self.board))
        self.assertTrue(out["ran"], out)
        self.assertTrue(out["success"], out)
        self.assertIn("report", out, "the report this check wrote is its result")

    def test_report_lists_only_the_rules_asked_for(self):
        # A20: the filter used to narrow the violations and leave the
        # report's per-rule counts at all the board's rules
        full = tool(main.run_drc(None, board_path=self.board))
        self.assertTrue(full["ran"], full)
        kinds = {drc.rule_key(drc._kind(r["rule"])) for r in full["report"]["rules"]}
        self.assertGreater(len(kinds), 2, "the report lists the board's rules")
        self.assertIn("clearance", kinds)
        self.assertNotIn("rules_omitted", full["report"], "without rules the report is whole")
        # a kind that is not the via rule's (the violations it filters to
        # are none, the case that cost the most)
        out = tool(main.run_drc(None, board_path=self.board, rules=["Width"]))
        self.assertTrue(out["ran"], out)
        self.assertEqual(out["matching_count"], 0, out)
        rules = out["report"]["rules"]
        self.assertTrue(rules, "the board has width rules")
        self.assertEqual({drc.rule_key(drc._kind(r["rule"])) for r in rules}, {"width"}, rules)
        self.assertEqual(out["report"]["rules_omitted"], len(full["report"]["rules"]) - len(rules))
        self.assertEqual(out["report"]["violations"], full["report"]["violations"],
                         "the totals are the check's")
        # the via rule's own kind: its entries, with the violations the rule found
        out = tool(main.run_drc(None, board_path=self.board, rules=["Clearance"]))
        rules = out["report"]["rules"]
        self.assertEqual({drc.rule_key(drc._kind(r["rule"])) for r in rules}, {"clearance"}, rules)
        self.assertGreater(sum(r["violations"] for r in rules), 0, rules)
        self.assertGreater(out["matching_count"], 0, out)

    def test_check_of_the_focused_board_leaves_its_folder_as_found(self):
        # A5, a board under Free Documents, named by no board_path: the
        # report beside it goes
        self.save_and_reopen()
        folder = Path(self.board).parent
        before = listing(folder)
        out = tool(main.run_drc(None))
        self.assertTrue(out["ran"], out)
        self.assertEqual(out["board"].lower(), self.board.lower(), out)
        self.assertEqual(listing(folder), before, "the check left its report beside the board")
        self.assertIs(out["report"].get("deleted"), True, out["report"])
        self.assertFalse(modified(self.board), "the check left the board modified")

    def test_check_keeps_unsaved_changes_marked(self):
        self.assertTrue(modified(self.board), "the added rule is an unsaved change")
        out = tool(main.run_drc(None, board_path=self.board))
        self.assertTrue(out["ran"], out)
        self.assertTrue(modified(self.board), "the check cleared an unsaved change's mark")
        self.assertTrue(out["board_modified"])


@unittest.skipUnless(LIVE, SKIP_REASON)
@unittest.skipUnless(WIFI.exists(), f"Altium's example board is not at {WIFI}")
class LiveDrcProjectTest(unittest.TestCase):
    """A19, on a copy of the WiFi board's project, opened as a project."""

    @classmethod
    def setUpClass(cls):
        check_scripts_are_this_checkouts()
        tmp = Path(win32api.GetLongPathName(tempfile.mkdtemp(prefix="drc_prj_live_")))
        cls.addClassCleanup(shutil.rmtree, tmp, ignore_errors=True)
        cls.folder = str(tmp / "WiFi")
        shutil.copytree(WIFI.parent, cls.folder)
        cls.project = str(Path(cls.folder) / "WiFi_miniPCIe.PrjPcb")
        cls.board = str(Path(cls.folder) / WIFI.name)
        # The board is given a rule it fails and saved, so the check finds
        # violations; then everything is closed for a fresh open per test
        cls.addClassCleanup(close_all_under, cls.folder)
        cls.open()
        rule = tool(main.create_pcb_rule(None, "clearance", "LiveViaGap", {"gap_mils": 40}, "IsVia", "IsVia",
                                         board_path=cls.board))
        assert rule.get("success"), rule
        saved = script(f"Obj1 := Client.GetDocumentByPath('{cls.board}');\n"
                       "ResultText := BoolToStr(Obj1.DoFileSave(''), True);").strip()
        assert saved == "True", saved
        close_all_under(cls.folder)

    @classmethod
    def open(cls):
        opened = open_project(cls.project)
        assert opened.lower() == cls.project.lower(), opened
        open_board(cls.board)

    def setUp(self):
        self.open()
        # A report a check left (A5) goes, so each test starts from the copy
        self.addCleanup(shutil.rmtree, self.outputs(), ignore_errors=True)
        self.addCleanup(close_all_under, self.folder)

    def check(self):
        out = tool(main.run_drc(None, board_path=self.board))
        self.assertTrue(out["success"], out)
        self.assertTrue(out["ran"], out)
        self.assertGreater(out["violation_count"], 0, "the rule should fail on the board's vias")
        return out

    def test_check_leaves_a_fresh_project_unmodified(self):
        self.assertFalse(modified(self.project), "the project is freshly opened")
        self.assertFalse(modified(self.board), "the board is freshly opened")
        out = self.check()
        self.assertFalse(modified(self.project), "the check left the project file modified")
        self.assertFalse(modified(self.board), "the check left the board modified")
        self.assertEqual(out.get("project", "").lower(), self.project.lower(), out)
        self.assertIs(out.get("project_modified"), False, out)
        info = tool(main.get_project_info(None))
        self.assertEqual(info["project_path"].lower(), self.project.lower())
        self.assertIs(info.get("project_modified"), False, info)
        self.assertEqual(info["modified_document_count"], 0, info)

    def test_check_keeps_a_projects_unsaved_change_marked(self):
        # The flag is what an unsaved change of the project sets, and what
        # the tools read
        script(f"Obj1 := Client.GetDocumentByPath('{self.project}');\n"
               "Obj1.SetModified(True);\nResultText := 'set';")
        self.assertTrue(modified(self.project))
        info = tool(main.get_project_info(None))
        self.assertIs(info.get("project_modified"), True, info)
        self.assertEqual(info["modified_document_count"], 1, info)
        out = self.check()
        self.assertTrue(modified(self.project), "the check cleared the project's unsaved change")
        self.assertIs(out.get("project_modified"), True, out)
        info = tool(main.get_project_info(None))
        self.assertIs(info.get("project_modified"), True, info)
        self.assertEqual(info["modified_document_count"], 1, info)

    @classmethod
    def outputs(cls):
        return Path(cls.folder) / "Project Outputs for WiFi_miniPCIe"

    def test_check_leaves_the_project_folder_as_found(self):
        self.assertFalse(self.outputs().exists(), "the copy has no outputs folder")
        before = listing(self.folder)
        out = self.check()
        self.assertEqual(listing(self.folder), before, "the check left files in the project folder")
        report = out["report"]
        self.assertIs(report.get("deleted"), True, report)
        self.assertNotIn("path", report, "a deleted report has no path")
        self.assertGreater(report["violations"], 0, "the report was read before it was deleted")
        # Deleting the report Altium lists among the project's generated
        # documents marks nothing and asks nothing
        self.assertFalse(modified(self.project), "the project file is left modified")
        self.assertFalse(modified(self.board), "the board is left modified")

    def test_keep_report_keeps_it(self):
        out = tool(main.run_drc(None, board_path=self.board, keep_report=True))
        self.assertTrue(out["ran"], out)
        report = out["report"]
        self.assertIs(report.get("deleted"), False, report)
        self.assertEqual(Path(report["path"]).parent, self.outputs(), report)
        self.assertTrue(Path(report["path"]).is_file(), report)
        self.assertTrue(Path(report["path"]).with_suffix(".html").is_file(), report)

    def test_an_existing_outputs_folder_and_report_stay(self):
        # Only what the check wrote goes: a folder that was there stays,
        # with what it held, and an earlier report is put back as it was
        self.outputs().mkdir()
        (self.outputs() / "other.txt").write_text("kept")
        earlier = self.outputs() / "Design Rule Check - WiFi.drc"
        earlier.write_text("an earlier report")
        before = listing(self.folder)
        out = self.check()
        self.assertEqual(listing(self.folder), before, "the check did not leave the folder as found")
        self.assertEqual(earlier.read_text(), "an earlier report")
        self.assertIs(out["report"].get("deleted"), True, out["report"])
        self.assertIs(out["report"].get("restored"), True, out["report"])


@unittest.skipUnless(LIVE, SKIP_REASON)
@unittest.skipUnless(WIFI.exists(), f"Altium's example board is not at {WIFI}")
class LiveCompileFolderTest(unittest.TestCase):
    """A5: a compile call writes nothing into the project folder. The
    project's <name>.PrjPcbStructure is written by Altium when the project
    is closed, compiled or not, so the call cannot remove it."""

    @classmethod
    def setUpClass(cls):
        check_scripts_are_this_checkouts()

    def setUp(self):
        tmp = Path(win32api.GetLongPathName(tempfile.mkdtemp(prefix="compile_live_")))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.folder = tmp / "WiFi"
        shutil.copytree(WIFI.parent, self.folder)
        self.project = str(self.folder / "WiFi_miniPCIe.PrjPcb")
        self.structure = self.folder / "WiFi_miniPCIe.PrjPcbStructure"
        self.addCleanup(close_all_under, str(self.folder))

    def compile_calls(self):
        # Opened by the first call, as a caller giving project_path does
        erc = tool(main.get_erc_violations(None, project_path=self.project))
        self.assertEqual(erc["project_path"].lower(), self.project.lower(), erc)
        self.assertTrue(erc["compiled"], erc)
        parts = tool(main.get_project_components(None, project_path=self.project))
        self.assertGreater(parts["component_count"], 0, parts)

    def test_no_structure_file_where_none_was(self):
        self.structure.unlink()
        before = listing(self.folder)
        self.compile_calls()
        self.assertEqual(listing(self.folder), before, "a compile call left a file in the project folder")

    def test_an_existing_structure_file_stays(self):
        content = self.structure.read_bytes()
        before = listing(self.folder)
        self.compile_calls()
        self.assertEqual(listing(self.folder), before)
        self.assertEqual(self.structure.read_bytes(), content)


# Each pour by the holes and outline points of its poured regions: a
# repour of the WiFi board with its tracks deleted changes them (Top_GND
# 18/481 to 18/476), its region count does not
POURS = """var
    Board : IPCB_Board;
    It : IPCB_BoardIterator;
    P : IPCB_Polygon;
    G : IPCB_GroupIterator;
    R : IPCB_Region;
    H, V : Integer;
Board := PCBServer.GetPCBBoardByPath('%s');
It := Board.BoardIterator_Create;
It.AddFilter_ObjectSet(MkSet(ePolyObject));
It.AddFilter_LayerSet(AllLayers);
It.AddFilter_Method(eProcessAll);
P := It.FirstPCBObject;
while P <> nil do
begin
    H := 0;
    V := 0;
    G := P.GroupIterator_Create;
    G.AddFilter_ObjectSet(MkSet(eRegionObject));
    R := G.FirstPCBObject;
    while R <> nil do
    begin
        H := H + R.HoleCount;
        V := V + R.MainContour.Count;
        R := G.NextPCBObject;
    end;
    P.GroupIterator_Destroy(G);
    ResultText := ResultText + P.Name + '=' + IntToStr(H) + '/' + IntToStr(V) + ' ';
    P := It.NextPCBObject;
end;
Board.BoardIterator_Destroy(It);"""


def repour_prompts():
    """Altium's "Design Rule Check" repour messages that are up, each as
    (window, {button text: button}), found here by their title and buttons,
    apart from the driver under test."""
    found = []

    def top(hwnd, _):
        if (win32gui.IsWindowVisible(hwnd) and win32gui.GetClassName(hwnd) == "TMessageForm"
                and win32gui.GetWindowText(hwnd) == "Design Rule Check"):
            buttons = {}
            win32gui.EnumChildWindows(hwnd, lambda c, _: buttons.__setitem__(
                win32gui.GetWindowText(c).replace("&", "").strip().lower(), c), None)
            if "run drc" in buttons:
                found.append((hwnd, buttons))
    win32gui.EnumWindows(top, None)
    return found


def answer_repour_prompts(button="cancel"):
    """Never leave Altium blocked behind the message: press one of its
    buttons, close a Design Rule Checker dialog left up, and give Altium a
    moment to finish the bridge command."""
    for _ in range(20):
        prompts = repour_prompts()
        if not prompts:
            break
        for _, buttons in prompts:
            if button in buttons:
                win32gui.PostMessage(buttons[button], win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, 0)
                win32gui.PostMessage(buttons[button], win32con.WM_LBUTTONUP, 0, 0)
        time.sleep(0.5)
    dialog = drc.find_dialog()
    if dialog is not None:
        win32gui.PostMessage(dialog, win32con.WM_CLOSE, 0, 0)
    time.sleep(3)


@unittest.skipUnless(LIVE, SKIP_REASON)
@unittest.skipUnless(WIFI.exists(), f"Altium's example board is not at {WIFI}")
class LiveDrcRepourTest(unittest.TestCase):
    """A21, on a copy of the WiFi board, whose tracks under its GND pours
    are deleted the way a session does."""

    # How long the check may take: a few seconds on this board. Before the
    # fix the call waited on the message for the bridge's 30 minutes.
    WAIT = 90

    @classmethod
    def setUpClass(cls):
        check_scripts_are_this_checkouts()

    def setUp(self):
        tmp = Path(win32api.GetLongPathName(tempfile.mkdtemp(prefix="drc_repour_live_")))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.board = str(tmp / "repour.PcbDoc")
        shutil.copyfile(WIFI, self.board)
        open_board(self.board)
        self.addCleanup(close_all_under, str(tmp))
        # Runs first: a message left up would block every later script
        self.addCleanup(answer_repour_prompts)

    def test_check_presses_run_drc_on_the_repour_message(self):
        for net in ("NetDS1_2", "NetC39_1"):
            out = tool(main.delete_pcb_objects(None, kinds=["track", "arc", "via"], net=net,
                                               board_path=self.board))
            self.assertGreater(out.get("deleted", 0), 0, out)
        pours = script(POURS % self.board).strip()
        self.assertIn("Top_GND=", pours)
        try:
            out = json.loads(asyncio.run(asyncio.wait_for(main.run_drc(None, board_path=self.board), self.WAIT)))
        except asyncio.TimeoutError:
            left = "Altium's repour message left up" if repour_prompts() else "no repour message seen"
            self.fail(f"run_drc did not return within {self.WAIT} s ({left})")
        self.assertTrue(out["success"], out)
        self.assertTrue(out["ran"], out)
        self.assertIs(out.get("repour_prompt"), True, out)
        self.assertIn("repour_note", out)
        self.assertEqual(repour_prompts(), [], "the message was left up")
        # The check of the board as it is: the three open connections the
        # deleted tracks left (2-pad net 1, 3-pad net 2), pours unchanged
        # (repoured, the check found 5)
        self.assertEqual(out["violation_count"], 3, out)
        self.assertEqual(out["listed_by_rule"], {"UnRoutedNet": 3}, out)
        self.assertEqual(script(POURS % self.board).strip(), pours, "the pours were repoured")
        self.assertTrue(modified(self.board), "the deleted tracks are an unsaved change")
        self.assertTrue(out["board_modified"])

    def test_no_repour_message_no_field(self):
        out = tool(main.run_drc(None, board_path=self.board))
        self.assertTrue(out["ran"], out)
        self.assertNotIn("repour_prompt", out)
        self.assertFalse(modified(self.board), "the check left the board modified")


if __name__ == "__main__":
    unittest.main()
