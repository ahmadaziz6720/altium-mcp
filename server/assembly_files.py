"""Turn Altium's BOM and pick and place into an assembly service's files,
and zip the Gerbers and drill files (A12). No Altium needed.

The service's columns come from server/data/output_presets/<service>.json
(the pages they were read from, and the date); the per-footprint rotation
corrections from a table the owner fills (<service>_rotations.csv there,
empty to start).
"""
import csv
import fnmatch
import io
import json
import os
import re
import zipfile
from typing import Dict, List, Optional, Tuple

PRESET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "output_presets")
MM_PER_MIL = 0.0254
UNIT_TO_MM = {"mm": 1.0, "mil": MM_PER_MIL}


class AssemblyError(ValueError):
    """Input that cannot be turned into the service's files; nothing written."""


def load_services(folder: str = PRESET_DIR) -> Dict[str, dict]:
    out = {}
    if not os.path.isdir(folder):
        return out
    for fname in sorted(os.listdir(folder)):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(folder, fname), encoding="utf-8") as f:
            data = json.load(f)
        for name, svc in data.get("assembly_services", {}).items():
            out[name] = dict(svc, service=data.get("service"), sources=data.get("sources", {}), folder=folder)
    return out


def _text(path: str) -> str:
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise AssemblyError(f"{path}: not text")


# --- Altium's files ----------------------------------------------------------

def read_bom(path: str) -> Tuple[List[str], List[Dict[str, str]]]:
    """An Altium BOM in CSV: its header and its rows (blank lines skipped)."""
    rows = [r for r in csv.reader(io.StringIO(_text(path))) if any(c.strip() for c in r)]
    if not rows:
        raise AssemblyError(f"{path}: empty")
    header = [h.strip() for h in rows[0]]
    return header, [dict(zip(header, r)) for r in rows[1:]]


def split_designators(text: str) -> List[str]:
    return [d.strip() for d in re.split(r"[,\s]+", text or "") if d.strip()]


def read_pick_place(path: str) -> Tuple[str, List[dict]]:
    """Altium's pick and place in CSV: the unit and per part designator,
    footprint, layer, x and y in mm, rotation (as the file gives them)."""
    lines = _text(path).splitlines()
    start = next((i for i, l in enumerate(lines) if re.match(r'\s*"?Designator"?\s*,', l)), None)
    if start is None:
        raise AssemblyError(f"{path}: no 'Designator' column header; a pick and place in CSV made by Altium "
                            "(GenerateCSVFormat) is needed")
    reader = csv.DictReader(lines[start:])
    names = [n.strip() for n in reader.fieldnames]
    x_col = next((n for n in names if re.fullmatch(r"Center-X\((mm|mil)\)", n)), None)
    y_col = next((n for n in names if re.fullmatch(r"Center-Y\((mm|mil)\)", n)), None)
    if not x_col or not y_col:
        raise AssemblyError(f"{path}: no Center-X/Center-Y column in mm or mil; it has {', '.join(names)}")
    unit = re.search(r"\((mm|mil)\)", x_col).group(1)
    for need in ("Layer", "Rotation", "Footprint"):
        if need not in names:
            raise AssemblyError(f"{path}: no '{need}' column; it has {', '.join(names)}")
    parts = []
    for r in reader:
        r = {k.strip(): (v or "").strip() for k, v in r.items() if k}
        if not r.get("Designator"):
            continue
        try:
            x, y, rot = float(r[x_col]), float(r[y_col]), float(r["Rotation"])
        except ValueError:
            raise AssemblyError(f"{path}: {r['Designator']} has a place or rotation that is not a number")
        parts.append({"designator": r["Designator"], "footprint": r["Footprint"], "layer": r["Layer"],
                      "x_mm": x * UNIT_TO_MM[unit], "y_mm": y * UNIT_TO_MM[unit], "rotation": rot})
    return unit, parts


def side(layer: str) -> Optional[str]:
    """'top' or 'bottom' for Altium's layer text (TopLayer, BottomLayer)."""
    key = layer.replace(" ", "").lower()
    if key in ("toplayer", "top", "t"):
        return "top"
    if key in ("bottomlayer", "bottom", "b"):
        return "bottom"
    return None


