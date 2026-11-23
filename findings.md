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
in `open_items.md` and `closed_items.md` and for an issue or PR sent upstream.

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

**2026-11-14: fixing `run_drc` (A17, A18), with live tests on copies of Altium's examples**

A checkout of `ad25` driven from its live tests (`ALTIUM_LIVE=1`), not a release.

1. After `run_drc`, a `run_altium_script` that takes the board from
   `PCBServer.GetCurrentPCBBoard` fails, "Undeclared identifier: BoardIterator_Create" (a
   call on nil): the report Altium opens is the focused document then.
   `PCBServer.GetPCBBoardByPath(<board>)` works.
2. A18, the variant that was reproduced: of sixteen checks of a small example board, one
   (the first after a save, close and reopen) came back `ran` false, "could not be started
   and was closed", with a report written by that very check. The "never appeared" message
   of the scenario test's entry was not seen.

Sorted into A18 (2). Not filed (1): a lesson for scripts after `run_drc`, in the paragraph
on live tests at the top of `open_items.md`.

**2026-11-14: scenario test of a release fixing `run_drc` (A17, A18), on a small 2-layer board (read, edit, short checks of project, silkscreen, footprint library, output job)**

Release `bin\0.7.0-20261114-145312` (build line `0.7.0-ad25-20261114-145312 1abba5f`).

1. `run_drc` (A17, held): on a freshly opened board with no unsaved change, after
   `get_board_summary`, `get_pcb_layer_stackup` and `get_all_nets`, one full `run_drc`
   gave `ran` true, 4 violations (the baseline), `board_modified` false; the board stayed
   "open" in `get_project_info`, Altium's own document flag read 0 by script, and a board
   iterator still found the 4 violation objects. On the same board with unsaved changes
   (5 tracks deleted) `board_modified` true, and true again after a route was added, as
   the tool says. After a save, close and reopen, `board_modified` false again.
2. `run_drc` (A18, held as far as met): three times the board was closed unsaved and
   reopened by script, and the first `run_drc` after it gave `ran` true each time, with
   the report rewritten by that call (file times after the call's start; the third time
   the old report was deleted first and the call wrote a new one). The `ran` false path
   was not met, so "no `report` when the check did not run" was not seen live.
3. New, near A17: the first `run_drc` after a project is opened leaves the **project
   file** (`.PrjPcb`) marked modified, while the board is not. Saved, the project file's
   diff is a new `[GeneratedDocument1]` section naming the DRC report's `.html` in the
   project's output folder, plus two existing sections moved. Clearing the project's
   flag and running `run_drc` again did not mark it again (the entry is there already),
   also after the output folder was deleted; a fresh open of the project marked it again
   on its first `run_drc`. `get_project_info` does not show it: `modified_document_count`
   0 and no entry for the project file, so the "nothing unsaved" check reads clean while
   closing the project would ask to save it. Workaround: close the project with its flag
   cleared (`SetModified(False)` on the `.PrjPcb` document). Expected: either the tool
   leaves the project as it found it, as it does the board, or `get_project_info` reports
   the project file's own state.
4. Wasteful, small: `run_drc(rules=[one kind])` whose filter matched 0 still returned the
   whole per-rule report, 14 rules, about 2.1k characters each call; nine `run_drc` calls
   were 26k of the session's 47k characters. A filter could narrow the report to the
   rules asked for, or the report to the rules with violations.
5. Lesson for scripts that open a project: `Client.OpenDocument('PrjPcb', <path>)` then
   opening its board put the board under "Free Documents" (`get_project_info` named Free
   Documents); `GetWorkspace.DM_OpenProject(<path>, True)` before opening the board
   works. After `run_drc`, `Client.GetDocumentByPath(<report .html path>)` returns nil
   (the report is open under a `file:///` name), so a script cannot close it that way.

Sorted into A17 (1); A18 (2); A19 (3); A20 (4). Not filed (5): a lesson for scripts that
open a project, in the paragraph on live tests at the top of `open_items.md`.

**2026-11-14: scenario test of a release fixing `run_drc` and `get_project_info` (A19, A20, A5), on a small 2-layer board (read, edit, short checks of project, silkscreen, footprint library, output job)**

Release `bin\0.7.0-20261114-163431` (build line `0.7.0-ad25-20261114-163431 d7e5c32`).

1. A19, held: on a project freshly opened with `DM_OpenProject` and its board, the first
   full `run_drc` gave `project` and `project_modified` false, `board_modified` false, and
   the `.PrjPcb` document's own flag read 0 by script; so did the filtered checks after it.
   With the project file marked modified by script beforehand, `get_project_info` gave
   `project_modified` true and `modified_document_count` 1, and `run_drc` left it modified
   (`project_modified` true). Saved, the project file gained the `[GeneratedDocument1]`
   entry naming the report's `.html` (deleted by then) and the two sections moved, as the
   item says; closed and reopened, a full `run_drc` brought up no dialog and left project
   and board unmodified.
2. A20, held: `rules=["Un-Routed Net"]` gave one report entry and `rules_omitted` 13, the
   totals (4 violations) the whole check's; `rules=["Clearance"]` the electrical clearance
   entry only, not Hole To Hole Clearance; a rule's own name (the solder mask sliver rule,
   4 violations) kept its kind's entry. A filtered call was 0.66–0.89k characters against
   2.1k before; a full call is still 5.8k (4 violations listed).
3. A5, held: after a full and three filtered `run_drc` on a project folder holding only
   the project's documents, the listing (names, sizes, times) was the same as before,
   `report.deleted` true and no `path`. `keep_report=true` kept both files and named the
   `.drc`; the next check without it gave `restored` true and the earlier report's bytes
   (hash) and times were unchanged. A board with unsaved changes (5 tracks deleted) gave
   `board_modified` true, the report narrowed and 1 unrouted connection, and still deleted
   and restored. The `.PrjPcbStructure` appeared when the project was closed, as the
   usage line says, and was deleted by hand.
4. Small, not a fault in what is checked: the folder's **own** modification time changes
   each check (the output folder is made and removed inside it), so a listing that
   includes `.` differs while every file in it is the same. Worth one line in the tool's
   description or the item, so a caller comparing folders by time is not misled.

Sorted into A19 (1); A20 (2); A5 (3, 4), all three Closed.

**2026-11-14: scenario test of a release fixing `get_unrouted_connections`, the script checker and `run_drc`'s repour message (A3, A9, A21), on a small 2-layer board (read, edit on a copy)**

Release `bin\0.7.0-20261114-180059` (build line `0.7.0-ad25-20261114-180059 bb0eeee`).

1. A3, held: on a copy of the board, the 5 tracks between two pads of a 3-pad net deleted
   with `delete_pcb_objects`, `get_unrouted_connections(nets=[it])` gave
   `connection_count` 1, its ends those of the one Un-Routed Net violation `run_drc(nets=[it])`
   gave (a track end to a pad, 34.67 mil). After save, close and reopen by script the same
   call gave the same 1, and `get_project_info` kept the board "open" (A4 still held).
   A whole-board call on the original gave 0, as the board is fully routed. `route_track`
   over the gap brought the whole board's count to 0. A second net, a bottom track between
   two vias deleted, gave its 1 connection (via to via, 240 mil), as DRC did. `analyzed` is
   gone from the result, as the item says.
2. A9, held: a script beginning `var WS : IDispatch; Prj : IDispatch; Doc : IDispatch; i, n : Integer;`
   on one line ran, all five names used. A leading line `var A : Integer; Bx, Cx : Integer; // E : Integer;`
   with `E` assigned in the body was refused before Altium was called, "'E' is not
   declared", so the comment is not read as a declaration and an undeclared name is still
   caught.
3. A21, held: the one bottom-layer track of a signal net under a board-wide bottom ground
   pour deleted, `run_drc(rules=["Un-Routed Net", "Modified Polygon"])` returned within
   seconds with `ran` true, `repour_prompt` true and the `repour_note`; Un-Routed Net 1
   and Modified Polygon 1 ("Polygon Not Repour After Edit"). The pour was unchanged (its
   region's hole count and outline points read by script the same before and after), no
   message was left up (the next script ran at once), `board_modified` true (the deletion
   unsaved), `project_modified` false. A full check after gave the same prompt and 7 in
   all: the 4 known, Un-Routed 1, Modified Polygon 1 and Net Antennae 1. On the unchanged
   board a full `run_drc` gave no `repour_prompt` field, as the item says.
4. Small, not wrong: with `nets` only, `get_unrouted_connections` gives `from_pad` and
   `to_pad` null even where an end is a pad's centre; the same connection read with
   `designators` names both ends, the track-end side by the pad that track leaves from. As
   the description says (pads are named with `designators`), but a caller reading by net
   cannot tell the pad without a second call. Naming a pad whenever an end lies on one, or
   a line in the description, would settle it.

The deleted copper and the test copy were closed unsaved (the copy saved once, with its net
routed again). `.PrjPcbStructure` appeared on closing each project, as the A5 usage line
says, and was deleted. 30 calls, 0 errors, 24k characters (9 `run_altium_script` for
opening, closing and checks; 4 `run_drc` 8.4k).

Sorted into A3 (1); A9 (2); A21 (3), all three Closed; A23, new (4).

**2026-11-14: scenario test of a release adding project and board-shape tools and a symbol's footprint (A10, A16), on a new project and library made for it, with short checks on a small 2-layer board**

Release `bin\0.7.0-20261114-210622` (build line `0.7.0-ad25-20261114-210622 b4da4cc`).

1. A10, held for the most part: `create_project` made its folder and a 29 kB project with
   no documents (`project_modified` false); a second call was refused ("not overwritten").
   With another project in focus (its board in front), `add_project_document(create=True)`
   of a new sheet gave `detached_from` that project, which kept its documents and stayed
   unmodified (flag read by script 0, its file byte-equal); a new board was not taken by
   it. A library in a sibling folder was added and saved relative (`..\<folder>\<lib>`); the
   same add again gave `already_in_project` true, `project_saved` false and a byte-equal
   project file; a missing document and an existing file with `create` were refused, the
   files byte-equal. `set_board_shape` refused a symmetric bow-tie ("encloses no area"), an
   asymmetric crossing outline ("crosses itself"), an arc with unequal radii (both radii
   given) and an empty mechanical layer, each leaving the board as it was. A rounded
   rectangle drawn out of order on Mechanical 1 (4 tracks, 4 arcs) plus a stray line became
   an 8-vertex shape, the stray line listed in `not_closed` with its ends; with one edge
   removed the call was refused, both gaps' ends given. Read back through Altium
   (`AreaSize`, `PointInPolygon`) on a reopened board: right (592.27 mm², corner out, middle
   in; a rounded 50 × 40 mm shape 1994.63 mm²).
2. Wrong, reported success: `set_board_shape` on a board just made by
   `add_project_document(create=True)` (origin at absolute 0, 0) returned the outline and
   box asked, `get_board_summary` agreed and the board was drawn right, but Altium's region
   of the outline was not: a 50 × 40 mm shape with one 5 mm rounded corner gave `AreaSize`
   1486.6 mm² (expected 1994.6), `PointInPolygon` false at (1, 1) and (25, 20) mm and true
   at (60, 20) mm, outside the board; a following plain 50 × 40 mm rectangle at
   (10, 10) mm gave 2200 mm² and (5, 5) mm inside. `Board.UpdateBoardOutline` called again
   from a script changed nothing. After save, close and reopen: 2000 mm², the points
   right, and later calls on that board right. Anything that reads the board's region in
   the same session (a pour, a DRC check against the outline, a placement test) may see a
   wrong shape. Workaround: save, close and reopen a new board before use. The live test
   checked `PointInPolygon` on a copied board, not on a new one. Bears on A10.
3. Wrong flag: `build_schematic(project_path, sheet_path)` with another project in focus
   took its sheet back from that project (`project.detached_from` names it) but left that
   project's file flag set: 0 before, modified after, twice in a row (its file not
   written). `add_project_document(create=True)` in the same state puts the flag back. The
   top-level `detached_from` of the same result is `""` while the nested one names the
   project. Bears on A10 ("a call must not change a project it was not given").
4. A16, held: a batch of three symbols, two with `FOOTPRINT` records (one model linked by
   name, its name with spaces), returned per symbol what the saved library holds when read
   apart from the server (`MODELDATAFILE0`, `ISCURRENT`); the symbol with none had no
   `footprints` entry. Specs with two `1`, a `.SchLib` as library and a relative library
   were refused, "nothing was made", and no symbol of theirs is in the saved file.
   `EDITSYMBOL` with `1` moved the mark and gave the by-name model its library; a `0` on
   the current footprint plus a new record left the new one current. `create_schematic_symbol`
   stored two footprints with the asked mark, and refused a name given twice. Parts placed
   by `build_schematic` without `footprint` carried the library's models and marks.
