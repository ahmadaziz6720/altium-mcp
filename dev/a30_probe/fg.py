"""Q6: with a window of another process in front (as ForegroundTest does),
how long Altium holds the foreground during calls served by the resident
bridge, against launches of a trivial script file (no guard here)."""
import ctypes
import subprocess
import sys
import time

import win32api
import win32gui
import win32process

import probe_lib as P
import bridge_res
from probe_lib import foreground


def bring_to_front(hwnd):
    this_thread = win32api.GetCurrentThreadId()
    front = win32gui.GetForegroundWindow()
    front_thread = win32process.GetWindowThreadProcessId(front)[0] if front else 0
    attached = False
    try:
        if front_thread and front_thread != this_thread:
            win32process.AttachThreadInput(this_thread, front_thread, True)
            attached = True
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            pass
        win32gui.BringWindowToTop(hwnd)
    finally:
        if attached:
            win32process.AttachThreadInput(this_thread, front_thread, False)


class Watch:
    def __init__(self):
        self.changes = []

    def __enter__(self):
        self.ev = foreground.ForegroundEvents(
            lambda h, when: self.changes.append((when, foreground.is_altium_window(h)))).__enter__()
        self.start = time.perf_counter()
        return self

    def __exit__(self, *a):
        self.end = time.perf_counter()
        self.ev.__exit__(None, None, None)

    def altium(self):
        total, since, times = 0.0, None, 0
        for when, alt in self.changes:
            if alt and since is None:
                since, times = when, times + 1
            elif not alt and since is not None:
                total, since = total + when - since, None
        if since is not None:
            total += self.end - since
        return total, times


win = subprocess.Popen([sys.executable, "-c",
                        "import tkinter; r = tkinter.Tk(); r.title('a30 foreground probe'); "
                        "r.geometry('420x120+60+60'); r.update(); print(int(r.wm_frame(), 16), flush=True); "
                        "r.mainloop()"], stdout=subprocess.PIPE, text=True)
hwnd = int(win.stdout.readline())
try:
    for _ in range(10):
        bring_to_front(hwnd)
        time.sleep(0.1)
        if ctypes.windll.user32.GetForegroundWindow() == hwnd:
            break
    print("test window in front:", ctypes.windll.user32.GetForegroundWindow() == hwnd)
    with Watch() as w:
        for i in range(10):
            dt, s = bridge_res.call()
            assert dt is not None, "resident call timed out"
    total, times = w.altium()
    front = ctypes.windll.user32.GetForegroundWindow()
    print(f"10 resident calls: Altium in front {total*1000:.0f} ms, {times} time(s); "
          f"front after: {'test window' if front == hwnd else P.sandbox._window_text(front)}")
    for i in range(10):
        bring_to_front(hwnd)
        time.sleep(0.1)
        if ctypes.windll.user32.GetForegroundWindow() == hwnd:
            break
    script = P.X / "triv.pas"
    out = P.X / "triv.txt"
    with Watch() as w:
        for i in range(3):
            out.unlink(missing_ok=True)
            P.launch(script)
            P.wait_file(out, 20)
            front = ctypes.windll.user32.GetForegroundWindow()
            if front != hwnd:
                bring_to_front(hwnd)
                time.sleep(0.2)
    total, times = w.altium()
    print(f"3 script launches (no guard): Altium in front {total*1000:.0f} ms, {times} time(s)")
finally:
    win.kill()
