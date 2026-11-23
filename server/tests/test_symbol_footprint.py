"""Unit tests for symbol_footprint and the checks create_symbols_batch and
create_schematic_symbol make of footprint records before Altium is called
(pure Python, no Altium needed: the bridge is faked).

Run from server/:  python -m unittest tests.test_symbol_footprint -v
"""
import asyncio
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import main  # noqa: E402
import symbol_footprint as sf  # noqa: E402
from altium_files import long_path, read_altium_text  # noqa: E402

PINS = ["1|A|eElectricPassive|eRotate180|0|0", "2|B|eElectricPassive|eRotate0|600|0"]


class ParseRecordTest(unittest.TestCase):
    def test_name_only(self):
        self.assertEqual(sf.parse_record("HDR1X2"), ("HDR1X2", "", ""))

    def test_fields_are_trimmed(self):
        self.assertEqual(sf.parse_record(" SO-G5/P.95 | | 1 "), ("SO-G5/P.95", "", "1"))

    def test_library_is_a_full_existing_pcblib(self):
        with tempfile.TemporaryDirectory() as d:
            lib = os.path.join(d, "Parts.PcbLib")
            open(lib, "w").close()
            model, library, current = sf.parse_record(f"NT|{lib}|0")
            self.assertEqual((model, current), ("NT", "0"))
            self.assertEqual(library.lower(), long_path(lib).lower())

    def test_refused(self):
        with tempfile.TemporaryDirectory() as d:
            lib = os.path.join(d, "Parts.PcbLib")
            open(lib, "w").close()
            other = os.path.join(d, "Parts.SchLib")
            open(other, "w").close()
            for record, text in (("", "no model name"),
                                 ("|" + lib, "no model name"),
                                 ("A|" + lib + "|2", "1 or 0"),
                                 ("A|" + lib + "|1|x", "more than three"),
                                 ("A|" + other, ".PcbLib"),
                                 ("A|" + os.path.join(d, "None.PcbLib"), "not a file"),
                                 ("A|Parts.PcbLib", "full path")):
                with self.assertRaises(ValueError, msg=record) as cm:
                    sf.parse_record(record)
                self.assertIn(text, str(cm.exception), record)


class CheckRecordsTest(unittest.TestCase):
    def test_several_footprints_one_current(self):
        self.assertEqual(sf.check_records(["A||1", "B", "C||0"]),
                         [("A", "", "1"), ("B", "", ""), ("C", "", "0")])

    def test_two_current_refused(self):
        with self.assertRaises(ValueError) as cm:
            sf.check_records(["A||1", "B||1"])
        self.assertIn("current", str(cm.exception))

    def test_a_name_twice_refused(self):
        with self.assertRaises(ValueError) as cm:
            sf.check_records(["A", "a||1"])
        self.assertIn("twice", str(cm.exception))


class NormalizeSpecTest(unittest.TestCase):
    def test_a_spec_without_footprints_is_as_it_was(self):
        text = "LIBRARY|C:\\x.SchLib\nSYMBOL|S|d|1\nPIN|1|A|eElectricPassive|eRotate0|0|0\n"
        self.assertEqual(sf.normalize_spec(text), (text, []))

    def test_records_are_written_in_full_after_their_symbol(self):
        with tempfile.TemporaryDirectory() as d:
            lib = os.path.join(d, "Parts.PcbLib")
            open(lib, "w").close()
            text = ("SYMBOL|S1|d|1\nFOOTPRINT|A\nFOOTPRINT|B|%s|1\n"
                    "EDITSYMBOL|S2\nFOOTPRINT|A|%s\nCOMMENT|x") % (lib, lib)
            out, errors = sf.normalize_spec(text)
            self.assertEqual(errors, [])
            lines = out.split("\n")
            self.assertEqual(lines[1], "FOOTPRINT|A||")
            norm = long_path(lib).lower()
            self.assertEqual(lines[2].lower(), f"footprint|b|{norm}|1")
            self.assertTrue(lines[2].startswith("FOOTPRINT|B|"))
            self.assertEqual(lines[3], "EDITSYMBOL|S2")
            self.assertEqual(lines[4].lower(), f"footprint|a|{norm}|")
            self.assertEqual(lines[5], "COMMENT|x")

    def test_errors_name_the_symbol(self):
        text = "SYMBOL|S1|d|1\nFOOTPRINT|A||1\nFOOTPRINT|B||1\nSYMBOL|S2|d|1\nFOOTPRINT|C"
        out, errors = sf.normalize_spec(text)
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith("S1: "), errors)

    def test_footprint_before_any_symbol(self):
        out, errors = sf.normalize_spec("LIBRARY|x\nFOOTPRINT|A\nSYMBOL|S|d|1\n")
        self.assertEqual(len(errors), 1)
        self.assertIn("line 2", errors[0])

    def test_same_footprint_in_two_symbols_is_fine(self):
        out, errors = sf.normalize_spec("SYMBOL|S1|d|1\nFOOTPRINT|A||1\nSYMBOL|S2|d|1\nFOOTPRINT|A||1")
        self.assertEqual(errors, [])


