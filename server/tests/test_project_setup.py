"""Unit tests for project_setup and the checks of create_project,
add_project_document, set_board_shape and build_schematic's project_path
that come before Altium (pure Python, no Altium needed: the bridge is faked).

Run from server/:  python -m unittest tests.test_project_setup -v
"""
import asyncio
import codecs
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import main  # noqa: E402
import project_setup as ps  # noqa: E402

ROUNDED = [[0, 0], [0, 1000], {"x": 1800, "y": 1000, "arc_center": [1800, 800], "clockwise": True},
           [2000, 800], [2000, 0]]


class ParseOutlineTest(unittest.TestCase):
    def test_rectangle(self):
        verts, err = ps.parse_outline([[0, 0], [100, 0], [100, 50], [0, 50]])
        self.assertEqual(err, "")
        self.assertEqual([(v["x"], v["y"], v["arc"]) for v in verts],
                         [(0, 0, None), (100, 0, None), (100, 50, None), (0, 50, None)])

    def test_closing_vertex_is_dropped(self):
        verts, _ = ps.parse_outline([[0, 0], [100, 0], [100, 50], [0, 0]])
        self.assertEqual(len(verts), 3)

    def test_millimetres(self):
        verts, err = ps.parse_outline([[0, 0], [25.4, 0], [25.4, 2.54]], "mm")
        self.assertEqual(err, "")
        self.assertAlmostEqual(verts[1]["x"], 1000)
        self.assertAlmostEqual(verts[2]["y"], 100)

    def test_arc_vertex(self):
        verts, err = ps.parse_outline(ROUNDED)
        self.assertEqual(err, "")
        self.assertEqual(verts[2]["arc"], {"center": (1800, 800), "clockwise": True})
        self.assertIsNone(verts[3]["arc"])

    def test_a_circle_of_two_arcs(self):
        verts, err = ps.parse_outline([{"x": 0, "y": 0, "arc_center": [0, 500]},
                                       {"x": 0, "y": 1000, "arc_center": [0, 500]}])
        self.assertEqual(err, "")
        self.assertEqual(len(verts), 2)

    def test_rejected(self):
        def err(outline, unit="mil"):
            return ps.parse_outline(outline, unit)[1]
        self.assertIn("unit", err([[0, 0], [1, 0], [0, 1]], "inch"))
        self.assertIn("list", err("0,0 1,1"))
        self.assertIn("two vertices", err([[0, 0]]))
        self.assertIn("repeats", err([[0, 0], [10, 0], [10, 0], [0, 10]]))
        self.assertIn("no area", err([[0, 0], [10, 0], [20, 0]]))
        self.assertIn("three corners", err([[0, 0], [10, 0]]))
        self.assertIn("crosses itself", err([[100, 0], [1000, 0], [0, 1000], [1000, 2000]]))
        self.assertIn("unknown key", err([{"x": 0, "y": 0, "center": [1, 1]}, [1, 0], [0, 1]]))
        self.assertIn("without arc_center", err([{"x": 0, "y": 0, "clockwise": True}, [1, 0], [0, 1]]))
        self.assertIn("true or false", err([{"x": 0, "y": 0, "arc_center": [0, 5], "clockwise": 1},
                                            [0, 10], [-5, 5]]))
        self.assertIn("arc_center is [cx, cy]", err([{"x": 0, "y": 0, "arc_center": [0]}, [0, 10], [-5, 5]]))
        self.assertIn("numbers", err([["a", 0], [1, 0], [0, 1]]))
        self.assertIn("numbers", err([[True, 0], [1, 0], [0, 1]]))
        self.assertIn("[x, y]", err([[0, 0, 0], [1, 0], [0, 1]]))
        self.assertIn("on the vertex", err([{"x": 0, "y": 0, "arc_center": [0, 0]}, [10, 0], [0, 10]]))
        self.assertIn("beyond", err([[0, 0], [200000, 0], [0, 10]]))

    def test_arc_ends_must_be_on_one_circle(self):
        msg = ps.parse_outline([{"x": 0, "y": 0, "arc_center": [500, 100]}, [1000, 0], [1000, 1000],
                                [0, 1000]])[1]
        self.assertEqual(msg, "")  # both ends 509.9 mil from the centre
        msg = ps.parse_outline([{"x": 0, "y": 0, "arc_center": [500, 0]}, [1000, 50], [0, 1000]])[1]
        self.assertIn("must be equal", msg)
        self.assertIn("500", msg)
        # within 0.1 mil is one circle
        self.assertEqual(ps.parse_outline([{"x": 0, "y": 0, "arc_center": [500, 0]}, [1000.05, 0],
                                           [0, 1000]])[1], "")

    def test_an_arc_that_bulges_across_an_edge_crosses(self):
        # the arc from (1000, 0) to (0, 0) around (500, 0) clockwise goes
        # up through y=500, across the edge at y=200
        msg = ps.parse_outline([[0, 0], [0, 200], [1000, 200],
                                {"x": 1000, "y": 0, "arc_center": [500, 0], "clockwise": False}])[1]
        self.assertIn("crosses itself", msg)


