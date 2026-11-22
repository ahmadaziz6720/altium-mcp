"""Live test of the compile tools after a script edit, in a running Altium
Designer. A48: Altium's project compile keeps its own model of each sheet and
updates it only from the change notices the schematic editor sends inside a
process. A script that changes an object without them (a part's footprint
through its implementation, a sheet property set directly) left
get_project_components and get_erc_violations reading the sheet as it was
before, and saving or closing the sheet did not change that. Both tools now
bring the compile's model of every sheet open in Altium up to date before
they compile, leaving the sheet's modified flag and its undo history as found.

See tests/live_altium.py for how to run it. It works on a copy of the power
sheet of the SpiritLevel-SL1 example Altium installs (skipped when it is not
there), in a project holding that sheet alone with the example's own project
settings, closed unsaved. (A project file holding nothing but the document
list compiled a sheet not open in Altium as empty on AD25, so the example's
settings are kept.)
"""
import asyncio
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.live_altium import LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close_all_under, script

if LIVE:
    import main
    import win32api

SL1 = Path(r"C:\Users\Public\Documents\Altium\AD25\Examples\SpiritLevel-SL1")
PROJECT = "SL1 Xilinx Spartan-IIE PQ208 Rev1.02.PrjPcb"
SHEET = "SL_Power.SchDoc"

BOUNDS = "Object not completely within sheet boundaries"


def one_sheet_project(folder: Path) -> Path:
    """The example's project file with its power sheet as its only document."""
    shutil.copyfile(SL1 / SHEET, folder / SHEET)
    sections, kept = [], []
    for line in (SL1 / PROJECT).read_text(encoding="latin-1").splitlines(keepends=True):
        if line.startswith("["):
            sections.append([])
        sections[-1].append(line)
    for section in sections:
        if not section[0].startswith("[Document"):
            kept.append(section)
        elif any(line.strip() == "DocumentPath=" + SHEET for line in section):
            kept.append(["[Document1]\r\n"] + section[1:])
    project = folder / "Refresh.PrjPcb"
    project.write_text("".join("".join(s) for s in kept), encoding="latin-1", newline="")
    return project