NO_LIBRARIES = {"success": True, "result": {"installed": [], "project_libraries": []}}


class LookupTest(unittest.TestCase):
    def test_search_order_project_first_pcblibs_once(self):
        self.assertEqual(sf.search_order([r"C:\p\A.PcbLib"], [r"c:\p\a.pcblib", r"C:\i\B.IntLib",
                                                                  r"C:\i\C.PCBLIB", r"C:\i\D.SchLib"]),
                         [r"C:\p\A.PcbLib", r"C:\i\C.PCBLIB"])

    def test_locate_takes_the_first_library_and_skips_unreadable(self):
        held = {"L1": None, "L2": {"X"}, "L3": {"X", "Y"}}
        self.assertEqual(sf.locate(["x", "y", "z"], ["L1", "L2", "L3"], lambda p, n: held[p]),
                         {"X": "L2", "Y": "L3"})

    def test_fill_records_keeps_given_libraries(self):
        records, problems = sf.fill_records([("A", "", "1"), ("B", "lib", "")], ["L"],
                                            lambda p, n: {"A"}, "S")
        self.assertEqual((records, problems), ([("A", "L", "1"), ("B", "lib", "")], []))


def run(coro, replies=None):
    """A tool's JSON result with the bridge faked: replies by command."""
    calls = []

    async def fake(command, params, timeout=None):
        calls.append((command, params))
        if replies is None or command not in replies:
            raise AssertionError(f"Altium was called: {command}")
        reply = replies[command]
        if "spec_file" in params:
            calls[-1] = (command, dict(params, spec=read_altium_text(params["spec_file"])))
        return reply(params) if callable(reply) else reply
    with mock.patch.object(main.altium_bridge, "execute_command", fake):
        return json.loads(asyncio.run(coro)), calls


class ToolChecksTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.lib = os.path.join(self.dir.name, "Parts.PcbLib")
        open(self.lib, "w").close()

    def test_two_current_footprints_are_refused_before_altium(self):
        out, calls = run(main.create_schematic_symbol(None, "S", "d", PINS,
                                                      footprints=[f"A|{self.lib}|1", f"B|{self.lib}|1"]))
        self.assertFalse(out["success"], out)
        self.assertIn("current", out["error"])
        self.assertEqual(calls, [])

    def test_a_missing_library_is_refused_before_altium(self):
        out, calls = run(main.create_schematic_symbol(None, "S", "d", PINS,
                                                      footprints=[f"A|{os.path.join(self.dir.name, 'No.PcbLib')}"]))
        self.assertFalse(out["success"], out)
        self.assertEqual(calls, [])

    def test_the_footprints_go_to_altium_in_full(self):
        reply = {"success": True, "result": {"success": True, "component_name": "S", "problems": []}}
        out, calls = run(main.create_schematic_symbol(None, "S", "d", PINS,
                                                      footprints=["A", f"B|{self.lib}|1"]),
                         {"get_installed_libraries": NO_LIBRARIES, "create_schematic_symbol": reply})
        self.assertEqual([c[0] for c in calls], ["get_installed_libraries", "create_schematic_symbol"])
        records = calls[1][1]["footprints"]
        self.assertEqual(records[0], "A||")
        self.assertTrue(records[1].startswith("B|") and records[1].endswith("|1"), records)
        # A66: a name no library holds is linked by name, and said so
        self.assertEqual(out["problems"], [sf.not_found_problem("S", "A")], out)

    def test_a_name_only_footprint_gets_the_library_that_holds_it(self):
        # A66: the project's library first, then the installed ones
        project = os.path.join(self.dir.name, "Project.PcbLib")
        installed = os.path.join(self.dir.name, "Installed.PcbLib")
        libs = {"success": True, "result": {"installed": [installed, r"C:\x\Parts.IntLib"],
                                            "project_libraries": [project]}}
        holds = {project.upper(): {"A"}, installed.upper(): {"A", "B"}}
        reply = {"success": True, "result": {"success": True, "component_name": "S", "problems": []}}
        with mock.patch.object(main.pcblib_file, "held_footprints",
                               lambda path, names: {n.upper() for n in names} & holds.get(path.upper(), set())):
            out, calls = run(main.create_schematic_symbol(None, "S", "d", PINS, footprints=["a", "B|", "C||0"]),
                             {"get_installed_libraries": libs, "create_schematic_symbol": reply})
        self.assertEqual(calls[0][1], {"library_path": ""})
        self.assertEqual(calls[1][1]["footprints"], [f"a|{project}|", f"B|{installed}|", "C||0"])
        self.assertEqual(out["problems"], [sf.not_found_problem("S", "C")], out)

    def test_a_footprint_with_its_library_asks_altium_nothing_more(self):
        reply = {"success": True, "result": {"success": True, "component_name": "S", "problems": []}}
        out, calls = run(main.create_schematic_symbol(None, "S", "d", PINS, footprints=[f"B|{self.lib}|1"]),
                         {"create_schematic_symbol": reply})
        self.assertEqual([c[0] for c in calls], ["create_schematic_symbol"])
        self.assertEqual(out["problems"], [])

    def test_no_footprints_sends_none(self):
        reply = {"success": True, "result": {"success": True, "component_name": "S"}}
        _, calls = run(main.create_schematic_symbol(None, "S", "d", PINS), {"create_schematic_symbol": reply})
        self.assertNotIn("footprints", calls[0][1])

    def test_a_bad_batch_spec_is_refused_whole_before_altium(self):
        spec = os.path.join(self.dir.name, "spec.txt")
        with open(spec, "w") as f:
            f.write(f"SYMBOL|S1|d|1\nFOOTPRINT|A|{self.lib}|1\nFOOTPRINT|B|{self.lib}|1\n"
                    "SYMBOL|S2|d|1\nPIN|1|A|eElectricPassive|eRotate0|0|0\n")
        out, calls = run(main.create_symbols_batch(None, spec))
        self.assertFalse(out["success"], out)
        self.assertIn("S1", out["error"])
        self.assertIn("nothing was made", out["error"])
        self.assertEqual(calls, [])

    def test_a_batch_spec_goes_to_altium_with_its_records_in_full(self):
        spec = os.path.join(self.dir.name, "spec.txt")
        with open(spec, "w") as f:
            f.write(f"SYMBOL|S1|d|1\nFOOTPRINT|A\nFOOTPRINT|B|{self.lib}\n")
        reply = {"success": True, "result": {"created": 1, "edited": 0, "failed": [], "problems": []}}
        out, calls = run(main.create_symbols_batch(None, spec),
                         {"get_installed_libraries": NO_LIBRARIES, "create_symbols_batch": reply})
        sent = calls[1][1]["spec"].split("\n")
        self.assertEqual(sent[1], "FOOTPRINT|A||")
        self.assertEqual(out["problems"], [sf.not_found_problem("S1", "A")], out)
        self.assertEqual(sent[2].lower(), f"footprint|b|{long_path(self.lib)}|".lower())
        # the caller's own file is as it was
        with open(spec) as f:
            self.assertEqual(f.read(), f"SYMBOL|S1|d|1\nFOOTPRINT|A\nFOOTPRINT|B|{self.lib}\n")

    def test_a_batch_name_only_footprint_gets_its_library(self):
        # A66: looked up for the spec's LIBRARY, written into the spec sent
        spec = os.path.join(self.dir.name, "spec.txt")
        schlib = os.path.join(self.dir.name, "Parts.SchLib")
        with open(spec, "w") as f:
            f.write(f"LIBRARY|{schlib}\nSYMBOL|S1|d|1\nFOOTPRINT|A||1\nEDITSYMBOL|S2\nFOOTPRINT|Z\n")
        libs = {"success": True, "result": {"installed": [self.lib], "project_libraries": []}}
        reply = {"success": True, "result": {"created": 1, "edited": 1, "failed": [], "problems": ["old"]}}
        with mock.patch.object(main.pcblib_file, "held_footprints",
                               lambda path, names: {n.upper() for n in names} & {"A"}):
            out, calls = run(main.create_symbols_batch(None, spec),
                             {"get_installed_libraries": libs, "create_symbols_batch": reply})
        self.assertEqual(calls[0][1]["library_path"].lower(), long_path(schlib).lower())
        sent = calls[1][1]["spec"].split("\n")
        self.assertEqual(sent[2], f"FOOTPRINT|A|{self.lib}|1")
        self.assertEqual(sent[4], "FOOTPRINT|Z||")
        self.assertEqual(out["problems"], ["old", sf.not_found_problem("S2", "Z")], out)


if __name__ == "__main__":
    unittest.main()
