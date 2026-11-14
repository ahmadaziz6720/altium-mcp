"""Setting up a project and its board: the pure logic of create_project,
add_project_document, set_board_shape and build_schematic's project_path.

A board outline is a list of vertices in order around the shape, closed back
to the first. A vertex is [x, y] (a corner, a straight edge to the next
vertex) or {"x", "y", "arc_center": [cx, cy], "clockwise": bool} (the edge to
the next vertex is an arc around arc_center, counter-clockwise unless
clockwise). Coordinates are from the board origin, in mils or millimetres.

To Altium it goes as one record per vertex, in internal units (10000 per
mil): 'L|x|y' or 'A|x|y|cx|cy|r|a1|a2', the angles in thousandths of a
degree. Altium draws an outline arc counter-clockwise from a1 to a2 whatever
the order the outline runs in (checked live in AD25), so a clockwise edge
gives its end vertex's angle as a1.

A shape on a mechanical layer is the tracks and arcs drawn there, chained end
to end into closed loops (chain_loops), and one loop picked (pick_outline).
"""
import math
import os
from typing import List, Optional, Tuple

import pcb_shapes
from altium_files import long_path, read_altium_text

COORD_PER_MIL = pcb_shapes.COORD_PER_MIL
MILS_PER_MM = 1 / 0.0254
UNITS = {"mil": 1.0, "mm": MILS_PER_MM}
# How far apart two ends may be and still count as one point: an arc's ends
# from its centre and angles, a track's end, a radius measured to each end of
# an arc edge. 0.1 mil is 2.54 um, well under any fabrication tolerance, and
# far over Altium's rounding (0.0001 mil).
TOLERANCE_MILS = 0.1
# An arc edge is checked as straight pieces at most this many degrees apart
ARC_STEP_DEG = 5.0
# A document's kind, by its extension, for a new document
NEW_KINDS = {".schdoc": "SCH", ".pcbdoc": "PCB"}


def _finite(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _angle(cx, cy, x, y) -> float:
    """The angle of (x, y) seen from (cx, cy), degrees in [0, 360)."""
    return math.degrees(math.atan2(y - cy, x - cx)) % 360.0


def unit_factor(unit: str) -> Tuple[float, str]:
    """Mils per unit, and an error ('' when fine)."""
    u = str(unit or "").strip().lower()
    if u in ("mils",):
        u = "mil"
    if u not in UNITS:
        return 0.0, f"unit is 'mil' or 'mm', not {unit!r}"
    return UNITS[u], ""


def _arc_points(v, nxt, steps_deg=ARC_STEP_DEG):
    """Points along the arc edge from vertex v to vertex nxt (v included,
    nxt not), in mils."""
    cx, cy = v["arc"]["center"]
    r = math.hypot(v["x"] - cx, v["y"] - cy)
    a1 = math.degrees(math.atan2(v["y"] - cy, v["x"] - cx))
    a2 = math.degrees(math.atan2(nxt["y"] - cy, nxt["x"] - cx))
    if v["arc"]["clockwise"]:
        sweep = -((a1 - a2) % 360.0 or 360.0)
    else:
        sweep = (a2 - a1) % 360.0 or 360.0
    n = max(2, int(math.ceil(abs(sweep) / steps_deg)))
    pts = [(v["x"], v["y"])]
    for k in range(1, n):
        a = math.radians(a1 + sweep * k / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def polyline(vertices) -> List[Tuple[float, float]]:
    """The outline as straight pieces, arcs every ARC_STEP_DEG degrees, mils."""
    pts = []
    n = len(vertices)
    for i, v in enumerate(vertices):
        if v.get("arc"):
            pts.extend(_arc_points(v, vertices[(i + 1) % n]))
        else:
            pts.append((v["x"], v["y"]))
    return pts


def polygon_area(pts) -> float:
    n = len(pts)
    return sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n)) / 2.0


