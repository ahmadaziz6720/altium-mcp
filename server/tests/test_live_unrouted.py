"""Live test of get_unrouted_connections in a running Altium Designer.

A4: a read leaves a saved, unchanged board unmodified and its tracks as
they were (analyzing its nets joined straight track segments and left it
modified).

A3: a connection opened by deleting copper is listed, before and after the
board is saved, closed and reopened, in 2D and in 3D view; and place_copper
leaves the connections its copper does not close on the board.
Board.AnalyzeNet, which both tools ran, removes every connection object of
the net it analyzes, open or not, in either view; and a board closed and
reopened in the same Altium is the board left in memory, so it came back
without them.

See tests/live_altium.py for how to run it. It works on copies of the small
WiFi board of the "Mini PC" example Altium installs (skipped when it is not
there). A3's two read tests set the view with Altium's "2" or "3" key,
Altium brought to the front (no script call switches it), and tell the view
by a screenshot; they are skipped when Altium cannot be brought to the
front or the view is not recognised, and leave Altium in 2D.
"""
import asyncio
import base64
import io
import shutil
import tempfile
import time
import unittest
from pathlib import Path

from tests.live_altium import (LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close, close_all_under, modified,
                               open_board, script, tool)

if LIVE:
    import main
    import win32api
    import win32con
    import win32gui
    from PIL import Image

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

# A 2-pad net routed by one track, R14-1 to DS1-2 (mils from the origin),
# and a 3-pad net (R15-1, C39-1, U1-3) routed by five
TWO_PAD = "NetDS1_2"
R14_1, DS1_2 = [797.244, 893.701], [797.244, 942.913]
THREE_PAD = "NetC39_1"
GROUP = ["R14", "DS1", "R15", "C39", "U1"]


def connection_objects(board, net):
    """The connection objects of net on the board, read by a board iterator."""
    return int(script(f"""var
    Board : IPCB_Board;
    It : IPCB_BoardIterator;
    P : IPCB_Primitive;
    N : Integer;
Board := PCBServer.GetPCBBoardByPath('{board}');
N := 0;
It := Board.BoardIterator_Create;
It.AddFilter_ObjectSet(MkSet(eConnectionObject));
It.AddFilter_LayerSet(AllLayers);
It.AddFilter_Method(eProcessAll);
P := It.FirstPCBObject;
while P <> nil do
begin
    if (P.Net <> nil) and (UpperCase(P.Net.Name) = UpperCase('{net}')) then N := N + 1;
    P := It.NextPCBObject;
end;
Board.BoardIterator_Destroy(It);
ResultText := IntToStr(N);""").strip())


