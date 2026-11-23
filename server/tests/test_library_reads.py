"""Unit tests for the library reads' results (A57): the inventory of
get_symbol_primitives and get_footprint_primitives (no name given) comes back
as compact JSON, one entry a line, and a call with a name is as before (pure
Python, no Altium needed: the bridge is faked). The live test is
tests/test_live_library_reads.py.

Run from server/:  python -m unittest tests.test_library_reads -v
"""
import asyncio
import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import main  # noqa: E402

SYMBOLS = {"library_name": "Big.SchLib", "symbol_count": 2,
           "symbols": [{"name": "R", "description": "Resistor, 0.1 W", "pins": 2},
                       {"name": "U\u00b51", "description": "", "pins": 0}]}
FOOTPRINTS = {"library_name": "Big.PcbLib", "library_path": "", "footprint_count": 1,
              "footprints": [{"name": "0603", "description": "Chip", "pads": 2}]}


def run(coro, result):
    """A tool's text with the bridge faked, and the params it was called with."""
    calls = []

    async def fake(command, params, timeout=None):
        calls.append(params)
        return {"success": True, "result": result}
    with mock.patch.object(main.altium_bridge, "execute_command", fake):
        return asyncio.run(coro), calls


class InventoryJsonTest(unittest.TestCase):
    def test_one_entry_a_line_and_the_same_data(self):
        out = main.library_inventory_json(SYMBOLS, "symbols")
        self.assertEqual(json.loads(out), SYMBOLS)
        lines = out.splitlines()
        self.assertEqual(lines[0], '{"library_name":"Big.SchLib","symbol_count":2,"symbols":[')
        self.assertEqual(lines[1], '{"name":"R","description":"Resistor, 0.1 W","pins":2},')
        self.assertEqual(lines[-1], "]}")
        self.assertEqual(len(lines), 4)

    def test_no_entries_and_no_other_keys(self):
        self.assertEqual(json.loads(main.library_inventory_json({"symbols": []}, "symbols")), {"symbols": []})

    def test_a_result_without_the_list_is_as_before(self):
        out = main.library_inventory_json({"error": "x"}, "symbols")
        self.assertEqual(out, json.dumps({"error": "x"}, indent=2))

    def test_smaller_than_indented(self):
        many = dict(SYMBOLS, symbols=SYMBOLS["symbols"] * 200)
        self.assertLess(len(main.library_inventory_json(many, "symbols")),
                        0.75 * len(json.dumps(many, indent=2)))


class ToolResultTest(unittest.TestCase):
    def test_symbol_inventory_is_compact(self):
        out, calls = run(main.get_symbol_primitives(None, "C:\\x\\Big.SchLib"), SYMBOLS)
        self.assertEqual(out, main.library_inventory_json(SYMBOLS, "symbols"))
        self.assertEqual(calls, [{"library_path": "C:\\x\\Big.SchLib", "symbol_name": ""}])

    def test_names_go_to_altium_as_given_and_the_dump_is_as_before(self):
        dump = {"library_name": "Big.SchLib", "symbol_count": 1, "symbols": [{"symbol_name": "R"}],
                "not_found": ["Q"]}
        out, calls = run(main.get_symbol_primitives(None, "", "R, Q"), dump)
        self.assertEqual(out, json.dumps(dump, indent=2))
        self.assertEqual(calls[0]["symbol_name"], "R, Q")

    def test_footprint_inventory_is_compact(self):
        out, _ = run(main.get_footprint_primitives(None, ""), FOOTPRINTS)
        self.assertEqual(out, main.library_inventory_json(FOOTPRINTS, "footprints"))

    def test_footprint_dump_is_as_before(self):
        dump = {"library_name": "Big.PcbLib", "library_path": "", "footprint_name": "0603",
                "primitives": [], "bodies_3d": []}
        out, _ = run(main.get_footprint_primitives(None, "", "0603"), dump)
        self.assertEqual(out, json.dumps(dump, indent=2))


if __name__ == "__main__":
    unittest.main()
