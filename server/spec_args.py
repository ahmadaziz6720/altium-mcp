"""A tool's arguments from a JSON file (spec_file), for calls too large to
send inline.

The file holds arguments as the call would give them: the same names, checked
as the same types. One given inline and in the file is refused, not merged,
and so is a name the tool does not have: a misspelled "wires" would otherwise
build a sheet with none. A tool that takes a spec_file gives every other
argument the default None, which is how one not given inline is told from
one given with its default value.
"""
import inspect
import json
import os
from pathlib import Path

from pydantic import TypeAdapter, ValidationError


def resolve(path: str, tool, inline: dict, required: tuple) -> tuple:
    """(inline with the file's arguments filled in, in inline's order, "")
    when fine, else (inline, the error)."""
    args = dict(inline)
    if path:
        given, error = _read(path)
        if error:
            return inline, error
        unknown = [name for name in given if name not in inline]
        if unknown:
            return inline, (f"spec_file holds {', '.join(unknown[:10])}: not an argument it can give "
                            f"(those are {', '.join(inline)})")
        both = [name for name in given if inline[name] is not None]
        if both:
            return inline, (f"{', '.join(both)} given inline as well as in spec_file: give each argument "
                            "in one place")
        parameters = inspect.signature(tool, eval_str=True).parameters
        for name, value in given.items():
            try:
                args[name] = TypeAdapter(parameters[name].annotation).validate_python(value)
            except ValidationError as e:
                return inline, f"{name} in spec_file: {e.errors()[0]['msg']}"
    missing = [name for name in required if args[name] is None]
    if missing:
        return inline, f"missing {', '.join(missing)}: give it inline or in spec_file"
    return args, ""


def _read(path: str) -> tuple:
    """(the file's object, "") when fine, else ({}, the error)."""
    # A relative path would be read from the server's folder, not the caller's
    if not os.path.isabs(path):
        return {}, f"spec_file must be a full path: {path}"
    try:
        # From bytes: json tells UTF-8 and UTF-16, with or without a byte-order mark
        given = json.loads(Path(path).read_bytes())
    except (OSError, ValueError) as e:
        return {}, f"could not read spec_file {path} as JSON: {e}"
    if not isinstance(given, dict):
        return {}, f"spec_file must hold a JSON object of the call's arguments: {path}"
    return given, ""
