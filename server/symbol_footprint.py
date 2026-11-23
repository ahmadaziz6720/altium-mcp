"""Footprint models of a library symbol: checking the FOOTPRINT records of a
symbol batch and the footprints argument of create_schematic_symbol before
Altium is asked to do anything.

A record is  <model name>[|<library>[|<current>]]  (in a batch spec behind
FOOTPRINT|): the footprint's name, the .PcbLib file that holds it (full path;
left out, the model is linked by name alone and Altium looks for it in the
libraries of the project), and 1 or 0 for whether it is the symbol's current
footprint (left out, it is the current one only when the symbol has none yet).
A symbol can carry several footprints and at most one is current, so two
records asking for it are refused. The script applies what is left, and the
result is read back from the library, not from the request.
"""
import os

from altium_files import long_path


def parse_record(record, exists=os.path.isfile):
    """One footprint record as (model, library, current): library the full
    path ('' when none), current '1', '0' or '' (not said). Raises ValueError
    naming what is wrong."""
    fields = [f.strip() for f in str(record).split("|")]
    if len(fields) > 3:
        raise ValueError(f"footprint '{record}' has more than three fields "
                         "(model name|library|current); a '|' cannot be in a name")
    fields += [""] * (3 - len(fields))
    model, library, current = fields
    if not model:
        raise ValueError(f"footprint '{record}' has no model name")
    if current not in ("", "0", "1"):
        raise ValueError(f"footprint '{record}': current is 1 or 0, not '{current}'")
    if library:
        if not library.lower().endswith(".pcblib"):
            raise ValueError(f"footprint '{model}': the library must be a .PcbLib file, not '{library}'")
        library = long_path(library)
        if not os.path.isabs(library):
            raise ValueError(f"footprint '{model}': the library must be a full path, not '{library}'")
        if not exists(library):
            raise ValueError(f"footprint '{model}': the library is not a file: {library}")
    return model, library, current


def check_records(records, exists=os.path.isfile):
    """The records of one symbol checked together and normalised: a list of
    (model, library, current). Raises ValueError for a bad record, a model
    named twice (a name is one footprint of the symbol) or two records asking
    to be the current one."""
    parsed = [parse_record(r, exists) for r in records]
    seen = set()
    for model, _, _ in parsed:
        if model.lower() in seen:
            raise ValueError(f"footprint '{model}' is given twice for one symbol")
        seen.add(model.lower())
    if sum(1 for _, _, current in parsed if current == "1") > 1:
        raise ValueError("more than one footprint is asked to be the current one (only one can be)")
    return parsed


def format_record(model, library, current):
    return f"{model}|{library}|{current}"


def normalize_spec(text, exists=os.path.isfile):
    """A batch spec's text with each FOOTPRINT| line checked and rewritten
    in full (library as a long full path, three fields), and the errors:
    (text, [message]). A FOOTPRINT line belongs to the last SYMBOL or
    EDITSYMBOL line before it. The text is returned unchanged when there is
    no FOOTPRINT line."""
    lines = text.split("\n")
    errors = []
    symbol = None
    group = []   # (line index, record) of the symbol being read

    def finish():
        if group:
            try:
                parsed = check_records([record for _, record in group], exists)
            except ValueError as e:
                errors.append(f"{symbol}: {e}")
                return
            for (i, _), (model, library, current) in zip(group, parsed):
                lines[i] = "FOOTPRINT|" + format_record(model, library, current)

    for i, line in enumerate(lines):
        fields = line.split("|")
        kind = fields[0].strip().upper()
        if kind in ("SYMBOL", "EDITSYMBOL"):
            finish()
            group = []
            symbol = fields[1].strip() if len(fields) > 1 else ""
        elif kind == "FOOTPRINT":
            if symbol is None:
                errors.append(f"line {i + 1}: FOOTPRINT before any SYMBOL or EDITSYMBOL")
                continue
            group.append((i, "|".join(fields[1:])))
    finish()
    return "\n".join(lines), errors


def search_order(project_libraries, installed):
    """The .PcbLib files a footprint linked by name is looked for in (A66):
    the project's libraries, then the installed ones in Altium's order, each
    once. Other kinds (an .IntLib, a .SchLib) cannot be linked to as a
    footprint's library and are left out."""
    order, seen = [], set()
    for path in list(project_libraries or []) + list(installed or []):
        path = str(path).strip()
        if path.lower().endswith(".pcblib") and path.lower() not in seen:
            seen.add(path.lower())
            order.append(path)
    return order


def not_found_problem(symbol, model):
    who = f"{symbol}: " if symbol else ""
    return (f"{who}footprint {model} is in no saved .PcbLib of the project or installed in "
            "Altium; linked by name only (give its library)")


def locate(models, libraries, held):
    """{model (upper case): library} for each model name the libraries hold,
    the first library in order that holds it. held(path, names) gives the
    upper-case names of names the saved file holds (None or an empty set
    when it holds none or cannot be read)."""
    found = {}
    wanted = {m.upper() for m in models}
    for path in libraries:
        left = [m for m in wanted if m not in found]
        if not left:
            break
        for name in held(path, left) or ():
            found.setdefault(name.upper(), path)
    return found


def fill_records(records, libraries, held, symbol=""):
    """create_schematic_symbol's records (model, library, current) with each
    name-only model given the library that holds it, and a problem line for
    each one no library holds: (records, [problem])."""
    names = [m for m, lib, _ in records if not lib]
    if not names:
        return list(records), []
    found = locate(names, libraries, held)
    out, problems = [], []
    for model, lib, current in records:
        if not lib:
            lib = found.get(model.upper(), "")
            if not lib:
                problems.append(not_found_problem(symbol, model))
        out.append((model, lib, current))
    return out, problems


def name_only_models(text):
    """The model names of a normalised spec's FOOTPRINT lines that give no
    library."""
    names = []
    for line in text.split("\n"):
        fields = line.split("|")
        if fields[0].strip().upper() == "FOOTPRINT" and len(fields) > 1 and fields[1].strip():
            if len(fields) < 3 or not fields[2].strip():
                names.append(fields[1].strip())
    return names


def spec_library(text):
    """The LIBRARY| path of a batch spec ('' when it has none: the focused
    library)."""
    for line in text.split("\n"):
        fields = line.split("|")
        if fields[0].strip().upper() == "LIBRARY" and len(fields) > 1:
            return fields[1].strip()
    return ""


def fill_spec(text, libraries, held):
    """A normalised spec with each name-only FOOTPRINT line given the library
    that holds it, and a problem line for each one no library holds:
    (text, [problem])."""
    names = name_only_models(text)
    if not names:
        return text, []
    found = locate(names, libraries, held)
    lines = text.split("\n")
    problems = []
    symbol = ""
    for i, line in enumerate(lines):
        fields = line.split("|")
        kind = fields[0].strip().upper()
        if kind in ("SYMBOL", "EDITSYMBOL"):
            symbol = fields[1].strip() if len(fields) > 1 else ""
        elif kind == "FOOTPRINT" and len(fields) > 1 and fields[1].strip():
            fields += [""] * (4 - len(fields))
            if fields[2].strip():
                continue
            model = fields[1].strip()
            lib = found.get(model.upper(), "")
            if lib:
                fields[2] = lib
                lines[i] = "|".join(fields)
            else:
                problems.append(not_found_problem(symbol, model))
    return "\n".join(lines), problems
