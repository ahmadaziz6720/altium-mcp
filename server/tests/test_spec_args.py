"""spec_file on build_schematic and edit_schematic (A58), offline: the tools
are called as a client calls them, through the server, and the bridge is
faked. What reaches Altium from a file is what the inline call sends; an
argument in both places, or a file that cannot be used, sends nothing.

Run from server/:  python -m unittest tests.test_spec_args -v
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


class SpecFileTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(main.long_path(tmp.name))
        lib = self.tmp / "Parts.SchLib"
        lib.write_bytes(b"")
        project = self.tmp / "P.PrjPcb"
        project.write_bytes(b"")
        self.build = {
            "parts": [{"designator": "R1", "symbol_library": str(lib), "symbol": "RES", "x": 1000.5, "y": 2000,
                       "comment": "10 Ω", "parameters": {"Value": "10 µF"}}],
            "wires": [[1000, 2000, 1500, 2000]],
            "junctions": [{"x": 1500, "y": 2000}],
            "net_labels": [{"x": 1200, "y": 2000, "text": "OUT"}],
            "power_ports": [{"x": 1500, "y": 2000, "text": "GND"}],
            "notes": [{"x": 900, "y": 900, "text": "note"}],
            "project_path": str(project),
            "sheet_path": str(self.tmp / "New.SchDoc"),
        }
        self.edit = {
            "sheet_path": str(self.tmp / "Sheet.SchDoc"),
            "operations": [{"op": "add_wire", "points": [[25.4, 50.8], [38.1, 50.8]]},
                           {"op": "add_net_label", "x": 25.4, "y": 50.8, "text": "OUT"}],
            "unit": "mm",
            "save": True,
        }
        self.tools = {"build_schematic": self.build, "edit_schematic": self.edit}

    def spec(self, content, encoding="utf-8"):
        fd, path = tempfile.mkstemp(suffix=".json", dir=self.tmp)
        with os.fdopen(fd, "wb") as f:
            text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
            f.write(text.encode(encoding))
        return path

    def call(self, name, args):
        """The tool's reply, and all it sent to Altium."""
        sent = []

        async def bridge(command, params):
            sent.append((command, params))
            return {"success": True, "result": {"success": True, "sheet": "Sheet1.SchDoc"}}

        async def add(*where, **more):
            sent.append(("add_to_project", where, more))
            return {"success": True}

        with mock.patch.object(main.altium_bridge, "execute_command", bridge), \
                mock.patch.object(main, "_add_to_project", add), \
                mock.patch.object(main, "write_altium_text", lambda path, text: sent.append((Path(path).name, text))), \
                mock.patch.object(main, "read_altium_text", return_value=""), \
                mock.patch.object(main, "_data_dir", return_value=self.tmp / "data"):
            try:
                content = asyncio.run(main.mcp.call_tool(name, args))
            except Exception as e:
                self.fail(f"{name} was not run: {e}")
        out = json.loads(content[0].text)
        out.pop("pin_map_file", None)  # a new file each build
        return out, sent

    def refused(self, name, args, *words):
        out, sent = self.call(name, args)
        self.assertFalse(out.get("success"), out)
        for word in words:
            self.assertIn(word, out["error"])
        self.assertEqual(sent, [], "a refused call reached Altium")

    def test_both_tools_take_a_spec_file(self):
        schemas = {t.name: t.inputSchema for t in asyncio.run(main.mcp.list_tools())}
        for name in self.tools:
            self.assertIn("spec_file", list(schemas[name]["properties"]))
            self.assertEqual(schemas[name].get("required", []), [], "the file can hold every other argument")

    def test_from_a_file_as_inline(self):
        for name, args in self.tools.items():
            with self.subTest(name):
                inline, sent = self.call(name, args)
                self.assertTrue(inline["success"], inline)
                self.assertTrue(sent)
                for encoding in ("utf-8", "utf-8-sig", "utf-16"):
                    self.assertEqual(self.call(name, {"spec_file": self.spec(args, encoding)}), (inline, sent))

    def test_the_others_may_be_inline(self):
        for name, args in self.tools.items():
            with self.subTest(name):
                rest = {k: v for k, v in args.items() if k != "sheet_path"}
                self.assertEqual(self.call(name, {"sheet_path": args["sheet_path"], "spec_file": self.spec(rest)}),
                                 self.call(name, args))

    def test_a_file_with_parts_only_is_the_pin_read(self):
        out, _ = self.call("build_schematic", {"spec_file": self.spec({"parts": self.build["parts"]})})
        self.assertIn("pin_map", out)

    def test_an_argument_inline_and_in_the_file_is_refused(self):
        for name, args in self.tools.items():
            path = self.spec(args)
            for key, value in args.items():
                with self.subTest(f"{name} {key}"):
                    self.refused(name, {key: value, "spec_file": path}, key, "inline")

    def test_a_default_or_an_empty_value_given_inline_is_given(self):
        for name, key, value in (("edit_schematic", "unit", "mil"), ("edit_schematic", "save", False),
                                 ("edit_schematic", "operations", []), ("build_schematic", "wires", []),
                                 ("build_schematic", "project_path", "")):
            with self.subTest(f"{name} {key}"):
                self.refused(name, {key: value, "spec_file": self.spec(self.tools[name])}, key, "inline")

    def test_without_unit_and_save_mils_unsaved(self):
        args = {k: v for k, v in self.edit.items() if k not in ("unit", "save")}
        explicit = self.call("edit_schematic", dict(args, unit="mil", save=False))
        self.assertIs(explicit[1][-1][1]["save"], False)
        for given in (args, {"spec_file": self.spec(args)}):
            self.assertEqual(self.call("edit_schematic", given), explicit)

    def test_the_file_is_typed_as_the_call(self):
        args = dict(self.edit, save="false")
        self.assertEqual(self.call("edit_schematic", {"spec_file": self.spec(args)}), self.call("edit_schematic", args))
        self.refused("edit_schematic", {"spec_file": self.spec(dict(self.edit, save="maybe"))}, "save")
        self.refused("build_schematic", {"spec_file": self.spec(dict(self.build, wires=None))}, "wires")
        self.refused("build_schematic", {"spec_file": self.spec(dict(self.build, parts={"R1": {}}))}, "parts")

    def test_a_file_that_cannot_be_used_is_refused(self):
        for name in self.tools:
            for path, word in ((str(self.tmp / "none.json"), "spec_file"),
                               ("relative.json", "full path"),
                               (str(self.tmp), "spec_file"),
                               (self.spec("{not json"), "spec_file"),
                               (self.spec([1, 2]), "object"),
                               (self.spec({"wire": []}), "wire"),
                               (self.spec({"spec_file": "x"}), "spec_file")):
                with self.subTest(f"{name} {path}"):
                    self.refused(name, {"spec_file": path}, word)

    def test_what_is_required_is_asked_for(self):
        self.refused("build_schematic", {}, "parts")
        self.refused("build_schematic", {"spec_file": self.spec({"wires": self.build["wires"]})}, "parts")
        self.refused("edit_schematic", {}, "sheet_path", "operations")
        self.refused("edit_schematic", {"sheet_path": self.edit["sheet_path"]}, "operations")


if __name__ == "__main__":
    unittest.main()
