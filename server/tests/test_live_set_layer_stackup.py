"""Live test of set_pcb_layer_stackup in a running Altium Designer.

It drives Altium, so it is not in the offline set CI runs. With Altium open:

    set ALTIUM_LIVE=1
    python -m unittest tests.test_live_set_layer_stackup -v      (from server/)

It runs this checkout's scripts and works on copies of two boards of the
examples Altium installs, in a temporary folder, closed unsaved: the 2-layer
SpiritLevel-SL1 board and the 4-layer WiFi board of the Mini PC example, whose
two inner layers hold copper. A stack set is read back through Altium: the
board's own stack read again (get_pcb_layer_stackup), and after a save, a
close and a reopen of the copy.
"""
import copy
import shutil
import tempfile
import unittest
from pathlib import Path

import win32api

from tests.live_altium import (LIVE, SKIP_REASON, check_scripts_are_this_checkouts, close, close_all_under,
                               modified, open_board, script, tool)

if LIVE:
    import main  # noqa: E402

EXAMPLES = Path(r"C:\Users\Public\Documents\Altium\AD25\Examples")
SL1 = EXAMPLES / "SpiritLevel-SL1" / "SL1 Xilinx Spartan-IIE PQ208 Rev1.02.PcbDoc"
WIFI = EXAMPLES / "Mini PC" / "Mini PC - WiFi" / "WiFi.PcbDoc"

# What a stack entry is compared on: the keys a set gives, as the read gives them
VALUE_KEYS = ("material_type", "layer_name", "copper_type", "copper_thickness_mils",
              "dielectric_type", "dielectric_material", "dielectric_height_mils", "dielectric_constant")


def stack():
    """The focused board's stack, as get_pcb_layer_stackup reads it."""
    out = tool(main.get_pcb_layer_stackup(None))
    if "error" in out:
        raise AssertionError(out["error"])
    return out


def save(path):
    out = script(f"Obj1 := Client.GetDocumentByPath('{path}');\n"
                 "ResultText := BoolToStr(Obj1.DoFileSave(''), True);").strip()
    if out != "True":
        raise AssertionError(f"could not save {path}")


def signal_layer_count(path):
    """Altium's own count of the board's signal layers (planes not counted)."""
    return int(script(f"var B : IPCB_Board;\nbegin\nB := PCBServer.GetPCBBoardByPath('{path}');\n"
                      "ResultText := IntToStr(B.LayerStack_V7.SignalLayerCount);\nend;").strip())


def track_on(path, layer_name):
    """Put a 10 mil track on the copper layer named layer_name; True when it
    landed there, which a layer that is not a routable copper layer refuses."""
    out = script(f"""var
    B : IPCB_Board;
    L : IPCB_LayerObject_V7;
    T : IPCB_Track;
    Layer : Integer;
begin
B := PCBServer.GetPCBBoardByPath('{path}');
Layer := 0;
L := B.LayerStack_V7.First(eLayerClass_Electrical);
while L <> nil do
begin
    if L.Name = '{layer_name}' then Layer := L.LayerID;
    L := B.LayerStack_V7.Next(eLayerClass_Electrical, L);
end;
if Layer = 0 then
    ResultText := 'no layer'
else
begin
    PCBServer.PreProcess;
    T := PCBServer.PCBObjectFactory(eTrackObject, eNoDimension, eCreate_Default);
    T.x1 := B.XOrigin + MilsToCoord(100); T.y1 := B.YOrigin + MilsToCoord(100);
    T.x2 := B.XOrigin + MilsToCoord(400); T.y2 := B.YOrigin + MilsToCoord(100);
    T.Width := MilsToCoord(10);
    T.Layer := Layer;
    B.AddPCBObject(T);
    PCBServer.PostProcess;
    ResultText := BoolToStr((T.Layer = Layer) and B.LayerStack_V7.LayerObject_V7[Layer].UsedByPrims, True);
end;
end;""").strip()
    return out == "True"


