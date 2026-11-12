"""Checking and encoding create_pcb_rule's values before they reach Altium.

Each rule kind takes its own values. Distances are given in mils and sent
to Altium in internal units (10000 per mil), so the Pascal side never parses
a decimal number.
"""
from typing import Dict, Tuple

COORD_PER_MIL = 10000

# kind -> {value name: (key sent to Altium, "mils" | "count" | "word", required)}
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
}

CONNECT_STYLES = ("relief", "direct", "none")
# Values that may be negative: a mask expansion below zero shrinks the opening
SIGNED = {"expansion"}


def encode_values(kind: str, values: dict) -> Tuple[str, str]:
    """("key=value;..." for Altium, "") or ("", error)."""
    spec = RULE_KINDS.get(kind)
    if spec is None:
        return "", f"unknown rule_type '{kind}'; one of: {', '.join(RULE_KINDS)}"
    values = dict(values or {})
    unknown = sorted(set(values) - set(spec))
    if unknown:
        return "", f"{kind} takes {', '.join(spec)}; not {', '.join(unknown)}"
    missing = [k for k, (_, _, req) in spec.items() if req and k not in values]
    if missing:
        return "", f"{kind} needs {', '.join(missing)}"
    out = []
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
        try:
            num = float(v)
        except (TypeError, ValueError):
            return "", f"{name} must be a number"
        if num < 0 and key not in SIGNED:
            return "", f"{name} cannot be negative"
        if unit == "count":
            if num not in (2, 4):
                return "", f"{name} is 2 or 4"
            out.append(f"{key}={int(num)}")
        else:
            out.append(f"{key}={int(round(num * COORD_PER_MIL))}")
    vals = {k.split("=")[0]: int(k.split("=")[1]) for k in out if not k.startswith("connect_style")}
    for lo, hi in (("min", "max"), ("min_diameter", "max_diameter"), ("min_hole", "max_hole")):
        if lo in vals and hi in vals and vals[lo] > vals[hi]:
            return "", f"{lo}_mils is larger than {hi}_mils"
    # Altium stores a preferred value outside the range, or a via hole as
    # large as the via, without complaint
    for lo, mid, hi in (("min", "preferred", "max"), ("min_diameter", "preferred_diameter", "max_diameter"),
                        ("min_hole", "preferred_hole", "max_hole")):
        if mid in vals and not vals[lo] <= vals[mid] <= vals[hi]:
            return "", f"{mid}_mils must be between {lo}_mils and {hi}_mils"
    for size in ("min", "preferred", "max"):
        hole, diameter = f"{size}_hole", f"{size}_diameter"
        if hole in vals and vals[hole] >= vals[diameter]:
            return "", f"{hole}_mils must be smaller than {diameter}_mils"
    return ";".join(out), ""


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