# --- The rotation table --------------------------------------------------------

def load_rotations(path: str) -> List[dict]:
    """The rows of a rotation table: footprint (a name or a * ? pattern),
    rotation (degrees added), layer (Top, Bottom or empty), note. Lines that
    start with # are comments."""
    if not path or not os.path.isfile(path):
        raise AssemblyError(f"rotation table not found: {path}")
    lines = [(i, l) for i, l in enumerate(_text(path).splitlines(), 1) if l.strip() and not l.lstrip().startswith("#")]
    if not lines:
        raise AssemblyError(f"{path}: no header line (footprint,rotation,layer,note)")
    reader = csv.reader([l for _, l in lines])
    header = [h.strip().lower() for h in next(reader)]
    if header[:2] != ["footprint", "rotation"]:
        raise AssemblyError(f"{path}: the header must start footprint,rotation (it is {','.join(header)})")
    rows = []
    for (lineno, _), r in zip(lines[1:], reader):
        r = dict(zip(header, [c.strip() for c in r]))
        if not r.get("footprint"):
            raise AssemblyError(f"{path} line {lineno}: no footprint")
        try:
            rotation = float(r.get("rotation", ""))
        except ValueError:
            raise AssemblyError(f"{path} line {lineno}: rotation '{r.get('rotation')}' is not a number")
        layer = r.get("layer", "")
        if layer and side(layer) is None:
            raise AssemblyError(f"{path} line {lineno}: layer '{layer}': Top, Bottom or empty")
        rows.append({"footprint": r["footprint"], "rotation": rotation, "layer": side(layer) if layer else None,
                     "note": r.get("note", ""), "line": lineno})
    return rows


def rotation_rule(rows: List[dict], footprint: str, part_side: str) -> Optional[dict]:
    """The first row that matches a footprint on a side (case ignored)."""
    fp = footprint.lower()
    for row in rows:
        if row["layer"] and row["layer"] != part_side:
            continue
        if fnmatch.fnmatchcase(fp, row["footprint"].lower()):
            return row
    return None


def number(value: float, decimals: int) -> str:
    text = f"{value:.{decimals}f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


# --- Gerbers and drills --------------------------------------------------------

def file_kind(path: str) -> Optional[str]:
    """'gerber' (RS-274X or X2: a %FS format statement), 'drill' (Excellon:
    starts with M48), or None."""
    try:
        with open(path, "rb") as f:
            head = f.read(8192).decode("latin-1")
    except OSError:
        return None
    if head.lstrip().startswith("M48"):
        return "drill"
    if re.search(r"%FS[LT][AI]X\d\dY\d\d\*%", head):
        return "gerber"
    return None


# --- The service's files -------------------------------------------------------

