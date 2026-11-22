"""Live test of get_erc_violations in a running Altium Designer. A49: on a
project with some hundreds of violations of a few kinds the result is a
summary, not every violation in full: one group per level and type with its
count and its first three details, the counts summing to the total, and the
full list in a file the result names.

See tests/live_altium.py for how to run it. It works on a copy of the
SpiritLevel-SL1 example Altium installs (skipped when it is not there): its
four child sheets as a flat project with a second copy of each, so every
designator and net is there twice (276 violations of six kinds on AD25,
69 of them suppressed by the example's no-ERC markers), closed unsaved.

A50: a violation Altium suppresses (a no-ERC marker on its pin) is left out
of the groups and counted as suppressed; on a one-sheet copy of the same
example's power sheet, a test point moved so its input pin floats.
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
        self.assertEqual(len(full["violations"]), erc["total"] + erc["suppressed"])
        listed = [v for v in full["violations"] if not v["suppressed"]]
        for g in groups:
            mine = [v["detail"] for v in listed if (v["level"], v["type"]) == (g["level"], g["type"])]
            self.assertEqual(len(mine), g["count"], g["type"])
            self.assertEqual(mine[:3], g["first"], g["type"])
        print(f"\nA49: {erc['total']} violations ({erc['suppressed']} more suppressed) in {len(groups)} "
              f"groups, {len(text)} characters; "
              f"the file {path.stat().st_size} bytes")


@unittest.skipUnless(LIVE, SKIP_REASON)
@unittest.skipUnless((SL1 / "SL_Power.SchDoc").exists(), f"Altium's example sheet is not in {SL1}")
class LiveErcSuppressedTest(unittest.TestCase):
    """A50: a violation Altium suppresses (a no-ERC marker on its pin) is
    left out of the groups and counted apart, as Altium's Messages panel
    leaves it out; the full list keeps it, marked."""

    FLOATING = "Nets containing floating input pins"

    @classmethod
    def setUpClass(cls):
        check_scripts_are_this_checkouts()

    def setUp(self):
        tmp = Path(win32api.GetLongPathName(tempfile.mkdtemp(prefix="erc_live_")))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        # A one-sheet project: the example's power sheet, whose test point
        # TP1 has an input pin
        self.sheet = tmp / "SL_Power.SchDoc"
        shutil.copyfile(SL1 / "SL_Power.SchDoc", self.sheet)
        self.project = tmp / "Suppressed.PrjPcb"
        self.project.write_text("[Design]\r\nVersion=1.0\r\n\r\n[Document1]\r\nDocumentPath=SL_Power.SchDoc\r\n",
                                encoding="latin-1")
        self.addCleanup(close_all_under, str(tmp))

    def edit(self, operations):
        out = json.loads(asyncio.run(main.edit_schematic(None, str(self.sheet), operations, save=True)))
        self.assertTrue(out.get("success"), out)

    def erc(self):
        erc = json.loads(asyncio.run(main.get_erc_violations(None, project_path=str(self.project))))
        if erc.get("full_list"):
            self.addCleanup(Path(erc["full_list"]).unlink, missing_ok=True)
        return erc

    def floating(self, erc):
        return [g for g in erc["groups"] if g["type"] == self.FLOATING]

    def test_a_violation_under_a_no_erc_marker_is_counted_apart(self):
        # TP1 moved to an empty corner: its input pin floats. The pin points
        # down 100 mil from the body, so its connection point is the origin.
        self.edit([{"op": "move_component", "designator": "TP1", "x": 1500, "y": 1500}])
        before = self.erc()
        self.assertEqual(len(self.floating(before)), 1, f"the fixture made no floating input pin: {before}")
        self.assertIn("TP1", self.floating(before)[0]["first"][0])
        self.assertEqual(before.get("suppressed", 0), 0, before)

        self.edit([{"op": "add_no_erc", "x": 1500, "y": 1500}])
        after = self.erc()
        self.assertEqual(self.floating(after), [],
                         f"a violation Altium suppresses is still listed: {self.floating(after)}")
        # The floating input pin's error and its net's no-driving-source warning
        self.assertEqual(after.get("suppressed"), 2, after)
        self.assertEqual(after["total"], before["total"] - 2, (before, after))
        self.assertEqual(after["errors"], before["errors"] - 1, (before, after))
        self.assertEqual(after["total"], after["fatal"] + after["errors"] + after["warnings"], after)
        self.assertEqual(sum(g["count"] for g in after["groups"]), after["total"], after)
        self.assertFalse(any("TP1" in d for g in after["groups"] for d in g["first"]), after)

        # The full list keeps every violation, the suppressed ones marked
        full = json.loads(Path(after["full_list"]).read_text(encoding="utf-8"))
        marked = [v for v in full["violations"] if v.get("suppressed")]
        self.assertEqual(len(marked), 2, full)
        self.assertTrue(all("TP1" in v["detail"] for v in marked), marked)
        self.assertEqual(len(full["violations"]), after["total"] + after["suppressed"], full)
        print(f"\nA50: {before['total']} violations before the marker; after it {after['total']} "
              f"listed and {after['suppressed']} suppressed")


if __name__ == "__main__":
    unittest.main()
