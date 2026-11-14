"""Unit tests for drc (pure Python, no Altium needed).

Run from server/:  python -m unittest tests.test_drc -v
"""
import asyncio
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import drc  # noqa: E402

REPORT = """Protel Design System Design Rule Check
PCB File : C:\\x\\board.PcbDoc
Date     : 01/11/2026
Time     : 11:44:49

Processing Rule : Clearance Constraint (Gap=0.15mm) (All),(All)
Rule Violations :3

Processing Rule : Width Constraint (Min=0.15mm) (Max=3mm) (Preferred=0.15mm) (All)
Rule Violations :0

Processing Rule : Hole To Hole Clearance (Gap=0.2mm) (IsMicroVia and ((StartLayer = 'Top Layer') and (StopLayer = 'Inner 1'))),(All)
Rule Violations :1


Violations Detected : 4
Waived Violations : 1
Time Elapsed        : 00:00:00
"""


class ReportTest(unittest.TestCase):
    def test_parse_report(self):
        r = drc.parse_report(REPORT)
        self.assertEqual(r["violations"], 4)
        self.assertEqual(r["waived"], 1)
        self.assertEqual([x["violations"] for x in r["rules"]], [3, 0, 1])
        self.assertEqual(r["rules"][0]["rule"], "Clearance Constraint (Gap=0.15mm) (All),(All)")
        self.assertIn("StopLayer = 'Inner 1'", r["rules"][2]["rule"])

    def test_parse_empty(self):
        self.assertEqual(drc.parse_report(""), {"violations": None, "waived": None, "rules": [],
                                                 "errors": [], "stopped": False})

    def test_report_narrowed_to_the_rules_asked_for(self):
        r = drc.parse_report(REPORT)
        self.assertEqual(drc.narrow_report(r, [])["rules"], r["rules"])    # no filter: as it is
        self.assertNotIn("rules_omitted", drc.narrow_report(r, []))
        # a kind, in any case, spacing or "Constraint": the entries of that kind
        for ask in (["Clearance"], ["clearance constraint"], ["CLEARANCE"]):
            n = drc.narrow_report(r, ask)
            self.assertEqual([x["violations"] for x in n["rules"]], [3], ask)
            self.assertEqual(n["rules_omitted"], 2)
            self.assertEqual((n["violations"], n["waived"]), (4, 1), "the totals are the check's")
        # whole kinds: Clearance is not Hole To Hole Clearance
        n = drc.narrow_report(r, ["Hole To Hole Clearance"])
        self.assertEqual([x["violations"] for x in n["rules"]], [1])
        # a rule with no violation is still a rule asked for
        self.assertEqual([x["violations"] for x in drc.narrow_report(r, ["Width"])["rules"]], [0])
        n = drc.narrow_report(r, ["Width", "Clearance"])
        self.assertEqual([x["violations"] for x in n["rules"]], [3, 0])
        # a kind the report has no entry for: no entries, all omitted
        n = drc.narrow_report(r, ["Short-Circuit"])
        self.assertEqual((n["rules"], n["rules_omitted"]), ([], 3))
        self.assertEqual(len(r["rules"]), 3, "the parsed report is not changed")

    def test_report_narrowed_by_a_rules_own_name(self):
        r = drc.parse_report(REPORT)
        gnd = {"rule": "Clearance_GND", "description": "Clearance Constraint: (0.1mm < 0.152mm) Between Via"}
        gnd.update(drc.measurement(gnd["description"]))
        # the report does not name a rule: the kind of what the name picked
        n = drc.narrow_report(r, ["clearance_gnd"], [gnd])
        self.assertEqual([x["violations"] for x in n["rules"]], [3])
        self.assertEqual(drc.narrow_report(r, ["clearance_gnd"], [])["rules"], [])

    def test_stopped_at_the_violation_limit(self):
        head, rest = REPORT.split("\n\n", 1)
        r = drc.parse_report(head + "\n\nERROR : More than 500 violations detected, DRC was stopped\n\n" + rest)
        self.assertTrue(r["stopped"])
        self.assertEqual(r["errors"], ["More than 500 violations detected, DRC was stopped"])
        self.assertEqual(len(r["rules"]), 3)
        self.assertFalse(drc.parse_report(REPORT)["stopped"])

    def test_find_report_beside_board_or_in_output_folder(self):
        with tempfile.TemporaryDirectory() as d:
            board = Path(d) / "board.PcbDoc"
            board.write_text("x")
            self.assertIsNone(drc.find_report(str(board), time.time()))
            beside = Path(d) / "Design Rule Check - board.drc"
            beside.write_text(REPORT)
            self.assertEqual(drc.find_report(str(board), time.time()), beside)
            out = Path(d) / "Project Outputs for P" / "Design Rule Check - board.drc"
            out.parent.mkdir()
            out.write_text(REPORT)
            later = time.time() + 5
            os.utime(out, (later, later))
            self.assertEqual(drc.find_report(str(board), time.time()), out)

    def test_old_report_is_not_this_run(self):
        with tempfile.TemporaryDirectory() as d:
            board = Path(d) / "board.PcbDoc"
            old = Path(d) / "Design Rule Check - board.drc"
            old.write_text(REPORT)
            past = time.time() - 3600
            os.utime(old, (past, past))
            self.assertIsNone(drc.find_report(str(board), time.time()))