def make(service: dict, bom_path: str, pnp_path: str, gerber_dir: str, out_dir: str,
         part_number_parameter: str = "", rotations_path: str = "", name: str = "") -> dict:
    """Write the service's BOM, placement list and zip into out_dir; returns
    what was written and what was found."""
    if not os.path.isfile(bom_path):
        raise AssemblyError(f"BOM not found: {bom_path}")
    if not os.path.isfile(pnp_path):
        raise AssemblyError(f"pick and place file not found: {pnp_path}")
    if not os.path.isdir(gerber_dir):
        raise AssemblyError(f"Gerber folder not found: {gerber_dir}")
    bom_cfg, cpl_cfg = service["bom"], service["cpl"]
    part_col = (part_number_parameter or bom_cfg["default_part_number_parameter"]).strip()

    header, bom_rows = read_bom(bom_path)
    need = ["Comment", "Designator", "Footprint", part_col]
    missing = [c for c in need if c not in header]
    if missing:
        raise AssemblyError(f"{bom_path}: no column {', '.join(missing)}; it has {', '.join(header)}. The BOM output "
                            f"must show those columns (write_outjob's bom columns; the part number is the "
                            f"parameter named '{part_col}')")
    unit, parts = read_pick_place(pnp_path)
    bad = [p["designator"] for p in parts if side(p["layer"]) is None]
    if bad:
        raise AssemblyError(f"{pnp_path}: a layer that is neither top nor bottom for {', '.join(bad)}")
    if rotations_path:
        table_path = rotations_path
    else:
        table_path = os.path.join(service["folder"], service["rotations"])
    rules = load_rotations(table_path)

    # the zip's files: the folder's own files (flat), by their content
    zipped, not_zipped, kinds = [], [], {"gerber": [], "drill": []}
    for fname in sorted(os.listdir(gerber_dir)):
        path = os.path.join(gerber_dir, fname)
        if not os.path.isfile(path):
            continue
        kind = file_kind(path)
        if kind:
            zipped.append(fname)
            kinds[kind].append(fname)
        else:
            not_zipped.append(fname)
    if not kinds["gerber"]:
        raise AssemblyError(f"{gerber_dir}: no Gerber file (none has a %FS format statement)")

    if not name:
        name = re.sub(r"^Pick Place for ", "", os.path.splitext(os.path.basename(pnp_path))[0]) or "board"
    os.makedirs(out_dir, exist_ok=True)
    tag = service.get("service", "service").replace(" ", "")
    bom_out = os.path.join(out_dir, f"{name}_{tag}_BOM.csv")
    cpl_out = os.path.join(out_dir, f"{name}_{tag}_CPL.csv")
    zip_out = os.path.join(out_dir, f"{name}_{tag}_Gerber.zip")

    # BOM: the service's columns, one row per Altium row
    missing_pn, bom_designators = [], []
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(bom_cfg["columns"])
    for r in bom_rows:
        pn = (r.get(part_col) or "").strip()
        designators = split_designators(r.get("Designator", ""))
        bom_designators += designators
        if not pn:
            missing_pn += designators
        w.writerow([r.get("Comment", ""), r.get("Designator", ""), r.get("Footprint", ""), pn])
    bom_text = buf.getvalue()

    # CPL: the service's columns, mm, the side named as it asks, rotations corrected
    applied = []
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(cpl_cfg["columns"])
    for p in parts:
        s = side(p["layer"])
        rot = p["rotation"]
        rule = rotation_rule(rules, p["footprint"], s)
        if rule:
            new = (rot + rule["rotation"]) % 360
            applied.append({"designator": p["designator"], "footprint": p["footprint"], "layer": s,
                            "from": number(rot, 3), "to": number(new, 3),
                            "rule": f"line {rule['line']}: {rule['footprint']} {number(rule['rotation'], 3)}"})
            rot = new
        w.writerow([p["designator"], f"{p['x_mm']:.4f}", f"{p['y_mm']:.4f}", cpl_cfg["layers"][s], number(rot, 3)])
    cpl_text = buf.getvalue()

    with open(bom_out, "w", encoding="utf-8", newline="") as f:
        f.write(bom_text)
    with open(cpl_out, "w", encoding="utf-8", newline="") as f:
        f.write(cpl_text)
    with zipfile.ZipFile(zip_out, "w", zipfile.ZIP_DEFLATED) as z:
        for fname in zipped:
            z.write(os.path.join(gerber_dir, fname), arcname=fname)

    placed = {p["designator"] for p in parts}
    listed = set(bom_designators)
    warnings = []
    if not kinds["drill"]:
        warnings.append(f"no drill file in {gerber_dir} (none starts with M48): the zip holds no holes")
    if missing_pn:
        warnings.append(f"{len(missing_pn)} parts have no '{part_col}' value: the service cannot pick a part for them")
    return {
        "success": True,
        "service": service.get("service"),
        "bom_file": bom_out, "cpl_file": cpl_out, "zip_file": zip_out,
        "bom_rows": len(bom_rows), "cpl_rows": len(parts),
        "pick_place_units": unit,
        "part_number_column": part_col,
        "missing_part_number": missing_pn,
        "rotation_table": table_path, "rotation_rows": len(rules),
        "rotations_applied": applied,
        "zipped": {"gerber": kinds["gerber"], "drill": kinds["drill"]},
        "not_zipped": not_zipped,
        "only_in_bom": sorted(listed - placed), "only_in_cpl": sorted(placed - listed),
        "warnings": warnings,
        "sources": {k: service["sources"][k]["url"] + f" (read {service['sources'][k]['read']})"
                    for k in service["sources"]},
    }
