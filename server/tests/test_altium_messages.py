"""Offline tests of how the bridge treats Altium's messages (A24): which it
presses, which it leaves, and what the call then says. No window is touched."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import altium_messages as am  # noqa: E402


def message(hwnd=1, title="Information", buttons=("OK",), cls="TMessageForm", text="", picture=None):
    return am.Message(hwnd, cls, title, text, list(buttons), picture)


class SafeToPressTest(unittest.TestCase):
    def test_a_single_ok_or_close(self):
        self.assertTrue(message(buttons=["OK"]).safe_to_press)
        self.assertTrue(message(buttons=["&OK"]).safe_to_press)
        self.assertTrue(message(buttons=["Close"]).safe_to_press)

    def test_choices_are_not(self):
        self.assertFalse(message(buttons=["Yes", "No"]).safe_to_press)
        self.assertFalse(message(buttons=["OK", "Cancel"]).safe_to_press)

    def test_another_single_button_is_not(self):
        # Altium's exception form: sending a report is not an answer to give
        self.assertFalse(message(cls="TShowException", buttons=["Send and Close"]).safe_to_press)

    def test_no_button_found_is_not(self):
        self.assertFalse(message(buttons=[]).safe_to_press)


class DescribeTest(unittest.TestCase):
    def test_names_title_class_buttons_and_text(self):
        d = message(cls="#32770", title="Altium", buttons=["&Yes", "No"], text="Save changes?").describe()
        self.assertEqual(d, "'Altium' (#32770, buttons: Yes, No): Save changes?")

    def test_points_to_the_picture_when_the_text_cannot_be_read(self):
        d = message(picture="C:/x/dialog_1.png").describe()
        self.assertIn("see the picture C:/x/dialog_1.png", d)

    def test_says_when_no_button_was_found(self):
        self.assertIn("buttons: none found", message(buttons=[]).describe())


class WatchTest(unittest.TestCase):
    def test_a_message_is_due_after_the_grace_once(self):
        w = am.Watch(grace=1.0)
        m = message(hwnd=7)
        self.assertEqual(w.due([m], 10.0), [])
        self.assertEqual(w.due([m], 10.5), [])
        self.assertEqual(w.due([m], 11.0), [m])
        self.assertEqual(w.due([m], 12.0), [])

    def test_a_message_gone_and_back_starts_again(self):
        w = am.Watch(grace=1.0)
        m = message(hwnd=7)
        w.due([m], 10.0)
        w.due([], 10.5)
        self.assertEqual(w.due([m], 11.0), [])
        self.assertEqual(w.due([m], 12.0), [m])

    def test_a_new_window_is_a_new_message(self):
        w = am.Watch(grace=0.0)
        self.assertEqual(len(w.due([message(hwnd=1)], 1.0)), 1)
        self.assertEqual(len(w.due([message(hwnd=2)], 2.0)), 1)


class FailureTest(unittest.TestCase):
    def test_pressed_and_the_command_went_on(self):
        out = am.failure("get_x", [message()], None, {"success": True, "result": "r"}, False)
        self.assertFalse(out["success"])
        self.assertIn("closed with its only button", out["error"])
        self.assertIn("went on and reported success", out["error"])
        self.assertEqual(out["reply_after_message"], {"success": True, "result": "r"})
        self.assertEqual(out["altium_messages"][0]["buttons"], ["OK"])

    def test_pressed_and_the_command_failed_after(self):
        out = am.failure("get_x", [message()], None, {"success": False, "error": "no board"}, False)
        self.assertIn("reported failure: no board", out["error"])

    def test_a_mutating_command_says_to_check_the_design(self):
        out = am.failure("place_x", [message()], None, {"success": True}, True)
        self.assertIn("check the design before running it again", out["error"])

    def test_left_open(self):
        out = am.failure("get_x", [], message(title="Confirm", buttons=["Yes", "No"]), None, False)
        self.assertIn("left open", out["error"])
        self.assertIn("'Confirm'", out["error"])
        self.assertNotIn("reply_after_message", out)
        self.assertEqual(len(out["altium_messages"]), 1)

    def test_back_after_each_press_is_said_so(self):
        out = am.failure("get_x", [message(hwnd=1), message(hwnd=2)], message(hwnd=3), None, False)
        self.assertIn("came back", out["error"])
        self.assertEqual(len(out["altium_messages"]), 3)

    def test_refusal(self):
        out = am.refusal("get_x", [message(title="Confirm", buttons=["Yes", "No"])])
        self.assertFalse(out["success"])
        self.assertTrue(out["error"].startswith("Not run"))
        self.assertIn("'Confirm'", out["error"])


if __name__ == "__main__":
    unittest.main()