5. Wrong, reported success: `build_schematic` with `footprint` on a part whose library
   symbol already has a current footprint adds the named model (by name, no library) as
   current and leaves the library's current one as it is: the placed part holds two
   current PCB footprints (`IsCurrent` 1 on both through the API, `ISCURRENT=T` twice in the
   saved sheet). Rare before A16, as the server's own symbols had no footprint; now the
   common case. Expected: the footprint given becomes the only current one (the mark moved
   when the symbol already has a model of that name). Bears on A16.
6. Small: `build_schematic`'s `sheet` gives the unsaved name (`Sheet1.SchDoc`) while
   `sheet_path` gives the file it was saved as.
7. Missing, small: an empty `.SchLib` (or `.PcbLib`) cannot be made by a tool;
   `create_symbols_batch`'s `LIBRARY` needs an existing file and `add_project_document`'s
   `create` makes sheets and boards only. Done by script in three statements
   (`CreateNewDocumentFromDocumentKind('SCHLIB')`, `DoSafeChangeFileNameAndSave`, then
   `SetModified(True)` and `DoFileSave('')`); the new library went into the project in
   focus, as A10's probe found for a sheet, and that project had to be closed unsaved.

Short checks: `get_server_status` (version and build as the release), `get_project_info`
(4 documents, `project_modified` false) and `get_board_summary` (as the baseline) on the
small board; `get_layout` of an area on a copy gave the 5 tracks expected (the shared
`LayoutSegment`). The copies were closed with their flags cleared; the reference project's
`.PrjPcbStructure` appeared on closing and was deleted. 58 calls, 0 errors, 33k characters
(25 `run_altium_script` for opening, closing, a library made and checks through the API).

Sorted into A10 (1), Closed; A25, new (2); A26, new (3, 6); A16 (4), Closed; A27, new
(5); A28, new (7).

**2026-11-14: scenario test of a release keeping the foreground and answering Altium's messages (A22, A24), with short checks on a small 2-layer board**

Release `bin\0.7.0-20261114-225815` (build line `0.7.0-ad25-20261114-225815 62aa16d`).
A window of another process (a small Tk window) was put in front, and every foreground change
logged by a WinEvent hook plus a poll of `GetForegroundWindow` every 20 ms. Messages were put
up by `run_altium_script` (`MessageDlg`), as a message inside a bridge command cannot be
raised from the user's side; so the bridge's watch was met only with a message already open
when the call began.

1. A22, held for ordinary calls: `get_project_info`, `get_board_summary`,
   `run_drc(rules=[…])` (its Design Rule Checker dialog included), `get_layout`,
   `check_silkscreen`, and `run_altium_script` opening a project: Altium in front 5 to 31 ms
   per call, the foreground back on the other window after each, the server log saying
   "gave the foreground back from Altium N time(s)". `get_screenshot`: 1.15 s, as its
   description says.
2. A22, the guard is off when no window is in front at the start. `ForegroundGuard` keeps
   nothing when `GetForegroundWindow` is 0, so for that whole call Altium is not sent back:
   here it took the foreground in the middle of a `run_altium_script` (its recovery's
   `-REditScript:Stop`) and kept it 4 minutes, until it was taken back by hand; every call
   after it found Altium in front and left it there, by design. The 0 came from the server's
   own path: each probe launch of `run_altium_script`'s recovery, refused by a busy Altium,
   raised an "Information" box ("There is another instance of running, but it is busy at the
   moment…"); the guard gave the foreground back, then the box was closed and the
   foreground fell to no window, for 15 s, 15 s and 31 s. So after a call that met a message,
   the user's window no longer has the keyboard either. A guess at a fix: keep the last
   window that was not Altium's (from the previous call) when the start reads 0, and give
   it back once more after a box is closed.
3. A22, partly: a `run_altium_script` that closes one project and opens another
   (`DM_OpenProject`, `Client.OpenDocument`, `Client.ShowDocument`) left Altium in front
   about 3.4 s in all, 2.75 s of it with no foreground event at all (only the poll saw
   Altium there); the guard reacts to events only. The same opening without closing a project
   first: 7 ms.
4. A24, held: with a Yes/No message open in Altium, `get_board_summary` and `run_drc` were
   refused within a second, "Not run: '…' would wait behind a message Altium is showing that
   waits for an answer: 'Confirm' (#32770, buttons: Yes, No); its text cannot be read from
   outside Altium, see the picture …"; the picture shows the text. Small: each refusal wrote
   a new picture of the same window, and the `altium_messages` list does not reach these
   tools' replies (the error text only).
5. A24 does not reach `run_altium_script`, which answers messages its own way, against
   A24's rule for messages with choices. (a) A script's own `MessageDlg` with Yes and No is
   closed after 6 s with `WM_CLOSE`: the script gets 2 (Cancel, not one of its buttons) and
   the call reports `success` true; only `dialogs_dismissed` 1 and a picture say so.
   (b) A call made while such a message is open (left by an earlier call) is launched
   anyway, and closes that message after 6 s, answering it Cancel: the earlier script then
   ran on to its end with that answer. The call itself said "no result after 20 s … Altium
   never started the script: a script of ours was stuck and has been stopped", `recovered`
   true. Expected, as for the bridge: not run, the message named. Bears on A24, A29.
6. Wrong diagnosis: `run_altium_script` with a timeout shorter than a message's wait (4 s, the
   script waiting on its `MessageDlg`) returned after about 55 s "no result after 4 s", "The
   debugger has been stopped, so it is no longer running", `executor_wedged` true,
   `recovered` false (3 attempts); the message was not named. The script had not stopped: it
   went on to its end when its message was closed 78 s later.
7. A24 not met: an OK-only message open before a bridge call, a script waiting on it. The
   check before the launch lets an OK-only message through (it leaves it to the watch),
   Altium refuses the launch as busy (a new modal "Information" `TMessageForm` over the
   message), and the watch never runs, as it starts only once the command has started.
   `get_board_summary` ended after 46 s with "Altium did not start the command (not
   executed). A script of ours was stuck in Altium's debugger and stopping it did not free
   Altium…": the message neither pressed nor named, two boxes left open. A click posted to
   the message did nothing while the busy box was over it; the busy box first, then the
   message, closed both, and the waiting script ended ("answered 1"). A guess at a fix:
   before the launch, press a lone OK (topmost first) or refuse naming it, as for a message
   with choices. Bears on A24.

Short checks, as the baseline: `get_server_status` (version and build as the release),
`get_project_info` (4 documents, `project_modified` false), `get_board_summary`,
`run_drc(rules=["Un-Routed Net"])` (`ran` true, 4 in all, 13 rules omitted, report deleted),
on a copy `get_layout` of an area (5 tracks) and `check_silkscreen` (0 to fix, 3 checked),
`get_outjob_settings` (2 containers, 1 output). The reference project's `.PrjPcbStructure`
appeared on closing and was deleted. 22 calls, 0 errors, 15k characters (8
`run_altium_script`: opening, closing, the messages).

Sorted into A22 (1), Closed; A31, new (2, 3); A24 (4), Closed, its small point into A29;
A32, new (5, 6); A33, new (7).

**2026-11-15: scenario test of a release serving calls from a resident bridge and answering Altium's messages (A30, A29), with the read and edit scenarios on a small 2-layer board**

Release `bin\0.7.0-20261115-114630` (build line `0.7.0-ad25-20261115-114630 f1b1559`), Altium
just started (it reopened the last project by itself). A window of another process in front,
every foreground change logged by a WinEvent hook plus a 20 ms poll, as in the A22 test. The
read and edit scenarios (move a part, placement check, delete and route a track, DRC, a via,
silkscreen check) ran on a copy of the project; the copy was closed unsaved.

1. A30, held. The first call started the resident ("none of this build is running", taken in
   2.92 s), and every bridge request after it, 26 of them (24 tool calls), was taken by it in 0.015 to 0.14 s,
   no launch (`get_server_status`: `last_call.mode` `resident`, one form `this_build`
   `alive`). Results the same as before on every tool used: project and board summary, layout
   of an area, `run_drc` filtered by rule and by net (`ran` true, the counts as before,
   report deleted, project left unmodified), component data, `move_components` there and
   back, `check_placement` (4 overlaps, then 1 clearance), `delete_pcb_objects` (dry run and
   real), `get_unrouted_connections` (1 connection = the DRC's), `route_track`, `place_vias`,
   `check_silkscreen`. The form is off-screen with `WS_EX_TOOLWINDOW` and without
   `WS_EX_APPWINDOW`. It outlived a `run_altium_script` recovery (3 attempts, two
   `-REditScript:Stop`) and a message answered by hand, and served the next call. The focused
   design project is the one the tools report, not the resident's script project (which shows
   in Altium's Projects panel).
2. A30, partly: Altium still came in front during calls the resident served, each time given
   back by A22's guard. (a) The start: the main window about 1.5 s, seen by the poll only (no
   foreground event, A31), then the resident form itself took the foreground once (5 ms).
   (b) The first `get_board_summary` after the start: the main window 25 ms; the same call
   again: never. Guess: the board is shown (brought to view) the first time a tool uses it.
   (c) Each `run_drc`: the Design Rule Checker dialog, then the main window, 24 ms each, as the
   tool says. (d) After `answer_altium_message` pressed a button: the resident form, then the
   main window, about 10 ms (closing the modal hands activation to the next window of
   Altium's, the form first). Small next to the 2 s per call before; (a) and (d) are new with
   the form.
3. `run_altium_script` is not served by the resident: each call is still a launch. A script
   that closes one project and opens another kept Altium in front 2.9 s, the closing script
   1.6 s, both with no foreground event (poll only): A31 met again, and A30's gain does not
   reach this tool. Not said in A30 whether that is meant; the tool's description still says
   `RunScriptFile`.
4. A32 met again, unchanged: `run_altium_script` with a `MessageDlg` (Yes/No) and
   `timeout_seconds=4` returned after about 55 s "no result after 4 s", "The debugger has been
   stopped, so it is no longer running", `executor_wedged` true, `recovered` false (3
   attempts), the message not named; its probes raised six "Information" (busy) boxes, and
   the guard gave the foreground back 20 times in the call. The message stayed open.
5. A29, held. `answer_altium_message()` listed the open message: title "Confirm", class
   `#32770`, buttons Yes and No, a picture showing its text (the picture cuts the buttons at
   the bottom; `text` empty, as it cannot be read). With the message open, `get_board_summary`
   was refused in 0.3 s, no request written, naming the message, its picture and
   `answer_altium_message`; the refusal reused the listing's picture (one picture per window,
   A29's small point held). `button="Cancel"`: "'Confirm' has no button 'Cancel': its buttons
   are Yes, No. Nothing was pressed." (`success` false, the message still open).
   `button="No"`: `success` true, the window gone, the next `get_board_summary` taken by the
   resident in 0.031 s with the guarded window still in front.
6. Small, A29 with A32: answering the message a `run_altium_script` of this server left open
   gave `outcome` "no_command_waiting" with the note "No call of this server was waiting on it
   (it may be a script of the user's own, another session's command, or one from before this
   server started)". It was this server's script, whose call had already ended with "no
   result"; the script's own answer (its `ResultText`) is read by no one. The note could say
   so when the window belongs to a sandbox run of this server.

