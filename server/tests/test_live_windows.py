"""Live tests: how a call meets Altium's windows (A22: the foreground).

With Altium Designer open, from server/:

    set ALTIUM_LIVE=1
    python -m unittest tests.test_live_windows -v

Nothing may be typed on the machine while they run: the test window must
keep the foreground for the test to mean anything.
"""
import asyncio
import ctypes
import json
import subprocess
import sys
import time
import unittest

from tests.live_altium import LIVE, SKIP_REASON, check_scripts_are_this_checkouts

if LIVE:
    import foreground
    import main
    import sandbox


# How long Altium may hold the foreground per call: the guard gives it back
# within milliseconds of the switch; before it, Altium kept it for the whole
# call and after (about 0.8 s and more)
MAX_ALTIUM_FRONT = 0.05


class _Watch:
    """Times, from foreground change events, how long Altium's windows were
    in front while a call ran."""

    def __init__(self):
        self.changes = []

    def _on_change(self, hwnd, when):
        self.changes.append((when, foreground.is_altium_window(hwnd)))

    def __enter__(self):
        self._events = foreground.ForegroundEvents(self._on_change).__enter__()
        if not self._events.hooked:
            raise unittest.SkipTest("no foreground event hook")
        self.start = time.perf_counter()
        return self

    def __exit__(self, *exc):
        self.end = time.perf_counter()
        self._events.__exit__(None, None, None)

    @property
    def altium_seconds(self):
        total, since = 0.0, None
        for when, altium in self.changes:
            if altium and since is None:
                since = when
            elif not altium and since is not None:
                total, since = total + when - since, None
        if since is not None:
            total += self.end - since
        return total

    @property
    def altium_times(self):
        return sum(1 for _, altium in self.changes if altium)


@unittest.skipUnless(LIVE, SKIP_REASON)
class ForegroundTest(unittest.TestCase):
    """A22: a call must not take the foreground (and with it the keyboard)
    from the window the user is working in."""

    def setUp(self):
        check_scripts_are_this_checkouts()
        # The window in front belongs to another process, as the user's
        # program does: a process may hand the foreground to the ones it
        # starts, so a window of the test's own would not show the fault
        self.window = subprocess.Popen(
            [sys.executable, "-c",
             "import tkinter; r = tkinter.Tk(); r.title('altium-mcp A22 foreground test'); "
             "r.geometry('420x120+60+60'); r.update(); print(int(r.wm_frame(), 16), flush=True); "
             "r.mainloop()"],
            stdout=subprocess.PIPE, text=True)
        self.hwnd = int(self.window.stdout.readline())
        for _ in range(10):
            main._bring_to_front(self.hwnd)
            time.sleep(0.1)
            if ctypes.windll.user32.GetForegroundWindow() == self.hwnd:
                break
        else:
            self.window.kill()
            self.skipTest("the test window could not take the foreground")

    def tearDown(self):
        self.window.kill()
        self.window.wait()

    def check(self, watch):
        front = ctypes.windll.user32.GetForegroundWindow()
        self.assertLess(watch.altium_seconds, MAX_ALTIUM_FRONT,
                        f"Altium had the foreground for {watch.altium_seconds * 1000:.0f} ms during "
                        f"the call ({watch.altium_times} time(s)); keys typed then go to Altium")
        self.assertEqual(front, self.hwnd,
                         f"after the call the foreground is {sandbox._window_text(front)!r} "
                         f"of {sandbox._process_name(front)}, not the test window")

    def test_a_read_leaves_the_foreground_where_it_was(self):
        with _Watch() as watch:
            response = asyncio.run(main.altium_bridge.execute_command("get_pcb_layers", {}))
        self.assertNotIn("did not start the command", str(response.get("error", "")),
                         f"the call never reached Altium: {response}")
        self.check(watch)

    def test_a_sandbox_script_leaves_the_foreground_where_it_was(self):
        with _Watch() as watch:
            out = json.loads(asyncio.run(main.run_altium_script(None, "ResultText := 'ok';", 60)))
        self.assertTrue(out.get("success"), out)
        self.check(watch)


if __name__ == "__main__":
    unittest.main()
