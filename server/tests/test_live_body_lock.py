"""Live test of the flag that locks a placed part's body, in a running Altium
Designer (A71): in a saved sheet every body graphic of a part (its lines,
rectangles, arcs and the like) carries IsNotAccesible=T, so a click on the
body selects the part, not the graphic. Parts placed in Altium's own editor
all have it; parts placed by build_schematic and by edit_schematic's
place_component have to as well.

Two symbols are made in a copy of the "SpiritLevel-SL1" example's library
(skipped when it is not there): eight pins drawn with a rectangle and a line,
and two pins drawn with four arcs. Each is placed ten times by each tool,
half of them while it is the symbol shown in the library editor and half
while the other one is. The flag is read from the saved sheet file: a script
cannot read it. See tests/live_altium.py for how to run it. All is made in a
temporary folder and closed at the end.
"""
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.live_altium import LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close_all_under, script, tool

if LIVE:
    import main
    import win32api
    from schdoc_reader import read_schdoc
    from tests.test_live_symbol_footprint import save_library

EXAMPLES = Path(r"C:\Users\Public\Documents\Altium\AD25\Examples")
SCHLIB = EXAMPLES / "SpiritLevel-SL1" / "Libraries" / "SpiritLevel_2E.SchLib"
SHEET = EXAMPLES / "Mini PC" / "Mini PC - WiFi" / "Connector_WiFi.SchDoc"

EIGHT, TWO = "BODYLOCK_8", "BODYLOCK_2"
# The body graphics each symbol is drawn with, as record types of the file
GRAPHICS = {"4": "label", "5": "bezier", "6": "polyline", "7": "polygon", "8": "ellipse", "9": "pie",
            "10": "round rectangle", "11": "elliptical arc", "12": "arc", "13": "line", "14": "rectangle"}
BODY = {EIGHT: ["line", "rectangle"], TWO: ["arc"] * 4}


def bodies(sheet):
    """The body graphics of each part of a saved sheet, by designator:
    {designator: [(graphic, locked)]}, sorted."""
    records = read_schdoc(sheet)[1:]
    designator = {r["OWNERINDEX"]: r.get("TEXT", "") for r in records
                  if r and r.get("RECORD") == "34" and "OWNERINDEX" in r}
    found = {}
    for i, r in enumerate(records):
        if r and r.get("RECORD") == "1":
            found[designator.get(str(i), f"record {i}")] = []
    for r in records:
        if r and r.get("RECORD") in GRAPHICS and r.get("OWNERINDEX") in designator:
            found[designator[r["OWNERINDEX"]]].append((GRAPHICS[r["RECORD"]], r.get("ISNOTACCESIBLE") == "T"))
    return {d: sorted(g) for d, g in found.items()}


