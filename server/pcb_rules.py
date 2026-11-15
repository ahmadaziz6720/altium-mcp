"""Checking and encoding create_pcb_rule's values before they reach Altium,
reading back what Altium stored, and the fabricator presets.

Each rule kind takes its own values. Distances are given in mils and sent
to Altium in internal units (10000 per mil), so the Pascal side never parses
a decimal number. Altium reads each rule back in the same "key=value;..."
form, which decode_values turns into the caller's keys and compare_values
holds against what was sent.
"""
import json
import math
import os
from typing import Dict, List, Tuple

COORD_PER_MIL = 10000
MILS_PER_MM = 1 / 0.0254
# Altium keeps a coordinate in 32 bits: beyond 100000 mils a value is a unit mistake
MAX_MILS = 100000

# kind -> {value name: (key sent to Altium, "mils" | "count" | "word" | "layers", required)}
RULE_KINDS: Dict[str, Dict[str, tuple]] = {
    "clearance": {"gap_mils": ("gap", "mils", True)},
    "width": {"min_mils": ("min", "mils", True), "max_mils": ("max", "mils", True),
              "preferred_mils": ("preferred", "mils", True)},
    "hole_size": {"min_mils": ("min", "mils", True), "max_mils": ("max", "mils", True)},
    "routing_via": {"min_diameter_mils": ("min_diameter", "mils", True),
                    "max_diameter_mils": ("max_diameter", "mils", True),
                    "preferred_diameter_mils": ("preferred_diameter", "mils", True),
                    "min_hole_mils": ("min_hole", "mils", True),
                    "max_hole_mils": ("max_hole", "mils", True),
                    "preferred_hole_mils": ("preferred_hole", "mils", True)},
    "solder_mask_expansion": {"expansion_mils": ("expansion", "mils", True)},
    "paste_mask_expansion": {"expansion_mils": ("expansion", "mils", True)},
    "polygon_connect": {"connect_style": ("connect_style", "word", True),
                        "conductor_width_mils": ("conductor_width", "mils", False),
                        "air_gap_mils": ("air_gap", "mils", False),
                        "entries": ("entries", "count", False)},
    "differential_pair": {"min_gap_mils": ("min_gap", "mils", True),
                          "max_gap_mils": ("max_gap", "mils", True),
                          "preferred_gap_mils": ("preferred_gap", "mils", True),
                          "min_width_mils": ("min_width", "mils", True),
                          "max_width_mils": ("max_width", "mils", True),
                          "preferred_width_mils": ("preferred_width", "mils", True),
                          "max_uncoupled_length_mils": ("max_uncoupled_length", "mils", False)},
    "length": {"min_mils": ("min", "mils", True), "max_mils": ("max", "mils", True)},
    "matched_length": {"tolerance_mils": ("tolerance", "mils", True)},
    "routing_layers": {"layers": ("layers", "layers", True)},
    "plane_connect": {"connect_style": ("connect_style", "word", True),
                      "expansion_mils": ("expansion", "mils", False),
                      "conductor_width_mils": ("conductor_width", "mils", False),
                      "air_gap_mils": ("air_gap", "mils", False),
                      "entries": ("entries", "count", False)},
    "component_clearance": {"gap_mils": ("gap", "mils", True),
                            "vertical_gap_mils": ("vertical_gap", "mils", False)},
    "silk_to_solder_mask": {"gap_mils": ("gap", "mils", True)},
    "silk_to_silk": {"gap_mils": ("gap", "mils", True)},
    "hole_to_hole": {"gap_mils": ("gap", "mils", True)},
    "annular_ring": {"min_mils": ("min", "mils", True)},
    "solder_mask_sliver": {"gap_mils": ("gap", "mils", True)},
}

