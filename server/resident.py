"""The resident bridge (A30): a script form that stays in Altium and serves
requests from a timer, so a call needs no script launch.

Every launch (X2.EXE -RScriptingSystem:RunScriptFile) makes Altium activate
itself, which A22's guard only undoes after the fact, and costs about 2 s
before the script takes the request. A form shown by RunScript of a script
PROJECT outlives the script that showed it, and its TTimer keeps firing; a
script FILE cannot do it (RunScriptFile loads no .dfm). So the bridge, as the
one unit script_bundle makes of it, and Resident/MCPResident.pas go into a
script project of their own, under the exchange folder, named by a tag of
their content, and it is started once.

The protocol, all of it beside the exchange folder's request.json:
  <root>/<tag>/take   written by the server after request.json; the form
                      deletes it and runs the bridge's Run. A take file the
                      server can still delete is a request not claimed.
  <root>/<tag>/stop   closes the form (another build's, being replaced).
  window caption      "altium-mcp resident <tag> <yyyymmddhhnnss>", set once
                      a second: the heartbeat, read with GetWindowText, which
                      for another process's window sends no message and so
                      never waits on Altium. Never a file: the server opening
                      one the form writes made the form's write fail once,
                      and an error in its handler stops its timer for good.
"""
import ctypes
import hashlib
import shutil
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import script_bundle

TEMPLATE_DIR = Path(__file__).parent / "AltiumScript" / "Resident"
UNIT = "MCPResident"
# The bridge's units, bundled into one (script_bundle)
BRIDGE_UNIT = "MCPBridge"
CAPTION = "altium-mcp resident "
# A caption older than this is a resident whose timer no longer runs
BEAT_FRESH = 5.0
# The newest prepared projects kept under the root
KEEP = 3


@dataclass
class Window:
    hwnd: int
    tag: str
    beat: Optional[float]     # epoch seconds of the caption's time; None: stopped or unreadable
    enabled: bool             # False while Altium runs a modal loop (VCL disables its other forms)

    def fresh(self, now: float) -> bool:
        return self.beat is not None and abs(now - self.beat) <= BEAT_FRESH


def parse_caption(text: str):
    """(tag, epoch seconds or None) of a resident's caption, or None."""
    if not text.startswith(CAPTION):
        return None
    parts = text[len(CAPTION):].split()
    if not parts:
        return None
    beat = None
    if len(parts) > 1:
        try:
            beat = datetime.strptime(parts[1], "%Y%m%d%H%M%S").timestamp()
        except ValueError:
            beat = None
    return parts[0], beat


def windows() -> List[Window]:
    """The resident forms of Altium (X2.EXE), any build's."""
    import sandbox
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    proto = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    found: List[Window] = []

    def top(hwnd, _):
        parsed = parse_caption(sandbox._window_text(hwnd))
        if parsed and sandbox._process_name(hwnd).lower() == "x2.exe":
            found.append(Window(int(hwnd), parsed[0], parsed[1], bool(user32.IsWindowEnabled(hwnd))))
        return True

    user32.EnumWindows(proto(top), 0)
    return found


GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000


def _taskbar_delete_tab(hwnd: int) -> bool:
    """ITaskbarList::DeleteTab, through the COM vtable with ctypes."""
    from ctypes import wintypes

    class GUID(ctypes.Structure):
        _fields_ = [("a", wintypes.DWORD), ("b", wintypes.WORD), ("c", wintypes.WORD),
                    ("d", ctypes.c_ubyte * 8)]

    def guid(a, b, c, d):
        return GUID(a, b, c, (ctypes.c_ubyte * 8)(*d))

    clsid = guid(0x56FDF344, 0xFD6D, 0x11D0, (0x95, 0x8A, 0x00, 0x60, 0x97, 0xC9, 0xA0, 0x90))
    iid = guid(0x56FDF342, 0xFD6D, 0x11D0, (0x95, 0x8A, 0x00, 0x60, 0x97, 0xC9, 0xA0, 0x90))
    ole32 = ctypes.OleDLL("ole32")
    init = ctypes.windll.ole32.CoInitializeEx(None, 2)  # apartment; S_FALSE / RPC_E_CHANGED_MODE are fine
    p = ctypes.c_void_p()
    try:
        ole32.CoCreateInstance(ctypes.byref(clsid), None, 1, ctypes.byref(iid), ctypes.byref(p))
        vtbl = ctypes.cast(ctypes.cast(p, ctypes.POINTER(ctypes.c_void_p))[0],
                           ctypes.POINTER(ctypes.c_void_p))
        method = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p)
        method_hwnd = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p, wintypes.HWND)
        release = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(vtbl[2])
        try:
            method(vtbl[3])(p)                      # HrInit
            method_hwnd(vtbl[5])(p, hwnd)           # DeleteTab
            return True
        finally:
            release(p)
    except OSError:
        return False
    finally:
        if init in (0, 1):
            ctypes.windll.ole32.CoUninitialize()


