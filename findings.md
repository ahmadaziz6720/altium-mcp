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
