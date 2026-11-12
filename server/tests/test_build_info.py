"""Tests for the version and build line get_server_status reports."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import build_info  # noqa: E402


class BuildInfoTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name, text, encoding="utf-8"):
        (self.root / name).write_text(text, encoding=encoding)

    def test_version_and_build_line(self):
        self.write("manifest.json", '{"name": "altium-mcp", "version": "0.7.0"}')
        self.write("BUILD.txt", "0.7.0-ad25-20261109-223143 0a6539a4ead9\n")
        self.assertEqual(build_info.build_info(self.root), {
            "version": "0.7.0",
            "build": "0.7.0-ad25-20261109-223143 0a6539a4ead9",
        })

    def test_checkout_without_build_txt(self):
        self.write("manifest.json", '{"version": "0.7.0"}')
        self.assertEqual(build_info.build_info(self.root), {"version": "0.7.0", "build": None})

    def test_missing_files_give_none(self):
        self.assertEqual(build_info.build_info(self.root), {"version": None, "build": None})

    def test_broken_manifest_gives_none(self):
        for text in ("{not json", "[1, 2]", '{"version": 7}', '{"version": "  "}'):
            with self.subTest(text=text):
                self.write("manifest.json", text)
                self.assertIsNone(build_info.manifest_version(self.root))

    def test_build_txt_as_powershell_writes_it(self):
        # Set-Content: ANSI with CRLF in PowerShell 5, UTF-8 in 7. Out-File in
        # 5: UTF-16 with a BOM. A BOM and leading blank lines are skipped.
        for name, data in (
            ("ascii crlf", b"0.7.0-ad25-1 abc\r\n"),
            ("utf-8 bom, blank first", b"\xef\xbb\xbf\r\n0.7.0-ad25-1 abc\r\n"),
            ("utf-16 le", "﻿0.7.0-ad25-1 abc\r\n".encode("utf-16-le")),
        ):
            with self.subTest(name):
                (self.root / "BUILD.txt").write_bytes(data)
                self.assertEqual(build_info.build_line(self.root), "0.7.0-ad25-1 abc")

    def test_undecodable_or_empty_build_txt_gives_none(self):
        for data in (b"\x80\x81\x82", b"", b"\r\n  \r\n"):
            with self.subTest(data=data):
                (self.root / "BUILD.txt").write_bytes(data)
                self.assertIsNone(build_info.build_line(self.root))

    def test_default_root_is_the_folder_above_server(self):
        self.assertTrue((build_info.ROOT / "server" / "build_info.py").exists())
        self.assertEqual(build_info.manifest_version(), build_info.manifest_version(build_info.ROOT))


class ServerStatusTest(unittest.TestCase):
    def test_status_reports_version_and_build(self):
        import asyncio
        import json
        from unittest import mock

        import main

        fake = {"version": "9.9.9", "build": "9.9.9-ad25-1 abc"}
        with mock.patch.object(main.altium_bridge.config, "discover_altium", return_value=False), \
                mock.patch.object(main.build_info, "build_info", return_value=fake):
            status = json.loads(asyncio.run(main.get_server_status(None)))
        self.assertEqual(status["version"], "9.9.9")
        self.assertEqual(status["build"], "9.9.9-ad25-1 abc")
        self.assertIn("script_path", status)


if __name__ == "__main__":
    unittest.main()