class RemoveReportTest(unittest.TestCase):
    """A5: the folder is left as the check found it."""

    def tree(self, d):
        return sorted((str(p.relative_to(d)), p.read_bytes() if p.is_file() else None,
                       p.stat().st_mtime_ns if p.is_file() else None) for p in Path(d).rglob("*"))

    def write_report(self, folder):
        folder.mkdir(parents=True, exist_ok=True)
        for name in drc.report_names("board"):
            (folder / name).write_text("this check")
        return folder / drc.report_names("board")[0]

    def test_report_and_the_folder_made_for_it_go(self):
        with tempfile.TemporaryDirectory() as d:
            board = Path(d) / "board.PcbDoc"
            board.write_text("x")
            (Path(d) / "History").mkdir()
            before = self.tree(d)
            snap = drc.snapshot_reports(str(board))
            report = self.write_report(Path(d) / "Project Outputs for P")
            self.assertEqual(drc.find_report(str(board), time.time()), report)
            self.assertEqual(drc.remove_report(report, snap), {"deleted": True})
            self.assertEqual(self.tree(d), before)

    def test_beside_the_board(self):
        with tempfile.TemporaryDirectory() as d:
            board = Path(d) / "board.PcbDoc"
            board.write_text("x")
            before = self.tree(d)
            snap = drc.snapshot_reports(str(board))
            report = self.write_report(Path(d))
            self.assertEqual(drc.remove_report(report, snap), {"deleted": True})
            self.assertEqual(self.tree(d), before)

    def test_an_earlier_report_and_its_folder_stay(self):
        with tempfile.TemporaryDirectory() as d:
            board = Path(d) / "board.PcbDoc"
            board.write_text("x")
            outputs = Path(d) / "Project Outputs for P"
            outputs.mkdir()
            (outputs / "other.txt").write_text("kept")
            earlier = outputs / drc.report_names("board")[0]
            earlier.write_text("an earlier report")
            past = time.time() - 3600
            os.utime(earlier, (past, past))
            before = self.tree(d)
            snap = drc.snapshot_reports(str(board))
            report = self.write_report(outputs)
            self.assertEqual(drc.remove_report(report, snap), {"deleted": True, "restored": True})
            self.assertEqual(self.tree(d), before)

    def test_a_folder_holding_something_else_is_left(self):
        with tempfile.TemporaryDirectory() as d:
            board = Path(d) / "board.PcbDoc"
            board.write_text("x")
            snap = drc.snapshot_reports(str(board))
            outputs = Path(d) / "Project Outputs for P"
            report = self.write_report(outputs)
            (outputs / "status.txt").write_text("not the report")
            out = drc.remove_report(report, snap)
            self.assertEqual(out, {"deleted": True, "folder_left": str(outputs)})
            self.assertEqual(sorted(p.name for p in outputs.iterdir()), ["status.txt"])

    def test_nothing_goes_without_a_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            report = self.write_report(Path(d) / "Project Outputs for P")
            out = drc.remove_report(report, None)
            self.assertFalse(out["deleted"])
            self.assertIn("delete_error", out)
            self.assertTrue(report.is_file())

    def test_a_report_outside_the_boards_folder_stays(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as e:
            board = Path(d) / "board.PcbDoc"
            board.write_text("x")
            snap = drc.snapshot_reports(str(board))
            report = self.write_report(Path(e) / "out")
            self.assertFalse(drc.remove_report(report, snap)["deleted"])
            self.assertTrue(report.is_file())


class DriveDialogTest(unittest.TestCase):
    """drive_dialog with the window functions replaced: the outcome must say
    whether the check really ran."""

    def run_driver(self, open_states, button=1, before_press=None):
        states = iter(open_states)
        outcome = drc.DialogOutcome()
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(drc, "find_dialog", return_value=42), \
                mock.patch.object(drc, "_run_button", return_value=button), \
                mock.patch.object(drc, "_is_open", side_effect=lambda h: next(states, True)), \
                mock.patch.object(drc.ctypes, "windll") as windll:
            async def go():
                task = asyncio.create_task(drc.drive_dialog(outcome, Path(d) / "progress.txt", keep_alive=0.01,
                                                            settle=0, press_wait=0.5, before_press=before_press))
                for _ in range(400):
                    if outcome.pressed or outcome.cancelled:
                        break
                    await asyncio.sleep(0.01)
                await asyncio.sleep(0.05)
                task.cancel()
            asyncio.run(go())
            posted = [c.args[1] for c in windll.user32.PostMessageW.call_args_list]
        return outcome, posted

    def test_pressed_when_dialog_closes(self):
        outcome, posted = self.run_driver([True, False])
        self.assertTrue(outcome.pressed)
        self.assertFalse(outcome.cancelled)
        self.assertEqual(posted, [drc.WM_LBUTTONDOWN, drc.WM_LBUTTONUP])

    def test_before_press_runs_once(self):
        calls = []
        outcome, posted = self.run_driver([True, False], before_press=lambda: calls.append(1))
        self.assertTrue(outcome.pressed)
        self.assertEqual(calls, [1])

    def test_a_failing_before_press_does_not_stop_the_check(self):
        def fail():
            raise OSError("no such file")
        outcome, posted = self.run_driver([True, False], before_press=fail)
        self.assertTrue(outcome.pressed)
        self.assertIn("before the check: no such file", outcome.notes)

    def test_closed_not_left_open_when_run_does_nothing(self):
        outcome, posted = self.run_driver([True] * 1000)
        self.assertFalse(outcome.pressed)
        self.assertTrue(outcome.cancelled)
        self.assertEqual(posted[-1], drc.WM_CLOSE)
        self.assertEqual(posted.count(drc.WM_LBUTTONDOWN), 3)
        self.assertFalse(outcome.ran_after_reply())

    def test_ran_when_the_reply_beats_the_close_check(self):
        # A small board is checked and answered before the driver looks
        # again: it is stopped with the press sent and the close unseen
        outcome = drc.DialogOutcome()
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(drc, "find_dialog", return_value=42), \
                mock.patch.object(drc, "_run_button", return_value=1), \
                mock.patch.object(drc, "_is_open", return_value=True), \
                mock.patch.object(drc.ctypes, "windll"):
            async def go():
                task = asyncio.create_task(drc.drive_dialog(outcome, Path(d) / "progress.txt", settle=0,
                                                            press_wait=5.0))
                while not outcome.posted:
                    await asyncio.sleep(0.001)
                task.cancel()
            asyncio.run(go())
        self.assertFalse(outcome.pressed)
        self.assertFalse(outcome.cancelled)
        self.assertTrue(outcome.ran_after_reply())

    def test_not_ran_when_no_dialog_was_seen(self):
        self.assertFalse(drc.DialogOutcome().ran_after_reply())
        self.assertFalse(drc.DialogOutcome(seen=True).ran_after_reply())

    # A21: Altium's repour message, answered with Run DRC
    PROMPT = (7, {"run drc": 71, "cancel": 72, "repour polygons and run drc": 73})

    def run_with_prompt(self, prompt_states, open_states=(True, True)):
        """The dialog stays open after the press while the message is up
        (open_states), then the message is up for as many looks as
        prompt_states gives True; returns the outcome and the windows posted to."""
        prompts = iter(prompt_states)
        states = iter(open_states)
        outcome = drc.DialogOutcome()
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(drc, "find_dialog", return_value=42), \
                mock.patch.object(drc, "_run_button", return_value=1), \
                mock.patch.object(drc, "_is_open", side_effect=lambda h: next(states, False)), \
                mock.patch.object(drc, "find_repour_prompt",
                                  side_effect=lambda: self.PROMPT if next(prompts, False) else None), \
                mock.patch.object(drc.ctypes, "windll") as windll:
            async def go():
                task = asyncio.create_task(drc.drive_dialog(outcome, Path(d) / "progress.txt", keep_alive=0.01,
                                                            settle=0, press_wait=0.5, poll=0.01,
                                                            repour_wait=0.05))
                await asyncio.sleep(1.0)
                task.cancel()
            asyncio.run(go())
            posted = [(c.args[0], c.args[1]) for c in windll.user32.PostMessageW.call_args_list]
        return outcome, posted

    def test_repour_message_gets_run_drc(self):
        # Seen once by the press loop, then once by the keep-alive loop,
        # which presses Run DRC; then it is gone
        outcome, posted = self.run_with_prompt([True, True])
        self.assertTrue(outcome.pressed)
        self.assertTrue(outcome.repour_prompt)
        self.assertFalse(outcome.repour_cancelled)
        self.assertTrue(outcome.ran_after_reply())
        self.assertEqual([w for w, m in posted if m == drc.WM_LBUTTONDOWN], [1, 71],
                         "Run in the dialog, then Run DRC in the message, nothing else")
        self.assertNotIn(drc.WM_CLOSE, [m for _, m in posted])

    def test_repour_message_after_the_dialog_closed(self):
        outcome, posted = self.run_with_prompt([False, True], open_states=[False])
        self.assertTrue(outcome.pressed)
        self.assertTrue(outcome.repour_prompt)
        self.assertEqual([w for w, m in posted if m == drc.WM_LBUTTONDOWN], [1, 71])

    def test_repour_message_that_stays_is_cancelled(self):
        outcome, posted = self.run_with_prompt([True] * 1000)
        self.assertTrue(outcome.repour_prompt)
        self.assertTrue(outcome.repour_cancelled)
        self.assertFalse(outcome.ran_after_reply(), "a cancelled message is no check")
        downs = [w for w, m in posted if m == drc.WM_LBUTTONDOWN]
        self.assertEqual(downs, [1, 71, 71, 71, 72], "three Run DRC presses, then Cancel once")
        self.assertTrue(any("cancelled" in n for n in outcome.notes), outcome.notes)

    def test_no_repour_message_no_flag(self):
        outcome, posted = self.run_with_prompt([], open_states=[False])
        self.assertTrue(outcome.pressed)
        self.assertFalse(outcome.repour_prompt)


class RepourPromptTest(unittest.TestCase):
    def test_known_by_class_title_and_buttons(self):
        buttons = ["&Run DRC", "Cancel", "Repour Polygons and Run DRC"]
        self.assertTrue(drc.is_repour_prompt("TMessageForm", "Design Rule Check", buttons))
        # in any order, any case
        self.assertTrue(drc.is_repour_prompt("TMessageForm", "Design Rule Check ",
                                             ["repour polygons and run drc", "RUN DRC"]))

    def test_other_windows_are_not_it(self):
        buttons = ["Run DRC", "Cancel", "Repour Polygons and Run DRC"]
        self.assertFalse(drc.is_repour_prompt("#32770", "Design Rule Check", buttons))
        self.assertFalse(drc.is_repour_prompt("TMessageForm", "Confirm", buttons))
        self.assertFalse(drc.is_repour_prompt("TDesignRuleCheckForm", "Design Rule Checker",
                                              ["Run Design Rule Check...", "Cancel"]))
        # a message of that title without the repour choice
        self.assertFalse(drc.is_repour_prompt("TMessageForm", "Design Rule Check", ["OK"]))
        self.assertFalse(drc.is_repour_prompt("TMessageForm", "Design Rule Check", ["Run DRC", "Cancel"]))

    def test_button_key(self):
        self.assertEqual(drc.button_key(" &Run DRC "), "run drc")


class ViolationTest(unittest.TestCase):
    def test_measurement_from_the_descriptor(self):
        self.assertEqual(drc.measurement("Clearance Constraint: (0.659mm < 1.27mm) Between Via (91.6mm,65.4mm)"),
                         {"kind": "Clearance Constraint", "actual_mils": 25.945, "limit_mils": 50.0,
                          "comparison": "<"})
        w = drc.measurement("Width Constraint: Track (9mm,44.2mm)(12.475mm,47.675mm) on SIG Actual Width = "
                            "0.125mm, Target Width = 0.254mm")
        self.assertEqual((w["actual_mils"], w["limit_mils"], w["comparison"]), (4.921, 10.0, "<"))
        self.assertEqual(drc.measurement("Un-Routed Net Constraint: Net GND Between Pad"),
                         {"kind": "Un-Routed Net Constraint"})

    def test_filters(self):
        v = {"rule": "Clearance_GND", "kind": "Clearance Constraint", "x_mils": 100, "y_mils": 100,
             "primitive1": {"net": "GND", "x_mils": 95, "y_mils": 100},
             "primitive2": {"net": "CLK", "x_mils": 300, "y_mils": 300}}
        self.assertTrue(drc.matches(v, rules=["clearance"]))
        self.assertFalse(drc.matches(v, rules=["width"]))
        self.assertTrue(drc.matches(v, nets=["clk"]))
        self.assertFalse(drc.matches(v, nets=["5V"]))
        self.assertTrue(drc.matches(v, area=[250, 250, 350, 350]))    # by an object's position
        self.assertFalse(drc.matches(v, area=[500, 500, 600, 600]))

    def test_rules_match_whole_names_and_kinds(self):
        def viol(rule, description):
            return {"rule": rule, "description": description, **drc.measurement(description)}

        gnd = viol("Clearance_GND", "Clearance Constraint: (0.1mm < 0.152mm) Between Via (1mm,1mm) And Via")
        holes = viol("HoleToHoleClearance", "Hole To Hole Clearance (Gap=0.1mm): (0.05mm < 0.1mm) Between Pad")
        edge = viol("BoardOutlineClearance", "Board Outline Clearance(Outline Edge): (Collision < 25mil) Between")
        net = viol("UnRoutedNet", "Un-Routed Net Constraint: Net GND Between Pad U1-1 And Pad U1-2")
        self.assertEqual(edge["kind"], "Board Outline Clearance")
        # a kind picks every rule of that kind, a name only its rule
        self.assertTrue(drc.matches(gnd, rules=["Clearance"]))
        self.assertTrue(drc.matches(gnd, rules=["clearance_gnd"]))
        self.assertFalse(drc.matches(holes, rules=["Clearance"]))
        self.assertFalse(drc.matches(edge, rules=["Clearance"]))
        self.assertTrue(drc.matches(holes, rules=["Hole To Hole Clearance"]))
        self.assertTrue(drc.matches(edge, rules=["BoardOutlineClearance"]))
        self.assertTrue(drc.matches(net, rules=["Un-Routed Net"]))
        self.assertTrue(drc.matches(net, rules=["unroutednet constraint"]))
        self.assertFalse(drc.matches(net, rules=["Net"]))


if __name__ == "__main__":
    unittest.main()