def _red_share(board):
    """The share of the board view drawn in the top layer's pure red: most of
    the WiFi board in 2D, none of it in 3D."""
    shot = asyncio.run(main.get_screenshot(None, "pcb", None))
    for item in shot if isinstance(shot, list) else [shot]:
        data = getattr(item, "data", None)
        if data is not None:
            raw = data if isinstance(data, bytes) else base64.b64decode(data)
            im = Image.open(io.BytesIO(raw)).convert("RGB")
            w, h = im.size
            canvas = im.crop((w // 5, h // 8, w * 3 // 4, h * 7 // 8)).resize((200, 200))
            px = list(canvas.getdata())
            return sum(1 for p in px if p == (255, 0, 0)) / len(px)
    raise unittest.SkipTest("no screenshot to tell the view by")


def _view(board):
    share = _red_share(board)
    return "2D" if share > 0.05 else "3D" if share < 0.005 else f"neither ({share:.0%} top-layer red)"


def set_view(board, mode):
    """Show the board in mode, "2D" or "3D", with Altium's "2" or "3" key,
    Altium in front. A board may open in 3D (a copy under a name last shown
    in 3D did)."""
    now = _view(board)
    if now == mode:
        return
    if now not in ("2D", "3D"):
        raise unittest.SkipTest(f"the board's view is not recognised: {now}")
    name = Path(board).name
    frames = []
    win32gui.EnumWindows(lambda h, _: frames.append(h) if name in win32gui.GetWindowText(h)
                         and win32gui.IsWindowVisible(h) else None, None)
    if not frames:
        raise unittest.SkipTest("no Altium frame shows the board")
    previous = win32gui.GetForegroundWindow()
    main._bring_to_front(frames[0])
    time.sleep(0.8)
    try:
        # A key goes to whichever window is in front: never to another one
        if win32gui.GetForegroundWindow() != frames[0]:
            raise unittest.SkipTest("Altium could not be brought to the front")
        key = ord(mode[0])
        win32api.keybd_event(key, 0, 0, 0)
        win32api.keybd_event(key, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(3)
    finally:
        try:
            win32gui.SetForegroundWindow(previous)
        except Exception:
            pass
    now = _view(board)
    if now != mode:
        raise unittest.SkipTest(f"the switch to {mode} was not seen: {now}")


def leave_in_2d(board):
    try:
        set_view(board, "2D")
    except unittest.SkipTest:
        pass


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
        self.addCleanup(close_all_under, str(tmp))

    def test_read_leaves_a_saved_board_unmodified(self):
        self.assertFalse(modified(self.board), "the board is freshly opened")
        tracks = script(TRACKS).strip()
        out = tool(main.get_unrouted_connections(None))
        self.assertTrue(out["success"], out)
        self.assertEqual(out["connection_count"], 0, "the example board is fully routed")
        self.assertEqual(script(TRACKS).strip(), tracks, "the read changed the board's tracks")
        self.assertFalse(modified(self.board), "a read left the board modified")

    # A3
    def delete_copper(self):
        for net in (TWO_PAD, THREE_PAD):
            out = tool(main.delete_pcb_objects(None, kinds=["track", "arc", "via"], net=net, board_path=self.board))
            self.assertGreater(out.get("deleted", 0), 0, out)

    def assert_open(self, out, when):
        self.assertTrue(out["success"], out)
        self.assertEqual(out["by_net"], {THREE_PAD: 2, TWO_PAD: 1}, f"{when}: {out}")
        two = [c for c in out["connections"] if c["net"] == TWO_PAD][0]
        self.assertEqual({two["from_pad"], two["to_pad"]}, {"R14-1", "DS1-2"}, two)
        for c in out["connections"]:
            if c["net"] == THREE_PAD:
                self.assertTrue({c["from_pad"], c["to_pad"]} <= {"R15-1", "C39-1", "U1-3"}, c)

    def reads_the_open_connections(self, mode):
        set_view(self.board, mode)
        # A board opens in the view Altium last showed: leave it in 2D
        self.addCleanup(leave_in_2d, self.board)
        self.delete_copper()
        self.assertTrue(modified(self.board))
        self.assert_open(tool(main.get_unrouted_connections(None, designators=GROUP, board_path=self.board)),
                         "on the board just changed")
        saved = script(f"Obj1 := Client.GetDocumentByPath('{self.board}');\n"
                       "ResultText := BoolToStr(Obj1.DoFileSave(''), True);").strip()
        self.assertEqual(saved, "True")
        close(self.board)
        open_board(self.board)
        set_view(self.board, mode)
        self.assertFalse(modified(self.board), "the board is reopened")
        tracks = script(TRACKS).strip()
        self.assert_open(tool(main.get_unrouted_connections(None, designators=GROUP, board_path=self.board)),
                         "saved, closed and reopened")
        self.assertEqual(script(TRACKS).strip(), tracks, "the read changed the board's tracks")
        self.assertFalse(modified(self.board), "a read left the board modified")
        self.assertEqual(connection_objects(self.board, TWO_PAD), 1, "the read left the connection off the board")

    def test_deleted_copper_leaves_open_connections(self):
        self.reads_the_open_connections("2D")

    def test_deleted_copper_leaves_open_connections_in_3d(self):
        self.reads_the_open_connections("3D")

    def test_place_copper_keeps_the_connections_it_leaves_open(self):
        out = tool(main.delete_pcb_objects(None, kinds=["track"], net=TWO_PAD, board_path=self.board))
        self.assertEqual(out.get("deleted"), 1, out)
        self.assertEqual(connection_objects(self.board, TWO_PAD), 1)
        # Half way: still open (the track's end is 13 mils short of the pad)
        mid = [R14_1[0], 905.0]
        out = tool(main.place_copper(None, tracks=[{"net": TWO_PAD, "layer": "Top Layer", "width": 10,
                                                    "start": R14_1, "end": mid}], board_path=self.board))
        self.assertTrue(out.get("success"), out)
        self.assertEqual(connection_objects(self.board, TWO_PAD), 1, "place_copper removed an open connection")
        # The rest: closed
        out = tool(main.place_copper(None, tracks=[{"net": TWO_PAD, "layer": "Top Layer", "width": 10,
                                                    "start": mid, "end": DS1_2}], board_path=self.board))
        self.assertTrue(out.get("success"), out)
        self.assertEqual(connection_objects(self.board, TWO_PAD), 0, "a closed connection is still drawn")
        un = tool(main.get_unrouted_connections(None, nets=[TWO_PAD], board_path=self.board))
        self.assertEqual(un["connection_count"], 0, un)


if __name__ == "__main__":
    unittest.main()