def hide_from_taskbar(hwnd: int) -> bool:
    """Take the resident's form off the taskbar and Alt+Tab. Altium gives a
    script form WS_EX_APPWINDOW, so the form, which must stay shown, had a
    taskbar button of its own; hiding it, even after its script ended, freed
    it (2026-11-15). Its styles are changed from here (allowed for another
    process's window) so that the taskbar does not list it again, and its
    button is removed. True when it is off the taskbar."""
    user32 = ctypes.windll.user32
    ex = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    if ex & WS_EX_APPWINDOW or not ex & WS_EX_TOOLWINDOW:
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, (ex & ~WS_EX_APPWINDOW) | WS_EX_TOOLWINDOW)
        return _taskbar_delete_tab(hwnd)
    return True


def decide(found: List[Window], tag: str, now: float, *, enabled: bool, altium_running: bool,
           message_open: bool, start_failures: int, max_failures: int = 2):
    """How this call reaches Altium: ("resident" | "start" | "launch", why).

    "launch" is the script launch per call, as before A30: when the resident
    is off, Altium is not running (the launch starts it), an Altium message
    or another modal loop is up (the form's timer fires inside it, so the
    request would be served there), a resident of this build is there but
    its timer stopped, or starting one failed max_failures times."""
    if not enabled:
        return "launch", "the resident bridge is off in config.json"
    if not altium_running:
        return "launch", "Altium is not running"
    if message_open:
        return "launch", "an Altium message is open"
    ours = [w for w in found if w.tag == tag]
    if any(w.fresh(now) and not w.enabled for w in ours):
        return "launch", "Altium is in a modal loop"
    if any(w.fresh(now) for w in ours):
        return "resident", "alive"
    if ours:
        return "launch", "a resident of this build is there but its timer has stopped"
    if start_failures >= max_failures:
        return "launch", f"starting the resident failed {start_failures} times"
    return "start", "none of this build is running"


