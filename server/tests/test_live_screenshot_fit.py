"""Live test of get_screenshot on a schematic sheet, in a running Altium
Designer (A60 (a)). A sheet was captured at whatever zoom it had, its bottom
cut, and zoom_to (designators) is for PCB only. A 'sch' capture now fits the
whole sheet first; zoom_to on a sheet is answered with a warning.

Whether the whole sheet is in the image is read from the image: the sheet's
black border line closed on all four sides, its sides in A3's proportion.

A copy of the power sheet of the SpiritLevel-SL1 example Altium installs is
used (skipped when it is not there), set to A3 and zoomed in, in a temporary
folder, closed unsaved; the document that was in front is shown again. See
tests/live_altium.py for how to run it.
"""
import asyncio
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.live_altium import LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close_all_under, script

if LIVE:
    import io

    import main
    import win32api
    from PIL import Image

SHEET = Path(r"C:\Users\Public\Documents\Altium\AD25\Examples\SpiritLevel-SL1\SL_Power.SchDoc")
BLACK = (0, 0, 0)
A3 = 420 / 297


def black_runs(line, min_len):
    out, start = [], None
    for i, p in enumerate(line + [None]):
        if p == BLACK and start is None:
            start = i
        elif p != BLACK and start is not None:
            if i - start >= min_len:
                out.append((start, i - 1))
            start = None
    return out


def sheet_frame(im):
    """The largest closed rectangle of black lines in the image, each side at
    least a quarter of the image's: a sheet's border seen whole. None when
    no such rectangle is there (a border cut by the view or the capture)."""
    im = im.convert("RGB")
    w, h = im.size
    px = im.load()
    rows = [(y, a, b) for y in range(h) for a, b in black_runs([px[x, y] for x in range(w)], w // 4)]
    cols = [(x, a, b) for x in range(w) for a, b in black_runs([px[x, y] for y in range(h)], h // 4)]
    best = None
    for y1, a1, b1 in rows:
        for y2, a2, b2 in rows:
            if y2 - y1 < h // 4 or abs(a1 - a2) > 3 or abs(b1 - b2) > 3:
                continue
            closed = all(any(abs(x - edge) <= 3 and c0 <= y1 + 3 and c1 >= y2 - 3 for x, c0, c1 in cols)
                         for edge in (a1, b1))
            if closed and (best is None or (b1 - a1) * (y2 - y1) > (best[2] - best[0]) * (best[3] - best[1])):
                best = (a1, y1, b1, y2)
    return best


@unittest.skipUnless(LIVE, SKIP_REASON)
@unittest.skipUnless(SHEET.exists(), f"Altium's example sheet is not at {SHEET}")
class LiveScreenshotFitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        check_scripts_are_this_checkouts()

    def setUp(self):
        front = script("if (Client.CurrentView <> nil) and (Client.CurrentView.OwnerDocument <> nil) then\n"
                       "    ResultText := Client.CurrentView.OwnerDocument.FileName;").strip()
        if front:
            self.addCleanup(script, f"Obj1 := Client.GetDocumentByPath('{front}');\n"
                                    "if Obj1 <> nil then Client.ShowDocument(Obj1);")
        tmp = Path(win32api.GetLongPathName(tempfile.mkdtemp(prefix="screenshot_fit_live_")))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.addCleanup(close_all_under, str(tmp))
        self.sheet = tmp / "Sheet.SchDoc"
        shutil.copyfile(SHEET, self.sheet)
        script(f"Obj1 := OpenSchDoc('{self.sheet}');\n"
               f"Client.ShowDocument(Client.GetDocumentByPath('{self.sheet}'));\n"
               "Obj1.SheetStyle := eSheetA3;\n"
               "Obj1.GraphicallyInvalidate;\n"
               "Client.SendMessage('SCH:Zoom', 'Action=ZoomIn', 255, Client.CurrentView);\n"
               "Client.SendMessage('SCH:Zoom', 'Action=ZoomIn', 255, Client.CurrentView);")

    def capture(self, zoom_to=None):
        shot = asyncio.run(main.get_screenshot(None, "sch", zoom_to))
        self.assertIsInstance(shot, list, shot)
        meta = json.loads(shot[0])
        self.assertEqual(meta.get("captured_document"), self.sheet.name, meta)
        return meta, Image.open(io.BytesIO(shot[1].data))

    def assert_whole_sheet(self, im):
        frame = sheet_frame(im)
        self.assertIsNotNone(frame, f"the {im.size[0]}x{im.size[1]} capture shows no closed sheet border: "
                                    "the sheet is cut")
        ratio = (frame[2] - frame[0]) / (frame[3] - frame[1])
        self.assertAlmostEqual(ratio, A3, delta=0.04, msg=f"the closed border {frame} is not the A3 sheet's")

    def test_a_sheet_zoomed_in_is_captured_whole(self):
        meta, im = self.capture()
        self.assert_whole_sheet(im)
        self.assertNotIn("warnings", meta)

    def test_zoom_to_on_a_sheet_is_answered_with_a_warning(self):
        meta, im = self.capture(["C1"])
        self.assertTrue(any("PCB only" in w for w in meta.get("warnings", [])), meta)
        self.assert_whole_sheet(im)


if __name__ == "__main__":
    unittest.main()