class EncodeDecodeTest(unittest.TestCase):
    def test_records(self):
        verts, _ = ps.parse_outline(ROUNDED)
        self.assertEqual(ps.encode(verts), "L|0|0;L|0|10000000;A|18000000|10000000|18000000|8000000|2000000|0|90000;"
                                           "L|20000000|8000000;L|20000000|0")

    def test_counter_clockwise_arc_angles(self):
        verts, _ = ps.parse_outline([[0, 0], [2000, 0], {"x": 2000, "y": 800, "arc_center": [1800, 800]},
                                     [1800, 1000], [0, 1000]])
        self.assertEqual(ps.encode(verts).split(";")[2], "A|20000000|8000000|18000000|8000000|2000000|0|90000")

    def test_round_trip(self):
        for outline, unit in ((ROUNDED, "mil"),
                              ([{"x": 0, "y": 25, "arc_center": [25, 25], "clockwise": False},
                                {"x": 50, "y": 25, "arc_center": [25, 25], "clockwise": False}], "mm"),
                              ([[0, 0], [12.7, 0], {"x": 12.7, "y": 5, "arc_center": [12.7, 7.5], "clockwise": True},
                                [12.7, 10], [0, 10]], "mm")):
            verts, err = ps.parse_outline(outline, unit)
            self.assertEqual(err, "")
            back, mils = ps.decode(ps.encode(verts).split(";"), unit)
            self.assertEqual(back, outline)
            self.assertEqual(len(mils), len(outline))

    def test_unit_names(self):
        self.assertEqual(ps.unit_factor("MM")[1], "")
        self.assertEqual(ps.unit_factor("mils")[0], 1.0)
        self.assertAlmostEqual(ps.unit_factor("mm")[0], 39.37007874)


# A 3000 x 2000 mil rounded rectangle (250 mil corners), its pieces shuffled
# and two tracks reversed
TRACKS = [(2750, 2000, 250, 2000), (3000, 250, 3000, 1750), (0, 1750, 0, 250), (2750, 0, 250, 0)]
ARCS = [(250, 250, 250, 180, 270), (2750, 1750, 250, 0, 90), (2750, 250, 250, 270, 360),
        (250, 1750, 250, 90, 180)]


