"""Live test of get_pcb_layer_stackup in a running Altium Designer.

It drives Altium, so it is not in the offline set CI runs. With Altium open:

    set ALTIUM_LIVE=1
    python -m unittest tests.test_live_layer_stackup -v      (from server/)

It runs this checkout's scripts (no "script_path" may be set in the config),
opens its own boards and closes them unsaved: a new board, and a copy of the
16-layer "Mini PC" example Altium installs (skipped when it is not there).
The documents already open in Altium are not touched.
"""
import asyncio
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

LIVE = os.environ.get("ALTIUM_LIVE") == "1"
MINI_PC = Path(r"C:\Users\Public\Documents\Altium\AD25\Examples\Mini PC"
               r"\Mini PC - Motherboard\MiniPC.PcbDoc")

if LIVE:
    import main  # noqa: E402


def _script(body):
    """Run a sandbox script through the server's own tool, return ResultText."""
    out = json.loads(asyncio.run(main.run_altium_script(None, body, 180)))
    if not out.get("success"):
        raise AssertionError(f"sandbox script failed: {json.dumps(out, indent=2)}")
    return out["result"]


def _stackup():
    out = json.loads(asyncio.run(main.get_pcb_layer_stackup(None)))
    if "error" in out:
        raise AssertionError(out["error"])
    return out


def _close(name):
    _script(f"Obj1 := Client.GetDocumentByPath('{name}');\n"
            "if Obj1 <> nil then\nbegin\n"
            "    Obj1.SetModified(False);\n"
            "    Client.CloseDocument(Obj1);\n"
            "end;\n"
            "ResultText := 'closed';")


def _thicknesses(layers):
    return [l["copper_thickness_mils"] if l["material_type"] == "Copper"
            else l["dielectric_height_mils"] for l in layers]


@unittest.skipUnless(LIVE, "drives Altium: set ALTIUM_LIVE=1 with Altium Designer open")
class LiveLayerStackupTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        scripts = Path(main.altium_bridge.config.script_path).resolve()
        here = Path(main.__file__).resolve().parent
        if here not in scripts.parents:
            raise unittest.SkipTest(f"script_path {scripts} is not this checkout's; the test "
                                    "would run other scripts than the ones under test")

    def test_new_board(self):
        """Altium's default 2-layer stack: a 12.6 mil FR-4 dielectric and two masks."""
        name = _script("CreateNewDocumentFromDocumentKind('PCB');\n"
                       "Obj1 := Client.CurrentView.OwnerDocument;\n"
                       "ResultText := Obj1.FileName;").strip()
        try:
            out = _stackup()
        finally:
            _close(name)
        self.assertEqual(out["board_name"], name)
        layers = out["layers"]
        self.assertEqual([l["layer_name"] for l in layers],
                         ["Top Solder", "Top Layer", "Dielectric 1", "Bottom Layer", "Bottom Solder"])
        self.assertEqual([l["material_type"] for l in layers],
                         ["Dielectric", "Copper", "Dielectric", "Copper", "Dielectric"])
        self.assertEqual([l["layer_order"] for l in layers], [1, 2, 3, 4, 5])
        for got, want in zip(_thicknesses(layers), [0.4, 1.4, 12.6, 1.4, 0.4]):
            self.assertAlmostEqual(got, want, places=3)
        core = layers[2]
        self.assertEqual(core["dielectric_material"], "FR-4")
        self.assertAlmostEqual(core["dielectric_constant"], 4.8, places=3)
        self.assertEqual(layers[0]["dielectric_material"], "Solder Resist")
        self.assertAlmostEqual(layers[0]["dielectric_constant"], 3.5, places=3)
        self.assertEqual(out["total_layers"], 2)
        self.assertEqual(out["dielectric_layers"], 3)
        self.assertAlmostEqual(out["total_thickness_mils"], 16.2, places=3)
        self.assertAlmostEqual(out["total_thickness_mm"], 16.2 * 0.0254, places=5)

    @unittest.skipUnless(MINI_PC.exists(), f"Altium's example board is not at {MINI_PC}")
    def test_16_layer_example(self):
        """Cores and prepregs alternate between 16 copper layers, in stack order."""
        tmp = Path(tempfile.mkdtemp(prefix="stackup_live_"))
        board = tmp / "stackup_example.PcbDoc"
        shutil.copyfile(MINI_PC, board)
        try:
            _script(f"Obj1 := Client.OpenDocument('PCB', '{board}');\n"
                    "Client.ShowDocument(Obj1);\n"
                    "ResultText := Obj1.FileName;")
            try:
                out = _stackup()
            finally:
                _close(str(board))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        self.assertEqual(out["board_name"], board.name)
        layers = out["layers"]
        kinds = [l["material_type"] for l in layers]
        # mask, then copper and dielectric in turn, then mask
        self.assertEqual(kinds, ["Dielectric"] + ["Copper", "Dielectric"] * 15 + ["Copper", "Dielectric"])
        self.assertEqual(out["total_layers"], 16)
        self.assertEqual(out["dielectric_layers"], 17)
        inner = [l["dielectric_type"] for l in layers[2:-2:2]]
        self.assertEqual(inner, ["Core", "PrePreg"] * 7 + ["Core"])
        self.assertEqual(layers[1]["layer_id"], "Top Layer")
        self.assertEqual(layers[-2]["layer_id"], "Bottom Layer")
        self.assertAlmostEqual(out["total_thickness_mils"], sum(_thicknesses(layers)), places=3)
        # 2 x 1.7717 + 14 x 0.6693 copper, 6 x 3.937 + 9 x 4.7244 dielectric, 2 x 0.3937 mask
        self.assertAlmostEqual(out["total_thickness_mils"], 79.843, places=2)


if __name__ == "__main__":
    unittest.main()
