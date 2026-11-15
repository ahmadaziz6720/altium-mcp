"""Live test of make_pcblib_from_board in a running Altium Designer (A8): a
PCB library made from a board by Altium's own Make PCB Library, run from a
script, saved where the caller says, and the board, its project and the open
documents left as they were found.

Each library is read back through Altium (get_footprint_primitives opens the
saved file): its footprints and their pad counts are compared with the
tool's result and with the board's components, read by a board iterator.

See tests/live_altium.py for how to run it. It works on a copy of the
"SpiritLevel-SL1" example project folder Altium installs (skipped when it is
not there); everything under the copy is closed unsaved after each test.
"""
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.live_altium import (LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close_all_under, listing,
                                modified, open_board, open_project, script, tool)

if LIVE:
    import main
    import win32api

EXAMPLE = Path(r"C:\Users\Public\Documents\Altium\AD25\Examples\SpiritLevel-SL1")
BOARD = "SL1 Xilinx Spartan-IIE PQ208 Rev1.02.PcbDoc"
PROJECT = "SL1 Xilinx Spartan-IIE PQ208 Rev1.02.PrjPcb"
SHEET = "SL_Power.SchDoc"


def open_documents():
    """Every document open in Altium, by its name, sorted. The server's own
    resident bridge projects (A30) are left out: a call may start one."""
    out = script("var\n  I, J : Integer;\n  M : IServerModule;\n  S : String;\nbegin\nS := '';\n"
                 "for I := 0 to Client.Count - 1 do\nbegin\n  M := Client.ServerModule[I];\n"
                 "  for J := 0 to M.DocumentCount - 1 do\n    S := S + M.Documents[J].FileName + #13#10;\nend;\n"
                 "ResultText := S;\nend;")
    return sorted(line for line in out.splitlines()
                  if line.strip() and "\\altium_mcp\\resident\\" not in line.lower())


def focused():
    return script("ResultText := Client.CurrentView.OwnerDocument.FileName;").strip()


def board_components(board):
    """{pattern (upper case): set of pad counts} of the board's components,
    read by a board iterator."""
    out = script(f"""var
    B : IPCB_Board;
    It : IPCB_BoardIterator;
    C : IPCB_Component;
    S : String;
begin
B := PCBServer.GetPCBBoardByPath('{board}');
S := '';
It := B.BoardIterator_Create;
It.AddFilter_ObjectSet(MkSet(eComponentObject));
It.AddFilter_LayerSet(AllLayers);
It.AddFilter_Method(eProcessAll);
C := It.FirstPCBObject;
while C <> nil do
begin
    S := S + C.Pattern + '|' + IntToStr(C.GetPrimitiveCount(MkSet(ePadObject))) + #13#10;
    C := It.NextPCBObject;
end;
B.BoardIterator_Destroy(It);
ResultText := S;
end;""")
    found = {}
    for line in out.splitlines():
        if "|" in line:
            name, pads = line.rsplit("|", 1)
            found.setdefault(name.upper(), set()).add(int(pads))
    return found


def project_state(project):
    """(documents, the project file's unsaved flag) as Altium has them."""
    out = script(f"""var
    P : IProject;
    I : Integer;
    S : String;
begin
P := GetWorkspace.DM_GetProjectFromPath('{project}');
S := BoolToStr(Client.GetDocumentByPath(P.DM_ProjectFullPath).Modified, True) + #13#10;
for I := 0 to P.DM_LogicalDocumentCount - 1 do
    S := S + P.DM_LogicalDocuments(I).DM_FullPath + #13#10;
ResultText := S;
end;""")
    lines = [line for line in out.splitlines() if line.strip()]
    return sorted(lines[1:]), lines[0] == "True"


def read_back(library):
    """{footprint name: pads} of a saved library, opened by Altium."""
    inv = tool(main.get_footprint_primitives(None, library_path=str(library)))
    return {fp["name"]: fp.get("pads", 0) for fp in inv["footprints"]}


