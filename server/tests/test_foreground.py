"""Offline tests of the foreground guard (A22): which window it keeps and
when it gives the foreground back. No window is touched."""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import foreground  # noqa: E402

ALTIUM = {100, 101}          # windows of X2.EXE
is_altium = ALTIUM.__contains__


class StepTest(unittest.TestCase):
    def test_altium_taking_the_front_is_given_back(self):
        self.assertEqual(foreground.step(5, 100, is_altium), (5, True))

    def test_another_altium_window_too(self):
        self.assertEqual(foreground.step(5, 101, is_altium), (5, True))

    def test_the_kept_window_itself_is_left(self):
        self.assertEqual(foreground.step(5, 5, is_altium), (5, False))

    def test_no_foreground_window_is_left(self):
        self.assertEqual(foreground.step(5, 0, is_altium), (5, False))

    def test_the_user_moving_to_another_program_is_followed(self):
        self.assertEqual(foreground.step(5, 7, is_altium), (7, False))

    def test_nothing_done_when_altium_was_in_front_at_the_start(self):
        self.assertEqual(foreground.step(None, 100, is_altium), (None, False))
        self.assertEqual(foreground.step(None, 7, is_altium), (None, False))


class GuardTest(unittest.TestCase):
    """The guard's handling of changes, its event thread replaced."""

    def guard(self, front):
        given = []
        g = foreground.ForegroundGuard(given.append, is_altium=is_altium)
        g._foreground = lambda: front
        events = mock.MagicMock()
        events.return_value.__enter__.return_value = events.return_value
        with mock.patch.object(foreground, "ForegroundEvents", events), \
                mock.patch.object(foreground.ctypes, "windll", create=True) as windll:
            windll.user32.IsWindow.return_value = True
            g.__enter__()
            return g, given, events

    def test_keeps_the_window_in_front_and_gives_it_back(self):
        g, given, events = self.guard(5)
        self.assertEqual(g.kept, 5)
        events.assert_called_once()
        with mock.patch.object(foreground.ctypes, "windll", create=True) as windll:
            windll.user32.IsWindow.return_value = True
            g._seen(100)
            g._seen(5)
        self.assertEqual(given, [5])
        self.assertEqual(g.given_back, 1)

    def test_does_not_listen_when_altium_is_in_front(self):
        g, given, events = self.guard(100)
        self.assertIsNone(g.kept)
        events.assert_not_called()

    def test_does_not_listen_when_nothing_is_in_front(self):
        g, given, events = self.guard(0)
        self.assertIsNone(g.kept)
        events.assert_not_called()

    def test_a_closed_window_is_not_given_the_front(self):
        g, given, _ = self.guard(5)
        with mock.patch.object(foreground.ctypes, "windll", create=True) as windll:
            windll.user32.IsWindow.return_value = False
            g._seen(100)
        self.assertEqual(given, [])

    def test_a_failed_give_back_is_not_counted(self):
        g, _, _ = self.guard(5)
        g._give_back = mock.Mock(side_effect=OSError("refused"))
        with mock.patch.object(foreground.ctypes, "windll", create=True) as windll:
            windll.user32.IsWindow.return_value = True
            g._seen(100)
        self.assertEqual(g.given_back, 0)


if __name__ == "__main__":
    unittest.main()
