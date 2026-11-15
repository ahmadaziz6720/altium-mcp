"""Unit tests for resident.py and the server's hand-over of a request to the
resident bridge (A30). No Altium needed: windows and launches are faked.

Run from server/:  python -m unittest tests.test_resident -v
"""
import asyncio
import os
import shutil
import sys
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import resident  # noqa: E402
from resident import Window  # noqa: E402


def caption(tag, when):
    return f"{resident.CAPTION}{tag} {datetime.fromtimestamp(when).strftime('%Y%m%d%H%M%S')}"


class CaptionTest(unittest.TestCase):
    def test_tag_and_time(self):
        now = int(time.time())
        self.assertEqual(resident.parse_caption(caption("abc123", now)), ("abc123", float(now)))

    def test_stopped_and_bare(self):
        self.assertEqual(resident.parse_caption(resident.CAPTION + "abc123 stopped"), ("abc123", None))
        self.assertEqual(resident.parse_caption(resident.CAPTION + "abc123"), ("abc123", None))

    def test_not_a_resident(self):
        self.assertIsNone(resident.parse_caption("Altium Designer"))
        self.assertIsNone(resident.parse_caption(resident.CAPTION))
        self.assertIsNone(resident.parse_caption("altium-mcp resident"))


class DecideTest(unittest.TestCase):
    NOW = 1_000_000.0

    def decide(self, found, **kw):
        args = dict(enabled=True, altium_running=True, message_open=False, start_failures=0)
        args.update(kw)
        return resident.decide(found, "mine", self.NOW, **args)[0]

    def win(self, tag="mine", age=1.0, enabled=True):
        return Window(1, tag, None if age is None else self.NOW - age, enabled)

    def test_alive_resident_serves(self):
        self.assertEqual(self.decide([self.win()]), "resident")

    def test_none_running_starts_one(self):
        self.assertEqual(self.decide([]), "start")

    def test_another_builds_resident_is_replaced(self):
        self.assertEqual(self.decide([self.win(tag="old")]), "start")

    def test_launch_when_off_or_altium_not_running(self):
        self.assertEqual(self.decide([self.win()], enabled=False), "launch")
        self.assertEqual(self.decide([], altium_running=False), "launch")

    def test_launch_while_a_message_or_a_modal_loop_is_up(self):
        # The form's timer fires inside a modal loop: the request would be
        # served there
        self.assertEqual(self.decide([self.win()], message_open=True), "launch")
        self.assertEqual(self.decide([self.win(enabled=False)]), "launch")

    def test_launch_when_ours_stopped_beating(self):
        self.assertEqual(self.decide([self.win(age=resident.BEAT_FRESH + 1)]), "launch")
        self.assertEqual(self.decide([self.win(age=None)]), "launch")

    def test_launch_after_failed_starts(self):
        self.assertEqual(self.decide([], start_failures=1), "start")
        self.assertEqual(self.decide([], start_failures=2), "launch")


class PrepareTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="resident_"))
        self.src = self.tmp / "src"
        self.src.mkdir()
        (self.src / "a.pas").write_text("procedure Run;\nbegin\nend;\n")
        (self.src / "b.pas").write_text("procedure B;\nbegin\nend;\n")
        (self.src / "P.PrjScr").write_text("[Document1]\nDocumentPath=a.pas\n\n"
                                           "[Document2]\nDocumentPath=b.pas\n")
        self.root = self.tmp / "resident"
        self.r = resident.Resident(self.root)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_project_holds_the_bundle_and_the_form(self):
        """The bridge goes in bundled, as a launch runs it: a script project
        compiles each unit in order, and a call to a routine defined further
        down fails there."""
        prj = self.r.prepare(self.src / "P.PrjScr")
        self.assertEqual(prj.parent, self.root / self.r.tag)
        text = prj.read_bytes().decode("latin-1")
        self.assertEqual(text.count("DocumentPath="), 2, text)
        self.assertIn("DocumentPath=MCPBridge.pas\r\n", text)
        self.assertIn("DocumentPath=MCPResident.pas\r\n", text)
        bridge = (prj.parent / "MCPBridge.pas").read_text(encoding="latin-1")
        self.assertIn("procedure Run;", bridge)
        self.assertIn("procedure B;", bridge)
        for name in ("MCPBridge.pas", "MCPResident.pas", "MCPResident.dfm"):
            data = (prj.parent / name).read_bytes()
            self.assertNotIn(b"\n", data.replace(b"\r\n", b""), f"{name}: Altium compiles CRLF only")

    def test_form_is_filled_with_its_tag_and_folder(self):
        prj = self.r.prepare(self.src / "P.PrjScr")
        form = (prj.parent / "MCPResident.pas").read_text(encoding="latin-1")
        self.assertNotIn("%TAG%", form)
        self.assertNotIn("%DIR%", form)
        self.assertIn(f"'altium-mcp resident {self.r.tag} '", form)
        self.assertIn(f"'{prj.parent}\\take'", form)
        self.assertIn(f"'{prj.parent}\\stop'", form)

    def test_tag_follows_the_content(self):
        self.r.prepare(self.src / "P.PrjScr")
        first = self.r.tag
        self.assertEqual(resident.Resident(self.root).prepare(self.src / "P.PrjScr").parent.name, first)
        time.sleep(0.01)
        (self.src / "b.pas").write_text("procedure B;\nbegin\n  B2;\nend;\n")
        self.r.prepare(self.src / "P.PrjScr")
        self.assertNotEqual(self.r.tag, first)

    def test_tag_is_the_same_for_lf_and_crlf_copies(self):
        """A release copy (git archive: LF) and a checkout (core.autocrlf:
        CRLF) at one commit must give one tag, or two servers on one Altium
        close each other's resident (A34 a). Covers the form's templates and
        the bridge's units and project file."""
        def tree(name, eol):
            base = self.tmp / name
            (base / "tpl").mkdir(parents=True)
            for src in (resident.TEMPLATE_DIR / "MCPResident.pas", resident.TEMPLATE_DIR / "MCPResident.dfm"):
                text = src.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", eol)
                (base / "tpl" / src.name).write_bytes(text)
            for n, body in (("a.pas", "procedure Run;\nbegin\nend;\n"), ("b.pas", "procedure B;\nbegin\nend;\n"),
                            ("P.PrjScr", "[Document1]\nDocumentPath=a.pas\n\n[Document2]\nDocumentPath=b.pas\n")):
                (base / n).write_bytes(body.replace("\n", eol.decode()).encode())
            return base

        tags = []
        for name, eol in (("lf", b"\n"), ("crlf", b"\r\n")):
            base = tree(name, eol)
            with mock.patch.object(resident, "TEMPLATE_DIR", base / "tpl"):
                r = resident.Resident(self.tmp / f"root_{name}")
                r.prepare(base / "P.PrjScr")
                tags.append(r.tag)
                form = (r.project.parent / "MCPResident.pas").read_bytes()
                self.assertNotIn(b"\n", form.replace(b"\r\n", b""))
        self.assertEqual(tags[0], tags[1], "LF and CRLF copies of one commit gave two tags")

    def test_old_projects_are_pruned(self):
        tags = []
        for i in range(5):
            (self.src / "b.pas").write_text(f"procedure B;\nbegin\n  // {i}\nend;\n")
            os.utime(self.src / "b.pas", (time.time() + i, time.time() + i))
            self.r.prepare(self.src / "P.PrjScr")
            tags.append(self.r.tag)
            os.utime(self.root / self.r.tag, (time.time() + i, time.time() + i))
        left = sorted(p.name for p in self.root.iterdir())
        self.assertEqual(len(left), resident.KEEP)
        self.assertIn(tags[-1], left)

    def test_a_callee_defined_further_down_comes_first(self):
        (self.src / "a.pas").write_text("procedure Run;\nbegin\n  Later;\nend;\n\n"
                                        "procedure Later;\nbegin\nend;\n")
        bridge = (self.r.prepare(self.src / "P.PrjScr").parent / "MCPBridge.pas").read_text(encoding="latin-1")
        self.assertLess(bridge.index("procedure Later;"), bridge.index("procedure Run;"))

    def test_take_and_reclaim(self):
        self.r.prepare(self.src / "P.PrjScr")
        self.r.write_take()
        self.assertFalse(self.r.taken())
        self.assertTrue(self.r.reclaim(), "a take file still there is a request not claimed")
        self.assertTrue(self.r.taken())
        self.assertFalse(self.r.reclaim(), "a take file gone is a claim")

    def test_the_shipped_form_fills(self):
        """The real form unit has both placeholders and the procedure the
        start command names."""
        text = (resident.TEMPLATE_DIR / "MCPResident.pas").read_text(encoding="latin-1")
        self.assertIn("%TAG%", text)
        self.assertIn("%DIR%take", text)
        self.assertIn("%DIR%stop", text)
        self.assertIn("procedure StartResident;", text)
        dfm = (resident.TEMPLATE_DIR / "MCPResident.dfm").read_text(encoding="latin-1")
        self.assertIn("OnTimer = ResidentTimerTimer", dfm)
        self.assertIn('ProcName="MCPResident>StartResident"', self.r.start_command("X2.EXE"))


