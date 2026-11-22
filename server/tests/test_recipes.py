"""Offline tests of docs/recipes.md: run_altium_script's description names it
by a path that exists, each script passes the sandbox's checks, and each is
the script its proof ran in Altium. No Altium is touched: the live helpers are
only asked for their script text, with the call that would run it replaced.

Run from server/:  python -m unittest tests.test_recipes -v
"""
import asyncio
import os
import re
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import main  # noqa: E402
import sandbox  # noqa: E402
from tests import (live_altium, test_live_compile_refresh, test_live_pcblib_from_board,  # noqa: E402
                   test_live_symbol_footprint)

RECIPES = Path(main.__file__).resolve().parent.parent / "docs" / "recipes.md"
TEMPLATE = (Path(main.__file__).parent / "SandboxScript" / "Sandbox.pas").read_text(encoding="utf-8")
# <...>, not {...}: braces are a comment in Pascal
VALUES = {"<project>": r"C:\Work\Example.PrjPcb", "<sheet>": r"C:\Work\Example.SchDoc",
          "<designator>": "U1", "<kind>": "eNoERC"}


def scripts():
    """{item code: script} of the file's sections that hold one."""
    out = {}
    for section in re.split(r"(?m)^## ", RECIPES.read_text(encoding="utf-8"))[1:]:
        blocks = re.findall(r"(?ms)^```pascal\n(.*?)^```", section)
        assert len(blocks) <= 1, f"two scripts in one section: {section.splitlines()[0]}"
        if blocks:
            out[section.split()[0]] = blocks[0].strip()
    return out


def sent(module, helper, *args, **kwargs):
    """The script a live test's helper sends."""
    with mock.patch.object(module, "script", return_value="True|x|") as script:
        getattr(module, helper)(*args, **kwargs)
    return script.call_args[0][0].strip()


def proved():
    """{item code: the script a live test ran in Altium and passed with}."""
    case = mock.Mock(unsafe=True)  # it has the test's assertEqual
    case.run_on_sheet.return_value = "removed"
    test_live_compile_refresh.LiveCompileAfterScriptEditTest.remove_by_script(case, "<kind>", notice=True)
    removal = case.run_on_sheet.call_args[0][0].replace("{sheet}", "<sheet>").strip()
    return {
        "A52": removal,
        "A55": sent(test_live_pcblib_from_board, "project_state", "<project>"),
        "A56": sent(test_live_symbol_footprint, "read_models", "<sheet>", "<designator>", in_library=False),
        "A62": sent(live_altium, "open_project", "<project>"),
    }


class DescriptionTest(unittest.TestCase):
    def test_the_description_names_the_file_by_an_existing_absolute_path(self):
        tools = {t.name: t for t in asyncio.run(main.mcp.list_tools())}
        named = re.search(r"([A-Za-z]:[\\/][^\r\n]*recipes\.md)", tools["run_altium_script"].description)
        self.assertIsNotNone(named, "run_altium_script's description names no recipes file")
        path = Path(named.group(1))
        self.assertTrue(path.is_absolute())
        self.assertTrue(path.is_file(), f"no file at {path}")
        self.assertEqual(path, RECIPES)


class RecipesTest(unittest.TestCase):
    def test_each_script_is_the_one_its_proof_ran(self):
        self.assertEqual(scripts(), proved())

    def test_each_script_passes_the_sandbox_checks(self):
        for code, script in scripts().items():
            with self.subTest(code):
                for mark, value in VALUES.items():
                    script = script.replace(mark, value)
                self.assertNotRegex(script, r"<[a-z]+>", "a placeholder the test does not know")
                split = sandbox.split_var_block(script)
                names = sandbox.declared_names(split.decls)
                self.assertEqual(sandbox.check_script(split.body, names, split.body_offset), [])
                self.assertEqual(sandbox.lint_script(split.body, split.body_offset, split.decls), [])
                self.assertIn("ResultText :=", sandbox.build_script(TEMPLATE, script, "log", "out").text)

    def test_a_script_that_removes_sends_the_notice(self):
        # Without it the compile keeps the removed object (A48 b)
        for code, script in scripts().items():
            with self.subTest(code):
                self.assertEqual(script.count(".RemoveSchObject("), script.count("SCHM_PrimitiveRegistration"))


if __name__ == "__main__":
    unittest.main()
