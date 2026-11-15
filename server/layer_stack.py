"""set_pcb_layer_stackup: the checks, the presets and the plan sent to Altium.

A stack is a list top to bottom in the form get_pcb_layer_stackup gives:
copper entries ("material_type": "Copper") and dielectric entries (cores,
prepregs, solder masks: "Dielectric"), values in mils. This module, which
needs no Altium, turns such a list into what the bridge's set_layer_stack
command does to a board (layers removed, layers added, values set), and
compares what Altium reads back with what was asked.

The shape a stack must have: the dielectrics above the top copper (the top
solder mask, and any surface layer), then copper and one dielectric in turn,
ending on copper, then the dielectrics below it. Altium keeps the Top Layer
and Bottom Layer always; a copper layer between them is added or removed with
the dielectric beside it, so one dielectric between two copper layers is what
the board can be given here.
"""
import re

INTERNAL_PER_MIL = 10000        # Altium's internal units per mil
DK_SCALE = 10000                # the constant is sent as an integer, x10000
UM_PER_MIL = 25.4

# TDielectricType as Altium numbers it, by the name the read gives
DIELECTRIC_TYPES = {"dielectric": 0, "core": 1, "prepreg": 2, "surface material": 3}
DIELECTRIC_TYPE_NAMES = {0: "Dielectric", 1: "Core", 2: "PrePreg", 3: "Surface Material"}
COPPER_TYPES = ("Signal", "Plane")

COPPER_KEYS = {"material_type", "layer_name", "layer_id", "copper_type", "copper_thickness_mils",
               "copper_thickness_um", "layer_order"}
DIELECTRIC_KEYS = {"material_type", "layer_name", "dielectric_type", "dielectric_material",
                   "dielectric_height_mils", "dielectric_height_um", "dielectric_constant", "layer_order"}

# What Altium can hold between Top Layer and Bottom Layer (Mid-Layer 1..30,
# Internal Plane 1..16)
MAX_INNER_SIGNAL = 30
MAX_PLANES = 16

# Values outside these are taken for a unit mistake (mm or um given as mils)
MAX_COPPER_MILS = 30.0          # about 22 oz
MAX_DIELECTRIC_MILS = 250.0     # 6.35 mm
MAX_DK = 100.0


def _mils(um):
    return round(um / UM_PER_MIL, 4)


def _mask():
    return {"material_type": "Dielectric", "dielectric_type": "Surface Material",
            "dielectric_material": "Solder Resist", "dielectric_height_mils": 0.4, "dielectric_constant": 3.5}


def _cu(um):
    return {"material_type": "Copper", "copper_type": "Signal", "copper_thickness_mils": _mils(um)}


def _diel(kind, material, um, dk):
    return {"material_type": "Dielectric", "dielectric_type": kind, "dielectric_material": material,
            "dielectric_height_mils": _mils(um), "dielectric_constant": dk}


# Generic builds, not a fabricator's figures: 1.6 mm of copper and dielectric
# (the solder masks, Altium's default 0.4 mil each, on top of that), 1 oz
# (35 um) outer copper, FR-4. The 4-layer one is the common build of a
# 7628-prepreg 4-layer board (fabricators such as JLCPCB offer one close to
# it): 0.5 oz (17.5 um) inner copper, one 7628 ply of 0.2 mm under each outer
# layer, a core making up the rest. The constants are typical FR-4 values
# (core 4.6, 7628 prepreg 4.4), approximate: for impedance work use the
# fabricator's own stack. Layer names are not set, so a board keeps its own
# and a new layer gets Altium's.
PRESETS = {
    "2_layer_1.6mm": {
        "description": "2 layers, 1.6 mm: 1 oz copper on a 1.53 mm FR-4 core (generic, approximate)",
        "layers": [_mask(), _cu(35.0), _diel("Core", "FR-4", 1530.0, 4.6), _cu(35.0),
                   _mask()],
    },
    "4_layer_1.6mm_7628": {
        "description": "4 layers, 1.6 mm, 7628 prepreg: 1 oz outer and 0.5 oz inner copper, "
                       "0.2 mm 7628 prepreg under each outer layer, 1.095 mm FR-4 core "
                       "(generic, approximate)",
        "layers": [_mask(), _cu(35.0), _diel("PrePreg", "FR-4 7628", 200.0, 4.4), _cu(17.5),
                   _diel("Core", "FR-4", 1095.0, 4.6), _cu(17.5), _diel("PrePreg", "FR-4 7628", 200.0, 4.4),
                   _cu(35.0), _mask()],
    },
}


