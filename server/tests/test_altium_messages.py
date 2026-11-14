"""Offline tests of how the bridge treats Altium's messages (A24, A29): which it
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

    def test_left_open_names_the_tool_that_answers_it(self):
        out = am.failure("get_x", [], message(title="Confirm", buttons=["Yes", "No"]), None, False)
        self.assertIn("answer_altium_message", out["error"])
        self.assertIn("or in Altium", out["error"])

    def test_refusal(self):
        out = am.refusal("get_x", [message(title="Confirm", buttons=["Yes", "No"])])
        self.assertFalse(out["success"])
        self.assertTrue(out["error"].startswith("Not run"))
        self.assertIn("'Confirm'", out["error"])
        self.assertIn("Answer it with answer_altium_message", out["error"])


class PicturesTest(unittest.TestCase):
    """A29: one picture per message window, not one per refusal."""

    def setUp(self):
        self.taken, self.alive = [], {1, 2}
        self.pictures = am.Pictures(self.take, alive=lambda h: h in self.alive, exists=lambda p: True)

    def take(self, m):
        self.taken.append(m.hwnd)
        return f"pic_{m.hwnd}_{len(self.taken)}.png"

    def test_the_same_window_keeps_its_first_picture(self):
        m = message(hwnd=1, buttons=["Yes", "No"])
        first = self.pictures.get(m)
        self.assertEqual(self.pictures.get(message(hwnd=1, buttons=["Yes", "No"])), first)
        self.assertEqual(self.taken, [1])

    def test_another_window_gets_its_own(self):
        self.pictures.get(message(hwnd=1))
        self.pictures.get(message(hwnd=2))
        self.assertEqual(self.taken, [1, 2])

    def test_a_handle_given_to_another_message_is_a_new_picture(self):
        self.pictures.get(message(hwnd=1, title="Confirm", buttons=["Yes", "No"]))
        self.pictures.get(message(hwnd=1, title="Information", buttons=["OK"]))
        self.assertEqual(self.taken, [1, 1])

    def test_a_window_gone_and_its_handle_back_is_a_new_picture(self):
        m = message(hwnd=1)
        self.pictures.get(m)
        self.alive.discard(1)
        self.pictures.get(message(hwnd=2))   # any reading drops the gone window
        self.alive.add(1)
        self.pictures.get(m)
        self.assertEqual(self.taken, [1, 2, 1])

    def test_a_picture_deleted_since_is_taken_again(self):
        pictures = am.Pictures(self.take, alive=lambda h: True, exists=lambda p: False)
        pictures.get(message(hwnd=1))
        pictures.get(message(hwnd=1))
        self.assertEqual(self.taken, [1, 1])

    def test_no_picture_is_not_kept(self):
        pictures = am.Pictures(lambda m: None, alive=lambda h: True)
        self.assertIsNone(pictures.get(message(hwnd=1)))


class PickTest(unittest.TestCase):
    """A29: which open message the tool answers."""

    def test_the_only_one_open(self):
        m = message(hwnd=1, title="Confirm")
        self.assertEqual(am.pick([m]), (m, ""))

    def test_by_title_in_any_case(self):
        a, b = message(hwnd=1, title="Confirm"), message(hwnd=2, title="Information")
        self.assertEqual(am.pick([a, b], "confirm")[0], a)

    def test_none_open(self):
        m, why = am.pick([])
        self.assertIsNone(m)
        self.assertIn("No Altium message is open", why)

    def test_several_open_and_no_title_asks_for_one(self):
        m, why = am.pick([message(hwnd=1, title="Confirm"), message(hwnd=2, title="Information")])
        self.assertIsNone(m)
        self.assertIn("Give the title", why)
        self.assertIn("'Confirm'", why)
        self.assertIn("'Information'", why)

    def test_a_title_none_has(self):
        m, why = am.pick([message(hwnd=1, title="Confirm")], "Warning")
        self.assertIsNone(m)
        self.assertIn("titled 'Warning'", why)
        self.assertIn("'Confirm'", why)

    def test_two_with_the_title_are_not_guessed(self):
        m, why = am.pick([message(hwnd=1, title="Confirm"), message(hwnd=2, title="Confirm")], "Confirm")
        self.assertIsNone(m)
        self.assertIn("cannot be told", why)


class ButtonTest(unittest.TestCase):
    def test_matched_without_the_mark_in_any_case(self):
        m = message(buttons=["&Yes", "&No"])
        self.assertEqual(am.matching_button(m, "no"), "&No")
        self.assertEqual(am.matching_button(m, "&YES"), "&Yes")

    def test_a_caption_it_has_not(self):
        m = message(title="Confirm", buttons=["&Yes", "&No"])
        self.assertIsNone(am.matching_button(m, "Cancel"))
        out = am.no_such_button(m, "Cancel")
        self.assertFalse(out["success"])
        self.assertIn("its buttons are Yes, No", out["error"])
        self.assertIn("Nothing was pressed", out["error"])


class ReplyForTest(unittest.TestCase):
    def test_the_waiting_commands_reply(self):
        self.assertEqual(am.reply_for('{"success": true, "request_id": "ab", "result": "r"}', "ab"),
                         {"success": True, "request_id": "ab", "result": "r"})

    def test_another_requests_reply_is_not_it(self):
        self.assertIsNone(am.reply_for('{"success": true, "request_id": "cd"}', "ab"))

    def test_a_reply_without_request_id_is_not_it(self):
        self.assertIsNone(am.reply_for('{"success": true}', "ab"))

    def test_half_written_or_not_json(self):
        self.assertIsNone(am.reply_for('{"success": tr', "ab"))
        self.assertIsNone(am.reply_for("", "ab"))
        self.assertIsNone(am.reply_for("[1]", "ab"))


class AfterAnswerTest(unittest.TestCase):
    def setUp(self):
        self.m = message(hwnd=1, title="Confirm", buttons=["&Yes", "&No"], picture="p.png")

    def test_replied(self):
        out = am.after_answer(self.m, "&No", "get_x", {"success": True, "result": "r"}, None, 1, False)
        self.assertTrue(out["success"])
        self.assertEqual(out["outcome"], "replied")
        self.assertEqual(out["answered"]["button"], "No")
        self.assertEqual(out["answered"]["picture"], "p.png")
        self.assertEqual(out["reply"]["result"], "r")
        self.assertIn("went on and reported success", out["note"])

    def test_replied_failure_of_a_mutating_command(self):
        out = am.after_answer(self.m, "No", "place_x", {"success": False, "error": "e"}, None, 1, True)
        self.assertIn("reported failure: e", out["note"])
        self.assertIn("check what it did", out["note"])

    def test_no_command_waiting(self):
        out = am.after_answer(self.m, "No", None, None, None, 0, False)
        self.assertEqual(out["outcome"], "no_command_waiting")
        self.assertIsNone(out["command"])
        self.assertNotIn("reply", out)

    def test_another_message(self):
        nxt = message(hwnd=2, title="Warning", buttons=["OK", "Cancel"])
        out = am.after_answer(self.m, "No", "get_x", None, nxt, 2, False)
        self.assertEqual(out["outcome"], "another_message")
        self.assertEqual(out["altium_messages"][0]["title"], "Warning")
        self.assertIn("answer_altium_message", out["note"])

    def test_no_reply_yet_is_said(self):
        out = am.after_answer(self.m, "No", "place_x", None, None, 60, True)
        self.assertEqual(out["outcome"], "no_reply_yet")
        self.assertNotIn("reply", out)
        self.assertIn("no reply within 60 s", out["note"])
        self.assertIn("changing the design", out["note"])


if __name__ == "__main__":
    unittest.main()
