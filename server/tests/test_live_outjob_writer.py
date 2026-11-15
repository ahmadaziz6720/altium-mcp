"""Live test of write_outjob and make_assembly_files (A12), in a running
Altium Designer.

It drives Altium, so it is not in the offline set CI runs. With Altium open:

    set ALTIUM_LIVE=1
    python -m unittest tests.test_live_outjob_writer -v      (from server/)

It runs this checkout's scripts on a copy of the SpiritLevel-SL1 example
project Altium installs, in a temporary folder, closed unsaved. An OutJob is
written from the JLCPCB preset, read back by get_outjob_settings, added to
the project and run by run_output_jobs; the files Altium writes are checked
for the layers and the format asked (the Gerber and Excellon headers, the
BOM and pick and place columns). The OutJob is then edited (Gerber and pick
and place units, the output folder) and run again while Altium still has it
open, and the files show the edit. Last, make_assembly_files turns Altium's
BOM and pick and place into JLCPCB's columns, applies a rotation table and
zips the Gerbers and drill files.
"""
import csv
import io
import re
import shutil
import tempfile
import time
import unittest
import zipfile
from pathlib import Path

import win32api

from tests.live_altium import (LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close_all_under,
                               open_project, script, tool)

if LIVE:
    import main  # noqa: E402

EXAMPLES = Path(r"C:\Users\Public\Documents\Altium\AD25\Examples")
SL1 = EXAMPLES / "SpiritLevel-SL1"
PROJECT = "SL1 Xilinx Spartan-IIE PQ208 Rev1.02.PrjPcb"
STEM = "SL1 Xilinx Spartan-IIE PQ208 Rev1.02"

# The layers a 2-layer board's JLCPCB set holds (the page's list), by the
# extension Altium gives each
JLC_GERBERS = {".GTL", ".GBL", ".GTO", ".GBO", ".GTS", ".GBS", ".GTP", ".GBP", ".GM"}


def head(path, n=4000):
    return Path(path).read_bytes()[:n].decode("latin-1")


