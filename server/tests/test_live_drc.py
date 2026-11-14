"""Live test of run_drc in a running Altium Designer. A17: a check that
finds violations leaves a saved, unchanged board unmodified (Altium's check
marked it modified whenever it found any), and a board with unsaved changes
still modified. A18: a check answered before the dialog driver saw the
dialog close is still a check that ran.

See tests/live_altium.py for how to run it. It works on copies of the small
WiFi board of the "Mini PC" example Altium installs (skipped when it is not
there), given a via-to-via clearance rule it fails, and saved once.
"""
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.live_altium import LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close, modified, open_board, script, tool

if LIVE:
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
        self.addCleanup(close, self.board)
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

    def test_check_keeps_unsaved_changes_marked(self):
        self.assertTrue(modified(self.board), "the added rule is an unsaved change")
        out = tool(main.run_drc(None, board_path=self.board))
        self.assertTrue(out["ran"], out)
        self.assertTrue(modified(self.board), "the check cleared an unsaved change's mark")
        self.assertTrue(out["board_modified"])


if __name__ == "__main__":
    unittest.main()