@unittest.skipUnless(LIVE, SKIP_REASON)
class LiveSetLayerStackupTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        check_scripts_are_this_checkouts()

    def setUp(self):
        # Altium is given the long path: the one it reports back
        self.tmp = Path(win32api.GetLongPathName(tempfile.mkdtemp(prefix="stackset_live_")))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        # Everything opened under it, closed unsaved
        self.addCleanup(close_all_under, str(self.tmp))

    def copy_of(self, src, name):
        board = str(self.tmp / name)
        shutil.copyfile(src, board)
        open_board(board)
        return board

    def reopen(self, board):
        save(board)
        close(board)
        open_board(board)

    def same_stack(self, wanted, layers, what):
        """Each wanted entry's keys equal the read's entry at its place."""
        self.assertEqual(len(layers), len(wanted), f"{what}: {layers}")
        for i, (w, got) in enumerate(zip(wanted, layers)):
            for key in VALUE_KEYS:
                if key not in w:
                    continue
                self.assertIn(key, got, f"{what}, entry {i + 1}: {got}")
                if isinstance(w[key], float):
                    self.assertAlmostEqual(got[key], w[key], places=4, msg=f"{what}, entry {i + 1}, {key}")
                else:
                    self.assertEqual(got[key], w[key], f"{what}, entry {i + 1}, {key}")

    @unittest.skipUnless(SL1.exists(), f"Altium's example board is not at {SL1}")
    def test_presets_on_a_two_layer_board(self):
        """2 to 4 layers by the 7628 preset, read back and after a reopen; back to 2."""
        board = self.copy_of(SL1, "presets.PcbDoc")
        self.assertFalse(modified(board))
        out = tool(main.set_pcb_layer_stackup(None, preset="4_layer_1.6mm_7628", board_path=board))
        self.assertTrue(out.get("success"), out)
        self.assertTrue(out["board_modified"], out)
        self.assertEqual(len(out["added"]), 2, out)
        self.assertEqual(out["removed"], [], out)
        wanted = out["requested"]
        self.assertEqual([l["material_type"] for l in wanted],
                         ["Dielectric", "Copper", "Dielectric", "Copper", "Dielectric", "Copper",
                          "Dielectric", "Copper", "Dielectric"])
        self.assertEqual([l.get("dielectric_type") for l in wanted[2::2][:3]], ["PrePreg", "Core", "PrePreg"])
        self.assertTrue(modified(board))

        now = stack()
        self.same_stack(wanted, now["layers"], "read back")
        self.assertEqual(now["total_layers"], 4)
        self.assertEqual([l.get("layer_id") for l in now["layers"] if l["material_type"] == "Copper"],
                         ["Top Layer", "Mid Layer 1", "Mid Layer 2", "Bottom Layer"])
        self.assertEqual([l.get("copper_type") for l in now["layers"] if l["material_type"] == "Copper"],
                         ["Signal"] * 4)
        # 1.6 mm of copper and dielectric, and the two 0.4 mil masks
        self.assertAlmostEqual(now["total_thickness_mils"], 62.9922 + 0.8, places=3)
        self.assertEqual(signal_layer_count(board), 4)

        self.reopen(board)
        self.assertFalse(modified(board))
        again = stack()
        self.same_stack(wanted, again["layers"], "after a save and reopen")
        self.assertEqual(again["layers"], now["layers"])

        # The new inner layers are routable: a track lands on one
        inner = [l["layer_name"] for l in again["layers"] if l.get("layer_id") == "Mid Layer 1"][0]
        self.assertTrue(track_on(board, inner), f"a track on {inner}")
        save(board)

        # Back to two layers: the empty inner layer goes, the one with the track is refused
        out = tool(main.set_pcb_layer_stackup(None, preset="2_layer_1.6mm", board_path=board))
        self.assertFalse(out.get("success"), out)
        self.assertIn(inner, out["error"])
        self.assertEqual([u["layer_id"] for u in out["layers_in_use"]], ["Mid Layer 1"], out)
        self.assertEqual(out["layers_in_use"][0]["objects"], 1, out)
        self.assertEqual(stack()["layers"], again["layers"], "a refused set leaves the stack")
        self.assertFalse(modified(board), "a refused set leaves the board unmodified")
        script(f"""var B : IPCB_Board; It : IPCB_BoardIterator; P : IPCB_Primitive;
begin
B := PCBServer.GetPCBBoardByPath('{board}');
It := B.BoardIterator_Create;
It.AddFilter_ObjectSet(MkSet(eTrackObject));
It.AddFilter_LayerSet(MkSet(2));
It.AddFilter_Method(eProcessAll);
P := It.FirstPCBObject;
while P <> nil do
begin
    if P.Layer = 2 then B.RemovePCBObject(P);
    P := It.NextPCBObject;
end;
B.BoardIterator_Destroy(It);
ResultText := 'removed';
end;""")
        out = tool(main.set_pcb_layer_stackup(None, preset="2_layer_1.6mm", board_path=board))
        self.assertTrue(out.get("success"), out)
        self.assertEqual(sorted(r["layer_id"] for r in out["removed"]), ["Mid Layer 1", "Mid Layer 2"])
        two = stack()
        self.same_stack(out["requested"], two["layers"], "two layers again")
        self.assertEqual(two["total_layers"], 2)
        self.assertAlmostEqual(two["total_thickness_mils"], 62.9922 + 0.8, places=3)
        self.reopen(board)
        self.assertEqual(stack()["layers"], two["layers"], "two layers after a reopen")

    @unittest.skipUnless(SL1.exists(), f"Altium's example board is not at {SL1}")
    def test_read_then_set_is_no_change(self):
        """The read's own list set back changes nothing and leaves the board unmodified."""
        board = self.copy_of(SL1, "same.PcbDoc")
        before = stack()
        out = tool(main.set_pcb_layer_stackup(None, layers=copy.deepcopy(before["layers"]), board_path=board))
        self.assertTrue(out.get("success"), out)
        self.assertEqual(out["changed"], 0, out)
        self.assertEqual((out["added"], out["removed"]), ([], []), out)
        self.assertFalse(out["board_modified"], out)
        self.assertFalse(modified(board))
        self.assertEqual(stack()["layers"], before["layers"])

    @unittest.skipUnless(WIFI.exists(), f"Altium's example board is not at {WIFI}")
    def test_edit_a_four_layer_board_with_copper_inside(self):
        """Refused where it would drop copper; a plane added and values set where it would not."""
        board = self.copy_of(WIFI, "edit.PcbDoc")
        before = stack()
        inner = [l["layer_name"] for l in before["layers"] if l.get("layer_id", "").startswith("Mid")]
        self.assertEqual(len(inner), 2)

        # Two layers would remove both inner layers, which hold copper: refused, a dry run too
        for dry in (True, False):
            out = tool(main.set_pcb_layer_stackup(None, preset="2_layer_1.6mm", dry_run=dry, board_path=board))
            self.assertFalse(out.get("success"), out)
            for name in inner:
                self.assertIn(name, out["error"])
            self.assertEqual(sorted(u["layer_id"] for u in out["layers_in_use"]), ["Mid Layer 1", "Mid Layer 2"])
            self.assertTrue(all(u["objects"] > 0 for u in out["layers_in_use"]), out)
        self.assertEqual(stack()["layers"], before["layers"])
        self.assertFalse(modified(board))

        # The read, edited: a plane and its dielectric between the two inner layers,
        # the first core's material, constant and height changed, the plane named
        layers = copy.deepcopy(before["layers"])
        layers[2].update(dielectric_material="FR-4 TG170", dielectric_constant=4.25,
                         dielectric_height_mils=12.5)
        layers[2].pop("dielectric_height_um")
        plane = {"material_type": "Copper", "layer_name": "GND plane", "copper_type": "Plane",
                 "copper_thickness_mils": 0.689}
        core = {"material_type": "Dielectric", "layer_name": "Core B", "dielectric_type": "Core",
                "dielectric_material": "FR-4", "dielectric_height_mils": 10.0, "dielectric_constant": 4.6}
        layers[5:5] = [plane, core]     # below int1_power and the prepreg under it

        dry = tool(main.set_pcb_layer_stackup(None, layers=layers, dry_run=True, board_path=board))
        self.assertTrue(dry.get("success"), dry)
        self.assertTrue(dry["dry_run"])
        self.assertEqual([a["copper_type"] for a in dry["would_add"]], ["Plane"], dry)
        self.assertEqual(dry["would_remove"], [], dry)
        self.assertEqual(stack()["layers"], before["layers"], "a dry run leaves the stack")
        self.assertFalse(modified(board))

        out = tool(main.set_pcb_layer_stackup(None, layers=layers, board_path=board))
        self.assertTrue(out.get("success"), out)
        self.assertTrue(out["board_modified"])
        now = stack()
        self.same_stack(layers, now["layers"], "read back")
        coppers = [l for l in now["layers"] if l["material_type"] == "Copper"]
        self.assertEqual([l["layer_name"] for l in coppers], ["TopLayer", inner[0], "GND plane", inner[1], "BottomLayer"])
        self.assertEqual(coppers[2]["copper_type"], "Plane")
        self.assertTrue(coppers[2]["layer_id"].startswith("Internal Plane"), coppers[2])
        self.assertEqual(now["total_layers"], 5)
        self.assertEqual(signal_layer_count(board), 4)

        self.reopen(board)
        again = stack()
        self.same_stack(layers, again["layers"], "after a save and reopen")
        self.assertEqual(again["layers"], now["layers"])

    def test_a_bad_list_is_refused_before_altium(self):
        out = tool(main.set_pcb_layer_stackup(None, layers=[
            {"material_type": "Copper", "copper_thickness_mils": 1.4},
            {"material_type": "Copper", "copper_thickness_mils": 1.4}]))
        self.assertFalse(out.get("success"), out)
        self.assertIn("dielectric", out["error"])


if __name__ == "__main__":
    unittest.main()