class ChainTest(unittest.TestCase):
    def test_one_loop(self):
        loops, problems = ps.chain_loops(TRACKS, ARCS)
        self.assertEqual(problems, [])
        self.assertEqual(len(loops), 1)
        verts = loops[0]
        self.assertEqual(len(verts), 8)
        arcs = [v["arc"] for v in verts if v["arc"]]
        self.assertEqual(sorted(a["center"] for a in arcs), [(250, 250), (250, 1750), (2750, 250), (2750, 1750)])
        self.assertEqual(len({a["clockwise"] for a in arcs}), 1, "one direction round the loop")
        # and it is a valid outline, its arcs in order
        out, err = ps.parse_outline([{"x": v["x"], "y": v["y"], "arc_center": list(v["arc"]["center"]),
                                      "clockwise": v["arc"]["clockwise"]} if v["arc"] else [v["x"], v["y"]]
                                     for v in verts])
        self.assertEqual(err, "")
        self.assertAlmostEqual(abs(ps.polygon_area(ps.polyline(out))), 3000 * 2000 - (4 - 3.14159) * 250 ** 2,
                               delta=500)

    def test_open_chain_and_branch(self):
        loops, problems = ps.chain_loops(TRACKS[1:], ARCS)
        self.assertEqual(loops, [])
        self.assertEqual(len(problems), 1)
        self.assertEqual(sorted(map(tuple, problems[0]["open_ends"])), [(250, 2000), (2750, 2000)])
        loops, problems = ps.chain_loops(TRACKS + [(250, 2000, 250, 2500)], ARCS)
        self.assertEqual(loops, [])
        self.assertEqual(problems, [{"branch_at": [250, 2000]}])

    def test_full_circle_and_dots(self):
        loops, problems = ps.chain_loops([(5, 5, 5, 5)], [(500, 500, 60, 0, 360), (0, 0, 0, 0, 90)])
        self.assertEqual(problems, [])
        self.assertEqual(len(loops), 1)
        self.assertEqual([(v["x"], v["y"]) for v in loops[0]], [(560, 500), (440, 500)])
        self.assertEqual(ps.parse_outline([{"x": v["x"], "y": v["y"], "arc_center": list(v["arc"]["center"])}
                                           for v in loops[0]])[1], "")

    def test_tolerance(self):
        square = [(0, 0, 100, 0), (100, 0, 100, 100), (100, 100, 0, 100)]
        self.assertEqual(len(ps.chain_loops(square + [(0, 100, 0.05, 0.05)], [])[0]), 1)
        loops, problems = ps.chain_loops(square + [(0, 100, 0.2, 0)], [])
        self.assertEqual(loops, [])
        self.assertEqual(len(problems), 1)

    def test_pick(self):
        loops, _ = ps.chain_loops(TRACKS, ARCS + [(500, 500, 60, 0, 360)])
        chosen, others, err = ps.pick_outline(loops)
        self.assertEqual(err, "")
        self.assertEqual(len(chosen), 8)
        self.assertEqual(others, [[440, 440, 560, 560]])
        outside = ps.chain_loops([(4000, 0, 4100, 0), (4100, 0, 4100, 100), (4100, 100, 4000, 0)], [])[0]
        chosen, others, err = ps.pick_outline(loops + outside)
        self.assertIsNone(chosen)
        self.assertIn("none of which holds all the others", err)
        self.assertEqual(ps.pick_outline([])[2], "no closed shape")


class ProjectFileTest(unittest.TestCase):
    def test_documents_listed(self):
        with tempfile.TemporaryDirectory() as d:
            prj = os.path.join(d, "P.PrjPcb")
            text = ("[Design]\r\nVersion=1.0\r\n\r\n[Document1]\r\nDocumentPath=Main.SchDoc\r\n"
                    "AnnotationEnabled=1\r\n\r\n[Document2]\r\nDocumentPath=..\\lib\\Parts.PcbLib\r\n\r\n"
                    "[GeneratedDocument1]\r\nDocumentPath=Project Outputs\\x.html\r\n")
            with open(prj, "wb") as f:
                f.write(codecs.BOM_UTF8 + text.encode("utf-8"))
            self.assertEqual(ps.project_file_documents(prj),
                             [os.path.join(d, "Main.SchDoc"), os.path.normpath(os.path.join(d, "..", "lib",
                                                                                          "Parts.PcbLib"))])

    def test_new_file_path_expands_short_names(self):
        import win32api
        with tempfile.TemporaryDirectory(prefix="a long folder name ") as d:
            short = win32api.GetShortPathName(d)
            got = ps.new_file_path(os.path.join(short, "New.PrjPcb"))
            self.assertTrue(ps.same_path(got, os.path.join(win32api.GetLongPathName(d), "New.PrjPcb")), got)
            self.assertIn("a long folder name", got)