def _preset_key(name):
    return re.sub(r"[\s_\-]+", "", str(name).lower())


def preset(name):
    """(the preset's layers, None), or (None, why not)."""
    want = _preset_key(name)
    for key, value in PRESETS.items():
        if _preset_key(key) == want:
            return [dict(l) for l in value["layers"]], None
    return None, (f"no preset {name!r}; the presets are: " +
                  "; ".join(f"{k} ({v['description']})" for k, v in PRESETS.items()))


def layer_id_key(text):
    """A layer id as compared: 'Mid-Layer 1' and 'mid layer 1' are one."""
    return re.sub(r"\s+", " ", str(text).replace("-", " ")).strip().lower()


def _kind_of_id(layer_id):
    key = layer_id_key(layer_id)
    if key.startswith("internal plane"):
        return "Plane"
    if key.startswith("mid layer") or key in ("top layer", "bottom layer"):
        return "Signal"
    return None


def _text(value, where, key):
    if not isinstance(value, str):
        return None, f"{where}: {key} must be text"
    value = value.strip()
    if not value:
        return None, f"{where}: {key} is empty"
    if any(c in value for c in "|;") or any(ord(c) < 32 for c in value):
        return None, f"{where}: {key} may not hold '|', ';' or control characters"
    return value, None


def _number(value, where, key):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None, f"{where}: {key} must be a number"
    return float(value), None


def _length(entry, where, base, limit):
    """The entry's <base>_mils, or its <base>_um in mils; both must agree."""
    mils = entry.get(base + "_mils")
    um = entry.get(base + "_um")
    if mils is None and um is None:
        return None, None
    if mils is not None:
        mils, error = _number(mils, where, base + "_mils")
        if error:
            return None, error
    if um is not None:
        um, error = _number(um, where, base + "_um")
        if error:
            return None, error
        if mils is None:
            mils = um / UM_PER_MIL
        elif abs(mils * UM_PER_MIL - um) > 0.01:
            return None, (f"{where}: {base}_mils {mils} and {base}_um {um} disagree "
                          f"({mils} mil is {mils * UM_PER_MIL:.4f} um); give one of the two")
    mils = round(mils, 4)
    if mils <= 0 or mils > limit:
        return None, f"{where}: {base} {mils} mil is outside (0, {limit}] mil"
    return mils, None


