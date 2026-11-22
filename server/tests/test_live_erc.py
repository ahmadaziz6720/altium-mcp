"""Live test of get_erc_violations in a running Altium Designer. A49: on a
project with some hundreds of violations of a few kinds the result is a
summary, not every violation in full: one group per level and type with its
count and its first three details, the counts summing to the total, and the
full list in a file the result names.

See tests/live_altium.py for how to run it. It works on a copy of the
SpiritLevel-SL1 example Altium installs (skipped when it is not there): its
four child sheets as a flat project with a second copy of each, so every
designator and net is there twice (276 violations of six kinds on AD25),
closed unsaved.
"""
import asyncio
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.live_altium import LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close_all_under

if LIVE:
    import main
    import win32api

SL1 = Path(r"C:\Users\Public\Documents\Altium\AD25\Examples\SpiritLevel-SL1")
PROJECT = "SL1 Xilinx Spartan-IIE PQ208 Rev1.02.PrjPcb"
TOP = "SL1 Xilinx Spartan-IIE PQ208 Rev1.02.SchDoc"
CHILDREN = ("SL_Config_2E.SchDoc", "SL_FPGA_Auto_2E.SchDoc", "SL_LCD_SW_LED_2E.SchDoc", "SL_Power.SchDoc")

# The result's size a session can take in one reply, with room to spare
MAX_CHARS = 10000


def flat_project_with_copies(folder: Path) -> Path:
    """The example's child sheets with a copy of each, in a flat project (the
    top sheet left out, so every sheet is compiled at the top level)."""
    for name in CHILDREN:
        shutil.copyfile(SL1 / name, folder / name)
        shutil.copyfile(SL1 / name, folder / ("Copy_" + name))
    text = (SL1 / PROJECT).read_text(encoding="latin-1")
    text = text.replace("DocumentPath=" + TOP, "DocumentPath=NotThere.txt")
    extra = "".join(f"[Document{n}]\r\nDocumentPath=Copy_{name}\r\n\r\n"
                    for n, name in enumerate(CHILDREN, start=100))
    i = text.index("[Document1]")
    project = folder / PROJECT
    project.write_text(text[:i] + extra + text[i:], encoding="latin-1")
    return project


@unittest.skipUnless(LIVE, SKIP_REASON)
@unittest.skipUnless((SL1 / PROJECT).exists(), f"Altium's example project is not in {SL1}")
class LiveErcSummaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        check_scripts_are_this_checkouts()

    def setUp(self):
        tmp = Path(win32api.GetLongPathName(tempfile.mkdtemp(prefix="erc_live_")))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.project = str(flat_project_with_copies(tmp))
        self.addCleanup(close_all_under, str(tmp))

    def test_many_violations_come_grouped_with_the_full_list_in_a_file(self):
        text = asyncio.run(main.get_erc_violations(None, project_path=self.project))
        self.assertLess(len(text), MAX_CHARS,
                        f"the result is {len(text)} characters, over {MAX_CHARS}: {text[:300]}")
        erc = json.loads(text)
        self.assertEqual(erc["project_path"].lower(), self.project.lower(), erc)
        self.assertGreater(erc["total"], 200, erc)
        self.assertEqual(erc["total"], erc["fatal"] + erc["errors"] + erc["warnings"], erc)

        groups = erc["groups"]
        self.assertGreaterEqual(len(groups), 4, groups)
        self.assertEqual(sum(g["count"] for g in groups), erc["total"], groups)
        for g in groups:
            self.assertEqual(len(g["first"]), min(3, g["count"]), g)
            self.assertTrue(all(isinstance(d, str) and d for d in g["first"]), g)
        self.assertEqual(len({(g["level"], g["type"]) for g in groups}), len(groups), "a group twice")
        for level, key in (("fatal", "fatal"), ("error", "errors"), ("warning", "warnings")):
            self.assertEqual(sum(g["count"] for g in groups if g["level"] == level), erc[key], level)

        # The full list, every violation in full, in the file named
        path = Path(erc["full_list"])
        self.addCleanup(path.unlink, missing_ok=True)
        full = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(full["project_path"], erc["project_path"])
        self.assertEqual(len(full["violations"]), erc["total"])
        for g in groups:
            mine = [v["detail"] for v in full["violations"] if (v["level"], v["type"]) == (g["level"], g["type"])]
            self.assertEqual(len(mine), g["count"], g["type"])
            self.assertEqual(mine[:3], g["first"], g["type"])
        print(f"\nA49: {erc['total']} violations in {len(groups)} groups, {len(text)} characters; "
              f"the file {path.stat().st_size} bytes")


if __name__ == "__main__":
    unittest.main()