def point_in_polygon(x, y, pts) -> bool:
    inside = False
    n = len(pts)
    for i in range(n):
        (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def bbox(pts) -> List[float]:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return [min(xs), min(ys), max(xs), max(ys)]


def parse_outline(outline, unit: str = "mil") -> Tuple[Optional[list], str]:
    """The outline's vertices in mils, as [{"x", "y", "arc": None or
    {"center": (cx, cy), "clockwise": bool}}], or (None, error).

    Rejects: an unknown unit or vertex form, fewer than two vertices, a
    vertex repeated next to itself, an arc edge whose ends are not the same
    distance from its centre (within TOLERANCE_MILS), a shape that encloses
    no area or crosses itself, and coordinates outside Altium's design
    space. A last vertex equal to the first (a straight edge) is dropped:
    the outline closes by itself."""
    factor, error = unit_factor(unit)
    if error:
        return None, error
    if not isinstance(outline, (list, tuple)):
        return None, "outline is a list of vertices"
    verts = []
    for i, p in enumerate(outline):
        where = f"vertex {i + 1}"
        arc = None
        if isinstance(p, dict):
            extra = set(p) - {"x", "y", "arc_center", "clockwise"}
            if extra:
                return None, (f"{where}: unknown key(s) {sorted(extra)}; a vertex is [x, y] or "
                              "{'x', 'y', 'arc_center': [cx, cy], 'clockwise': false}")
            x, y = p.get("x"), p.get("y")
            if "arc_center" in p:
                c = p["arc_center"]
                if not (isinstance(c, (list, tuple)) and len(c) == 2 and all(_finite(v) for v in c)):
                    return None, f"{where}: arc_center is [cx, cy]"
                cw = p.get("clockwise", False)
                if not isinstance(cw, bool):
                    return None, f"{where}: clockwise is true or false"
                arc = {"center": (c[0] * factor, c[1] * factor), "clockwise": cw}
            elif "clockwise" in p:
                return None, f"{where}: clockwise without arc_center"
        elif isinstance(p, (list, tuple)) and len(p) == 2:
            x, y = p
        else:
            return None, f"{where}: give [x, y] or {{'x', 'y', 'arc_center', 'clockwise'}}"
        if not (_finite(x) and _finite(y)):
            return None, f"{where}: x and y must be numbers"
        verts.append({"x": x * factor, "y": y * factor, "arc": arc})

    if len(verts) > 2 and not verts[-1]["arc"] and _same(verts[-1], verts[0]):
        verts.pop()  # closed explicitly: drop the repeat
    n = len(verts)
    if n < 2:
        return None, "outline needs at least two vertices (three for straight edges only)"
    for i in range(n):
        v, nxt = verts[i], verts[(i + 1) % n]
        if _same(v, nxt):
            return None, f"outline repeats vertex {i + 1}"
        if v["arc"]:
            cx, cy = v["arc"]["center"]
            r1 = math.hypot(v["x"] - cx, v["y"] - cy)
            r2 = math.hypot(nxt["x"] - cx, nxt["y"] - cy)
            if r1 < TOLERANCE_MILS:
                return None, f"vertex {i + 1}: arc_center is on the vertex itself"
            if abs(r1 - r2) > TOLERANCE_MILS:
                return None, (f"vertex {i + 1}: the arc's ends are {_fmt(r1 / factor)} and "
                              f"{_fmt(r2 / factor)} {unit} from arc_center; they must be equal")
    pts = polyline(verts)
    if any(abs(c) > pcb_shapes.AREA_LIMIT_MILS for p in pts for c in p):
        return None, f"outline reaches beyond {pcb_shapes.AREA_LIMIT_MILS} mil from the board origin"
    # The crossing and area checks of the pour outlines, on the arcs as points
    _, error = pcb_shapes.outline_points([[x, y] for x, y in pts])
    if error:
        if "cross" in error:
            return None, "the outline crosses itself; give the vertices in order around the shape"
        if "area" in error:
            return None, "the outline encloses no area"
        return None, error
    return verts, ""


def _same(a, b) -> bool:
    return math.hypot(a["x"] - b["x"], a["y"] - b["y"]) < 0.5 / COORD_PER_MIL


def _fmt(v: float) -> str:
    return f"{v:.4f}".rstrip("0").rstrip(".")


def _coord(v: float) -> int:
    return int(round(v * COORD_PER_MIL))


def encode(vertices) -> str:
    """The outline as Altium's records, ';' between them."""
    out = []
    n = len(vertices)
    for i, v in enumerate(vertices):
        if v["arc"]:
            nxt = vertices[(i + 1) % n]
            cx, cy = v["arc"]["center"]
            r = math.hypot(v["x"] - cx, v["y"] - cy)
            a_here, a_next = _angle(cx, cy, v["x"], v["y"]), _angle(cx, cy, nxt["x"], nxt["y"])
            a1, a2 = (a_next, a_here) if v["arc"]["clockwise"] else (a_here, a_next)
            out.append(f"A|{_coord(v['x'])}|{_coord(v['y'])}|{_coord(cx)}|{_coord(cy)}|{_coord(r)}|"
                       f"{int(round(a1 * 1000))}|{int(round(a2 * 1000))}")
        else:
            out.append(f"L|{_coord(v['x'])}|{_coord(v['y'])}")
    return ";".join(out)


def decode(records, unit: str = "mil") -> Tuple[list, list]:
    """Altium's outline, read back as 'L|x|y' or 'A|x|y|cx|cy|r|a1|a2'
    records (internal units from the board origin, angles in thousandths of
    a degree), in the form parse_outline takes, in unit; and its vertices in
    mils, for a bounding box. An arc's direction is the end its vertex is
    at: the start angle counter-clockwise, the end angle clockwise."""
    factor, _ = unit_factor(unit)
    digits = 4 if factor == 1.0 else 5
    out, mils = [], []
    for rec in records:
        f = rec.split("|")
        x, y = int(f[1]) / COORD_PER_MIL, int(f[2]) / COORD_PER_MIL
        ux, uy = round(x / factor, digits), round(y / factor, digits)
        if f[0] == "A":
            cx, cy = int(f[3]) / COORD_PER_MIL, int(f[4]) / COORD_PER_MIL
            a = _angle(cx, cy, x, y)
            a1, a2 = int(f[6]) / 1000.0, int(f[7]) / 1000.0
            d1 = abs((a - a1 + 180) % 360 - 180)
            d2 = abs((a - a2 + 180) % 360 - 180)
            out.append({"x": ux, "y": uy, "arc_center": [round(cx / factor, digits), round(cy / factor, digits)],
                        "clockwise": d2 < d1})
            mils.append({"x": x, "y": y, "arc": {"center": (cx, cy), "clockwise": d2 < d1}})
        else:
            out.append([ux, uy])
            mils.append({"x": x, "y": y, "arc": None})
    return out, mils


# --- A shape on a mechanical layer -----------------------------------------

def _pieces(tracks, arcs):
    """Tracks [x1, y1, x2, y2] and arcs [cx, cy, r, a1, a2] (mils, degrees,
    counter-clockwise from a1 to a2) as pieces with two ends; full circles
    apart, as loops of their own."""
    pieces, circles = [], []
    for t in tracks:
        x1, y1, x2, y2 = (float(v) for v in t)
        if math.hypot(x2 - x1, y2 - y1) < TOLERANCE_MILS:
            continue  # a dot: no edge
        pieces.append({"ends": [(x1, y1), (x2, y2)], "arc": None})
    for a in arcs:
        cx, cy, r, a1, a2 = (float(v) for v in a)
        if r < TOLERANCE_MILS:
            continue
        sweep = (a2 - a1) % 360.0
        if sweep < 1e-6 or sweep > 360.0 - 1e-6:
            # a full circle: two half circles, from the right and the left
            circles.append([{"x": cx + r, "y": cy, "arc": {"center": (cx, cy), "clockwise": False}},
                            {"x": cx - r, "y": cy, "arc": {"center": (cx, cy), "clockwise": False}}])
            continue
        p1 = (cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1)))
        p2 = (cx + r * math.cos(math.radians(a2)), cy + r * math.sin(math.radians(a2)))
        pieces.append({"ends": [p1, p2], "arc": (cx, cy)})
    return pieces, circles


