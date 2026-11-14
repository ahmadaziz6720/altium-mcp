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
