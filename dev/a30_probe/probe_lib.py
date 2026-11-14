"""Helpers for the A30 probes: launch a script file as the server does, read
X2.EXE's private bytes, list Altium's dialogs, time the foreground.

Run the probes with the server's venv python (pywin32), Altium open:
    python bridge_res.py start; python bridge_res.py calls 30; python fg.py;
    python longevity.py 240; python ui.py alive; python bridge_res.py stop
A script file Altium runs must have CRLF line ends (LF only: "Error in
declaration block"), and a FileName with a space in it, unquoted, starts a
second X2.EXE instead of reaching the running one."""
import ctypes
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

SERVER = Path(__file__).resolve().parents[2] / "server"
sys.path.insert(0, str(SERVER))
import sandbox  # noqa: E402
import foreground  # noqa: E402

HERE = Path(__file__).parent
ALTIUM = r"C:\Program Files\Altium\AD25\X2.EXE"
X = Path(r"C:\Users\Public\a30_probe")  # exchange folder of the probe (no space in it)
X.mkdir(exist_ok=True)
(X / "triv.pas").write_text((HERE / "triv.pas").read_text(), encoding="latin-1", newline="\r\n")


def launch(script: Path, proc: str = "Run") -> float:
    t = time.perf_counter()
    subprocess.Popen(f'"{ALTIUM}" -RScriptingSystem:RunScriptFile(FileName={script}^|ProcName={proc})',
                     shell=True)
    return t


def x2_pid() -> int:
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq X2.EXE", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True).stdout.strip()
    if not out or "X2.EXE" not in out:
        return 0
    return int(out.split(",")[1].strip('"'))


class PMC(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                ("PrivateUsage", ctypes.c_size_t)]


def private_bytes(pid: int = 0) -> int:
    pid = pid or x2_pid()
    k = ctypes.windll.kernel32
    h = k.OpenProcess(0x1000 | 0x0010, False, pid)
    if not h:
        return -1
    try:
        c = PMC()
        c.cb = ctypes.sizeof(c)
        ctypes.windll.psapi.GetProcessMemoryInfo(h, ctypes.byref(c), c.cb)
        return c.PrivateUsage
    finally:
        k.CloseHandle(h)


def handles(pid: int = 0):
    """(GDI, USER) objects of X2.EXE."""
    pid = pid or x2_pid()
    k = ctypes.windll.kernel32
    h = k.OpenProcess(0x1000, False, pid)
    try:
        u = ctypes.windll.user32
        return u.GetGuiResources(h, 0), u.GetGuiResources(h, 1)
    finally:
        k.CloseHandle(h)


def dialogs():
    return sandbox.altium_dialogs()


def wait_file(p: Path, timeout: float) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if p.exists():
            return True
        time.sleep(0.05)
    return p.exists()


def read(p: Path) -> str:
    for _ in range(40):
        try:
            return p.read_text(encoding="latin-1")
        except OSError:
            time.sleep(0.05)
    return ""


def clear_dialogs():
    for _ in range(10):
        d = dialogs()
        if not d:
            return
        for x in d:
            print("  answering dialog:", x.cls, repr(x.title), repr(x.text[:120]))
            sandbox.answer_dialog(x)
        time.sleep(0.5)
