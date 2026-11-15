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
