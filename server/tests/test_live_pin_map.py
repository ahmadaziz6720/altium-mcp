"""Live test of build_schematic's pin map in a running Altium Designer (A46).
A symbol whose pins share names (four GND, three VDD) and a number (two
shield pins SH) is placed 24 times. With no wires the map holds every pin by
its number, at the connection point Altium gives it; with wires the result
is small, a count per part and the path of the file that holds the map.

See tests/live_altium.py for how to run it. The symbol is made in a copy of
the "SpiritLevel-SL1" example's library (skipped when it is not there); all
is closed unsaved at the end.
"""
import asyncio
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.live_altium import LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close, close_all_under, script, tool

if LIVE:
    import main
    import win32api
    from tests.test_live_symbol_footprint import save_library

SCHLIB = Path(r"C:\Users\Public\Documents\Altium\AD25\Examples\SpiritLevel-SL1\Libraries\SpiritLevel_2E.SchLib")
SYMBOL = "PINMAP_TEST"
NAMES = ["GND"] * 4 + ["VDD"] * 3 + ["SHIELD"] * 2 + [f"IO{n}" for n in range(7)]
NUMBERS = [str(n) for n in range(1, 8)] + ["SH", "SH"] + [str(n) for n in range(8, 15)]
PARTS = 24
# The result's size with wires: a short fixed part and some 15 characters a part
MAX_CHARS = 2000


def sheet_pins(sheet):
    """Every pin on an open sheet, read through Altium: sorted (designator,
    number, name, x, y), the connection point in mils."""
    out = script(f"""var
    D : ISch_Document;
    It, It2 : ISch_Iterator;
    C : ISch_Component;
    P : ISch_Pin;
    X, Y : Integer;
    L : TStringList;
begin
D := SchServer.GetSchDocumentByPath('{sheet}');
L := TStringList.Create;
It := D.SchIterator_Create;
It.AddFilter_ObjectSet(MkSet(eSchComponent));
C := It.FirstSchObject;
while C <> nil do
begin
    It2 := C.SchIterator_Create;
    It2.AddFilter_ObjectSet(MkSet(ePin));
    P := It2.FirstSchObject;
    while P <> nil do
    begin
        X := P.Location.X;
        Y := P.Location.Y;
        if P.Orientation = 0 then X := X + P.PinLength;
        if P.Orientation = 1 then Y := Y + P.PinLength;
        if P.Orientation = 2 then X := X - P.PinLength;
        if P.Orientation = 3 then Y := Y - P.PinLength;
        L.Add(C.Designator.Text + '|' + P.Designator + '|' + P.Name + '|' + IntToStr(X) + '|' + IntToStr(Y));
        P := It2.NextSchObject;
    end;
    C.SchIterator_Destroy(It2);
    C := It.NextSchObject;
end;
D.SchIterator_Destroy(It);
ResultText := L.Text;
L.Free;
end;""")
    pins = [row.split("|") for row in out.splitlines() if row.strip()]
    return sorted((d, num, name, int(x) / 10000, int(y) / 10000) for d, num, name, x, y in pins)


def map_pins(pin_map):
    """A pin map in sheet_pins' form: '#2' taken off a repeated number."""
    return sorted((d, key.split("#")[0], p["name"], p["x"], p["y"])
                  for d, pins in pin_map.items() for key, p in pins.items())


@unittest.skipUnless(LIVE, SKIP_REASON)
@unittest.skipUnless(SCHLIB.exists(), f"Altium's example library is not at {SCHLIB}")
class LivePinMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        check_scripts_are_this_checkouts()
        # Altium is given the long path: the one it reports back
        cls.tmp = Path(win32api.GetLongPathName(tempfile.mkdtemp(prefix="pinmap_live_")))
        cls.addClassCleanup(shutil.rmtree, cls.tmp, ignore_errors=True)
        cls.addClassCleanup(close_all_under, str(cls.tmp))
        cls.lib = cls.tmp / "Parts.SchLib"
        shutil.copyfile(SCHLIB, cls.lib)
        pins = [f"PIN|{num}|{name}|eElectricPassive|eRotate180|0|{-100 * i}"
                for i, (num, name) in enumerate(zip(NUMBERS, NAMES))]
        spec = cls.tmp / "spec.txt"
        # LIBRARY: nothing is made unless that copy is the focused library
        spec.write_text("\n".join([f"LIBRARY|{cls.lib}", f"SYMBOL|{SYMBOL}|Pins sharing a name|1", *pins]) + "\n",
                        encoding="utf-8")
        out = tool(main.create_symbols_batch(None, str(spec)))
        if out.get("created") != 1 or out.get("failed") or out.get("problems"):
            raise AssertionError(f"the test's symbol was not made: {out}")
        save_library(cls.lib)
        close_all_under(str(cls.tmp))
        cls.parts = [{"designator": f"U{i + 1}", "symbol_library": str(cls.lib), "symbol": SYMBOL,
                      "x": 1500 + 1300 * (i % 8), "y": 7500 - 2000 * (i // 8), "orientation": i % 2}
                     for i in range(PARTS)]

    def setUp(self):
        data = tempfile.TemporaryDirectory()
        self.addCleanup(data.cleanup)
        self.data = Path(data.name)

    def build(self, **args):
        with mock.patch.object(main, "_data_dir", return_value=self.data):
            text = asyncio.run(main.build_schematic(None, self.parts, **args))
        out = json.loads(text)
        self.assertTrue(out.get("success"), out)
        self.addCleanup(close, out["sheet"])
        return text, out

    def test_without_wires_every_pin_by_its_number(self):
        text, out = self.build()
        print(f"\n  no wires: {len(text)} characters", flush=True)
        pins = sheet_pins(out["sheet"])
        self.assertEqual(len(pins), PARTS * len(NAMES))
        got = {d: len(p) for d, p in out["pin_map"].items()}
        self.assertEqual(got, {p["designator"]: len(NAMES) for p in self.parts}, "pins of the map were lost")
        self.assertEqual(map_pins(out["pin_map"]), pins)

    def test_with_wires_a_count_per_part_and_the_map_in_a_file(self):
        text, out = self.build(wires=[[1000, 1000, 2000, 1000]])
        print(f"\n  with wires: {len(text)} characters", flush=True)
        self.assertLessEqual(len(text), MAX_CHARS, "the result with wires is too large")
        self.assertNotIn("pin_map", out)
        self.assertEqual(out["pin_counts"], {p["designator"]: len(NAMES) for p in self.parts})
        path = Path(out["pin_map_file"])
        self.assertEqual(path.parent, self.data / "pin_maps")
        saved = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(saved["sheet"], out["sheet"])
        self.assertEqual(map_pins(saved["pin_map"]), sheet_pins(out["sheet"]))


if __name__ == "__main__":
    unittest.main()
