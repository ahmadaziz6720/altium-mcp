"""Altium's modal messages met while a bridge command runs (A24).

A message Altium puts up during a command holds the script that raised it,
and with it the command and every call after it, until someone answers it.
No tool knew of most of them, so a call waited out the bridge's limit (up to
30 minutes) and its result, when it came, did not say why. The bridge now
reads Altium's top-level message windows while it waits:

- one a tool's own driver answers (run_drc's repour message) is left to it;
- one with a single OK or Close button is pressed, the command goes on, and
  the call fails naming it, with what the command answered after it;
- one with choices is left open for the user and the call fails at once
  naming it: no answer is safe to give for them;
- a call made while such a message is still open is not run.

Altium's own message boxes (TMessageForm) draw their text where it cannot be
read from outside, so each message is kept as a picture too.
"""
import ctypes
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from sandbox import _process_name, _window_text

# Altium's message boxes, Win32 dialogs (a MessageBox, a task dialog) and the
# form that reports an exception inside Altium
MESSAGE_CLASSES = ("TMessageForm", "#32770", "TShowException")
# How long a message stays up before the bridge acts on it: a tool's driver
# polls for its own dialogs and answers them within this time
GRACE = 1.0
# Messages pressed in one call before it is ended: one that comes back after
# each press (Altium's RCW exception form came back about 280 times) is not
# answered for ever
MAX_PRESSES = 3
SAFE_BUTTONS = ("ok", "close")
WM_CLOSE, WM_LBUTTONDOWN, WM_LBUTTONUP, MK_LBUTTON = 0x0010, 0x0201, 0x0202, 0x0001


def button_key(text: str) -> str:
    """A button's caption as compared: no accelerator mark, any case."""
    return text.replace("&", "").strip().lower()


@dataclass
class Message:
    hwnd: int
    cls: str
    title: str
    text: str = ""
    buttons: List[str] = field(default_factory=list)
    picture: Optional[str] = None

    @property
    def safe_to_press(self) -> bool:
        """A single OK or Close button: the only answer there is."""
        return len(self.buttons) == 1 and button_key(self.buttons[0]) in SAFE_BUTTONS

    def describe(self) -> str:
        shown = ", ".join(b.replace("&", "") for b in self.buttons) or "none found"
        out = f"'{self.title}' ({self.cls}, buttons: {shown})"
        if self.text:
            out += f": {self.text}"
        elif self.picture:
            out += f"; its text cannot be read from outside Altium, see the picture {self.picture}"
        return out

    def as_dict(self) -> dict:
        return {"title": self.title, "class": self.cls, "text": self.text,
                "buttons": [b.replace("&", "") for b in self.buttons], "picture": self.picture}


def _is_button(cls: str) -> bool:
    return "button" in cls.lower() or "btn" in cls.lower()


def _class_name(hwnd: int) -> str:
    buf = ctypes.create_unicode_buffer(64)
    ctypes.windll.user32.GetClassNameW(hwnd, buf, 64)
    return buf.value


