"""Live test of the project setup tools in a running Altium Designer (A10):
create_project makes a .PrjPcb, add_project_document adds an existing
document or a new schematic or board to it, set_board_shape sets a board's
outline from vertices (mils or mm, arcs allowed) or from a closed shape on a
mechanical layer, and build_schematic saves its sheet into a project. Each
is read back through Altium (the project's documents, the board's outline,
get_board_summary) and from the saved files (the documents the .PrjPcb
lists, the outline in the saved .PcbDoc).

See tests/live_altium.py for how to run it. Everything is made in a
temporary folder and closed unsaved at the end; the board tests also use a
copy of the small WiFi board of the "Mini PC" example Altium installs, and
build_schematic a copy of a library of the "SpiritLevel-SL1" example
(skipped when they are not there).
"""
import json
import math
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.live_altium import (LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close_all_under, modified,
                               open_board, open_project, script, tool)

if LIVE:
    import main
    import pythoncom
    import win32api
    from win32com import storagecon as sc

EXAMPLES = Path(r"C:\Users\Public\Documents\Altium\AD25\Examples")
WIFI_DIR = EXAMPLES / "Mini PC" / "Mini PC - WiFi"
WIFI = WIFI_DIR / "WiFi.PcbDoc"
WIFI_SHEET = WIFI_DIR / "Connector_WiFi.SchDoc"
SCHLIB = EXAMPLES / "SpiritLevel-SL1" / "Libraries" / "SpiritLevel_2E.SchLib"


def file_documents(project):
    """The documents a saved .PrjPcb lists, as full paths, lower case."""
    folder = Path(project).parent
    text = Path(project).read_bytes().decode("utf-8-sig", errors="replace")
    return sorted(str((folder / m).resolve()).lower()
                  for m in re.findall(r"^DocumentPath=(.+?)\s*$", text, re.M))


def project_documents(project):
    """The documents Altium's open project lists, as full paths, lower case,
    but the ActiveBOM virtual document Altium may add, which has no file."""
    out = script(f"""var
    P : IProject;
    I : Integer;
    S : String;
P := GetWorkspace.DM_GetProjectFromPath('{project}');
S := '';
if P <> nil then
    for I := 0 to P.DM_LogicalDocumentCount - 1 do
        S := S + P.DM_LogicalDocuments(I).DM_FullPath + '|';
ResultText := S;""")
    return sorted(p.lower() for p in out.strip().split("|") if p and not p.lower().endswith(".virtualbom"))


def saved_outline(board):
    """The board outline in a saved .PcbDoc: (kind, x, y) per vertex in mils
    from the board origin, from the Board6 record (KINDn, VXn, VYn, which
    are absolute)."""
    origin = script(f"Obj1 := PCBServer.GetPCBBoardByPath('{board}');\n"
                    "ResultText := IntToStr(Obj1.XOrigin) + '|' + IntToStr(Obj1.YOrigin);").strip().split("|")
    ox, oy = (int(v) / 10000 for v in origin)
    st =pythoncom.StgOpenStorage(str(board), None, sc.STGM_READ | sc.STGM_SHARE_DENY_WRITE, None, 0)
    sub = st.OpenStorage("Board6", None, sc.STGM_READ | sc.STGM_SHARE_EXCLUSIVE, None, 0)
    stm = sub.OpenStream("Data", None, sc.STGM_READ | sc.STGM_SHARE_EXCLUSIVE, 0)
    data = b""
    while True:
        chunk = stm.Read(65536)
        if not chunk:
            break
        data += chunk
    text = data.decode("latin-1")
    fields = dict(re.findall(r"\|((?:KIND|VX|VY)\d+)=([^|]*)", text))

    def mil(v):
        return float(v.strip().replace("mil", ""))

    out, i = [], 0
    while f"KIND{i}" in fields:
        out.append((int(fields[f"KIND{i}"]), round(mil(fields[f"VX{i}"]) - ox, 3),
                    round(mil(fields[f"VY{i}"]) - oy, 3)))
        i += 1
    return out