# Altium's short descriptor of each kind, as get_pcb_rules gives it in
# "rule_kind" (read from Altium Designer 25)
SHORT_DESCRIPTORS = {
    "clearance": "Clearance Constraint", "width": "Width Constraint", "hole_size": "Hole Size Constraint",
    "routing_via": "Routing Via Style", "solder_mask_expansion": "Solder Mask Expansion",
    "paste_mask_expansion": "Paste Mask Expansion", "polygon_connect": "Polygon Connect Style",
    "differential_pair": "Differential Pairs Routing", "length": "Length Constraint",
    "matched_length": "Matched Net Lengths", "routing_layers": "Routing Layers",
    "plane_connect": "Power Plane Connect Style", "component_clearance": "Component Clearance Constraint",
    "silk_to_solder_mask": "Silk To Solder Mask Clearance Constraint",
    "silk_to_silk": "Silk To Silk Clearance Constraint", "hole_to_hole": "Hole To Hole Clearance Constraint",
    "annular_ring": "Minimum Annular Ring", "solder_mask_sliver": "Minimum Solder Mask Sliver Constraint",
}

# Rules between two objects, which use scope2 as well
BINARY_KINDS = {"clearance", "component_clearance", "silk_to_solder_mask", "silk_to_silk", "hole_to_hole",
                "solder_mask_sliver"}

CONNECT_STYLES = ("relief", "direct", "none")
# Kinds whose value may be negative: a mask expansion below zero shrinks the opening
SIGNED = {"solder_mask_expansion", "paste_mask_expansion"}
# Characters a layer name cannot hold: they separate the values on their way to Altium
LAYER_NAME_FORBIDDEN = ",;=|\r\n"


def _encode_layers(name, v):
    if isinstance(v, str) or not isinstance(v, (list, tuple)) or not v:
        return "", f"{name} is a list of the board's signal layer names, e.g. [\"Top Layer\"]"
    names = []
    for item in v:
        if not isinstance(item, str) or not item.strip():
            return "", f"{name} holds layer names (non-empty strings)"
        if any(c in item for c in LAYER_NAME_FORBIDDEN):
            return "", f"layer name {item!r} holds one of , ; = |"
        if item.strip().lower() in (n.lower() for n in names):
            return "", f"layer {item!r} is named twice"
        names.append(item.strip())
    return ",".join(names), ""


def encode_values(kind: str, values: dict) -> Tuple[str, str]:
    """("key=value;..." for Altium, "") or ("", error)."""
    spec = RULE_KINDS.get(kind)
    if spec is None:
        return "", f"unknown rule_type '{kind}'; one of: {', '.join(RULE_KINDS)}"
    if values is not None and not isinstance(values, dict):
        return "", "values is an object of the kind's values, e.g. {\"gap_mils\": 8}"
    values = dict(values or {})
    unknown = sorted(set(values) - set(spec))
    if unknown:
        return "", f"{kind} takes {', '.join(spec)}; not {', '.join(unknown)}"
    missing = [k for k, (_, _, req) in spec.items() if req and k not in values]
    if missing:
        return "", f"{kind} needs {', '.join(missing)}"
    out = []
    vals = {}
    for name, (key, unit, _) in spec.items():
        if name not in values:
            continue
        v = values[name]
        if unit == "word":
            v = str(v).lower()
            if v not in CONNECT_STYLES:
                return "", f"{name} is one of {', '.join(CONNECT_STYLES)}"
            out.append(f"{key}={v}")
            continue
        if unit == "layers":
            text, error = _encode_layers(name, v)
            if error:
                return "", error
            out.append(f"{key}={text}")
            continue
        if isinstance(v, bool):
            return "", f"{name} must be a number"
        try:
            num = float(v)
        except (TypeError, ValueError):
            return "", f"{name} must be a number"
        if not math.isfinite(num):
            return "", f"{name} must be a number"
        if num < 0 and kind not in SIGNED:
            return "", f"{name} cannot be negative"
        if unit == "count":
            if num not in (2, 4):
                return "", f"{name} is 2 or 4"
            vals[key] = int(num)
        else:
            if abs(num) > MAX_MILS:
                return "", f"{name} is larger than {MAX_MILS} mils; a unit mistake?"
            vals[key] = int(round(num * COORD_PER_MIL))
        out.append(f"{key}={vals[key]}")
    for lo, hi in (("min", "max"), ("min_diameter", "max_diameter"), ("min_hole", "max_hole"),
                   ("min_gap", "max_gap"), ("min_width", "max_width")):
        if lo in vals and hi in vals and vals[lo] > vals[hi]:
            return "", f"{lo}_mils is larger than {hi}_mils"
    # Altium stores a preferred value outside the range, or a via hole as
    # large as the via, without complaint
    for lo, mid, hi in (("min", "preferred", "max"), ("min_diameter", "preferred_diameter", "max_diameter"),
                        ("min_hole", "preferred_hole", "max_hole"), ("min_gap", "preferred_gap", "max_gap"),
                        ("min_width", "preferred_width", "max_width")):
        if mid in vals and not vals[lo] <= vals[mid] <= vals[hi]:
            return "", f"{mid}_mils must be between {lo}_mils and {hi}_mils"
    for size in ("min", "preferred", "max"):
        hole, diameter = f"{size}_hole", f"{size}_diameter"
        if hole in vals and vals[hole] >= vals[diameter]:
            return "", f"{hole}_mils must be smaller than {diameter}_mils"
    return ";".join(out), ""


