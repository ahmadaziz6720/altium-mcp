"""Live test of spec_file in a running Altium Designer (A58): a sheet built
by build_schematic from a JSON file, then changed by edit_schematic from
another, each read back from the saved .SchDoc.

See tests/live_altium.py for how to run it. Everything is made in a
temporary folder, the parts from a copy of the "SpiritLevel-SL1" example's
library (skipped when it is not there), and closed at the end.
"""
import asyncio
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.live_altium import LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close_all_under, tool

if LIVE:
    import main
    import win32api
    from schdoc_reader import coord, read_schdoc

SCHLIB = Path(r"C:\Users\Public\Documents\Altium\AD25\Examples\SpiritLevel-SL1\Libraries\SpiritLevel_2E.SchLib")
NOTE = "From a file"
VALUE = "10 µF ±5%"


def saved(sheet):
    """What the saved sheet holds of what the test draws, in mils."""
    records = read_schdoc(sheet)
    out = {"parts": {}, "values": [], "wires": [], "labels": [], "ports": [], "notes": [], "junctions": []}

    def at(rec, x="LOCATION.X", y="LOCATION.Y"):
        return round(coord(rec, x), 2), round(coord(rec, y), 2)

    parts = {i: at(rec) for i, rec in enumerate(records) if rec and rec.get("RECORD") == "1"}
    for rec in records:
        if not rec:
            continue
        kind, owner = rec.get("RECORD"), int(rec.get("OWNERINDEX", -2)) + 1
        if kind == "34" and owner in parts:
            out["parts"][rec["TEXT"]] = parts[owner]
        elif kind == "41" and rec.get("NAME") == "SpecValue":
            out["values"].append(rec["TEXT"])
        elif kind == "27":
            out["wires"].append([at(rec, f"X{n}", f"Y{n}") for n in range(1, int(rec["LOCATIONCOUNT"]) + 1)])
        elif kind == "25":
            out["labels"].append((rec["TEXT"], *at(rec)))
        elif kind == "17":
            out["ports"].append((rec["TEXT"], *at(rec)))
        elif kind == "4" and rec.get("TEXT") == NOTE:
            out["notes"].append(at(rec))
        elif kind == "29":
            out["junctions"].append(at(rec))
    out["wires"].sort()
    out["labels"].sort()
    return out


@unittest.skipUnless(LIVE, SKIP_REASON)
@unittest.skipUnless(SCHLIB.exists(), f"Altium's example library is not at {SCHLIB}")
class LiveSpecFileTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        check_scripts_are_this_checkouts()
        # Altium is given the long path: the one it reports back
        cls.tmp = Path(win32api.GetLongPathName(tempfile.mkdtemp(prefix="specfile_live_")))
        cls.addClassCleanup(shutil.rmtree, cls.tmp, ignore_errors=True)
        cls.addClassCleanup(close_all_under, str(cls.tmp))

    def call(self, name, **args):
        """As a client calls it, through the server."""
        # The pin map's file goes to the test's folder, not the user's
        with mock.patch.object(main, "_data_dir", return_value=self.tmp / "data"):
            try:
                content = asyncio.run(main.mcp.call_tool(name, args))
            except Exception as e:
                self.fail(f"{name} was not run: {e}")
        return json.loads(content[0].text)

    def spec(self, name, content):
        path = self.tmp / name
        path.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
        return str(path)

    def test_build_and_edit_from_a_file(self):
        lib = self.tmp / "Parts.SchLib"
        shutil.copyfile(SCHLIB, lib)
        project = self.tmp / "Spec.PrjPcb"
        self.assertTrue(tool(main.create_project(None, str(project)))["success"])
        sheet = self.tmp / "Spec.SchDoc"
        build = {
            "parts": [{"designator": "R1", "symbol_library": str(lib), "symbol": "RES", "x": 2000, "y": 3000,
                       "parameters": {"SpecValue": VALUE}},
                      {"designator": "R2", "symbol_library": str(lib), "symbol": "RES", "x": 3000, "y": 3000}],
            "wires": [[2000, 2000, 2500, 2000, 2500, 2400], [2500, 2000, 3000, 2000]],
            "junctions": [{"x": 2500, "y": 2000}],
            "net_labels": [{"x": 2100, "y": 2000, "text": "FROM_FILE"}],
            "power_ports": [{"x": 3000, "y": 2000, "text": "GND"}],
            "notes": [{"x": 1500, "y": 1500, "text": NOTE}],
            "project_path": str(project),
            "sheet_path": str(sheet),
        }
        out = self.call("build_schematic", spec_file=self.spec("build.json", build))
        self.assertTrue(out.get("success"), out)
        self.assertEqual(sorted(out["pin_counts"]), ["R1", "R2"])
        self.assertEqual(saved(sheet), {
            "parts": {"R1": (2000, 3000), "R2": (3000, 3000)},
            "values": [VALUE],
            "wires": [[(2000, 2000), (2500, 2000), (2500, 2400)], [(2500, 2000), (3000, 2000)]],
            "junctions": [(2500, 2000)],
            "labels": [("FROM_FILE", 2100, 2000)],
            "ports": [("GND", 3000, 2000)],
            "notes": [(1500, 1500)],
        })

        edit = {"operations": [{"op": "move_component", "designator": "R2", "x": 101.6, "y": 76.2},
                               {"op": "add_wire", "points": [[50.8, 38.1], [63.5, 38.1]]},
                               {"op": "add_net_label", "x": 50.8, "y": 38.1, "text": "EDITED"}],
                "unit": "mm", "save": True}
        path = self.spec("edit.json", edit)
        before = sheet.read_bytes()
        both = self.call("edit_schematic", sheet_path=str(sheet), unit="mil", spec_file=path)
        self.assertFalse(both.get("success"), both)
        self.assertEqual(sheet.read_bytes(), before, "a refused edit changed the saved sheet")

        out = self.call("edit_schematic", sheet_path=str(sheet), spec_file=path)
        self.assertFalse(out.get("errors") or out.get("error"), out)
        got = saved(sheet)
        self.assertEqual(got["parts"], {"R1": (2000, 3000), "R2": (4000, 3000)})
        self.assertIn([(2000, 1500), (2500, 1500)], got["wires"])
        self.assertEqual(len(got["wires"]), 3, got)
        self.assertEqual(got["labels"], [("EDITED", 2000, 1500), ("FROM_FILE", 2100, 2000)])


if __name__ == "__main__":
    unittest.main()
