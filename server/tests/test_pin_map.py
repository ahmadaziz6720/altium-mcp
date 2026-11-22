"""build_schematic's pin map (A46), offline: keyed by pin number with the
name a field, so pins that share a name are all kept, and with wires only a
count per part, the map in a file. The bridge is faked.

Run from server/:  python -m unittest tests.test_pin_map -v
"""
import asyncio
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import main  # noqa: E402

M = 10000  # Altium's coords per mil


def line(part, number, x, y, name):
    """A line of the bridge's pin_map.txt."""
    return f"PIN|{part}|{number}|{x * M}|{y * M}|{name}"


LINES = [line("U1", "1", 100, 200, "GND"), line("U1", "2", 100, 300, "GND"), line("U1", "3", 100, 400, "GND"),
         line("U1", "4", 500, 200, "VDD"), line("J1", "SH", 900, 100, "SHIELD"),
         line("J1", "SH", 900, 300, "SHIELD"), line("J1", "A1", 800, 100, "RX|TX")]
FULL = {"U1": {"1": {"name": "GND", "x": 100, "y": 200}, "2": {"name": "GND", "x": 100, "y": 300},
               "3": {"name": "GND", "x": 100, "y": 400}, "4": {"name": "VDD", "x": 500, "y": 200}},
        "J1": {"SH": {"name": "SHIELD", "x": 900, "y": 100}, "SH#2": {"name": "SHIELD", "x": 900, "y": 300},
               "A1": {"name": "RX|TX", "x": 800, "y": 100}}}
WIRE = [[100, 200, 500, 200]]


class PinMapTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.lib = self.tmp / "Parts.SchLib"
        self.lib.write_bytes(b"")
        self.data = self.tmp / "data"

    def build(self, lines=LINES, data=None, **args):
        parts = [{"designator": "U1", "symbol_library": str(self.lib), "symbol": "IC", "x": 0, "y": 0}]
        reply = {"success": True, "result": {"success": True, "sheet": "Sheet7.SchDoc", "parts": 2}}
        with mock.patch.object(main.altium_bridge, "execute_command", mock.AsyncMock(return_value=reply)), \
                mock.patch.object(main, "write_altium_text"), \
                mock.patch.object(main, "read_altium_text", return_value="\n".join(lines) + "\n"), \
                mock.patch.object(main, "_data_dir", return_value=data or self.data), \
                mock.patch.object(main.Path, "is_file", return_value=True):
            text = asyncio.run(main.build_schematic(None, parts, **args))
        return text, json.loads(text)

    def test_keyed_by_number_the_pins_sharing_a_name_kept(self):
        _, out = self.build()
        self.assertEqual(out["pin_map"], FULL)

    def test_a_number_already_taken_does_not_lose_a_pin(self):
        _, out = self.build([line("X1", "1", 1, 1, "A"), line("X1", "1#2", 2, 2, "B"), line("X1", "1", 3, 3, "C"),
                             line("X1", "", 4, 4, "D"), line("X1", "", 5, 5, "E")])
        self.assertEqual(sorted(p["name"] for p in out["pin_map"]["X1"].values()), list("ABCDE"))

    def test_a_part_entry_names_its_part_and_none_is_part_a(self):
        # A45: the last field of the bridge's PART line
        part = {"designator": "U1", "symbol_library": str(self.lib), "symbol": "IC", "x": 0, "y": 0}
        reply = {"success": True, "result": {"success": True, "sheet": "Sheet7.SchDoc"}}
        with mock.patch.object(main.altium_bridge, "execute_command", mock.AsyncMock(return_value=reply)) as sent, \
                mock.patch.object(main, "write_altium_text") as written, \
                mock.patch.object(main.Path, "is_file", return_value=False):
            asyncio.run(main.build_schematic(None, [part, dict(part, part="c"), dict(part, part=6)]))
            lines = [row for row in written.call_args.args[1].splitlines() if row.startswith("PART|")]
            self.assertEqual([row.split("|")[9:] for row in lines], [["1"], ["3"], ["6"]])
            sent.reset_mock()
            refused = json.loads(asyncio.run(main.build_schematic(None, [dict(part, part="B2")])))
            self.assertFalse(refused["success"])
            self.assertIn("U1", refused["error"])
            sent.assert_not_called()

    def test_fractions_of_a_mil_are_kept(self):
        _, out = self.build(["PIN|R1|1|393701|-5000|1"])
        self.assertEqual(out["pin_map"], {"R1": {"1": {"name": "1", "x": 39.3701, "y": -0.5}}})

    def test_without_wires_the_map_comes_back_whole_and_no_file_is_written(self):
        for wires in (None, []):
            _, out = self.build(wires=wires, net_labels=[{"x": 100, "y": 200, "text": "N"}])
            self.assertEqual(out["pin_map"], FULL)
            self.assertNotIn("pin_map_file", out)
        self.assertFalse(self.data.exists())

    def test_with_wires_a_count_per_part_and_the_map_in_a_file(self):
        text, out = self.build(wires=WIRE)
        self.assertNotIn("pin_map", out)
        self.assertNotIn("SHIELD", text)
        self.assertEqual(out["pin_counts"], {"U1": 4, "J1": 3})
        path = Path(out["pin_map_file"])
        self.assertEqual(path.parent, self.data / "pin_maps")
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"sheet": "Sheet7.SchDoc", "pin_map": FULL})

    def test_one_file_per_build(self):
        # a closed free sheet's name is the next one's: Sheet7.SchDoc twice
        prj = str(self.tmp / "P.PrjPcb")
        _, free = self.build(wires=WIRE)
        _, again = self.build([line("R9", "1", 7, 7, "1")], wires=WIRE)
        self.assertNotEqual(again["pin_map_file"], free["pin_map_file"])
        self.assertEqual(json.loads(Path(free["pin_map_file"]).read_text(encoding="utf-8"))["pin_map"], FULL)
        with mock.patch.object(main, "_add_to_project", mock.AsyncMock(return_value={"success": True})), \
                mock.patch.object(main, "_project_path", return_value=(prj, "")), \
                mock.patch.object(main, "_new_document_path", side_effect=lambda path, _: (path, "")):
            sheets = [str(self.tmp / folder / "Power.SchDoc") for folder in ("One", "Two")]
            built = [self.build(wires=WIRE, project_path=prj, sheet_path=sheet)[1] for sheet in sheets]
        files = [free["pin_map_file"]] + [out["pin_map_file"] for out in built]
        self.assertEqual(len(set(files)), 3, files)
        self.assertEqual([json.loads(Path(f).read_text(encoding="utf-8"))["sheet"] for f in files],
                         ["Sheet7.SchDoc"] + sheets)

    def test_only_the_newest_files_are_kept(self):
        folder = self.data / "pin_maps"
        folder.mkdir(parents=True)
        other = folder / "notes.json"
        other.write_text("{}")
        old = [folder / f"pin_map_old{n}.json" for n in range(25)]
        for n, path in enumerate(old):
            path.write_text("{}")
            os.utime(path, (1000000 + n, 1000000 + n))
        _, out = self.build(wires=WIRE)
        self.assertEqual(sorted(p.name for p in folder.glob("pin_map_*.json")),
                         sorted([Path(out["pin_map_file"]).name] + [p.name for p in old[-19:]]))
        self.assertTrue(other.exists(), "not the map's file, not the map's to delete")

    def test_a_file_that_cannot_be_written_leaves_the_map_in_the_reply(self):
        blocker = self.tmp / "blocker"
        blocker.write_text("x")
        _, out = self.build(data=blocker / "data", wires=WIRE)
        self.assertEqual(out["pin_map"], FULL)
        self.assertNotIn("pin_map_file", out)
        self.assertIn("could not write", out["pin_map_file_error"])


if __name__ == "__main__":
    unittest.main()
