"""Checking and encoding edit_schematic's operations for Altium.

Each operation becomes one pipe-delimited line of the spec file the bridge
reads (sch_edit_spec.txt). Coordinates are given in mil or mm, absolute on
the sheet with Altium's origin at the bottom left, and sent in internal
units, so a metric sheet keeps its exact positions.
"""
import os
from typing import List, Tuple

COORD_PER = {"mil": 10000, "mm": 10000 / 0.0254}
ROTATIONS = {0: 0, 90: 1, 180: 2, 270: 3}
POWER_STYLES = {"circle": 0, "arrow": 1, "bar": 2, "wave": 3, "power_ground": 4,
                "signal_ground": 5, "earth": 6}
DELETE_KINDS = ("wire", "net_label", "power_port", "junction", "no_erc", "port", "note")

# op -> (required keys, optional keys)
OPS = {
    "move_component": (("designator",), ("part", "x", "y", "rotation", "mirror")),
    "delete_component": (("designator",), ("part",)),
    "set_parameter": (("designator", "name", "value"), ("part", "visible")),
    "move_text": (("designator", "name"), ("part", "x", "y", "justification", "orientation", "visible")),
    "add_wire": (("points",), ()),
    "add_net_label": (("x", "y", "text"), ("orientation", "justification")),
    "add_power_port": (("x", "y", "text"), ("style", "orientation", "show_net_name")),
    "add_junction": (("x", "y"), ()),
    "add_no_erc": (("x", "y"), ()),
    "delete_at": (("kind", "x", "y"), ("text",)),
    "place_component": (("library", "symbol", "designator", "x", "y"), ("part", "rotation", "mirror", "comment")),
    "set_footprint": (("designator", "footprint", "library"), ()),
}


class OpError(ValueError):
    pass


def _text(v, what) -> str:
    s = str(v)
    if any(c in s for c in "|\r\n"):
        raise OpError(f"{what} cannot contain '|' or a line break")
    return s


def _flag(v) -> str:
    """-1 keeps the current value, 0/1 sets it."""
    return "-1" if v is None else ("1" if v else "0")


def _int_in(v, lo, hi, what) -> int:
    try:
        n = int(v)
    except (TypeError, ValueError):
        raise OpError(f"{what} must be a whole number")
    if not lo <= n <= hi or n != float(v):
        raise OpError(f"{what} must be {lo}..{hi}")
    return n


def part_number(v) -> int:
    """A part of a multi-part component as its number: given as that or as
    its letter (A = 1, AA = 27); 0 when none is given."""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    s = "" if v is None else str(v).strip().upper()
    if not s:
        return 0
    n = -1
    if s.isascii() and s.isdigit():
        n = int(s)
    elif len(s) <= 2 and all("A" <= c <= "Z" for c in s):
        n = 0
        for c in s:
            n = n * 26 + ord(c) - ord("A") + 1
    if not 0 <= n <= 255:
        raise OpError("part is a letter (A, B, ...) or a number up to 255")
    return n


def _rotation(v) -> str:
    if v is None:
        return "-1"
    try:
        return str(ROTATIONS[int(v) % 360])
    except (TypeError, ValueError, KeyError):
        raise OpError("rotation is 0, 90, 180 or 270 degrees")