def chain_loops(tracks, arcs, tolerance: float = TOLERANCE_MILS) -> Tuple[list, list]:
    """The closed loops the tracks and arcs form, each as outline vertices
    in mils (parse_outline's form), and what does not close: open chains
    ({"open_ends": [[x, y], [x, y]]}) and branch points ({"branch_at":
    [x, y]}, three or more ends meeting). Ends closer than tolerance meet."""
    pieces, loops = _pieces(tracks, arcs)
    # Ends into points: an end joins the first point within tolerance
    points = []
    for p in pieces:
        p["nodes"] = []
        for e in p["ends"]:
            for k, q in enumerate(points):
                if math.hypot(e[0] - q[0], e[1] - q[1]) <= tolerance:
                    p["nodes"].append(k)
                    break
            else:
                points.append(e)
                p["nodes"].append(len(points) - 1)
    at = {}
    for i, p in enumerate(pieces):
        if p["nodes"][0] == p["nodes"][1]:
            continue  # an arc or track that closes on itself within tolerance
        for k in p["nodes"]:
            at.setdefault(k, []).append(i)
    problems = []
    used = set()
    for start in range(len(pieces)):
        if start in used or pieces[start]["nodes"][0] == pieces[start]["nodes"][1]:
            continue
        # The pieces joined to this one
        group, todo = {start}, [start]
        while todo:
            i = todo.pop()
            for k in pieces[i]["nodes"]:
                for j in at[k]:
                    if j not in group:
                        group.add(j)
                        todo.append(j)
        used |= group
        nodes = {k for i in group for k in pieces[i]["nodes"]}
        branches = [k for k in nodes if len(at[k]) > 2]
        ends = [k for k in nodes if len(at[k]) == 1]
        if branches:
            problems.extend({"branch_at": _pt(points[k])} for k in branches)
            continue
        if ends:
            problems.append({"open_ends": [_pt(points[k]) for k in ends]})
            continue
        # Every point has two pieces: walk the loop
        verts, i, node = [], start, pieces[start]["nodes"][0]
        for _ in range(len(group)):
            p = pieces[i]
            forward = p["nodes"][0] == node
            here = p["ends"][0] if forward else p["ends"][1]
            arc = None
            if p["arc"]:
                # counter-clockwise from end 0 to end 1
                arc = {"center": p["arc"], "clockwise": not forward}
            verts.append({"x": here[0], "y": here[1], "arc": arc})
            node = p["nodes"][1] if forward else p["nodes"][0]
            i = next(j for j in at[node] if j != i)
        loops.append(verts)
    return loops, problems


