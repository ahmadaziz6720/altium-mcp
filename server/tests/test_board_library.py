"""Unit tests for board_library (make_pcblib_from_board's reply compared with
the board) and the tool's checks before Altium (pure Python, no Altium
needed: the bridge is faked).

Run from server/:  python -m unittest tests.test_board_library -v
"""
import asyncio
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import board_library as bl  # noqa: E402
import main  # noqa: E402

# A board of four patterns; two R0805 components differ, so Altium writes
# R0805 and R0805_2
REPLY = {
    "board": r"C:\b\Board.PcbDoc", "library_path": r"C:\b\Board.PcbLib", "board_was_open": True,
    "board_modified": False, "board_flag_cleared": False, "made_as": r"C:\b\Board.PcbLib",
    "removed_by_filter": 0,
    "board_components": ["R0805|2", "R0805|2", "R0805|2", "SOIC-8|8", "TP|1", "LOGO|0"],
    "made": ["R0805", "R0805_2", "SOIC-8", "TP", "LOGO"],
    "written": ["R0805|2|9", "R0805_2|2|9", "SOIC-8|8|14", "TP|1|3", "LOGO|0|6"],
}


class SummariseTest(unittest.TestCase):
    def test_everything_written(self):
        out = bl.summarise(REPLY)
        self.assertEqual(out["problems"], [])
        self.assertEqual(out["not_written"], [])
        self.assertEqual(out["footprint_count"], 5)
        self.assertEqual(out["board_patterns"], 4)
        self.assertEqual(out["board_components"], 6)
        self.assertEqual(out["footprints"][1], {"name": "R0805_2", "pads": 2, "primitives": 9, "pattern": "R0805"})
        self.assertNotIn("pattern", out["footprints"][0])
        self.assertNotIn("board_flag_cleared", out)
        self.assertNotIn("removed_by_filter", out)

    def test_a_pattern_not_written(self):
        reply = dict(REPLY, written=["R0805|2|9", "SOIC-8|8|14", "TP|1|3"], made=["R0805", "SOIC-8", "TP"])
        out = bl.summarise(reply)
        self.assertEqual(out["not_written"], ["LOGO"])
        self.assertEqual(len(out["problems"]), 1)
        self.assertIn("LOGO: on the board (1 components)", out["problems"][0])

    def test_pad_counts_must_agree(self):
        reply = dict(REPLY, written=["R0805|3|9", "R0805_2|2|9", "SOIC-8|8|14", "TP|1|3", "LOGO|0|6"])
        out = bl.summarise(reply)
        self.assertEqual(out["problems"], ["R0805: 3 pads, its components on the board have 2"])
        # A component pad count no footprint of its pattern has
        reply = dict(REPLY, board_components=REPLY["board_components"] + ["TP|2"])
        out = bl.summarise(reply)
        self.assertEqual(len(out["problems"]), 1)
        self.assertIn("TP: a component with 2 pads", out["problems"][0])

    def test_kept_but_not_saved(self):
        reply = dict(REPLY, made=REPLY["made"] + ["EXTRA"])
        out = bl.summarise(reply)
        self.assertEqual(out["problems"], ["EXTRA: kept before the save, not in the saved file"])

    def test_a_footprint_of_no_pattern(self):
        reply = dict(REPLY, written=REPLY["written"] + ["OTHER|4|4"], made=REPLY["made"] + ["OTHER"])
        out = bl.summarise(reply)
        self.assertEqual(out["problems"], ["OTHER: not a pattern of the board"])

    def test_scope_of_the_footprints_asked_for(self):
        reply = dict(REPLY, written=["R0805|2|9", "R0805_2|2|9", "TP|1|3"], made=["R0805", "R0805_2", "TP"],
                     removed_by_filter=2)
        out = bl.summarise(reply, ["r0805", " tp "])
        self.assertEqual(out["problems"], [])
        self.assertEqual(out["board_patterns"], 2)
        self.assertEqual(out["board_components"], 4)
        self.assertEqual(out["removed_by_filter"], 2)

    def test_pattern_of(self):
        patterns = bl.board_patterns(["A_1|2", "B|2", "C_D|3"])
        self.assertEqual(bl.pattern_of("a_1", patterns), "A_1")
        self.assertEqual(bl.pattern_of("A_1_2", patterns), "A_1")
        self.assertEqual(bl.pattern_of("B_12", patterns), "B")
        self.assertEqual(bl.pattern_of("C_D", patterns), "C_D")
        self.assertIsNone(bl.pattern_of("B_", patterns))
        self.assertIsNone(bl.pattern_of("B_x", patterns))
        self.assertIsNone(bl.pattern_of("E_2", patterns))

    def test_names_with_a_bar_and_bad_items(self):
        patterns = bl.board_patterns(["X|Y|4", "bad", "Z|n"])
        self.assertEqual(list(patterns), ["X|Y"])
        self.assertEqual(patterns["X|Y"]["pads"], {4})


