"""Live test of get_layout(include_touching=true) in a running Altium
Designer (A6): a pour that reaches beyond the area is given by its net,
layer and bounding box, not with its whole outline.

See tests/live_altium.py for how to run it. On a new board it places a
2000 x 2000 mil pour, a small pour and a track, then reads a 200 mil area.
"""
import unittest

from tests.live_altium import LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close, new_board, tool

if LIVE:
    import main


def _square(x1, y1, x2, y2):
    return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]


@unittest.skipUnless(LIVE, SKIP_REASON)
class LiveLayoutTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        check_scripts_are_this_checkouts()

    def setUp(self):
        self.name = new_board()
        self.addCleanup(close, self.name)
        out = tool(main.place_copper(
            None,
            tracks=[{"net": "", "layer": "Top Layer", "width": 10, "start": [20, 50], "end": [80, 50]}],
            pours=[{"net": "", "layer": "Bottom Layer", "name": "BIG", "outline": _square(-1000, -1000, 1000, 1000)},
                   {"net": "", "layer": "Top Layer", "name": "SMALL", "outline": _square(10, 70, 90, 90)}]))
        self.assertTrue(out.get("success", True) and "error" not in out, out)

    def test_pour_reaching_out_is_given_by_its_box(self):
        out = tool(main.get_layout(None, area=[-50, -50, 150, 150], include_touching=True))
        self.assertTrue(out["success"], out)
        self.assertEqual([p["name"] for p in out["pours"]], ["SMALL"])
        self.assertEqual(len(out["pours"][0]["outline"]), 4)
        self.assertEqual(out["beyond_area"], [{"type": "pour", "name": "BIG", "net": "", "layer": "Bottom Layer",
                                               "bbox": [-1000, -1000, 1000, 1000], "vertices": 4}])
        self.assertEqual(out["counts"]["pours"], 1)
        self.assertEqual(out["counts"]["beyond_area"], 1)
        self.assertEqual(len(out["tracks"]), 1)

    def test_full_outlines_gives_it_whole(self):
        out = tool(main.get_layout(None, area=[-50, -50, 150, 150], include_touching=True, full_outlines=True))
        self.assertTrue(out["success"], out)
        self.assertEqual(sorted(p["name"] for p in out["pours"]), ["BIG", "SMALL"])
        self.assertEqual(out["beyond_area"], [])


if __name__ == "__main__":
    unittest.main()