def inside(board, x, y):
    """Whether (x, y) mils from the board origin is inside the board outline."""
    out = script(f"""var
    B : IPCB_Board;
B := PCBServer.GetPCBBoardByPath('{board}');
B.BoardOutline.Invalidate;
ResultText := BoolToStr(B.BoardOutline.PointInPolygon(B.XOrigin + {int(x * 10000)}, B.YOrigin + {int(y * 10000)}), True);""")
    return out.strip() == "True"


def save(path):
    out = script(f"Obj1 := Client.GetDocumentByPath('{path}');\n"
                 "ResultText := BoolToStr(Obj1.DoFileSave(''), True);").strip()
    if out != "True":
        raise AssertionError(f"could not save {path}")


class _Temp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        check_scripts_are_this_checkouts()

    def setUp(self):
        # Altium is given the long path: the one it reports back
        self.tmp = Path(win32api.GetLongPathName(tempfile.mkdtemp(prefix="setup_live_")))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        # Everything opened under it, closed unsaved
        self.addCleanup(close_all_under, str(self.tmp))

    def same(self, a, b):
        self.assertEqual(str(a).lower(), str(b).lower())


@unittest.skipUnless(LIVE, SKIP_REASON)
class LiveProjectTest(_Temp):
    def test_create_project(self):
        path = self.tmp / "Setup Test.PrjPcb"
        out = tool(main.create_project(None, str(path)))
        self.assertTrue(out.get("success"), out)
        self.assertTrue(path.is_file(), "no project file on disk")
        self.same(out["project_path"], path)
        self.assertEqual(out["documents"], [])
        self.assertFalse(out["project_modified"], out)
        self.assertEqual(file_documents(path), [])
        self.assertEqual(project_documents(path), [], "the project is open in Altium, empty")
        # Altium's own project file, with its defaults
        self.assertIn("[Design]", path.read_text(encoding="utf-8-sig", errors="replace"))

        before = path.read_bytes()
        again = tool(main.create_project(None, str(path)))
        self.assertFalse(again.get("success"), again)
        self.assertIn("exists", again["error"])
        self.assertEqual(path.read_bytes(), before, "the existing project was changed")

        wrong = tool(main.create_project(None, str(self.tmp / "x.PrjScr")))
        self.assertFalse(wrong.get("success"), wrong)

        # A folder that is not there yet is made
        deeper = self.tmp / "new folder" / "Deeper.PrjPcb"
        out = tool(main.create_project(None, str(deeper)))
        self.assertTrue(out.get("success"), out)
        self.assertTrue(deeper.is_file())

    @unittest.skipUnless(WIFI_SHEET.exists(), f"Altium's example sheet is not at {WIFI_SHEET}")
    def test_add_documents(self):
        prj = self.tmp / "Adds.PrjPcb"
        self.assertTrue(tool(main.create_project(None, str(prj)))["success"])

        sheet = self.tmp / "Main.SchDoc"
        out = tool(main.add_project_document(None, str(prj), str(sheet), create=True))
        self.assertTrue(out.get("success"), out)
        self.assertTrue(out["created"])
        self.assertTrue(sheet.is_file(), "the new sheet was not written")
        self.assertIn({"path": str(sheet), "kind": "SCH"},
                      [{"path": d["path"], "kind": d["kind"]} for d in out["documents"]], out["documents"])
        self.assertTrue(out["in_project_file"], out)
        self.assertFalse(out["project_modified"], "the project file was not saved")

        board = self.tmp / "Main.PcbDoc"
        out = tool(main.add_project_document(None, str(prj), str(board), create=True))
        self.assertTrue(out.get("success"), out)
        self.assertTrue(board.is_file(), "the new board was not written")
        self.assertIn("PCB", [d["kind"] for d in out["documents"] if d["path"].lower() == str(board).lower()])

        existing = self.tmp / "Connector.SchDoc"
        shutil.copyfile(WIFI_SHEET, existing)
        out = tool(main.add_project_document(None, str(prj), str(existing)))
        self.assertTrue(out.get("success"), out)
        self.assertFalse(out["created"])
        self.assertFalse(out["already_in_project"])

        want = sorted(str(p).lower() for p in (sheet, board, existing))
        self.assertEqual(file_documents(prj), want, "the saved project file")
        self.assertEqual(project_documents(prj), want, "the project in Altium")

        again = tool(main.add_project_document(None, str(prj), str(existing)))
        self.assertTrue(again.get("success"), again)
        self.assertTrue(again["already_in_project"])
        self.assertEqual(file_documents(prj), want)

        missing = tool(main.add_project_document(None, str(prj), str(self.tmp / "none.SchDoc")))
        self.assertFalse(missing.get("success"), missing)
        before = existing.read_bytes()
        over = tool(main.add_project_document(None, str(prj), str(existing), create=True))
        self.assertFalse(over.get("success"), over)
        self.assertIn("exists", over["error"])
        self.assertEqual(existing.read_bytes(), before)
        kind = tool(main.add_project_document(None, str(prj), str(self.tmp / "x.OutJob"), create=True))
        self.assertFalse(kind.get("success"), kind)
        self.assertEqual(file_documents(prj), want, "a refused add changed the project")

    @unittest.skipUnless(WIFI.exists(), f"Altium's example board is not at {WIFI}")
    def test_new_document_stays_out_of_the_focused_project(self):
        # A new document can be taken into the focused project: here a copy
        # of the WiFi project, its board in front
        other = self.tmp / "other"
        shutil.copytree(WIFI_DIR, other)
        other_prj = other / "WiFi_miniPCIe.PrjPcb"
        open_project(str(other_prj))
        open_board(str(other / "WiFi.PcbDoc"))
        self.assertFalse(modified(str(other_prj)))
        other_docs = project_documents(other_prj)

        prj = self.tmp / "Mine.PrjPcb"
        self.assertTrue(tool(main.create_project(None, str(prj)))["success"])
        for name in ("New.SchDoc", "New.PcbDoc"):
            out = tool(main.add_project_document(None, str(prj), str(self.tmp / name), create=True))
            self.assertTrue(out.get("success"), out)
        self.assertEqual(project_documents(other_prj), other_docs, "the other project took a new document")
        self.assertFalse(modified(str(other_prj)), "the other project was left modified")
        self.assertEqual(project_documents(prj),
                         sorted(str(self.tmp / n).lower() for n in ("New.SchDoc", "New.PcbDoc")))

    @unittest.skipUnless(SCHLIB.exists(), f"Altium's example library is not at {SCHLIB}")
    def test_build_schematic_into_a_project(self):
        lib = self.tmp / "Parts.SchLib"
        shutil.copyfile(SCHLIB, lib)
        prj = self.tmp / "Built.PrjPcb"
        self.assertTrue(tool(main.create_project(None, str(prj)))["success"])
        sheet = self.tmp / "Built.SchDoc"
        parts = [{"designator": "R1", "symbol_library": str(lib), "symbol": "RES", "x": 1000, "y": 1000},
                 {"designator": "R2", "symbol_library": str(lib), "symbol": "RES", "x": 2000, "y": 1000}]
        out = tool(main.build_schematic(None, parts, project_path=str(prj), sheet_path=str(sheet)))
        self.assertTrue(out.get("success"), out)
        self.assertEqual(out["parts"], 2, out)
        self.assertTrue(sheet.is_file(), "the sheet was not saved")
        self.same(out["sheet_path"], sheet)
        self.assertIn(str(sheet).lower(), [d["path"].lower() for d in out["project"]["documents"]])
        self.assertTrue(out["project"]["in_project_file"])
        self.assertEqual(file_documents(prj), [str(sheet).lower()])
        self.assertEqual(project_documents(prj), [str(sheet).lower()])
        count = script(f"""var
    D : ISch_Document;
    It : ISch_Iterator;
    C : ISch_GraphicalObject;
    N : Integer;
D := SchServer.GetSchDocumentByPath('{sheet}');
N := 0;
It := D.SchIterator_Create;
It.AddFilter_ObjectSet(MkSet(eSchComponent));
C := It.FirstSchObject;
while C <> nil do
begin
    N := N + 1;
    C := It.NextSchObject;
end;
D.SchIterator_Destroy(It);
ResultText := IntToStr(N) + '|' + BoolToStr(Client.GetDocumentByPath('{sheet}').Modified, True);""").strip()
        self.assertEqual(count, "2|False", "the project's sheet holds the parts, saved")

        # A sheet is saved into a project only: neither is given alone
        alone = tool(main.build_schematic(None, parts, sheet_path=str(self.tmp / "Alone.SchDoc")))
        self.assertFalse(alone.get("success"), alone)
        alone = tool(main.build_schematic(None, parts, project_path=str(prj)))
        self.assertFalse(alone.get("success"), alone)


