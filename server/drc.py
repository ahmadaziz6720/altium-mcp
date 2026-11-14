"""Running Altium's design rule check from the MCP server.

PCB:DesignRuleCheck opens the modal "Design Rule Checker" dialog and waits
for someone to press "Run Design Rule Check...". No script call runs the
check without it (IPCB_Board.RunBatchDesignRuleCheck exists but fails for
every argument list), so while the bridge command waits, drive_dialog
presses that button from outside Altium. Altium's TXPBitBtn ignores
BM_CLICK; posted mouse messages addressed to the button work.

Cancelling the dialog leaves no violations, exactly like a board that passes.
So a result only counts as a check that ran when the button was pressed and
the dialog closed, and the report Altium writes is read to confirm it.

When copper under a polygon pour has changed since it was poured, Altium
answers the Run press with a "Design Rule Check" message (Run DRC, Cancel,
Repour Polygons and Run DRC) and the check waits on it. drive_dialog presses
Run DRC: the board is checked as it is, its pours not changed, and the
outcome says the message was met.
"""
import asyncio
import ctypes
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple

from sandbox import _process_name, _window_text

DIALOG_CLASS = "TDesignRuleCheckForm"
RUN_BUTTON = "run design rule check"
WM_CLOSE, WM_LBUTTONDOWN, WM_LBUTTONUP, MK_LBUTTON = 0x0010, 0x0201, 0x0202, 0x0001
# Altium's message when the pours need repouring, and its buttons
REPOUR_CLASS = "TMessageForm"
REPOUR_TITLE = "Design Rule Check"
REPOUR_RUN = "run drc"
REPOUR_REPOUR = "repour polygons and run drc"
REPOUR_CANCEL = "cancel"


def button_key(text: str) -> str:
    """A button's caption as compared: no accelerator mark, any case."""
    return text.replace("&", "").strip().lower()


def is_repour_prompt(cls: str, title: str, buttons) -> bool:
    """Whether a window is Altium's repour message, by its class, its title
    and its buttons' captions (Run DRC and Repour Polygons and Run DRC),
    never by the position of a button."""
    keys = {button_key(b) for b in buttons}
    return (cls == REPOUR_CLASS and title.strip() == REPOUR_TITLE
            and REPOUR_RUN in keys and REPOUR_REPOUR in keys)


