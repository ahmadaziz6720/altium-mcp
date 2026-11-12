# Open Items

What sessions found in this fork's server and what was decided about each, A-numbered.
The raw entries are in [`findings.md`](findings.md); this file holds the items. Each item
names where it goes: **upstream** (an issue or PR at `coffeenmusic/altium-mcp`), **local**
(a fix on `ad25`, sent upstream as a PR when it is general), **usage** (a note for the
sessions that use the server), or **not taken**.

Three sections: **Open**, not yet fixed; **Waiting**, fixed and not yet settled (a PR not
merged, a fix not yet run in a session); **Closed**, merged upstream, run and held, or
decided against, with the record.

**Open: A3, A5, A8.**

A2, A7, A4 and A6 went out together in `build-20261112-120520` (owner, 2026-11-12), so one
scenario test covers them; A3 and A8 were not waited for. A live test uses the helpers in
`server/tests/live_altium.py` (`ALTIUM_LIVE=1`, the server's own tools, its own boards
closed unsaved).

---

## Open

**A3. `get_unrouted_connections` reports 0 for a net that is open.** After the only track
between two pads of a 3-pad net was deleted (`delete_pcb_objects`), `run_drc` gave one
Un-Routed Net violation for that net while `get_unrouted_connections(nets=[that net])`
returned `connection_count` 0, four times, also after save, close and reopen. Its pass
(`Board.AnalyzeNet` per net, then a board iterator on `eConnectionObject`) found no
connection object on the board at all; every net had `ConnectsVisible` true. The board was
in 3D view throughout, untested whether that matters; not yet seen on a board open from the
start. Local, to reproduce first: a live test that deletes a track and expects the
connection, in 2D and 3D view; if the connection objects cannot be had reliably, take the
open connections from a DRC Un-Routed Net run instead. Usage until then:
`run_drc(nets=[...])` gives the open connection with its ends. (2026-11-12, 3.)
Reproduced 2026-11-12 in a session fixing A4, on a copy of the WiFi board of Altium's Mini PC
example, freshly opened: every free track, arc and via of a 2-pad signal net removed by a
script, then `get_unrouted_connections(nets=[it])` (nets analyzed, the board being
modified) gave 0 while `run_drc(nets=[it])` gave the one Un-Routed Net between its two
pads, and a board iterator on `eConnectionObject` found none on the whole board, before
and after analyzing. On a copy of the Mini PC motherboard the same iterator found 564 after
one net was analyzed. So it is not the 3D view alone; whether a board has connection
objects at all varies.

**A5. Read calls leave files in the project folder.** `run_drc` writes `Design Rule Check -
<board>.drc` and `.html` beside the board or in `Project Outputs for <project>`, and
compiling (`get_erc_violations`, `get_project_components`) leaves `<project>.PrjPcbStructure`.
On a project that must stay untouched they were deleted by hand. Local: an option on
`run_drc` to delete its report once read (or write it elsewhere, if Altium allows), and the
compile calls to remove a `.PrjPcbStructure` they created where none was before.
(2026-11-12, 5.)