def _parse(text: str) -> dict:
    out = {}
    for item in str(text or "").split(";"):
        if "=" in item:
            k, v = item.split("=", 1)
            out[k.strip()] = v
    return out


def decode_values(kind: str, text: str) -> dict:
    """Altium's read-back "key=value;..." in the caller's keys (mils as numbers,
    layers as a list of names); keys Altium did not give are left out."""
    raw = _parse(text)
    out = {}
    for name, (key, unit, _) in RULE_KINDS.get(kind, {}).items():
        if key not in raw:
            continue
        v = raw[key]
        try:
            if unit == "mils":
                n = int(v) / COORD_PER_MIL
                out[name] = int(n) if n == int(n) else round(n, 4)
            elif unit == "count":
                out[name] = int(v)
            elif unit == "layers":
                out[name] = [s for s in v.split(",") if s]
            else:
                out[name] = v
        except ValueError:
            out[name] = v
    return out


def compare_values(kind: str, sent: str, read_back: str) -> List[str]:
    """What Altium stored that differs from what was sent, one line each."""
    want, got = _parse(sent), _parse(read_back)
    spec = {key: (name, unit) for name, (key, unit, _) in RULE_KINDS.get(kind, {}).items()}
    out = []
    for key, value in want.items():
        name, unit = spec.get(key, (key, ""))
        if key not in got:
            out.append(f"{name}: not read back")
        elif unit == "layers":
            a = sorted(s.lower() for s in value.split(",") if s)
            b = sorted(s.lower() for s in got[key].split(",") if s)
            if a != b:
                out.append(f"{name}: sent {value.split(',')}, Altium has {[s for s in got[key].split(',') if s]}")
        elif str(got[key]).lower() != str(value).lower():
            shown = decode_values(kind, f"{key}={got[key]}").get(name, got[key])
            sent_shown = decode_values(kind, f"{key}={value}").get(name, value)
            out.append(f"{name}: sent {sent_shown}, Altium has {shown}")
    if got.get("layers_differ"):
        out.append(f"the per-layer values differ between signal layers ({got['layers_differ']})")
    return out


# --- Fabricator presets --------------------------------------------------

PRESET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "fab_presets")


def load_presets(folder: str = PRESET_DIR) -> Dict[str, dict]:
    """preset name -> its build, with the file's fabricator, source page and date read."""
    out = {}
    if not os.path.isdir(folder):
        return out
    for fname in sorted(os.listdir(folder)):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(folder, fname), encoding="utf-8") as f:
            data = json.load(f)
        for name, build in data.get("presets", {}).items():
            out[name] = dict(build, fabricator=data["fabricator"], source=data["source"], read=data["read"],
                             file=fname)
    return out