41 calls, 0 errors, 35k characters (3 `run_altium_script`: opening, closing, the message; 11
`get_server_status`). The reference project's `.PrjPcbStructure` appeared again on closing and
was deleted (A5's usage).

Sorted into A30 (1), Closed; A34, new (2 (b) and (d), 3 as (d), 5's picture as (c)); A31
(2 (a), 3), met again; A32 (4, 6), met again; A29 (5), Closed. 2 (c), the DRC dialog, is
as the tool says.

**2026-11-15: scenario test of a release adding stack, rule-kind, rule-preset and output-job tools (A35, A13, A14, A12), on a copy of a small 2-layer board, with short checks**

Release `bin\0.7.0-20261115-143551` (build line `0.7.0-ad25-20261115-143551 cc1015d`). The
stack, rule and output steps ran on a copy of the project, closed unsaved at the end (the
stack and rules after a save and reopen in between). The session's server was restarted
once midway (the client reconnected); same release, same resident.

1. A35, held. Before the first call a resident of tag `9f6d405bbefc` was already alive (left by
   the fork's live tests from the checkout); the release's `get_server_status` gave the same
   tag, `this_build` true, and its first call was taken by it (`mode` resident, "alive", 0.078
   s): no start, no launch. Offline, `Resident.prepare` on the checkout, on the release copy
   and on a copy of the release with every `.pas`/`.dfm`/`.PrjScr` turned to LF gave the same
   tag, `9f6d405bbefc`, all three. A second resident project of another tag (`adc685c40861`,
   no live form) was still listed in Altium's Projects panel, from an earlier build.
2. A13, held. `set_pcb_layer_stackup` with the read passed back: `changed` 0,
   `board_modified` false. Preset `4_layer_1.6mm_7628`: Mid-Layer 1 and 2 added, the stack
   read back equal (63.79 mil with masks), `differences` []; a track routed on Mid Layer 1;
   after a save and reopen, Altium's own stack lists 4 signal layers and the track is there.
   Preset `2_layer_1.6mm` then refused with `layers_in_use` (Mid Layer 1, 1 object), nothing
   changed; the track deleted, both inner layers removed, read back equal. Refused before
   Altium: a 1600 mil dielectric ("outside (0, 250.0] mil"), a `|` in a layer name, two
   dielectrics between two copper layers.
3. Small, A13: the dry run of the 4-layer preset on the 2-layer board listed in
   `would_change` only the two outer coppers' thickness (1.4 → 1.378); the call then reported
   `changed` 15. The existing core between the outer layers became the top prepreg (type,
   material, height 60 → 7.874 mil, constant 4.8 → 4.4), and the new layers' values were set:
   neither is in the dry run, which therefore understates what the call does to the
   existing dielectric.
4. A14, held for the values. All eleven new kinds made with values read back equal to those
   sent (`differential_pair` with uncoupled length, `routing_layers`, `length`,
   `matched_length`, `plane_connect`, `component_clearance` at priority 2, `silk_to_silk`,
   `silk_to_solder_mask`, `hole_to_hole` at the lowest priority, `annular_ring`,
   `solder_mask_sliver`), and in the saved file after a reopen (58 rules, the priorities as
   set). Refused: priority 99 ("out of range: 1 (the highest) to 2"), a routing layer the
   board does not have ("Its signal layers: Top Layer,Bottom Layer"), min gap above max gap.
   `create_pcb_rules_preset("jlcpcb_2layer_1oz")`: dry run without width (width in
   `skipped`, 10 `not_set` with why), then with a width: 9 rules, each read back equal, the
   priorities as the plan said (above the board's catch-all of its kind, or above a rule of
   the same scope); a second call refused by name.
5. **A14, failed in a way the read cannot show: a priority set by the tools is not what the
   batch DRC uses until the board is reopened.** A via-scoped annular ring rule of 5 mil
   (`IsVia`) was made first; the preset then put its 1.97 mil via ring rule (same scope) at
   priority 1, the 5 mil rule at 2 (`get_pcb_rules`, a board iterator's `Priority`, and
   `FindDominantRuleForObject` for every via all agree: the preset's rule dominates all 17
   vias). `run_drc` in the same session nevertheless reported 14 violations of the 5 mil rule
   ("Minimum Annular Ring: (4mil < 5mil)", every 20/12 mil via), `success` true. Saved, closed,
   reopened: the same check, 0. Then, on the reopened board, a 6 mil rule of the same scope
   made at priority 4 (the lowest; `create_pcb_rule` read back 4): `run_drc` reported 17
   violations of it, all vias, the report listing it first. So the add at 1 and the
   remove-and-add-again moves give the property the right order, but the DRC in that session
   checks by the order the rules were added (the last added winning), and a preset or a
   low-priority rule changes what the DRC reports until the board is reopened. Workaround:
   save, close and reopen before `run_drc`. A check after the moves that the DRC agrees (or
   whatever Altium call refreshes its rule order) would be needed for `priority` to hold.
6. A12, held. `write_outjob(preset="fab_jlcpcb")` on a new file, `add_project_document`, then
   `run_output_jobs(["JLCPCB Outputs"])`: the folder holds nine Gerbers (`%FSLAX44Y44*%`
   `%MOMM*%`, `.GM` outline), the plated drill file (`;FILE_FORMAT=2:5`, `INCH`; the board has
   no non-plated hole, so no `-NonPlated` file), the BOM CSV with Comment, Designator,
   Footprint, LCSC Part # (12 rows, part number empty) and the pick and place in mm.
   `make_assembly_files`: BOM 12 rows, CPL 16, all 16 named in `missing_part_number` with a
   warning, a flat zip of the nine Gerbers and the drill file, Altium's reports in
   `not_zipped`. The OutJob then edited (Gerber inch 2:5, pick and place mil, another folder)
   and opened in Altium: the run gave `outjob_reloaded` true and `%FSLAX25Y25*%` `%MOIN*%`,
   Center-X in mil; the offline step on the mil file gave the same Mid X/Y as from the mm file
   (difference 0.0000 mm), a two-row rotation table applied (an exact name +90 on Top, a
   `RESC*` pattern +180 on both: 3 parts turned), and `part_number_parameter="Comment"` filled
   the part number. Refused: a preset over the existing file without `overwrite`, a part
   number column the BOM lacks (naming the columns it has).
7. Wasteful, A12 and A13: every `write_outjob` returns the whole read of the file, about 10k
   characters, 7k of them the Gerber's 55 plotted layers listed one by one (all 30 mid layers
   and 16 planes, as the preset plots every copper layer); an edit of two settings returned
   the same 10k. `set_pcb_layer_stackup` returns `requested` and `stack` both (3 to 5k for a
   2- or 4-layer board). A summary (`plotted_layers`: "every copper layer" plus the others by
   name; the stack only when it differs) would do for a check.
8. Met at the start, source unknown: Altium had the reference project focused with
   `project_modified` true and a fifth document, `Sheet1.SchDoc` (no path, not open, not on
   disk); the project file on disk was unchanged. A new schematic taken into the focused
   project by an earlier call or test and never detached is the likely cause (A10's
   `detached_from` covers `add_project_document` and `build_schematic`); nothing in this
   session made it. Closed unsaved, the project reopened clean (4 documents, not modified).

60 calls, 0 errors, 110k characters (8 `run_altium_script`: opening, closing, checks through
Altium; the largest `get_pcb_rules` 13k, `write_outjob` 11k and 10k, `run_drc` 9k). The
reference project's `.PrjPcbStructure` was there before the session and was deleted (A5's
usage).

Sorted into A35 (1), A13 (2), A12 (6), Closed; A14 (4), Closed but its priority; A34 (e)
(1, the resident project of an earlier build listed); A37 (3), A38 (5), A39 (7), new; A26
(8), possibly met again.

**2026-11-15: scenario test of a release placing parts from integrated libraries, searching a database library and making a PCB library from a board (A40, A8), on copies of a small 2-layer board, with short checks**

Release `bin\0.7.0-20261115-172812` (build line `0.7.0-ad25-20261115-172812 de0620d`). The
resident bridge of this build was already running (`this_build` true). Short checks held:
`get_project_info`, `get_board_summary` (same as the baseline), `get_layout` of an area,
`check_silkscreen`, `get_outjob_settings`.

1. A40, held for the search. `search_dblib` on a test DbLib over CSV files (Access engine):
   three tables (two enabled, one by `UserWhereText`, one by `Key=`), listed with their key;
   a term found in the enabled tables only, with `all_tables` also in the disabled one; a
   quote (`O'Brien`), a `%` and an `_` in the term taken literally; `part_number` found in an
   enabled and in a disabled table, all fields; an unknown part number `null` with a note; an
   unknown `table` refused naming the tables; a table the database lacks reported with the
   engine's message; no path with no DbLib installed refused ("no DbLib is installed in
   Altium"). `get_installed_libraries` listed Altium's seven installed libraries, all
   `IntLib`, `exists` true.
2. A40, held for placing. `build_schematic` with `project_path`: two parts from one installed
   `.IntLib` (one rotated 180 and mirrored, with a comment), one from another `.IntLib`, one
   from a `.SchLib`. Read back through Altium and from the saved file: each `.IntLib` part
   has its library reference, the library's file name as library name, the Design Item ID,
   the place, rotation, mirror and comment asked for, and the library's models (footprint
   current, simulation, signal integrity); every pin's connection point equal to `pin_map`.
   `edit_schematic` `place_component` from both `.IntLib`s (rotation 90 with mirror, a
   comment), saved, reopened: equal. A symbol not in the `.IntLib` reported per operation
   ("not found in …"), the others applied; a `.PcbLib` refused before Altium, a missing
   `.IntLib` and a bare file name reported as "library not found". `build_schematic` with a
   missing `.IntLib` refused before Altium.
3. **Found, A26 and its "possibly met again" explained: `build_schematic` puts its new sheet
   into whatever project is focused, also without `project_path`.** With a saved, unmodified
   project focused (its board in front), `build_schematic(parts)` with no `project_path`, the
   case the description calls "a new, unsaved free document", left a `Sheet1.SchDoc` (no
   path) in that project's documents and its file flag set (0 → -1); `success` true,
   `detached_from` "". The same with `project_path` but a part missing: the call failed
   (`missing_parts` in the error string), and the unsaved sheet stayed in the focused project
   with the flag set, not mentioned. With `project_path` and every part found, the sheet was
   taken out of the focused project (`project.detached_from` names it) but that project's
   flag stayed set (A26 as reported). This is the `Sheet1.SchDoc` met at the start of this
   session and of the last one in the reference project: a sheet built by an earlier call
   or live test while it was focused. Expected: the sheet in no project (Free Documents)
   without `project_path`, in none after a failure, and the focused project's flag as found
   in all three cases.
