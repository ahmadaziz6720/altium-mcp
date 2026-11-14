"""Live test of run_drc in a running Altium Designer. A17: a check that
finds violations leaves a saved, unchanged board unmodified (Altium's check
marked it modified whenever it found any), and a board with unsaved changes
still modified. A18: a check answered before the dialog driver saw the
dialog close is still a check that ran. A19: a check of a board in a
freshly opened project leaves the project file unmodified too (the check
adds its report to the project's generated documents), a project with an
unsaved change stays marked, and get_project_info says which. A20: with
"rules" the report lists only the rules asked for.

See tests/live_altium.py for how to run it. It works on copies of the small
WiFi board of the "Mini PC" example Altium installs (skipped when it is not
there), given a via-to-via clearance rule it fails, and saved once; A19's
tests on a copy of the board's whole project folder.
"""
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.live_altium import (LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close, close_all_under,
                                modified, open_board, open_project, script, tool)

if LIVE:
    import drc
    import main
    import win32api

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


if __name__ == "__main__":
    unittest.main()