def find_dialog() -> Optional[int]:
    """The visible Design Rule Checker dialog of X2.EXE, if one is open."""
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    found = []
    proto = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def top(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            cls = ctypes.create_unicode_buffer(64)
            user32.GetClassNameW(hwnd, cls, 64)
            if cls.value == DIALOG_CLASS and _process_name(hwnd).lower() == "x2.exe":
                found.append(hwnd)
        return True

    user32.EnumWindows(proto(top), 0)
    return found[0] if found else None


def _run_button(dialog: int) -> Optional[int]:
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    found = []
    proto = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def child(hwnd, _):
        if RUN_BUTTON in _window_text(hwnd).replace("&", "").lower():
            found.append(hwnd)
        return True

    user32.EnumChildWindows(dialog, proto(child), 0)
    return found[0] if found else None


def _class_name(hwnd: int) -> str:
    cls = ctypes.create_unicode_buffer(64)
    ctypes.windll.user32.GetClassNameW(hwnd, cls, 64)
    return cls.value


def find_repour_prompt() -> Optional[Tuple[int, Dict[str, int]]]:
    """Altium's repour message, if one is up: its window and its buttons by
    caption (button_key)."""
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    found = []
    proto = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def top(hwnd, _):
        if (user32.IsWindowVisible(hwnd) and _class_name(hwnd) == REPOUR_CLASS
                and _window_text(hwnd).strip() == REPOUR_TITLE
                and _process_name(hwnd).lower() == "x2.exe"):
            buttons = {}

            def child(c, _):
                buttons.setdefault(button_key(_window_text(c)), c)
                return True
            user32.EnumChildWindows(hwnd, proto(child), 0)
            if is_repour_prompt(REPOUR_CLASS, REPOUR_TITLE, buttons):
                found.append((hwnd, buttons))
        return True

    user32.EnumWindows(proto(top), 0)
    return found[0] if found else None


def _press(button: int) -> None:
    """Altium's TXPBitBtn ignores BM_CLICK: post a mouse click to it."""
    user32 = ctypes.windll.user32
    user32.PostMessageW(button, WM_LBUTTONDOWN, MK_LBUTTON, 0)
    user32.PostMessageW(button, WM_LBUTTONUP, 0, 0)


def _is_open(hwnd: int) -> bool:
    user32 = ctypes.windll.user32
    return bool(user32.IsWindow(hwnd) and user32.IsWindowVisible(hwnd))


@dataclass
class DialogOutcome:
    pressed: bool = False      # the Run button was pressed and the dialog closed
    cancelled: bool = False    # the dialog would not run and was closed (no check)
    seen: bool = False
    posted: bool = False       # a press of the Run button was sent
    repour_prompt: bool = False     # Altium's repour message was met, Run DRC pressed
    repour_cancelled: bool = False  # it would not take Run DRC and was cancelled (no check)
    notes: List[str] = field(default_factory=list)

    def ran_after_reply(self) -> bool:
        """Whether the check ran, once Altium has replied. The dialog is
        modal, so a reply means it closed. A small board is checked and
        answered within the quarter second the driver waits after a press
        before looking: the driver is then stopped with the press sent and
        the close unseen. A press sent and no close of ours means the press
        closed it. A repour message that was cancelled means no check."""
        if self.repour_cancelled:
            return False
        return self.pressed or (self.posted and not self.cancelled)


@dataclass
class _RepourAnswer:
    window: Optional[int] = None
    presses: int = 0
    last: float = 0.0


def _answer_repour_prompt(outcome: DialogOutcome, state: _RepourAnswer, attempts: int,
                          press_wait: float) -> bool:
    """Press Run DRC on Altium's repour message when it is up; True if it
    is. A message that does not take the press is cancelled after
    `attempts` presses, `press_wait` seconds apart, so Altium is never left
    blocked."""
    prompt = find_repour_prompt()
    if prompt is None:
        return False
    window, buttons = prompt
    if window != state.window:
        state.window, state.presses, state.last = window, 0, 0.0
    now = time.monotonic()
    if state.presses and now - state.last < press_wait:
        return True
    if state.presses < attempts:
        _press(buttons[REPOUR_RUN])
        state.presses += 1
        state.last = now
        outcome.repour_prompt = True
        if state.presses > 1:
            outcome.notes.append(f"repour message: Run DRC press {state.presses - 1} did not close it")
    elif not outcome.repour_cancelled:
        if REPOUR_CANCEL in buttons:
            _press(buttons[REPOUR_CANCEL])
        else:
            ctypes.windll.user32.PostMessageW(window, WM_CLOSE, 0, 0)
        outcome.repour_cancelled = True
        outcome.notes.append(f"the repour message did not take Run DRC after {attempts} presses "
                             "and was cancelled")
    return True


async def drive_dialog(outcome: DialogOutcome, progress_file: Path, keep_alive: float = 5.0,
                       settle: float = 0.6, attempts: int = 3, press_wait: float = 5.0,
                       before_press: Optional[Callable[[], None]] = None, poll: float = 0.25,
                       repour_wait: float = 2.0) -> None:
    """Press Run in the Design Rule Checker dialog when it opens, then keep the
    bridge's progress file fresh while the check runs, so a long check is not
    taken for a hung command, and press Run DRC on Altium's repour message
    when it comes. before_press is called once the dialog is up, before the
    check runs and writes its report. Runs until cancelled by the caller."""
    user32 = ctypes.windll.user32
    repour = _RepourAnswer()
    while not outcome.pressed and not outcome.cancelled:
        dialog = find_dialog()
        if dialog is None:
            await asyncio.sleep(0.2)
            continue
        if not outcome.seen and before_press is not None:
            try:
                before_press()
            except Exception as e:   # never keep the check from running
                outcome.notes.append(f"before the check: {e}")
        outcome.seen = True
        await asyncio.sleep(settle)   # the buttons answer only once the form is up
        for n in range(attempts):
            button = _run_button(dialog)
            if button is None:
                outcome.notes.append("the dialog has no Run Design Rule Check button")
                break
            _press(button)
            outcome.posted = True
            for _ in range(max(1, int(press_wait / 0.25))):
                await asyncio.sleep(0.25)
                # The repour message is Altium's answer to the press: the
                # check goes on once it is answered (below)
                if not _is_open(dialog) or find_repour_prompt() is not None:
                    outcome.pressed = True
                    break
            if outcome.pressed:
                break
            outcome.notes.append(f"press {n + 1} did not close the dialog")
        if not outcome.pressed:
            # Never leave Altium blocked behind a modal dialog
            user32.PostMessageW(dialog, WM_CLOSE, 0, 0)
            outcome.cancelled = True
    touched = None
    while True:
        try:
            _answer_repour_prompt(outcome, repour, attempts, repour_wait)
        except Exception as e:   # never stop keeping the command alive
            outcome.notes.append(f"repour message: {e}")
        now = time.monotonic()
        if touched is None or now - touched >= keep_alive:
            try:
                progress_file.touch()
            except OSError:
                pass
            touched = now
        await asyncio.sleep(poll)


_RULE_RE = re.compile(r"^Processing Rule : (.*)$")
_COUNT_RE = re.compile(r"^Rule Violations :\s*(\d+)")
_TOTAL_RE = re.compile(r"^Violations Detected :\s*(\d+)")
_WAIVED_RE = re.compile(r"^Waived Violations :\s*(\d+)")
# "ERROR : More than 500 violations detected, DRC was stopped"
_ERROR_RE = re.compile(r"^ERROR\s*:\s*(.*)$")


# What a violation's descriptor says about by how much, as Altium writes it:
#   "Clearance Constraint: (0.659mm < 1.27mm) Between Via ... And Via ..."
#   "Width Constraint: Track ... Actual Width = 0.15mm, Target Width = 0.254mm"
_NUM = r"(-?\d+(?:\.\d+)?)\s*(mm|mil|um)"
_PAIR = re.compile(r"\(\s*" + _NUM + r"\s*([<>]=?)\s*" + _NUM + r"\s*\)")
_ACTUAL = re.compile(r"Actual [\w ]*?=\s*" + _NUM + r",\s*Target [\w ]*?=\s*" + _NUM)
_TO_MILS = {"mm": 1 / 0.0254, "mil": 1.0, "um": 0.001 / 0.0254}
# How many violations a filtered run_drc fetches from Altium before filtering
FILTER_FETCH = 5000


def _kind(descriptor: str) -> str:
    # the rule kind leads the descriptor, up to its values or its colon:
    # "Board Outline Clearance(Outline Edge): (Collision < 25mil) ..."
    return re.split(r"[(:]", descriptor, 1)[0].strip()


def rule_key(text: str) -> str:
    """A rule name or kind as compared by the rules filter: any case, without
    spaces, punctuation or a trailing "Constraint", so "Un-Routed Net",
    "UnRoutedNet" and "Un-Routed Net Constraint" are the same."""
    key = re.sub(r"[^0-9a-z]", "", text.lower())
    return key[:-len("constraint")] if key.endswith("constraint") else key


def measurement(descriptor: str) -> dict:
    """The measured and allowed values in a violation's descriptor, in mils:
    {"kind", "actual_mils", "limit_mils", "comparison"}; only "kind" when the
    descriptor gives no numbers."""
    out = {"kind": _kind(descriptor)} if ":" in descriptor else {}
    m = _PAIR.search(descriptor)
    if m:
        out.update(actual_mils=round(float(m.group(1)) * _TO_MILS[m.group(2)], 3),
                   limit_mils=round(float(m.group(4)) * _TO_MILS[m.group(5)], 3),
                   comparison=m.group(3))
        return out
    m = _ACTUAL.search(descriptor)
    if m:
        actual = round(float(m.group(1)) * _TO_MILS[m.group(2)], 3)
        limit = round(float(m.group(3)) * _TO_MILS[m.group(4)], 3)
        out.update(actual_mils=actual, limit_mils=limit, comparison="<" if actual < limit else ">")
    return out


def _points(v: dict):
    yield v.get("x_mils"), v.get("y_mils")
    for key in ("primitive1", "primitive2"):
        p = v.get(key) or {}
        yield p.get("x_mils"), p.get("y_mils")


def matches(v: dict, rules=(), nets=(), area=None) -> bool:
    """Whether a violation passes the filters: its rule's name or kind is one
    of rules (as rule_key compares them), a primitive is on one of nets, its
    location is inside area ([x1, y1, x2, y2] in mils from the board origin).
    Whole names, not substrings: "Clearance" is the electrical clearance
    rules, not Hole To Hole Clearance or Silk to Silk (Clearance=0mm)."""
    if rules:
        kind = v.get("kind") or _kind(v.get("description", ""))
        have = {rule_key(v.get("rule", "")), rule_key(kind)} - {""}
        if not have & {rule_key(r) for r in rules}:
            return False
    if nets:
        on = {(v.get(k) or {}).get("net", "").lower() for k in ("primitive1", "primitive2")}
        if not on & {n.lower() for n in nets}:
            return False
    if area is not None:
        x1, x2 = sorted((area[0], area[2]))
        y1, y2 = sorted((area[1], area[3]))
        if not any(x is not None and x1 <= x <= x2 and y1 <= y <= y2 for x, y in _points(v)):
            return False
    return True


def parse_report(text: str) -> dict:
    """Per-rule violation counts and totals from a .drc report, its errors,
    and whether Altium stopped the check at its violation limit."""
    rules, current, errors = [], None, []
    total = waived = None
    for line in text.splitlines():
        line = line.strip()
        m = _ERROR_RE.match(line)
        if m:
            errors.append(m.group(1).strip())
            continue
        m = _RULE_RE.match(line)
        if m:
            current = m.group(1).strip()
            continue
        m = _COUNT_RE.match(line)
        if m and current is not None:
            rules.append({"rule": current, "violations": int(m.group(1))})
            current = None
            continue
        m = _TOTAL_RE.match(line)
        if m:
            total = int(m.group(1))
        m = _WAIVED_RE.match(line)
        if m:
            waived = int(m.group(1))
    return {"violations": total, "waived": waived, "rules": rules, "errors": errors,
            "stopped": any("stopped" in e.lower() for e in errors)}


def narrow_report(report: dict, rules, violations=()) -> dict:
    """The parsed report cut to the rules a `rules` filter asks for, by the
    same match the violations get (matches): a report entry names its rule
    by kind and settings ("Clearance Constraint (Gap=0.15mm) (All),(All)"),
    not by the rule's own name, so an entry is kept when its kind is one of
    rules; a rule's own name in rules keeps the kinds of the violations
    (the ones given) that name picked. "rules_omitted" counts the entries
    left out; the totals stay the whole check's."""
    if not rules:
        return report
    kinds = {rule_key(r) for r in rules}
    for v in violations:
        if matches(v, rules):
            kinds.add(rule_key(v.get("kind") or _kind(v.get("description", ""))))
    kept = [r for r in report.get("rules", []) if rule_key(_kind(r["rule"])) in kinds]
    return {**report, "rules": kept, "rules_omitted": len(report.get("rules", [])) - len(kept)}


REPORT_SUFFIXES = (".drc", ".html")


def report_names(board_stem: str) -> List[str]:
    """The files Altium's check writes for a board: its report and the
    report's page."""
    return [f"Design Rule Check - {board_stem}{suffix}" for suffix in REPORT_SUFFIXES]


def _report_folders(root: Path):
    """The folders a board's report is looked for in: the board's own, the
    folders in it (the project's output folder) and the folders in those."""
    yield root
    try:
        level1 = [p for p in root.iterdir() if p.is_dir()]
    except OSError:
        return
    for folder in level1:
        yield folder
    for folder in level1:
        try:
            yield from (p for p in folder.iterdir() if p.is_dir())
        except OSError:
            pass


def find_report(board_path: str, since: float) -> Optional[Path]:
    """The .drc report written for this board after `since`. Altium writes it
    beside the board, or into the project's output folder."""
    board = Path(board_path)
    if not board.parent.is_dir():
        return None
    candidates = []
    name = report_names(board.stem)[0]
    for folder in _report_folders(board.parent):
        p = folder / name
        try:
            if p.stat().st_mtime >= since - 2:
                candidates.append(p)
        except OSError:
            pass
    return max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None


def _key(path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


@dataclass
class ReportSnapshot:
    """What a board's folder held, where its report goes, before a check."""
    board: str
    root: Path
    folders: Set[str]                               # _key of each folder there
    files: Dict[str, Tuple[bytes, int, int]]        # an earlier report: bytes, atime_ns, mtime_ns


def snapshot_reports(board_path: str) -> Optional[ReportSnapshot]:
    """The folders a check may write the board's report into and the report
    files already there, so remove_report can leave them as they were."""
    root = Path(board_path).parent
    if not root.is_dir():
        return None
    folders, files = set(), {}
    for folder in _report_folders(root):
        folders.add(_key(folder))
        for name in report_names(Path(board_path).stem):
            p = folder / name
            try:
                st = p.stat()
                files[_key(p)] = (p.read_bytes(), st.st_atime_ns, st.st_mtime_ns)
            except OSError:
                pass
    return ReportSnapshot(board_path, root, folders, files)


def remove_report(report: Path, snap: Optional[ReportSnapshot]) -> dict:
    """Leave the folder as `snap` found it: the report this check wrote and its
    page are deleted, or, where an earlier report was, put back as it was;
    then the folders the check made for them, when empty. {"deleted": True},
    with "restored" when an earlier report was put back and "folder_left"
    when a folder the check made held something else; {"deleted": False,
    "delete_error": why} when the report stays."""
    if snap is None:
        return {"deleted": False, "delete_error": "what the folder held before the check is not known"}
    root = _key(snap.root)
    made = []
    folder = report.parent
    while _key(folder) != root:
        if folder.parent == folder:
            return {"deleted": False, "delete_error": "the report is not in the board's folder"}
        if _key(folder) not in snap.folders:
            made.append(folder)
        folder = folder.parent
    out = {"deleted": True}
    try:
        for suffix in REPORT_SUFFIXES:
            p = report.with_suffix(suffix)
            earlier = snap.files.get(_key(p))
            if earlier is not None:
                data, atime, mtime = earlier
                if not p.is_file() or p.read_bytes() != data:
                    p.write_bytes(data)
                os.utime(p, ns=(atime, mtime))
                out["restored"] = True
            elif p.exists():
                p.unlink()
    except OSError as e:
        return {"deleted": False, "delete_error": str(e)}
    for folder in made:   # the deepest first
        try:
            folder.rmdir()
        except OSError:
            out["folder_left"] = str(folder)
            break
    return out
