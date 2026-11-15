"""Live tests of the resident bridge (A30): a call served by a script form
that stays in Altium, with no script launch.

With Altium Designer open, from server/:

    set ALTIUM_LIVE=1
    python -m unittest tests.test_live_resident -v

Nothing may be typed on the machine while they run: the foreground test
needs its window to keep the foreground.
"""
import asyncio
import ctypes
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from tests.live_altium import LIVE, SKIP_REASON, check_scripts_are_this_checkouts

if LIVE:
    import main
    import resident
    from tests import test_live_windows as windows_tests

# A call served by the resident: about 0.1 s against about 2 s by a launch
QUICK = 0.6


def call(command="get_pcb_layers"):
    t = time.monotonic()
    response = asyncio.run(main.altium_bridge.execute_command(command, {}))
    return response, time.monotonic() - t


def stop_all_residents():
    found = resident.windows()
    for w in found:
        folder = main.RESIDENT_ROOT / w.tag
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "stop").write_text("stop")
    end = time.monotonic() + 5
    while resident.windows() and time.monotonic() < end:
        time.sleep(0.1)
    for w in found:
        try:
            (main.RESIDENT_ROOT / w.tag / "stop").unlink()
        except OSError:
            pass


class _Case(unittest.TestCase):
    def setUp(self):
        check_scripts_are_this_checkouts()
        self.launches = 0
        real = main.altium_bridge.run_altium_script

        async def counting():
            self.launches += 1
            return await real()

        p = mock.patch.object(main.altium_bridge, "run_altium_script", counting)
        p.start()
        self.addCleanup(p.stop)
        main.altium_bridge._resident_failures = 0

    def reached(self, response):
        self.assertNotIn("did not start the command", str(response.get("error", "")),
                         f"the call never reached Altium: {response}")
        self.assertIn("request_id", response, response)


@unittest.skipUnless(LIVE, SKIP_REASON)
class ResidentTest(_Case):

    def test_calls_after_the_first_are_served_with_no_launch(self):
        stop_all_residents()
        response, _ = call()
        self.reached(response)
        self.assertEqual(main.altium_bridge.last_route["mode"], "start", main.altium_bridge.last_route)
        took = []
        for _ in range(5):
            response, dt = call()
            self.reached(response)
            self.assertEqual(main.altium_bridge.last_route["mode"], "resident",
                             main.altium_bridge.last_route)
            took.append(dt)
        self.assertEqual(self.launches, 0, "a call launched the bridge script")
        self.assertLess(sorted(took)[2], QUICK, f"calls took {took}")

    def test_the_resident_is_off_the_taskbar(self):
        call()
        ours = [w for w in resident.windows() if w.tag == main.altium_bridge.resident.tag]
        self.assertTrue(ours, "no resident of this build")
        for w in ours:
            ex = ctypes.windll.user32.GetWindowLongW(w.hwnd, resident.GWL_EXSTYLE)
            self.assertFalse(ex & resident.WS_EX_APPWINDOW, f"exstyle {ex:#x}: a taskbar button")
            self.assertTrue(ex & resident.WS_EX_TOOLWINDOW, f"exstyle {ex:#x}: listed in Alt+Tab")

    def test_a_request_not_claimed_goes_by_a_launch(self):
        call()
        # The resident never sees this take file, as when it is held up
        elsewhere = Path(tempfile.mkdtemp(prefix="a30_")) / "take"
        self.addCleanup(shutil.rmtree, elsewhere.parent, True)
        with mock.patch.object(main.altium_bridge.resident, "take_file", lambda tag=None: elsewhere):
            response, _ = call()
        self.reached(response)
        self.assertEqual(self.launches, 1)
        self.assertIn("fallback", main.altium_bridge.last_route)
        response, dt = call()
        self.reached(response)
        self.assertEqual(main.altium_bridge.last_route["mode"], "resident", "the resident is still there")

    def test_a_resident_of_another_build_is_replaced(self):
        call()
        old = main.altium_bridge.resident.tag
        # Another build: the same units and one routine more (a blank line
        # would not do: the bundle the resident runs drops it)
        src = Path(main.altium_bridge.config.script_path).parent
        copy = Path(tempfile.mkdtemp(prefix="a30_build_")) / "AltiumScript"
        self.addCleanup(shutil.rmtree, copy.parent, True)
        shutil.copytree(src, copy, ignore=shutil.ignore_patterns("Resident"))
        with open(copy / "Altium_API.pas", "a", encoding="latin-1") as f:
            f.write("\r\nprocedure A30OtherBuild;\r\nbegin\r\nend;\r\n")
        with mock.patch.object(main.altium_bridge.config, "script_path", str(copy / "Altium_API.PrjScr")):
            response, _ = call()
            self.reached(response)
            new = main.altium_bridge.resident.tag
            self.assertNotEqual(new, old)
            self.assertEqual(main.altium_bridge.last_route["mode"], "start")
            tags = [w.tag for w in resident.windows()]
            self.assertIn(new, tags)
            self.assertNotIn(old, tags, "the other build's resident was not closed")
        stop_all_residents()
        response, _ = call()
        self.reached(response)
        self.assertEqual(main.altium_bridge.resident.tag, old)


@unittest.skipUnless(LIVE, SKIP_REASON)
class ResidentForegroundTest(windows_tests.ForegroundTest if LIVE else unittest.TestCase):
    """A call the resident serves never brings Altium to the front, not
    even for the milliseconds A22's guard needs."""

    # test_live_windows runs these
    test_a_read_leaves_the_foreground_where_it_was = None
    test_a_sandbox_script_leaves_the_foreground_where_it_was = None

    def test_a_served_call_never_takes_the_foreground(self):
        asyncio.run(main.altium_bridge.execute_command("get_pcb_layers", {}))  # started, if need be
        main._bring_to_front(self.hwnd)
        time.sleep(0.5)
        with windows_tests._Watch() as watch:
            for _ in range(5):
                response = asyncio.run(main.altium_bridge.execute_command("get_pcb_layers", {}))
                self.assertEqual(main.altium_bridge.last_route["mode"], "resident",
                                 main.altium_bridge.last_route)
        self.assertNotIn("did not start the command", str(response.get("error", "")))
        self.assertEqual(watch.altium_times, 0, f"Altium came to the front {watch.altium_times} time(s)")
        self.assertEqual(ctypes.windll.user32.GetForegroundWindow(), self.hwnd)


if __name__ == "__main__":
    unittest.main()
