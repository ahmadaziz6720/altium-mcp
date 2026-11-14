"""python ui.py <label> [seconds]: how fast Altium's UI thread answers a
window message (WM_NULL round trip every 20 ms), and X2.EXE's CPU time, over
the given time: with the resident alive and without."""
import ctypes
import sys
import time
from ctypes import wintypes

import probe_lib as P

secs = float(sys.argv[2]) if len(sys.argv) > 2 else 15
u, k = ctypes.windll.user32, ctypes.windll.kernel32
hwnd = u.FindWindowW("TApplication", None)
main = None
proto = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def top(h, _):
    global main
    c = ctypes.create_unicode_buffer(64)
    u.GetClassNameW(h, c, 64)
    if c.value == "TDocumentForm" and u.IsWindowVisible(h) and P.sandbox._process_name(h).lower() == "x2.exe":
        main = h
        return False
    return True


u.EnumWindows(proto(top), 0)


def cpu():
    h = k.OpenProcess(0x1000, False, P.x2_pid())
    c, e, kt, ut = (wintypes.FILETIME() for _ in range(4))
    k.GetProcessTimes(h, ctypes.byref(c), ctypes.byref(e), ctypes.byref(kt), ctypes.byref(ut))
    k.CloseHandle(h)
    f = lambda t: (t.dwHighDateTime << 32 | t.dwLowDateTime) / 1e7
    return f(kt) + f(ut)


c0, t0, lat = cpu(), time.perf_counter(), []
res = ctypes.c_size_t()
while time.perf_counter() - t0 < secs:
    a = time.perf_counter()
    u.SendMessageTimeoutW(main, 0, 0, 0, 0x0002, 5000, ctypes.byref(res))
    lat.append(time.perf_counter() - a)
    time.sleep(0.02)
c1, t1 = cpu(), time.perf_counter()
lat.sort()
print(f"{sys.argv[1]}: {len(lat)} pings, median {lat[len(lat)//2]*1000:.2f} ms, "
      f"p99 {lat[int(len(lat)*0.99)]*1000:.2f} ms, max {lat[-1]*1000:.2f} ms; "
      f"X2 CPU {100*(c1-c0)/(t1-t0):.2f} % of one core")