def _pt(p) -> List[float]:
    return [round(p[0], 4), round(p[1], 4)]


def pick_outline(loops) -> Tuple[Optional[list], list, str]:
    """The loop to make the board shape from: the only one, or the largest
    when every other lies inside it (a cutout or a keep-out drawn on the
    same layer). Returns (vertices, the other loops' boxes, error)."""
    if not loops:
        return None, [], "no closed shape"
    shapes = []
    for verts in loops:
        pts = polyline(verts)
        shapes.append((abs(polygon_area(pts)), pts, verts))
    shapes.sort(key=lambda s: -s[0])
    outer = shapes[0]
    others = [[round(v, 4) for v in bbox(s[1])] for s in shapes[1:]]
    for _, pts, _ in shapes[1:]:
        if not all(point_in_polygon(x, y, outer[1]) for x, y in pts):
            return None, others, ("several closed shapes, none of which holds all the others: "
                                  "their boxes (mils) are " +
                                  ", ".join(str([round(v, 4) for v in bbox(s[1])]) for s in shapes))
    return outer[2], others, ""


# --- The project file -------------------------------------------------------

def new_file_path(path: str) -> str:
    """A file that does not exist yet as Altium names it: absolute, its
    folder's 8.3 names expanded (long_path cannot expand a path that is not
    there), backslashes."""
    path = os.path.abspath(str(path))
    folder, name = os.path.split(path)
    return os.path.join(long_path(folder), name)


def project_file_documents(project_path: str) -> List[str]:
    """The documents a saved .PrjPcb lists ([DocumentN] DocumentPath), as
    full paths (a path in the file is relative to the project's folder)."""
    folder = os.path.dirname(project_path)
    out, section = [], ""
    for line in read_altium_text(project_path).split("\n"):
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
        elif section.lower().startswith("document") and section[8:].isdigit() and "=" in line:
            key, value = line.split("=", 1)
            if key.strip().lower() == "documentpath" and value.strip():
                out.append(os.path.normpath(os.path.join(folder, value.strip())))
    return out


def same_path(a: str, b: str) -> bool:
    return os.path.normcase(os.path.normpath(a)) == os.path.normcase(os.path.normpath(b))
