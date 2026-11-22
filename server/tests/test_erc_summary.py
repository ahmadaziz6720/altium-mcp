"""get_erc_violations' reply grouped by level and type (A49), the suppressed
violations left out of the groups (A50), offline."""
import asyncio
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import erc_summary  # noqa: E402


def violation(level, kind, n):
    return {"level": level, "type": kind, "detail": f"{kind} #{n}"}


def reply(violations):
    return {"project_path": r"C:\Work\Board\Board.PrjPcb", "compiled": True, "unsaved_in_altium": [],
            "missing_on_disk": [], "total": len(violations),
            "fatal": sum(v["level"] == "fatal" for v in violations),
            "errors": sum(v["level"] == "error" for v in violations),
            "warnings": sum(v["level"] == "warning" for v in violations), "violations": violations}


class GroupTest(unittest.TestCase):
    def test_one_group_per_level_and_type_with_its_first_three(self):
        vs = ([violation("warning", "Floating net label", i) for i in range(5)]
              + [violation("error", "Duplicate nets", i) for i in range(7)]
              + [violation("warning", "Duplicate nets", 0)]
              + [violation("error", "Unconnected pin", i) for i in range(2)])
        groups = erc_summary.group(vs)
        self.assertEqual([(g["level"], g["type"], g["count"]) for g in groups],
                         [("error", "Duplicate nets", 7), ("error", "Unconnected pin", 2),
                          ("warning", "Floating net label", 5), ("warning", "Duplicate nets", 1)])
        self.assertEqual(groups[0]["first"], ["Duplicate nets #0", "Duplicate nets #1", "Duplicate nets #2"])
        self.assertEqual(groups[1]["first"], ["Unconnected pin #0", "Unconnected pin #1"])
        self.assertEqual(sum(g["count"] for g in groups), len(vs))

    def test_fatal_first_and_an_unknown_level_last(self):
        vs = [violation("odd", "X", 0), violation("warning", "W", 0), violation("fatal", "F", 0)]
        self.assertEqual([g["level"] for g in erc_summary.group(vs)], ["fatal", "warning", "odd"])

    def test_no_violations_no_groups(self):
        out = erc_summary.summarize(reply([]), "f.json")
        self.assertEqual(out["groups"], [])
        self.assertEqual(out["total"], 0)


class SummarizeTest(unittest.TestCase):
    def test_the_list_replaced_by_groups_and_the_file(self):
        data = reply([violation("error", "Duplicate nets", i) for i in range(300)])
        out = erc_summary.summarize(data, r"C:\data\erc.json")
        self.assertNotIn("violations", out)
        self.assertEqual(out["full_list"], r"C:\data\erc.json")
        self.assertNotIn("full_list_error", out)
        for key in ("project_path", "compiled", "unsaved_in_altium", "missing_on_disk", "total", "fatal",
                    "errors", "warnings"):
            self.assertEqual(out[key], data[key], key)
        self.assertEqual(out["groups"][0]["count"], 300)
        self.assertLess(len(json.dumps(out)), len(json.dumps(data)) / 20)
        self.assertEqual(len(data["violations"]), 300, "the reply itself is not changed")

    def test_suppressed_violations_left_out_of_the_groups(self):
        # A50: the bridge marks what Altium suppresses and counts it apart
        listed = [violation("error", "Duplicate nets", i) for i in range(4)]
        hidden = [dict(violation("error", "Floating input pins", 0), suppressed=True),
                  dict(violation("warning", "No driving source", 0), suppressed=True)]
        data = dict(reply(listed), suppressed=2, violations=[dict(v, suppressed=False) for v in listed] + hidden)
        out = erc_summary.summarize(data, "f.json")
        self.assertEqual([(g["type"], g["count"]) for g in out["groups"]], [("Duplicate nets", 4)])
        self.assertEqual((out["total"], out["errors"], out["warnings"], out["suppressed"]), (4, 4, 0, 2))
        self.assertEqual(len(data["violations"]), 6, "the full list keeps them")

    def test_a_file_not_written_says_so(self):
        out = erc_summary.summarize(reply([violation("error", "E", 0)]), "", "could not write")
        self.assertIsNone(out["full_list"])
        self.assertEqual(out["full_list_error"], "could not write")


class FullListTest(unittest.TestCase):
    def test_one_file_per_project_path(self):
        folder = Path(r"C:\data")
        a = erc_summary.full_list_path(folder, r"C:\One\Board.PrjPcb")
        self.assertEqual(a, erc_summary.full_list_path(folder, r"c:\one\board.PrjPcb"))
        self.assertNotEqual(a, erc_summary.full_list_path(folder, r"C:\Two\Board.PrjPcb"))
        self.assertEqual(a.parent, folder)
        self.assertTrue(a.name.startswith("erc_Board_") and a.name.endswith(".json"), a.name)

    def test_a_name_with_odd_characters_makes_a_plain_file_name(self):
        p = erc_summary.full_list_path(Path("d"), r"C:\x\My Board: rev*2.PrjPcb")
        self.assertRegex(p.name, r"^erc_[\w.-]+_[0-9a-f]{8}\.json$")

    def test_written_and_read_back(self):
        data = reply([violation("warning", "W", i) for i in range(4)])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sub" / "erc.json"
            self.assertEqual(erc_summary.write_full_list(data, path), "")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), data)

    def test_a_write_that_fails_gives_the_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            blocker = Path(tmp) / "file"
            blocker.write_text("x")
            error = erc_summary.write_full_list(reply([]), blocker / "erc.json")
        self.assertIn("could not write the full list", error)


class ToolTest(unittest.TestCase):
    """The tool around the bridge's reply, with the bridge mocked."""

    def run_tool(self, bridge_text, folder):
        import main
        with mock.patch.object(main, "_simple_command", mock.AsyncMock(return_value=bridge_text)), \
                mock.patch.object(main, "_data_dir", return_value=Path(folder)):
            return asyncio.run(main.get_erc_violations(None))

    def test_grouped_with_the_file_written(self):
        data = reply([violation("error", "Duplicate nets", i) for i in range(50)])
        with tempfile.TemporaryDirectory() as tmp:
            out = json.loads(self.run_tool(json.dumps(data), tmp))
            self.assertEqual(out["groups"][0]["count"], 50)
            self.assertEqual(json.loads(Path(out["full_list"]).read_text(encoding="utf-8")), data)
            self.assertEqual(Path(out["full_list"]).parent, Path(tmp))

    def test_an_error_passes_through(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_tool("ERROR: No project is focused", tmp), "ERROR: No project is focused")
            failed = json.dumps({"error": "Failed to get ERC violations: timeout"})
            self.assertEqual(self.run_tool(failed, tmp), failed)
            self.assertEqual(list(Path(tmp).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