4. A8, held. `make_pcblib_from_board` on the open board in front (16 components, 12
   patterns): 12 footprints in the saved file, pads and primitive counts per footprint equal
   to a library made by hand with Design > Make PCB Library from the same board (pads,
   tracks, arcs, texts, 3D bodies), `problems` []; the board and project file unmodified, the
   project folder's files unchanged, nothing written beside the board, the library closed.
   `footprints` in lower case, two names: 2 footprints, `removed_by_filter` 10, the document
   that was in front (another library) in front again. A board with an unsaved move:
   `board_modified` true after. A board not open, its project not open: 3 footprints asked,
   3 written, the board closed again, nothing left open, its folder unchanged. Refused: a file
   already at `library_path`, a pattern not on the board ("Not on the board: …. Nothing was
   made."), a board not found, a `.SchDoc` as board, a path without `.PcbLib`, a board with
   no components ("The board has no components. Nothing was made.").
5. **A8, reported success with less than the board has: the footprints' descriptions are
   lost.** Six of the twelve components carry a footprint description on the board
   (`IPCB_Component.FootprintDescription`, e.g. "Chip Resistor, 2-Leads, Body …"), and the
   library made by hand from the menu has them; in every library the tool made, read back
   with `get_footprint_primitives`, every description is "". The result's comparison with
   the board checks pads and patterns only, so `problems` stays []. Expected: each
   footprint's description as the board has it (set before the save), or the difference
   listed.
6. Minor, A40: `edit_schematic` with only a `place_component` whose symbol is not in the
   `.IntLib` (`applied` 0, `saved` false) left the sheet marked modified; nothing on it
   changed. A part placed from a `.SchLib` is still saved with library name, library path
   and target file name `*` and no Design Item ID, where an `.IntLib` part is now linked to
   its library: the two ways differ.
7. Minor, A40: `search_dblib` with exactly 20 matches and the default `max_rows` 20 says "a
   table reached max_rows (20): narrow the term or raise max_rows", though there is no
   21st (fetching one row more would tell). Every reply repeats the `tables` list (about
   0.3k characters); a search of 20 matches is 8k.
8. Seen in Altium, from tests run before this session: a temporary `Parts.SchLib` of a
   live test's folder in Free Documents, and two resident script projects of different
   tags open (A34 (e)).

64 calls, 0 errors, 54.5k characters (18 `run_altium_script`: opening, closing, checks
through Altium; the largest `search_dblib` 8k). The reference project's
`.PrjPcbStructure`, written by Altium on close, was deleted (A5's usage).

Sorted into A40 (1, 2), A8 (4), Closed; A26 (3), met again and widened; A41 (5), A42 (6),
A43 (7), A44 (8, the temporary library), new; A34 (e) (8, the resident projects), met again.

**2026-11-18: preparing to draw two schematics from parts in installed libraries, stopped before the first sheet**

Release `bin\0.7.0-20261115-172812`.

1. `get_symbol_primitives` in inventory mode (no `symbol_name`) on a 418-symbol `.SchLib`
   returned 91k characters, over the tool result limit, so it was saved to a file and read
   by script. Every symbol's record carries its per-type counts; to find the generic parts
   (resistor, capacitor, diode, connector) only name and description were needed. Missing:
   a `name` or `term` filter, or an inventory of names and descriptions only. Reported
   success.
2. Missing: a read of several symbols' pins in one call. A layout needs each symbol's pin
   designator, name, location, orientation and length; `get_symbol_primitives` gives one
   symbol per call with all its graphics. Done instead by one `run_altium_script` over the
   library's components for a list of 27 names, then again for 6 in a second library:
   2 calls in place of 33.
3. Seen before drawing, not met yet: a sheet of some 60 parts and 150 wires has to go into
   `build_schematic` and `edit_schematic` as inline JSON (about 20k characters a sheet).
   `create_symbols_batch` takes a spec file; the sheet tools take none. A `spec_file` on
   `build_schematic` and `edit_schematic` would spare a large payload per sheet.

4 calls, 0 errors, about 100k characters (91k of them point 1's result).

Sorted into A57 (1, 2), new; A58 (3), new.

**2026-11-18: a 9-sheet schematic of 294 parts drawn from a connection table, checked against it**

Release `0.7.0-20261115-172812`.

1. `build_schematic` with a multi-part symbol (6 parts) placed part A only; its `pin_map` listed
   the pins of all six parts, all at part A's origin, and `success` was true. Nothing says the
   other parts were not placed; `edit_schematic`'s `place_component` has no `part` either.
   Workaround: the symbol made single-part. New.
2. `build_schematic`'s `pin_map` is keyed by pin name: pins sharing a name (several `GND`, two
   shield pins, five `VDD`) collapse to one entry, the last. Pin numbers would keep them apart.
   New.
3. A26, met again: a free document from an earlier `build_schematic` call (no `project_path`)
   was taken into the project by the next call with `project_path`; `detached_from` `""`.
   Removing it by script (`DM_RemoveSourceDocument`, then saving the project) left the project
   file with two `[DocumentN]` sections for the same sheet: Altium rewrites the sections it
   knows and keeps the stale last one. Fixed by hand in the file.
4. A28, met again: the project's library made with `run_altium_script`
   (`Client.OpenNewDocument('SCHLIB', ...)`, `SetFileName`, `DoFileSave`).
5. No tool sets a sheet's size, title block or document parameters (Title, DocumentNumber,
   Revision): `build_schematic` makes the sheet in Altium's default size. Done by
   `run_altium_script` on each sheet (`SheetStyle := eSheetA3`, parameters by iterator), 9 calls.
   New.
6. `get_erc_violations` then reported 852 "Object not completely within sheet boundaries", every
   one beyond x 11500 or y 7600, A4's bounds, though each sheet reads `SheetStyle` A3,
   `SheetSizeX/Y` 15500 x 11100, saved, and draws A3 on screen. A second run gave the same.
   Either the compile keeps the size the sheet was created with, or the check reads it from
   elsewhere. Not resolved. New.
7. `get_erc_violations` returned 155k characters (capped at 1000 violations) and failed the
   tool-result limit: read from the saved file. No `type`, `level` or `limit` filter. New.
8. `build_schematic`'s `net_labels` take no justification: every sheet's labels went in a second
   call through `edit_schematic`'s `add_net_label`. A `justification` key would save that call.
   New.
9. `build_schematic` echoes the whole `pin_map` (a 71-part sheet: about 20k characters) when the
   caller already computed every pin. An option to leave it out would help. New.
10. No tool removes a document from a project or deletes its file: a sheet rebuilt from scratch
    needed `run_altium_script` (`DM_RemoveSourceDocument`, `DeleteFile`) each time (3 times).
    New.
11. `run_altium_script`: a local `procedure` with its own `var` block is refused by the lint
    ("not declared"), and declared globally Altium refuses `procedure` itself ("Unknown
    identifier"). Loops with `List1` and globals work. Lesson.
12. A netlist read for checking (nets with pin number and name) needed `run_altium_script`
    (`DM_Compile`, `DM_DocumentFlattened`, `DM_Nets`, `DM_Pins`) saved to a file; no tool
    returns the compiled netlist. New.
13. `check_schematic` found every readability fault the drawing had (text overlaps, wires
    ending past the last tap, a pin used as a branch point, a wire through a body) and its
    `clear: true` suggestions applied cleanly with `move_text`. Lesson: worth running after
    every sheet.

About 150 calls, 4 failed or refused (point 11's twice, a property missing on an interface, the
ERC result's size).

Sorted into A45 (1), new; A46 (2, 9), new; A26 (3), met again; A28 (4), met again; A47 (5), new; A48 (6), new; A49 (7), new; A51 (8), new; A52 (10), new; A53 (11), new; A54 (12), new. Not filed (13): a lesson, `check_schematic` after every sheet.

**2026-11-19: audit of a 9-sheet schematic already drawn: ERC, netlist against its source table, drafting check, footprints**

Release `bin\0.7.0-20261115-172812`.

1. `get_erc_violations(project_path)`: none of the 852 "Object not completely within sheet
   boundaries" of the 2026-11-18 entry's point 6 (A4's bounds on A3 sheets) came back, in a new
   Altium session on the same saved sheets, with nothing changed in their size. So the check read
   the size the sheets were created with, in that session only; a save, close and reopen clears
   it. Lesson. Bears on that point 6; no item yet.
2. `get_erc_violations` returned 273 violations, about 150 of them "Duplicate nets" from one
   sheet of unannotated parts, the rest to be found among them. Point 7 of the 2026-11-18 entry
   met again: a `type` or `level` filter, or a count per type with the details on request,
   would have made it one short read.
3. The compiled netlist (net, pin number, pin name) again needed `run_altium_script`
   (`DM_Compile`, `DM_DocumentFlattened`, `DM_Nets`, `DM_Pins`, saved to a file), 1 call.
   Point 12 of the 2026-11-18 entry met again.
4. `get_project_info` with no project focused returned `"project_path": "Free Documents"` and
   nothing else; it takes no `project_path`, unlike `get_erc_violations` and
   `get_project_components`. A `project_path` argument would let it read a project not in
   focus. New.
5. `check_schematic` on the `.PrjPcb` with `max_issues_per_sheet: 0` gave the counts of all 10
   sheets in one short reply. Lesson: the cheap way to re-check a drawn project.
6. A footprint added to a library symbol with `create_symbols_batch` (`FOOTPRINT`, read back
   right) does not reach the part already placed from it, and no tool updates a placed part from
   its library or sets its footprint: `run_altium_script` (`AddSchImplementation`,
   `AddDataFileLink`), 1 call, then `get_project_components` showed it. Checking the footprint's
   pad names against the symbol's pins took another script (no tool returns a footprint's pad
   names short of the full dump of `get_footprint_primitives`). Bears on A16 (closed: the
   library side) and A11. New.

11 calls, none failed.

Sorted into A48 (1), new; A49 (2), new; A54 (3), new; A55 (4), new; A56 (6), new; A57 (6), new. Not filed (5): a lesson, `max_issues_per_sheet: 0` on the project.

**2026-11-19: a ten-sheet schematic made hierarchical with signal harnesses**

Release `bin\0.7.0-20261115-172812`.

1. No tool places a sheet symbol or sheet entry, a port, a harness connector with its entries,
   or a signal harness, and `edit_schematic` has no op for them (it has wires, net labels,
   power ports). All of it went through `run_altium_script`: 8 harness connectors, 14 harness
   lines, 14 ports, 9 sheet symbols with 14 entries, about 300 stub wires and labels. A data
   file per sheet read by one interpreter script kept each call short. New.
2. `ISch_HarnessConnector` has no `Side` nor `HarnessConnectorSide` property in DelphiScript
   ("Undeclared identifier"); the file's `HARNESSCONNECTORSIDE` is set by
   `HC.Mirror(Point(centre_x, top))` after the connector is registered, which puts the harness
   on the left and the entries on the right. The type label comes out mirrored and
   right-justified past the connector: `HarnessConnectorType.IsMirrored := False`,
   `Justification := 0` and its `Location` set again put it back. `DistanceFromTop` and
   `PrimaryConnectionPosition` take coordinates (`MilsToCoord(100)` for one grid). Lesson.
3. A signal harness from `SchObjectFactory(eSignalHarness, eCreate_Default)` gets the smallest
   line width. Drawn between two sheet entries on a top sheet, compile gave 7 fatal "Missing
   Harness Type on Signal Harness", "Unconnected line" for each, and one "Multiple Harness
   Types on harness" naming all seven types: every sheet entry carried the members of every
   harness. The flattened netlist was still right, by member names that happened to be unique.
   `LineWidth := eMedium` (Altium's default) on the same lines: 0 fatal, each net joined only
   through its own harness. The same smallest width between a harness connector and a port on
   a lower sheet connected without complaint. The scripts reported success. New; a tool placing
   harnesses would set the width.
4. A script's `CreateNewDocumentFromDocumentKind('SCH')` for a scratch sheet put it into the
   focused project and left the project modified; taking it out needed
   `DM_RemoveSourceDocument` and closing the document. A copied file opened by path stays a
   free document. A26 met again in kind (a new sheet joining the focused project).
5. `get_erc_violations` on a project with 199 violations returned about 100,000 characters,
   over the client's limit three times, read back from the saved file with a script. Most of
   it was 99 warnings of one kind and 30 of another. A summary option (counts by type, the
   first few of each) would serve a check. New.
6. `get_screenshot` for a schematic has no fit option (`zoom_to` is PCB only); a script with
   `RunProcess('Sch:Zoom')` and `Action=Document` did not fit the sheet, `Sch:ZoomFit` did.
   New.
7. DelphiScript lessons: names are case-insensitive (`F` and `f` declared together: "Identifier
   redeclared"); an interface variable not assigned is not `nil`, so `if SS <> nil` passed and
   the call on it failed; set it to `nil` first. `TStringList.StrictDelimiter` exists. Lesson.
8. `check_schematic` read the harness objects right: no wire ending on a harness entry or
   connector edge was flagged, and its `sheet_entry_margin` caught the eight sheet symbols. It
   also made the occupancy search for free space possible from the saved files (its `Sheet`
   and `Checker.obstacles`). Lesson.

About 50 calls, 6 failed (script errors on the API names in 2 and 7).
9. Changing a project option had no tool: the project was closed by `run_altium_script`
   (`WorkspaceManager:CloseObject`, ObjectKind Project), its file edited, and reopened by
   `get_erc_violations(project_path)`; `Client.OpenDocument('PrjPcb', path)` in a script did not
   put it back in the workspace (the next call found no project). New.

Sorted into A59 (1, 3), new; A26 (4), met again; A49 (5), new; A60 (6), new; A62 (9), new. Not filed (2, 7, 8): DelphiScript and `check_schematic` lessons, point 2's API notes kept in A59.

**2026-11-19: a module footprint made in a new project footprint library and given to a symbol and its placed parts**

Release `bin\0.7.0-20261115-172812`.

1. A28 met again: the new `.PcbLib` was made by `run_altium_script`
   (`Client.OpenNewDocument('PCBLIB', '', '', False)`, `DoSafeChangeFileNameAndSave`,
   `SetModified(True)`, `DoFileSave('')`), 1 call; with no project in focus ("Free Documents") it
   joined none, and `add_project_document(create=False)` then added it cleanly. The new library
   holds Altium's empty default footprint `PCBComponent_1` beside the one made; no tool deletes a
   footprint, so it stays. New (a `create` for libraries would make it empty, or remove it).
2. `create_pcb_footprint` takes no hole, so a through-hole footprint went through
   `create_footprints_batch` instead: 18 plated pads, tracks on two mechanical layers and the
   overlay, one arc, in one call, no problems. Layer names as `get_footprint_primitives` prints
   them ("Multi Layer", "Mechanical Layer 15", "Top Overlay") were taken as they are. Lesson: read
   a library footprint of the same kind first and copy its layers, widths and pad stack.
3. The previous entry's point 6 met again: `create_symbols_batch` `FOOTPRINT` linked the library
   symbol (read back right), and the five parts already placed from it needed
   `run_altium_script` (`AddSchImplementation`, `AddDataFileLink`, `IsCurrent`), 1 call; a second
   script read them back current in memory. But `get_project_components` (which compiles in
   memory, "nothing is saved") and a script's own `DM_Compile` both gave the five parts an empty
   `footprint`. The script had left the sheet's `Modified` false (PreProcess/PostProcess and
   `SCHM_PrimitiveRegistration` do not set it), so the owner's Save All skipped the sheet and the
   change stayed in memory only; `Client.GetDocumentByPath(path).SetModified(True)` marked it.
   Saved then, and even closed and reopened from disk (the records there, read back with
   `ExportToParameters`, the same as a part whose footprint the compile does show), the compile
   still gave an empty `footprint`. Only one more script edit on the sheet (one part's datafile
   link rewritten, `SetModified(True)`) made it give the footprint, for all five parts, the four
   untouched included. So the project compile keeps a sheet's components from before a script
   edit until a change it is told of. Reported success with a stale result. Lesson: after a script
   edit, set the document modified and make a tracked change before reading the compile. A tool
   setting a placed part's footprint would do it. New; bears on that point 6 and A16 (closed, the
   library side).
4. `get_component_data` on schematic parts with no board placement: `"No component data found"`.
   It reads the board only, which its description does not say; `get_project_components` is the
   schematic-side read. Lesson.
5. DelphiScript: `ISch_Document` has no `Modified` property ("Undeclared identifier:
   Modified"); the `IServerDocument` from `Client.GetDocumentByPath` has it. Lesson.

6. `create_footprints_batch` `EDITFOOTPRINT` with `MODEL3D` (a Y-up STEP, rotation X 90, z offset
   and x|y offset, embedded) worked first time; `get_footprint_primitives`' standoff and overall
   height confirmed the orientation before saving, the rotations null until saved, as described.
   Lesson: read the STEP's pin positions first (an OCCT read) to set the offset.

7. `edit_schematic` `delete_at` with `kind: no_erc` at a point holding two markers removed both
   (34 to 22 for six points), while it says it removes "the object located there". Reported 6
   applied. New: one object per op, or the count removed in the result.
8. No-ERC markers placed by `edit_schematic` (and others placed by script earlier) exactly on the
   ends of three unconnected input pins, `SuppressAll` true, did not suppress ERC's "Nets
   containing floating input pins" for those pins ("Unconnected Pin ... at" the same mils),
   compiled both from disk and from memory; the marker reads "All violations" in Altium's
   properties. Not resolved; cause unknown. New.
9. No tool sets a placed part's Comment (`edit_schematic` `set_parameter` creates a parameter by
   name; Comment is the part's own property): `Comp.Comment.Text` by script, with
   `SetModified(True)` per point 3. New (small).

35 calls, 4 failed (point 4, the script of point 5, two scripts on DM violation names).

Sorted into A28 (1), met again; A48 (3), new; A56 (3), new; A67 (4), new; A68 (7), new; A50 (8), new; A69 (9), new. Not filed (2, 5, 6): lessons.

**2026-11-19: no-ERC markers that seemed not to suppress, traced to the ERC reader**

Release `bin\0.7.0-20261115-172812`.

1. `get_erc_violations` lists violations that Altium has suppressed. Six "Nets containing
   floating input pins" errors on unconnected input pins, each with a no-ERC marker exactly on
   its end (raw coordinates equal, `IsActive` and `SuppressAll` true), and their six "no driving
   source" and six "Unconnected Pin ... at" warnings, are in the tool's result (95: 6 errors,
   89 warnings); Altium's own Messages panel after a GUI compile does not show them: it opens
   on the first warning, which is No. 7 in the tool's list, the list being the compile's order.
   A test marker added by `edit_schematic` on another net's pin left that net's "IO Pin and
   Output Pin" warning in the tool's list too. `GetERCViolations` (other_utils.pas) reads every
   `Project.DM_Violations(I)` with no suppression test; the project file's
   `ReportSuppressedErrorsInMessages=0` says the compile keeps suppressed ones and only the
   panel hides them. Reported success, with errors that are not there. Resolves the 2026-11-19
   entry's point 8 (cause found). New: filter the suppressed ones, or report them apart
   (`suppressed: n`); the property that tells them is not known yet (the DM names tried in that
   entry failed).
2. A diagnostic test marker left the sheet modified after it was deleted again, with no net
   change: the owner chooses to save or revert. Lesson.

11 calls (6 `run_altium_script`, 2 `edit_schematic`, 2 `get_erc_violations`, 1 status), 1 failed: a script reading `Location` on every object kind ("Undeclared identifier: Location", the sandbox caught it).

Sorted into A50 (1), new. Not filed (2): a lesson.

**2026-11-19: a vendor part (symbol and footprint with an embedded 3D model) copied from an extracted `.IntLib` into a project's own libraries**

Release `bin\0.7.0-20261115-172812`.

1. `run_altium_script`'s helper `OpenSchDoc(path)` given a `.SchLib` opens it as a schematic:
   `Client.GetDocumentByPath(...).Kind` is `SCH`, the document's `ObjectId` 32 (a library
   opened as a library reads 33). From then on, until that document is closed, every call that
   needs it as a library fails: `SchLibIterator_Create` and `AddSchComponent` give "Undeclared
   identifier" (5 scripts), and `create_symbols_batch` with `LIBRARY|<that path>` returns
   "Could not open and focus ... - nothing was created or edited", because `OpenDocument('SchLib',
   ...)` only focuses the document already open as SCH. Workaround: `Client.CloseDocument` (it was
   not modified) and `Client.OpenDocument('SchLib', path)`. The cause took 7 failed calls to
   find: nothing says which kind a document is open as. New: `OpenSchDoc` refuses a `.SchLib` (or
   opens it as one), and the batch tool's "could not open and focus" names the kind it found.
2. `ISch_Component.Replicate` of a symbol in one `.SchLib`, added to another with
   `AddSchComponent` and `SCHM_PrimitiveRegistration`, copies the symbol's parameters, Comment,
   Designator and footprint model but **none of its lines and pins**: the script succeeded and
   the saved copy had 0 primitives (`get_symbol_primitives`). Only the inventory showed it
   (`"other": 2`, no `pins`). Workaround: replicate the children of kinds `eLine`, `ePin` one
   by one and `AddSchObject` them to the copy (12 added, then identical to the source in
   `get_symbol_primitives`). Lesson for scripts; new for a tool (point 4).
3. Copying a footprint between two `.PcbLib`s by script works, embedded 3D body included:
   `CreatePCBLibComp`, `RegisterComponent`, then each primitive of the source's
   `GroupIterator` `Replicate`d, moved by minus the source library's `Board.XOrigin`/`YOrigin`
   (the source footprint is the one shown, so it is held offset by the origin; the new one is
   not) and `AddPCBObject`ed. `get_footprint_primitives` on both saved files: the same pads,
   tracks, arcs, and `bodies_3d` (model embedded, rotation, standoff). Lesson.
4. Missing tools, met together: extract an `.IntLib`'s sources (done by
   `IntegratedLibraryManager.ExtractSources(path)`, which writes a folder beside the
   `.IntLib`), and copy a symbol or a footprint from one library into another (points 2, 3).
   Bears on A15 (parts from local libraries only) and A28 (library making); neither covers a
   copy. New.

