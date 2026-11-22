"""build_schematic's pin map: every placed pin's connection point.

It is keyed by the pin's number, which tells pins of one name apart (several
GND, two shield pins), the name a field. A sheet of some 70 parts comes to
20,000 characters and more, and the caller needs it once: to route from. So
the reply holds it whole only for a call with no wires, the pin read the
tool's description advises; with wires it holds a count per part and the
path of a file with the map. The file is the server's own, in its per-user
folder: the exchange folder is readable by every account on the machine.
"""
import json
import os
import re
import tempfile
from pathlib import Path

# Map files kept. One per build, not per sheet: Altium gives a new free sheet
# the name of one closed before (Sheet1.SchDoc again), and the path a reply
# gave must not come to hold another sheet's pins at the next build.
KEEP = 20


def parse(text: str) -> dict:
    """{part: {number: {name, x, y}}}, in mils, of the bridge's lines
    PIN|part|number|x|y|name (Altium's coords, 10000 a mil; the name last, as
    it may hold a "|"). A number a part has again gets "#2", "#3", ..."""
    parts = {}
    for line in text.splitlines():
        f = line.split("|", 5)
        if len(f) != 6 or f[0] != "PIN":
            continue
        pins = parts.setdefault(f[1], {})
        key, n = f[2], 1
        while key in pins:
            n += 1
            key = f"{f[2]}#{n}"
        pins[key] = {"name": f[5], "x": int(f[3]) / 10000, "y": int(f[4]) / 10000}
    return parts


def counts(pins: dict) -> dict:
    """{part: its number of pins}."""
    return {part: len(numbers) for part, numbers in pins.items()}


def write(folder: Path, sheet: str, pins: dict) -> tuple:
    """Write the map to a new file in folder, the newest KEEP left there;
    (its path, "") when done, else ("", the error)."""
    stem = re.sub(r"[^\w.-]+", "_", Path(sheet).stem)[:60] or "sheet"
    try:
        folder.mkdir(parents=True, exist_ok=True)
        fd, path = tempfile.mkstemp(prefix=f"pin_map_{stem}_", suffix=".json", dir=folder)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"sheet": sheet, "pin_map": pins}, f, indent=1, ensure_ascii=False)
    except OSError as e:
        return "", f"could not write the pin map to {folder}: {e}"
    _prune(folder, Path(path))
    return path, ""


def _prune(folder: Path, written: Path) -> None:
    try:
        others = sorted((p for p in folder.glob("pin_map_*.json") if p != written),
                        key=lambda p: p.stat().st_mtime, reverse=True)
        for old in others[KEEP - 1:]:
            old.unlink()
    except OSError:
        pass  # another server pruning, or a file held open: best effort
