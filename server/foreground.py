"""Keep the foreground where it was while a command runs in Altium (A22).

Altium activates its main window whenever it takes a script command line
(-RScriptingSystem:RunScriptFile or RunScript), even for a script that does
nothing; a bare X2.EXE launch does not. Every call of the server is such a
command line, so without this Altium came to the front at every call, over
whatever the user had open, and the keys they typed then went to Altium and
were read as its commands.

Nothing found keeps Altium from activating itself: the launch shown without
activation (SW_SHOWNOACTIVATE, SW_SHOWMINNOACTIVE) and LockSetForegroundWindow
from this background process changed nothing (2026-11-14). So the guard
listens for foreground changes while a call runs (a WinEvent hook, told of
each change as it happens) and gives the foreground back to the window that
had it the moment an Altium window takes it.
"""
import ctypes
import logging
import threading
import time
from ctypes import wintypes
from typing import Callable, Optional

logger = logging.getLogger("AltiumMCPServer")

ALTIUM_EXE = "x2.exe"
EVENT_SYSTEM_FOREGROUND = 0x0003
WINEVENT_OUTOFCONTEXT = 0x0000
WM_QUIT = 0x0012

WINEVENTPROC = ctypes.WINFUNCTYPE(None, wintypes.HANDLE, wintypes.DWORD, wintypes.HWND,
                                  wintypes.LONG, wintypes.LONG, wintypes.DWORD, wintypes.DWORD)


def step(previous: Optional[int], current: int, is_altium: Callable[[int], bool]):
    """One foreground change: (the window to keep, whether to give it back now).

    previous None: Altium or no window was in front when the call began, so
    Altium in front is where the user is, and nothing is done. A window of
    another program coming to the front is the user's move, and becomes the
    one kept."""
    if previous is None or not current or current == previous:
        return previous, False
    if is_altium(current):
        return previous, True
    return current, False


def is_altium_window(hwnd: int) -> bool:
    import sandbox
    return sandbox._process_name(hwnd).lower() == ALTIUM_EXE


class ForegroundEvents:
    """Calls on_change(hwnd, time) from a thread of its own each time the
    foreground window changes, while open."""

    def __init__(self, on_change: Callable[[int, float], None]):
        self._on_change = on_change
        self._ready = threading.Event()
        self._thread_id = 0
        self._thread: Optional[threading.Thread] = None
        self.hooked = False

    def _run(self):
        user32 = ctypes.windll.user32
        self._thread_id = ctypes.windll.kernel32.GetCurrentThreadId()

        def on_event(hook, event, hwnd, obj, child, thread, ms):
            try:
                self._on_change(hwnd or 0, time.perf_counter())
            except Exception as e:
                logger.debug(f"foreground event: {e}")

        proc = WINEVENTPROC(on_event)
        user32.SetWinEventHook.restype = wintypes.HANDLE
        hook = user32.SetWinEventHook(EVENT_SYSTEM_FOREGROUND, EVENT_SYSTEM_FOREGROUND, None,
                                      proc, 0, 0, WINEVENT_OUTOFCONTEXT)
        self.hooked = bool(hook)
        msg = wintypes.MSG()
        user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 0)  # the thread's queue exists now
        self._ready.set()
        try:
            if hook:
                while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            if hook:
                user32.UnhookWinEvent(wintypes.HANDLE(hook))

    def __enter__(self):
        self._thread = threading.Thread(target=self._run, name="foreground-events", daemon=True)
        self._thread.start()
        self._ready.wait(5)
        return self

    def __exit__(self, *exc):
        if self._thread is not None:
            if self.hooked:
                ctypes.windll.user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
            self._thread.join(5)
        return False


class ForegroundGuard:
    """While open, gives the foreground back to the window that had it at the
    start whenever a window of Altium takes it. Does nothing when Altium was
    in front at the start (the user is working in it).

        with ForegroundGuard(give_back):
            ... launch the script, wait for its response ...
    """

    def __init__(self, give_back: Callable[[int], None],
                 is_altium: Callable[[int], bool] = is_altium_window):
        self._give_back = give_back
        self._is_altium = is_altium
        self._events: Optional[ForegroundEvents] = None
        self._lock = threading.Lock()
        self.kept: Optional[int] = None
        self.given_back = 0

    def _foreground(self) -> int:
        return ctypes.windll.user32.GetForegroundWindow() or 0

    def _seen(self, current: int, _when: float = 0.0):
        with self._lock:
            self.kept, back = step(self.kept, current, self._is_altium)
            if back and ctypes.windll.user32.IsWindow(self.kept):
                try:
                    self._give_back(self.kept)
                    self.given_back += 1
                except Exception as e:
                    logger.debug(f"could not give the foreground back: {e}")

    def __enter__(self):
        try:
            front = self._foreground()
            self.kept = front if front and not self._is_altium(front) else None
        except Exception as e:
            logger.debug(f"foreground not read: {e}")
            self.kept = None
        if self.kept is not None:
            self._events = ForegroundEvents(self._seen).__enter__()
        return self

    def __exit__(self, *exc):
        if self._events is not None:
            self._events.__exit__(None, None, None)
            # Once more: a change just before the hook went away
            self._seen(self._foreground())
            if self.given_back:
                logger.info(f"gave the foreground back from Altium {self.given_back} time(s)")
        return False