import main  # noqa: E402


class HandOverTest(unittest.TestCase):
    """The server's route for one call: resident, start, or launch."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="handover_"))
        self.bridge = main.AltiumBridge.__new__(main.AltiumBridge)
        self.bridge.config = mock.Mock(resident_bridge=True, script_path=str(main.DEFAULT_SCRIPT_PATH),
                                       altium_exe_path="X2.EXE")
        self.bridge.resident = resident.Resident(self.tmp)
        self.bridge._resident_failures = 0
        self.bridge.last_route = None
        self.launches = []

        async def launch():
            self.launches.append("launch")
            return True

        async def started(timeout):
            return True

        self.patches = [mock.patch.object(self.bridge, "run_altium_script", launch),
                        mock.patch.object(main.AltiumBridge, "_wait_for_start", staticmethod(started)),
                        mock.patch.object(main.altium_messages, "find", return_value=[]),
                        mock.patch.object(main, "_dismiss_altium_dialogs", return_value=[]),
                        mock.patch.object(main, "RESIDENT_TAKE_TIMEOUT", 0.3),
                        mock.patch.object(main, "START_TIMEOUT", 0.3)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def windows(self, *tags):
        return [Window(1, t, time.time(), True) for t in tags]

    def run_call(self, found, claim=False):
        """One hand-over with these resident windows; claim: the resident
        deletes the take file (claims the request) shortly after."""
        async def go():
            async def claimer():
                take = self.bridge.resident.take_file()
                for _ in range(200):
                    await asyncio.sleep(0.01)
                    if take.exists():
                        take.unlink()
                        return
            task = asyncio.ensure_future(claimer()) if claim else None
            out = await self.bridge._hand_over("x", False)
            if task:
                await task
            return out
        with mock.patch.object(resident, "windows", return_value=found):
            self.bridge.resident.prepare(main.DEFAULT_SCRIPT_PATH)
            return asyncio.run(go())

    def test_alive_resident_takes_the_request_with_no_launch(self):
        self.bridge.resident.prepare(main.DEFAULT_SCRIPT_PATH)
        self.assertTrue(self.run_call(self.windows(self.bridge.resident.tag), claim=True))
        self.assertEqual(self.launches, [])
        self.assertEqual(self.bridge.last_route["mode"], "resident")

    def test_resident_not_claiming_falls_back_to_a_launch(self):
        self.bridge.resident.prepare(main.DEFAULT_SCRIPT_PATH)
        self.assertTrue(self.run_call(self.windows(self.bridge.resident.tag)))
        self.assertEqual(self.launches, ["launch"])
        self.assertTrue(self.bridge.resident.taken(), "the take file is removed: the resident never serves it")
        self.assertIn("fallback", self.bridge.last_route)

    def test_none_alive_starts_one(self):
        with mock.patch.object(main.subprocess, "Popen") as popen:
            self.assertTrue(self.run_call([], claim=True))
        self.assertIn("MCPResident>StartResident", popen.call_args[0][0])
        self.assertEqual(self.launches, [])
        self.assertEqual(self.bridge._resident_failures, 0)

    def test_a_start_that_fails_twice_stops_trying(self):
        with mock.patch.object(main.subprocess, "Popen") as popen:
            for _ in range(3):
                self.assertTrue(self.run_call([]))
        self.assertEqual(popen.call_count, 2, "two starts, then launches only")
        self.assertEqual(self.launches, ["launch"] * 3)
        self.assertEqual(self.bridge.last_route["mode"], "launch")

    def test_off_in_config_launches(self):
        self.bridge.config.resident_bridge = False
        self.assertTrue(self.run_call([]))
        self.assertEqual(self.launches, ["launch"])

    def test_a_leftover_take_file_is_removed_before_a_launch(self):
        """A launch-mode call must leave nothing for the resident to claim."""
        self.bridge.resident.prepare(main.DEFAULT_SCRIPT_PATH)
        self.bridge.resident.write_take()
        with mock.patch.object(main.altium_messages, "find", return_value=["a message"]):
            self.assertTrue(self.run_call(self.windows(self.bridge.resident.tag)))
        self.assertEqual(self.launches, ["launch"])
        self.assertTrue(self.bridge.resident.taken())


if __name__ == "__main__":
    unittest.main()