# A 2000 x 1000 mil board with its top right corner rounded (200 mil),
# given clockwise
ROUNDED = [[0, 0], [0, 1000], {"x": 1800, "y": 1000, "arc_center": [1800, 800], "clockwise": True},
           [2000, 800], [2000, 0]]
# A 50 mm round board
ROUND_MM = [{"x": 0, "y": 25, "arc_center": [25, 25], "clockwise": False},
            {"x": 50, "y": 25, "arc_center": [25, 25], "clockwise": False}]


@unittest.skipUnless(LIVE, SKIP_REASON)
@unittest.skipUnless(WIFI.exists(), f"Altium's example board is not at {WIFI}")
class LiveBoardShapeTest(_Temp):
    def setUp(self):
        super().setUp()
        self.board = str(self.tmp / "shape.PcbDoc")
        shutil.copyfile(WIFI, self.board)
        open_board(self.board)

    def summary(self):
        out = tool(main.get_board_summary(None))
        self.same(out["pcb_path"], self.board)
        return out["board_outline"]

    def test_outline_in_mils_with_an_arc(self):
        before = self.summary()
        out = tool(main.set_board_shape(None, outline=ROUNDED, board_path=self.board))
        self.assertTrue(out.get("success"), out)
        self.assertEqual(out["outline"], ROUNDED, "the outline read back")
        self.assertEqual(out["bounding_box"], {"x1": 0, "y1": 0, "x2": 2000, "y2": 1000,
                                               "width": 2000, "height": 1000}, out)
        self.assertEqual(out["unit"], "mil")
        self.assertTrue(out["board_modified"])
        now = self.summary()
        self.assertNotEqual(now, before)
        self.assertEqual((now["x1_mm"], now["y1_mm"], now["width_mm"], now["height_mm"], now["vertex_count"]),
                         (0, 0, 50.8, 25.4, 5), now)
        # an arc, not a corner: the corner is outside, just in from the arc inside
        self.assertFalse(inside(self.board, 1990, 990))
        self.assertTrue(inside(self.board, 1900, 900))
        self.assertTrue(inside(self.board, 1000, 500))
        self.assertTrue(modified(self.board))
        save(self.board)
        self.assertEqual(saved_outline(self.board)[:5],
                         [(0, 0, 0), (0, 0, 1000), (1, 1800, 1000), (0, 2000, 800), (0, 2000, 0)],
                         "the outline in the saved file")

    def test_outline_in_mm(self):
        out = tool(main.set_board_shape(None, outline=ROUND_MM, unit="mm", board_path=self.board))
        self.assertTrue(out.get("success"), out)
        self.assertEqual(out["unit"], "mm")
        self.assertEqual(out["outline"], ROUND_MM)
        self.assertEqual(out["bounding_box"], {"x1": 0, "y1": 0, "x2": 50, "y2": 50, "width": 50, "height": 50})
        now = self.summary()
        self.assertEqual((now["x1_mm"], now["y1_mm"], now["width_mm"], now["height_mm"], now["vertex_count"]),
                         (0, 0, 50, 50, 2), now)
        self.assertTrue(inside(self.board, 984, 984))       # the centre
        self.assertFalse(inside(self.board, 100, 100))      # inside the box, outside the circle

    def test_a_refused_outline_leaves_the_board(self):
        before = self.summary()
        self.assertFalse(modified(self.board))
        crossing = [[100, 0], [1000, 0], [0, 1000], [1000, 2000]]
        out = tool(main.set_board_shape(None, outline=crossing, board_path=self.board))
        self.assertFalse(out.get("success"), out)
        self.assertIn("crosses itself", out["error"])
        bad_arc = [[0, 0], {"x": 1000, "y": 0, "arc_center": [500, 100]}, [1000, 1000]]
        out = tool(main.set_board_shape(None, outline=bad_arc, board_path=self.board))
        self.assertFalse(out.get("success"), out)
        out = tool(main.set_board_shape(None, board_path=self.board))
        self.assertFalse(out.get("success"), out)
        out = tool(main.set_board_shape(None, outline=ROUNDED, mechanical_layer="Mechanical 1",
                                        board_path=self.board))
        self.assertFalse(out.get("success"), out)
        out = tool(main.set_board_shape(None, mechanical_layer="No Such Layer", board_path=self.board))
        self.assertFalse(out.get("success"), out)
        self.assertIn("mechanical layer", out["error"])
        self.assertEqual(self.summary(), before)
        self.assertFalse(modified(self.board), "a refused call changed the board")