def run(coro, reply=None):
    """The tool's JSON result with the bridge faked; the calls made."""
    calls = []

    async def fake(command, params, timeout=None):
        calls.append((command, params, timeout))
        if reply is None:
            raise AssertionError(f"Altium was called: {command}")
        return reply
    with mock.patch.object(main.altium_bridge, "execute_command", fake):
        return json.loads(asyncio.run(coro)), calls


class ToolTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.board = os.path.join(self.dir.name, "Board.PcbDoc")
        open(self.board, "w").close()
        self.lib = os.path.join(self.dir.name, "out", "Board.PcbLib")

    def test_refused_before_altium(self):
        out, _ = run(main.make_pcblib_from_board(None, os.path.join(self.dir.name, "none.PcbDoc"), self.lib))
        self.assertIn("Board not found", out["error"])
        out, _ = run(main.make_pcblib_from_board(None, os.path.join(self.dir.name, "x.SchDoc"), self.lib))
        self.assertIn(".PcbDoc", out["error"])
        out, _ = run(main.make_pcblib_from_board(None, self.board, os.path.join(self.dir.name, "x.SchLib")))
        self.assertIn(".pcblib", out["error"])
        existing = os.path.join(self.dir.name, "Old.PcbLib")
        open(existing, "w").close()
        out, _ = run(main.make_pcblib_from_board(None, self.board, existing))
        self.assertIn("already exists", out["error"])
        out, _ = run(main.make_pcblib_from_board(None, self.board, self.lib, footprints=["TP", ""]))
        self.assertIn("pattern names", out["error"])

    def test_request_and_result(self):
        out, calls = run(main.make_pcblib_from_board(None, self.board, self.lib, footprints=[" TP "]),
                         {"success": True, "result": json.dumps(dict(REPLY, written=["TP|1|3"], made=["TP"]))})
        self.assertTrue(out["success"], out)
        command, params, timeout = calls[0]
        self.assertEqual(command, "make_pcblib_from_board")
        self.assertEqual(params["source_board"], main.long_path(self.board))
        self.assertEqual(params["footprints"], ["TP"])
        self.assertTrue(params["library_path"].endswith(os.path.join("out", "Board.PcbLib")))
        self.assertNotIn("board_path", params)
        self.assertEqual(timeout, main.MAKE_PCBLIB_TIMEOUT)
        self.assertEqual(out["footprints"], [{"name": "TP", "pads": 1, "primitives": 3}])
        self.assertIn("make_pcblib_from_board", main.MUTATING_COMMANDS)

    def test_disagreement_fails_and_names_the_file(self):
        reply = dict(REPLY, written=["TP|1|3"], made=["TP"])
        out, _ = run(main.make_pcblib_from_board(None, self.board, self.lib),
                     {"success": True, "result": json.dumps(reply)})
        self.assertFalse(out["success"])
        self.assertIn("was saved at", out["error"])
        self.assertEqual(out["not_written"], ["LOGO", "R0805", "SOIC-8"])

    def test_altium_error(self):
        out, _ = run(main.make_pcblib_from_board(None, self.board, self.lib),
                     {"success": False, "error": "Not on the board: NOPE. Nothing was made."})
        self.assertFalse(out["success"])
        self.assertIn("NOPE", out["error"])
        self.assertFalse(out["library_written"])


if __name__ == "__main__":
    unittest.main()