@unittest.skipUnless(LIVE, SKIP_REASON)
@unittest.skipUnless(SL1.exists(), f"Altium's example project is not at {SL1}")
class LiveOutJobWriterTest(unittest.TestCase):

    def setUp(self):
        check_scripts_are_this_checkouts()
        tmp = Path(win32api.GetLongPathName(tempfile.mkdtemp(prefix="outjob_live_")))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.tmp = tmp
        self.folder = tmp / "SL1"
        shutil.copytree(SL1, self.folder)
        self.project = str(self.folder / PROJECT)
        self.addCleanup(close_all_under, str(self.folder))
        opened = open_project(self.project)
        self.assertEqual(opened.lower(), self.project.lower())

    def files(self, folder):
        return {p.name: p for p in Path(folder).iterdir() if p.is_file()}

    def test_preset_written_read_back_run_edited_and_made_into_assembly_files(self):
        outjob = str(self.folder / "JLCPCB.OutJob")

        # 1. Written from the preset, and the tool's own read-back agrees
        out = tool(main.write_outjob(None, outjob, preset="fab_jlcpcb"))
        self.assertTrue(out.get("success"), out)
        self.assertTrue(out["created"], out)
        self.assertEqual(out["differences"], [], out)
        container = out["container"]
        self.assertEqual(out["output_folder"], "JLCPCB", out)

        # 2. get_outjob_settings reads back what the preset sets
        s = tool(main.get_outjob_settings(None, outjob))
        self.assertNotIn("error", s, s)
        by_type = {o["type"]: o for o in s["outputs"]}
        self.assertEqual(set(by_type), {"Gerber", "NC Drill", "BOM_PartType", "Pick Place"}, s)
        for o in s["outputs"]:
            self.assertEqual(o["connected_containers"], [container], o)
        g = by_type["Gerber"]["gerber"]
        self.assertEqual((g["units"], g["decimals"], g["origin"], g["zeroes"]),
                         ("Metric", "4", "Absolute", "SuppressLeadingZeroes"), g)
        self.assertTrue(g["plot_board_profile"], g)
        plotted = {l["name"] for l in g["plotted_layers"]}
        for name in ("Top Layer", "Bottom Layer", "Top Overlay", "Bottom Overlay", "Top Solder", "Bottom Solder",
                     "Top Paste", "Bottom Paste", "Mid Layer 1", "Mid Layer 30", "Internal Plane 16"):
            self.assertIn(name, plotted)
        self.assertFalse(any(n.startswith("Mechanical") or n == "Keep-Out Layer" for n in plotted),
                         "one outline only: the board profile")
        d = by_type["NC Drill"]["nc_drill"]
        self.assertEqual((d["Units"], d["NumberOfUnits"], d["NumberOfDecimals"], d["ZeroesMode"],
                          d["OriginPosition"], d["GenerateSeparatePlatedNonPlatedFiles"]),
                         ("Imperial", "2", "5", "KeepLeadingAndTrailingZeroes", "Absolute", "True"), d)
        b = by_type["BOM_PartType"]["bom"]
        self.assertEqual(b["format"], "csv", b)
        self.assertEqual(b["columns"], ["Comment", "Designator", "Footprint", "LCSC Part #"], b)
        p = by_type["Pick Place"]["pick_place"]
        self.assertEqual((p["Units"], p["GenerateCSVFormat"], p["GenerateTextFormat"]),
                         ("Metric", "True", "False"), p)
        c = next(c for c in s["containers"] if c["name"] == container)
        self.assertEqual((c["type"], c["base_path"], c["release_managed"], c["add_to_project"]),
                         ("GeneratedFiles", "JLCPCB", False, False), c)

        # a preset over an existing file is refused, the file unchanged
        before = Path(outjob).read_bytes()
        again = tool(main.write_outjob(None, outjob, preset="fab_jlcpcb"))
        self.assertFalse(again.get("success"), again)
        self.assertEqual(Path(outjob).read_bytes(), before)

        # 3. Run in Altium: the files it writes have the layers and format asked
        added = tool(main.add_project_document(None, self.project, outjob))
        self.assertTrue(added.get("success"), added)
        run = tool(main.run_output_jobs(None, [container], outjob))
        self.assertTrue(run.get("success"), run)
        self.assertIs(run.get("outjob_reloaded"), False, run)
        out_dir = self.folder / "JLCPCB"
        made = self.files(out_dir)
        exts = {Path(n).suffix.upper() for n in made}
        self.assertTrue(JLC_GERBERS <= exts, sorted(made))
        self.assertFalse({".GM1", ".GKO"} & exts, "one outline only")
        gtl = head(out_dir / f"{STEM}.GTL")
        self.assertIn("%FSLAX44Y44*%", gtl)
        self.assertIn("%MOMM*%", gtl)
        drills = sorted(n for n in made if n.upper().endswith(".TXT") and "Holes" in n)
        self.assertTrue(any("NonPlated" in n for n in drills) and any("-Plated" in n for n in drills), drills)
        for n in drills:
            text = head(out_dir / n, 400)
            self.assertTrue(text.startswith("M48"), n)
            self.assertIn(";FILE_FORMAT=2:5", text)
            self.assertRegex(text, r"\nINCH\r?\n", "inches, leading and trailing zeroes kept (no LZ/TZ)")
        boms = [n for n in made if n.lower().endswith(".csv") and not n.startswith("Pick Place")]
        self.assertEqual(len(boms), 1, sorted(made))
        bom_path = out_dir / boms[0]
        header = bom_path.read_text(encoding="utf-8-sig").splitlines()[0]
        self.assertEqual(header, "Comment,Designator,Footprint,LCSC Part #")
        pnp_path = out_dir / f"Pick Place for {STEM}.csv"
        self.assertIn('"Center-X(mm)","Center-Y(mm)"', pnp_path.read_text(encoding="latin-1"))

        # 4. Edited while Altium has it open: Gerber in inches 2:5, pick and
        # place in mils, another folder; the second run shows the edit. The
        # OutJob is opened here (the first run may leave it open or not), so
        # Altium holds the file as it was before the edit
        state = script(f"Obj1 := Client.OpenDocument('OUTPUTJOB', '{outjob}');\n"
                       f"ResultText := BoolToStr(Client.IsDocumentOpen('{outjob}'), True) + ' ' + "
                       "BoolToStr(Obj1.Modified, True);").strip()
        self.assertEqual(state, "True False", "Altium has the OutJob open, as saved")
        out = tool(main.write_outjob(None, outjob, output_folder="JLCPCB inch",
                                     gerber={"units": "inch", "format": "2:5"}, pick_place={"units": "mil"}))
        self.assertTrue(out.get("success"), out)
        self.assertFalse(out["created"], out)
        self.assertEqual(out["differences"], [], out)
        s = tool(main.get_outjob_settings(None, outjob))
        by_type = {o["type"]: o for o in s["outputs"]}
        g = by_type["Gerber"]["gerber"]
        self.assertEqual((g["units"], g["decimals"], g["origin"]), ("Imperial", "5", "Absolute"), g)
        self.assertEqual(by_type["Pick Place"]["pick_place"]["Units"], "Imperial")
        self.assertEqual(by_type["NC Drill"]["nc_drill"]["Units"], "Imperial", "an output not named is kept")
        # Altium may notice the file changed and reopen it itself; given a
        # moment, the OutJob is open again before the run
        time.sleep(3)
        self.assertEqual(script(f"ResultText := BoolToStr(Client.IsDocumentOpen('{outjob}'), True);").strip(),
                         "True", "Altium has the OutJob open before the second run")
        run = tool(main.run_output_jobs(None, [container], outjob))
        self.assertTrue(run.get("success"), run)
        self.assertIs(run.get("outjob_reloaded"), True, "Altium had the OutJob open from before the edit")
        self.assertIs(run.get("outjob_unsaved_changes"), False, run)
        inch_dir = self.folder / "JLCPCB inch"
        self.assertTrue(inch_dir.is_dir(), "the second run wrote to the new folder")
        gtl = head(inch_dir / f"{STEM}.GTL")
        self.assertIn("%FSLAX25Y25*%", gtl, "the run used the edited file, not Altium's open copy")
        self.assertIn("%MOIN*%", gtl)
        pnp_mil = inch_dir / f"Pick Place for {STEM}.csv"
        self.assertIn('"Center-X(mil)"', pnp_mil.read_text(encoding="latin-1"))

        # an OutJob with unsaved changes in Altium is run as Altium has it,
        # not closed (which would drop them), and the result says so
        script(f"Obj1 := Client.GetDocumentByPath('{outjob}');\nObj1.SetModified(True);\n"
               "ResultText := BoolToStr(Obj1.Modified, True);")
        run = tool(main.run_output_jobs(None, [container], outjob))
        self.assertTrue(run.get("success"), run)
        self.assertIs(run.get("outjob_unsaved_changes"), True, run)
        self.assertIs(run.get("outjob_reloaded"), False, run)
        self.assertIn("unsaved changes", run.get("note", ""), run)

        # 5. The offline step on Altium's files: JLCPCB's columns, the
        # rotation table, the zip
        table = self.tmp / "rotations.csv"
        table.write_text("footprint,rotation,layer,note\nCR2012-0805,90,,test row\n", encoding="utf-8")
        asm_dir = self.tmp / "asm"
        out = tool(main.make_assembly_files(None, "jlcpcb", str(bom_path), str(pnp_path), str(out_dir),
                                            str(asm_dir), rotations_path=str(table)))
        self.assertTrue(out.get("success"), out)
        bom_rows = list(csv.reader(io.StringIO(Path(out["bom_file"]).read_text(encoding="utf-8-sig"))))
        self.assertEqual(bom_rows[0], ["Comment", "Designator", "Footprint", "LCSC Part #"])
        altium_rows = [r for r in csv.reader(io.StringIO(bom_path.read_text(encoding="utf-8-sig"))) if r][1:]
        self.assertEqual(len(bom_rows) - 1, len(altium_rows))
        self.assertEqual(out["bom_rows"], len(altium_rows))
        self.assertTrue(out["missing_part_number"], "the example has no LCSC Part # parameter")
        cpl = list(csv.DictReader(io.StringIO(Path(out["cpl_file"]).read_text(encoding="utf-8-sig"))))
        self.assertEqual(list(cpl[0]), ["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        alt = self._altium_pnp(pnp_path)
        self.assertEqual({r["Designator"] for r in cpl}, set(alt))
        self.assertEqual(out["cpl_rows"], len(alt))
        r10 = next(r for r in cpl if r["Designator"] == "R10")
        self.assertEqual(alt["R10"]["Footprint"], "CR2012-0805")
        self.assertEqual(float(r10["Rotation"]), (float(alt["R10"]["Rotation"]) + 90) % 360)
        self.assertAlmostEqual(float(r10["Mid X"]), float(alt["R10"]["Center-X(mm)"]), places=4)
        self.assertEqual(r10["Layer"], "Top")
        corrected = {c["designator"] for c in out["rotations_applied"]}
        self.assertEqual(corrected, {d for d, r in alt.items() if r["Footprint"] == "CR2012-0805"})
        # the example's schematic has parts the board does not place, and the
        # board test points the schematic does not have: each is named
        listed = {d.strip() for r in altium_rows for d in r[1].split(",")}
        self.assertEqual(out["only_in_bom"], sorted(listed - set(alt)), out)
        self.assertEqual(out["only_in_cpl"], sorted(set(alt) - listed), out)
        with zipfile.ZipFile(out["zip_file"]) as z:
            names = set(z.namelist())
        self.assertTrue(all("/" not in n for n in names), "flat, no folder inside")
        self.assertEqual({Path(n).suffix.upper() for n in names if not n.upper().endswith(".TXT")}, JLC_GERBERS)
        self.assertEqual({n for n in names if n.upper().endswith(".TXT")}, set(drills))
        for skipped in (f"{STEM}.REP", f"{STEM}.DRR", "Status Report.Txt"):
            self.assertNotIn(skipped, names)
            self.assertIn(skipped, out["not_zipped"])

        # the pick and place in mils gives the same places in mm
        out_mil = tool(main.make_assembly_files(None, "jlcpcb", str(bom_path), str(pnp_mil), str(inch_dir),
                                                str(self.tmp / "asm_mil"), rotations_path=str(table)))
        self.assertTrue(out_mil.get("success"), out_mil)
        cpl_mil = {r["Designator"]: r for r in csv.DictReader(
            io.StringIO(Path(out_mil["cpl_file"]).read_text(encoding="utf-8-sig")))}
        for r in cpl:
            self.assertAlmostEqual(float(cpl_mil[r["Designator"]]["Mid X"]), float(r["Mid X"]), delta=0.001)
            self.assertAlmostEqual(float(cpl_mil[r["Designator"]]["Mid Y"]), float(r["Mid Y"]), delta=0.001)

    def _altium_pnp(self, path):
        lines = Path(path).read_text(encoding="latin-1").splitlines()
        start = next(i for i, l in enumerate(lines) if l.startswith('"Designator"'))
        return {r["Designator"]: r for r in csv.DictReader(lines[start:])}


if __name__ == "__main__":
    unittest.main()