def find(handled: Optional[Callable[["Message"], bool]] = None) -> List[Message]:
    """Altium's visible message windows, less the ones handled says a tool
    answers itself."""
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    proto = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    found: List[Message] = []

    def top(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        cls = _class_name(hwnd)
        if cls not in MESSAGE_CLASSES or _process_name(hwnd).lower() != "x2.exe":
            return True
        buttons, texts = [], []

        def child(h, __):
            if not user32.IsWindowVisible(h):
                return True
            c, t = _class_name(h), _window_text(h).strip()
            if _is_button(c):
                if t:
                    buttons.append(t)
            elif t and c not in ("DirectUIHWND", "CtrlNotifySink"):
                texts.append(t)
            return True

        user32.EnumChildWindows(hwnd, proto(child), 0)
        m = Message(int(hwnd), cls, _window_text(hwnd), " ".join(" ".join(texts).split()), buttons)
        if handled is None or not handled(m):
            found.append(m)
        return True

    user32.EnumWindows(proto(top), 0)
    return found


def press(m: Message) -> bool:
    """Press a message's only button (a posted click, which Altium's own
    buttons take where they ignore BM_CLICK); close it if that did not.
    True once it is gone."""
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    proto = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    target = []

    def child(h, _):
        if _is_button(_class_name(h)) and button_key(_window_text(h)) in SAFE_BUTTONS:
            target.append(h)
        return True

    user32.EnumChildWindows(m.hwnd, proto(child), 0)
    if target:
        user32.PostMessageW(target[0], WM_LBUTTONDOWN, MK_LBUTTON, 0)
        user32.PostMessageW(target[0], WM_LBUTTONUP, 0, 0)
    for attempt in range(20):
        time.sleep(0.1)
        if not (user32.IsWindow(m.hwnd) and user32.IsWindowVisible(m.hwnd)):
            return True
        if attempt == 9:
            user32.PostMessageW(m.hwnd, WM_CLOSE, 0, 0)
    return False


class Watch:
    """Which messages have been up for GRACE seconds, over the readings of
    one call; each window is acted on once."""

    def __init__(self, grace: float = GRACE):
        self.grace = grace
        self.first_seen: Dict[int, float] = {}
        self.acted: set = set()

    def due(self, found: List[Message], now: float) -> List[Message]:
        here = {m.hwnd for m in found}
        for gone in [h for h in self.first_seen if h not in here]:
            del self.first_seen[gone]
        out = []
        for m in found:
            seen = self.first_seen.setdefault(m.hwnd, now)
            if m.hwnd not in self.acted and now - seen >= self.grace:
                self.acted.add(m.hwnd)
                out.append(m)
        return out


def failure(command: str, pressed: List[Message], left: Optional[Message],
            reply: Optional[dict], mutating: bool) -> dict:
    """The call's result once a message was met: a failure that names each
    message, what was done with it, and what the command answered after."""
    parts = []
    if pressed:
        parts.append(f"Altium showed {'a message' if len(pressed) == 1 else f'{len(pressed)} messages'} "
                     f"during '{command}' that no step of the tool expects: "
                     + "; ".join(m.describe() for m in pressed)
                     + (". It was closed with its only button" if len(pressed) == 1 else
                        ". Each was closed with its only button"))
    if left is not None and left.safe_to_press:
        parts.append(f"A message came back after each press ({len(pressed)} pressed) and was left "
                     f"open: {left.describe()}. Altium may need a restart; the command waits on it")
    elif left is not None:
        parts.append(f"Altium is showing a message during '{command}' that waits for an answer: "
                     f"{left.describe()}. It was left open, as no answer is safe to give for it: "
                     f"answer it in Altium. The command waits on it and goes on once it is answered")
    if left is None:
        if reply is None:
            parts.append("The command gave no answer after it")
        else:
            said = ("reported success" if reply.get("success") else
                    f"reported failure: {reply.get('error', 'no reason given')}")
            parts.append(f"The command went on and {said} (reply_after_message)")
    if mutating:
        parts.append(f"'{command}' changes the design, so check the design before running it again")
    out = {"success": False, "error": ". ".join(parts) + ".",
           "altium_messages": [m.as_dict() for m in pressed + ([left] if left else [])]}
    if reply is not None:
        out["reply_after_message"] = reply
    return out


def refusal(command: str, open_messages: List[Message]) -> dict:
    """A call not run because Altium is showing a message that waits for an
    answer: a script launched now would only queue behind it."""
    return {"success": False,
            "error": f"Not run: '{command}' would wait behind a message Altium is showing that waits "
                     f"for an answer: " + "; ".join(m.describe() for m in open_messages)
                     + ". Answer it in Altium (it may be one the user has open), then retry.",
            "altium_messages": [m.as_dict() for m in open_messages]}