5. No tool gives a placed part a footprint: `edit_schematic` has no such op (A16 covers a
   symbol's, in its library). Done by script on 11 placed parts across two sheets:
   `AddSchImplementation`, `ModelType 'PCBLIB'`, `AddDataFileLink`, `IsCurrent`, inside
   `SCHM_BeginModify`/`EndModify`; `get_project_components` then read the footprints, and the
   compiled netlist was unchanged. New (small).
6. `run_altium_script`'s pre-check refuses a script whose nested procedure declares its own
   `var` block ("'X' is not declared"): it reads only the leading block. Workaround: all
   variables in the leading block, the procedure inlined. New (small).

37 calls (23 `run_altium_script`, 3 `get_symbol_primitives`, 2 `get_footprint_primitives`, 2 `create_symbols_batch`, 7 other), 8 failed: 1 script of the session's own error, 5 scripts and 1 `create_symbols_batch` from point 1, 1 script refused by point 6.

Sorted into A70 (1), new; A63 (2, 3, 4), new; A56 (5), new; A53 (6), new.

**2026-11-19: releasing Altium for the owner's own library search, between sessions**

Release: not read (no tool called this session); the live resident's tag `07987973414d`.

1. Missing: a way to close the resident bridge on purpose. The owner asked to stop the
   server's script so they could search parts in Altium themselves before moving to a new
   session. No tool does it, so the session wrote the `stop` file by hand into
   `C:\Users\Public\altium_mcp\resident\07987973414d\`, from the README's account of how a
   resident of another build is told to close. Whether the form closed was not seen: the
   `stop` file stays in the folder (as in the two older tags' folders), and reading
   `get_server_status` to check was not tried for fear it starts the resident again. A
   tool, or a `get_server_status` option, that closes the resident and reports it gone
   would serve. Bears on A34 (e), the resident's project left in the Projects panel.

Sorted into A34 (1), part (f).

**2026-11-19: footprints put on placed placeholder parts, and footprint sources surveyed**

Release: `0.7.0-20261115-172812`.

1. Met again (the 2026-11-19 entry's point 5, no tool gives a placed part a footprint):
   `run_altium_script` (`AddSchImplementation`, `ModelType 'PCBLIB'`, `AddDataFileLink`,
   `IsCurrent`, the placeholder parameter removed, inside `SCHM_BeginModify`/`EndModify`,
   then `SaveDoc`) on 6 parts across two sheets, 1 call. This time `get_project_components`
   read the 6 footprints at once: the stale compile of that entry's point 3 did not recur
   with `SaveDoc` (which marks the document modified) right after the script. A16.
2. Missing: a read of which library each placed part's footprint links to. Done by script
   (each current PCBLIB implementation's `DatafileLink[0].Location`), 2 calls. It showed
   parts linked to a library file that does not hold their footprint (an older copy of a
   vendor library at another path), which nothing else reports: `get_project_components`
   gives the footprint name only, and a compile raises nothing. A `footprint_library` field
   in `get_project_components`, and a flag when the linked file lacks the footprint, would
   serve. New (small); bears on A16.
3. `edit_schematic` `delete_component` on two parts the owner had placed only to bring their
   library in was refused by the client's own permission check, not the server: nothing to
   fix here, noted so a session expects it.
4. Missing: a tool that turns or moves a footprint's 3D body (a vendor model lying across
   its pads). `IPCB_Model.GetState(RX, RY, RZ, DZ)` through `run_altium_script` returned 3 in
   every variable (var parameters are not filled through the script's late binding), so the
   rotation could not be read there; `get_footprint_primitives`' `bodies_3d` read it from the
   saved file. Turning the body with `RotateAroundXY(origin, 90)` between
   `PCBM_BeginModify`/`EndModify`, then `SaveDoc`, held: read back rotation Z 90, X kept. New;
   bears on A28 (library making).
5. Copying a footprint from a large vendor `.PcbLib` into a project library, the previous
   entry's point 3 method with `SetBoardToComponentByName` on the source first, held: 15
   primitives, the embedded body included, read back the same. Repointing placed parts from
   one footprint to another needed `RemoveSchImplementation` and a new implementation (no
   setter for a link's location found). A16, the earlier entry's points 3 and 5.
6. A vendor `.IntLib` whose footprint had no 3D body and whose STEP came as a separate file:
   extracted (`ExtractSources`), footprint and symbol copied as before (the symbol's children
   replicated one by one, 8 of 8 held), then `create_footprints_batch` `EDITFOOTPRINT` with a
   `MODEL3D` record added the body, `create_symbols_batch` `EDITSYMBOL` `FOOTPRINT` relinked
   the symbol: all held. The model's orientation had to be read from the STEP's points outside
   Altium (Y-up, base at y 0, so rotation X 90); a tool reporting a STEP's extents and up axis,
   or `bodies_3d` giving the body's bounding box once placed, would spare that. New (small).
7. Met again (the entry "releasing Altium for the owner's own library search"): the owner
   asked for the server's script to be stopped at the end so they could use the vendor's
   library loader in Altium. Done by writing the resident's `stop` file by hand; no tool does
   it. A34 (e).

About 20 calls (9 `run_altium_script`, 10 `get_symbol_primitives`/`get_footprint_primitives`
reads, 1 refused `edit_schematic`, 3 `get_project_components`, 1 `add_project_document`); none
failed in the server; one script's `GetState` read was useless (point 4). Reading a
whole footprint library's inventory (`get_footprint_primitives` without a name) overflowed the
client's result limit at about 60 KB; a name filter would serve.

Sorted into A56 (1, 2, 5), new; A63 (5, 6), new; A64 (4, 6), new; A34 (7), part (f). Not filed (3): the client's own permission check, not the server.

**2026-11-19: placeholder parts swapped to library parts, a part added to a sheet, symbols deleted from a library**

Release `0.7.0-20261115-172812`.

1. `edit_schematic` `delete_component` then `place_component` from a project `.SchLib`, at the
   same point, on a symbol whose pins sit where the old one's did: held, the wires kept their
   connection, the netlist read back equal. `place_component` from a `.SchLib` left Altium's
   focus on that library: the next `get_screenshot(view_type="sch")` was refused ("Altium has a
   SCHLIB document focused"), twice in the session, each time one `run_altium_script` of
   `Client.ShowDocument` on the sheet before the screenshot. Reported success both times. New;
   near A26 (a tool leaving the focus elsewhere). Local: the edit puts the sheet back in front.
2. `edit_schematic` `add_power_port` shows the net name by default; every other port on the
   sheet had it hidden, so the new GND read differently. Redone with `show_net_name: false`
   (`delete_at` + `add_power_port`, held). Not a fault: noted so a session passes the sheet's
   own style. A line in the description ("match the sheet's ports") would spare the second call.
3. Missing, met again: setting a placed part's footprint (a placeholder given a footprint copied
   into the project library) and copying a footprint between libraries, both by
   `run_altium_script` as the earlier entries did (`RemoveSchImplementation` + a new
   implementation; `Replicate` of each primitive), both held. Also by script, no tool for it:
   removing a part's parameter (`Remove_Parameter`, held), changing a free text label's text
   and adding a second one (`Replicate` + `RegisterSchObjectInContainer`, held), deleting two
   symbols from a `.SchLib` (`RemoveSchComponent` on the `SchLibIterator`'s component, then
   `SaveDoc`, held: read back gone). A28 (library making) for the last; the others new.
4. `run_altium_script`: parts collected into a scratch `TStringList` with `AddObject` and read
   back with `Objects[K]` cannot be called (`Undeclared identifier: I_ObjectAddress` on the
   first call), and `RemoveSchObject` on them did nothing. The sandbox caught it and closed the
   undo group it left open, as it says. Redone by finding the part again in a fresh iterator for
   each deletion (bounded `for`), held. Lesson for the description's script notes: keep
   `IDispatch` variables, not `TStringList` objects.

5. `create_symbols_batch`, six symbols copied from dumped ones (`get_symbol_primitives` ->
   PIN, GRAPHIC with a label, COMMENT, SYMPARAM, FOOTPRINT): held, one read back identical to
   its source. Missing: moving placed parts onto another library symbol in place. Done by
   script, setting `LibReference`, `DesignItemId`, `SourceLibraryName`, `LibraryPath` and
   `ComponentDescription` on 21 placed parts whose drawing matched the new symbol: held, the
   compiled project read the new references and the netlist was unchanged. `delete_component`
   + `place_component` would have lost each part's text positions. New.
6. Met again (A34 (e)): at the session's end the owner asked to stop the server's script. The
   `stop` file written by hand into the resident's folder; checked this time without
   `get_server_status`: an `EnumWindows` search from PowerShell for a window titled
   `altium-mcp resident` found none 3 s later, so the form closed. The check is cheap and does
   not wake the resident; a tool doing both would still serve.

About 30 calls (17 `run_altium_script`, 4 `edit_schematic`, 4 `get_footprint_primitives` and
`get_symbol_primitives`, 4 screenshots, 2 `check_schematic`, 1 `get_erc_violations`, 2
`get_project_components`); none failed in the server.

Sorted into A61 (1), new; A67 (2, 4), new; A56 (3), new; A63 (3), new; A69 (3, 5), new; A34 (6), part (f).

**2026-11-19: comparing a vendor footprint against a stand-in, then releasing Altium**

Release `0.7.0-20261115-172812`.

1. Met again (A34 (e)): the owner asked for the server's script to be stopped so they could
   use the vendor's library loader in Altium. The `stop` file written by hand into the
   resident's folder; an `EnumWindows` search from PowerShell for `altium-mcp resident` found
   none 3 s later. The `stop` file was still there afterwards; whether the next start clears
   it was not checked. No tool does it. The next `run_altium_script`, later in the session,
   started the resident again without a problem, so the leftover `stop` file did not block it.
2. Met again (the earlier entry's "extract an `.IntLib`'s sources"): with Altium released to
   the owner, a vendor `.IntLib`'s footprint was read outside Altium: its `PCBLib/0.pcblib`
   stream, zlib-compressed, inflates to a whole `.PcbLib` compound file that Altium opens. Python
   with `olefile` and `zlib`; the same file parsed for pads, tracks, arcs and bodies (record
   layout as KiCad's Altium importer reads it) gave the numbers to compare without a call. New
   for a tool: reading an `.IntLib`'s footprint, or `get_footprint_primitives` taking an
   `.IntLib` path.
3. Held again: three footprints copied by script from those `.PcbLib`s into a project library,
   embedded 3D bodies included (the earlier entries' method), read back with
   `get_footprint_primitives`; then existing tracks and arcs moved in place by `BeginModify`,
   coordinate change, `EndModify`: held, saved.
4. Failed silently, no error: adding a new track to an **existing** footprint of a `.PcbLib`.
   `PCBObjectFactory` track (or a `Replicate` of one of the footprint's tracks) added with
   `Comp.AddPCBObject(T)`, `Comp` from `GetComponentByName` or from `CurrentComponent` after
   `SetBoardToComponentByName`, with and without `SendMessageToRobots(Comp.I_ObjectAddress,
   c_Broadcast, PCBM_BoardRegisteration, T.I_ObjectAddress)`: the comp's `GroupIterator` count
   rose inside the same script, `SaveDoc` saved, yet the track was not in the saved file and
   gone from the comp in the next script. Four script runs lost that way. Held:
   `Board.AddPCBObject(T)` on `PcbLib.Board` after `SetBoardToComponentByName`, coordinates
   offset by `Board.XOrigin`/`YOrigin`, then `SendMessageToRobots(Board.I_ObjectAddress, ...)`;
   read back from the saved file. `create_footprints_batch` `EDITFOOTPRINT` takes only
   `MODEL3D`, so no tool adds or moves primitives of an existing footprint. A28 (library
   making); the silent loss is new.
5. `get_screenshot` `view_type "pcb"` captured the project's `.PcbDoc` while a `.PcbLib` was
   the document the scripts had focused: no way to look at a library footprint. Small, new.

About 15 calls (`get_server_status`, `get_installed_libraries`, 3 `get_footprint_primitives`,
8 `run_altium_script`, 1 `get_screenshot`); none failed in the server, one pattern lost its
work silently (point 4).

Sorted into A34 (1), part (f); A63 (2, 3), new; A64 (4), new; A60 (5), new.

**2026-11-19: three terminal symbols made, eight placed parts moved onto them, a symbol deleted from a library**

Release `0.7.0-20261115-172812`.

1. `create_symbols_batch`, three symbols copied by hand from a downloaded symbol's placed
   instance (a filled body, pins on one side): held, footprints read back linked. Missing: the
   GRAPHIC `rectangle` record takes no line or fill colour, and no record places the symbol's
   Designator or Comment. Both done by `run_altium_script` on the `SchLibIterator`'s component
   (`ISch_Rectangle.Color` / `AreaColor`, `Designator.Location`, `Comment.Location`, inside
   `SCHM_BeginModify` / `SCHM_EndModify`): held, parts placed afterwards carried both. Local: a
   colour field on the rectangle (and polygon) record, a `DESIGNATOR|x|y|justification` record
   and `COMMENT` with x|y. New; near A28 (library making).
2. `edit_schematic` `delete_component` + `place_component` (with `mirror` for two of them) at
   the old pin-1 point, then `move_text` for the Designator and Comment, in one call per sheet:
   held, every pin read back where it was, the netlist compared unchanged, texts where they
   were. Answers the earlier entry's point 5 (text positions lost by delete and place): the
   `move_text` ops in the same call restore them, so delete and place serves a swap whose
   drawing differs. Still missing: a swap op that keeps the part's place and text.
3. `get_component_data` with schematic designators on a project whose board holds no parts
   returned `{"error": "No component data found"}`: it reads the board only, which its
   description ("Get all data for components in Altium") does not say. Read with
   `get_schematic_data` instead. Small, new: a line in the description.
4. `run_altium_script`'s lint refused a script reading `.Corner` through an `IDispatch`
   variable before Altium was called, and said to declare `ISch_Rectangle`: held, one call lost.
5. Met again (A28): a symbol deleted from a `.SchLib` by `RemoveSchComponent`, held, read back
   gone.
6. Missing: changing an existing footprint's 3D body placement (rotation, offset) and a pad's
   stack. A body copied earlier by script into a library kept only its X rotation and lay
   turned and off the pads; `get_footprint_primitives` reads the placement from the saved file
   only, so an unsaved change cannot be checked with it. Done by `run_altium_script`:
   `Model := Body.Model; Model.SetState(90, 0, 270, 0); Body.Model := Model;
   Body.SetState_FromModel; Body.MoveByXY(...)` inside `PreProcess`/`PostProcess`, read back
   through an `IPCB_ComponentBody` variable's `BoundingRectangle` (the rotations applied X
   first, then Z): held. `Pad.Mode := ePadMode_Simple`, `TopShape := eRectangular`: held. Local:
   an EDITFOOTPRINT record to set a body's rotation and offset, and the body's extent in
   `get_footprint_primitives` read live. New.

About 15 calls (`get_server_status`, 2 `get_symbol_primitives`, `get_schematic_data`,
`get_component_data`, `create_symbols_batch`, 3 `edit_schematic`, 8 `run_altium_script`,
`get_footprint_primitives`,
`get_erc_violations`); none failed in the server.

Sorted into A65 (1), new; A69 (2), new; A67 (3), new; A63 (5), new; A64 (6), new. Not filed (4): the lint refused as meant, its message naming the fix.

**2026-11-19: placed parts selected as a rectangle; two connectors swapped onto another symbol**

Release `0.7.0-20261115-172812`.

1. Placed parts whose own primitives could be selected alone: a click on the part's body
   selected its rectangle (Properties showed a rectangle, not a part). In the saved sheet a
   placed part's child primitives carry `IsNotAccesible=T` (Altium's spelling); on 24 parts
   across nine sheets the body rectangle (on two diodes their six lines) did not. All 24 had
   been placed or placed again by script or by the server's tools in earlier sessions; parts
   placed from a library in Altium's own UI all had it. Not reproduced: `edit_schematic`
   `place_component` today set the flag on both parts it placed. The flag is not readable
   from DelphiScript: `Obj.IsNotAccesible` and `Obj.IsNotAccessible` on a child rectangle both
   gave "Undeclared identifier". Found only by reading the saved file's records. Workaround,
   held: per part, inside `PreProcess`/`PostProcess` and `SCHM_BeginModify`/`SCHM_EndModify`,
   `Comp.PinsMoveable := True; Comp.PinsMoveable := False;` then save: every child primitive
   carried the flag after, nothing else in the records changed, the netlist unchanged. Local:
   `check_schematic` (it reads the saved file) could report a placed part with a child
   primitive lacking the flag, its fix the toggle; and the place and build tools checked for
   setting it. New.
2. `ISch_Component.Locked` in a script: "Undeclared identifier: Locked". Small, a lesson:
   the component's lock is not under that name; `PinsMoveable` is the Lock Primitives box.
3. `edit_schematic` `delete_component` + `place_component` + `move_text` in one call, swapping
   two 3-pin connectors onto a symbol of the same pin geometry at the same origin: held again
   (the earlier entry's point 2), pins read back on their nets, texts where they were,
   `check_schematic` no issue.

About 17 calls (`get_server_status`, 11 `run_altium_script`, `get_project_components`,
`edit_schematic`, `check_schematic`, `get_erc_violations`); none failed in the server.

Sorted into A71 (1), new. Not filed (2, 3): a lesson (`PinsMoveable` is the Lock Primitives box); a swap that held again.

**2026-11-19: a second project's libraries made from another's, a symbol and footprint added, one sheet drawn**

Release `bin\0.7.0-20261115-172812`.

1. `run_altium_script`'s helper `OpenSchDoc(path)` on a `.SchLib` opened the library as a
   schematic sheet (document kind `SCH`, `ObjectID` 32, a sheet border and zones shown), not
   as a library. A second script's `Client.OpenDocument('SCHLIB', path)` returned the same
   sheet, and an iterator call on it (`SchLibIterator_Create`) failed, the next run hung for
   120 s. Closed unsaved by script; `get_symbol_primitives(library_path)` then opened it as a
   library (`ObjectID` 33). Had the sheet been saved, the library file would have been
   overwritten as a schematic. The helper's description says it returns the ISch_Document;
   it does not refuse a library. Local: `OpenSchDoc` opens by the file's extension, or
   refuses a `.SchLib`. New.
2. Deleting a symbol from a `.SchLib` and a footprint from a `.PcbLib` has no tool:
   `RemoveSchComponent` and `RemoveComponent` by script, both held after save. A library
   for a new project was made as a file copy of another project's, then pruned that way.
   Bears on A28 (no tool makes an empty library).
3. A footprint copied between two PcbLibs by script (`CreatePCBLibComp`,
   `RegisterComponent`, each source primitive's `Replicate` added with `AddPCBObject` and
   registered with `PCBM_BoardRegisteration`, to the component's and in a second try to the
   library board's address) showed its primitives in `get_footprint_primitives`' inventory
   before save and none after; both runs reported success. `create_footprints_batch` from
   the source's dump made it right, the STEP taken out of the source library's embedded
   models (`Library/Models/<n>`, zlib) since `MODEL3D` needs a file. A tool copying a
   footprint, 3D body included, between libraries would serve. New.
4. `get_footprint_primitives` on the footprint just made and saved gives its 3D body's
   rotations and z offset as null, "not in the saved library file", the body's model named by
   the full STEP path given to `MODEL3D`; not seen whether the rotations given were applied.
   New.
5. Setting a sheet's size and its title block parameters has no tool: a script set
   `SheetStyle` and each document parameter's `Text`. A first try reading names and values
   from one TStringList (`Names`, `ValueFromIndex`) failed with "Could not convert variant
   of type (OleStr) into type (Double)"; two lists by index worked. Lesson.

About 30 calls, 4 failed (points 1 and 5, the replicate's two runs reported success).

Sorted into A70 (1), new; A63 (2, 3), new; A64 (4), new; A47 (5), new.

**2026-11-19: a sheet drawn, a library symbol's pins moved, the sheet drawn again**

Release `bin\0.7.0-20261115-172812`.

1. `check_schematic` reported a sheet clean while a placed symbol's own pin names crossed:
   a top pin's vertical name ran down over the left pins' names, and three bottom pins'
   names over the right side's last pin names. Seen only in `get_screenshot`. Local: a
   `pin_name_overlap` issue, each visible pin name's box (by its pin's orientation and the
   font) against the others' of the same part, with the library symbol named as the fix.
   New.
2. Moving a pin of a library symbol has no tool: `create_symbols_batch` `EDITSYMBOL` leaves
   pins and graphics alone, as its description says. Done by script: the pins iterated
   inside the component, `MoveByXY`, and the body rectangle's `Corner` set directly (a write;
   the lint did not refuse it), between `SCHM_BeginModify`/`SCHM_EndModify`, then
   `SaveDoc` on the `.SchLib`; `get_symbol_primitives` read it back as asked. Local: an
   `EDITSYMBOL` record to move or replace a pin (`MOVEPIN|<number>|x|y`), and a rectangle's
   resize. New.
3. Taking a sheet out of a project has no tool, and `build_schematic` refuses an existing
   path, so a sheet built wrongly cannot be built again in place. Workaround held: every
   component, wire, net label, power port, junction and no-ERC removed by script (title
   block parameters and notes kept), then the whole sheet placed again by one
   `edit_schematic` call of 209 operations (25 `place_component`, 98 `add_wire`, 35
   junctions, 23 power ports, 22 labels, 6 no-ERC): applied 209, no error, the netlist then
   as asked. `edit_schematic` has no op for a free text note, so the notes had to be kept.
   Local: `build_schematic` with `replace: true` on a sheet of the project, keeping its
   sheet style and parameters; or an `add_note` op. New.
4. `get_screenshot` captures the current zoom only; a script's
   `Client.SendMessage('SCH:Zoom', 'Action=Document', 255, Client.CurrentView)` fitted the
   sheet first. Local: a `fit` option for `sch`. Small, new.

About 20 calls (`get_server_status`, `get_symbol_primitives` 3, `build_schematic`,
`edit_schematic` 3, `check_schematic` 3, `get_screenshot` 2, 7 `run_altium_script`); none
failed in the server.

Sorted into A72 (1), new; A65 (2), new; A52 (3), new; A69 (3), new; A60 (4), new.

**2026-11-19: a sub-sheet of eight repeated output channels drawn, then a five-sheet hierarchy with two signal harnesses**

Release `bin\0.7.0-20261115-172812`.

1. `build_schematic` without `project_path`, used as the description says for a parts-only
   call to read the pin map, put its `Sheet1.SchDoc` into the focused project and left the
   project modified; `DM_FreeDocumentsProject` did not list it. Taken out by script
   (`DM_RemoveSourceDocument`, the document closed unmodified). Reported success. A26, met
   again.
2. `run_altium_script` refused a script that opens several sheets in turn: "1 PreProcess but 2
   PostProcess call(s)". The script closes each sheet's group before opening the next (one
   `PostProcess` in the branch that opens a sheet, one after the loop), so the groups were
   balanced at run time; `skip_lint=True` ran it with no group left open. The lint counts
   calls in the text. Local: refuse only when the text has fewer `PostProcess` than
   `PreProcess`, or recognise a `PostProcess` before a `PreProcess` in the same branch. New.
3. Sheet symbols with entries, harness connectors with entries, signal harnesses, ports, free
   text notes and document parameters were all placed by script, no tool doing it: one
   interpreter script reading a line file, 146 lines for three sheets in one call. The
   earlier 2026-11-19 entry's point 1, met again.
4. After that call, `get_erc_violations(project_path)` gave 2 fatal "Missing Harness Type on
   Signal Harness", "Unconnected line" for both harnesses on the top sheet, one "Multiple
   Harness Types on harness", every sheet entry carrying both harnesses' members, and 16
   "Invalid Connection to a Harness Connector" on the two connectors whose entries face left,
   though their saved records match a working sheet's field for field. `LineWidth := eMedium`
   set on every signal harness (the earlier entry's point 3) and the sheets saved: the same 36
   violations. The project closed by script (`WorkspaceManager:CloseObject`) and opened again
   by `get_erc_violations(project_path)`: 0 fatal, every harness violation gone, the netlist
   as asked. The compile read connectivity made in that session, not what the saved sheets
   hold, and reported it as the design's. Which of the two changes was needed is not
   separated: the width was set before the reopen. Local: a `reload` option on
   `get_erc_violations` (close and reopen the project's sheets first), or a tool that places
   harness objects and refreshes connectivity. New.
5. A project option (sheet entries naming nets) changed with no tool, as in the earlier
   entry's point 9: project saved and closed by script, the `.PrjPcb` edited, reopened by
   `get_erc_violations(project_path)`. The file Altium writes is LF only; an edit that adds a
   CR leaves it mixed. Lesson.
6. Altium adds a `<sheet>.Harness` document to the project for each sheet holding a harness
   connector, and the project shows modified until saved. Lesson.
7. `RunProcess('Sch:Zoom')` with `Action=Document` did not fit an A3 sheet before
   `get_screenshot`: the bottom quarter was cut off. The earlier entries' zoom point, met
   again.

About 25 calls (`build_schematic` 2, `edit_schematic`, `check_schematic` 4, `get_screenshot`
4, `get_erc_violations` 3, `get_project_info` 3, `add_project_document`, 9
`run_altium_script`); one refused by the lint (point 2), none failed in Altium.

Sorted into A26 (1), met again; A53 (2), new; A59 (3), new; A48 (4), new; A62 (5), new; A60 (7), new. Not filed (6): a lesson.

**2026-11-19: an isolator sub-sheet drawn in place on an existing sheet, one block of it moved**

Release `bin\0.7.0-20261115-172812`.

1. `check_schematic` reported a sheet clean while two power ports of neighbouring circuits
   overlapped: a ground port (symbol below its hot spot, net name shown under it) 300 mil
   above a rail port (bar, net name above it) at the same x, twice on the sheet. Seen only
   in `get_screenshot`. `text_overlap` lists a port's text against wires, pins, parts and
   other text, but neither port's graphic and the other's text were taken as colliding.
   Local: each power port's box, its symbol and its shown name, against the other ports'
   boxes and part bodies. New; the same kind as the earlier 2026-11-19 entry's point 1 (an
   overlap seen only in a screenshot).
2. Moving one block of a drawn sheet (a part, its two decoupling capacitors, 11 wires, 3
   junctions, 6 power ports, 2 labels, a no-ERC) 300 mil down has no tool:
   `move_component` moves the part only, its wires stay. Done in one `edit_schematic` of 51
   operations, built by diffing the sheet's old and new operation lists: 23 `delete_at` (a
   wire by its first segment's midpoint), 3 `move_component`, 25 adds; applied 51, no error,
   the netlist then as before. Local: `move_component` with `drag: true` (Altium's drag,
   wires following), or a `move_region` op moving everything inside a rectangle. New.
3. `edit_schematic` has no op for a free text note: four notes placed by
   `run_altium_script` on the existing sheet, the three old ones removed by `delete_at`
   kind `note` (which held). The earlier 2026-11-19 entry's point 3, met again.
4. After `edit_schematic` with `move_component`, the last part moved stayed selected in
   Altium (its handles in the next `get_screenshot`). Harmless; small, new.
5. `get_screenshot` at the current zoom cut the bottom of an A3 sheet. The earlier entry's
   point 4, met again.

About 22 calls (`get_server_status`, `search_library_symbol`, `get_symbol_primitives` 3,
`get_project_info`, `get_schematic_data`, `edit_schematic` 3, `check_schematic` 3,
`get_screenshot` 3, `get_erc_violations` 2, 4 `run_altium_script`); none failed in the
server.

Sorted into A72 (1), new; A69 (2, 3), new; A61 (4), new; A60 (5), new.

**2026-11-20: two library symbols drawn again in a project's style, three parts swapped onto them, a connector symbol restyled in two libraries**

Release `bin\0.7.0-20261115-172812`.

1. The missing `IsNotAccesible=T` on a placed part's body (the 2026-11-19 entry's point 1,
   "not reproduced" then), reproduced: one `edit_schematic` call with three
   `place_component` from a project `.SchLib` (two of a 16-pin symbol, one of an 8-pin
   symbol, both made minutes before by `create_schematic_symbol`, each body a rectangle
   and a line). The two 16-pin parts carried the flag on both body primitives; the 8-pin
   part on neither, so a click took its rectangle. Reported success. Found only by reading
   the saved file. The same read of the project's other sheets, drawn earlier by
   `build_schematic` and `edit_schematic`, found 19 more parts without it (a 28-pin IC's
   rectangle, diodes' six lines each). Workaround held again: `PinsMoveable` True then
   False inside `PreProcess`/`PostProcess`, saved, flag set. Local as before: set it in
   `place_component` and `build_schematic`, and `check_schematic` reporting it.
2. `create_schematic_symbol` cannot set the symbol's Comment or add a parameter: the
   symbols came out with Comment `*` and no designator prefix or part-number parameter,
   where the library's own symbols carry them. Comment set by `run_altium_script` on the
   library (`Comp.Comment.Text`); the part number set on the placed parts by
   `edit_schematic` `set_parameter` instead, since the sandbox says never to register
   objects into a library. Local: `comment` and `parameters` [{name, value, visible}]
   arguments. New.
3. `get_screenshot` for `sch` has no zoom: the earlier entries' point (fit), met again,
   now for a part rather than the sheet. `RunProcess('Sch:Zoom')` and
   `Client.SendMessage('SCH:Zoom', 'Action=Selected', 255, Client.CurrentView)` with three
   parts selected both left the view where it was. The parts were checked by data instead.
   Local: `zoom_to` designators for `sch` as for `pcb`. Met again.
4. Swapping three parts onto a symbol of other geometry with every pin where it was: one
   `edit_schematic` (3 `delete_component`, 3 `place_component` at the old origin plus the
   offset between the two symbols' origins, 3 `set_parameter`), then `move_text` for the
   designators `check_schematic` suggested; nets unchanged against the reference netlist.
   Held.
5. `create_schematic_symbol` with `footprints: ["<name>"]` (no library) reported the
   footprint linked, `problems` empty, but the parts placed from the symbol had no
   footprint in Altium: the footprint was in an installed vendor `.PcbLib`, not in the
   project's libraries, and the link held no location. Found by the owner. Fixed by
   setting `DatafileLink(0).Location` to the `.PcbLib` path on the library symbol and on
   the placed parts by `run_altium_script`. Reported success with a wrong result. Local:
   resolve a name-only footprint at creation and put it in `problems` when no project
   library holds it, or fill the location from the installed library that does. The
   caller's error too: the library path should have been given. New.

6. Point 1 met a third time, later the same day: one `edit_schematic` `place_component`
   of a 2-pin symbol (four arcs) left all four body primitives without the flag. So it is
   not one symbol's fault: of six parts placed by `place_component` today, three came in
   without it. Fixed by the same toggle.
7. The owner asked to stop the resident bridge. No tool does it; done by writing the
   `stop` file in `resident\<tag>\` as the README describes, and `get_server_status`
   then showed no window. The next call started it again. Local: a `stop_resident` tool,
   or a line in `get_server_status`'s description saying how. New.

About 40 calls (`get_server_status` 2, `get_symbol_primitives` 6, `get_schematic_data` 2,
`create_schematic_symbol` 2, `edit_schematic` 2, `check_schematic` 2,
`get_erc_violations`, `get_screenshot` 4, 13 `run_altium_script`); one script failed on
"Undeclared identifier: IsNotAccesible", as the earlier entry said it would.

Sorted into A71 (1, 6), new; A65 (2), new; A60 (3), new; A66 (5), new; A34 (7), part (f). Not filed (4): a swap that held, a lesson.

**2026-11-22: token cost of seventeen design sessions, measured from their transcripts**

Release `bin\0.7.0-20261115-172812` (the sessions of 2026-11-18 to 20).

1. Read from the `usage` of every reply in the transcripts of seventeen schematic and
   library sessions that called the server: 343.5M tokens of context sent in all, peaks of
   160k to 420k context, and one session of 208 turns, never compacted, that grew from 71k
   to 880k and sent 99M by itself. Most of that is the session's length, every turn sending
   the whole context again; the server's results are the part that is its own. Where they
   were largest, in characters of result summed over the seventeen sessions: A49 met again,
   `get_erc_violations` up to 105k in one session (6 calls) and 76k in another (2 calls);
   A46 and A58 met again, `build_schematic` 142k of results and 171k of input over 14 calls
   in one session, the inline sheet going in and the whole pin map coming back each time;
   A57 met again, `get_symbol_primitives` and `get_footprint_primitives` 20k to 44k in a
   session each, `get_project_components` 63k in one (7 calls). Seven `get_screenshot`
   images in one session were next to nothing beside them. Lesson: these four items are
   where the server's share of a design session's cost sits; a summary by default with the
   detail on request (A49's proposal) is the pattern for each.

Sorted into A49 (1), met again; A46 (1), met again; A58 (1), met again; A57 (1), met again.

**2026-11-23: scenario test of a release grouping ERC results, leaving out suppressed violations and refreshing the compile (A49, A50, A48)**

Release `bin\0.7.0-20261123-001227` (build `0.7.0-ad25-20261123-001227 891ee59`), Altium
Designer 25, resident bridge `this_build` from the first call. 30 calls, 0 errors, 30.4k
characters of results (10 `get_erc_violations` 1.1k to 1.8k each, 15 `run_altium_script`).

1. A49, held. A test project of eight copies of one small sheet (net scope set so each
   sheet keeps its own nets): 400 violations, 239 listed in 5 groups, 161 suppressed.
   `get_erc_violations` returned 1.6k to 1.8k characters; the same reply in the old
   format, built from the full-list file, is 45k. Group counts sum to `total` and to
   `errors` (235) and `warnings` (4); `compile=false` gives the same groups; the full-list
   file holds all 400, each marked. Reported success, rightly.
2. A49, small: `first` often holds one text three times. A violation's detail does not
   name its sheet, so on repeated sheets the first three of a group read the same
   ("Net X has only one pin (Pin J1-4)" x3, "Duplicate Net Names Wire X" x3): two of the
   three lines tell nothing. Local: the first three distinct details, or the sheet with
   each. New.
3. A50, held. A sheet with 23 active no-ERC markers (`SuppressAll`) on unused connector
   pins: earlier releases listed 23 "Nets with only one pin" errors there (27 in all), and
   a test baseline had counted them as real; now `total` 4, `suppressed` 23, and Altium
   counts exactly 23 active markers. With the markers removed from four of the eight
   copies of item 1 (and the project reopened, see 5), 92 of those errors moved from
   `suppressed` to the list. A second project with no markers: 5 warnings, 0 suppressed,
   as before.
4. A48, held for edits. A placed part's current footprint renamed through its
   implementation by script, no notices, modified flag left false:
   `get_project_components` gave the new name; the control, the same edit read through a
   script's own `DM_Compile`, gave the old one. A custom sheet size of 2000 x 2000 mil set
   directly: `get_erc_violations` gave 100 "Object not completely within sheet
   boundaries". The sheet's and the project's modified flags stayed 0 through both tools.
5. A48 does not reach objects a script removed. A no-ERC marker removed with
   `RemoveSchObject` inside `PreProcess`/`PostProcess` and no notice for the removed
   object, sheet open: `get_erc_violations` still compiled it in, its violation still
   suppressed. At scale: 92 markers removed from four open sheets and the sheets saved,
   `suppressed` stayed 345 over two calls; only after the project was closed and reopened
   did it read 161 with 92 more listed. A marker removed with
   `SchServer.RobotManager.SendMessage(Doc.I_ObjectAddress, c_BroadCast,
   SCHM_PrimitiveRegistration, O.I_ObjectAddress)` after the removal came through at once.
   Reported success with a stale result. The refresh sends end notices for the objects the
   sheet still holds, so a removed one is never named. Local: the removal notice in
   `run_altium_script`'s description beside the one for new objects, and a usage line
   under A48; or a check of the compile's object count against the sheet's. New.
6. Lesson, sandbox: an object stored in `List1.AddObject` and read back as
   `List1.Objects[j]` is not the interface. `Doc.RemoveSchObject(List1.Objects[j])` ran
   with no error and removed nothing (the script reported 23 removed per sheet, the sheets
   saved with all 23), and `List1.Objects[j].I_ObjectAddress` failed "Undeclared
   identifier: I_ObjectAddress", the sandbox's diagnosis reading it as a call on nil.
   Re-iterating for the first object each time worked. Reported success with nothing done.
   Local: a line in the description that `List1..3` keep strings, not objects. New.
7. At the start, the project Altium had in focus, a user's design (not a test project),
   was modified, its document list holding three `PCBn.PcbDoc` and one `Sheet1.SchDoc`
   with no path, unsaved; and the Projects panel held two `MCPResident.PrjScr`, this
   build's and an earlier tag's. Left as found. The pathless sheet is A26's leftover again;
   the three pathless boards are new of their kind (some tool or test made boards while a
   user's project had focus). A26, A34, met again.

Sorted into A74 (2), new; A48 (5), failed; A75 (6), new; A26 (7), met again; A34 (7), met again; A44 (7), met again. Held: A49 (1); A50 (3); A48 (4).

**2026-11-23: scenario test of a release listing distinct ERC details and telling scripts to send the notice for a removed object (A74, A48 (b) in part)**

Release `bin\0.7.0-20261123-031122` (build `0.7.0-ad25-20261123-031122 6aa0661`), Altium
Designer 25. 37 calls, 0 errors, 31.0k characters of results (14 `run_altium_script`, 13
`get_erc_violations` 0.6k to 2.1k each).

1. A74, held. On eight copies of one small sheet, checked against the full-list file where
   it was read: groups of 35 (5 distinct texts), 127 (28) and 92 (23) each gave three
   different lines where their first three violations were one text; a group of 4 with one
   distinct text gave one line and `count` 4. No `first` repeated a text in any of the 13
   replies, the group counts summed to `total` in each, and `compile=false` gave the same
   groups.
2. A48 (b), the part built held: the notice the description names
   (`SCHM_PrimitiveRegistration` naming the object just removed) is enough. 92 no-ERC
   markers removed by script from four open sheets (4, then 88 in one process per sheet),
   nothing saved: the next `get_erc_violations` followed each time (`suppressed` 345, 337,
   161). Saved, the project closed and reopened: the same list of errors and suppressed
   violations. The notice worked for a marker sent inside the process and after it, and
   for a removed part inside it (`get_project_components` dropped it at once).
3. A48 (b), still open as written: with no notice a removed marker stayed compiled in
   (its violation still suppressed) and a removed part stayed listed (15 components where
   the sheet held 14), both reported success with a stale result. The item's usage (save
   the sheet, close it, open it again) cured both, so it holds for a part too, which the
   item marks as not probed.
4. A48 (b), no gap seen in the server's own removals: `edit_schematic`'s `delete_at` of a
   no-ERC marker and `delete_component`, unsaved, were both in the next compile. A48's
   refresh for edits held again (a footprint and a sheet size set by script with no
   notice, the modified flags still 0).
5. New, small, cause not looked for: Altium's component revision warnings ("Can't perform
   revision status validation: Failed to connect to server") come and go between compiles.
   In 2 of 12 compiles all four were absent: `total` 235, then 239 for the same sheets
   after the project was reopened; on another copy 1, where 5 was expected. Reported
   success. Lesson: compare two compiles by `errors` and their groups, not by `total`.
6. New, small: after the test's projects were closed by script, the focused project was
   the resident's own `MCPResident.PrjScr` (Free Documents at the start, the resident not
   yet started), which is what a tool called without `project_path` takes. Seen in a
   workspace read, no tool called so. Bears on A34.

Sorted into A76 (5), new; A48 (2, 3, 4), checked; A34 (6), met again. Held: A74 (1).

**2026-11-23: scenario test of a release mapping pins by number, taking spec files, placing parts of multi-part symbols, leaving the focused project as found and setting a placed part's footprint (group 2)**

Release `bin\0.7.0-20261123-103915` (build `0.7.0-ad25-20261123-103915 8f57314`), Altium
Designer 25. 42 calls, 0 errors, 39.6k characters of results (14 `run_altium_script`, 8
`build_schematic`, the largest 9.5k: a map of 162 pins with no wires).

1. A46, held. A build with no wires of five parts (two 2-pin parts, a 2-pin part, a large
   multi-part FPGA symbol as part A and another as part B) gave `pin_map` keyed by number:
   162 pins, 32 of one part's pins sharing the name `I/O` all kept, each point equal to the
   saved file's pin end. With wires: `pin_counts` and `pin_map_file` only (1.3k characters),
   the file's points equal to the sheet's.
2. A58, held. `build_schematic(spec_file=...)` built a sheet into a project from a file (two
   parts, a parameter that is not ASCII, two wires, a net label, a power port, a note), each
   read back from the saved file; `edit_schematic(spec_file=...)` in mm moved a part and
   placed a no-ERC marker, saved. Refused before Altium: a relative `spec_file`; a file
   holding `wire` ("not an argument it can give"); `wires` inline and in the file; `unit`
   inline and in the file for `edit_schematic`.
3. A45, held. A symbol saved showing part C was placed as part A with no `part`, and
   `warnings` named parts B, C; `part="B"` placed part 2 only; `place_component` with
   `part="C"` placed part 3; `part="G"` refused in both tools ("has no part G (its parts are
   A to C)"), in the build as a missing part.
4. A45, new, failed: the parts of one component placed by the two tools do not compile as
   one. Part B placed by `build_schematic` and part C, same designator and library, by
   `edit_schematic` `place_component` on the same sheet: ERC "Duplicate Component
   Designators" for it and "unused sub-part(s) (1) and (2)" and "(1) and (3)", and
   `get_project_components` lists the designator twice. Parts B and C both placed by
   `place_component` compile as one. In the saved file the build's part has
   `DESIGNITEMID` set, `SOURCELIBRARYNAME` `*` and no `LIBRARYPATH`; `place_component`'s
   has `LIBRARYPATH` and `SOURCELIBRARYNAME` the library's file name and no
   `DESIGNITEMID`. `edit_schematic`'s `warnings` treated them as one component ("part A
   not placed on this sheet"). Reported success. Local: one way of filling the library
   fields in both tools. New.
5. A26, held. Another project focused (unmodified, its board in front): a build into a new
   project (twice), a build with no `project_path` (the sheet a free document), and a
   build into the new project with a missing part (the sheet left a free document, named
   in the error, the target project unchanged) each left the focused project's flag 0,
   its four documents, and its files' md5 as they were. `detached_from` is the full path,
   `sheet` the path saved.
6. A26, A61, new, small: after a `build_schematic` the focused project is Free Documents.
   The symbol library the build used, already open, is left in front, where the other
   project's board was before. A tool called without `project_path` next reads Free
   Documents (`get_project_info` did). Not reported in the result. Local: the document
   that was in front shown again at the end.
7. A27, held. A footprint given for a symbol whose library footprint is current became
   the only current one (added by name, no library), the library's mark gone; a name the
   symbol already holds, given in another case, was made current, not added again.
8. A71, held. A symbol shown in the library editor while placed, by `build_schematic` and
   by `place_component`: every body graphic of both parts `IsNotAccesible=T` in the saved
   file, as on every other part placed in the test.
9. A56 (a), held. `set_footprint` made the footprint given the only current one, linked to
   the `.PcbLib` given (`MODELDATAFILE0` in the saved file), the part's other three kept
   not current; a footprint the part already had was linked to the new library, not added
   twice. Refused before Altium, the whole call: a `.SchLib` as the library, a footprint
   the saved `.PcbLib` does not hold, a library not there. An unknown designator failed
   that operation only, the rest applied.
10. Recipes and A75, held for the file: `run_altium_script`'s description names the recipes
    file by a path that exists, and says `List1..3` keep strings. Three recipes run as
    written, placeholders filled: A55 on a project not focused gave its flag and three
    documents, as the build had them; A34 (f), the `stop` file closed the form within
    about 7 s and the next call started it again, the file gone; A52 with `eNoERC` on a
    sheet with one marker: the next compile dropped it (`suppressed` 1 to 0, the
    single-pin violation it hid listed). Small: A52's section says the script "does not
    mark the sheet modified", but the sheet was modified after it (flag set, listed in
    `unsaved_in_altium`), as the notice does. Local: that sentence corrected.

Sorted into A77 (4), new; A61 (6), met again; A78 (10), new; A34 (10), checked; A52 (10), checked. Held: A46 (1); A58 (2); A45 (3); A26 (5); A27 (7); A71 (8); A56 (9, 10); A75 (10); A55 (10), usage.