def parse_layers(layers):
    """The list checked and made plain: (entries, None) or (None, why not).

    An entry keeps the keys given, values checked: copper_thickness_mils and
    dielectric_height_mils in mils rounded to Altium's 0.0001 mil (from the
    _um key when only that is given), dielectric_type and copper_type in the
    read's spelling. A key left out is left as the board has it."""
    if not isinstance(layers, list) or not layers:
        return None, "layers must be a list of stack entries, top to bottom"
    out = []
    for i, entry in enumerate(layers, 1):
        where = f"entry {i}"
        if not isinstance(entry, dict):
            return None, f"{where} is not an object"
        kind = str(entry.get("material_type", "")).strip().lower()
        if kind not in ("copper", "dielectric"):
            return None, f"{where}: material_type must be 'Copper' or 'Dielectric'"
        allowed = COPPER_KEYS if kind == "copper" else DIELECTRIC_KEYS
        unknown = sorted(set(entry) - allowed)
        if unknown:
            return None, (f"{where} ({entry.get('material_type')}): unknown key(s) {', '.join(unknown)}; "
                          f"the keys are {', '.join(sorted(allowed))}")
        item = {"material_type": "Copper" if kind == "copper" else "Dielectric"}
        if entry.get("layer_name") is not None:
            item["layer_name"], error = _text(entry["layer_name"], where, "layer_name")
            if error:
                return None, error
        if kind == "copper":
            if entry.get("layer_id") is not None:
                item["layer_id"], error = _text(entry["layer_id"], where, "layer_id")
                if error:
                    return None, error
            ctype = entry.get("copper_type")
            if ctype is not None:
                match = [t for t in COPPER_TYPES if t.lower() == str(ctype).strip().lower()]
                if not match:
                    return None, f"{where}: copper_type must be 'Signal' or 'Plane'"
                ctype = match[0]
            id_kind = _kind_of_id(item["layer_id"]) if "layer_id" in item else None
            if ctype and id_kind and ctype != id_kind:
                return None, f"{where}: layer_id {item['layer_id']!r} is a {id_kind} layer, copper_type says {ctype}"
            if ctype or id_kind:
                item["copper_type"] = ctype or id_kind
            value, error = _length(entry, where, "copper_thickness", MAX_COPPER_MILS)
            if error:
                return None, error
            if value is not None:
                item["copper_thickness_mils"] = value
        else:
            dtype = entry.get("dielectric_type")
            if dtype is not None:
                code = DIELECTRIC_TYPES.get(str(dtype).strip().lower())
                if code is None:
                    return None, (f"{where}: dielectric_type must be one of "
                                  f"{', '.join(DIELECTRIC_TYPE_NAMES.values())}")
                item["dielectric_type"] = DIELECTRIC_TYPE_NAMES[code]
            if entry.get("dielectric_material") is not None:
                item["dielectric_material"], error = _text(entry["dielectric_material"], where,
                                                           "dielectric_material")
                if error:
                    return None, error
            value, error = _length(entry, where, "dielectric_height", MAX_DIELECTRIC_MILS)
            if error:
                return None, error
            if value is not None:
                item["dielectric_height_mils"] = value
            if entry.get("dielectric_constant") is not None:
                dk, error = _number(entry["dielectric_constant"], where, "dielectric_constant")
                if error:
                    return None, error
                dk = round(dk, 4)
                if dk < 1 or dk > MAX_DK:
                    return None, f"{where}: dielectric_constant {dk} is outside [1, {MAX_DK}]"
                item["dielectric_constant"] = dk
        out.append(item)
    return out, None


def split(entries, whose="the list"):
    """(top, coppers, gaps, bottom, None): the dielectrics above the top
    copper, the copper entries, the one dielectric between each two, the
    dielectrics below; or (..., why not)."""
    kinds = [e["material_type"] for e in entries]
    if "Copper" not in kinds:
        return None, None, None, None, f"{whose} has no copper layer"
    first = kinds.index("Copper")
    last = len(kinds) - 1 - kinds[::-1].index("Copper")
    top, body, bottom = entries[:first], entries[first:last + 1], entries[last + 1:]
    coppers, gaps = [], []
    i = 0
    while i < len(body):
        coppers.append(body[i])
        i += 1
        if i >= len(body):
            break
        run = []
        while body[i]["material_type"] == "Dielectric":
            run.append(body[i])
            i += 1
        above = coppers[-1].get("layer_name", f"copper {len(coppers)}")
        below = body[i].get("layer_name", f"copper {len(coppers) + 1}")
        if len(run) != 1:
            what = "no dielectric" if not run else f"{len(run)} dielectrics"
            return None, None, None, None, (
                f"{whose} has {what} between {above} and {below}: a stack set here has one dielectric "
                f"between two copper layers (Altium adds and removes a copper layer with the dielectric "
                f"beside it); use Altium's Layer Stack Manager for more")
        gaps.append(run[0])
    if len(coppers) < 2:
        return None, None, None, None, f"{whose} has {len(coppers)} copper layer; Altium's boards have at least 2"
    return top, coppers, gaps, bottom, None


