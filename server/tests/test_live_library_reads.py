"""Live test of the library reads in a running Altium Designer (A57):
get_symbol_primitives and get_footprint_primitives without a name give each
symbol's or footprint's name, description and pin or pad count only, so the
inventory of a library of some hundreds of symbols fits in a result; and the
name argument takes several names, comma-separated, for the details of
several in one call.

See tests/live_altium.py for how to run it. It works on copies of a symbol
library and a footprint library of the "SpiritLevel-SL1" example Altium
installs (skipped when they are not there), made larger with
create_symbols_batch and create_footprints_batch; everything is closed
unsaved at the end.
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.live_altium import LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close_all_under, tool

if LIVE:
    import asyncio
    import main
    import win32api

LIBS = Path(r"C:\Users\Public\Documents\Altium\AD25\Examples\SpiritLevel-SL1\Libraries")
SCHLIB = LIBS / "SpiritLevel_2E.SchLib"
PCBLIB = LIBS / "Spirit_Level_Project.PcbLib"

SYMBOLS = 450
FOOTPRINTS = 300
DESC = "Inventory test part {:03d}, a description of the length libraries hold"
# Today's inventory of the 450 symbols was over this; a result is cut at it
LIMIT = 60000


def pins(i):
    return i % 4 + 1


def pads(i):
    return i % 3 + 1


def text(coro):
    """A tool's result as the client gets it: its text and that text read."""
    out = asyncio.run(coro)
    return out, json.loads(out)


