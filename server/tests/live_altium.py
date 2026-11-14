"""Helpers for the live tests, which drive a running Altium Designer.

They are not in the offline set CI runs. With Altium open, from server/:

    set ALTIUM_LIVE=1
    python -m unittest tests.test_live_<name> -v

Each test runs this checkout's scripts (no "script_path" may be set in the
config), works on boards of its own and closes them unsaved; the documents
already open in Altium are not touched.
"""
import asyncio
import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

LIVE = os.environ.get("ALTIUM_LIVE") == "1"
SKIP_REASON = "drives Altium: set ALTIUM_LIVE=1 with Altium Designer open"

if LIVE:
    import main  # noqa: E402,F401


def check_scripts_are_this_checkouts():
    """Skip when the server would run another copy's scripts."""
    scripts = Path(main.altium_bridge.config.script_path).resolve()
    here = Path(main.__file__).resolve().parent
    if here not in scripts.parents:
        raise unittest.SkipTest(f"script_path {scripts} is not this checkout's; the test "
                                "would run other scripts than the ones under test")


def tool(coro):
    """Run one of the server's tools, its JSON result as a dict or list."""
    return json.loads(asyncio.run(coro))


def script(body):
    """Run a sandbox script through the server's own tool, return ResultText."""
    out = json.loads(asyncio.run(main.run_altium_script(None, body, 180)))
    if not out.get("success"):
        raise AssertionError(f"sandbox script failed: {json.dumps(out, indent=2)}")
    return out["result"].replace('{"sandbox": "no result set"}', "")


def new_board():
    """A new, empty PCB document, focused; returns its file name."""
    return script("CreateNewDocumentFromDocumentKind('PCB');\n"
                  "Obj1 := Client.CurrentView.OwnerDocument;\n"
                  "ResultText := Obj1.FileName;").strip()


def open_board(path):
    script(f"Obj1 := Client.OpenDocument('PCB', '{path}');\n"
           "Client.ShowDocument(Obj1);\n"
           "ResultText := Obj1.FileName;")


def save_board_as(name, path):
    """Save the open document name to path (a new board's first save)."""
    out = script(f"Obj1 := Client.GetDocumentByPath('{name}');\n"
                 f"ResultText := BoolToStr(Obj1.DoSafeChangeFileNameAndSave('{path}', 'PCB'), True);")
    if out.strip() != "True":
        raise AssertionError(f"could not save {name} as {path}: {out}")


def modified(name):
    """Whether the open document name has unsaved changes."""
    out = script(f"Obj1 := Client.GetDocumentByPath('{name}');\n"
                 "ResultText := BoolToStr(Obj1.Modified, True);").strip()
    return out == "True"


def close(name):
    """Close an open document unsaved."""
    script(f"Obj1 := Client.GetDocumentByPath('{name}');\n"
           "if Obj1 <> nil then\nbegin\n"
           "    Obj1.SetModified(False);\n"
           "    Client.CloseDocument(Obj1);\n"
           "end;\n"
           "ResultText := 'closed';")


def open_project(path):
    """Open a .PrjPcb as a project, before its board: a board opened alone
    lands under Free Documents. Returns the project's path as Altium has it."""
    return script(f"Obj1 := GetWorkspace.DM_OpenProject('{path}', True);\n"
                  "ResultText := Obj1.DM_ProjectFullPath;").strip()


def close_all_under(folder):
    """Close unsaved every open document whose name holds folder: a project,
    its documents and the reports Altium opened for it (a report is open
    under a file:/// name, which Client.GetDocumentByPath does not find)."""
    script("var\n  I, J : Integer;\n  M : IServerModule;\n  D : IServerDocument;\nbegin\n"
           "for I := 0 to Client.Count - 1 do\nbegin\n"
           "  M := Client.ServerModule[I];\n"
           "  for J := M.DocumentCount - 1 downto 0 do\n  begin\n"
           "    D := M.Documents[J];\n"
           f"    if Pos(UpperCase('{folder}'), UpperCase(D.FileName)) > 0 then\n    begin\n"
           "      D.SetModified(False);\n"
           "      Client.CloseDocument(D);\n"
           "    end;\n  end;\nend;\n"
           "ResultText := 'closed';\nend;")