def plan(wanted, board):
    """What turns the board's stack (its read, parsed) into wanted, both lists
    of entries. Returns (plan, None) or (None, why not). The plan: "remove",
    the board's copper entries to remove; "add", per new copper its index in
    the final copper list, kind and the board layer it goes above; "final",
    every entry of the final stack in order with what it is set to."""
    w_top, w_cu, w_gaps, w_bottom, error = split(wanted)
    if error:
        return None, error
    b_top, b_cu, b_gaps, b_bottom, error = split(board, "the board's stack")
    if error:
        return None, error
    for name, w, b in (("above the top copper", w_top, b_top), ("below the bottom copper", w_bottom, b_bottom)):
        if w and len(w) != len(b):
            return None, (f"the list has {len(w)} dielectric(s) {name}, the board {len(b)} "
                          f"({', '.join(e.get('layer_name', '?') for e in b) or 'none'}): give the same number, "
                          f"or none to leave them as they are; surface layers are not added or removed here")
    for name, entry, fixed in (("top", w_cu[0], "Top Layer"), ("bottom", w_cu[-1], "Bottom Layer")):
        if entry.get("copper_type") == "Plane":
            return None, f"the {name} copper layer cannot be a plane: it is always Altium's {fixed}"
        if "layer_id" in entry and layer_id_key(entry["layer_id"]) != layer_id_key(fixed):
            return None, f"the {name} copper layer is always Altium's {fixed}, not {entry['layer_id']}"

    ids = [layer_id_key(w["layer_id"]) for w in w_cu if "layer_id" in w]
    twice = sorted({i for i in ids if ids.count(i) > 1})
    if twice:
        return None, f"layer_id given twice: {', '.join(twice)}"
    w_inner, b_inner = w_cu[1:-1], b_cu[1:-1]
    b_index = {layer_id_key(b["layer_id"]): j for j, b in enumerate(b_inner)}
    # The board layer each entry names by layer_id, when the board has it
    named = [b_index.get(layer_id_key(w["layer_id"])) if "layer_id" in w else None for w in w_inner]
    claimed = {j for j in named if j is not None}
    match = [None] * len(w_inner)
    p = 0
    for i, w in enumerate(w_inner):
        j = named[i]
        if j is not None:
            if j < p:
                return None, (f"{w['layer_id']} is listed out of the board's order of its inner layers "
                              f"({', '.join(b['layer_id'] for b in b_inner)}): existing layers are not "
                              f"reordered here; leave one out (it is removed) and list a new layer instead")
            if w.get("copper_type") and w["copper_type"] != b_inner[j].get("copper_type"):
                return None, f"{w['layer_id']} is a {b_inner[j].get('copper_type')} layer, not a {w['copper_type']}"
            match[i], p = j, j + 1
        elif "layer_id" not in w:
            # The next free board layer of the same kind, before the next named one
            stop = min([k for k in named[i + 1:] if k is not None] + [len(b_inner)])
            for k in range(p, stop):
                if k in claimed:
                    continue
                if w.get("copper_type") in (None, b_inner[k].get("copper_type")):
                    match[i], p = k, k + 1
                    claimed.add(k)
                    break
    kept = {j for j in match if j is not None}
    remove = [b for j, b in enumerate(b_inner) if j not in kept]

    signals = sum(1 for i, w in enumerate(w_inner)
                  if (b_inner[match[i]].get("copper_type") if match[i] is not None else w.get("copper_type"))
                  != "Plane")
    planes = len(w_inner) - signals
    if signals > MAX_INNER_SIGNAL or planes > MAX_PLANES:
        return None, (f"{signals} inner signal layers and {planes} planes: Altium holds at most "
                      f"{MAX_INNER_SIGNAL} and {MAX_PLANES}")

    # Each new layer goes above the next kept copper below it (Bottom Layer at the last)
    add = []
    for i, w in enumerate(w_inner):
        if match[i] is None:
            below = next((b_inner[match[k]]["layer_id"] for k in range(i + 1, len(w_inner)) if match[k] is not None),
                         b_cu[-1]["layer_id"])
            add.append({"index": i + 1, "copper_type": w.get("copper_type") or "Signal", "above": below,
                        "layer_name": w.get("layer_name")})

    final_cu = [dict(w_cu[0], layer_id=b_cu[0]["layer_id"])]
    for i, w in enumerate(w_inner):
        final_cu.append(dict(w, layer_id=b_inner[match[i]]["layer_id"]) if match[i] is not None
                        else dict(w, copper_type=w.get("copper_type") or "Signal", new=True))
    final_cu.append(dict(w_cu[-1], layer_id=b_cu[-1]["layer_id"]))
    final = list(w_top) if w_top else [{"material_type": "Dielectric", "keep": True} for _ in b_top]
    for i, c in enumerate(final_cu):
        if i:
            final.append(w_gaps[i - 1])
        final.append(c)
    final += list(w_bottom) if w_bottom else [{"material_type": "Dielectric", "keep": True} for _ in b_bottom]
    return {"remove": remove, "add": add, "final": final,
            "structural": bool(remove or add)}, None