def preset_rule_values(rule: dict) -> dict:
    """A preset rule's values in create_pcb_rule's keys: the file's mm figures in mils."""
    out = {}
    for key, value in rule.get("values_mm", {}).items():
        out[f"{key}_mils"] = value * MILS_PER_MM
    return out


def is_catch_all(rule: dict) -> bool:
    """A get_pcb_rules entry whose scope is everything."""
    f1 = str(rule.get("filter1", "")).strip().lower()
    f2 = str(rule.get("filter2", "")).strip().lower()
    return f1 == "all" and (rule.get("unary", False) or f2 in ("all", ""))


def _norm(scope) -> str:
    return "".join(str(scope).split()).lower()


def _same_scope(rule: dict, scope1: str, scope2: str, binary: bool) -> bool:
    if _norm(rule.get("filter1", "")) != _norm(scope1):
        return False
    return not binary or _norm(rule.get("filter2", "")) == _norm(scope2)


def plan_priorities(existing: List[dict], new_rules: List[dict], replace: bool = False) -> List[int]:
    """The priority each new rule is given, the rules added in order.

    A new rule goes directly above the highest rule of its kind that it is
    meant to take over (one scoped to everything, or one of the same scope),
    so the board's narrower rules keep winning where they apply; it is the
    lowest of its kind when there is none. existing: get_pcb_rules entries
    (name, rule_kind, priority, filter1, filter2, unary). new_rules: dicts
    of name, rule_type, scope1, scope2. With replace, a board rule of a new
    rule's name is taken out first, as create_pcb_rule does."""
    by_kind: Dict[str, List[dict]] = {}
    for r in sorted(existing, key=lambda r: int(r.get("priority", 0))):
        by_kind.setdefault(r.get("rule_kind", ""), []).append(r)
    out = []
    for new in new_rules:
        kind = SHORT_DESCRIPTORS[new["rule_type"]]
        rules = by_kind.setdefault(kind, [])
        if replace:
            rules[:] = [r for r in rules if str(r.get("name", "")).lower() != new["name"].lower()]
        binary = new["rule_type"] in BINARY_KINDS
        at = len(rules)
        for i, r in enumerate(rules):
            if is_catch_all(r) or _same_scope(r, new["scope1"], new["scope2"], binary):
                at = i
                break
        rules.insert(at, {"name": new["name"], "rule_kind": kind, "filter1": new["scope1"],
                          "filter2": new["scope2"], "unary": not binary})
        out.append(at + 1)
    return out


def _scope_suffixes(filter1: str, filter2: str):
    """The ways a rule's Descriptor ends with its scope, longest first."""
    return (f"({filter1}),({filter2})", f"( ({filter1}) )", f"({filter1})")


def compact_rule(rule: dict) -> dict:
    """One get_pcb_rules entry with its scope given once.

    Altium's Descriptor is the constraint followed by the scope, which
    filter1 and filter2 give again. The scope is cut from it, leaving
    "constraint" ("Clearance Constraint (Gap=10mil)"); a descriptor that does
    not end in the scope is kept whole as the constraint. filter2 is left
    out of a unary rule, which has one scope.
    """
    out = {k: v for k, v in rule.items() if k not in ("descriptor", "unary", "filter2")}
    f1, f2 = str(rule.get("filter1", "")), str(rule.get("filter2", ""))
    text = str(rule.get("descriptor", "")).rstrip()
    for suffix in _scope_suffixes(f1, f2):
        head = text[:-len(suffix)].rstrip()
        # a comma left over: the descriptor's two scopes are not the filters
        if text.endswith(suffix) and not head.endswith(","):
            text = head
            break
    out["constraint"] = text
    if not rule.get("unary", False):
        out["filter2"] = f2
    return out