def run(coro, replies=None):
    """A tool's JSON result with the bridge faked: replies by command."""
    calls = []

    async def fake(command, params, timeout=None):
        calls.append((command, params))
        if replies is None or command not in replies:
            raise AssertionError(f"Altium was called: {command}")
        reply = replies[command]
        return reply(params) if callable(reply) else reply
    with mock.patch.object(main.altium_bridge, "execute_command", fake):
        return json.loads(asyncio.run(coro)), calls


class ToolChecksTest(unittest.TestCase):
    """What the tools refuse before Altium is called."""

    def test_create_project(self):
        with tempfile.TemporaryDirectory() as d:
            existing = os.path.join(d, "P.PrjPcb")
            open(existing, "w").close()
            out, _ = run(main.create_project(None, existing))
            self.assertIn("already exists", out["error"])
            out, _ = run(main.create_project(None, os.path.join(d, "P.PrjScr")))
            self.assertIn(".prjpcb", out["error"])
            out, _ = run(main.create_project(None, ""))
            self.assertFalse(out["success"])

    def test_add_project_document(self):
        with tempfile.TemporaryDirectory() as d:
            prj = os.path.join(d, "P.PrjPcb")
            open(prj, "w").close()
            sheet = os.path.join(d, "S.SchDoc")
            open(sheet, "w").close()
            out, _ = run(main.add_project_document(None, os.path.join(d, "none.PrjPcb"), sheet))
            self.assertIn("not found", out["error"])
            out, _ = run(main.add_project_document(None, prj, sheet, create=True))
            self.assertIn("already exists", out["error"])
            out, _ = run(main.add_project_document(None, prj, os.path.join(d, "x.OutJob"), create=True))
            self.assertIn(".SchDoc or a .PcbDoc", out["error"])
            out, _ = run(main.add_project_document(None, prj, os.path.join(d, "none.SchDoc")))
            self.assertIn("not found", out["error"])

    def test_add_reads_the_saved_project_file(self):
        with tempfile.TemporaryDirectory() as d:
            prj = os.path.join(d, "P.PrjPcb")
            sheet = os.path.join(d, "S.SchDoc")
            open(sheet, "w").close()
            with open(prj, "w") as f:
                f.write("[Design]\n")
            def reply(params):
                return {"success": True, "result": {"success": True, "documents": [{"path": sheet, "kind": "SCH"}]}}
            out, calls = run(main.add_project_document(None, prj, sheet), {"add_project_document": reply})
            self.assertEqual(calls[0][1]["new_kind"], "")
            self.assertFalse(out["success"], "the project file does not list it")
            with open(prj, "w") as f:
                f.write("[Document1]\nDocumentPath=S.SchDoc\n")
            out, _ = run(main.add_project_document(None, prj, sheet), {"add_project_document": reply})
            self.assertTrue(out["success"], out)
            self.assertTrue(out["in_project_file"])

    def test_build_schematic_project_arguments(self):
        with tempfile.TemporaryDirectory() as d:
            prj = os.path.join(d, "P.PrjPcb")
            open(prj, "w").close()
            parts = [{"designator": "R1", "symbol_library": "x.SchLib", "symbol": "RES", "x": 0, "y": 0}]
            out, _ = run(main.build_schematic(None, parts, project_path=prj))
            self.assertIn("go together", out["error"])
            out, _ = run(main.build_schematic(None, parts, sheet_path=os.path.join(d, "S.SchDoc")))
            self.assertIn("go together", out["error"])
            out, _ = run(main.build_schematic(None, parts, project_path=prj, sheet_path=os.path.join(d, "S.PcbDoc")))
            self.assertIn(".schdoc", out["error"])

    def test_set_board_shape_arguments(self):
        out, _ = run(main.set_board_shape(None))
        self.assertIn("one of the two", out["error"])
        out, _ = run(main.set_board_shape(None, outline=ROUNDED, mechanical_layer="Mechanical 1"))
        self.assertIn("one of the two", out["error"])
        out, _ = run(main.set_board_shape(None, outline=ROUNDED, unit="inch"))
        self.assertIn("unit", out["error"])
        out, _ = run(main.set_board_shape(None, outline=[[0, 0], [10, 0], [20, 0]]))
        self.assertIn("no area", out["error"])


