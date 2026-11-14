"""Live tests: how a call meets Altium's windows (A22: the foreground; A24:
Altium's messages).

With Altium Designer open, from server/:

    set ALTIUM_LIVE=1
    python -m unittest tests.test_live_windows -v

Nothing may be typed on the machine while they run: the test window must
keep the foreground for the test to mean anything.
"""
import asyncio
import ctypes
import json
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

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


# A script in place of the bridge's: it takes the request as the bridge
# does, puts up an Altium message, and answers once the message is closed
MESSAGE_SCRIPT = """procedure Run;
var
    Reply : TStringList;
    Answer : Integer;
begin
    DeleteFile('{request}');
    Answer := MessageDlg('altium-mcp A24 live test: {what}', {kind}, {buttons}, 0);
    Reply := TStringList.Create;
    Reply.Text := '{{"success": true, "result": "answered ' + IntToStr(Answer) + '"}}';
    Reply.SaveToFile('{response}');
    Reply.Free;
end;
"""


@unittest.skipUnless(LIVE, SKIP_REASON)
class MessageTest(unittest.TestCase):
    """A24: a message Altium puts up during a call that no driver of the
    tool knows ends the call, named, instead of holding it until the
    bridge's limit."""

    LIMIT = 40      # the call's timeout without progress, as a tool's
    QUICK = 20      # the call must end well before it

    def setUp(self):
        check_scripts_are_this_checkouts()
        if sandbox.altium_dialogs():
            self.skipTest("Altium shows a dialog already: "
                          + ", ".join(repr(d.title) for d in sandbox.altium_dialogs()))
        self.folder = Path(tempfile.mkdtemp(prefix="a24_"))

    def tearDown(self):
        # Whatever the outcome, leave Altium as the test found it: no message
        # of the test's open (nor the "busy" box a launch behind it raises),
        # no script of ours waiting, no stuck mark for the next call
        for _ in range(20):
            left = sandbox.altium_dialogs()
            if not left:
                break
            for d in left:
                sandbox.answer_dialog(d)
            time.sleep(0.5)
        main._sandbox().recover()
        main._clear_script_stuck()
        shutil.rmtree(self.folder, ignore_errors=True)

    def run_with_message(self, what, kind, buttons):
        script = self.folder / "message.pas"
        script.write_text(MESSAGE_SCRIPT.format(
            request=main.REQUEST_FILE, response=main.RESPONSE_FILE,
            what=what, kind=kind, buttons=buttons))
        start = time.monotonic()
        with mock.patch.object(main.script_bundle, "ensure_bundle", return_value=str(script)):
            response = asyncio.run(main.altium_bridge.execute_command(
                "a24_message_test", {}, timeout=self.LIMIT))
        return response, time.monotonic() - start

    def test_an_ok_only_message_is_closed_and_named(self):
        response, took = self.run_with_message("an OK-only message", "mtInformation", "MkSet(mbOK)")
        self.assertLess(took, self.QUICK, f"the call waited {took:.0f} s: {response}")
        self.assertFalse(response.get("success"), response)
        error = response.get("error", "")
        self.assertIn("Information", error)
        self.assertIn("OK", error)
        # Closed, so the script went on and answered
        self.assertIn("closed", error)
        self.assertEqual(response.get("reply_after_message", {}).get("result"), "answered 1",
                         response)
        self.assertTrue(response.get("altium_messages", [{}])[0].get("picture"), response)

    def test_a_message_with_choices_is_left_open_and_named(self):
        response, took = self.run_with_message("a message with choices", "mtConfirmation",
                                               "MkSet(mbYes, mbNo)")
        self.assertLess(took, self.QUICK, f"the call waited {took:.0f} s: {response}")
        self.assertFalse(response.get("success"), response)
        error = response.get("error", "")
        self.assertIn("Confirm", error)
        self.assertIn("Yes", error)
        self.assertIn("No", error)
        self.assertIn("left open", error)
        still = [d for d in sandbox.altium_dialogs() if d.title == "Confirm"]
        self.assertTrue(still, "the message with choices was closed by the call")

    def test_a_call_after_a_message_left_open_is_refused_at_once(self):
        self.run_with_message("a message with choices", "mtConfirmation", "MkSet(mbYes, mbNo)")
        start = time.monotonic()
        response = asyncio.run(main.altium_bridge.execute_command("get_pcb_layers", {}))
        took = time.monotonic() - start
        self.assertLess(took, 5, f"the next call waited {took:.0f} s: {response}")
        self.assertFalse(response.get("success"), response)
        self.assertIn("Confirm", response.get("error", ""))
        self.assertIn("not run", response.get("error", "").lower())


if __name__ == "__main__":
    unittest.main()
