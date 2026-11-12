"""Live test of get_unrouted_connections in a running Altium Designer (A4):
a read leaves a saved, unchanged board unmodified and its tracks as they
were (analyzing its nets joined straight track segments and left it
modified).

See tests/live_altium.py for how to run it. It works on copies of the small
WiFi board of the "Mini PC" example Altium installs (skipped when it is not
there).
"""
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.live_altium import (LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close, modified, open_board,
                               script, tool)

if LIVE:
    import main
    import win32api

WIFI = Path(r"C:\Users\Public\Documents\Altium\AD25\Examples\Mini PC\Mini PC - WiFi\WiFi.PcbDoc")

TRACKS = """var
    Board : IPCB_Board;
    It : IPCB_BoardIterator;
    P : IPCB_Primitive;
    N : Integer;
Board := PCBServer.GetCurrentPCBBoard;
It := Board.BoardIterator_Create;
It.AddFilter_ObjectSet(MkSet(eTrackObject));
It.AddFilter_LayerSet(AllLayers);
It.AddFilter_Method(eProcessAll);
N := 0;
P := It.FirstPCBObject;
while P <> nil do
begin
    N := N + 1;
    P := It.NextPCBObject;
end;
Board.BoardIterator_Destroy(It);
ResultText := IntToStr(N);"""


@unittest.skipUnless(LIVE, SKIP_REASON)
@unittest.skipUnless(WIFI.exists(), f"Altium's example board is not at {WIFI}")
class LiveUnroutedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        check_scripts_are_this_checkouts()

    def setUp(self):
        # Altium is given the long path: the one it reports back
        tmp = Path(win32api.GetLongPathName(tempfile.mkdtemp(prefix="unrouted_live_")))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.board = str(tmp / "unrouted.PcbDoc")
        shutil.copyfile(WIFI, self.board)
        open_board(self.board)
        self.addCleanup(close, self.board)

    def test_read_leaves_a_saved_board_unmodified(self):
        self.assertFalse(modified(self.board), "the board is freshly opened")
        tracks = script(TRACKS).strip()
        out = tool(main.get_unrouted_connections(None))
        self.assertTrue(out["success"], out)
        self.assertEqual(script(TRACKS).strip(), tracks, "the read changed the board's tracks")
        self.assertFalse(modified(self.board), "a read left the board modified")
        self.assertFalse(out["analyzed"])


if __name__ == "__main__":
    unittest.main()