class Resident:
    """The resident project of one script project's units, under root."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.tag: Optional[str] = None
        self.project: Optional[Path] = None
        self._stamp = None

    def folder(self, tag: Optional[str] = None) -> Path:
        return self.root / (tag or self.tag)

    def take_file(self, tag: Optional[str] = None) -> Path:
        return self.folder(tag) / "take"

    def stop_file(self, tag: Optional[str] = None) -> Path:
        return self.folder(tag) / "stop"

    def prepare(self, script_project) -> Path:
        """The resident's .PrjScr for the given bridge project, written when
        its units change; sets tag. The tag is a hash of every file's text,
        so a resident of an older build is told apart by its caption.

        The bridge goes in as script_bundle's single unit, the code a launch
        runs, not as its own units: a script project compiles each unit in
        the order written, and a unit that calls a routine defined further
        down fails there ("Undeclared identifier: SchLibIsFocused", 2026-11-15),
        which the bundle's ordering avoids. Raises ValueError when the bundle
        cannot be built, as script_bundle does."""
        script_project = Path(script_project)
        units = script_bundle.project_units(script_project)
        templates = [TEMPLATE_DIR / f"{UNIT}.pas", TEMPLATE_DIR / f"{UNIT}.dfm"]
        stamp = tuple((str(p), p.stat().st_mtime, p.stat().st_size)
                      for p in units + templates + [script_project, Path(script_bundle.__file__)])
        if stamp == self._stamp and self.project is not None and self.project.exists():
            return self.project
        texts = [(f"{BRIDGE_UNIT}.pas", script_bundle.bundle_text(units).encode("latin-1"))]
        texts += [(p.name, p.read_bytes()) for p in templates]
        # Altium compiles CRLF only ("Error in declaration block"). The tag is
        # hashed from the text as it is written, so a copy with LF line ends
        # (git archive) and a checkout with CRLF (core.autocrlf) at one commit
        # give one tag and do not close each other's resident (A34 a).
        texts = [(name, data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
                 for name, data in texts]
        digest = hashlib.sha256()
        for name, data in texts:
            digest.update(name.encode() + b"\0" + data + b"\0")
        tag = digest.hexdigest()[:12]
        folder = self.root / tag
        project = folder / f"{UNIT}.PrjScr"
        if not project.exists():
            tmp = self.root / f"{tag}.tmp"
            shutil.rmtree(tmp, ignore_errors=True)
            tmp.mkdir(parents=True)
            fill = {"%TAG%": tag, "%DIR%": str(folder) + "\\"}
            for name, data in texts:
                if name.startswith(UNIT):
                    text = data.decode("latin-1")
                    for k, v in fill.items():
                        text = text.replace(k, v)
                    data = text.encode("latin-1")
                (tmp / name).write_bytes(data)
            docs = [f"{BRIDGE_UNIT}.pas", f"{UNIT}.pas"]
            prj = "[Design]\nVersion=1.0\n\n" + "".join(
                f"[Document{i + 1}]\nDocumentPath={d}\n\n" for i, d in enumerate(docs))
            (tmp / project.name).write_bytes(prj.replace("\n", "\r\n").encode("latin-1"))
            if folder.exists():
                shutil.rmtree(folder, ignore_errors=True)  # half made: no project in it
            try:
                tmp.replace(folder)
            except OSError:
                shutil.rmtree(tmp, ignore_errors=True)  # another server made it meanwhile
        self.tag, self.project, self._stamp = tag, project, stamp
        self._prune()
        return project

    def _prune(self):
        try:
            old = sorted((p for p in self.root.iterdir() if p.is_dir() and p.name != self.tag),
                         key=lambda p: p.stat().st_mtime)
            for p in old[:-(KEEP - 1) or None]:
                shutil.rmtree(p, ignore_errors=True)  # Altium may hold a running one's files
        except OSError:
            pass

    def start_command(self, altium_exe: str) -> str:
        return (f'"{altium_exe}" -RScriptingSystem:RunScript(ProjectName="{self.project}"^|'
                f'ProcName="{UNIT}>StartResident")')

    def clear(self, tag: Optional[str] = None):
        """No take or stop file left for a resident of tag."""
        for f in (self.take_file(tag), self.stop_file(tag)):
            try:
                f.unlink()
            except OSError:
                pass

    def write_take(self):
        self.take_file().write_text("take")

    def reclaim(self) -> bool:
        """True when the take file was still there (now removed): the
        resident never claimed the request. False: it claimed it."""
        try:
            self.take_file().unlink()
            return True
        except FileNotFoundError:
            return False

    def taken(self) -> bool:
        return not self.take_file().exists()

    def stop_others(self, found: List[Window], wait: float = 3.0) -> List[str]:
        """Tell the residents of other builds to close; the tags told."""
        told = []
        for w in found:
            if w.tag != self.tag and w.tag not in told:
                try:
                    self.folder(w.tag).mkdir(parents=True, exist_ok=True)
                    self.stop_file(w.tag).write_text("stop")
                    told.append(w.tag)
                except OSError:
                    pass
        end = time.monotonic() + wait
        while told and time.monotonic() < end:
            if not any(w.tag in told and w.beat is not None for w in windows()):
                break
            time.sleep(0.1)
        return told