@unittest.skipUnless(LIVE, SKIP_REASON)
@unittest.skipUnless(SCHLIB.exists() and PCBLIB.exists(), f"Altium's example libraries are not at {LIBS}")
class LiveLibraryReadsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        check_scripts_are_this_checkouts()
        # Altium is given the long path: the one it reports back
        cls.tmp = Path(win32api.GetLongPathName(tempfile.mkdtemp(prefix="libreads_live_")))
        cls.lib = cls.tmp / "Big.SchLib"
        cls.fp = cls.tmp / "Big.PcbLib"
        shutil.copyfile(SCHLIB, cls.lib)
        shutil.copyfile(PCBLIB, cls.fp)
        try:
            spec = cls.tmp / "symbols.txt"
            lines = [f"LIBRARY|{cls.lib}"]
            for i in range(SYMBOLS):
                lines.append(f"SYMBOL|INV_{i:03d}|{DESC.format(i)}|1")
                lines += [f"PIN|{p + 1}|P{p + 1}|eElectricPassive|eRotate180|0|{-100 * p}" for p in range(pins(i))]
            spec.write_text("\n".join(lines) + "\n", encoding="utf-8")
            out = tool(main.create_symbols_batch(None, str(spec)))
            if out.get("created") != SYMBOLS:
                raise AssertionError(f"the symbols were not made: {json.dumps(out)[:600]}")
            spec = cls.tmp / "footprints.txt"
            lines = [f"FPLIB|{cls.fp}"]
            for i in range(FOOTPRINTS):
                lines.append(f"FOOTPRINT|INVFP_{i:03d}|{DESC.format(i)}")
                lines += [f"PAD|{p + 1}|{100 * p}|0|0|Top Layer|0|0|0|0|0|40|40|2" for p in range(pads(i))]
            spec.write_text("\n".join(lines) + "\n", encoding="utf-8")
            out = tool(main.create_footprints_batch(None, str(spec)))
            if out.get("created") != FOOTPRINTS:
                raise AssertionError(f"the footprints were not made: {json.dumps(out)[:600]}")
        except Exception:
            cls.tearDownClass()
            raise

    @classmethod
    def tearDownClass(cls):
        close_all_under(str(cls.tmp))
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_symbol_inventory_is_names_descriptions_and_pins(self):
        out, got = text(main.get_symbol_primitives(None, str(self.lib)))
        self.assertLess(len(out), LIMIT, f"the inventory of {got.get('symbol_count')} symbols is "
                                         f"{len(out)} characters")
        made = {s["name"]: s for s in got["symbols"] if s["name"].startswith("INV_")}
        self.assertEqual(len(made), SYMBOLS)
        for s in got["symbols"]:
            self.assertEqual(set(s), {"name", "description", "pins"}, s)
        for i in range(SYMBOLS):
            self.assertEqual(made[f"INV_{i:03d}"], {"name": f"INV_{i:03d}", "description": DESC.format(i),
                                                    "pins": pins(i)})
        self.assertEqual(got["symbol_count"], len(got["symbols"]))
        print(f"\nsymbol inventory: {got['symbol_count']} symbols, {len(out)} characters")

    def test_several_symbols_in_one_call(self):
        got = tool(main.get_symbol_primitives(None, str(self.lib), "INV_001, inv_002,INV_007"))
        self.assertNotIn("error", got, got)
        dumps = {s["symbol_name"]: s for s in got["symbols"]}
        self.assertEqual(sorted(dumps), ["INV_001", "INV_002", "INV_007"], got)
        self.assertEqual(got["symbol_count"], 3)
        for name, i in (("INV_001", 1), ("INV_002", 2), ("INV_007", 7)):
            pin_list = [p for p in dumps[name]["primitives"] if p["type"] == "pin"]
            self.assertEqual(len(pin_list), pins(i), name)
            self.assertEqual(dumps[name]["description"], DESC.format(i))
        self.assertEqual(got.get("not_found", []), [])

    def test_several_symbols_some_missing(self):
        got = tool(main.get_symbol_primitives(None, str(self.lib), "INV_003,NO_SUCH_SYMBOL"))
        self.assertEqual([s["symbol_name"] for s in got["symbols"]], ["INV_003"], got)
        self.assertEqual(got["not_found"], ["NO_SUCH_SYMBOL"], got)

    def test_one_symbol_is_as_before(self):
        got = tool(main.get_symbol_primitives(None, str(self.lib), "inv_005"))
        self.assertEqual(got["symbol_name"], "INV_005", got)
        self.assertEqual(len([p for p in got["primitives"] if p["type"] == "pin"]), pins(5))

    def test_a_name_with_a_comma_is_read_whole(self):
        # The example library holds "Jumper, 2-Pin": not two names
        got = tool(main.get_symbol_primitives(None, str(self.lib), "Jumper, 2-Pin"))
        self.assertEqual(got.get("symbol_name"), "Jumper, 2-Pin", got)
        self.assertNotIn("not_found", got)

    def test_footprint_inventory_is_names_descriptions_and_pads(self):
        out, got = text(main.get_footprint_primitives(None, str(self.fp)))
        self.assertLess(len(out), LIMIT, f"the inventory of {got.get('footprint_count')} footprints is "
                                         f"{len(out)} characters")
        for f in got["footprints"]:
            self.assertEqual(set(f), {"name", "description", "pads"}, f)
        made = {f["name"]: f for f in got["footprints"] if f["name"].startswith("INVFP_")}
        self.assertEqual(len(made), FOOTPRINTS)
        for i in range(FOOTPRINTS):
            self.assertEqual(made[f"INVFP_{i:03d}"], {"name": f"INVFP_{i:03d}", "description": DESC.format(i),
                                                      "pads": pads(i)})
        self.assertEqual(got["footprint_count"], len(got["footprints"]))
        print(f"\nfootprint inventory: {got['footprint_count']} footprints, {len(out)} characters")

    def test_several_footprints_in_one_call(self):
        got = tool(main.get_footprint_primitives(None, str(self.fp), "INVFP_004,invfp_005, NONE_SUCH"))
        self.assertNotIn("error", got, got)
        dumps = {f["footprint_name"]: f for f in got["footprints"]}
        self.assertEqual(sorted(dumps), ["INVFP_004", "INVFP_005"], got)
        for name, i in (("INVFP_004", 4), ("INVFP_005", 5)):
            self.assertEqual(len([p for p in dumps[name]["primitives"] if p["type"] == "pad"]), pads(i), name)
            self.assertIn("bodies_3d", dumps[name])
        self.assertEqual(got["not_found"], ["NONE_SUCH"], got)
        self.assertEqual(got["footprint_count"], 2)


if __name__ == "__main__":
    unittest.main()