def _internal(mils):
    return str(int(round(mils * INTERNAL_PER_MIL)))


def encode(the_plan):
    """The bridge's set_layer_stack spec, records joined by ';':
    R|<layer id> per layer removed, A|S or A|P|<layer id it goes above> per
    layer added (in order top to bottom), then per entry of the final stack
    C|<name>|<thickness> or D|<name>|<type>|<material>|<height>|<constant>,
    lengths in internal units, the constant x10000; an empty field is left as
    the board has it."""
    recs = [f"R|{r['layer_id']}" for r in the_plan["remove"]]
    recs += [f"A|{'P' if a['copper_type'] == 'Plane' else 'S'}|{a['above']}" for a in the_plan["add"]]
    for e in the_plan["final"]:
        name = e.get("layer_name", "")
        if e["material_type"] == "Copper":
            t = e.get("copper_thickness_mils")
            recs.append(f"C|{name}|{_internal(t) if t is not None else ''}")
        else:
            dtype = e.get("dielectric_type")
            h = e.get("dielectric_height_mils")
            dk = e.get("dielectric_constant")
            recs.append("D|" + "|".join([
                name,
                str(DIELECTRIC_TYPES[dtype.lower()]) if dtype else "",
                e.get("dielectric_material", ""),
                _internal(h) if h is not None else "",
                str(int(round(dk * DK_SCALE))) if dk is not None else ""]))
    return ";".join(recs)


COMPARED = ("layer_name", "copper_type", "copper_thickness_mils", "dielectric_type", "dielectric_material",
            "dielectric_height_mils", "dielectric_constant")


def compare(final, read_layers):
    """Where Altium's read differs from what was asked: a list of
    {"entry", "key", "asked", "read"}, empty when equal on every key given."""
    if len(final) != len(read_layers):
        return [{"entry": None, "key": "layers", "asked": len(final), "read": len(read_layers)}]
    out = []
    for i, (want, got) in enumerate(zip(final, read_layers), 1):
        if want["material_type"] != got.get("material_type"):
            out.append({"entry": i, "key": "material_type", "asked": want["material_type"],
                        "read": got.get("material_type")})
            continue
        for key in COMPARED:
            if key not in want:
                continue
            asked, read = want[key], got.get(key)
            if isinstance(asked, float):
                same = isinstance(read, (int, float)) and abs(read - asked) < 0.00005
            else:
                same = asked == read
            if not same:
                out.append({"entry": i, "key": key, "asked": asked, "read": read})
    return out


def value_changes(final, board_layers, structural):
    """For a dry run: the values a set would change, by entry of the final
    stack. With layers added or removed only the top and bottom copper and
    the surface layers are compared, as which dielectric Altium keeps beside a
    layer added or removed is its own; the rest is set as listed."""
    if not structural:
        pairs = list(zip(range(1, len(final) + 1), final, board_layers))
    else:
        b_cu = [i for i, e in enumerate(board_layers) if e["material_type"] == "Copper"]
        f_cu = [i for i, e in enumerate(final) if e["material_type"] == "Copper"]
        idx = list(range(f_cu[0] + 1)) + list(range(f_cu[-1], len(final)))
        b_idx = list(range(b_cu[0] + 1)) + list(range(b_cu[-1], len(board_layers)))
        pairs = [(i + 1, final[i], board_layers[j]) for i, j in zip(idx, b_idx)]
    out = []
    for n, want, have in pairs:
        for key in COMPARED:
            if key in want and want[key] != have.get(key):
                out.append({"entry": n, "layer_name": have.get("layer_name"), "key": key,
                            "from": have.get(key), "to": want[key]})
    return out
