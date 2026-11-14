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
