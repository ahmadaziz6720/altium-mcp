"""Summarizing get_erc_violations' reply.

A project with a few hundred violations comes to 100,000 characters and more
when every one is listed in full, past what a client takes in one tool
result; most of them are a few kinds repeated (a sheet's duplicate nets, a
copied block's duplicate designators). So the reply is grouped here, after
Altium returns it: one group per level and type, with its count and its
first few details, and the full list goes to a file the reply names.
"""
import hashlib
import json
import re
from pathlib import Path

# Details kept per group in the reply
FIRST = 3

# Groups in this order of level, then the largest first
_LEVELS = {"fatal": 0, "error": 1, "warning": 2}


def full_list_path(folder: Path, project_path: str) -> Path:
    """Where the full list of a project's violations goes: one file per
    project in folder, named for the project and a hash of its path, so two
    projects of one name do not share it."""
    stem = re.sub(r"[^\w.-]+", "_", Path(project_path or "project").stem)[:60] or "project"
    digest = hashlib.sha1(str(project_path).lower().encode("utf-8")).hexdigest()[:8]
    return Path(folder) / f"erc_{stem}_{digest}.json"


def group(violations: list, first: int = FIRST) -> list:
    """[{level, type, count, first}] of violations [{level, type, detail}],
    first holding the details of the group's first violations in Altium's
    order."""
    groups = {}
    for v in violations:
        key = (v.get("level", ""), v.get("type", ""))
        g = groups.setdefault(key, {"level": key[0], "type": key[1], "count": 0, "first": []})
        g["count"] += 1
        if len(g["first"]) < first:
            g["first"].append(v.get("detail", ""))
    return sorted(groups.values(), key=lambda g: (_LEVELS.get(g["level"], len(_LEVELS)), -g["count"]))


def summarize(data: dict, full_list: str, error: str = "") -> dict:
    """data, Altium's reply, with its violations replaced by their groups and
    the path of the file holding them all (None, with full_list_error, when
    it could not be written)."""
    out = {k: v for k, v in data.items() if k != "violations"}
    out["groups"] = group(data.get("violations", []))
    out["full_list"] = full_list or None
    if error:
        out["full_list_error"] = error
    return out


def write_full_list(data: dict, path: Path) -> str:
    """Write Altium's whole reply to path; '' when done, else the error."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    except OSError as e:
        return f"could not write the full list to {path}: {e}"
    return ""