**A8. No tool to make a PcbLib from a board.** `RunProcess('PCB:MakeLibrary')` and
`Client.SendMessage('PCB:MakeLibrary', ...)` from `run_altium_script` returned success and
did nothing (no document, no dialog); it was done by hand through the menu. Local: find a
way that works from a script (the process with its parameters, or building the library from
the board's footprints through the PcbLib API), then a tool. (2026-11-12, 7.)

## Waiting

**A1. `get_server_status` reports no version or commit.** It returns the Altium exe and the
script path only, so a result cannot be tied to the code that ran. Until fixed, the release
folder in `script_path` names the stamp, and its `BUILD.txt` the commit (`CLAUDE.md`,
*Release and run*). Local: add the `manifest.json` version and the content of `BUILD.txt`
when present; upstream PR for the version part.
Fixed in `e2ecb5c`: the status adds `version` and `build` (the `BUILD.txt` line, `null` in a
checkout); offline tests in `test_build_info.py`. Released in `build-20261112-101037`.
Scenario test of that build held (2026-11-12, 1): `version` 0.7.0, `build` equal to the
release folder's `BUILD.txt`, `script_path` in the same folder. Waits for the upstream PR
for the version part.

**A2. `get_pcb_layer_stackup` reports success with the dielectrics missing.** On a 2-layer
board with a 60 mil FR-4 core and a 0.4 mil solder mask on each side it returns
`total_layers` 2, `total_thickness_mils` 2.8 (the two coppers only) and "No Dielectric",
height 0, on both copper layers. The script walks `Board.ElectricalLayerIterator` and reads
`LayerObject.Dielectric` of each copper layer, which is empty on AD25; a walk of
`Board.LayerStack_V7` with `First/Next(eLayerClass_Dielectric)` lists all three (core
h=60 mil, er=4.8, FR-4; masks h=0.4 mil, er=3.5). Local: list the stack in order from
`LayerStack_V7`, the dielectric layers as entries of their own, and sum the thickness from
them; upstream PR, the code is upstream's. (2026-11-12, 2.)
Fixed in `975fe36`: `layers` is the stack top to bottom from `LayerStack_V7`
(`eLayerClass_Physical`), copper and dielectric entries told apart by `material_type`,
overlays and pastes left out; `total_thickness_mils` sums both, `total_layers` still counts
copper, `dielectric_layers` added. A dielectric with no type set reads `eNoDielectric` on
AD25 and is given as "Dielectric". Live test `tests/test_live_layer_stackup.py`
(`ALTIUM_LIVE=1`): a new board (16.2 mil) and a copy of the 16-layer Mini PC example
(cores and prepregs in turn, 79.84 mil); 2/2 pass in AD25, 2/2 fail on the old script.
Released in `build-20261112-120520`; then the scenario test, then the upstream PR.

**A7. `get_pcb_rules` repeats each rule's scope.** 9.3k characters for 38 rules, the scope
given in `descriptor` and again in `filter1`/`filter2`. Local: one of the two, and upstream
PR. (2026-11-12, 6.)
Fixed in `c011483`: `descriptor` is given as `constraint`, the scope cut from its end
(kept whole when it does not end in the filters), and `filter2` is left out of a unary
rule (`IPCB_Rule.IsUnary`; AD25 reports the Fanout rules binary). Offline tests in
`test_pcb_rules.py`; live test `tests/test_live_pcb_rules.py` (a new board's default
rules): 1/1 pass in AD25, fails on the old script. Released in `build-20261112-120520`;
then the scenario test, then the upstream PR.

**A4. `get_unrouted_connections` leaves the board modified.** On a freshly opened board
`get_project_info` read "open" before the call and "modified" after, with no primitive count
changed. A read then makes Altium ask to save on close and fails the "nothing unsaved"
check. Likely the `AnalyzeNet` pass, which can join collinear track segments (the script's
own comment). Local: no `AnalyzeNet` on an unchanged board, or restore the document's
modified flag after the read when nothing was changed. (2026-11-12, 4.)
Fixed in `6ad21e8`: a board whose document has no unsaved change is not analyzed (its
ratsnest is the one built when it was opened); one with unsaved changes still is; the
result says which, as `analyzed`. Live test `tests/test_live_unrouted.py` on a copy of the
WiFi board of Altium's Mini PC example (on the old script the read left it modified, its
track count unchanged, as in the finding; on a copy of the Mini PC motherboard the old
script also joined 11 tracks): 1/1 pass in AD25, fails on the old script. Released in
`build-20261112-120520`; then the scenario test.

**A6. `get_layout(include_touching=true)` returns whole pours.** For two small chip parts it
returned 8.6k characters, most of it the full outlines of two board-wide ground pours that
only reach into the area. Local: a polygon or region larger than the area is given clipped
to it, or by its net, layer and bounding box with its full outline left out unless asked.
(2026-11-12, 6.)
Fixed in `6ae1092`: with `include_touching`, a pour, region or cutout whose outline (arc
edges included) reaches beyond the area goes into `beyond_area` (type, name, net, layer,
bbox, vertex count) and out of the lists `place_copper` reads; `full_outlines=true` gives
them whole, which the router's two calls ask for (regions are its obstacles). Offline
tests in `test_pcb_layout.py`; live test `tests/test_live_layout.py` (a new board, a
2000 mil pour and a small one): 2/2 pass in AD25, both fail on the old code. Released in
`build-20261112-120520`; then the scenario test.

## Closed
