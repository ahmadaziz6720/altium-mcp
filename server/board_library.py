"""make_pcblib_from_board's reply: Altium's library from a board, compared
with the board.

The bridge command (other_utils.pas, MakePcbLibFromBoard) runs Altium's own
Make PCB Library on the board, saves the library and reads the saved file
back. It returns the board's components as "pattern|pads", the footprints it
kept before saving as names, and the footprints read back from the saved file
as "name|pads|primitives". This module turns that into the tool's result and
says what does not agree: a pattern of the board (in scope) with no footprint
in the saved file, a footprint whose pad count no component of its pattern
has, a component pad count no footprint of its pattern has, or a footprint
kept that the saved file does not hold.

Altium writes one footprint per pattern, and a second footprint of a pattern
whose components differ gets "_<n>" after the name (CR2012-0805_2).
"""

import re

_SUFFIX = re.compile(r"^(.*)_(\d+)$")


def _split(item, fields):
    """'a|b|c' split from the right into fields parts (a pattern may hold
    '|'), or None."""
    parts = str(item).rsplit("|", fields - 1)
    return parts if len(parts) == fields else None


def board_patterns(components):
    """{PATTERN (upper case): {"name", "components", "pads": set}} of the
    board's components given as "pattern|pads"."""
    out = {}
    for item in components or []:
        parts = _split(item, 2)
        if not parts:
            continue
        name, pads = parts
        try:
            pads = int(pads)
        except ValueError:
            continue
        entry = out.setdefault(name.upper(), {"name": name, "components": 0, "pads": set()})
        entry["components"] += 1
        entry["pads"].add(pads)
    return out


def pattern_of(footprint, patterns):
    """The board pattern (upper case) a footprint of Altium's library comes
    from: its own name, or its name without Altium's "_<n>"; None when
    neither is a pattern of the board."""
    upper = footprint.upper()
    if upper in patterns:
        return upper
    m = _SUFFIX.match(upper)
    if m and m.group(1) in patterns:
        return m.group(1)
    return None


def in_scope(patterns, wanted):
    """The patterns asked for (upper case), all of them when wanted is
    empty."""
    if not wanted:
        return set(patterns)
    return {w.strip().upper() for w in wanted if w.strip().upper() in patterns}


def summarise(reply, wanted=None):
    """The tool's result from the bridge's reply. "problems" lists what does
    not agree with the board; empty means every pattern in scope was written
    with the pad counts its components have."""
    patterns = board_patterns(reply.get("board_components"))
    scope = in_scope(patterns, wanted)
    written = []
    for item in reply.get("written") or []:
        parts = _split(item, 3)
        if not parts:
            continue
        name, pads, prims = parts
        try:
            written.append({"name": name, "pads": int(pads), "primitives": int(prims)})
        except ValueError:
            continue

    problems = []
    covered = {}
    for fp in written:
        pattern = pattern_of(fp["name"], patterns)
        if pattern is None:
            problems.append(f"{fp['name']}: not a pattern of the board")
            continue
        if patterns[pattern]["name"] != fp["name"]:
            fp["pattern"] = patterns[pattern]["name"]
        covered.setdefault(pattern, set()).add(fp["pads"])
        if fp["pads"] not in patterns[pattern]["pads"]:
            problems.append(f"{fp['name']}: {fp['pads']} pads, its components on the board have "
                            f"{', '.join(str(p) for p in sorted(patterns[pattern]['pads']))}")

    not_written = []
    for pattern in sorted(scope):
        entry = patterns[pattern]
        if pattern not in covered:
            not_written.append(entry["name"])
            problems.append(f"{entry['name']}: on the board ({entry['components']} components), "
                            "not in the saved library")
            continue
        missing = entry["pads"] - covered[pattern]
        if missing:
            problems.append(f"{entry['name']}: a component with {', '.join(str(p) for p in sorted(missing))} "
                            "pads has no footprint of that pad count in the saved library")

    saved = {fp["name"].upper() for fp in written}
    for name in reply.get("made") or []:
        if str(name).upper() not in saved:
            problems.append(f"{name}: kept before the save, not in the saved file")

    result = {
        "library_path": reply.get("library_path", ""),
        "board": reply.get("board", ""),
        "footprint_count": len(written),
        "footprints": written,
        "board_patterns": len(scope),
        "board_components": sum(patterns[p]["components"] for p in scope),
        "not_written": not_written,
        "problems": problems,
        "board_was_open": bool(reply.get("board_was_open")),
        "board_modified": bool(reply.get("board_modified")),
    }
    if reply.get("board_flag_cleared"):
        result["board_flag_cleared"] = True
    if reply.get("removed_by_filter"):
        result["removed_by_filter"] = reply["removed_by_filter"]
    return result