# A 3000 x 2000 mil rounded rectangle (250 mil corners) drawn on a mechanical
# layer, its pieces out of order and some reversed: T is a track (x1, y1, x2,
# y2), A an arc (cx, cy, r, start, end), mils and degrees
DRAWN = [("T", 2750, 2000, 250, 2000), ("A", 250, 250, 250, 180, 270), ("T", 3000, 250, 3000, 1750),
         ("A", 2750, 1750, 250, 0, 90), ("T", 0, 1750, 0, 250), ("A", 2750, 250, 250, 270, 360),
         ("T", 250, 0, 2750, 0), ("A", 250, 1750, 250, 90, 180)]
# A mounting hole's circle inside it, and a line below it, not closed
HOLE = ("A", 500, 500, 60, 0, 360)
STRAY = ("T", 0, -500, 3000, -500)


def draw(board, layer, pieces):
    lines = ["var\n    B : IPCB_Board;\n    T : IPCB_Track;\n    A : IPCB_Arc;",
             f"B := PCBServer.GetPCBBoardByPath('{board}');", "PCBServer.PreProcess;"]
    for p in pieces:
        if p[0] == "T":
            lines.append("T := PCBServer.PCBObjectFactory(eTrackObject, eNoDimension, eCreate_Default);")
            lines.append(f"T.x1 := B.XOrigin + {p[1] * 10000}; T.y1 := B.YOrigin + {p[2] * 10000}; "
                         f"T.x2 := B.XOrigin + {p[3] * 10000}; T.y2 := B.YOrigin + {p[4] * 10000};")
            lines.append(f"T.Width := 100000; T.Layer := {layer}; B.AddPCBObject(T);")
            lines.append("PCBServer.SendMessageToRobots(B.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, "
                         "T.I_ObjectAddress);")
        else:
            lines.append("A := PCBServer.PCBObjectFactory(eArcObject, eNoDimension, eCreate_Default);")
            lines.append(f"A.XCenter := B.XOrigin + {p[1] * 10000}; A.YCenter := B.YOrigin + {p[2] * 10000}; "
                         f"A.Radius := {p[3] * 10000}; A.StartAngle := {p[4]}; A.EndAngle := {p[5]};")
            lines.append(f"A.LineWidth := 100000; A.Layer := {layer}; B.AddPCBObject(A);")
            lines.append("PCBServer.SendMessageToRobots(B.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, "
                         "A.I_ObjectAddress);")
    lines += ["PCBServer.PostProcess;", "ResultText := 'drawn';"]
    script("\n".join(lines))


