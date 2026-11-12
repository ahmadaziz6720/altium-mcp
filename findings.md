# Findings

What sessions found using `altium-mcp`, this fork's server, written by them without being
asked, one dated entry per session at the end of this file. Those sessions mostly run in
other repos: by the owner's Git rule they write here and never commit. The paragraph that
tells them to is in the owner's global `CLAUDE.md`.

What an entry holds:

- a call that failed, or that reported success while the result was wrong (these matter
  most: the server's value is that its checks can be trusted);
- a workaround the session needed, and what it cost (calls, a document thrown away, an
  undo in Altium);
- a tool or option that was missing for the task at hand;
- a call pattern that wasted tokens (many calls for one thing, a large result read once);
- what the session learned about using the server on Altium Designer 25 that the next
  session should know.

Check [`open_items.md`](open_items.md) first: when a point bears on an item, name it
(`A3, met again`). A session with no findings writes no entry.

One entry: heading `**YYYY-MM-DD: <what was done, in general terms>**`, then a line naming
the release (the `bin\<v>-<stamp>` folder that `get_server_status` shows in `script_path`),
then numbered points. Each point names the tool, what happened against what was expected,
the workaround if any, and whether the server reported success.

**The problem only, never its source** (owner's rule; this fork is public). An entry does
not say where the problem was met:

- no repo, project or client name;
- no file, schematic, board, library or part number of the owner's, and no path;
- no report, section or session reference.

It describes the design in general terms ("a 4-layer board with a split ground plane",
"a schematic symbol with 120 pins on four sides"). It gives the tool calls and the numbers
that show the fault, and nothing that identifies the design. The same holds for the items
in `open_items.md` and for an issue or PR sent upstream.

**Sorting.** A session in this repo sorts the entries into `open_items.md`, and adds a line
under each entry it sorted, naming where each point went by the entry's own numbers:
`Sorted into A6 (1, 3); A2 (2). Not filed (4): one-off.` Nothing here is decided until it
is an item there. An entry is not edited once its session has ended, and none is deleted.

---

**2026-11-12: scenario test of a release on a small 2-layer board (read, edit, silkscreen, footprint library, output job)**

Release `bin\0.7.0-20261112-101037` (build line `0.7.0-ad25-20261112-101037 fb7cb6d`).

1. `get_server_status` (A1, held): returns `version` 0.7.0 and `build` equal to the line in
   the release folder's `BUILD.txt`; `script_path` in the same folder.
2. `get_pcb_layer_stackup` reports success with a wrong stackup. On a 2-layer board with a
   60 mil FR-4 core and 0.4 mil solder mask on each side, it returns `total_layers` 2,
   `total_thickness_mils` 2.8 (the two 1.4 mil coppers only), and `dielectric_type`
   "No Dielectric", height 0, for both copper layers. The core and both masks are missing.
   A script walking `Board.LayerStack_V7` with `First/Next(eLayerClass_Dielectric)` lists all
   three (core h=60 mil, er=4.8, FR-4; masks h=0.4 mil, er=3.5).
3. `get_unrouted_connections` reports success with `connection_count` 0 for a net that is
   open. After `delete_pcb_objects` removed the only track between two pads of a 3-pad net,
   Altium's batch DRC (`run_drc`) reported one Un-Routed Net violation for that net, while
   `get_unrouted_connections(nets=[that net])` returned 0, four times, also after saving,
   closing and reopening the board. A script doing what the tool does (`Board.AnalyzeNet`,
   then a board iterator on `eConnectionObject`, all layers) finds 0 connection objects on
   that board; every net has `ConnectsVisible` true and the connection layer is displayed.
   The board was shown in 3D view throughout; whether that matters was not checked. Not
   seen on a board that had an open connection from the start: both boards tried were fully
   routed. Workaround: `run_drc(nets=[...])`, which gives the open connection with its ends.
4. `get_unrouted_connections` leaves the board marked modified: on a freshly opened board,
   `get_project_info` gave state "open" before the call and "modified" after it, with the
   per-layer primitive counts of `get_board_summary` unchanged. A read call then makes Altium
   ask to save on close, and fails the "nothing unsaved" check that `get_project_info` is
   meant for. Likely the `AnalyzeNet` pass.
5. Read calls write into the project folder: `run_drc` writes `Design Rule Check - <board>.drc`
   and `.html` beside the board or in `Project Outputs for <project>` (documented, but no
   option to send the report elsewhere), and compiling (`get_erc_violations`,
   `get_project_components`) leaves a `<project>.PrjPcbStructure`. On a reference project that
   must stay untouched they had to be deleted by hand afterwards.
6. Wasteful: `get_layout(designators=[two small chip parts], include_touching=true)` returned
   8.6k characters, most of it the full outlines of two board-wide ground pours that only
   reach into the area. `get_pcb_rules` is 9.3k characters for 38 rules (each rule's scope
   repeated in `descriptor` and in `filter1`/`filter2`).
7. Missing tool: no way to make a PcbLib from a board. `RunProcess('PCB:MakeLibrary')` and
   `Client.SendMessage('PCB:MakeLibrary', ...)` from `run_altium_script` returned success and
   did nothing (no document, no dialog); it was done by hand through the menu.

Sorted into A1 (1); A2 (2); A3 (3); A4 (4); A5 (5); A6, A7 (6); A8 (7).

**2026-11-12: fixing three read tools, with live tests on new boards and copies of Altium's examples**

A checkout of `ad25` driven from its live tests (`ALTIUM_LIVE=1`), not a release.

1. A3, met again, on a copy of a small example board Altium installs, freshly opened
   (the view not checked): every free track, arc and via of a 2-pad signal net removed by a script,
   then `get_unrouted_connections(nets=[it])` with the nets analyzed returned
   `connection_count` 0 and success, while `run_drc(nets=[it])` gave the one Un-Routed Net
   between its two pads. A board iterator on `eConnectionObject` found none on the whole
   board, before and after `AnalyzeNet`. On a 16-layer example board the same iterator
   found 564 after one net was analyzed.
2. `run_altium_script` refused a script before running it, "'Net' is not declared", for a
   leading `var Board : IPCB_Board; Net : IPCB_Net; i : Integer;` on one line: the check
   reads only the first declaration of a line. One declaration per line passed.
3. A new PCB document saved by script with `IServerDocument.DoSafeChangeFileNameAndSave(path,
   'PCB')` returned True and wrote no file; `DoFileSave('PCB')` after it also returned True
   and wrote nothing. `DoFileSave('')` on a board opened from a file did write it.
4. A net a script creates (`PCBObjectFactory(eNetObject, ...)`, `AddPCBObject`, pads and
   tracks given it) holds until the board is saved: after save, close and reopen the pads
   and tracks have no net, and the net is gone. A test that needs a net uses one the board
   already has.
5. Three opens of a 16-layer example board in one Altium run brought Altium to 3.7 GB
   (7 GB machine), and the server refused every further call until Altium was restarted
   (its memory guard, as designed).

Sorted into A3 (1); A9 (2). Not filed (3, 4, 5): lessons for live tests, in the
paragraph on live tests at the top of `open_items.md`.

**2026-11-12: scenario test of a release fixing four read tools, on a small 2-layer board (read, edit, short checks of silkscreen, footprint library, output job)**

Release `bin\0.7.0-20261112-120520` (build line `0.7.0-ad25-20261112-120520 31e7047`).

1. `get_pcb_layer_stackup` (A2, held): the stack top to bottom, mask 0.4 / copper 1.4 /
   core 60 (FR-4, er 4.8) / copper 1.4 / mask 0.4, `total_thickness_mils` 63.6,
   `dielectric_layers` 3. Matches a `LayerStack_V7` walk; the core's type is unset there
   (0), so "Dielectric" is right.
2. `get_pcb_rules` (A7, held): 38 rules, the scope once in `filter1`/`filter2`, `filter2`
   only on binary rules, `constraint` without the scope. The reply went from 9.3k to 8.5k
   characters (about 9 % less, some 220 per rule): what is left is mostly the key names and
   the indentation repeated on every rule, not the scope.
3. `get_unrouted_connections` (A4, held): on a freshly opened board `analyzed` false and
   the board still "open" in `get_project_info` after the call; on a board with unsaved
   changes `analyzed` true.
4. `get_layout(designators=[two small chip parts], include_touching=true)` (A6, held):
   5.0k characters, was 8.6k; the two board-wide ground pours come as `beyond_area`
   entries (net, layer, bbox, vertex count), the tracks and vias as before.
5. `run_drc` leaves the board marked modified. On a freshly reopened board, after
   `get_board_summary`, `get_pcb_layer_stackup` and `get_all_nets` the state was still
   "open"; after one `run_drc` it was "modified". It happened on a call that reported
   `ran` false too (point 6), so it is something the tool does before Altium's check runs.
   Same effect as A4: a read makes Altium ask to save on close and fails the "nothing
   unsaved" check. Whether Altium's own DRC from the menu also marks the board was not
   checked. Workaround: close the board with its modified flag cleared.
6. `run_drc` returned `success` false, `ran` false, "the Design Rule Checker dialog never
   appeared", on the first DRC after the board was closed unsaved and reopened by script;
   the same call repeated at once ran normally. Reported as a failure, as it should be, but
   the reply still carried `report` with its per-rule counts and `violation_count` 4: that
   report was the file a previous run had left, not marked as stale, and it looks like a
   result. Workaround: call again.
7. A3, met again, without `AnalyzeNet`: a board saved with one connection open (DRC gave
   1 Un-Routed Net before the save), closed and reopened, then
   `get_unrouted_connections(nets=[it])` returned `analyzed` false and `connection_count` 0,
   and a board iterator on `eConnectionObject` found none on the whole board. Before the
   save, on the modified board, `analyzed` true also gave 0. The board was in 3D view
   throughout (2D not tried). So the ratsnest built at open lacks the connection objects
   too, not only the analyzed one.

Sorted into A2 (1); A7 (2); A4 (3); A6 (4); A17 (5); A18 (6); A3 (7).