def encode_operations(operations: list, unit: str = "mil") -> Tuple[List[str], str]:
    """(spec lines, "") or ([], "operation N: what is wrong")."""
    if unit not in COORD_PER:
        return [], "unit is mil or mm"
    scale = COORD_PER[unit]

    def c(v, what="coordinate"):
        try:
            return str(int(round(float(v) * scale)))
        except (TypeError, ValueError):
            raise OpError(f"{what} must be a number")

    lines = []
    for i, op in enumerate(operations or []):
        try:
            if not isinstance(op, dict) or op.get("op") not in OPS:
                raise OpError(f"'op' must be one of {', '.join(OPS)}")
            kind = op["op"]
            required, optional = OPS[kind]
            missing = [k for k in required if op.get(k) is None]
            if missing:
                raise OpError(f"{kind} needs {', '.join(missing)}")
            unknown = sorted(set(op) - set(required) - set(optional) - {"op"})
            if unknown:
                raise OpError(f"{kind} does not take {', '.join(unknown)}")
            part = str(part_number(op.get("part")))

            if kind == "move_component":
                if ("x" in op) != ("y" in op):
                    raise OpError("give both x and y, or neither")
                xy = [c(op["x"]), c(op["y"])] if "x" in op else ["", ""]
                lines.append("|".join(["MOVE", _text(op["designator"], "designator"), part] + xy +
                                      [_rotation(op.get("rotation")), _flag(op.get("mirror"))]))
            elif kind == "delete_component":
                lines.append("|".join(["DELETE", _text(op["designator"], "designator"), part]))
            elif kind == "set_parameter":
                lines.append("|".join(["PARAM", _text(op["designator"], "designator"), part,
                                       _text(op["name"], "name"), _text(op["value"], "value"),
                                       _flag(op.get("visible"))]))
            elif kind == "move_text":
                if ("x" in op) != ("y" in op):
                    raise OpError("give both x and y, or neither")
                xy = [c(op["x"]), c(op["y"])] if "x" in op else ["", ""]
                just = "-1" if op.get("justification") is None else str(
                    _int_in(op["justification"], 0, 8, "justification"))
                orient = "-1" if op.get("orientation") is None else str(
                    _int_in(op["orientation"], 0, 3, "orientation"))
                lines.append("|".join(["TEXT", _text(op["designator"], "designator"), part,
                                       _text(op["name"], "name")] + xy + [just, orient, _flag(op.get("visible"))]))
            elif kind == "add_wire":
                pts = op["points"]
                if not isinstance(pts, list) or len(pts) < 2 or any(len(p) != 2 for p in pts):
                    raise OpError("points is a list of at least two [x, y]")
                lines.append("|".join(["WIRE"] + [c(v) for p in pts for v in p]))
            elif kind == "add_net_label":
                lines.append("|".join(["LABEL", c(op["x"]), c(op["y"]),
                                       str(_int_in(op.get("orientation", 0), 0, 3, "orientation")),
                                       str(_int_in(op.get("justification", 0), 0, 8, "justification")),
                                       _text(op["text"], "text")]))
            elif kind == "add_power_port":
                style = op.get("style", "bar")
                style = POWER_STYLES.get(style, style) if isinstance(style, str) else style
                style = _int_in(style, 0, 10, f"style (or one of {', '.join(POWER_STYLES)})")
                lines.append("|".join(["POWER", c(op["x"]), c(op["y"]),
                                       str(_int_in(op.get("orientation", 1), 0, 3, "orientation")), str(style),
                                       "1" if op.get("show_net_name", True) else "0", _text(op["text"], "text")]))
            elif kind in ("add_junction", "add_no_erc"):
                lines.append("|".join(["JUNCTION" if kind == "add_junction" else "NOERC", c(op["x"]), c(op["y"])]))
            elif kind == "delete_at":
                if op["kind"] not in DELETE_KINDS:
                    raise OpError(f"kind is one of {', '.join(DELETE_KINDS)}")
                lines.append("|".join(["DELETE_AT", op["kind"], c(op["x"]), c(op["y"]),
                                       _text(op.get("text", ""), "text")]))
            elif kind == "place_component":
                lib = _text(op["library"], "library")
                if not lib.lower().endswith((".schlib", ".intlib")):
                    raise OpError("library must be the full path of a .SchLib or .IntLib file")
                lines.append("|".join(["PLACE", _text(op["designator"], "designator"), lib,
                                       _text(op["symbol"], "symbol"), c(op["x"]), c(op["y"]),
                                       _rotation(op.get("rotation", 0)), "1" if op.get("mirror") else "0",
                                       _text(op.get("comment", ""), "comment"),
                                       "1" if part == "0" else part]))
            elif kind == "set_footprint":
                lib = _text(op["library"], "library")
                name = _text(op["footprint"], "footprint").strip()
                if not lib.lower().endswith(".pcblib"):
                    raise OpError("library must be the full path of a .PcbLib file")
                if not os.path.isfile(lib):
                    raise OpError(f"no footprint library at {lib}")
                # A part linked to a library that lacks its footprint is
                # what the op is for putting right (A56), so it is not made
                import pcblib_file
                holds = pcblib_file.holds_footprint(lib, name)
                if holds is None:
                    raise OpError(f"the footprint library {lib} could not be read")
                if not holds:
                    raise OpError(f"the saved library {lib} does not hold the footprint {name}")
                lines.append("|".join(["FOOTPRINT", _text(op["designator"], "designator"), name, lib]))
        except OpError as e:
            return [], f"operation {i + 1}: {e}"
    if not lines:
        return [], "operations is empty"
    return lines, ""