def echo_outline(params):
    """set_board_outline as Altium answers it: the vertices it was given."""
    recs = params["outline"].split(";")
    return {"success": True, "result": "\n".join(recs + ["B|0|0|30000000|20000000", "M|1", "F|C:\\b.PcbDoc"])}


class SetBoardShapeTest(unittest.TestCase):
    def test_outline_read_back(self):
        out, calls = run(main.set_board_shape(None, outline=ROUNDED), {"set_board_outline": echo_outline})
        self.assertTrue(out["success"], out)
        self.assertEqual(out["outline"], ROUNDED)
        self.assertEqual(out["bounding_box"], {"x1": 0, "y1": 0, "x2": 3000, "y2": 2000, "width": 3000,
                                               "height": 2000})
        self.assertTrue(out["board_modified"])
        self.assertEqual(out["board"], "C:\\b.PcbDoc")

    def test_an_outline_altium_did_not_take(self):
        def other(params):
            return {"success": True, "result": "L|0|0\nL|10000000|0\nL|0|10000000\nB|0|0|1|1\nM|1\nF|b"}
        out, _ = run(main.set_board_shape(None, outline=ROUNDED), {"set_board_outline": other})
        self.assertFalse(out["success"])
        self.assertIn("differs", out["error"])

    def test_from_a_layer(self):
        lines = ["L|Board Shape"]
        lines += ["T|" + "|".join(str(int(v * 10000)) for v in t) for t in TRACKS + [(0, -500, 3000, -500)]]
        lines += ["A|" + "|".join(str(int(v * 10000)) for v in a[:3]) + "|" +
                  "|".join(str(int(v * 1000)) for v in a[3:]) for a in ARCS + [(500, 500, 60, 0, 360)]]
        replies = {"board_layer_shapes": {"success": True, "result": "\n".join(lines)},
                   "set_board_outline": echo_outline}
        out, calls = run(main.set_board_shape(None, mechanical_layer="Board Shape", unit="mm"), replies)
        self.assertTrue(out["success"], out)
        self.assertEqual(calls[0], ("board_layer_shapes", {"layer": "Board Shape", "board_path": ""}))
        self.assertEqual(out["vertex_count"], 8)
        self.assertEqual(out["unit"], "mm")
        self.assertEqual(out["from_layer"]["layer"], "Board Shape")
        self.assertEqual(out["from_layer"]["pieces"], 8)
        self.assertEqual(out["from_layer"]["other_closed_shapes"], [[11.176, 11.176, 14.224, 14.224]])
        self.assertEqual(out["from_layer"]["not_closed"], [{"open_ends": [[0, -12.7], [76.2, -12.7]]}])

    def test_from_a_layer_with_a_gap(self):
        lines = ["L|Mechanical 1"] + ["T|" + "|".join(str(v * 10000) for v in t) for t in TRACKS[1:]]
        lines += ["A|" + "|".join(str(v * 10000) for v in a[:3]) + "|" + "|".join(str(v * 1000) for v in a[3:])
                  for a in ARCS]
        out, calls = run(main.set_board_shape(None, mechanical_layer="Mechanical 1"),
                         {"board_layer_shapes": {"success": True, "result": "\n".join(lines)}})
        self.assertFalse(out["success"])
        self.assertIn("no closed shape on Mechanical 1", out["error"])
        self.assertEqual(sorted(map(tuple, out["not_closed"][0]["open_ends"])), [(250, 2000), (2750, 2000)])
        self.assertEqual([c[0] for c in calls], ["board_layer_shapes"], "the board was not changed")


if __name__ == "__main__":
    unittest.main()