@unittest.skipUnless(LIVE, SKIP_REASON)
@unittest.skipUnless(SCHLIB.exists() and SHEET.exists(), f"Altium's examples are not at {EXAMPLES}")
class LiveBodyLockTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        check_scripts_are_this_checkouts()
        cls.tmp = Path(win32api.GetLongPathName(tempfile.mkdtemp(prefix="bodylock_live_")))
        cls.addClassCleanup(shutil.rmtree, cls.tmp, ignore_errors=True)
        cls.addClassCleanup(close_all_under, str(cls.tmp))
        cls.lib = cls.tmp / "Parts.SchLib"
        shutil.copyfile(SCHLIB, cls.lib)
        eight = [f"PIN|{n}|P{n}|eElectricPassive|eRotate180|100|{-100 * (n - 1)}" for n in range(1, 5)]
        eight += [f"PIN|{n}|P{n}|eElectricPassive|eRotate0|500|{-100 * (n - 5)}" for n in range(5, 9)]
        two = ["PIN|1|A|eElectricPassive|eRotate180|0|0", "PIN|2|B|eElectricPassive|eRotate0|600|0"]
        spec = cls.tmp / "spec.txt"
        spec.write_text("\n".join(
            [f"LIBRARY|{cls.lib}", f"SYMBOL|{EIGHT}|Eight pins|1", *eight,
             "GRAPHIC|rectangle|1|1|0|100|-400|500|100", "GRAPHIC|line|1|1|100|-150|500|-150",
             f"SYMBOL|{TWO}|Two pins|1", *two] +
            [f"GRAPHIC|arc|1|1|{75 + 150 * k}|0|75|0|180" for k in range(4)]) + "\n", encoding="utf-8")
        out = tool(main.create_symbols_batch(None, str(spec)))
        if out.get("created") != 2 or out.get("failed") or out.get("problems"):
            raise AssertionError(f"the test's symbols were not made: {out}")
        save_library(cls.lib)
        close_all_under(str(cls.tmp))

    def setUp(self):
        self.folder = self.tmp / self._testMethodName
        self.project = self.folder / "Lock.PrjPcb"
        self.assertTrue(tool(main.create_project(None, str(self.project))).get("success"))
        self.addCleanup(close_all_under, str(self.folder))

    def show(self, symbol):
        """Open the library with symbol the one shown in its editor."""
        shown = script(f"""var
    Lib : ISch_Lib;
    It : ISch_Iterator;
    C : ISch_Component;
begin
Obj1 := Client.OpenDocument('SchLib', '{self.lib}');
Client.ShowDocument(Obj1);
Lib := SchServer.GetSchDocumentByPath('{self.lib}');
It := Lib.SchLibIterator_Create;
It.AddFilter_ObjectSet(MkSet(eSchComponent));
C := It.FirstSchObject;
while C <> nil do
begin
    if C.LibReference = '{symbol}' then Lib.CurrentSchComponent := C;
    C := It.NextSchObject;
end;
Lib.SchIterator_Destroy(It);
Lib.GraphicallyInvalidate;
ResultText := Lib.CurrentSchComponent.LibReference;
end;""").strip()
        self.assertEqual(shown, symbol, "the library editor does not show the symbol asked")
        focused = script("ResultText := GetWorkspace.DM_FocusedProject.DM_ProjectFullPath;").strip()
        if not (focused == "Free Documents" or focused.lower().startswith(str(self.tmp).lower())):
            self.fail(f"not run: the focused project is not the test's: {focused}")

    def assert_locked(self, got, placed):
        """Every part placed (designator: (symbol, the symbol shown while it was
        placed)) has its body in the saved sheets (got, as bodies() reads
        them), and every body graphic is locked."""
        missing = [d for d in placed if d not in got]
        self.assertEqual(missing, [], "parts not in the saved sheet")
        drawn = {d: [g for g, _ in got[d]] for d in placed}
        self.assertEqual(drawn, {d: BODY[s] for d, (s, _) in placed.items()}, "not the bodies drawn")
        unlocked = {d: [g for g, locked in got[d] if not locked] for d in placed}
        unlocked = {d: g for d, g in unlocked.items() if g}
        for symbol in (EIGHT, TWO):
            mine = [d for d, (s, _) in placed.items() if s == symbol]
            print(f"\n  {symbol}: {len(mine)} placed, {sum(d in unlocked for d in mine)} with an unlocked body "
                  f"({sum(d in unlocked and placed[d][1] == symbol for d in mine)} of them placed while shown)")
        self.assertEqual(unlocked, {}, f"{len(unlocked)} of {len(placed)} placed parts have a body graphic "
                                       "without IsNotAccesible=T: " +
                         "; ".join(f"{d} ({placed[d][0]}, {'shown' if placed[d][1] == placed[d][0] else 'not shown'}):"
                                   f" {', '.join(g)}" for d, g in sorted(unlocked.items())))

    def test_build_schematic_locks_every_body(self):
        placed = {}
        for round_, shown in enumerate((EIGHT, TWO)):
            self.show(shown)
            sheet = self.folder / f"Built{round_}.SchDoc"
            parts = []
            for k in range(5):
                for n, symbol in enumerate((EIGHT, TWO)):
                    designator = f"{'K' if symbol == EIGHT else 'A'}{round_ * 5 + k + 1}"
                    parts.append({"designator": designator, "symbol_library": str(self.lib), "symbol": symbol,
                                  "x": 1000 + 1000 * k, "y": 2000 + 2000 * n})
                    placed[designator] = (symbol, shown)
            out = tool(main.build_schematic(None, parts, project_path=str(self.project), sheet_path=str(sheet)))
            self.assertTrue(out.get("success"), out)
        # One check over both sheets: their designators differ
        got = {**bodies(self.folder / "Built0.SchDoc"), **bodies(self.folder / "Built1.SchDoc")}
        self.assert_locked(got, placed)

    def test_place_component_locks_every_body(self):
        sheet = self.folder / "Edited.SchDoc"
        shutil.copyfile(SHEET, sheet)
        self.assertTrue(tool(main.add_project_document(None, str(self.project), str(sheet))).get("success"))
        placed = {}
        for k in range(10):
            shown = (EIGHT, TWO)[k % 2]
            self.show(shown)
            operations = []
            for n, symbol in enumerate((EIGHT, TWO)):
                designator = f"{'LK' if symbol == EIGHT else 'LA'}{k + 1}"
                operations.append({"op": "place_component", "library": str(self.lib), "symbol": symbol,
                                   "designator": designator, "x": 1000 + 1000 * (k % 5),
                                   "y": 2000 + 2000 * n + 4000 * (k // 5)})
                placed[designator] = (symbol, shown)
            out = tool(main.edit_schematic(None, str(sheet), operations, save=True))
            self.assertTrue(out.get("success"), out)
            self.assertEqual(out.get("applied"), 2, out)
        self.assert_locked(bodies(sheet), placed)