@unittest.skipUnless(LIVE, SKIP_REASON)
class LiveShapeFromLayerTest(_Temp):
    def setUp(self):
        super().setUp()
        # A new board, made by the tools, in a new project
        prj = self.tmp / "Layer.PrjPcb"
        self.assertTrue(tool(main.create_project(None, str(prj)))["success"])
        self.board = str(self.tmp / "Layer.PcbDoc")
        out = tool(main.add_project_document(None, str(prj), self.board, create=True))
        self.assertTrue(out.get("success"), out)

    def outline_vertex_count(self):
        return int(script(f"ResultText := IntToStr(PCBServer.GetPCBBoardByPath('{self.board}')"
                          ".BoardOutline.PointCount);").strip())

    def test_shape_from_a_mechanical_layer(self):
        draw(self.board, "eMechanical1", DRAWN + [HOLE, STRAY])
        out = tool(main.set_board_shape(None, mechanical_layer="Mechanical 1", board_path=self.board))
        self.assertTrue(out.get("success"), out)
        self.assertEqual(out["bounding_box"], {"x1": 0, "y1": 0, "x2": 3000, "y2": 2000,
                                               "width": 3000, "height": 2000}, out)
        arcs = sorted((tuple(v["arc_center"]), v["clockwise"]) for v in out["outline"] if isinstance(v, dict))
        self.assertEqual(len(out["outline"]), 8, out["outline"])
        self.assertEqual([a[0] for a in arcs], [(250, 250), (250, 1750), (2750, 250), (2750, 1750)])
        self.assertEqual(len({a[1] for a in arcs}), 1, "every corner turns the same way")
        corners = sorted(tuple(v) if isinstance(v, list) else (v["x"], v["y"]) for v in out["outline"])
        self.assertEqual(corners, sorted([(0, 250), (0, 1750), (250, 0), (250, 2000), (2750, 0), (2750, 2000),
                                          (3000, 250), (3000, 1750)]))
        self.assertEqual(out["from_layer"]["layer"], "Mechanical 1")
        self.assertEqual(out["from_layer"]["pieces"], 8)
        self.assertEqual(len(out["from_layer"]["other_closed_shapes"]), 1, out["from_layer"])
        self.assertEqual(len(out["from_layer"]["not_closed"]), 1, out["from_layer"])
        now = tool(main.get_board_summary(None))["board_outline"]
        self.assertEqual((now["x1_mm"], now["y1_mm"], now["width_mm"], now["height_mm"], now["vertex_count"]),
                         (0, 0, 76.2, 50.8, 8), now)
        self.assertFalse(inside(self.board, 10, 10), "a rounded corner")
        self.assertTrue(inside(self.board, 1500, 1000))

    def test_a_gap_is_refused(self):
        before = self.outline_vertex_count()
        draw(self.board, "eMechanical1", DRAWN[1:])
        out = tool(main.set_board_shape(None, mechanical_layer="Mechanical 1", board_path=self.board))
        self.assertFalse(out.get("success"), out)
        self.assertIn("no closed shape", out["error"])
        ends = sorted(tuple(e) for e in out["not_closed"][0]["open_ends"])
        self.assertEqual(ends, [(250, 2000), (2750, 2000)], out)
        self.assertEqual(self.outline_vertex_count(), before)


if __name__ == "__main__":
    unittest.main()