@unittest.skipUnless(LIVE, SKIP_REASON)
@unittest.skipUnless((SL1 / PROJECT).exists(), f"Altium's example project is not in {SL1}")
class LiveCompileAfterScriptEditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        check_scripts_are_this_checkouts()

    def setUp(self):
        tmp = Path(win32api.GetLongPathName(tempfile.mkdtemp(prefix="compile_refresh_live_")))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.project = str(one_sheet_project(tmp))
        self.sheet = str(tmp / SHEET)
        self.addCleanup(close_all_under, str(tmp))
        script(f"Obj1 := GetWorkspace.DM_OpenProject('{self.project}', True);\n"
               f"Obj2 := OpenSchDoc('{self.sheet}');\n"
               "ResultText := 'open';")

    def run_on_sheet(self, body):
        return script(body.replace("{sheet}", self.sheet)).strip()

    def set_modified(self, value):
        self.run_on_sheet(f"Client.GetDocumentByPath('{{sheet}}').SetModified({value});\nResultText := 'set';")

    def is_modified(self):
        return self.run_on_sheet("ResultText := BoolToStr(Client.GetDocumentByPath('{sheet}').Modified, True);") \
            == "True"

    def footprints(self):
        parts = json.loads(asyncio.run(main.get_project_components(None, project_path=self.project)))
        self.assertIn("components", parts, parts)
        return {c["designator"]: c["footprint"] for c in parts["components"]}

    def erc_groups(self):
        erc = json.loads(asyncio.run(main.get_erc_violations(None, project_path=self.project)))
        self.assertIn("groups", erc, erc)
        if erc.get("full_list"):
            self.addCleanup(Path(erc["full_list"]).unlink, missing_ok=True)
        return {g["type"]: g["count"] for g in erc["groups"]}

    def test_a_footprint_a_script_set_is_compiled(self):
        self.assertEqual(self.footprints()["D1"], "DO214")
        # As sessions did it: the part's current PCB model renamed inside
        # PreProcess/PostProcess, the change notices sent for the model only
        out = self.run_on_sheet("""var
  Doc, It, C, MIt, M : IDispatch;
begin
  Doc := OpenSchDoc('{sheet}');
  It := Doc.SchIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eSchComponent));
  C := It.FirstSchObject;
  while C <> nil do
  begin
    if C.Designator.Text = 'D1' then
    begin
      SchServer.ProcessControl.PreProcess(Doc, '');
      MIt := C.SchIterator_Create;
      MIt.AddFilter_ObjectSet(MkSet(eImplementation));
      M := MIt.FirstSchObject;
      while M <> nil do
      begin
        if (M.ModelType = 'PCBLIB') and M.IsCurrent then
        begin
          SchServer.RobotManager.SendMessage(M.I_ObjectAddress, c_BroadCast, SCHM_BeginModify, c_NoEventData);
          M.ModelName := 'A48_NEW_FP';
          SchServer.RobotManager.SendMessage(M.I_ObjectAddress, c_BroadCast, SCHM_EndModify, c_NoEventData);
          S1 := S1 + 'set';
        end;
        M := MIt.NextSchObject;
      end;
      C.SchIterator_Destroy(MIt);
      SchServer.ProcessControl.PostProcess(Doc, '');
    end;
    C := It.NextSchObject;
  end;
  Doc.SchIterator_Destroy(It);
  ResultText := S1;
end;""")
        self.assertEqual(out, "set")
        self.set_modified("False")
        self.assertEqual(self.footprints()["D1"], "A48_NEW_FP",
                         "the compile reads the footprint from before the script's edit")
        self.assertFalse(self.is_modified(), "the call left the sheet marked modified")

    def test_a_sheet_size_a_script_set_is_compiled(self):
        self.assertNotIn(BOUNDS, self.erc_groups())
        # The sheet made 2000 x 2000 mil by setting its properties directly:
        # most of the drawing is then outside it
        self.run_on_sheet("Obj1 := OpenSchDoc('{sheet}');\n"
                          "Obj1.UseCustomSheet := True;\nObj1.CustomX := 2000;\nObj1.CustomY := 2000;\n"
                          "ResultText := 'resized';")
        self.set_modified("True")
        groups = self.erc_groups()
        self.assertGreater(groups.get(BOUNDS, 0), 100,
                           f"the compile reads the sheet size from before the script's edit: {groups}")
        self.assertTrue(self.is_modified(), "the call cleared the sheet's modified flag")

    def test_the_users_last_undo_step_stays_the_last(self):
        # A rename made with undo, then a compile call: one Undo takes the
        # rename back, so the call put nothing in the sheet's undo history
        label = """var Doc, It, L : IDispatch;
begin
  Doc := OpenSchDoc('{sheet}');
  It := Doc.SchIterator_Create;
  It.AddFilter_ObjectSet(MkSet(eNetLabel));
  L := It.FirstSchObject;
  %s
  ResultText := L.Text;
  Doc.SchIterator_Destroy(It);
end;"""
        renamed = self.run_on_sheet(label % """SchServer.ProcessControl.PreProcess(Doc, '');
  SchServer.RobotManager.SendMessage(L.I_ObjectAddress, c_BroadCast, SCHM_BeginModify, c_NoEventData);
  L.Text := 'A48_RENAMED';
  SchServer.RobotManager.SendMessage(L.I_ObjectAddress, c_BroadCast, SCHM_EndModify, c_NoEventData);
  SchServer.ProcessControl.PostProcess(Doc, '');""")
        self.assertEqual(renamed, "A48_RENAMED")
        self.footprints()
        undone = self.run_on_sheet(label % """Client.ShowDocument(Client.GetDocumentByPath('{sheet}'));
  ResetParameters;
  RunProcess('Sch:Undo');""")
        self.assertNotEqual(undone, "A48_RENAMED", "one Undo after the call no longer takes back the rename")


if __name__ == "__main__":
    unittest.main()
