"""What code the server runs: the version in manifest.json and, for a packaged
copy, the line its BUILD.txt holds.

Both files sit in the folder above server/. A copy made for release may carry
a BUILD.txt naming the build and the commit it was made from; a git checkout
has none. A file that is missing or unreadable gives None, never an error:
get_server_status must answer whatever state the folder is in.
"""
import json
from pathlib import Path
from typing import Dict, Optional

ROOT = Path(__file__).resolve().parent.parent


def manifest_version(root: Path = ROOT) -> Optional[str]:
    """The "version" of root/manifest.json, or None."""
    try:
        with open(root / "manifest.json", encoding="utf-8") as f:
            version = json.load(f).get("version")
    except (OSError, ValueError, AttributeError):
        return None
    return version if isinstance(version, str) and version.strip() else None


def build_line(root: Path = ROOT) -> Optional[str]:
    """The first non-empty line of root/BUILD.txt, or None."""
    try:
        data = (root / "BUILD.txt").read_bytes()
        # Out-File in Windows PowerShell 5 writes UTF-16 with a BOM;
        # Set-Content writes ANSI there and UTF-8 in PowerShell 7.
        if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
            text = data.decode("utf-16")
        else:
            text = data.decode("utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return None


def build_info(root: Path = ROOT) -> Dict[str, Optional[str]]:
    return {"version": manifest_version(root), "build": build_line(root)}