@unittest.skipUnless(LIVE, SKIP_REASON)
@unittest.skipUnless((EXAMPLE / BOARD).exists(), f"Altium's example board is not in {EXAMPLE}")
class LivePcbLibFromBoardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        check_scripts_are_this_checkouts()

    def setUp(self):
        # Altium is given the long path: the one it reports back
        self.tmp = Path(win32api.GetLongPathName(tempfile.mkdtemp(prefix="pcblib_live_")))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.folder = self.tmp / "SL1"
        shutil.copytree(EXAMPLE, self.folder)
        self.board = str(self.folder / BOARD)
        self.project = str(self.folder / PROJECT)
        self.addCleanup(close_all_under, str(self.tmp))

    def check_against_board(self, footprints, components):
        """Every footprint is a pattern of the board (Altium names a second,
        different footprint of one pattern "<pattern>_<n>") with a pad count
        its components have."""
        for name, pads in footprints.items():
            pattern = name.upper()
            if pattern not in components and "_" in pattern:
                pattern = pattern.rsplit("_", 1)[0]
            self.assertIn(pattern, components, f"{name} is not a pattern of the board")
            self.assertIn(pads, components[pattern], f"{name}: {pads} pads")

    def test_board_open_in_its_project(self):
        open_project(self.project)
        open_board(self.board)
        components = board_components(self.board)
        self.assertEqual(len(components), 29)
        # Another document of the project in front, as a caller may have it
        script(f"Obj1 := Client.OpenDocument('SCH', '{self.folder / SHEET}');\nClient.ShowDocument(Obj1);\n"
               "ResultText := Obj1.FileName;")
        docs, front = open_documents(), focused()
        prj_before = project_state(self.project)
        files_before = listing(self.folder)
        library = self.tmp / "out" / "SL1.PcbLib"

        out = tool(main.make_pcblib_from_board(None, self.board, str(library)))

        self.assertTrue(out.get("success"), out)
        self.assertEqual(out["problems"], [])
        self.assertTrue(library.is_file())
        # Left as found: no document added or closed, the same one in front,
        # the board and the project unchanged, no file in the project folder
        self.assertEqual(open_documents(), docs)
        self.assertEqual(focused(), front)
        self.assertFalse(modified(self.board), "the board was left modified")
        self.assertEqual(project_state(self.project), prj_before)
        self.assertEqual(listing(self.folder), files_before)
        self.assertTrue(out["board_was_open"])
        self.assertFalse(out["board_modified"])

        saved = read_back(library)
        self.assertEqual(saved, {fp["name"]: fp["pads"] for fp in out["footprints"]})
        self.assertEqual(out["footprint_count"], len(saved))
        # One footprint per pattern at least, each pattern of the board there
        self.assertGreaterEqual(len(saved), len(components))
        self.assertEqual(components.keys() - {n.upper() for n in saved}, set())
        self.check_against_board(saved, components)
        self.assertEqual(saved["PQ208"], 210)

    def test_board_not_open_and_some_footprints(self):
        docs = open_documents()
        library = self.tmp / "Some.PcbLib"

        out = tool(main.make_pcblib_from_board(None, self.board, str(library),
                                               footprints=["pq208", "CR2012-0805", "TP"]))

        self.assertTrue(out.get("success"), out)
        self.assertEqual(out["problems"], [])
        # The board was opened for the call and closed again
        self.assertFalse(out["board_was_open"])
        self.assertEqual(open_documents(), docs)
        saved = read_back(library)
        self.assertEqual(saved, {fp["name"]: fp["pads"] for fp in out["footprints"]})
        # Altium's second footprint of a pattern comes with it
        self.assertEqual(saved, {"PQ208": 210, "CR2012-0805": 2, "CR2012-0805_2": 2, "TP": 1})
        self.assertEqual(out["removed_by_filter"], 28)

    def test_board_with_unsaved_changes_stays_marked(self):
        open_board(self.board)
        script(f"Obj1 := Client.GetDocumentByPath('{self.board}');\nObj1.SetModified(True);\nResultText := 'marked';")
        library = self.tmp / "Tp.PcbLib"

        out = tool(main.make_pcblib_from_board(None, self.board, str(library), footprints=["TP"]))

        self.assertTrue(out.get("success"), out)
        self.assertTrue(modified(self.board), "the board's unsaved changes were unmarked")
        self.assertTrue(out["board_modified"])
        self.assertEqual(read_back(library), {"TP": 1})

    def test_refused_calls_write_nothing(self):
        existing = self.tmp / "Existing.PcbLib"
        existing.write_bytes(b"not a library")
        docs = open_documents()

        out = tool(main.make_pcblib_from_board(None, self.board, str(existing)))
        self.assertFalse(out["success"])
        self.assertIn("already exists", out["error"])
        self.assertEqual(existing.read_bytes(), b"not a library")

        library = self.tmp / "None.PcbLib"
        out = tool(main.make_pcblib_from_board(None, self.board, str(library), footprints=["NO_SUCH_FP", "TP"]))
        self.assertFalse(out["success"])
        self.assertIn("NO_SUCH_FP", out["error"])
        self.assertNotIn("TP", out["error"].split("Not on the board:")[-1].split(".")[0])
        self.assertFalse(library.exists())
        self.assertEqual(open_documents(), docs)

        out = tool(main.make_pcblib_from_board(None, str(self.folder / "missing.PcbDoc"), str(library)))
        self.assertFalse(out["success"])
        self.assertFalse(library.exists())


if __name__ == "__main__":
    unittest.main()
