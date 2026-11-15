"""Unit tests for assembly_files and make_assembly_files (A12), no Altium.

The fixtures are Altium's own output for the SpiritLevel-SL1 example
project, made in AD25 by an OutJob from the fab_jlcpcb preset: its BOM in
CSV and its pick and place in CSV in mm and in mil.

From server/:  python -m unittest tests.test_assembly_files -v
"""
import asyncio
import csv
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import assembly_files as af  # noqa: E402

FIX = Path(__file__).parent / "fixtures"
BOM = FIX / "altium_bom_jlcpcb.csv"
PNP_MM = FIX / "altium_pick_place_mm.csv"
PNP_MIL = FIX / "altium_pick_place_mil.csv"

GERBER = "G04*\r\n%FSLAX44Y44*%\r\n%MOMM*%\r\nG01*\r\nM02*\r\n"
DRILL = "M48\r\n;FILE_FORMAT=2:5\r\nINCH\r\nT01C0.01181\r\n%\r\nT01\r\nX0763779Y0677165\r\nM30\r\n"


def rows(path):
    return list(csv.reader(io.StringIO(Path(path).read_text(encoding="utf-8-sig"))))


class ReadTest(unittest.TestCase):
    def test_altium_bom(self):
        header, bom = af.read_bom(str(BOM))
        self.assertEqual(header, ["Comment", "Designator", "Footprint", "LCSC Part #"])
        self.assertEqual(len(bom), 46)
        self.assertEqual(bom[0]["Designator"], "C1, C2, C3")
        self.assertEqual(af.split_designators(bom[0]["Designator"]), ["C1", "C2", "C3"])

    def test_altium_pick_place_mm_and_mil_agree(self):
        unit, mm = af.read_pick_place(str(PNP_MM))
        self.assertEqual(unit, "mm")
        unit, mil = af.read_pick_place(str(PNP_MIL))
        self.assertEqual(unit, "mil")
        self.assertEqual(len(mm), 113)
        by = {p["designator"]: p for p in mil}
        for p in mm:
            q = by[p["designator"]]
            self.assertAlmostEqual(p["x_mm"], q["x_mm"], delta=0.001)
            self.assertAlmostEqual(p["y_mm"], q["y_mm"], delta=0.001)
            self.assertEqual(p["rotation"], q["rotation"])
        s1 = next(p for p in mm if p["designator"] == "S1")
        self.assertEqual((s1["footprint"], s1["layer"], s1["x_mm"], s1["rotation"]),
                         ("PCB_SWITCH", "TopLayer", 177.1, 90.0))
        self.assertTrue(any(af.side(p["layer"]) == "bottom" for p in mm))

    def test_not_a_csv_pick_place(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp, "pp.txt")
            p.write_text("Designator Comment Layer\nR1 1k TopLayer\n")
            with self.assertRaises(af.AssemblyError):
                af.read_pick_place(str(p))


class RotationTableTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def table(self, text):
        p = os.path.join(self.tmp, "r.csv")
        Path(p).write_text(text, encoding="utf-8")
        return p

    def test_shipped_table_is_empty_and_reads(self):
        svc = af.load_services()["jlcpcb"]
        path = os.path.join(svc["folder"], svc["rotations"])
        self.assertEqual(af.load_rotations(path), [])

    def test_rows_patterns_and_layers(self):
        rules = af.load_rotations(self.table(
            "# comment\nfootprint,rotation,layer,note\nSOT-23,180,,exact\nSOT*,-90,Bottom,pattern\nsot*,90,,any\n"))
        self.assertEqual(len(rules), 3)
        self.assertEqual(af.rotation_rule(rules, "SOT-23", "top")["rotation"], 180)
        self.assertEqual(af.rotation_rule(rules, "sot-223", "bottom")["rotation"], -90)
        self.assertEqual(af.rotation_rule(rules, "SOT-223", "top")["rotation"], 90)
        self.assertIsNone(af.rotation_rule(rules, "0805", "top"))
        self.assertEqual(rules[1]["line"], 4)

    def test_bad_tables(self):
        for text in ("", "name,rotation\nX,1\n", "footprint,rotation\nX,ninety\n", "footprint,rotation,layer\nX,90,Mid\n",
                     "footprint,rotation\n,90\n"):
            with self.assertRaises(af.AssemblyError, msg=text):
                af.load_rotations(self.table(text))
        with self.assertRaises(af.AssemblyError):
            af.load_rotations(os.path.join(self.tmp, "missing.csv"))


class MakeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.gerbers = self.tmp / "out"
        self.gerbers.mkdir()
        for ext in (".GTL", ".GBL", ".GTO", ".GM"):
            (self.gerbers / f"Board{ext}").write_text(GERBER)
        (self.gerbers / "Board-RoundHoles-Plated.TXT").write_text(DRILL)
        (self.gerbers / "Board.REP").write_text("Layer report\r\n")
        (self.gerbers / "Status Report.Txt").write_text("Project Outputs Generation Report\r\n")
        (self.gerbers / "sub").mkdir()
        (self.gerbers / "sub" / "Other.GTL").write_text(GERBER)
        self.svc = af.load_services()["jlcpcb"]
        self.table = self.tmp / "rot.csv"
        self.table.write_text("footprint,rotation,layer,note\nCR2012-0805,90,Top,\nCR2012*,180,,\n", encoding="utf-8")

    def make(self, **kw):
        args = dict(service=self.svc, bom_path=str(BOM), pnp_path=str(PNP_MM), gerber_dir=str(self.gerbers),
                    out_dir=str(self.tmp / "jlc"), rotations_path=str(self.table))
        args.update(kw)
        return af.make(**args)

    def test_files_in_the_services_form(self):
        out = self.make()
        self.assertTrue(out["success"])
        bom = rows(out["bom_file"])
        self.assertEqual(bom[0], ["Comment", "Designator", "Footprint", "LCSC Part #"])
        self.assertEqual(len(bom) - 1, out["bom_rows"])
        self.assertEqual(bom[1], ["100uF 16V", "C1, C2, C3", "CAPPR2-5X6.8", ""])
        self.assertEqual(len(out["missing_part_number"]), 113, "the example sets no LCSC Part #")
        cpl = list(csv.DictReader(io.StringIO(Path(out["cpl_file"]).read_text(encoding="utf-8-sig"))))
        self.assertEqual(list(cpl[0]), ["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        self.assertEqual(len(cpl), 113)
        s1 = next(r for r in cpl if r["Designator"] == "S1")
        self.assertEqual((s1["Mid X"], s1["Mid Y"], s1["Layer"], s1["Rotation"]), ("177.1000", "14.2400", "Top", "90"))
        self.assertEqual({r["Layer"] for r in cpl}, {"Top", "Bottom"})
        # rotations: the Top row for top parts, the pattern for the bottom ones
        by = {r["Designator"]: r for r in cpl}
        self.assertEqual(by["R10"]["Rotation"], "270")      # 180 + 90
        self.assertEqual(by["R22"]["Rotation"], "90")       # bottom, 270 + 180
        applied = {a["designator"]: a for a in out["rotations_applied"]}
        self.assertEqual(applied["R22"]["rule"], "line 3: CR2012* 180")
        self.assertEqual(applied["R10"]["from"], "180")
        self.assertEqual(out["only_in_bom"], ["JS1", "JS2", "JS3"])
        self.assertEqual(out["only_in_cpl"], ["TP1", "TP2", "TP3"])

    def test_zip_is_flat_and_holds_gerbers_and_drills_only(self):
        out = self.make()
        with zipfile.ZipFile(out["zip_file"]) as z:
            names = sorted(z.namelist())
        self.assertEqual(names, ["Board-RoundHoles-Plated.TXT", "Board.GBL", "Board.GM", "Board.GTL", "Board.GTO"])
        self.assertEqual(out["zipped"]["drill"], ["Board-RoundHoles-Plated.TXT"])
        self.assertEqual(out["not_zipped"], ["Board.REP", "Status Report.Txt"])
        self.assertEqual(out["warnings"][-1:], [w for w in out["warnings"] if "LCSC" in w])

    def test_mil_pick_place_gives_the_same_mm(self):
        a = rows(self.make()["cpl_file"])
        b = rows(self.make(pnp_path=str(PNP_MIL), out_dir=str(self.tmp / "mil"))["cpl_file"])
        for ra, rb in zip(sorted(a[1:]), sorted(b[1:])):
            self.assertEqual(ra[0], rb[0])
            self.assertAlmostEqual(float(ra[1]), float(rb[1]), delta=0.001)
            self.assertAlmostEqual(float(ra[2]), float(rb[2]), delta=0.001)

    def test_refusals_and_warnings(self):
        with self.assertRaises(af.AssemblyError) as e:
            self.make(part_number_parameter="JLCPCB Part #")
        self.assertIn("JLCPCB Part #", str(e.exception))
        self.assertFalse((self.tmp / "jlc").exists(), "nothing written")
        empty = self.tmp / "empty"
        empty.mkdir()
        (empty / "notes.txt").write_text("x")
        with self.assertRaises(af.AssemblyError):
            self.make(gerber_dir=str(empty))
        (self.gerbers / "Board-RoundHoles-Plated.TXT").unlink()
        out = self.make()
        self.assertTrue(any("no drill file" in w for w in out["warnings"]), out["warnings"])

    def test_file_kind(self):
        self.assertEqual(af.file_kind(str(self.gerbers / "Board.GTL")), "gerber")
        self.assertEqual(af.file_kind(str(self.gerbers / "Board-RoundHoles-Plated.TXT")), "drill")
        self.assertIsNone(af.file_kind(str(self.gerbers / "Board.REP")))

    def test_service_names_its_pages(self):
        for key in ("bom", "cpl"):
            srcs = self.svc[key]["source"]
            for s in ([srcs] if isinstance(srcs, str) else srcs):
                self.assertTrue(self.svc["sources"][s]["url"].startswith("https://jlcpcb.com/help/"))
                self.assertEqual(self.svc["sources"][s]["read"], "2026-11-15")
        self.assertEqual(self.svc["cpl"]["columns"], ["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        self.assertIn("Metric(mm)", self.svc["cpl"]["page_text"])


class ToolTest(unittest.TestCase):
    def test_unknown_service(self):
        import main
        out = json.loads(asyncio.run(main.make_assembly_files(None, "pcbway", str(BOM), str(PNP_MM), ".", ".")))
        self.assertFalse(out["success"])
        self.assertIn("jlcpcb", out["error"])

    def test_missing_input(self):
        import main
        out = json.loads(asyncio.run(main.make_assembly_files(None, "jlcpcb", str(FIX / "nope.csv"), str(PNP_MM),
                                                              ".", ".")))
        self.assertFalse(out["success"])
        self.assertIn("BOM not found", out["error"])


if __name__ == "__main__":
    unittest.main()
