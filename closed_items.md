# Closed Items

The A-items closed, each with its record: run and held, merged upstream, or decided
against. A newly closed item goes at the end of `## Closed`; the runs done follow. The
items still open or waiting are in [`open_items.md`](open_items.md). Split from that file
on 2026-11-15, when it took the `backlog` plugin's format.

## Closed

### A4 - `get_unrouted_connections` leaves the board modified - CLOSED 2026-11-12

On a freshly opened board
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
`build-20261112-120520`. Closed: the scenario test of that build held (2026-11-12, third
entry, 3): on a freshly opened board `analyzed` false and the board still "open" after
the call; on a board with unsaved changes `analyzed` true.

### A6 - `get_layout(include_touching=true)` returns whole pours - CLOSED 2026-11-12

For two small chip parts it
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
`build-20261112-120520`. Closed: the scenario test of that build held (2026-11-12, third
entry, 4): 5.0k characters for the same call, was 8.6k, the two board-wide ground pours
as `beyond_area` entries.

### A17 - `run_drc` leaves the board modified - CLOSED 2026-11-14

On a freshly reopened board, after
`get_board_summary`, `get_pcb_layer_stackup` and `get_all_nets` the state was still "open";
after one `run_drc` it was "modified", also on a call that reported `ran` false (A18), so
it is something the tool does before Altium's check runs. Same effect as A4: a read makes
Altium ask to save on close and fails the "nothing unsaved" check. Whether Altium's own
DRC from the menu marks the board too was not checked. Local: find the step that marks it
and leave an unchanged board unmodified, as A4 did. Usage until then: close the board with
its modified flag cleared. (2026-11-12, third entry, 5.)
Fixed in `338bfdb`: the check itself marks the board, whenever it finds violations, as it
replaces the board's violation markers (a board with none stays unmodified). The script
reads the flag before `PCB:DesignRuleCheck` and clears it after when the board had no
unsaved change; the result gives `board_modified`. A board with unsaved changes stays
marked. Live test `tests/test_live_drc.py` (`ALTIUM_LIVE=1`, a copy of the WiFi example
board given a via-to-via clearance rule it fails, 8 violations, saved and reopened): passes
in AD25, fails on the old script. Released in `build-20261114-145312`. Closed: the
scenario test of that build held (2026-11-14, second entry, 1): a freshly opened board
with no unsaved change gave `board_modified` false after one full `run_drc` with 4
violations, still "open" in `get_project_info`, the violation objects still on the board;
with unsaved changes `board_modified` true. The project file is marked instead (A19).

### A18 - `run_drc` returns a stale report when the check did not run - CLOSED 2026-11-14

On the first DRC
after a board was closed unsaved and reopened by script it returned `success` false, `ran`
false, "the Design Rule Checker dialog never appeared", as it should, but the reply still
carried `report` with per-rule counts and `violation_count` 4: the file a previous run had
left, not marked stale, and it reads as a result. The same call repeated at once ran
normally. Local: no `report` or counts when `ran` is false (or the file's time checked
against the call's), and find why the first DRC after a reopen does not start. Usage until
then: call again. (2026-11-12, third entry, 6.)
Fixed in `338bfdb`. Not a stale report: the check had run, and the report and counts were
its own. The dialog driver looks a quarter second after its press for the dialog to
close; a small board is checked and answered within that time, the driver is stopped with
the close unseen, and `ran` read false. Reproduced once in sixteen checks of the example
board after a save and reopen, with the "could not be started and was closed" message. The
driver now records the press, and a reply after a press with no close of ours counts as a
check that ran; a check that did not run gives no `report`. Offline tests in
`test_drc.py`; live test in `tests/test_live_drc.py` with the close hidden from the driver:
passes in AD25, fails on the old Python. Not explained: the entry's message was "never
appeared", which says the driver saw no dialog at all; not reproduced. A17's modified
board on that call fits the check having run. Released in `build-20261114-145312`.
Closed: the scenario test of that build held as far as met (2026-11-14, second entry, 2):
three closes unsaved and reopens by script, and the first `run_drc` after each gave `ran`
true with the report that call wrote. The `ran` false path was not met live; the offline
tests cover it.

### A19 - `run_drc` leaves the project file modified, and `get_project_info` does not say so - CLOSED 2026-11-14

The first `run_drc` after a project is opened marks the `.PrjPcb` modified while the
board stays unmodified (A17 held). Saved, the project file gains a `[GeneratedDocument1]`
section naming the DRC report's `.html` in the project's output folder, and two existing
sections move. Later checks do not mark it again (the entry is there), also after the
output folder is deleted; a fresh open of the project does, on its first `run_drc`.
`get_project_info` gives `modified_document_count` 0 and no entry for the project file, so
the "nothing unsaved" check reads clean while closing the project asks to save it. Near
A5 (files a read leaves behind). Local: leave the project as the tool found it, as A17
does the board (its flag read before the check and cleared after when it had no unsaved
change), and give the project file's own state in `get_project_info`. Usage until then:
close the project with its flag cleared (`SetModified(False)` on the `.PrjPcb`
document). (2026-11-14, second entry, 3.)
Cause: the first `PCB:DesignRuleCheck` after a project is opened adds its report to the
project's generated documents, which marks the `.PrjPcb` document modified, whether the
check finds violations or not (reproduced 2026-11-14 on a copy of the WiFi board's
project of Altium's Mini PC example: 0 violations, project file marked). `get_project_info`
walked the project's logical documents only, so the project file itself was never read.
Fixed in `7a8ff22`: `run_drc`'s script finds the project the board is
a document of (none for a board under Free Documents), reads its document's flag before
the check and clears it after when the project had no unsaved change, as A17 does the
board; the result gives `project` and `project_modified` for a board in a project. The
generated-documents entry stays in memory and is saved with the project's next save.
`get_project_info` gives `project_modified` (the `.PrjPcb` document's own flag) and counts
it in `modified_document_count`. Live test `tests/test_live_drc.py`, class
`LiveDrcProjectTest` (`ALTIUM_LIVE=1`, a copy of the WiFi project folder, its board given
a via-to-via clearance rule it fails and saved, then the project opened with
`DM_OpenProject` before its board, fresh for each test, everything under the copy closed
unsaved after): before the fix both tests failed ("True is not false : the check left the
project file modified"; with the project marked by script, `get_project_info` had no
`project_modified` and `modified_document_count` 0). After: 5/5 of `test_live_drc` pass
in AD25 (the two new, A17's two, A18's one); the old class now also closes the DRC
reports its checks opened (helper `close_all_under` in `tests/live_altium.py`, with
`open_project`). Offline: 271 tests pass.
Decided 2026-11-14 by the run, not the owner: a board under Free Documents gives no
`project` or `project_modified`, and the project file is not added to `documents` in
`get_project_info`, because Free Documents has no file to save, and `documents` lists the
project's own documents, which a caller walks by kind.
Local: on `ad25`, in `7a8ff22`. Released in `build-20261114-163431`. Upstream: not yet decided.
Closed: the scenario test of that build held (2026-11-14, third entry, 1): the first full
`run_drc` on a freshly opened project gave `project_modified` false and the `.PrjPcb`
document's flag read 0 by script; a project marked beforehand read `project_modified` true
and `modified_document_count` 1 in `get_project_info`, and stayed marked.

### A20 - `run_drc`'s report ignores the rule filter - CLOSED 2026-11-14

`run_drc(rules=[one kind])` whose
filter matched no violation still returned the per-rule report of all 14 rules, about
2.1k characters a call; nine calls were 26k of a session's 47k characters.
(2026-11-14, second entry, 4.)
Cause: `run_drc` filtered the violations with `drc.matches` and then attached the parsed
`.drc` report whole. A report entry names a rule by its kind and settings (`Clearance
Constraint (Gap=0.2mm) (All),(All)`), never by the rule's own name.
Fixed in `aeb2a9f`: with `rules` given, `drc.narrow_report` keeps the
report entries whose kind is one of `rules` (compared as `matches` compares, `rule_key`:
any case, spacing, a trailing "Constraint"), so "Clearance" keeps the Clearance entries
and not Hole To Hole Clearance. A rule's own name in `rules` keeps the kinds of the
violations that name picked (a name with no violation keeps nothing). `report` then also
gives `rules_omitted`, the number of entries left out; its `violations`, `waived` and
`stopped` stay the whole check's. Without `rules` the report is whole, as before, and
`nets` and `area` do not narrow it. Offline: two tests in `tests/test_drc.py`. Live test
`tests/test_live_drc.py`, `LiveDrcTest.test_report_lists_only_the_rules_asked_for` (a copy
of the WiFi board with its via-to-via clearance rule): `rules=["Width"]` gives a report of
the Width entries only, with `rules_omitted` and the check's totals; `rules=["Clearance"]`
the Clearance entries, the via rule's 8 violations among them; no `rules`, the whole
report. Before the fix (narrowing switched off) it failed: "Items in the first set but not
the second: 'powerplaneconnectrule' 'unroutednet' 'clearance' 'shortcircuit'" (all 7
entries listed for `rules=["Width"]`). After: 6/6 of `test_live_drc` pass in AD25;
offline: 273 tests pass.
Decided 2026-11-14 by the run, not the owner: the report is narrowed to the rules asked
for only, not also to "the rules with violations" (the other half of the item's first
wording), because the plan's decision is the filter alone, and a rule that was checked
and passed is a fact the caller may be asking for.
Local: on `ad25`, in `aeb2a9f`. Released in `build-20261114-163431`. Upstream: not yet decided.
Closed: the scenario test of that build held (2026-11-14, third entry, 2): one report
entry and `rules_omitted` 13 for one kind, the electrical clearance entry only for
"Clearance", a rule's own name keeping its kind; a filtered call 0.66 to 0.89k characters,
was 2.1k.

### A5 - Read calls leave files in the project folder - CLOSED 2026-11-14

`run_drc` writes `Design Rule Check -
<board>.drc` and `.html` beside the board or in `Project Outputs for <project>`, and
compiling (`get_erc_violations`, `get_project_components`) leaves `<project>.PrjPcbStructure`.
On a project that must stay untouched they were deleted by hand. Local: an option on
`run_drc` to delete its report once read (or write it elsewhere, if Altium allows), and the
compile calls to remove a `.PrjPcbStructure` they created where none was before.
(2026-11-12, 5.)
Cause: `run_drc` is Altium's own check, which writes its report (`Design Rule Check -
<board>.drc` and `.html`) beside the board or in the project's output folder, making that
folder when there is none; the tool read the report and left it. The compile calls write
nothing. On a copy of the WiFi project of Altium's Mini PC example with its
`.PrjPcbStructure` removed, `get_erc_violations` and `get_project_components` (the only
tools that compile, `DM_Compile`), the project opened by the call or before it, left the
folder as it was, also 5 to 15 s later; the file appeared when the project was closed, and
as well after a project was only opened and closed with no call at all. An existing one
was written back with the same content. So it is Altium's close of the project, not the
call.
Fixed in `d7e5c32`: once the Design Rule Checker dialog is up, before
the check runs, `run_drc` notes the folders where the report may go and any report already
there (`drc.snapshot_reports`), for the board the bridge script names in the exchange
folder's `last_board.txt` as it brings the board to the front (so also with no
`board_path`). Once the report is read it deletes the report and its `.html`, puts an
earlier report back as it was (bytes and times), and removes the folders the check made,
when empty (`drc.remove_report`); a report left by a check that did not run goes too. The
result's `report` gives `deleted` true and no `path`, `restored` true when an earlier
report was put back, `folder_left` when a folder the check made holds something else;
`keep_report=true` keeps it, with `deleted` false and `path` naming the `.drc`. A report
not deleted (a file error, the board's folder not known) keeps its `path`, with
`delete_error`. Deleting the `.html` the project lists among its generated documents (A19)
brought up no dialog and marked neither the project file nor the board; the entry stays in
the project's memory and is saved with its next save, as before. An output folder the
project sets outside the board's folder is not looked in, as before (no `report`, nothing
deleted). `get_erc_violations` now says when Altium writes the structure file.
Live tests in `tests/test_live_drc.py` (`ALTIUM_LIVE=1`; folder listings with each file's
size and time, helper `listing` in `tests/live_altium.py`): on the copy of the WiFi
project folder, `LiveDrcProjectTest.test_check_leaves_the_project_folder_as_found`
(listing equal, `deleted` true, no `path`, project and board unmodified),
`test_keep_report_keeps_it` and `test_an_existing_outputs_folder_and_report_stay` (an
outputs folder holding another file and an earlier report: all as they were); on the copy
of the board under Free Documents, `LiveDrcTest.test_check_of_the_focused_board_leaves_its_folder_as_found`
(no `board_path`, the report beside the board); and `LiveCompileFolderTest`, two tests (no
structure file where none was; an existing one unchanged). Before the fix the four
`run_drc` tests failed: "Lists differ: ... ('Project Outputs for WiFi_miniPCIe',) ... : the
check left files in the project folder", the earlier report overwritten (2428 bytes for
17), `keep_report` an unexpected keyword argument, the focused board's report left beside
it; the two compile tests passed. After: 12/12 of `test_live_drc` pass in AD25. Offline:
281 tests pass (8 new in `tests/test_drc.py`, for `remove_report` and the dialog driver's
`before_press`).
Usage: a project that must stay untouched gets a `.PrjPcbStructure` when Altium closes it;
delete it after the close.
Decided 2026-11-14 by the run, not the owner: the compile calls are left unchanged, their
part of the item settled by the test passing, because no call writes the
`.PrjPcbStructure`: Altium writes it when the project closes, compiled or not, after the
call has returned, so a call has nothing to remove and could reach the file only by
closing a project the caller may have open.
Decided 2026-11-14 by the run, not the owner: an earlier report in the same place is put
back as it was (bytes and times), not left overwritten by this check's, because the call
is to leave the folder as it found it, and the earlier report is someone's own.
Decided 2026-11-14 by the run, not the owner: the folder is noted when the dialog is up,
for the board named in `last_board.txt`, not by a call made before the check, because with
no `board_path` only the bridge script knows the board, and that moment comes before the
check writes anything at no extra call; when the reply names another board nothing is
deleted (`delete_error`).
Local: on `ad25`, in `d7e5c32`. Released in `build-20261114-163431`. Upstream: not yet decided.
Closed: the scenario test of that build held (2026-11-14, third entry, 3): the project
folder's listing (names, sizes, times) equal before and after a full and three filtered
checks, `keep_report` kept the report and the next check put it back (`restored`, bytes
and times unchanged). The folder's own modification time does change each check, as the
output folder is made and removed in it (third entry, 4): a caller compares the files,
not the folder's time. `.PrjPcbStructure` is written when the project closes, as found.

### A3 - `get_unrouted_connections` reports 0 for a net that is open - CLOSED 2026-11-14

After the only track
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
Met again 2026-11-12 (third entry, 7) without `AnalyzeNet`: a board saved with one
connection open (DRC: 1 Un-Routed Net), closed and reopened, gave `analyzed` false and
`connection_count` 0, and no `eConnectionObject` on the whole board; before the save, on
the modified board, `analyzed` true also gave 0. So the ratsnest built at open lacks the
connection objects too. 3D view throughout, 2D not tried.
Probe 2026-11-14, on copies of the WiFi board of Altium's Mini PC example, in 2D and in 3D
view (switched with Altium's "3" key): the connection objects are there, and
`Board.AnalyzeNet` is what removes them. The track of a 2-pad net deleted with
`delete_pcb_objects` left one connection object on the net at once, in either view;
`Board.AnalyzeNet` on that net then left none, in either view, and none came back (later
scripts, `Board.ViewManager_FullUpdate`, `PCB:Zoom` redraw, `PCB:ShowConnections`,
`Net.ConnectivelyInValidate`, `PCBServer.PreProcess`/`PostProcess` around it). A copy
saved with the connection open and opened under a new name had it; the same board closed
and reopened by script did not when it had been analyzed before its save: the reopened
board is the one left in Altium's memory, not read again. So every case of this item is
`AnalyzeNet`: the first call analyzed the modified board, and the reopened board was that
same analyzed board. `Net.Rebuild` (and `Board.CleanNet`) brought the connection back, in
either view. On five nets with their copper deleted (2-pad, 3-pad and with vias), the
connection objects after `Net.Rebuild` were per net those of a DRC Un-Routed Net run, 6 in
all, while the tool gave 0. `Net.Rebuild` on every net of a freshly opened board changed no
track and left it unmodified (WiFi: 27 nets, 579 tracks, 0 connections; Mini PC
motherboard: 837 nets in about 3 s, 48,299 tracks, 564 connections before and after),
where `AnalyzeNet` had joined 11 of the motherboard's tracks (A4). `place_copper` also ran
`AnalyzeNet` on the nets of its copper: a track laid half way between the two pads left
no connection object (`Net.Rebuild` then gave the 1). Copper added by `route_track`
(which does not analyze) updated the connection at once. The DRC way would have met a
further stop: after copper under a pour is deleted, Altium answers the Run press with a
"Design Rule Check" message (Run DRC, Cancel, Repour Polygons and Run DRC) that the
dialog driver does not press, and `run_drc` waits (pressed by hand in the probe).
Not explained: the 2026-11-12 reproduction saw no connection object before analyzing,
after its own script removed the copper; `delete_pcb_objects` registers each removal with
the board, which a bare `RemovePCBObject` may not.
Cause: `get_unrouted_connections` and `place_copper` ran `Board.AnalyzeNet`, which removes
every connection object of the net it analyzes, open or not, in 2D and 3D view.
Fixed in `2f3393a`: `get_unrouted_connections` rebuilds the
connections of the nets it reads with `Net.Rebuild` on every call, the board's modified
flag put back when it had no unsaved change (A4); its result no longer has `analyzed`.
`place_copper` rebuilds the nets of its copper with `Net.Rebuild` instead of analyzing
them, so the connections its copper leaves open stay on the board.
Live test `tests/test_live_unrouted.py` (`ALTIUM_LIVE=1`, copies of the WiFi board, closed
unsaved): the tracks of a 2-pad and a 3-pad net deleted, then the read on the changed
board and again after save, close and reopen, in 2D
(`test_deleted_copper_leaves_open_connections`) and in 3D
(`test_deleted_copper_leaves_open_connections_in_3d`), each expecting
`{"NetC39_1": 2, "NetDS1_2": 1}` with the pads named, the board's tracks unchanged and the
reopened board left unmodified; and
`test_place_copper_keeps_the_connections_it_leaves_open` (a half-way track leaves the
connection object, the rest closes it). Before the fix all three failed: "AssertionError:
{} != {'NetC39_1': 2, 'NetDS1_2': 1}" (both views) and "0 != 1 : place_copper removed an
open connection"; A4's test passed. After: 4/4 of `test_live_unrouted` pass in AD25, the
3D test run in 3D; `test_live_layout` (2, `place_copper`) and `test_live_drc` (12) pass.
Offline: 281 tests pass.
Decided 2026-11-14 by the run, not the owner: no DRC fallback and no `source` field,
because the probe found a way that gives the connection objects reliably (`Net.Rebuild`,
equal per net to DRC's Un-Routed Net, in both views), and the DRC way also stops on
Altium's repour message after copper under a pour was deleted.
Decided 2026-11-14 by the run, not the owner: the nets read are rebuilt on every call, also
on a board with no unsaved change (its flag put back), not only on a modified one, because
a board closed and reopened in the same Altium keeps the connections it had in memory, and
a rebuild changes no copper and is quick.
Decided 2026-11-14 by the run, not the owner: `place_copper` rebuilds instead of analyzing
too, because its analysis took the open connections of every net it touched off the board,
for Altium's own view and any reader that does not rebuild; `Net.Rebuild` over
`Board.CleanNet`, which brought the connection back too, because only the rebuild was
checked to change no copper on whole boards.
Decided 2026-11-14 by the run, not the owner: `analyzed` is dropped from the result, because
every call now rebuilds the nets it reads, so it would always be true.
Decided 2026-11-14 by the run, not the owner: the 3D test switches the view with Altium's
"3" key, Altium brought to the front (no key is sent when it is not), and tells 2D from 3D
by the share of the top layer's red in a screenshot, skipping when either cannot be done,
because no script call switched the view (`PCB:SwitchTo2D3D` with `Mode=3D`, `Mode=Toggle`,
`ViewMode=3D` or none, by `RunProcess` and `Client.SendMessage`) and no document or view
property read differs between the two. A board may open in 3D (a copy under a name last
shown in 3D did), so the test leaves Altium in 2D.
Local: on `ad25`, in `2f3393a`. Released in `build-20261114-180059`. Upstream: not yet decided.
Closed: the scenario test of that build held (2026-11-14, fourth entry, 1): on a copy of a
fully routed board the tracks of a 3-pad net deleted gave the 1 connection DRC gave, the
same after save, close and reopen, the board left "open"; a second net's via-to-via gap
gave its 1 too, and the whole board read 0 once routed again.

### A9 - `run_altium_script`'s compile check reads one declaration per `var` line - CLOSED 2026-11-14

A
leading `var Board : IPCB_Board; Net : IPCB_Net; i : Integer;` on one line was refused
before it ran, "'Net' is not declared"; one declaration per line passed. Delphi allows
several. Local: read every declaration of the line. (2026-11-12, second entry, 2.)
Cause: `split_var_block` took a line as a declaration only when it held exactly one
(`Name1, Name2 : Type;`), and `declared_names` read only what came before the first
colon of a line. A `var` line with several declarations therefore gave one name
(`Board`), the others (`Net`, `i`) were never known to `check_script`, and a later line
of several declarations ended the block, leaving it in the script body. `lint_script`
took every name of a line as `IDispatch` when any declaration of it was.
Fix: `sandbox.py` reads every declaration of a line
(`declarations`, with `declared_names` built on it): a declaration line may hold several,
the `var` line and the lines after it, a comma list (`a, b : Integer`) included, and
comments are ignored; `lint_script` treats as untyped only the names of the `IDispatch`
declarations. Nothing that reaches Altium changed: the text put into the template is the
same lines as before.
Offline tests in `tests/test_sandbox.py` (6 new). Before the fix, 6 failed: "AssertionError:
Lists differ: ['Board'] != ['Board', 'Net', 'i']" (`declared_names` of the line),
"'Net' is not declared. Use a sandbox variable or declare it in a leading var block"
(`check_script` on `var Board : IPCB_Board; Net : IPCB_Net; i : Integer;` and a
body using all three), the block ended at a line of two declarations ("Lists differ: []
!= ['A : Integer; B, C : String;', 'D : Double;']"), a comment's `E : Integer;` read as
a declaration, and a lint check ("1 != 2") on an `IDispatch` line. After: 50 pass in
`test_sandbox` and 288 in the offline list of `.github/workflows/tests.yml`.
Not covered: a `var` section inside a nested procedure or function; the checker reads
only the script's leading `var` block, as before.
Decided 2026-11-14 by the run, not the owner: `a, b : Integer` and several declarations on
a line read by one regular expression for a declaration, used for the block's split, the
names and the lint, because one definition keeps the three from disagreeing again.
Decided 2026-11-14 by the run, not the owner: a trailing comment on a declaration line
stays `//` only, as before, because `{ }` and `(* *)` after a declaration were never read
as part of the block and the item is about several declarations.
Fixed in `7ec1ed2`. Local: on `ad25`, in `7ec1ed2`. Released in `build-20261114-180059`. Upstream: not yet decided.
Closed: the scenario test of that build held (2026-11-14, fourth entry, 2): a leading `var`
line of five declarations, `i, n : Integer` among them, ran; a name declared only in a
`//` comment of that line was still refused before Altium was called.

### A21 - `run_drc` waits on Altium's repour message - CLOSED 2026-11-14

After copper under a pour was deleted,
Altium answered the dialog's Run press with a "Design Rule Check" message (Run DRC, Cancel,
Repour Polygons and Run DRC) that `run_drc`'s dialog driver does not press, so the call
waited until it timed out; the message was pressed by hand. Met 2026-11-14 in the run's
probe for A3, on a copy of the WiFi board of Altium's Mini PC example. Local: the driver
presses Run DRC (the check of the board as it is, pours not changed, so the board and the
result stay what was asked), and the result says the message was met; a live test that
deletes copper under a pour and runs the check, failing on a timeout before the fix.
Decided 2026-11-14 by the run, not the owner: A21 joins group 2 after A9, because a check
that never returns blocks every later step that runs one, its fix is in `run_drc`'s dialog
driver alone, and group 2's scenario test runs `run_drc`.
Cause: the message is a `TMessageForm` of X2.EXE titled "Design Rule Check", its buttons
`TXPBitBtn` captioned "Run DRC", "Cancel" and "Repour Polygons and Run DRC", up about a
second after the dialog's Run press (probe 2026-11-14, a copy of the WiFi board with the
tracks of two nets under its GND pours deleted by `delete_pcb_objects`). The dialog
driver pressed only the Design Rule Checker dialog's Run button and then just kept the
bridge's progress file fresh, so the command, held by the message, counted as working and
waited up to the bridge's 30 minute limit.
Fixed in `ed18a1c`: the driver (`drc.drive_dialog`) looks for the
message while it waits for the dialog to close and, every quarter second, for the rest of
the call; it knows it by its class, title and the captions of its buttons
(`drc.is_repour_prompt`: Run DRC and Repour Polygons and Run DRC, any case, `&` ignored),
never by a button's position, and presses Run DRC, a posted click as the dialog's Run
button gets. The board is checked as it is, its pours not changed. The result gives
`repour_prompt` true and a `repour_note` (the pours were not repoured and may be out of
date: `repour_polygons`, then `run_drc` again); a call that does not meet the message
gives neither. A message that does not take Run DRC after three presses, 2 s apart, is
cancelled (its Cancel button) and the result is `ran` false, with the presses in `notes`.
The board's and the project's flags are handled as before (A17, A19), and other dialogs
as before.
Live test `tests/test_live_drc.py`, class `LiveDrcRepourTest` (`ALTIUM_LIVE=1`, a copy of
the WiFi board, closed unsaved; its cleanup presses Cancel on a message left up and
closes a Design Rule Checker dialog left open, so Altium is never left blocked):
`test_check_presses_run_drc_on_the_repour_message` deletes the tracks of `NetDS1_2` and
`NetC39_1` under the GND pours with `delete_pcb_objects`, runs `run_drc` with a 90 s
limit, and expects `ran`, `repour_prompt`, no message left up, the 3 Un-Routed Net
violations those tracks leave, the pours unchanged (each pour read by the holes and
outline points of its regions: "Repour Polygons and Run DRC" changed Top_GND from 18/481
to 18/476 and found 5 violations) and the board still modified;
`test_no_repour_message_no_field`, the board unchanged, no `repour_prompt`. Before the
fix the first failed: "AssertionError: run_drc did not return within 90 s (Altium's
repour message left up)"; the cleanup answered it and the second test then passed.
After: 14/14 of `test_live_drc` pass in AD25 (the two new, and the 12 of A17 to A20 and A5). Offline: 7 new in `tests/test_drc.py` (the message known by class,
title and buttons; Run DRC pressed when it comes before or after the dialog closes, and
nothing else posted; a message that stays cancelled after three presses, `ran` false;
no message, no flag); 295 tests pass in the offline list of `.github/workflows/tests.yml`.
Decided 2026-11-14 by the run, not the owner: the message counts as Altium taking the
dialog's Run press, so the driver stops pressing the dialog when it is up, because it is
Altium's answer to that press, and waiting for the dialog to close behind it would count
presses the message holds up as failures and close the dialog.
Decided 2026-11-14 by the run, not the owner: a message that will not take Run DRC is
cancelled after three presses and the call reports `ran` false, not left up, because a
message left up blocks Altium for every later call, and a check that was cancelled must
not read as a result.
Decided 2026-11-14 by the run, not the owner: `repour_prompt` is given only when the
message was met, because a call that does not meet it gives the result it gave before,
and its absence says the pours were current.
Decided 2026-11-14 by the run, not the owner: the test reads the pours by the holes and
outline points of their regions, because a repour of the test's board changed those and
left the region count of every pour as it was.
Fixed in `ed18a1c`. Local: on `ad25`, in `ed18a1c`. Released in `build-20261114-180059`. Upstream: not yet decided.
Closed: the scenario test of that build held (2026-11-14, fourth entry, 3): with the track
of a net under a ground pour deleted, `run_drc` returned within seconds, `ran` true,
`repour_prompt` true, the pour unchanged and no message left up; on the unchanged board a
full check gave no `repour_prompt`.

### A10 - No tool to set up a project and its board - CLOSED 2026-11-14

`build_schematic` makes its sheet
outside any project, as a free document, and no tool creates a `.PrjPcb`, adds a sheet to
one, creates a `.PcbDoc` in it, or sets the board shape. The step from schematic to board
is done by hand. Local: tools to create a project and add documents to it, and to set the
board shape from an outline (mils or mm, arcs allowed) or from a closed shape on a
mechanical layer.
Found 2026-11-14 by the run's probes in AD25: `GetWorkspace.DM_CreateNewDocument('PcbProject')`
makes an unsaved project and `DoSafeChangeFileNameAndSave(<path>, 'PrjPcb')` writes its file
(29 kB of Altium's defaults). For a new `.SchDoc` or `.PcbDoc` the same call returns True and
renames the document but writes no file; a second save (`SetModified(True)`, then
`DoFileSave('')`) writes it (`DoFileSave('PCB')` did not). A new schematic is taken into the
project that has focus (a copy of the WiFi project of Altium's Mini PC example, its board in
front), a new board is not. A board outline's segments set by script read back at once, but
its area, box and `PointInPolygon` keep the old shape until `Board.UpdateBoardOutline`. An
outline arc is drawn counter-clockwise from `Angle1` to `Angle2` whichever way the outline
runs. A primitive's layer above Mechanical 16 could not be set or read by script
(`Layer_V7`, `V7_Layer` undeclared). After an add Altium may list an `ActiveBOM.VirtualBom`
document of its own, with no file and not in the project file.
Fix: four tools. `create_project(project_path)`: Altium makes the project, saved there
(the folder made when missing); refused when a file is there. `add_project_document(
project_path, document_path, create=False)`: an existing document, or with `create` a new
`.SchDoc` or `.PcbDoc` saved there and left open; the project opened when it is not, its
file saved after the add; a document already in it left as it is (`already_in_project`);
a new document a focused project took is taken out of it again (`detached_from`), its file
flag put back. The result is the project's documents read back from Altium and
`in_project_file`, the saved `.PrjPcb` read from disk. `set_board_shape(outline, unit,
mechanical_layer, board_path)`: vertices `[x, y]` or `{x, y, arc_center, clockwise}` in
mils or mm, checked in `project_setup.py` (an arc's ends on one circle within 0.1 mil, no
crossing, an area, within Altium's design space), or the free tracks and arcs of Mechanical
1 to 16 (by number or name) chained end to end (ends within 0.1 mil meet) into closed
loops, one picked; the board's outline read back (vertices in the form given, box,
`board_modified`) and compared with what was asked, a difference a failure; the board
changed, not saved. `build_schematic(project_path, sheet_path)`: the sheet saved at
`sheet_path` and added to the project, as `add_project_document`. Bridge commands
`create_project`, `add_project_document` (`other_utils.pas`), `set_board_outline` and
`board_layer_shapes` (`pcb_layout.pas`, reusing `LayoutSegment`).
Live test `tests/test_live_project_setup.py` (`ALTIUM_LIVE=1`, a temporary folder, everything
under it closed unsaved; copies of the WiFi board and project and of a library of the
SpiritLevel-SL1 example): a project made and refused a second time, its file unchanged;
a new sheet, a new board and a copied sheet added, the saved project file and Altium's
project listing all three, a repeat add and a refused add changing nothing; a new sheet and
board added while the WiFi project copy has focus, that project not given them and left
unmodified (the sheet was taken and given back, `detached_from`); `build_schematic` with
two parts into a project, the sheet saved holding both; a copy of the WiFi board given a
rounded corner in mils (clockwise) and a 50 mm round shape, read back equal, through
`get_board_summary`, `PointInPolygon` (the corner outside, the arc's inside in) and the
saved file's Board6 record; refused outlines leaving the board unchanged and unmodified; a
new board's rounded rectangle drawn on Mechanical 1 out of order, with a hole's circle
inside and a stray line, made its shape (8 vertices, the other two listed), and with one
track missing refused, its open ends given. Before the tools all 9 errored:
"AttributeError: module 'main' has no attribute 'create_project'" (`set_board_shape` for
the board tests). After: 9/9 pass in AD25; `test_live_layout` and `test_live_pcb_rules`
(3, `pcb_layout.pas` and the focus list) pass. Offline: 28 new in
`tests/test_project_setup.py`; 323 tests pass in the offline list of
`.github/workflows/tests.yml`.
Decided 2026-11-14 by the run, not the owner: `build_schematic` takes `sheet_path` only with
`project_path`, because the item is the sheet in a project, and without both the sheet stays
the unsaved free document it was.
Decided 2026-11-14 by the run, not the owner: the project file is saved after every add,
because an add held only in memory is lost when the project is closed unsaved, and the
result is read back from the saved file.
Decided 2026-11-14 by the run, not the owner: a new document another project took is taken
out of it again and that project's file flag put back when it had no unsaved change,
because a call must not change a project it was not given (`build_schematic` already
detached its sheet so).
Decided 2026-11-14 by the run, not the owner: the shape is taken from Mechanical 1 to 16
only, and Mechanical 16 refused on a board that uses a mechanical layer above it, because
a primitive on a layer above 16 reads as Mechanical 16 and no script call gave its own
layer, so another layer's pieces could be taken into the shape.
Decided 2026-11-14 by the run, not the owner: of several closed shapes on the layer the
largest is used when it holds every other (listed, not made into cutouts), else the call is
refused, because a cutout or hole drawn on the outline's layer is common, and a guess
between shapes side by side would give a wrong board.
Decided 2026-11-14 by the run, not the owner: `set_board_shape` changes the board without
saving it, as the other PCB edit tools do; the result's `board_modified` says so.
Fixed in `97299f4`. Local: on `ad25`, released in `build-20261114-210622`. Upstream: not
yet decided.
Closed: the scenario test of that build held for what A10 asked (2026-11-14, fifth entry, 1):
`create_project`, `add_project_document` (new sheet and board, a library from another
folder saved relative, a repeat add, refused adds, a focused project given back its
sheet and left unmodified) and `set_board_shape` (an outline in mm with an arc, four
refused outlines, a shape from Mechanical 1 with a stray line listed and a gap refused),
read back right through Altium on a reopened board. Two faults it found in these tools
are items of their own: A25 (the shape's region wrong on a board just made, until it is
reopened) and A26 (`build_schematic` with `project_path` leaves the focused project
modified).
Decided 2026-11-14 by the run, not the owner: A10 is closed and its two faults go to A25
and A26, because what A10 asked for exists and held, and each fault needs its own test
and fix that the next run can take apart.

### A16 - A library symbol cannot be given its footprint - CLOSED 2026-11-14

`create_schematic_symbol` and
`create_symbols_batch` (`SYMBOL`, `EDITSYMBOL`) have no record for a footprint model; a
footprint is set only on a part `build_schematic` places (`footprint`). A symbol made from
a datasheet leaves its library without the link, and each placement must give it again.
Local: a `FOOTPRINT` record (model name, library, current or not) in the symbol batch, and
the same in `create_schematic_symbol`.
Found 2026-11-14 by the run's probes in AD25: a symbol's footprint is an `ISch_Implementation`
of type `PCBLIB` (`Comp.AddSchImplementation`, `ModelName`, `ModelType := 'PCBLIB'`,
`IsCurrent`) and its library a datafile link (`AddDataFileLink(<entity>, <path>, 'PCBLib')`,
`ClearAllDatafileLinks`; `DatafileCount` and the link's getters are not in the script API).
`Impl.ExportToParameters` gives the stored record: `MODELDATAFILE0=<library>`,
`MODELDATAFILEENTITY0`, `MODELDATAFILEKIND0=PCBLib`, `ISCURRENT=T` (absent on a model that is
not current). A link with no location stores the entity and kind only, which is what a model
linked "by name" holds; `UseComponentLibrary` gives another record (`USECOMPONENTLIBRARY=T`)
that belongs to integrated libraries. A symbol also carries 3D (`PCB3DLIB`) and simulation
(`SI`) models in the same list, each type with a current of its own; `Comp.Replicate`, which
`build_schematic` places parts with, copies all of them.
Fix: `FOOTPRINT|<model>[|<library>[|<current 1/0>]]` after `SYMBOL` or `EDITSYMBOL` in the
batch spec, and `footprints` (entries `model[|library[|current]]`) in `create_schematic_symbol`.
A symbol can carry several; a record for a name the symbol already has changes that footprint
(library, current) instead of adding one, and nothing else of the symbol's models is touched
(`ApplyFootprint` in `schematic_utils.pas`, applied in `ApplySymbolEdits`' one undo step).
`server/symbol_footprint.py` checks the records before Altium is called: a library must be a
full path to an existing `.PcbLib` (long path form), `current` 1 or 0 or empty, no name twice
for a symbol, at most one asking for `1`; a bad spec is refused whole (`nothing was made`),
and a batch's records are rewritten in full for the script. The results are read back from
the symbol in the library: the batch result gets `footprints` (per symbol with such records:
`symbol` and `models` with `model`, `library`, `current`; the key is absent when no record was
given), `create_schematic_symbol`'s a `footprints` list and `problems`; what a record stored
(current mark, library) is checked after and a difference is a `problems` entry.
Live test `tests/test_live_symbol_footprint.py` (`ALTIUM_LIVE=1`, a temporary folder, closed
unsaved; copies of a library and a footprint library of the SpiritLevel-SL1 example): a batch
symbol with two footprints (one `1`) read back in the result, in the open library and, after
the library is saved, closed and opened anew, from the saved file; first footprint current when
none says so; a footprint with no library (link by name); `EDITSYMBOL` of an example symbol that
has a footprint, a 3D and a simulation model: an added footprint not current, the same name
again with `1` taking the mark, the 3D and simulation models unchanged; refused records
(two `1`, a missing library, a `.SchLib` as library) leaving the library without the symbol;
`create_schematic_symbol` with footprints and without; a batch with `SYMPARAM`, `DESCRIPTION`
around a `FOOTPRINT` and a symbol with none (no `footprints` in its result); a part placed by
`build_schematic` with no `footprint` from such a symbol, its footprint model current on the
placed part. Before the code 7 of the 8 tests then written failed (`KeyError: 'footprints'` in
the batch results, `TypeError: create_schematic_symbol() got an unexpected keyword argument
'footprints'`, and `AssertionError: {} != {'HDR1X2': True}` : "the placed part did not take
the library's footprint"); the 8th, a symbol made without footprints, passed and is kept as a
guard. After: 9/9 pass in AD25 (the ninth, the batch with the other records, added after);
`test_live_project_setup`'s `build_schematic` test (the file the code shares) passes. Offline:
18 new in `tests/test_symbol_footprint.py`; 341 tests pass in the offline list of
`.github/workflows/tests.yml`.
Decided 2026-11-14 by the run, not the owner: the result is read from the symbol in the
library as it is in Altium, not from a saved file, because neither tool saves the library (the
user does); the live test saves, closes and reopens it and reads the file's models through
Altium as well.
Decided 2026-11-14 by the run, not the owner: `current` left out gives a new footprint the
mark only when no other footprint of the symbol has it, and an existing one keeps its own,
because adding a footprint to a symbol must not change the one a design already uses; only a
record saying `1` moves the mark.
Decided 2026-11-14 by the run, not the owner: a record for a name the symbol already has
replaces that footprint's library and mark instead of adding a second model of the same name,
because two models of one name in one symbol cannot both be placed and a repeated batch
should leave the same library.
Decided 2026-11-14 by the run, not the owner: a library is a full path to an existing
`.PcbLib` file, and a record without one links the model by name only (the stored form of
"Any"), because a path that is not a file is a broken link and a relative name resolves
against whatever Altium has open; whether the footprint name is in the library is not
checked, as nothing reads a `.PcbLib`'s footprint names without Altium here and Altium does
not check it when the link is made.
Decided 2026-11-14 by the run, not the owner: a bad `FOOTPRINT` record refuses the whole batch
spec before the first symbol is made, because the symbols made before a bad record would stay
in the library of a call that reports failure.
Fixed in `b4da4cc`. Local: on `ad25`, released in `build-20261114-210622`. Upstream: not
yet decided.
Closed: the scenario test of that build held (2026-11-14, fifth entry, 4): `FOOTPRINT`
records in the batch, `EDITSYMBOL` moving the current mark, three refused specs ("nothing
was made") and `create_schematic_symbol`, each equal to the saved library read apart from
the server; a part placed by `build_schematic` without `footprint` carried the library's
models and marks. The interplay it found with a part placed with `footprint` is A27.

### A22 - A call takes the keyboard and the front of the screen for Altium - CLOSED 2026-11-14

While the server
runs, Altium's window comes to the front at every call, over a full-screen video too, and
the keys typed in another program go to Altium, read as its commands (the owner,
2026-11-14). A stray key there can change the open board under a call, so a result, a
live test or a scenario test can be wrong without anyone seeing it; the window on top is a
nuisance only. Likely cause, unchecked: every call starts `X2.EXE -RScriptingSystem:…`,
which the running Altium takes as a new command line and answers by activating its main
window; only the screenshot tool gives the foreground back after (`_bring_to_front`, then
the previous window). Local, to reproduce first: a live test that notes the foreground
window, makes one read, and fails when Altium kept the foreground. Then either give the
foreground back to the window that had it once the response is in, as the screenshot tool
does, or reach the running Altium without activating it (another way to start the script,
or the window shown without activation), whichever holds. Usage until then: nothing is
typed on the machine while a test or a scenario test runs. Not in the run of 2026-11-14's
groups (the owner: "catat dulu aja"): for the next run.
Cause, found 2026-11-14: Altium activates itself whenever it takes a script command line
(`RunScriptFile`, even of a script that does nothing); `X2.EXE` launched with no argument
does not. Launching shown without activation (`SW_SHOWNOACTIVATE`, `SW_SHOWMINNOACTIVE`) and
`LockSetForegroundWindow` from the server (refused: not the foreground process) changed
nothing, so no way was found to reach Altium without the activation. Fix: `foreground.py`'s
`ForegroundGuard`, around every bridge command and `run_altium_script`, listens for
foreground changes (a WinEvent hook) and gives the foreground back to the window that had
it the moment an Altium window takes it; it does nothing when Altium was in front at the
start, and follows the user to another program. Altium now holds the foreground 1 to 7 ms
per call instead of the whole call and after; a key typed in those milliseconds still goes
to Altium. Decided 2026-11-14 by the session, not the owner: the give-back, as the way that
holds, because the activation could not be prevented. Live test
`tests/test_live_windows.py` (`ForegroundTest`, a window of another process in front, the
time Altium is in front measured from the events): before, "Altium had the foreground for
760 ms during the call" (a read) and 240 ms (`run_altium_script`), 2/2 fail; after, 2/2
pass. Offline tests in `test_foreground.py` (11). Offline 352 OK; the live set 43 tests, 42
pass: `test_add_documents` was refused once by the "Altium is not responding" check before
its call was launched (Altium busy just after a 7 s `add_project_document`), and its module
passed 9/9 twice alone after. Fixed in `842e6f8`. Local: on `ad25`, released in
`build-20261114-225815`. Upstream: not yet decided.
Closed: the scenario test of that build held for ordinary calls (2026-11-14, sixth
entry, 1): reads, `run_drc` with its dialog, `get_layout`, `check_silkscreen` and a
`run_altium_script` opening a project left Altium in front 5 to 31 ms per call, the
foreground back on the other window after each. Two gaps it found are A31: the guard is
off for a call that starts with no window in front (Altium kept the foreground 4
minutes), and a script that closes one project and opens another kept Altium in front
about 3.4 s with no foreground event to act on.

### A24 - A modal message no driver knows blocks the call until the bridge's limit - CLOSED 2026-11-14

When
Altium puts up a message the server does not expect, the script that raised it waits on it,
the bridge keeps waiting (up to its 30 minute limit, as A21's did), and every later call
waits behind it; nothing says a message is up, and the result, when it comes, does not name
it. Each one met so far was fixed for its own tool only: A21's repour message in `run_drc`.
Met again in the run of 2026-11-14: an "Information" message, "File Not Open", one OK
button, while A11's probe drove the ECO dialog and exported its report; and a
`TShowException` "COM object that has been separated from its underlying RCW cannot be
used" that came back after each close (A11). The owner, 2026-11-14: it has happened before
with other messages. Local, to reproduce first: a live test that has a script put up a
message Altium's way (e.g. `ShowMessage` from `run_altium_script`) and fails when the call
does not return within a short limit naming the message. Then a watch in the bridge, for
every command: while it waits, a top-level modal window of X2.EXE that the tool's own
driver does not handle (`TMessageForm`, `#32770`, `TShowException`) ends the call as a
failure that gives its title, text and buttons; which messages it may then close, and
with which button, to be decided with the test (an OK-only message is safe to close, one
with choices may not be). Usage until then: a call that does not return in a minute or two
is looked at on Altium's screen. Not in the run of 2026-11-14's groups: for the next run,
with A22 (both are how a call meets Altium's windows).
Reproduced 2026-11-14: a script launched through the bridge itself (the live test swaps
the bundle for a small `.pas` that takes the request and calls `MessageDlg`) put up its
message and the call waited out its whole limit, then blamed "a runtime error" in the
debugger; the next call waited 44 s and reported "Altium did not start the command". A
script's `MessageDlg` is a task dialog (`#32770`) whose buttons are child windows (`OK`,
`&Yes`, `&No`) and whose text, in a `DirectUIHWND`, cannot be read from outside; Altium's
`TMessageForm` text cannot be read either; so each message is kept as a picture
(`dialogs\` beside the exchange files) and the result points to it. Fix:
`altium_messages.py` and the bridge's wait loop. Every 0.25 s the bridge reads X2.EXE's
top-level `TMessageForm`, `#32770` and `TShowException` windows; one up for 1 s that the
tool does not answer itself (`execute_command(handled=…)`: `run_drc` names its repour
message) is acted on: a single OK or Close button is pressed (a posted click), the command
goes on, and the call fails naming the message, with the command's own answer after it in
`reply_after_message` and, for a command that changes the design, a word to check it; one
with choices (or another single button, `TShowException`'s "Send and Close") is left open
and the call fails at once naming it, as no answer is safe to give for it; a message that
comes back after 3 presses is left open the same way (the RCW loop, A11). A call made while
a message with choices is open is not run, and says so at once. Decided 2026-11-14 by the
session, not the owner: these answers (press only a lone OK or Close; leave choices to the
user; fail the call in both cases even when the command then succeeded), because a result
met by an unexpected message may be wrong and the caller must know; the 1 s grace, for a
tool's own driver to answer first. Not changed: the "busy" box a refused launch raises is a
`#32770` "Information" on AD25, which the not-started path (`_dismiss_altium_dialogs`,
`TMessageForm` only) leaves open. Live test `tests/test_live_windows.py` (`MessageTest`):
before, 3/3 fail ("the call waited 42 s", twice; "the next call waited 44 s"); after, 3/3
pass, the five tests of the file in 25 s. Offline tests in `test_altium_messages.py` (16).
Offline 368 OK; the live set 46/46 pass (Altium not restarted before it).
Fixed in `83623df`. Local: on `ad25`, released in `build-20261114-225815`. Upstream: not
yet decided.
Closed: the scenario test of that build held for what A24 asked of the bridge
(2026-11-14, sixth entry, 4): with a Yes/No message open, `get_board_summary` and
`run_drc` were refused within a second, the message, its buttons and its picture named.
Gaps it found are items of their own: A32 (`run_altium_script` answers a message with
choices itself, closing it as Cancel, and is launched while one is open; its diagnosis
of a script waiting on a message is wrong) and A33 (an OK-only message open before a
bridge call is neither pressed nor named). Its small point on the refusal (a new picture
per refusal, the `altium_messages` list not in the tool's reply) went into A29.

### A29 - A message with choices blocks Altium until someone answers it - CLOSED 2026-11-15

Since A24 a
message Altium puts up during a call that has choices (Yes/No, OK/Cancel) or another single
button ends the call at once, named, with a picture of it, and is left open; every later
call is refused while it is up. So the call no longer waits, but Altium does: nothing the
server has can answer it, and only the owner, at Altium's screen, can (the owner,
2026-11-14: "bikin agent nunggu gw dong"). The server should not choose an answer itself:
"No" to a save question throws work away, and "Cancel" in the middle of a command can leave
the design half changed. Local: a tool that answers an open Altium message with one of its
buttons by caption (`answer_altium_message`, e.g. `button="Cancel"`), its list of open
messages with title, buttons and picture when called with none, and the answer read back
(the window gone, what the waiting command then answered); the A24 failure and refusal
naming the tool. The agent, which sees the picture and knows what it was doing, answers,
and asks the owner only when unsure. A live test: a script's `MessageDlg` with Yes/No
(`tests/test_live_windows.py`'s `MessageTest` puts one up), answered "No" by the tool, the
script's reply read back. (The owner, 2026-11-14, after A24's commit.)
Also, from the scenario test of `build-20261114-225815` (2026-11-14, sixth entry, 4):
each refusal writes a new picture of the same window, and the `altium_messages` list
reaches the tool's reply only as the error text: one picture per window, and the list
in the reply, with the tool.
Cause: nothing in the server pressed a button other than a lone OK or Close, and nothing
kept the command left waiting, so its late reply was dropped by the next call (which
deletes any leftover reply); the refusal took a new picture of the same window at each
call. Fix: `answer_altium_message` (`main.py`, `altium_messages.py`). With no `button` it
lists Altium's open message windows (title, class, buttons, picture, and
`command_waiting` on the one a call of this server left its command waiting on),
changing nothing, and gives that command's reply once it is in. With a `button` it picks
the only open message or the one with that `title` (any case), presses the button by
caption (`button_key`: no `&`, any case), and, when it is the message the left command
waits on (or that one is gone and this may be its next), waits for that command's reply,
told apart by its `request_id`: `outcome` "replied" with `reply`, "another_message" (the
command met a further message, named with its picture, left open), "no_reply_yet" after
`wait_seconds` (60) without progress, said so, or "no_command_waiting". A caption the
message does not have, no message, several and no title, or two with the same title:
fails, naming them, nothing pressed. A24's failure ("left open") and refusal ("Not run")
now say "answer it with answer_altium_message (…) or in Altium". One picture per window:
`altium_messages.Pictures`, kept by handle, class, title and buttons, dropped once the
window is gone.
Decided 2026-11-14 by the run, not the owner: listing takes no lock; pressing takes this
server's command lock and then the exchange lock, each with a bounded 10 s wait
(`ANSWER_LOCK_WAIT`), and presses nothing when one stays held, because the script waiting
on the message holds neither lock (the call that launched it ended and let both go), so
no wait here can deadlock with it, and holding both until the reply is read keeps a new
request from deleting that reply; an exchange lock held by another session means the
message may be that session's, which is not this caller's to answer.
Decided 2026-11-14 by the run, not the owner: a button named by the caller is pressed by
a posted click, then `BM_CLICK`, never by closing the window, because a close gives the
script another answer than the one asked for (A32 (a): Cancel, 2); a further message met
while waiting for the reply is named and left, even an OK-only one, because the tool
answers only what the caller asked.
Decided 2026-11-14 by the run, not the owner: the reply is taken only with the waiting
command's `request_id` (one without it is not), because a reply of another request would
be a wrong result.
Decided 2026-11-14 by the run, not the owner: the `altium_messages` list is not added to
the reply of every tool (they pass on only the error text, which names each message's
title, buttons and picture); the list, with the pictures, is `answer_altium_message`'s
reply with no button, because that is the smaller change and the error already names the
tool.
Live test `tests/test_live_windows.py` (`AnswerTest`, the script's `MessageDlg` with Yes
and No; `MESSAGE_SCRIPT` now echoes the request's `request_id`, as the bridge does):
before, 4/4 fail: "module 'main' has no attribute 'answer_altium_message'" (3) and "a new
picture per refusal" (three files of one window); after, 4/4 pass ("No" pressed, the window
gone, the reply "answered 7" read back, the next call run; the listing with the picture,
the window still open; "Cancel" failing with "its buttons are Yes, No"; one picture), the
file 9/9 in 56 s. Offline tests in `test_altium_messages.py` (40, 24 new); offline 392 OK.
Fixed in `c348b6d`. Local: on `ad25`, released in `build-20261115-114630`. Upstream: not yet
decided.
Closed: the scenario test of that build held (2026-11-15, first entry, 5):
`answer_altium_message()` listed the open Yes/No message with its title, buttons and
picture; with it open `get_board_summary` was refused in 0.3 s naming it and the tool,
with the listing's picture (one picture per window); `button="Cancel"` failed naming Yes
and No, nothing pressed; `button="No"` closed it, and the next call ran. Its small points
went into A34 (c) (the picture cuts the buttons) and A32 (d) (the note on a message a
`run_altium_script` of this server left open).

### A30 - A script launch per call is what brings Altium to the front - CLOSED 2026-11-15

A22's guard gives
the foreground back within 1 to 7 ms, but every call still starts
`X2.EXE -RScriptingSystem:RunScriptFile(…)`, and Altium activates itself on each such
command line (a bare `X2.EXE` does not): a key typed in those milliseconds still goes to
Altium (about 2 to 3 % of calls while the owner types without pause), the window may flash
for a frame, and each launch costs about 2 s of the call (from "Running command" to
"Bridge script started" in the server log). Cleaner: a bridge that stays in Altium,
started once, reading `request.json` by itself (a script form kept open with a timer, or
another way into the running Altium), so no command line per call. Unknown, to probe
first: whether a script form shown non-modal survives the end of the script that showed
it in AD25, whether its timer fires while a script of the user's own runs or sits in the
debugger, how it is started again after Altium restarts, and the script engine's memory
per call (it leaks on every launch now). Also worth a look: whether the running Altium
takes commands another way (COM, DDE) without activating. Found: a decision with the owner
before the build, as it changes the bridge upstream's tools all rest on; A22's guard stays
either way. (The owner, 2026-11-14, after A22's commit.)

Probed 2026-11-14 (live, AD25, the server not running; the scripts are in `dev/a30_probe/`).
(1) Yes, from a script *project* only. A form shown with `Show` by
`ScriptingSystem:RunScript(ProjectName=…)` outlives the script that showed it, and its
`TTimer` (100 ms) kept firing: over 240 s with a call every 10 s, 24/24 served, no stall seen
at a 0.2 s sampling. `RunScriptFile` cannot do it: it loads no `.dfm` ("Undeclared
identifier: TProbeForm"), and DelphiScript takes no script routine as an event handler
(`OnTimer := Proc`: "Invalid procedure usage"; `@Proc`: "Expression expected"). The form
must stay visible: never shown, or shown and hidden in the same run, the script ends and
the form is freed; shown borderless at -32000,-32000 it works. With the bridge's own units
and a form unit in one project, its timer calling the bridge's `Run` whenever
`request.json` is there: 30 calls, the reply after median 110 ms (max 153 ms), against
median 1.90 s (max 2.02 s) for the same request through a launch of the bundle, 1.86 s of
it before the script takes the request.
(2) The timer fires while Altium shows a modal message (`ShowMessage`), while another
script's runtime-error dialog is up, and while that script sits stopped after it: 5/5 calls
served in each, about 110 ms. A request is then served inside a modal loop, so A24's rule
(no call while a message is open) has to be checked by the server before it writes the
request. While another script runs it fires only if that script pumps messages
(`Application.ProcessMessages`: a request is served in the middle of that script); one that
does not holds it off for its whole run (a 5.05 s gap for a 5 s loop). Scripts launched
beside it run (30 bundle launches, 34 trivial ones); `-REditScript:Stop` with nothing
stopped leaves it alive. It does not block Altium's UI: a window-message round trip median
0.99 ms, p99 2.86 ms with it, 0.98 and 2.65 ms without; Altium's CPU 11.15 % against
10.94 % of one core, idle. A runtime error inside its own handler (a command's) ends it:
Altium shows a plain "Error" box (OK only) and opens the unit's source in its editor, the
timer stops for good (a `try`/`finally` around the call did not keep it), and the next
`-REditScript:Stop` frees the form. An exception from its own file write did the same once
("Cannot create file … being used by another process": the probe was reading the heartbeat
file at that moment), so the server must read such a file by its time only, never opening
it. Once, not reproduced in three tries, a form stopped after a launch was refused behind
another script stopped in the debugger.
(3) It dies with Altium; it is started by one `RunScript` of its project, 2.3 s (Altium
takes the front once, as at every launch now, which A22's guard handles). Not tried across
a real restart: the process ends, so the form does, and the server starts it again at the
first call that finds no window of it. A second launch of the same project while it lives
is refused ("Another script executing now", an Error box, and the launch after it "There is
another instance of running, but it is busy", an Information box), so the server checks it
is alive before starting it: its window (by its caption, of X2.EXE, not hung) and a
heartbeat file's time. A command it serves holds the heartbeat still, so a still heartbeat
while a request is in flight is not a death. Each `RunScript` of a project adds that
project to Altium's Projects panel; closing it there (`Client.CloseDocument`) left the form
running.
(4) Memory: 30 launches of the bundle, +3.9 MB private bytes (0.13 MB per call), GDI and
USER objects unchanged; 30 launches of a trivial script file, +0.0 MB; 30 calls served by
the resident, +0.0 MB and handles unchanged; the resident's own start, +1.4 to 4.5 MB and
+13 GDI, +26 USER objects, once.
(5) No other way in found. The Running Object Table holds nothing of Altium;
`GetActiveObject` on `Altium.Application`, `AltiumDesigner.Application`, `DXP.Application`,
`X2.Application`, `DXP.Client` and `Altium.Client`: "Invalid class string"; the 104 HKCR keys
naming Altium are file types, the Mechatronic `SolidSDK` classes ("Operation unavailable")
and the URL protocols `DXP:` and `DXPProcess:`, whose open command is `X2.exe "%1"`, the
same command line. No DDE server answered (services DXP, Altium, X2, AltiumDesigner,
Client, ADVPCB, PROTEL; topics System, Client and the service's name). Not tried: the
message a second X2.EXE hands its command line to the first with; the activation is in the
first's handling of it.
(6) 10 calls served by the resident with a window of another process in front: Altium in
front 0 ms, 0 times, the window kept the foreground; 3 unguarded launches of a script file:
Altium in front 3 times. Two traps met on the way: a script file with LF line ends does not
compile ("Error in declaration block at Line:3, Char:53"), and a `FileName` holding a space,
unquoted, starts a second X2.EXE instead of reaching the running one (the server's exchange
folder has none).
Recommended by the run, for the owner's decision: build it, as the first path, with the
launch per call kept as its fallback. A form unit (about 80 lines) in the bridge's project,
started by one guarded `RunScript` at a call that finds no window of it; the server checks
it alive and that no Altium message is open, writes `request.json` as now and, when it is
not taken within about 1 s, falls back to the launch it does now (which also covers a
resident ended by a runtime error: `-REditScript:Stop` as now, and the resident started
again at the next call). Its heartbeat carries the bundle's hash, and a resident of another
build is told to close (a stop file) and started again, so a new release never serves with
old code. Gains: about 1.8 s and 0.13 MB per call, and no activation at all for a served
call (A22's 1 to 7 ms window and A31's gaps go away for those). Costs and risks: re-entrancy
(a request served inside a modal loop or inside a user's script that pumps messages; the
server's check before writing covers the first, nothing covers the second), one script
project in the Projects panel and an off-screen form of Altium's for the session, a
runtime error still opening the bridge's source in Altium's editor, and a second path to
test (live tests: it serves, lasts minutes, takes no foreground, falls back once it is
gone, comes back after a runtime error). A22's guard stays for the launches.
Decided 2026-11-15 by the owner: build it, as the run recommended (the launch kept as
the fallback).
Fix: `server/resident.py` and `server/AltiumScript/Resident/MCPResident.pas` (`.dfm`), and
`main.py`'s `_hand_over`. The resident project, under `C:\Users\Public\altium_mcp\resident\<tag>\`,
holds the bridge as script_bundle's one unit (`MCPBridge.pas`) and the form unit, filled
with its tag and folder; the tag is a hash of their text. Each call writes `request.json`,
then a `take` file the form deletes (its claim) before it runs the bridge's `Run`; a `take`
the server can still delete after 1.5 s is a request not claimed, and the call goes by the
launch as before. The heartbeat is the form's caption, `altium-mcp resident <tag>
<yyyymmddhhnnss>`, read with `GetWindowText` (no message sent, no file opened); a `stop`
file closes the form. A call goes by the launch when Altium is not running, an Altium
message is open or the form is disabled (a modal loop: VCL disables the other forms of the
thread), this build's form is there with a caption older than 5 s, or two starts failed;
none of this build alive, it is started (`RunScript` of its project, guarded by A22), the
residents of other builds told to stop first. `"resident_bridge": false` in `config.json`
turns it off. `get_server_status` gives `resident_bridge` (tag, the forms, how the last
call went). The response is looked for every 20 ms for the first 2 s (was 250 ms).
Found on the way (2026-11-15): (a) Altium gives a script form `WS_EX_APPWINDOW`, so the form
had a taskbar button of its own; hidden by the form after its script ended, it was still
freed (every call then started it again), so the server changes its styles (off
`WS_EX_APPWINDOW`, on `WS_EX_TOOLWINDOW`) and removes its button (`ITaskbarList::DeleteTab`).
(b) With the bridge's own units in the project, `create_symbols_batch` and
`create_schematic_symbol` failed: "Undeclared identifier: SchLibIsFocused" (an Error box,
the form's timer stopped for good, freed by the timeout's `-REditScript:Stop`): a script
project compiles each unit in order, and `schematic_utils.pas` calls `SchLibIsFocused`
above its definition. The bundle orders routines, so the resident runs the bundle. The
launch's own fallback (the project, when bundling fails) has the same fault; not changed.
(c) While Altium's UI thread is busy (opening the 16-layer example board, 18 s) the
caption goes stale and one call went by the launch, the next by the resident again. (d)
`-REditScript:Stop` with nothing stopped (the sandbox's recovery) left the form alive.
Live test `tests/test_live_resident.py` (5): calls after the first served with no launch,
under 0.6 s; the form off the taskbar and Alt+Tab; a request not claimed goes by the launch
and the resident stays; a resident of another build replaced; five served calls with
Altium never in front (`_Watch`: 0 times). With `resident_bridge` off, 2 of them fail
("'launch' != 'start'", "'launch' != 'resident'"). Measured: start 2.0 to 2.5 s, then
median 0.11 s per call (was about 2.0 s). `test_live_windows`'s A24 tests run their own
script by a launch (resident off in the test). All live modules, 55 tests, through the
resident (114 calls taken by it, the A24 tests' 7 by launch): 54 passed, the one failure
the replacement test's own (a blank line did not change the bundle; it now adds a
routine), then 5/5. Offline: `tests/test_resident.py` (23); 415 OK.
Found after the release (2026-11-15): the tag hashes the files' bytes before the line ends
are made CRLF, so the release copy (`git archive`) and this checkout, at the same commit,
give two tags (`0fd9980a5570`, `a4ea8490f7f3`): a live test from the checkout and a session
on the release, on one Altium, close each other's resident and start their own (2 s and one
launch each time). Hash the text after the CRLF step. Not changed yet.
Fixed in `f1b1559`. Local: on `ad25`, released in `build-20261115-114630`. Upstream: not yet
decided.
Closed: the scenario test of that build held (2026-11-15, first entry, 1): the first
call started the resident (2.92 s), and the 26 bridge requests after it were taken by it
in 0.015 to 0.14 s with no launch, the results the same as before on every tool used
(reads, `run_drc`, the edit and silkscreen scenarios on a copy); the form stayed off the
taskbar, outlived a `run_altium_script` recovery and a message answered by hand, and the
tools reported the design project, not the resident's. What is left: A34 (a), (b) and
(d) (the tag hashed before the CRLF step; Altium briefly in front at the first board
call and after a pressed button; `run_altium_script` still a launch) and A31 (the
resident's start and that launch kept Altium in front 1.5 to 2.9 s with no foreground
event).

### A35 - A34 (a), the resident's tag differed between a release copy and a checkout - CLOSED 2026-11-15

The tag
(`Resident.prepare`) hashed the form's `.pas` and `.dfm` as read from disk, and made the
line ends CRLF only afterwards, when writing them. A release copy (`git archive`: LF) and a
checkout (`core.autocrlf`: CRLF) at one commit therefore gave two tags (`0fd9980a5570` and
`a4ea8490f7f3`), and on one Altium each closed the other's resident and started its own
(2 s and one launch each time). The bundle (`script_bundle.bundle_text`) already splits
and joins its units' lines and writes CRLF, and `project_units` reads the project file by
regex, so neither differs by line ends: only the two templates did. (Found after A30's
release, 2026-11-15.) Local.
Fix: `server/resident.py`, `prepare`: every file's text (the bundle and the two templates)
is made CRLF, as it is written, before the hash; the `%TAG%`/`%DIR%` fill comes after the
tag is known, as before.
Test before: `test_resident.PrepareTest.test_tag_is_the_same_for_lf_and_crlf_copies`
(the form's templates and the bridge's units and project file, once with LF and once with
CRLF line ends) failed on the old code: `AssertionError: 'ee2c90ff7ed6' != 'd19c84dbe662'`
("LF and CRLF copies of one commit gave two tags"). After: it passes; offline 416 OK (was
415). Live, `ALTIUM_LIVE=1` from this checkout in AD25: `test_live_resident` 5/5, and the
other live modules (`windows`, `drc`, `layer_stackup`, `layout`, `pcb_rules`,
`project_setup`, `symbol_footprint`, `unrouted`) 50/50, so 55 of 55 passed; the checkout's
resident now has the release copy's tag, `0fd9980a5570`.
Decided 2026-11-15 by the run, not the owner: this entry carries the code A35 and names
A34 (a) in its title, because a code can head one item only (`board.py --check` rejects a
second `A34` heading) and A34 stays Open for (b), (c), (d).
Decided 2026-11-15 by the run, not the owner: the test builds its LF and CRLF trees from
the shipped form templates in temporary folders, with `TEMPLATE_DIR` patched, because the
real files' line ends depend on the clone's `core.autocrlf` and the test must not.
Fixed in `a1d9606`. Local: on `ad25`, released in `build-20261115-143551`. Upstream: not yet
decided.
Closed: the scenario test of that build held (2026-11-15, second entry, 1): the
release's `get_server_status` gave the tag of the resident the checkout's live tests had
left, `this_build` true, and its first call was taken by it with no start and no launch;
`Resident.prepare` on the checkout, the release copy and an LF copy of it gave one tag. A
resident project of an earlier build still listed in Altium's Projects panel went to A34
(e).

### A13 - The layer stack can only be read - CLOSED 2026-11-15

`get_pcb_layer_stackup` reads it; nothing adds
or removes layers or sets copper weight, dielectric thickness, material or constant. Local:
a tool that sets the stack from a list top to bottom, as the read gives it, with presets
for common fabrication stacks (2-layer 1.6 mm; 4-layer 1.6 mm with 7628 prepreg).
Found 2026-11-15 by the run's probes in AD25 (`Board.LayerStack_V7`, method names read from
Altium's SDK interface assembly): `FirstAvailableSignalLayer` / `FirstAvailableInternalPlane`
give a free layer and `InsertInStackAbove(<copper layer>, <it>)` puts it in the stack directly
above that layer, with a new dielectric between them (`InsertLayer` wants the old integer
layer id and puts the layer above Bottom Layer); `RemoveFromStack(<layer>)` takes a copper
layer out with the dielectric below it. A new dielectric may come with no material and a
constant of 1e12 until set. `Name`, `CopperThickness`, `DielectricType` (0 none, 1 core,
2 prepreg, 3 surface material), `DielectricMaterial`, `DielectricHeight` and
`DielectricConstant` are set directly and are in the saved file. A layer removed while it
holds a track leaves the track on a layer that is no longer in the stack. Altium does not
mark the board modified for any of these. `UsedByPrims` stays True after a layer's last
object is deleted. `Board.MasterLayerStack` (`SubstackCount`) tells a rigid-flex board.
Fix: `set_pcb_layer_stackup(layers | preset, dry_run, board_path)`. `layers` is the stack
top to bottom in the read's form (its `layers`, passed back as they are or edited): copper
entries (`layer_name`, `layer_id`, `copper_type` Signal or Plane, `copper_thickness_mils`)
and dielectric entries (`layer_name`, `dielectric_type`, `dielectric_material`,
`dielectric_height_mils`, `dielectric_constant`); the read's `_um` keys taken when the mils
are not given, and refused when both disagree; a key left out is left as the board has it;
`layer_order` ignored; an unknown key, a value outside sane limits (a unit mistake) or a `|`
or `;` in a name refused before Altium. The shape: the surface dielectrics, copper and one
dielectric in turn, the surface dielectrics below. Top and bottom copper are Altium's Top and
Bottom Layer; an inner entry keeps the board layer its `layer_id` names, or, without one, the
board's next inner layer of its kind in order; the rest are new signal layers (planes where
`copper_type` or an `Internal Plane` id says so); the board's inner layers no entry keeps are
removed. The result: `requested`, `added` and `removed` copper layers, `changed` (values
written), `board_modified`, `stack` (the read again) and `differences` from what was asked
(`success` false when any); `dry_run` gives `would_add`, `would_remove`, `would_change` and
runs Altium's check of the layers to remove. Presets (`server/layer_stack.py`, `PRESETS`;
generic builds, approximate, not a fabricator's figures, as no fabricator's page was read):
`2_layer_1.6mm`, 1 oz (35 um, 1.378 mil) copper on a 1.53 mm (60.2362 mil) FR-4 core, Dk
4.6; `4_layer_1.6mm_7628`, 1 oz outer and 0.5 oz (17.5 um, 0.689 mil) inner signal layers,
one 7628 ply of 0.2 mm (7.874 mil, Dk 4.4) under each outer layer and a 1.095 mm (43.1102 mil)
FR-4 core (Dk 4.6), the common build of a 7628 4-layer board that fabricators such as JLCPCB
offer something close to; both 1.6 mm of copper and dielectric, plus Altium's 0.4 mil solder
masks (Solder Resist, Dk 3.5); no layer names set. Python side in `server/layer_stack.py`
(checks, presets, the plan, the bridge records, the comparison), the tool in `main.py`; bridge
command `set_layer_stack` (`SetLayerStack` in `pcb_utils.pas`): records `R|`, `A|`, then one
`C|`/`D|` per layer of the stack after them, lengths in internal units, the constant x10000
(no float text, as Altium's `FloatToStr` writes a decimal comma here). The read
(`get_pcb_layer_stackup`) gives each copper entry a `copper_type` as well.
Test before: `tests/test_live_set_layer_stackup.py` (`ALTIUM_LIVE=1`, copies of the 2-layer
SpiritLevel-SL1 board and of the 4-layer WiFi board of the Mini PC example, closed unsaved):
the 4-layer preset on the 2-layer board read back equal, after a save and reopen too, the new
inner layers routable (a track lands on one) and Altium counting 4 signal layers; the 2-layer
preset then refused while one inner layer holds that track (`layers_in_use`, 1 object, stack
and flag unchanged) and, the track deleted, both inner layers removed and the 2-layer stack
read back equal after a reopen; the read set back as it is changing nothing (`changed` 0, the
board not modified); on the WiFi copy the 2-layer preset refused, dry run too, as both inner
layers hold copper, then the read edited (a plane and a core added between the inner layers,
the first core's material, constant and height changed), a dry run first changing nothing,
read back equal and after a reopen, 5 copper layers of which 4 signal; a bad list refused
before Altium. Before the tool all 4 errored: "AttributeError: module 'main' has no attribute
'set_pcb_layer_stackup'". After: 4/4 pass in AD25; with `test_live_layer_stackup` (2, the read
it changes) and `test_live_pcb_rules` (1, `pcb_utils.pas`) 7 of 7 live tests passed. Offline:
37 new in `tests/test_layer_stack.py` (presets, checks, the plan, the records, the comparison,
the tool with the bridge faked), added to `.github/workflows/tests.yml`; 453 tests pass
(was 416). Altium was restarted once during the work (3.7 GB, the server's memory guard).
Met on the way, not fixed here: a board open under its short (8.3) path is opened a second
time by a tool given that path, as `long_path` gives the long form and `FocusBoardByPath` does
not find the open document by it; the live test opens its copies by the long path, as
`test_live_project_setup` does.
Decided 2026-11-15 by the run, not the owner: removing a copper layer that holds objects, or a
plane with a net, is refused with each such layer and its object count, nothing changed (dry
run too), because `RemoveFromStack` leaves the objects on a layer outside the stack, which no
read shows; removing them in the call would drop copper the caller did not name.
Decided 2026-11-15 by the run, not the owner: one dielectric between two copper layers, the
surface dielectrics neither added nor removed (as many as the board has, or none), existing
inner layers never reordered, a board with two dielectrics in one gap or a rigid-flex board
refused, because Altium adds and removes a copper layer with one dielectric beside it and the
values are then set by place; adding a dielectric alone was not probed, and the smaller change
covers the presets and a read set back.
Decided 2026-11-15 by the run, not the owner: an inner entry without a `layer_id` keeps the
board's next inner layer of its kind, because a preset set on a board of its own size must
keep the board's layers and what is on them instead of removing and adding them.
Decided 2026-11-15 by the run, not the owner: a value equal to the board's is not written, and
the board is marked modified only when a layer or a value changed, because the read set back
must leave the board as it was, as the item's "read back equal" asks.
Decided 2026-11-15 by the run, not the owner: a layer in use is told by counting its objects
with a board iterator, not by `UsedByPrims`, because that flag stayed True after the layer's
only object was deleted and would refuse a removal that is safe.
Decided 2026-11-15 by the run, not the owner: the read gives `copper_type` (Signal or Plane),
because the set takes the read's form and a plane must come back a plane; the `layer_id` told
it only by its wording.
Fixed in `a389c2a`. Local: on `ad25`, released in `build-20261115-143551`. Upstream: not yet
decided.
Closed: the scenario test of that build held (2026-11-15, second entry, 2): the read
set back changed nothing; the 4-layer preset read back equal, after a save and reopen too,
a track on a new inner layer kept; the 2-layer preset refused while that layer held it, then
removed both inner layers once it was deleted; bad lists refused before Altium. The dry
run's `would_change` leaving out the existing dielectric's changes (same entry, 3) is A37.

### A14 - `create_pcb_rule` covers seven rule kinds - CLOSED 2026-11-15

Clearance, width, hole size, routing
via, solder and paste mask expansion, polygon connect. Not differential pairs, length or
matched length, routing layers, plane connect, component clearance, silkscreen clearances
or hole to hole; no preset that sets a fabricator's minimums at once; priority cannot be
set (the tool's own note). Local: more kinds, differential pair and matched length first,
and a capability preset.
Cause: the tool's Pascal side (`CreatePCBRule` in `pcb_utils.pas`) made only those seven
rule interfaces, and nothing tried priority beyond `Rule.Priority`.
Found 2026-11-15 by the run's probes in AD25 (interface names read from Altium's SDK
interface assembly, each tried in a sandbox script): the kinds are made by
`PCBServer.PCBRuleFactory` with `eRule_DifferentialPairsRouting`
(`IPCB_DifferentialPairsRoutingRule`: `MinGap`/`MaxGap`/`PreferedGap` and
`MinWidth`/`MaxWidth`/`PreferedWidth` per layer, `MaxUncoupledLength`; its descriptor shows
the smallest minimum and largest maximum over all layers), `eRule_MaxMinLength`
(`MinLimit`, `MaxLimit`), `eRule_MatchedLengths` (`Tolerance`), `eRule_RoutingLayers`
(`RoutingLayers(<layer>)`, every layer allowed by default; its descriptor names no layer),
`eRule_PowerPlaneConnectStyle` (`PlaneConnectStyle`, `ReliefExpansion`,
`ReliefConductorWidth`, `ReliefAirGap`, `ReliefEntries`), `eRule_ComponentClearance` (`Gap`,
`VerticalGap`), `eRule_SilkToSolderMaskClearance` (`SilkToMaskGap`),
`eRule_SilkToSilkClearance` (`SilkToSilkClearance`), `eRule_HoleToHoleClearance` (`Gap`),
`eRule_MinimumAnnularRing` (`Minimum`) and `eRule_MinimumSolderMaskSliver`
(`MinSolderMaskSliver`); every property is set directly and is in the saved file. Altium's
board outline clearance rule has `GetState_Gap` and `GetClearance` only, no setter. Priority:
the SDK gives `IPCB_Rule.Priority` a getter only, and `Rule.Priority := 2` in a script stops
it with an exception; no board or server method orders rules. A rule removed and added again
(`Board.RemovePCBObject`, `AddPCBObject`, the same object) goes to priority 1 of its kind and
the others move down, its values kept; that sets any priority.
Fix: eleven kinds more in `create_pcb_rule`, values in mils as before (`server/pcb_rules.py`,
`RULE_KINDS`): `differential_pair` (`min_gap_mils`, `max_gap_mils`, `preferred_gap_mils`,
`min_width_mils`, `max_width_mils`, `preferred_width_mils`, set on every signal layer as
`width` is; optional `max_uncoupled_length_mils`), `length` (`min_mils`, `max_mils`),
`matched_length` (`tolerance_mils`), `routing_layers` (`layers`, the board's signal layer
names routing may use; its other signal layers are set not allowed; a name the board does not
have refused in Altium before anything changes, with the board's signal layers), `plane_connect`
(`connect_style` relief, direct or none; optional `expansion_mils`, `conductor_width_mils`,
`air_gap_mils`, `entries` 2 or 4), `component_clearance` (`gap_mils`, optional
`vertical_gap_mils`), `silk_to_solder_mask`, `silk_to_silk`, `hole_to_hole` and
`solder_mask_sliver` (`gap_mils`), `annular_ring` (`min_mils`). Checks before Altium: min not
above max and preferred between them for each trio, no negative value but a mask expansion's,
no value past 100000 mils (a unit mistake), a number that is a number (not a bool, NaN or
infinity), a layer name without `,`, `;`, `=` or `|`, none named twice. `priority` (1 the
highest of its kind; 0 or none leaves the rule at 1, as before): refused past one more than
the kind's other rules, in Altium before any change, with the range; the rule is added at 1
and the rule at the asked priority is removed and added again, priority minus 1 times, in
the same undo step, so the rules above it keep their order. Each call now reads the rule's
values back from Altium (`read_back`, in the keys given, the layer names for
`routing_layers`) and holds them against what was sent: a value stored otherwise, a per-layer
value that differs between layers, or a priority not reached is listed in `differences`
with `success` false. The warning of a rule scoped to everything now needs it at priority 1,
and a one-scope kind's `scope2` no longer hides it. The result gives the rule's comment too.
Fabricator preset: `create_pcb_rules_preset(preset, board_path, dry_run, replace,
width_preferred_mils, width_max_mils)`, from `server/data/fab_presets/jlcpcb.json`: JLCPCB's
PCB capabilities page (https://jlcpcb.com/capabilities/pcb-capabilities), read 2026-11-15 by
a plain GET (the page shows no date of its own); each rule quotes its row and the page's text,
its figures in mm as the page gives them. `jlcpcb_2layer_1oz`: clearance 0.10 mm and width
minimum 0.10 mm ("0.10 / 0.10 mm (4 / 4 mil)"), hole size 0.15 to 6.3 mm, hole to hole 0.2 mm
between vias (IsVia, IsVia) and 0.45 mm otherwise ("Pad Hole-to-Hole Spacing"), annular ring
0.18 mm on pads ("absolute minimum") and 0.05 mm on vias (derived: half of the 0.1 mm by which
the page says a via's diameter must exceed its hole), silk to solder mask 0.15 mm (IsPad, All;
"Pad to Silkscreen"), solder mask sliver 0.10 mm (1 oz, green, red, yellow, blue, purple).
`jlcpcb_multilayer_1oz`: the same with clearance and width 0.09 mm and the pad ring 0.15 mm.
What the page gives and no rule sets is listed in the file and the result (`not_set`, with
why): hole-to-track clearances, board edge clearance, the non-plated hole and ring minimums,
silkscreen line width and text height, the 1:1 mask opening, the black and white mask bridge,
and no silk-to-silk figure on the page. Rules are named `JLCPCB_2L_1oz_…` / `JLCPCB_ML_1oz_…`,
their comment the page, the date and the row. The page gives a width minimum only: the width
rule is made when `width_preferred_mils` and `width_max_mils` are given, else listed in
`skipped`. A preset rule name already on the board refuses the whole call (unless `replace`);
`dry_run` reads the board's rules only and gives the plan. The preset's data file is kept by
git through a `!server/data/fab_presets/*.json` line in `.gitignore` (upstream ignores
`*.json`).
Test before: `tests/test_live_create_pcb_rule.py` (`ALTIUM_LIVE=1`, copies of the 2-layer
SpiritLevel-SL1 example board, closed unsaved): each of the eleven kinds made, its properties
read through a board iterator by the test's own script, its descriptor through
`get_pcb_rules`, and the properties again after a save and reopen; a routing layer the board
does not have refused, nothing added, the board unmodified; two clearance rules put at the
lowest priority and at 2, the kind's order read back and after a reopen, a priority out of
range refused with the order unchanged; the 2-layer JLCPCB preset by a dry run (nothing
changed, width skipped) and then with a width, each rule's properties, comment and priority
read back (above the board's catch-all or same-scope rule of its kind, below its narrower
ones) and after a reopen, and a second call refused by name. Before the change all 3 failed:
"unknown rule_type 'differential_pair'; one of: clearance, width, hole_size, routing_via,
solder_mask_expansion, paste_mask_expansion, polygon_connect", "TypeError:
create_pcb_rule() got an unexpected keyword argument 'priority'" and "AttributeError: module
'main' has no attribute 'create_pcb_rules_preset'". After: 3/3 pass in AD25; with
`test_live_pcb_rules` (1), `test_live_set_layer_stackup` (4, `pcb_utils.pas`) and
`test_live_drc` (14, a user of `create_pcb_rule`) 22 of 22 live tests passed. Offline: 9 new in
`tests/test_pcb_rules.py` (each kind's encoding and checks, the read-back and its
comparison) and 22 in the new `tests/test_fab_presets.py` (the preset file: its page and
date, each figure in its quoted text or its working given, every rule encoding; the
priorities planned; the tool's priority and read-back and the preset tool with the bridge
faked), added to `.github/workflows/tests.yml`; 484 tests pass (was 453).
Decided 2026-11-15 by the run, not the owner: priority is set by removing and adding again
the rules that stay above the new one, because the API gives no setter and that move keeps
each rule's object and values; the result's read priority, checked against the one asked,
says whether it held.
Decided 2026-11-15 by the run, not the owner: a preset rule goes directly above the highest
rule of its kind that it takes over (scoped to everything, or of its own scope), the lowest of
its kind when there is none, because at priority 1 a rule scoped to everything would override
every narrower rule the designer set, and below the board's catch-all it would never apply.
Decided 2026-11-15 by the run, not the owner: the preset holds only rules whose every figure
is the page's (or worked out from its text, the working written), so the width rule waits for
the caller's preferred and largest width and no routing via style rule is made (the via hole
and diameter minimums are held by the hole size and annular ring rules), because the page
gives no preferred or largest value and a figure from memory is what the decision rules out.
Decided 2026-11-15 by the run, not the owner: `annular_ring` and `solder_mask_sliver` were
added beside the kinds the decision named, because the page's annular ring and mask bridge
minimums are part of a fabricator's minimums and Altium checks them by those two rules.
Decided 2026-11-15 by the run, not the owner: every call reads the values back and reports
`success` false on a difference, because the descriptor of a routing layers rule names no
layer and a differential pair's shows only the extremes over all layers, so it cannot show
what was stored.
Fixed in `4c8b5c0`. Local: on `ad25`, released in `build-20261115-143551`. Upstream: not yet
decided.
Closed for the kinds, the read-back and the preset: the scenario test of that build
held (2026-11-15, second entry, 4): the eleven kinds made and read back equal, after a
reopen too; refusals named; `create_pcb_rules_preset("jlcpcb_2layer_1oz")` made 9 rules at
the priorities planned, a second call refused. Not held for `priority` (same entry, 5): the
property reads right, but `run_drc` in the same session checks by the order the rules were
added until the board is reopened; that is A38, Open.
Decided 2026-11-15 by the run, not the owner: A14 Closed for what held and the priority's
fault made A38, because the kinds and the preset are used as they are, and A38 names the
one thing that does not hold with its workaround.

### A12 - Output jobs can be run and read, not made - CLOSED 2026-11-15

`run_output_jobs` runs containers of
an OutJob that exists and `get_outjob_settings` reads one from disk; nothing creates an
OutJob or sets its outputs (Gerber layers and format, NC Drill, BOM, pick and place, output
folder). Nor are outputs given in the form an assembly service asks for, e.g. JLCPCB's: a
BOM of Comment, Designator, Footprint and the supplier part number; a placement list of
Designator, Mid X, Mid Y, Layer, Rotation, with the per-footprint rotation corrections it
needs; the Gerbers and drill files zipped. Local: a tool that writes an OutJob from a
preset or edits the outputs of one, and a step that turns Altium's BOM and pick and place
into a named service's columns.
Cause: no tool wrote an OutJob (`get_outjob_settings` only parses one, `run_output_jobs` only
runs one), and nothing turned Altium's BOM and pick and place into a service's form.
Found 2026-11-15 by the run's probes in AD25 (OutJobs written by hand after Altium's own
examples, Bluetooth Sentinel and Mini PC, run by `run_output_jobs` on a copy of the
SpiritLevel-SL1 example): an OutJob written as plain INI text, added to the project, runs with
the settings it holds. `GerberUnit` Metric/Imperial with `NumberOfDecimals` 4 gave
`%FSLAX44Y44*%` `%MOMM*%`, Imperial 5 gave `%FSLAX25Y25*%` `%MOIN*%`; NC Drill `ZeroesMode`
`KeepLeadingAndTrailingZeroes` gave `INCH` (2:5, both zeroes kept), `SuppressLeadingZeroes`
gave `INCH,TZ`; `GenerateSeparatePlatedNonPlatedFiles` gave `-Plated` and `-NonPlated` files;
`PlotBoardProfile=True` gave the board's shape as `.GM`; Mid Layer 1 and 2 and Internal Plane 1
in `Plot.Set` gave no file on the 2-layer board (Altium plots only the layers in the stack);
a BOM column named after a parameter no part has comes out empty; BOM `BatchMode` 0 to 6 wrote
.csv, .txt, .xlsx, .html, .xml (+ .xsl), .xlsx and .pdf, and 7 put up "EOleException Unknown
report mode: 7" and stopped the run until its OK was pressed (149 s); a GeneratedFiles
container with `ReleaseManaged`=0 writes into `OutputBasePath`, relative to the project's
folder or absolute, with `OutputPathOutputer` `[Output Type]` one subfolder per output type,
empty none. Altium reloads an open OutJob it has not changed when the file changes on disk,
a moment later: a run started before that used the old settings once (the first run of the
test below: "the second run wrote to the new folder" false).
Fix: `write_outjob(outjob_path, preset, gerber, nc_drill, bom, pick_place, output_folder,
container, board_document, overwrite)` (`server/outjob_writer.py`, the tool in `main.py`; no
Altium). A new file needs a preset; an existing one is edited line by line, every line not
asked for kept as it was (and its encoding: ANSI, or UTF-8 with or without its mark); a preset
over an existing file is refused unless `overwrite`. Each group goes into the first output of
its kind (Gerber RS-274X, NC Drill, BOM_PartType, Pick Place), added from Altium's own record
when there is none, and is connected to the container (named, or the file's first
GeneratedFiles one, added when there is none; a Publish or Printer container refused).
Settings: gerber `units` (mm, inch), `format` (mm 4:2 to 4:4, inch 2:3 to 2:5; a change of
units needs its format), `zeroes`, `origin`, `layers` (names as the read gives them, `copper`
for every copper layer), `board_profile`; nc_drill `units`, `format`, `zeroes`, `origin`,
`separate_plated`; bom `format` (csv, txt, html, xml, xlsx, pdf), `columns`, `group_by` (the
exported BOM not opened, no export dialog); pick_place `units` (mm, mil), `formats` (csv, txt);
`output_folder` (not release managed, no subfolder per type, so the zip can be flat). Every
check runs on a copy before the file is touched. The file is then read back by
`outjob_parser.parse_outjob` and held against what was asked (`differences`, `success` false
when any); the result gives the read (`settings`). `get_outjob_settings` gives a BOM's `bom`
(file format, columns, grouping, sort, whether it opens the export). `run_output_jobs` closes
and opens again an OutJob Altium has open with no unsaved change, so the run uses the file as
saved (`outjob_reloaded`); one with unsaved changes is run as Altium has it, not closed, and
the result says so (`outjob_unsaved_changes`, `note`); the flag is read through `BoolToStr`,
as `DocumentModified` says (read directly it is always False in the bridge, which would have
closed an OutJob with unsaved changes and dropped them).
Preset `fab_jlcpcb` (`server/data/output_presets/jlcpcb.json`, kept by git through
`!server/data/output_presets/*.json` in `.gitignore`), from JLCPCB's pages read 2026-11-15 by
a plain GET each, each setting quoting its page: "How to Generate Gerber Files in Altium
Designer 26" (https://jlcpcb.com/help/article/how-to-export-altium-pcb-to-gerber-files, "Last
updated on Nov 10, 2026", made with AD 26.1.1, its dialogs unchanged in 24 and 25 by the page):
Gerber "Units: Millimeters", "Decimal: 0.0001 mm (a 4:4 coordinate format ...)", "Suppress
leading zeroes", the layers Board Outline (.GM), Top/Bottom Layer, Overlay, Solder and Paste,
one outline only; NC Drill "Units: Inches", "Format: 2:5", "Keep leading and trailing
zeroes", "Reference to absolute origin", plated and non-plated holes in separate files; the
zip .zip and flat. "How to Generate BOM and Pick and Place Files in Altium Designer"
(https://jlcpcb.com/help/article/how-to-generate-bill-of-materials-and-centroid-file-from-altium,
"Last updated on Sep 09, 2026"): the BOM in CSV, Comment, Designator, Footprint, the LCSC part
number last, from "a new parameter named LCSC Part #". "Bill of Materials for PCB Assembly"
(https://jlcpcb.com/help/article/bill-of-materials-for-pcb-assembly, Sep 09, 2026): Comment,
Designator, Footprint. "Pick & Place File for PCB Assembly"
(https://jlcpcb.com/help/article/pick-place-file-for-pcb-assembly, Sep 09, 2026): Designator,
Mid X/Mid Y "Required units: Metric(mm)", Layer "Top / Bottom", Rotation "Positive values are
counter clockwise". Container "JLCPCB Outputs", folder "JLCPCB". The first URL the brief named
(`how-to-generate-gerber-and-drill-files-in-altium-designer`) gave 404; the pages above were
found by a search of jlcpcb.com.
Offline step: `make_assembly_files(service, bom_path, pick_place_path, gerber_dir, out_dir,
part_number_parameter, rotations_path, name)` (`server/assembly_files.py`; no Altium), service
`jlcpcb` from the same file: `<name>_JLCPCB_BOM.csv` (Comment, Designator, Footprint, LCSC Part
#, one row per row of Altium's BOM; the part number from the column named by
`part_number_parameter`, default "LCSC Part #"; a missing column refused, naming the columns
the file has), `<name>_JLCPCB_CPL.csv` (Designator, Mid X, Mid Y in mm with 4 decimals, from
Altium's Center-X/Y in mm or mil, Layer Top or Bottom, Rotation corrected), and
`<name>_JLCPCB_Gerber.zip`, flat, of gerber_dir's own files whose content is a Gerber (a `%FS`
statement) or an Excellon file (starts with `M48`); Altium's reports beside them are listed in
`not_zipped`. The result names the parts with no part number, the rotations applied (the table
row each), and the designators in only one of the two files. The rotation table
`server/data/output_presets/jlcpcb_rotations.csv` (footprint name or `*`/`?` pattern, degrees
added, Top/Bottom or both, note; `#` lines are comments; the first row that matches is used) is
empty, for the owner to fill.
Test before: `tests/test_live_outjob_writer.py` (`ALTIUM_LIVE=1`, a copy of the SpiritLevel-SL1
example project, closed unsaved): the preset written, read back by `get_outjob_settings`
(Gerber Metric 4 Absolute, suppressed leading zeroes, board profile, every copper layer, no
mechanical or keep-out layer; NC Drill Imperial 2:5, zeroes kept, absolute, plated apart; BOM
csv with the four columns; pick and place mm CSV; the container's folder, not release managed,
not added to the project), a preset over it refused and the file unchanged, added to the
project and run: the .GTL `%FSLAX44Y44*%` `%MOMM*%`, the nine layers' files and no .GM1 or .GKO,
the plated and non-plated drill files `;FILE_FORMAT=2:5` and `INCH`, the BOM's header, the pick
and place in mm; then, the OutJob open in Altium, edited (Gerber inch 2:5, pick and place mil,
folder "JLCPCB inch"), read back, run again: the new folder, `%FSLAX25Y25*%` `%MOIN*%`, Center-X
in mil, `outjob_reloaded` true; marked modified in Altium and run: `outjob_unsaved_changes`
true, not reopened; last the offline step on Altium's files with a one-row rotation table: the
BOM and CPL columns and row counts, R10 (CR2012-0805) turned by 90, Mid X equal to Altium's
Center-X, the zip flat with the nine Gerbers and the drill files and without the reports, the
designators in one file only as the files give them, and the mil file giving the same mm within
0.001. Before the tools it errored: "AttributeError: module 'main' has no attribute
'write_outjob'". On the old `run_output_jobs` script it fails at "None is not False" (no
`outjob_reloaded`).
After: 1/1 passes in AD25 (run twice in its final form); with `test_live_project_setup` (9, the other
functions of `other_utils.pas`) and `test_live_resident` (5, the bridge's bundle changed) 15 of
15 live tests passed, on an Altium restarted by the run (the server's memory guard stopped the
first try at 3.7 GB). Offline: 20 new in `tests/test_outjob_writer.py` (layer IDs both ways,
each setting's keys and checks, the preset and its pages, an Altium file edited with one line
changed, an output and a container added and connected, a refused request changing nothing,
the read-back comparison, the tool's refusals and encoding), 14 in `tests/test_assembly_files.py`
(Altium's real BOM and pick and place in mm and mil from this test's run, as fixtures in
`tests/fixtures/`, their path line made neutral; the rotation table; the files, the zip, the
refusals) and 1 in `tests/test_outjob_parser.py` (the BOM summary), the two new modules added to
`.github/workflows/tests.yml`; 519 tests pass (was 484).
Decided 2026-11-15 by the run, not the owner: the Gerber origin is absolute, because the page
gives none for the Gerbers and gives "Reference to absolute origin" for the drill files, and the
two must line up.
Decided 2026-11-15 by the run, not the owner: the preset plots every copper layer Altium has
(Top, Mid Layer 1 to 30, Internal Plane 1 to 16, Bottom), because Altium writes a file only for
those in the board's stack (probed), so a 4- or 6-layer board gets its inner layers without the
preset knowing the board, where a fixed 2-layer list would drop them silently; the read lists
all 48 as the file holds them.
Decided 2026-11-15 by the run, not the owner: the board profile (`PlotBoardProfile`, written as
.GM) is the preset's one outline, no mechanical layer, because the page names Board Outline
(.GM) the standard and asks for one outline layer, and which mechanical layer holds a board's
outline differs from board to board.
Decided 2026-11-15 by the run, not the owner: the BOM's part number column and its default
parameter are "LCSC Part #", because that is the parameter the Altium page tells to add and its
last column; another name is given by `part_number_parameter` (and the BOM's `columns`).
Decided 2026-11-15 by the run, not the owner: the BOM's grouping is Comment, Footprint and LCSC
Part #, one row per part with its designators together, because the pages give no grouping and
show rows of several designators; Mid X and Mid Y are plain numbers in mm, because the page names
the unit, not a suffix; the aperture tolerance stays Altium's 50 (0.000127 mm), which Altium
shows as the page's 0.00013 mm.
Decided 2026-11-15 by the run, not the owner: BOM `BatchMode` 2 (also .xlsx) is not offered and 7
and up are refused, because 2 and 5 wrote the same kind of file with no way told apart and 7 put
up an error that stopped the run.
Decided 2026-11-15 by the run, not the owner: `run_output_jobs` closes and opens again an open
OutJob with no unsaved change, because Altium's own reload of a changed file comes a moment later
and a run before it used the old settings once; it costs a close and an open, and an OutJob with
unsaved changes is left as it is and named in the result. The test shows the reload and the
unsaved case; it does not fail reliably on the old script by its effect (after a 3 s pause Altium
had reloaded the file itself, three runs of three), only by the missing flag.
Decided 2026-11-15 by the run, not the owner: a rotation row adds its degrees as given on the
side it names (both when none), because the pages read give no correction and no rule for the
bottom side, and the owner fills the table from what JLCPCB's review shows.
Decided 2026-11-15 by the run, not the owner: `write_outjob` does not add the file to the
project; the caller does it with `add_project_document`, because that tool already does it and
checks it, and `write_outjob` then needs no Altium.
Fixed in `cc1015d`. Local: on `ad25`, released in `build-20261115-143551`. Upstream: not yet
decided.
Closed: the scenario test of that build held (2026-11-15, second entry, 6):
`write_outjob(preset="fab_jlcpcb")` added to the project and run gave nine Gerbers (mm,
`.GM` outline), the drill file (2:5 inch), the BOM with the LCSC column and the pick and
place in mm; the OutJob edited (Gerber inch, pick and place mil) while open was reloaded
(`outjob_reloaded` true); `make_assembly_files` gave the same Mid X/Y from the mil file as
from the mm file, applied a two-row rotation table and zipped flat; refusals named. The size
of its result (same entry, 7) is A39.

### A40 - A15 (a), parts from an `.IntLib` and the DbLib search as a tool - CLOSED 2026-11-15

`build_schematic`
and `edit_schematic`'s `place_component` refused any library but a `.SchLib`, in Python,
before Altium was called: the bridge placed a part by opening its library as a document and
copying the symbol, and a symbol inside an `.IntLib` cannot be opened that way. A `.DbLib`'s
database could be searched only with `dev/db_search.py`, a command line, not a tool. (The
review of 2026-11-12, A15; split from it by the run.) Local.
Fix: `server/AltiumScript/schematic_utils.pas`, `PlaceIntLibComponent`: a part from an
`.IntLib` is placed by Altium's own `IntegratedLibraryManager.PlaceLibraryComponent` (library
reference, path, `Designator|Orientation|Location.X|Location.Y`), which places it on the
schematic in front, so the sheet is brought to the front first; it returns no object, so the
part is placed under a designator no part has, found by it, and then given its designator,
mirror, exact place and comment as a `.SchLib` part is. `BuildCircuitFromSpec` (a `PART`
record) and `PlaceSchComponent` (edit's `PLACE`) take that way for an `.IntLib` path; a part
not in the library (`PlaceLibraryComponent` returns False) is reported as a missing part or
an operation's error, as from a `.SchLib`. The Design Item ID, which links the part to its
entry in the library, is kept unless `design_item_id` is given. `server/main.py` and
`server/sch_edit.py` accept `.SchLib` or `.IntLib`. New `server/dblib.py`, the search from
`dev/db_search.py` made a module: the DbLib's tables and part-number field (`Key=` or
`UserWhereText`), its connection string (a relative Data Source resolved against the
DbLib's folder), one SELECT at a time through OLE DB (anything else refused, names and
terms quoted, LIKE wildcards in a term taken literally), a failed query reported with the
database's message; a match names its symbol and footprint by the DbLib's own field
mappings (`[Library Ref]`, `[Footprint Ref]`, ...) or by column name. New tools
`search_dblib` (term, or a part number giving all its fields; read-only, needs no Altium)
and `get_installed_libraries` (bridge command `get_installed_libraries`, from
`IntegratedLibraryManager.InstalledLibraryPath`; `search_dblib` with no path takes the one
DbLib installed). `dev/db_search.py` is now a command line over `server/dblib.py`. README's
tool list updated.
Test before: `tests/test_live_libraries.py` (`ALTIUM_LIVE=1`, AD25; an `.IntLib` compiled by
Altium in a temporary folder from copies of the SpiritLevel-SL1 example's libraries, and a
copy of the Atmel QTouch `.IntLib` Altium ships) failed 4 of 4 on the old code:
`build_schematic` gave `symbol_library must be the full path of an existing .SchLib file
(integrated libraries such as .IntLib are not supported)`, `edit_schematic` gave
`operation 1: library must be the full path of a .SchLib file`, and
`main.get_installed_libraries` did not exist.
After: `test_live_libraries` 5/5 (a sheet built from two `.IntLib`s and a `.SchLib`, each
part read back through Altium with its library reference, library name, Design Item ID,
place, rotation, mirror and comment, and the `.IntLib` part's footprints equal to the
symbol's in the library it was compiled from; a part missing from an `.IntLib` reported;
`place_component` from both `.IntLib`s with a missing one reported, saved and read back
from the reopened file; one undo takes back an edit that placed an `.IntLib` part and a
wire; `get_installed_libraries` equal to Altium's list, a library installed by the test
listed as `IntLib` and gone once uninstalled). The live tests of the tools touched:
`test_live_project_setup.LiveProjectTest` 4/4 and `test_live_symbol_footprint` 9/9. Offline
533 OK (was 519): new `tests/test_dblib.py` 14 (its 4 database tests search CSV files
through the Access database engine's text driver, skipped where it is not installed, as on
CI), `test_sch_edit` with an `.IntLib` placed and a `.PcbLib` refused; `tests.test_dblib`
added to `.github/workflows/tests.yml`.
Decided 2026-11-15 by the run, not the owner: the done part carries the code A40 and names
A15 (a) in its title, A15 staying Open for (b), because a code can head one item only
(`board.py --check`), as A34 (a) became A35.
Decided 2026-11-15 by the run, not the owner: an `.IntLib` part is placed by
`PlaceLibraryComponent`, not by extracting the library's symbols to a `.SchLib` and copying
from there, because Altium then links the part as it links one it places itself (Design
Item ID, library name, the library's models) and no extracted copy is left on disk. Altium
sets the placed part's library path to `*` and its library name to the file's name; the
tool keeps both.
Decided 2026-11-15 by the run, not the owner: `get_installed_libraries` added, not named in
the item, because `dev/db_search.py` found the DbLib among Altium's installed libraries
when none was given, and a caller has no other way to learn the path of an installed
`.IntLib` to place from; one read-only call.
Decided 2026-11-15 by the run, not the owner: a database query that fails is an error with
the database's message, where `dev/db_search.py` printed it and returned no rows, because
no rows from a failed query read as "no such part".
Decided 2026-11-15 by the run, not the owner: the live test compiles its `.IntLib` from the
example's libraries and uninstalls it again (Altium installs a library it compiles),
because the `.IntLib`s AD25 installs carry no footprints to read back.
Fixed in `5c25999`.
Local: on `ad25`, released in `build-20261115-172812`. Upstream: not yet
decided.
Closed: the scenario test of that build held (2026-11-15, third entry, 1 and 2):
`search_dblib` on a test DbLib over CSV files (tables enabled and disabled, by `Key=` and by
`UserWhereText`; a quote, `%` and `_` taken literally; a part number in an enabled and in a
disabled table; refusals and the engine's error named); `get_installed_libraries` listed the
seven installed libraries; `build_schematic` and `place_component` from two `.IntLib`s and a
`.SchLib`, read back through Altium and from the saved file with library reference, library
name, Design Item ID, place, rotation, mirror, comment and the library's models, every pin
equal to `pin_map`; a missing symbol reported, a wrong library refused. What it left: A42
(same entry, 6) and A43 (7).

### A8 - No tool to make a PcbLib from a board - CLOSED 2026-11-15

`RunProcess('PCB:MakeLibrary')` and
`Client.SendMessage('PCB:MakeLibrary', ...)` from `run_altium_script` returned success and
did nothing (no document, no dialog); it was done by hand through the menu. Local: find a
way that works from a script (the process with its parameters, or building the library from
the board's footprints through the PcbLib API), then a tool. (2026-11-12, 7.)
Probe 2026-11-15 by the run, live in AD25, on a copy of the SpiritLevel-SL1 example project
(its board: 115 components, 29 patterns). Cause: `PCB:MakeLibrary` is the menu item's
process launcher id (`PLPCB:MakeLibrary` in `AdvPcb.rcs`), not a command; its command is
`PCB:BuildPCBLibrary` with `AddLibraryToProject=True`, which hands over to
`MakeLib:BuildPCBLibrary` (`Makelib.ins`, "Builds a PCB library from the current board").
`Makelib.dll` reads three parameters: `RunHidden`, `AddLibraryToProject` and `FileName`.
`RunProcess('PCB:BuildPCBLibrary')` with `RunHidden=True` and `AddLibraryToProject=False`,
the board in front, made the library in about 20 s with no dialog: a new, unsaved PCB
library document named `<board name>.PcbLib` in the board's folder (nothing written there),
32 footprints (one per pattern, and `HDR1X2_2`, `CC2012-0805_2`, `CR2012-0805_2` where
components of one pattern differ, as the menu does), the board and the project file left
unmodified, the project's documents unchanged. With a file of that name already there it
named the document `<board name>1.PcbLib` and left the file alone. `FileName` (a full path,
with or without `.PcbLib`) was ignored. `DoSafeChangeFileNameAndSave` then wrote the
library at another path in one save, and the file reopened held 32 footprints;
`IPCB_Library.RemoveComponent` took footprints out before the save (the one shown
included), and the file reopened held the 2 kept. So the API way (copying each footprint's
primitives) was not needed.
Fix: `make_pcblib_from_board(board_path, library_path, footprints)` (`main.py`,
`board_library.py`, `MakePcbLibFromBoard` in `other_utils.pas`). The script notes the
document in front and whether the board is open and modified, opens the board when it is
not, reads its components (pattern and pad count), refuses a name in `footprints` that is
not a pattern of the board before anything is made, runs the process as above, takes the
PCB library that was not open before as Altium's, removes the footprints not asked for
(a pattern keeps its `_<n>` variants), saves it at `library_path` and closes it, then opens
the saved file again and reads each footprint's pads and primitives, and closes it. The
board is left as found: closed again when it was not open, its flag cleared when the call
marked a board that had no unsaved change (the process did not), the document that was in
front shown again. `board_library.summarise` compares the file read back with the board:
a pattern in scope with no footprint, a footprint whose pad count no component of its
pattern has, a component pad count no footprint of its pattern has, a footprint kept but not
in the file; any of these fails the call, the file kept and named. Refused before Altium: a
file at `library_path` (nothing overwritten), not a `.PcbLib`, a board not found or not a
`.PcbDoc`. One call on the example board: 26 s, 32 footprints from 29 patterns (PQ208 with
210 pads), 2.1k characters.
Live test `tests/test_live_pcblib_from_board.py` (copy of the SpiritLevel-SL1 project
folder, each library read back by `get_footprint_primitives` on the saved file and compared
with the tool's result and with the board's components read by a board iterator): before
the tool, 3/3 failed, "AttributeError: module 'main' has no attribute
'make_pcblib_from_board'". After, 4/4: the board open in its project with a sheet in front
(32 footprints read back equal, every pattern there with its pad counts; the open documents,
the document in front, the board's and the project file's flags, the project's documents
and the project folder's files all as before); the board not open and three patterns asked
for (4 footprints, `CR2012-0805_2` with its pattern, 28 removed, the board closed again);
a board with unsaved changes still marked after; refusals (a file there unchanged, a name
not on the board, a board not found: no file written, no document left open). With
`test_live_symbol_footprint` (the footprint tools; 9/9): 13/13 in 222 s. Offline 545 OK
(was 533): new `tests/test_board_library.py` 12, added to `.github/workflows/tests.yml`.
Decided 2026-11-15 by the run, not the owner: Altium's own Make PCB Library, not a copy of
each footprint's primitives through the API, because the process run hidden worked from a
script and copies every primitive kind and 3D body as the menu does, with less code to be
wrong.
Decided 2026-11-15 by the run, not the owner: the board goes to the bridge as
`source_board`, not `board_path`, because `board_path` makes the bridge open and remember
the board before the command runs, and the command could then not know it had to close it
again.
Decided 2026-11-15 by the run, not the owner: a name in `footprints` that is not a pattern of
the board refuses the call with nothing made, and a library that does not agree with the
board after the save fails the call with the file kept and named, because a library missing
a footprint asked for, reported as success, is a wrong result.
Decided 2026-11-15 by the run, not the owner: Altium's `<pattern>_<n>` footprints are kept,
named with their pattern, and come with a pattern asked for, because each is the footprint
of components on the board that differ from the first of that pattern.
Fixed in `de0620d`.
Local: on `ad25`, released in `build-20261115-172812`. Upstream: not yet
decided.
Closed: the scenario test of that build held for what it asked (2026-11-15, third entry,
4): 12 footprints, each equal to a library made by hand from the menu in pads, tracks, arcs,
texts and 3D bodies; the filter in lower case, a board not open (closed again), a board with
an unsaved move (still modified), the document in front restored, the folder unchanged, six
refusals. The footprints' descriptions lost with `problems` [] (same entry, 5) is A41.

### A49 - `get_erc_violations` returns every violation in full, past the result limit - CLOSED 2026-11-23

Sorted out of the entries of 2026-11-18 (second), point 7: 155k characters (capped at 1000
violations), failed the tool-result limit, read from the saved file; 2026-11-19 (first),
point 2: 273 violations, about 150 of them one sheet's "Duplicate nets"; 2026-11-19
(second), point 5: 199 violations, about 100,000 characters, over the client's limit three
times, most of it 99 warnings of one kind and 30 of another.

Proposed: local; a summary by default (counts by type and level, the first few of each),
with `type`, `level` and `limit` filters for the details. Not decided.

Met again 2026-11-22 (findings 2026-11-22, point 1), build `0.7.0-20261115-172812`, measured
from the transcripts of seventeen schematic and library sessions: up to 105k characters of
results in one session (6 calls) and 76k in another (2 calls), the largest of the server's
own share of a session's cost.

Decided 2026-11-22 in the plan (the owner's token rule): by default grouped by type and
level, each with its count and its first three violations in full, the full list in a file
whose path the result gives; no new argument.

Cause: the bridge's `GetERCViolations` (`other_utils.pas`) puts every `DM_Violations(I)` in
the reply as `{level, type, detail}`, and the tool passed the reply on whole; a few kinds
repeated by the hundred make up most of it. The tool wrote no file to point to: the
bridge's `WriteJSONToFile` only returns its text.

Fix (`server/erc_summary.py`, `get_erc_violations` in `server/main.py`): Altium's reply is
grouped in Python, `violations` replaced by `groups [{level, type, count, first}]`
(`first`: the details of the group's first three violations, in Altium's order; fatal, then
error, then warning, the largest group first) and `full_list`, the path of a JSON file
holding Altium's whole reply; `total`, `fatal`, `errors`, `warnings` and the sheet status
as before. A file that cannot be written gives `full_list: null` and `full_list_error`. An
error reply passes through unchanged. A50's `suppressed` count goes beside `total`; not
done here. The description, `manifest.json` and `README.md` say so.

Decided 2026-11-22 by the run, not the owner: the full list written into the server's own
per-user folder (`%USERPROFILE%\.altium-mcp`, beside `config.json` and the log), one file
per project, `erc_<project>_<hash of its path>.json`, overwritten by the next call, because
the tool wrote no file and the public exchange folder was cleared of design data on
purpose (`LEFTOVER_TEMP_FILES`), and one file per project keeps two sessions on two
projects from overwriting each other's list.

Decided 2026-11-22 by the run, not the owner: `first` holds the details only, the level and
type being the group's, because it keeps each violation's text whole at the smallest size.

Test before: `tests/test_live_erc.py` (a copy of the SpiritLevel-SL1 example's four child
sheets as a flat project with a second copy of each: 276 violations, six kinds), on the old
code: `AssertionError: 38833 not less than 10000 : the result is 38833 characters, over
10000`. After: 1/1 pass in AD25, 276 violations in 6 groups, 2,146 characters, the counts
summing to the total and to each level's count, the file's list matching each group's count
and first three (36,626 bytes); `test_live_drc.LiveCompileFolderTest`, which calls the tool,
2/2 pass (it now deletes the file it made). Offline: `tests/test_erc_summary.py`, 11 tests,
added to `tests.yml`; the whole list 556/556 pass. Tool listing: 80 tools, 164,529
characters before, 164,709 after (+180, 0.1 %).

Fixed in `69f2cf9`. Released in `build-20261123-001227`.

Held 2026-11-23: the scenario test of build 0.7.0-20261123-001227 (findings 2026-11-23, point 1): on a project of eight copies of one small sheet, 400 violations, 239 listed in 5 groups and 161 suppressed; 1.6k to 1.8k characters, against 45k for the same reply in the old format; the group counts summing to `total` and to `errors` (235) and `warnings` (4); `compile=false` gave the same groups; the full-list file held all 400, each marked.

### A50 - `get_erc_violations` lists violations Altium has suppressed - CLOSED 2026-11-23

Sorted out of the entry of 2026-11-19 (fourth), point 1, which found the cause of
2026-11-19 (third), point 8. Six "Nets containing floating input pins" errors, each on a pin
with a no-ERC marker exactly on its end (`IsActive` and `SuppressAll` true), and their twelve
warnings are in the tool's result; Altium's Messages panel after a GUI compile does not show
them. A test marker on another net's pin left that net's warning in the list too.
`GetERCViolations` (other_utils.pas) reads every `Project.DM_Violations(I)` with no
suppression test; `ReportSuppressedErrorsInMessages=0` in the project file says the compile
keeps suppressed ones and the panel hides them. Reported success, with errors that are not
there: a session spent calls on markers that worked.

Proposed: local; the suppressed ones left out, or reported apart (`suppressed: n`); the
property that tells them is not known yet (the DM names tried failed). Not decided.

Decided 2026-11-22 in the plan (the owner's token rule): no new tool or argument; a probe
first; found, the suppressed ones left out of the groups and counted as `suppressed: n`.

Cause: the bridge's `GetERCViolations` (`other_utils.pas`) put every `DM_Violations(I)` in
the reply and counted it in `total` and its level, with no suppression test. Probe (a
sandbox script on the test's sheet below): `IViolation.DM_IsSuppressed` exists on AD25 and
reads True for exactly the two violations of the pin under the marker (the floating input
pin's error and its net's no-driving-source warning), False for the others;
`DM_Suppressed`, `DM_IsHidden`, `DM_IsIgnored` and `DM_IsVisible` do not exist, and
`DM_CompilationStage`, `DM_GeneralField`, `DM_ImageIndex` and the descriptor strings do not
tell. The violation's related pin gives no location (`DM_LocationX` -9999), so a match
against the markers would have had to find each pin on its sheet.

Fix: the bridge marks each violation `suppressed` (true or false) and counts the suppressed
ones in `suppressed`, outside `total`, `fatal`, `errors` and `warnings`;
`erc_summary.summarize` groups only those not suppressed; the full-list file keeps every
violation, marked. The description, `manifest.json` and `README.md` say so.

Decided 2026-11-22 by the run, not the owner: the suppressed ones counted out of `total` and
their level's count as well as out of the groups, because the result then counts what
Altium's Messages panel shows and the groups still sum to `total`.

Decided 2026-11-22 by the run, not the owner: Altium's own `DM_IsSuppressed`, not a match of
pin locations against the active no-ERC markers, because it is Altium's decision, markers
that suppress chosen types only included, with nothing re-implemented.

Test before: `tests/test_live_erc.py`, `LiveErcSuppressedTest` (a one-sheet project, a copy
of the SpiritLevel-SL1 example's power sheet, a test point moved so its input pin floats,
then a no-ERC marker on that pin's end), on the old code: `AssertionError: Lists differ:
[{...}] != [] ... : a violation Altium suppresses is still listed: [{'level': 'error',
'type': 'Nets containing floating input pins', 'count': 1, 'first': ['Net NetTP1_1 contains
floating input pins (Pin TP1-1)']}]`. After: 1/1 pass in AD25, 4 violations before the
marker, after it 2 listed and 2 suppressed, the two marked in the file. A49's test on the
same example's doubled project: 207 violations listed and 69 suppressed by the example's own
markers (276 in all), 6 groups, 2,164 characters. `test_live_erc` and `test_live_drc`
together 16/16 pass. Offline: `tests/test_erc_summary.py` 12 tests (one added); the whole
list of `tests.yml` 557/557 pass. Tool listing: 80 tools, 164,709 characters before,
164,841 after (+132, 0.08 %).

Fixed in `49ecf2f`. Released in `build-20261123-001227`.

Held 2026-11-23: the scenario test of build 0.7.0-20261123-001227 (findings 2026-11-23, point 3): a sheet with 23 active no-ERC markers (`SuppressAll`) on unused connector pins, listed by earlier releases as 23 "Nets with only one pin" errors, now `total` 4 and `suppressed` 23, Altium counting exactly 23 active markers; with the markers removed from four of the eight copies of point 1's sheet (the project reopened, see A48), 92 of those errors moved from `suppressed` to the list; a project with no markers, 5 warnings and 0 suppressed, as before.

### A74 - `get_erc_violations`' `first` repeats one text - CLOSED 2026-11-23

Sorted out of the entry of 2026-11-23, point 2, the scenario test of build `0.7.0-20261123-001227`: a
violation's detail does not name its sheet, so on a project of repeated sheets a group's
first three often read the same ("Net X has only one pin (Pin J1-4)" three times,
"Duplicate Net Names Wire X" three times), two of the three lines telling nothing. Reported
success, rightly: the counts are right, the lines wasted.

Local: `first` holds the group's first three *distinct* details (A49's grouping,
`server/erc_summary.py`). The entry also proposed the sheet with each detail.

Decided 2026-11-23 by the run, not the owner: taken into group 1 again, by the run's rule
for a new point small and in the group's files (*The scenario test of a group*, 7), because
it is A49's grouping; the first three distinct details, not the sheet with each, because
the token rule asks for the smaller change.

Cause: `erc_summary.group` kept the first three details as they came, and a detail that
Altium gives for each of several copies of a sheet is the same text each time. Fixed in
the commit that moves it here: a detail already in the group's `first` is not added again,
so `first` is the first three distinct ones in Altium's order, fewer when the group has
fewer; `count` still counts the repeats. The description and the README say "first 3
distinct details" (the tool listing 157,971 to 157,962 characters, 80 tools).
Tests first: two offline in `tests/test_erc_summary.py` (failed, `['A', 'A', 'A'] !=
['A', 'B', 'C']` and the same of a group with one distinct detail) and a live one in
`tests/test_live_erc.py` on four copies of the SpiritLevel-SL1 example's power sheet
(failed, "Lists differ", the group Duplicate nets starting with one text twice). After,
2026-11-23: `test_erc_summary` 14/14; live in AD25 `test_live_erc` 3/3 (that project 1,066
characters before and 1,067 after, the third line now a new one; A49's 207 violations
2,163 both times, the counts summing to the total), `test_live_compile_refresh` and
`test_live_drc`'s `LiveCompileFolderTest` 9 run, OK with A48 (b)'s two expected failures;
the offline list 559, OK.

Fixed in `12ce1ca`. Released in `build-20261123-031122`.

Held 2026-11-23: the scenario test of build 0.7.0-20261123-031122 (findings 2026-11-23, second entry, point 1): on eight copies of one small sheet, groups of 35 (5 distinct texts), 127 (28) and 92 (23) each gave three different lines where their first three violations were one text; a group of 4 with one distinct text gave one line and `count` 4; no `first` repeated a text in any of the 13 replies, the group counts summed to `total` in each, and `compile=false` gave the same groups.

### A46 - `build_schematic`'s `pin_map` is keyed by pin name and always returned whole - CLOSED 2026-11-23

Sorted out of the entry of 2026-11-18 (second), points 2 and 9. Pins sharing a name
(several `GND`, two shield pins, five `VDD`) collapse to one entry, the last; pin numbers
would keep them apart. And the whole map comes back on every call (a 71-part sheet: about
20k characters) when the caller has already computed every pin.

Proposed: local; keyed by pin number, the name as a field, and an option to leave the map
out. Not decided.

Met again 2026-11-22 (findings 2026-11-22, point 1), build `0.7.0-20261115-172812`, measured
from seventeen sessions' transcripts: `build_schematic` 142k characters of results over 14
calls in one session, the whole pin map coming back each time (with A58: 171k of input).

Decided 2026-11-22 in the plan, not the owner: `pin_map` keyed by pin number, the name a
field; returned in full only on a call with no wires (the pin read the description advises);
with wires, a count per part, the map written to a JSON file in the server's own folder and
that file's path given; no new argument, because it is the smaller change.

Cause: the bridge's `pin_map.txt` had each pin's name and not its number, so
`build_schematic` could key only by name, a later pin of one name replacing the earlier; and
it put the map into every result, indented, four lines a pin.

Fixed in the commit that moves it here: the script writes `PIN|designator|number|x|y|name`
(the name last, as it may hold a pipe), and the new `server/pin_map.py` makes
`{designator: {number: {name, x, y}}}` of it. With no wires that is `pin_map`; with wires
the result has `pin_counts` and `pin_map_file` instead, and if the file cannot be written
the map itself with `pin_map_file_error`. The description, the README and the manifest's
line say so (the tool listing 157,962 to 158,036 characters, 80 tools).

Decided 2026-11-23 by the run, not the owner:
- a number a part has twice (two shield pins `SH`, two parts of one designator) gets `#2`,
  `#3`, because keyed by number alone such pins would be lost as the names' were;
- "the server's own folder" is the per-user data folder, `%USERPROFILE%\.altium-mcp\pin_maps`,
  because A49's full list goes to that data folder and the exchange folder is readable by
  every account on the machine;
- one file per build, the newest 20 kept, not one per sheet, because Altium named two builds
  in a row `Sheet1.SchDoc` (the first closed), so a path given earlier would have come to
  hold another sheet's pins;
- the tool's result is JSON without indents, because indented, the map with a name in each
  pin would take nearly twice the characters.

Tests first. Live, `tests/test_live_pin_map.py`, on 24 parts of a 16-pin symbol made in a
copy of the SpiritLevel-SL1 example's library (four GND, three VDD, two pins numbered SH),
2 failed: "pins of the map were lost" (10 of each part's 16) and "14022 not less than or
equal to 2000 : the result with wires is too large". Offline, `tests/test_pin_map.py`, 8
failed on the code before (5 failures, 3 errors: `'pin_map' unexpectedly found`,
`KeyError: 'pin_map_file'`, and the new line format read as `{}`).

After, 2026-11-23, live in AD25: `test_live_pin_map` 2/2 (with wires 447 characters, was
14,022; without 16,568 with all 384 pins, was 14,022 with 240; each pin's number, name and
point equal to what Altium gives on the sheet), `test_live_libraries` 5/5,
`test_live_project_setup` 9/9, and of `test_live_symbol_footprint` the one test that builds a
sheet, 1/1; the offline list, the new module added, 567, OK. The other live tests not run.

Seen and left: a build with a missing part comes back as the error text, with no pin map;
`pin_map.txt` in the exchange folder is read after the bridge's lock is released, so two
sessions building at once could read each other's map (both by reading the code, not
tested). A part on a multi-part symbol is A45's.

Built in build `0.7.0-20261123-103915` (tag `build-20261123-103915`), commit `a441051`.

Held 2026-11-23: the scenario test of build 0.7.0-20261123-103915 (findings 2026-11-23, the group 2 entry, point 1): on a build with no wires of five parts, `pin_map` keyed by number, 162 pins with the 32 sharing one name all kept, each point the saved file's pin end; with wires, `pin_counts` and `pin_map_file` only (1.3k characters), the file's points the sheet's.

### A58 - `build_schematic` and `edit_schematic` take no spec file - CLOSED 2026-11-23

Sorted out of the entry of 2026-11-18 (first), point 3, seen before drawing: a sheet of some
60 parts and 150 wires goes in as inline JSON, about 20k characters a sheet;
`create_symbols_batch` takes a spec file, the sheet tools none.

Proposed: local; a `spec_file` on both. Not decided.

Met again 2026-11-22 (findings 2026-11-22, point 1), build `0.7.0-20261115-172812`, measured
from seventeen sessions' transcripts: 171k characters of `build_schematic` input over 14
calls in one session, the inline sheet sent each time (with A46: 142k of results).

Decided 2026-11-22 by the owner (the opening answer of `## Run 2026-11-22`): taken, a `spec_file` argument on `build_schematic` and `edit_schematic`, the one new argument of that run.

Cause: both tools took the sheet only as call arguments, `parts`, or `sheet_path` and
`operations`, required there.

Fixed in the commit that moves it here: both take `spec_file`, the full path of a JSON file
of their other arguments, read by the new `server/spec_args.py` and checked as the same
types. An argument in both places is refused, and nothing is sent to Altium. The
descriptions, the README and the manifest's two lines say so. The tool listing 158,036 to
158,565 characters (0.3%), 80 tools.

Decided 2026-11-23 by the run, not the owner:
- arguments that are not in the file may be given inline beside it, because the decision
  refuses the argument given twice, and two different ones need no merge rule;
- the other arguments of both tools default to none, `parts`, `sheet_path` and `operations`
  asked for by the tool and no longer by the schema, because the file may hold them, and
  because a default value given inline (`unit` mil, `save` false) is otherwise not told from
  one not given and would lose to the file's unnoticed;
- a name the tool does not have, in the file, is refused, because a misspelled `wires` would
  build a sheet without wires and report success;
- a relative path is refused, because it would be read from the server's folder.

Tests first. Offline, `tests/test_spec_args.py`, called through the server as a client
calls it, all failing on the code before (40 failures in 10 tests): "'spec_file' not found
in ['parts', 'wires', ...]", "1 validation error for build_schematicArguments parts Field
required", and with `parts` inline beside a file "True is not false": the unknown argument
was dropped and success reported. Live, `tests/test_live_spec_file.py`, 1 failed with the
same "parts Field required".

After, 2026-11-23: offline 10/10, and the list with the new module 577, OK. Live in AD25,
`test_live_spec_file` 1/1: a build from a file into a project (two parts, a parameter that
is not ASCII, two wires, a junction, a label, a power port, a note) read back from the
saved .SchDoc, then an edit from a file in mm read back the same way, and one with `unit`
in both places refused, the sheet's bytes unchanged. The callers' live tests:
`test_live_pin_map` 2/2, `test_live_libraries` 5/5, `test_live_project_setup` 9/9,
`test_live_compile_refresh` 7 (2 of them expected failures), `test_live_erc` 3/3, and the
one test of `test_live_symbol_footprint` that builds a sheet. The other live tests not run.

Seen and left: on every tool the server drops an inline argument it does not know, without
a word (the mcp package's argument model; how the test before got its false success).

Built in build `0.7.0-20261123-103915` (tag `build-20261123-103915`), commit `cc27c73`.

Held 2026-11-23: the scenario test of build 0.7.0-20261123-103915 (findings 2026-11-23, the group 2 entry, point 2): `build_schematic` built a sheet from a spec file and `edit_schematic` edited one from a file in mm, each read back from the saved file; a relative path, a name the tool does not have and an argument given twice refused before Altium.

### A45 - `build_schematic` places only part A of a multi-part symbol - CLOSED 2026-11-23

Sorted out of the entry of 2026-11-18 (second), point 1, build `0.7.0-20261115-172812`. A
symbol of six parts was placed with part A only; `pin_map` listed the pins of all six parts,
all at part A's origin, and `success` was true. Nothing said the other parts were not
placed, and `edit_schematic`'s `place_component` takes no `part` either. Workaround: the
symbol made single-part. Reported success with a wrong result.

Proposed: local; every part placed (or the parts asked, a `part` key on both tools), and
`pin_map` per placed part; a live test with a multi-part symbol. Not decided.

Decided 2026-11-22 in the plan, not the owner: a `part` key (letter or number) in a part
entry of both tools, part A when there is none, the parts not placed under `warnings`, and
`pin_map` with the placed parts' pins only; a key inside an existing list, not an argument.

Cause: both tools replicated the symbol and never set its current part, so the part placed
was the one the library was saved showing: A mostly, but part C for a symbol last shown at
C (one of the SpiritLevel-SL1 example's symbols is saved so). The pin map took every pin
the component's iterator gives, which is every part's. Nothing read the part count.

Fixed in the commit that moves it here: `part` in `build_schematic`'s parts and in
`place_component`, set on each placed part, from a `.SchLib` and from an `.IntLib`; the pin
map and `pins` count what each placed part shows (its part's pins and those of all parts,
in its display mode); `warnings` has a line per component with parts not on the sheet
(`U1 (<symbol>): parts B, C not placed on this sheet`), absent when there is none. The
descriptions and the README say so (the tool listing 158,565 to 158,879 characters, 80
tools, no new argument).

Decided 2026-11-23 by the run, not the owner:
- `place_component` gets the key as `build_schematic` does, with nothing left for the token
  rule, because it is an operation inside `edit_schematic`'s `operations` list: its values
  are keys there, not arguments of the tool;
- the other operations' `part` takes a letter too, because one key with two forms in one
  tool would need explaining, and they read it in the same line of code;
- a part the symbol does not have is not placed and is reported as a missing part or a
  failed operation, because placing another in its place would be a wrong result again; from
  an `.IntLib` it is placed and taken off again, as the count is known only then;
- `warnings` goes by what the sheet holds after the call and says "on this sheet", given a
  `part` or not, because a part may sit on another sheet, which the tools do not read, and
  a part placed by an earlier edit is placed.

Tests first. Live, `tests/test_live_multipart.py`, a six-part symbol with a pin all parts
share, made in a copy of the example's library and compiled into an `.IntLib`, 7 of 7
failed: "silent on parts B, C, D, E, F of U1, which are not placed" (success, 13 pins for
part A's 3), "not the parts asked" (six entries, six times part A), a symbol shown at part
C placed as part 3, and a part G placed with success. Offline, `test_sch_edit` and
`test_pin_map`, 3 failed ("place_component does not take part", no part in the bridge's
line).

After, 2026-11-23, live in AD25: `test_live_multipart` 8/8 (an undo test added; places,
parts and pins read from the saved file; six entries compile to one component),
`test_live_pin_map` 2/2, `test_live_spec_file` 1/1, `test_live_libraries` 5/5,
`test_live_project_setup` 9/9, `test_live_compile_refresh` 7 (two expected failures,
A48 (b)), `test_live_erc`'s test that edits a sheet 1/1, `test_live_symbol_footprint`'s
test that builds one 1/1. A one-off build of all 39 symbols of the example's library: the
map's 467 pins equal to the saved file's, each symbol at part A. The offline list 579, OK.
The other live tests not run.

Seen and left, by reading the code, not tested: the same part given twice under one
designator is placed twice, unreported; text placement by `param_placement.txt` measures
the body over all of a symbol's parts; a warning of a failed build is inside its error text,
as the rest of that result is.

Built in build `0.7.0-20261123-103915` (tag `build-20261123-103915`), commit `007672a`.

Held 2026-11-23: the scenario test of build 0.7.0-20261123-103915 (findings 2026-11-23, the group 2 entry, point 3): a symbol saved showing part C placed as part A with no `part`, `warnings` naming parts B and C; `part="B"` in the build and `part="C"` in `place_component` placed those parts only; `part="G"` refused in both tools.

### A26 - `build_schematic` leaves the focused project modified, and puts its sheet in it - CLOSED 2026-11-23

With another project in focus, `build_schematic(project_path, sheet_path)` took its sheet
back from that project (`project.detached_from` names it) but left that project's file flag
set: unmodified before, modified after, twice in a row (its file not written).
`add_project_document(create=True)` in the same state puts the flag back. In the same result
the top-level `detached_from` is `""` while the nested one names the project, and `sheet`
gives the unsaved name (`Sheet1.SchDoc`) where `sheet_path` gives the file saved.
(2026-11-14, fifth entry, 3 and 6.)
Met again 2026-11-15 (second entry, 8; third entry, 3), widened: without `project_path` the
new sheet went into the focused project and set its flag, `success` true, `detached_from`
`""`; with `project_path` and a part missing, the unsaved sheet stayed in the focused project
with its flag set, not mentioned. Met again 2026-11-18 (second entry, point 3; A52),
2026-11-19 (second entry, point 4, in kind; fourteenth entry, point 1) and 2026-11-23 (point
7, build `0.7.0-20261123-001227`): a `Sheet1.SchDoc` with no path in the focused project,
left modified.

Decided (the run's plan): the focused project's modified flag left as found; without
`project_path` the sheet stays a free document; after a failure the unsaved sheet is taken
out again; one `detached_from`, and `sheet` the saved name.
Decided 2026-11-23 by the run, not the owner:
- after a failure the sheet is taken out of the project and stays open as a free document,
  named in the error, not closed, because a close leaves its entry in the list and the
  partial sheet is what shows what was placed;
- `detached_from` is the project's full path, because that is what `add_project_document`
  gives and two projects can share a file name;
- the live test's check that Free Documents is unchanged leaves out the test's own library,
  because the build opens it as a free document of its own and it is not the sheet the
  check is for.

Cause, from a probe in AD25: `DM_CreateNewDocument('SCH')` puts the sheet into the focused
project and sets its flag, and from then on `DM_FocusedProject` is Free Documents.
`build_schematic` read the focused project only after that, so it found nothing to take out
(`detached_from` `""`); with `project_path` the add took the sheet out later, when the flag
was already set, and so left it set. Closing a sheet never saved takes it out of neither
list, a project's or Free Documents'.

Fixed in the commit that moves it here: the focused project and its flag read before the
sheet is made, the sheet taken out and the flag put back in the same script; one
`detached_from`, at the top (the build's, else the add's); `sheet` the path saved; a build
with parts missing says in its error that the sheet is open as an unsaved free document.
`build_schematic`'s description and the README say so. No new argument.

Test first, `tests/test_live_build_focus.py` (4 tests, live in AD25, on temporary projects
and a copy of an example library): before, on the code without the fix, 4 failures of 4,
each `AssertionError: Tuples differ: (True, [...other.schdoc, 'sheet1.schdoc']) != (False,
[...other.schdoc]) : the focused project is not as it was found (modified, its documents)`
(the one into a project: the sheet gone, the flag still set). Offline, `test_project_setup`'s
`test_build_schematic_names_the_saved_sheet_and_one_detached_from` failed before:
"'Sheet1.SchDoc' != ... sheet is not the name the sheet was saved as".
After: `test_live_build_focus` 4/4; the live tests that build (`test_live_project_setup`,
`test_live_multipart`, `test_live_pin_map`, `test_live_spec_file`, `test_live_libraries`,
`test_live_symbol_footprint`) 34/34, none skipped; the offline list 585/585, none skipped.
The tool listing 80 tools, 159,149 to 159,305 characters (+0.1%). The clean-up met no
dialog: sheets closed before their projects, no project opened twice.

Built in build `0.7.0-20261123-103915` (tag `build-20261123-103915`), commit `153c546`.

Held 2026-11-23: the scenario test of build 0.7.0-20261123-103915 (findings 2026-11-23, the group 2 entry, point 5): with another project focused, four builds (into a new project twice, with no `project_path`, with a missing part) each left its flag, its documents and its files' md5 as they were; `detached_from` the full path, `sheet` the path saved.

### A27 - `build_schematic` with `footprint` on a symbol that has a current one gives two - CLOSED 2026-11-23

A part whose library symbol already has a current footprint, placed with `footprint`, gets
the named model added (by name, no library) as current while the library's current one keeps
its mark: two current PCB footprints (`IsCurrent` 1 on both through the API, `ISCURRENT=T`
twice in the saved sheet). Rare before A16, now the common case. Reported success. Local:
the footprint given becomes the only current one, its mark moved when the symbol already has
a model of that name. (2026-11-14, fifth entry, 5.)

Cause: the build's FOOTPRINT record (`schematic_utils.pas`) always added a new
implementation with `IsCurrent` true and never looked at the models the placed part came
with from its library symbol, so the library's current footprint kept its mark; a name the
symbol already held was added a second time.

Fixed in the commit that moves it here: `SetPlacedFootprint` in `schematic_utils.pas`,
called by the build for each FOOTPRINT record, makes the symbol's own model of that name
(any case) current, or adds it (by name, no library) when there is none, and takes the mark
from every other footprint of the part; 3D and simulation models are left alone. The
`footprint` line of `build_schematic`'s description says so. `place_component` takes no
footprint and is not affected.

Decided 2026-11-23 by the run, not the owner: a name the symbol already has is made current,
not added again, because a second model of one name would be a duplicate; the fix stays in
the build, not in `ApplyFootprint`, because that one links a library file and would clear an
existing model's link; the description gets one sentence (124 characters), because the
behaviour is part of the argument's contract.

Test before: `tests/test_live_build_footprint.py`, 3 of 5 failed: "Lists differ: [('HDR1X2',
True), ('NT', True)] != [('HDR1X2', False), ('NT', True)] : the part has two current
footprints, or the wrong one"; the saved sheet gave `['HDR1X2', 'NT'] != ['NT']`; asking for
a model the symbol had gave a second one, "[('HDR1X2', False), ('NT', True), ('hdr1x2',
True)] ... a second model was added, or both are current". After:
`test_live_build_footprint` 5/5; with `test_live_symbol_footprint` (its `read_models` now on
a `read_model_list` that shows a duplicate), `test_live_project_setup`, `test_live_pin_map`
and `test_live_build_focus` 29 OK; the offline list 585 OK. The tool listing 159,305 to
159,429 characters. Not tested live: a part from an `.IntLib`, the same code path.

Built in build `0.7.0-20261123-103915` (tag `build-20261123-103915`), commit `71f8054`.

Held 2026-11-23: the scenario test of build 0.7.0-20261123-103915 (findings 2026-11-23, the group 2 entry, point 7): a footprint given for a symbol whose library footprint is current became the only current one, the library's mark gone; a name the symbol held, given in another case, made current, not added again.

### A71 - Parts placed by the tools sometimes lack the flag that locks their body - CLOSED 2026-11-23

2026-11-19 (eleventh), point 1: a click on a placed part's body selected its rectangle. In
the saved sheet a placed part's child primitives carry `IsNotAccesible=T`; on 24 parts
placed by script or by the server's tools the body did not, while parts placed in Altium's
own UI all had it. Not reproduced that day. 2026-11-20, points 1 and 6: reproduced; of six
parts placed by `edit_schematic` `place_component` that day three came in without it (an
8-pin symbol's rectangle and line, a 2-pin symbol's four arcs), and 19 more were found on
sheets drawn earlier by `build_schematic` and `edit_schematic`. Reported success. Not
readable from DelphiScript ("Undeclared identifier: IsNotAccesible"); found only in the
saved file. Workaround held: `Comp.PinsMoveable := True`, then `False`, inside
`PreProcess`/`PostProcess` and `SCHM_BeginModify`/`EndModify`, saved.

Proposed: local; the toggle after placing in `place_component` and `build_schematic`, and
`check_schematic` reporting a part with a child lacking the flag; a live test with the
symbols that lost it. Decided by the run's plan: the toggle; the `check_schematic` part not
in this run, left for an item of its own at the run's end.

Cause (2026-11-23, backlog run): a part lacks the flag exactly when its symbol is the one
shown in the library editor while it is placed. Altium then hands that symbol's body to the
library document, `Replicate` leaves it out, and `ReplicateLibSymbol`'s second pass (issue
#22) adds copies of the graphics without the flag. A symbol not shown is copied whole and
keeps the flag. Which symbol the editor showed is what made the fault look intermittent.
Pins, designators and parameters do not carry the flag, even on parts placed in Altium's UI.

Fixed in the commit that moves it here: `LockPartBody` in `schematic_utils.pas`. Once a part
copied from a `.SchLib` is on the sheet, inside the modify, it flips `PinsMoveable` to the
opposite value and sets it back to the symbol's own; Altium then sets the flag on every body
graphic. It runs in `build_schematic` and in `edit_schematic`'s `place_component`. `.IntLib`
parts, placed by Altium's `PlaceLibraryComponent`, are left as they were. The tool listing
unchanged (159,429 characters).

Decided 2026-11-23 by the run, not the owner: the value set back rather than forced to
False, because a symbol saved with movable pins keeps that setting (only the False case,
every placed part, tested); the `.IntLib` path not touched, because the fault is in the copy
path (the `.IntLib` path untested); each symbol placed five times while shown and five while
not, because the item named no cause and the split shows which condition fails.

Test: `tests/test_live_body_lock.py` makes an 8-pin symbol drawn with a rectangle and a line
and a 2-pin one drawn with four arcs in a copy of an example library; each tool places each
symbol ten times, five while it is the shown symbol, and the test reads `IsNotAccesible` on
every body graphic from the saved sheet. Before: "10 of 20 placed parts have a body graphic
without IsNotAccesible=T" for each tool, the 10 every placement made while its own symbol
was shown. After: 0 of 40, 2/2. The live tests of the tools touched 46 OK (2 expected
failures, already marked); the offline list 585 OK.

Built in build `0.7.0-20261123-103915` (tag `build-20261123-103915`), commit `9ae6937`.

Held 2026-11-23: the scenario test of build 0.7.0-20261123-103915 (findings 2026-11-23, the group 2 entry, point 8): a symbol shown in the library editor while placed, by `build_schematic` and by `place_component`, had `IsNotAccesible=T` on every body graphic of both parts in the saved file.

### A56 - No tool sets a placed part's footprint or says which library it links to - CLOSED 2026-11-23

A footprint given to a library symbol (A16, closed, the library side) does not reach the
parts already placed from it, and no tool sets or changes a placed part's footprint. Done by
`run_altium_script` (`AddSchImplementation`, `ModelType 'PCBLIB'`, `AddDataFileLink`,
`IsCurrent`, inside `SCHM_BeginModify`/`EndModify`, then `SaveDoc`; to repoint,
`RemoveSchImplementation` and a new implementation, no setter for a link's location found)
in five sessions: 2026-11-19 (first), point 6; (third), point 3, the compile then stale (A48
(b)); (fifth), point 5, 11 parts; (seventh), points 1 and 5; (eighth), point 3. Also missing
(2026-11-19 (seventh), point 2): which library each placed part's footprint links to. A
script showed parts linked to a file that does not hold their footprint (an older copy of a
vendor library at another path), which neither `get_project_components` (the footprint's
name only) nor a compile reports.

Proposed: local; an `edit_schematic` op setting a placed part's footprint (name and
library), or one updating placed parts from their library symbol; a `footprint_library`
field in `get_project_components`, flagged when the linked file lacks the footprint. Not
decided.

Decided 2026-11-22 by the owner (the opening answer of `## Run 2026-11-22`): (a) taken, an
`edit_schematic` op setting a placed part's footprint. (b), which library a part links to: a
recipe in `docs/recipes.md` if a session's script is in the record, no field in
`get_project_components` (the plan, not the owner).

(b) written 2026-11-23 in `docs/recipes.md`: `test_live_symbol_footprint`'s `read_models`,
the script that test ran on a placed part, one designator per call, read from
`ExportToParameters` (`ISCURRENT`, `MODELDATAFILE0`). Not covered: every part in one call,
and whether the linked file holds the footprint. Its "Proved by" line now says that
`MODELDATAFILE0` on a placed part is asserted by `test_live_set_footprint` (the same script,
`read_model_list`).

(a) fixed in the commit that moves it here: an `edit_schematic` op `set_footprint`
(`designator`, `footprint`, `library`), one more entry in its operations list, no new tool
or argument. Every part of that designator on the sheet gets the footprint as its only
current one, linked to the `.PcbLib` given: `SetPartFootprint` in `schematic_utils.pas`
calls the library side's `ApplyFootprint` (A16's `FOOTPRINT` record, current `1`) inside the
part's `SCHM_BeginModify`/`EndModify`. A footprint of that name the part has already is
linked anew (`ClearAllDatafileLinks`, `AddDataFileLink`), not added twice; the other
footprints lose their current mark and stay; 3D and simulation models are left alone (A27's
rule). After the edit each part is read back: one current footprint, the one asked, linked
to that library, or the op fails saying how many are current. Before Altium is called,
`sch_edit` refuses a library that is not a `.PcbLib`, does not exist, cannot be read, or
whose saved file does not hold the footprint (`pcblib_file.holds_footprint`, by the
`PATTERN` name). `pcblib_file` now reads an empty stream as no bytes, where it used to
raise. The README's `edit_schematic` entry names the op.

Decided 2026-11-23 by the run, not the owner:
- the footprint replaced stays on the part as a non-current alternative, not removed with `RemoveSchImplementation` as the sessions' scripts did, because `ApplyFootprint` (A16, A27) does it so: one current footprint, nothing the part held lost, and reuse the smaller change;
- the library required and checked to hold the footprint in its saved file (a footprint not saved yet refused until its library is saved), because the item's own failure was parts linked to a file that does not hold their footprint;
- no `part` key: every part of the designator gets the footprint, because a footprint belongs to the component, not to one of its parts (a multi-part component not tested live);
- the offline tests in the modules already in `tests.yml` (`test_sch_edit`, `test_pcblib_file`), because the op is encoded in `sch_edit` and the check is in `pcblib_file`.

Tests before, on the code without the fix: `test_live_set_footprint` 3 of 3 failed, its
setUp reading the part's own HDR1X2 as the only current footprint and every call returning
`"operation 1: 'op' must be one of move_component, ..., place_component"`; offline
`test_sch_edit.SetFootprintTest` 2 of 2 failed with the same message, and
`test_pcblib_file.test_holds_footprint` with `AttributeError: module 'pcblib_file' has no
attribute 'holds_footprint'`. After: `test_live_set_footprint` 3/3 (through Altium and from
the saved sheet's `MODELDATAFILE0`, `ISCURRENT`: the footprint given the only current one,
linked to the library given; one the part has linked anew, not added; the other models
unchanged); the live tests of the tools touched (set_footprint, build_footprint,
symbol_footprint, body_lock, compile_refresh, erc, libraries, multipart, spec_file) 43 OK, 2
expected failures already marked; offline 588/588. The tool listing 159,429 to 159,660
characters (+0.14%).

Built in build `0.7.0-20261123-103915` (tag `build-20261123-103915`), commit `8f57314`.

Held 2026-11-23: the scenario test of build 0.7.0-20261123-103915 (findings 2026-11-23, the group 2 entry, points 9 and 10): (a) `set_footprint` made the footprint given the only current one, linked to the `.PcbLib` given, the part's other three kept not current, one it had linked anew, a wrong library or footprint refused before Altium (point 9); (b), its recipe, held with the recipes file (point 10).

### A75 - `run_altium_script`'s `List1..3` keep strings, not objects - CLOSED 2026-11-23

Sorted out of the entry of 2026-11-23, point 6, the scenario test of build `0.7.0-20261123-001227`: an
object stored by `List1.AddObject` and read back as `List1.Objects[j]` is not the
interface. `Doc.RemoveSchObject(List1.Objects[j])` ran with no error and removed nothing
(the script reported 23 removed per sheet, and the sheets were saved with all 23), and
`List1.Objects[j].I_ObjectAddress` failed "Undeclared identifier: I_ObjectAddress", the
sandbox's diagnosis reading it as a call on nil. Iterating again for the first object each
time worked. Reported success with nothing done.

Local: a line in `run_altium_script`'s description beside the recipes: `List1..3` keep
strings, not objects; a loop that removes objects takes the first one again each time.

Decided 2026-11-23 by the run, not the owner: taken into group 3, a step before its tests,
by the run's rule for a new point small and in the group's files (*The scenario test of a
group*, 7), because `run_altium_script`'s description and the recipes are group 3's.

Cause: the sandbox's `List1..3` are `TStringList`s, and in Altium's DelphiScript an
object kept by `AddObject` does not come back as the interface it was; the description
called them `TStringList` and said nothing more.

Fixed in the commit that moves it here, as usage, the sandbox unchanged: two lines of
`run_altium_script`'s description, after the recipes line: `List1..3` keep strings, not
objects; `Objects[j]` is no interface, so a removal through it does nothing; take the first
object again each time. Not run in Altium: the step was offline, Altium blocked (A26's
line in the run).

Test first, `tests/test_recipes.py`'s
`test_the_description_says_the_lists_keep_strings_not_objects` (offline), before: 1
failure of 5, `AssertionError: Regex didn't match: 'List1\.\.3 keep strings, not objects'
not found in 'Run a DelphiScript snippet ...'`. After: 5/5. The offline list: 573 of 584
run, OK; 11 not run, as they start or stop processes or look for Altium's windows
(`test_start_server`'s `InUseTest` 2, `ExchangeLockTest` 4, `test_dblib`'s
`SearchDatabaseTest` 4, `ServerStatusTest` 1). The tool listing: 80 tools, 159,000 to
159,149 characters (+0.09%), from this checkout.

Built in build `0.7.0-20261123-103915` (tag `build-20261123-103915`), commit `b764b10`.

Held 2026-11-23: the scenario test of build 0.7.0-20261123-103915 (findings 2026-11-23, the group 2 entry, point 10): `run_altium_script`'s description names the recipes file by a path that exists and says `List1..3` keep strings.

### A55 - `get_project_info` takes no `project_path` - CLOSED 2026-11-23, usage

Sorted out of the entry of 2026-11-19 (first), point 4: with no project focused it returned
`"project_path": "Free Documents"` and nothing else, unlike `get_erc_violations` and
`get_project_components`, which take a path.

Proposed: local; a `project_path` argument. Not decided.

Decided 2026-11-22 by the owner (the opening answer of `## Run 2026-11-22`): no tool; written as a recipe in `docs/recipes.md` (a DelphiScript a session proved, with its `run_altium_script` call), pointed to by one line of `run_altium_script`'s description, and closed as usage once the scenario test held for the file. A record with no proven script leaves the item Open.

Cause: `GetProjectInfo` (`other_utils.pas`) reads `DM_FocusedProject` alone.

Fixed in the commit that moves it here, as usage, the tool unchanged: `docs/recipes.md`
(new) has a script reading a project by path, focused or not, and `run_altium_script`'s
description names the file by its absolute path, computed from `main.py`'s folder at
import. The script is `project_state` of `test_live_pcblib_from_board`, run in that test's
pass of 2026-11-15 (A8); the same read by path with another project focused ran in
`test_live_project_setup`. It gives the project file's unsaved flag and the documents, not
the parameters, the variants or each document's state. Not run in Altium today: the step
was offline.

Decided 2026-11-23 by the run, not the owner, for the whole recipes file:
- a proved script is one whose text exists and was run: here, a live test's script in this
  repo that passed in Altium, kept word for word but its placeholders. The items' records
  and their `findings.md` entries hold calls and no script text, and no session's transcript
  was read for one, because the plan names those two as the source;
- no script composed from a record's calls is in the file, labelled or not: those items
  stay Open with what is missing, because the owner's decision says so and a script in that
  file would be run as proved;
- where the proved way was a tool call or a file step, the section says *No script* and
  the item stays Open (A34 (f), A51, A67 (a) and (b), A69 (d)), because the decision asks
  for a script;
- A55 moves here though its script returns less than the tool would, because what was met
  (a project not in focus not readable at all) is covered, and the recipe says what it
  leaves out;
- README's manual packaging command takes `docs` too, because the description's path
  would name no file in a package made with it.

Test first, `tests/test_recipes.py` (new, offline, in the workflow's list), before: 1
failure and 3 errors of 4: `AssertionError: unexpectedly None : run_altium_script's
description names no recipes file`; `FileNotFoundError` on `docs/recipes.md`. After: 4/4,
also from a copy laid out as a release in a folder with a space in its name: the path
exists, each script passes the sandbox's checks and equals the one its live test sends, a
removal has its notice. The offline list: 574 of 583 run, OK; 9 not run, as they start or
stop processes or look for Altium's windows, which this step did not do (`InUseTest` 2,
`ExchangeLockTest` 2, `test_dblib`'s database tests 4, `ServerStatusTest` 1). The tool
listing: 80 tools, 158,879 to 159,000 characters (0.08%) from this checkout; a release's
longer path adds to it.

Met by the first two runs of that list today, before they were isolated: `test_build_info`'s
`ServerStatusTest` calls the real `get_server_status`, so an offline run looks for Altium's
windows and may write and prune the resident's folder. The window call was refused by the
run's guard and that folder's time was unchanged; `test_symbol_footprint` made and removed
a temporary file in the exchange folder, and the server's log grew. The runs after used a
scratch exchange and data folder, the real ones unchanged.

For the scenario test, the three to run: this script (A55, its proof), the step of A34 (f)
(met in five entries) and A52's removal (two entries, and A48 b's notice). Next, when there
is room: A56 (b), whose library field on a placed part no test asserted.

Built in build `0.7.0-20261123-103915` (tag `build-20261123-103915`), commit `ba17162`.

Held 2026-11-23: the scenario test of build 0.7.0-20261123-103915 (findings 2026-11-23, the group 2 entry, point 10): the description's line read, the recipes file opened and three recipes run as written, A55's on a project not focused giving its flag and three documents as the build had them, A34 (f)'s and A52's as well.

### A57 - Library reads return too much, or one symbol per call - CLOSED 2026-11-23

2026-11-18 (first), point 1: `get_symbol_primitives` in inventory mode on a 418-symbol
`.SchLib` returned 91k characters, over the result limit, where name and description were
all that was needed. 2026-11-19 (seventh), its closing line: `get_footprint_primitives`
without a name on a whole footprint library overflowed at about 60 KB. 2026-11-18 (first),
point 2: a layout needs several symbols' pins (designator, name, location, orientation,
length), one call per symbol with all its graphics; one `run_altium_script` did 27 symbols.
2026-11-19 (first), point 6: a footprint's pad names only through the full dump.

Proposed: local; a `name` or `term` filter and a names-and-descriptions inventory on both
tools, a list of symbol names with a pins-only mode, and a pads-only mode for footprints.
Not decided.

Met again 2026-11-22 (findings 2026-11-22, point 1), build `0.7.0-20261115-172812`, measured
from seventeen sessions' transcripts: `get_symbol_primitives` and `get_footprint_primitives`
20k to 44k characters of results in a session each. The same point names
`get_project_components`, 63k in one session (7 calls), filed here as the entry did: it is a
project read, not a library one, and no item yet covers its size.

Cause: the inventory mode of both tools gave every primitive type's count on each entry
(and `part_count` on a symbol's), and the server printed the result indented, a line per
key: the keys and indentation of some hundreds of entries outweighed their names and
descriptions. A name was compared whole, so one call read one symbol or footprint, or all
of them with `"*"`.

Fixed: the inventory gives each symbol's `name`, `description` and `pins`, each
footprint's `name`, `description` and `pads` (the scripts count only pins or pads), and the
server prints it one entry a line, compact (`library_inventory_json` in `server/main.py`);
a dump is printed as before. The name argument takes several names, comma-separated
(`SplitNameList`, `LibNameWanted`, `NotFoundJSON` in `other_utils.pas`): each one found is
dumped into `symbols` (or `footprints`), as `"*"` does, with `symbol_count` (or
`footprint_count`) and `not_found` for those missing; none found is the error one name
gives. One name is as before. No new argument; the tool listing 159,660 to 159,602
characters.
Decided 2026-11-23 by the run, not the owner: a string with a comma that is itself a name
in the library is read as that one name, split only when no symbol or footprint is named
so, because Altium's own example library holds `Jumper, 2-Pin`, and splitting it would
report two names missing where the library has the symbol.
Decided 2026-11-23 by the run, not the owner: several names give a list as `"*"` does,
with `not_found`, and an error only when none is found, because a call for several should
still give the ones it found, and say which it did not.
Decided 2026-11-23 by the run, not the owner: the inventory printed compact, one entry a
line, because the indentation and the spaces of a few hundred entries were a large part of
the result and the plan left the form open; the dumps are printed as before, being out of
the item's decision.
Test before (`tests/test_live_library_reads.py`, a copy of an example `.SchLib` with 450
symbols added, 489 in all, and a copy of an example `.PcbLib` with 300 footprints added, 333
in all): 4 failed, 1 error of 6: "93587 not less than 60000 : the inventory of 489 symbols
is 93587 characters"; the footprint inventory gave `tracks` beside `pads`; "Symbol not
found in library: INV_001, inv_002,INV_007" and "Footprint not found in library:
INVFP_004,invfp_005, NONE_SUCH"; the call with a missing name gave no `symbols`.
Test after: 7/7 live (a name with a comma read whole added), the symbol inventory 53,793
characters for 489 symbols, the footprint inventory 36,270 for 333 footprints; the live
tests of the tools touched, `test_live_symbol_footprint` and `test_live_pcblib_from_board`,
13/13 together; offline 8 new (`tests/test_library_reads.py`, added to `tests.yml`),
596/596 offline in all. `get_project_components`' size (the line of 2026-11-22) is not in
this fix: it is left for an item of its own, filed with the run's other leftovers at its
end.
Fixed in the commit that moves it here.

Built in build `0.7.0-20261123-140004` (tag `build-20261123-140004`), commit `c7aac0a`.

Held 2026-11-23: the scenario test of build 0.7.0-20261123-140004 (findings 2026-11-23, the group 3 entry, point 1): inventory mode gave `name`, `description` and `pins` (or `pads`) per entry, one a line, 39 symbols in 2.9k characters and 12 footprints in 1.2k; several comma-separated names, in any case and with spaces after the comma, dumped each with its count and `not_found` for the missing one, and a symbol whose own name holds a comma was dumped whole. The libraries were small, so the size of an inventory of hundreds stays the fork's live test's measure.

### A66 - `create_schematic_symbol` reports a footprint linked by name that no library of the project holds - CLOSED 2026-11-23

Sorted out of the entry of 2026-11-20, point 5: `footprints: ["<name>"]` reported the
footprint linked, `problems` empty, but the parts placed from the symbol had no footprint in
Altium: it was in an installed vendor `.PcbLib`, not in the project's libraries, and the link
held no location. Found by the owner. Fixed by setting `DatafileLink(0).Location` on the
symbol and the placed parts by script. Reported success with a wrong result (the caller
should also have given the library).

Proposed: local; a name-only footprint resolved at creation: the location filled from the
library that holds it, else a line in `problems`. Not decided.

Cause: a footprint given by name only went to Altium with an empty library, and the
script stored the link as it was asked (`ApplyFootprint`, `AddDataFileLink(Model, '',
'PCBLib')`) and read back the same empty library, so the read-back matched the request and
`problems` stayed empty; nothing looked for the library that holds the name. The same holds
for a `FOOTPRINT|<name>` record of `create_symbols_batch`, which goes through the same code.

Fixed: before Altium is asked to make the symbol, a name with no library is looked up in
the saved `.PcbLib` files of the projects that hold the symbol library (the focused one for
`create_schematic_symbol`, the spec's `LIBRARY|` for `create_symbols_batch`), then of the
installed libraries in Altium's order, and the first that holds it is written into the
record; none does, the link is by name as before and `problems` gets a line naming the
symbol and the footprint ("... is in no saved .PcbLib of the project or installed in
Altium; linked by name only (give its library)"). The bridge command behind
`get_installed_libraries` also gives `project_libraries` for a `library_path`
(`GetInstalledLibraries` in `other_utils.pas`; the tool's own result is as before); the
lookup is `search_order`, `fill_records` and `fill_spec` in `server/symbol_footprint.py`, a
file read by `held_footprints` in `server/pcblib_file.py`. One more call to Altium only when
a name has no library. No new tool or argument; the two `footprints` descriptions say where
a name is looked for; the tool listing 159,606 to 159,605 characters.
Decided 2026-11-23 by the run, not the owner: only saved `.PcbLib` files are looked in, an
installed `.IntLib` not, because a footprint's library is a `.PcbLib` path (the tool refuses
any other) and the file on disk is what the link points Altium to; a footprint made in an
open library and not saved yet is reported, not guessed.
Decided 2026-11-23 by the run, not the owner: `create_symbols_batch`'s `FOOTPRINT` records
are fixed with it, because they share the code and its live test asserted the same fault
(a name-only link, `problems` empty).
Decided 2026-11-23 by the run, not the owner: "the project" is every open project whose
documents include the symbol library, `Free Documents` among them, in workspace order,
because a library can be in several projects and a free one has no other.
Test before (`tests/test_live_symbol_footprint.py`, copies of an example's `.SchLib` and
`.PcbLib`, the `.PcbLib` installed for the test and the installed list put back as found):
3 failed of 3: a name held only by the installed copy, "Lists differ: [('HDR1X2', '',
True)] != [('HDR1X2', '<the installed copy>', True)]"; a name held by the project's
`.PcbLib` (and a second copy installed), "{'HDR1X2': ('', True), 'NT': ('', False)} !=
..."; a name no library holds, "0 != 1" problems.
Test after: 11/11 of `tests/test_live_symbol_footprint.py` live (the three above among them;
the test of a name-only link now asserts its problem line), and with the live tests of the
tools touched (`test_live_libraries`, `test_live_build_footprint`, `test_live_body_lock`,
`test_live_library_reads`, `test_live_multipart`, `test_live_pin_map`) 40/40; offline 7 new
(`tests/test_symbol_footprint.py`, `tests/test_pcblib_file.py`), 603/603 in all.
Fixed in the commit that moves it here.

Built in build `0.7.0-20261123-140004` (tag `build-20261123-140004`), commit `3ab04ad`.

Held 2026-11-23: the scenario test of build 0.7.0-20261123-140004 (findings 2026-11-23, the group 3 entry, point 3): a `FOOTPRINT|<name>` of `create_symbols_batch` with no library was linked to the saved `.PcbLib` of the symbol library's project that holds it, current, `problems` []; `create_schematic_symbol` linked a name that `.PcbLib` holds (given in lower case) to it, and a name held only by an installed `.IntLib` and one held nowhere by name, each with its line in `problems`; the saved library the same. The name stored as typed, not in the library's case, is A79.

### A41 - `make_pcblib_from_board` loses the footprints' descriptions - CLOSED 2026-11-23

Six of the twelve
components of a 2-layer board carry a footprint description
(`IPCB_Component.FootprintDescription`), and the library Altium's menu makes from that board
keeps them; in every library the tool made, read back with `get_footprint_primitives`, every
description is empty, and `problems` stays [] because the comparison checks patterns and pads
only. Reported success with less than the board has. Local: find where they are lost (the
hidden run, the filter or the save), give each footprint the board's description before the
save, and compare descriptions too; a live test that fails today. (2026-11-15, third entry,
5.) For the next run.

Cause, found by a probe: Altium's own `PCB:BuildPCBLibrary`, run hidden as the bridge runs
it, makes every footprint with an empty description; read in memory straight after the run,
before the filter and the save, all twelve footprints of a board whose components carry
eleven descriptions had none. The save and the filter lose nothing; the comparison checked
patterns and pads only, so nothing saw it.

Fixed: the bridge (`MakePcbLibFromBoard` in `other_utils.pas`) reads each component's
`FootprintDescription` with its pattern, and gives each footprint it keeps, Altium's
`_<n>` variants too, its pattern's description before the save, where Altium left it
empty (`FootprintPatternIndex`, shared with the filter's `FootprintWanted`). It returns the
board's descriptions per pattern and the saved file's per footprint, and
`server/board_library.py` puts a line in `problems` for a footprint whose description read
back is not one its pattern's components carry (success false). No new tool or argument;
the result is as before but for that line; the tool's description names the check, the
tool listing 159,605 to 159,622 characters.
Decided 2026-11-23 by the run, not the owner: the description given is the first one met on
the board for the pattern, to every footprint of it, and the check accepts any its
components carry, because Altium's library records no component a `_<n>` variant comes
from, and the components of one pattern carry one description on the boards seen.
Decided 2026-11-23 by the run, not the owner: the descriptions are not added to each
footprint of the result, only a problem line when one differs, because the token rule
asks that a result not grow.
Test before (`tests/test_live_pcblib_from_board.py`, `LivePcbLibDescriptionsTest`, a copy
of an Altium example board whose components carry footprint descriptions, read back with
`get_footprint_primitives`): failed, "AssertionError: {'STM-LQFP64_L': ('', ['Thin QFP,
64-Leads[1039 chars]n'])} != {} : footprints whose description is not the board's", every
footprint of the twelve empty.
Test after: 5/5 of `tests/test_live_pcblib_from_board.py` live (the one above among them);
offline 1 new (`tests/test_board_library.py`), 604/604 in all.
Fixed in the commit that moves it here.

Built in build `0.7.0-20261123-140004` (tag `build-20261123-140004`), commit `e4a6669`.

Held 2026-11-23: the scenario test of build 0.7.0-20261123-140004 (findings 2026-11-23, the group 3 entry, point 2): a library made from a 2-layer board of 16 components (12 patterns) kept the descriptions of the six footprints whose components carry one, each equal to the one in a library made by Altium's menu from the same board, the six without empty in both; with `footprints` (three names in mixed case) the same for those three; `problems` [] both times.

### A70 - `run_altium_script`'s `OpenSchDoc` opens a `.SchLib` as a sheet - CLOSED 2026-11-23

Sorted out of the entries of 2026-11-19 (fifth), point 1, and (twelfth), point 1. Given a
`.SchLib`, the helper opens it as a schematic (kind `SCH`, `ObjectId` 32; opened as a
library it reads 33). Until it is closed every call that needs the library fails:
`SchLibIterator_Create` and `AddSchComponent` "Undeclared identifier", `create_symbols_batch`
"Could not open and focus ... - nothing was created or edited", a script's
`Client.OpenDocument('SCHLIB', ...)` returning the same sheet, one run hanging 120 s. Seven
calls to find the cause in one session; saved, the library would have been overwritten as a
sheet. Workaround: close it unsaved and open it as `SchLib`.

Proposed: local; `OpenSchDoc` opens by the file's extension or refuses a `.SchLib`, and the
batch tool's "could not open and focus" names the kind it found. Not decided.

Cause: the helper (`Sandbox.pas`) called `Client.OpenDocument('SCH', Path)` for every path, and
Altium opens the file as the kind it is told: a `.SchLib` told `SCH` is a sheet (kind SCH,
ObjectId 32) until closed. `create_symbols_batch` then found the file open (it only
focuses an open library), `SchLibIsFocused` was false (not ObjectId 33), and its error gave
no reason.

Fixed: `OpenSchDoc` opens by the file's extension, `SCHLIB` for `.SchLib` (any case), `SCH`
otherwise; when the file is already open as a sheet it returns that sheet and logs
"is open as a schematic sheet, not a library; close it unsaved and call again", in the
script's steps. `create_symbols_batch`'s "Could not open and focus <path>" gains
`OpenKindNote`: " - it is open as kind SCH (a schematic sheet, not a library; close it unsaved
and call again)", or " - it is open as kind <K>" for another kind, nothing when the file is
not open. No new tool or argument; `run_altium_script`'s description gains "(a .SchLib as a
library; ...)" in the helpers line, the tool listing 159,622 to 159,646 characters.
Decided 2026-11-23 by the run, not the owner: a `.SchLib` already open as a sheet is
returned as that sheet with a logged line, not closed or reopened by the helper, because
closing a document the caller may have changed is not the helper's call, and the log keeps
the result true.
Test before (`tests/test_live_open_schlib.py`, a copy of an Altium example library):
failed twice, "AssertionError: Tuples differ: ('32', 'SCH|32') != ('33', 'SCHLIB|33') :
OpenSchDoc did not open the .SchLib as a library (ObjectId 33, kind SCHLIB)", and the batch
tool's error "Failed batch creation: Could not open and focus <path> - nothing was created or
edited" without the kind ("'open as kind SCH (a schematic sheet' not found").
Test after: 4/4 of `tests/test_live_open_schlib.py` live (a new module: the library opened
as a library, a sheet still as a sheet, the logged line for a library open as a sheet, the
batch error naming the kind); the live tests of the tools touched, `test_live_symbol_footprint`,
`test_live_multipart`, `test_live_body_lock`, `test_live_compile_refresh`, 32 in one run with
the new ones, 31 passing; `test_live_multipart`'s `test_parts_from_an_intlib` failed once in
that run (the message was not kept, Altium had about 600 MB free) and passed alone and in two
reruns (`test_live_multipart` 8/8, the first three modules in sequence 23/23): not
reproduced, not from this change; offline 3 new (`tests/test_sandbox.py`), 607/607 in all.
Fixed in the commit that moves it here.

Built in build `0.7.0-20261123-140004` (tag `build-20261123-140004`), commit `f4ae3d3`.

Held 2026-11-23: the scenario test of build 0.7.0-20261123-140004 (findings 2026-11-23, the group 3 entry, point 4): `OpenSchDoc` on a closed `.SchLib` gave kind `SCHLIB`, unmodified; with the file open as a sheet, it returned the sheet and logged that it is open as a sheet, `create_symbols_batch` refused with nothing created or edited, and once the sheet was closed unsaved as the message says, the same batch created the symbol; the file on disk unchanged (md5).

### A28 - No tool makes an empty library - CLOSED 2026-11-23

`create_symbols_batch`'s `LIBRARY` needs an
existing `.SchLib` and `add_project_document`'s `create` makes sheets and boards only, so
a new `.SchLib` or `.PcbLib` is made by script (`CreateNewDocumentFromDocumentKind`,
`DoSafeChangeFileNameAndSave`, then `SetModified(True)` and `DoFileSave('')`), and it went
into the project in focus, as A10's probe found for a sheet. Local: `create` for `.SchLib`
and `.PcbLib` in `add_project_document`, or a library made by the symbol and footprint
tools when missing. (2026-11-14, fifth entry, 7.) For the next run.
Met again 2026-11-18 (findings 2026-11-18, second entry, point 4), build
`0.7.0-20261115-172812`: the project's `.SchLib` made by script
(`Client.OpenNewDocument('SCHLIB', ...)`, `SetFileName`, `DoFileSave`).
Met again 2026-11-19 (findings 2026-11-19, third entry, point 1), same build: a new `.PcbLib`
made by script with no project in focus joined none, and `add_project_document(create=False)`
then added it cleanly; it holds Altium's empty default footprint `PCBComponent_1` beside the
one made, and no tool deletes a footprint (A63), so a `create` should make it empty.

Decided 2026-11-22 by the owner (the opening answer of `## Run 2026-11-22`): taken, `add_project_document(create=True)` makes an empty `.SchLib` or `.PcbLib` too, no new argument.

Cause: `add_project_document`'s `create` knew two kinds only (`NEW_KINDS` in
`server/project_setup.py`, `.schdoc` and `.pcbdoc`), so a `.SchLib` or `.PcbLib` path was
refused before Altium was called. And a library Altium makes by script is not empty: a new
`.SchLib` holds `Component_1`, a new `.PcbLib` `PCBComponent_1` (probed live, one each).

Fixed: `NEW_KINDS` gains `.schlib` (`SCHLIB`) and `.pcblib` (`PCBLIB`), so `create=True` makes
either through the same path as a sheet or a board: saved at `document_path`, added to the
project named, taken out again of a project that had focus (`detached_from`), the project
file saved. In `AddProjectDocument` (`other_utils.pas`) a new library is emptied before its
first save by `LibraryItemCount` (`RemoveSchComponent` or `RemoveComponent` on each item,
then counted again); one left, the call fails, the library open unsaved and not added. No
new tool or argument; the description names the four kinds and that Altium shows a
`Component_1` in a `.SchLib` that has none when it opens it again (probed: the saved file
holds no symbol, the reopened library one, unmodified). The tool listing 159,646 to 159,770
characters.
Decided 2026-11-23 by the run, not the owner: the `.SchLib` emptied too, not only the
`.PcbLib`, because the decision asks for an empty library of either kind and the file on
disk is then empty, while the `Component_1` Altium shows on reopening is said in the
description rather than hidden, so the result stays true.
Test before (`tests/test_live_project_setup.py`, `test_create_libraries`, new): "AssertionError:
False is not true : {'success': False, 'error': '...\\Parts.SchLib must end in .schdoc or
.pcbdoc (create makes a .SchDoc or a .PcbDoc)'}", and the same for `New.SchLib` in
`test_new_document_stays_out_of_the_focused_project`, extended to the two library kinds.
Test after: `test_create_libraries` live (each library on disk, in the project as Altium
and the saved `.PrjPcb` list it, kind `SCHLIB` or `PCBLIB`, no symbol or footprint in the
saved file nor in the open library, unmodified; then one symbol by `create_symbols_batch` and
one footprint by `create_footprints_batch`, and after a save each file holds only that one;
a second `create` refused, the file unchanged); `test_live_project_setup` and
`test_live_build_focus` 14/14 live; offline 1 new (`tests/test_project_setup.py`, the kind
sent for each of the four extensions), 608/608 in all.
Fixed in the commit that moves it here.

Built in build `0.7.0-20261123-140004` (tag `build-20261123-140004`), commit `ad9e9da`.

Held 2026-11-23: the scenario test of build 0.7.0-20261123-140004 (findings 2026-11-23, the group 3 entry, point 5): with another project focused, `add_project_document(create=True)` made an empty `.SchLib` and an empty `.PcbLib` in the project named, both in its saved `.PrjPcb` and read back with 0 symbols and 0 footprints, the focused project's files unchanged (md5); a second `create` refused; one footprint and one symbol added by the batch tools, saved and read again, each library held only that one (no `Component_1`, no `PCBComponent_1`).

### A77 - The parts of one component placed by `build_schematic` and by `place_component` do not compile as one - CLOSED 2026-11-23

Sorted out of the group 2 entry of 2026-11-23, point 4, the scenario test of build
`0.7.0-20261123-103915`. Part B of a multi-part symbol placed by `build_schematic` and part
C, same designator and library, by `edit_schematic` `place_component` on the same sheet:
ERC "Duplicate Component Designators" for it and "unused sub-part(s) (1) and (2)" and "(1)
and (3)", and `get_project_components` lists the designator twice. Parts B and C both
placed by `place_component` compile as one. In the saved file the build's part has
`DESIGNITEMID` set, `SOURCELIBRARYNAME` `*` and no `LIBRARYPATH`; `place_component`'s has
`LIBRARYPATH` and `SOURCELIBRARYNAME` the library's file name and no `DESIGNITEMID`: the two
tools fill a placed part's library fields differently. `edit_schematic`'s `warnings`
treated them as one component ("part A not placed on this sheet"). Reported success. The
entry filed it under A45 as failed.

Local: one way of filling the library fields in both tools.

Decided 2026-11-23 by the run, not the owner: a new item in group 3, not A45 fixed again
with group 2 checked again, because A45's own promise held (point 3) and the fault is in how
the two tools fill a part's library fields, older than A45.

Taken into `## Run 2026-11-22`, group 3 (a step of its own).

Cause: the two tools set different library fields on a part from a `.SchLib`.
`build_schematic` set only `DesignItemID` (empty when no `design_item_id` is given, saved as
the library reference), so `SOURCELIBRARYNAME` and `LIBRARYPATH` were saved as `*`.
`place_component` set `LibraryPath` and `SourceLibraryName` and never set `DesignItemID`, so
it was saved with none. Altium compiled the two parts as two components. A part from an
`.IntLib` is placed by Altium itself (`PlaceIntLibComponent`) in both tools, and was not
affected.

Fixed: one procedure, `SetPartLibrary` in `schematic_utils.pas`, used by both tools for a
part from a `.SchLib`. It sets `LibraryPath` to the library's path, `SourceLibraryName` to its
file name, and `DesignItemID` to the given one or else the library reference. No tool,
argument or description changed.
Decided 2026-11-23 by the run, not the owner: `place_component`'s fields kept, plus a Design
Item ID in both, rather than the build's `*`, because they name the library a part came from,
as Altium's own sheets do (`SOURCELIBRARYNAME` is the library's file name in the examples'
sheets), so the result stays true. A sheet built before this fix still holds `*` on its
parts, so a part added to it now by `place_component` is likely still compiled apart (not
tested); the fix reaches parts placed from this build on.

Test before (`tests/test_live_multipart.py`,
`test_parts_by_the_build_and_by_place_component_compile_as_one`, new: part B by the build,
part C by `place_component`, one designator, the project compiled): "AssertionError: Lists
differ: ['U1', 'U1'] != ['U1'] : the parts are not one component; their library fields
(part, DESIGNITEMID, SOURCELIBRARYNAME, LIBRARYPATH, LIBREFERENCE): [('2', 'MULTIPART_TEST',
'*', '*', 'MULTIPART_TEST'), ('3', None, 'Multi.SchLib', '<tmp>\Multi.SchLib',
'MULTIPART_TEST')]".
Test after, 2026-11-23, live in AD25: `test_live_multipart` 9/9 (that test included, the
saved fields of both parts equal), `test_live_pin_map` 2/2, `test_live_body_lock` 2/2,
`test_live_spec_file` 1/1, `test_live_build_focus` 4/4, `test_live_build_footprint` 5/5,
`test_live_libraries` 5/5, `test_live_set_footprint` 3/3. `test_live_symbol_footprint` and
`test_live_project_setup` did not run to the end: Claude Code stopped the run for low memory
(about 0.8 GB free), so they are left to the group's run of every `test_live_*`. Offline:
the whole list of `tests.yml`, 608/608.
Fixed in the commit that moves it here.

Built in build `0.7.0-20261123-140004` (tag `build-20261123-140004`), commit `afc0fad`.

Held 2026-11-23: the scenario test of build 0.7.0-20261123-140004 (findings 2026-11-23, the group 3 entry, point 7): part B of a multi-part symbol by `build_schematic` and part C, same designator and `.SchLib`, by `edit_schematic` `place_component` compiled as one component: one in `get_project_components`, no "Duplicate Component Designators", only "unused sub-part(s) (1)" for the part not placed; the saved file gives both parts the same `DESIGNITEMID`, `SOURCELIBRARYNAME` (the library's file name) and `LIBRARYPATH`.

### A78 - A52's recipe says its script does not mark the sheet modified, but it does - CLOSED 2026-11-23

Sorted out of the group 2 entry of 2026-11-23, point 10, the scenario test of build
`0.7.0-20261123-103915`, small: A52's section of `docs/recipes.md` says its removal script
"does not mark the sheet modified", but after it the sheet was modified (its flag set,
listed in `unsaved_in_altium`), as the notice it sends does.

Local: that sentence corrected, offline.

Taken into `## Run 2026-11-22`, group 3 (a step of its own).

Cause: the recipe's sentence was written from the script's lines, which save nothing, and
was never checked on a sheet. The script removes the object through the schematic server
(`RemoveSchObject` between `PreProcess` and `PostProcess`) and sends the registration
notice, and a removal made so is an edit of the document: the sheet is left modified.
Which of the calls sets the flag was not isolated.

Fixed: the sentence in A52's section of `docs/recipes.md`, from "It saves nothing and does
not mark the sheet modified" to "It saves nothing, but it marks the sheet modified (its
flag is set, and `unsaved_in_altium` lists it): save it, or leave it unsaved on purpose."
No script, tool or description changed. Offline: `tests.test_recipes` 5/5 and the whole list
of `tests.yml`, 608/608.
Fixed in the commit that moves it here.

Built in build `0.7.0-20261123-140004` (tag `build-20261123-140004`), commit `049670b`.

Held 2026-11-23: the scenario test of build 0.7.0-20261123-140004 (findings 2026-11-23, the group 3 entry, point 8): A52's section now says the script marks the sheet modified; run on a saved sheet with one no-ERC marker, the flag went 0 to -1, the sheet was listed in `unsaved_in_altium`, `suppressed` 1 to 0.

## Not items

## Run 2026-11-14

**The run of 2026-11-14** (planned with the owner; one long session in this repo,
subagents doing the work, and each group's scenario test run by the session itself). Every
open item is in it, in five groups; each group ends with a release, its scenario test and
the sort of that test's entry, before the next group starts. Every item below is decided;
after the one opening question nothing in it waits on the owner.

How it runs:

- **Unattended.** After reading this brief the session asks the owner **one** question, in
  one `AskUserQuestion` call, then runs to the end without stopping or asking again. That
  question holds everything the run would otherwise stop for: for all five releases, the
  push of `ad25` before each, the tag, the registration in the owner's test project and
  the release page (`CLAUDE.md`, *Release and run*, steps 1 to 5); the scenario tests run
  headless (below); the commit of each scenario test's entry without a question
  (`CLAUDE.md`, *Findings*); anything in this plan the session reads as unclear. The
  plugin questions of the session start go into that call, up to four questions; every
  later one (`clockify`'s offer, `git-workflow`'s notes, `core`'s session note) is not
  asked, as the opening sentence rules out questions for the turn ("tanpa nanya
  apa-apa"), and each is named in one line of the report.
- **A decision met mid-run is the session's own**: the option that keeps the server's
  checks honest and its results true, the smaller change when two are equal. Each is
  written into its item as "Decided 2026-11-14 by the run, not the owner: …, because …",
  and listed in the report.
- **Never stop on one item.** A fix that does not hold after a reasonable try, or a probe
  that finds no way, is left Open with what was tried written into it, its partial code
  not committed, and the run goes on. Altium hung or gone: end `X2.EXE` and start Altium
  Designer 25 again (the path is `get_server_status`'s `altium_exe`). A permission prompt
  or a dialog nobody answers is the one thing the session cannot pass: it writes where it
  stood under *Where the run stands* first.
- **One Altium, so one thing at a time**: live tests and scenario tests drive the same
  Altium, so items go one after another on `ad25` in the main tree, never in parallel,
  and a scenario test never runs beside a live test.
- **The main session stays thin**: it hands each item to **one fresh subagent**, reads its
  report and the diff, commits, and ticks the step below. It runs the scenario test and
  the sort itself.
- **The model fits the task** (the owner, 2026-11-14): Sonnet (`model: "sonnet"`) for a
  step that runs what is written and reads the result: a group's offline and live tests
  before its release, the release steps 2 to 5, and the small items A9, A20 and A16. The
  default model for a fix or a probe that needs diagnosis or design (A19, A5, A3, A10 to
  A15, A8) and for the scenario test, whose job is to catch a result reported right that
  is wrong. A Sonnet item whose test does not pass after its try goes once more to a
  fresh subagent on the default model, and the item says so. These are defaults: the
  main session moves a step up or down by its own reading of it (a small item that turns
  out to need a probe goes up; a probe already settled, leaving a pattern to follow, goes
  down), the goal being high quality at the lower cost. Each change is a line in the
  report, with why.
- **Per item**, as `dev/README.md`, `PLACEMENT_TOOL_REVIEW.md` and `CLAUDE.md` give it:
  first a live test that shows the fault on the current code
  (`server/tests/live_altium.py`'s helpers, `ALTIUM_LIVE=1`, a copy of an Altium example,
  closed unsaved); an item whose test does not fail is closed instead, the test kept if
  worth keeping. A feature's live
  test shows the tool doing what it says, read back through Altium (a board iterator, the
  saved file), and fails before the tool exists. Then the fix; that test and the live
  tests of the tools it touched; the offline unit tests (`.github/workflows/tests.yml`'s
  list, a new module added to it). A probe item is a live probe first, its result written
  into the item; the build follows when the decision covers it.
- **A subagent's brief**: its item as written below and in the item, the decision, the
  files likely touched, and these rules: read `CLAUDE.md`, `README.md`, `dev/README.md`;
  never switch branches, commit, push, tag or reset; a stash only by name and file;
  `findings.md` is not the subagent's to edit. Then `open_items.md`: the item moved to the
  end of Waiting with its cause, its fix, the test before (its message) and after (with
  counts), and "Local: on `ad25`, in the commit that moves it here; not yet in a build.
  Upstream: not yet decided."; a partly done item stays Open with what was tried; the
  `**Open: …**` line updated and `python board.py --check` clean. Report, ten lines: the
  outcome, the failing test before, the tests after with counts, every file changed, its
  "Decided … by the run" lines, a proposed commit subject and body. Nothing that names
  where a finding came from (`findings.md`'s top).
- **Commits**: one per item, its fix with its note, as `git-workflow:pr` gives a commit on
  `ad25` (no trailer). Pushed at the group's release.
- **A group's release**, as `CLAUDE.md` gives it, steps 1 to 5, on the opening answer: the
  offline tests and every `test_live_*` once, Altium restarted before them; push; copy;
  venv; register and tag; the release page. Each Waiting line of the group gets its build.
- **A group's scenario test, run by the session** (the owner, 2026-11-14: no new session
  opened by hand). It replaces, for this run, the ending that tells the owner to open one.
  A headless session in the owner's test project (its path and its procedure are in the
  owner's global `CLAUDE.md`, *The altium-mcp MCP server*): a new process, so it loads
  the release just registered, and its local registration is the one tested. Its id is
  made first and written under *Where the run stands* before it starts:

      cd "<test project>"
      claude -p "<opening sentence>" --session-id <uuid> --permission-mode auto
        --allowedTools mcp__altium-mcp --add-dir "<this clone>" --output-format json

  run in the background, one line. The opening sentence: `Uji skenario release <v>-<stamp>
  (<items>), menurut <procedure>. Tanpa nanya apa-apa. Cek singkat dulu (get_server_status,
  get_project_info, get_board_summary). Skenario baru untuk fitur baru ditulis ke prosedur
  dengan baseline-nya. Finding ke findings.md fork, baris hasil dan pemetaan di prosedur;
  jangan commit. Akhiri dengan laporan sepuluh baris: tiap item lolos atau gagal, finding
  baru.` Cut short (a limit, the laptop off): from the same folder, `claude -p --resume
  <uuid> "lanjutkan uji skenario"`, same flags. Then the session commits the entry alone,
  sorts it into the items (an item that held moves to Closed, a new point a new A-item),
  and updates the release page (step 7). A new item from a scenario test joins a later
  group only when its fix is small and in that group's files; otherwise it stays Open for
  the next run.
- **The report at the end**, in Indonesian, in the reply and in a line here: per item
  Closed, Waiting with its commit, or Open with why; the decisions the run took; the five
  builds; what the scenario tests found.

Groups, in order (the owner's order of importance of 2026-11-14, kept within a group's
files; `run_drc` first, as A3's way out uses it):

1. **`run_drc` and the project's state**: A19, A20, A5.
   - A19: the `.PrjPcb` document's flag read before the check and cleared after when the
     project had no unsaved change, as A17 does the board; `get_project_info` gives the
     project file's own state (`project_modified`) and counts it.
   - A20: with `rules` given, the report lists only those rules; without, as now.
   - A5: a call leaves the project folder as it found it: `run_drc` deletes the `.drc`,
     the `.html` and the outputs folder it created once read, `keep_report=true` to keep
     them; the compile calls remove a `.PrjPcbStructure` they created where none was.
2. **Wrong results, scripts**: A3, A9.
   - A3, a probe first: a live test that deletes a track on a saved copy, reopens it and
     expects the connection, in 2D and in 3D view. If no way gives the connection objects
     reliably, `get_unrouted_connections` takes the open connections from a DRC Un-Routed
     Net run on those nets (board and project left as found, group 1's way), and the
     result says which (`source`: `ratsnest` or `drc`). An honest count over a fast one.
   - A9: every declaration of a `var` line read, `a, b : Integer` included; offline tests.
   - A21 (added by the run, found by A3's probe): `run_drc` presses Run DRC on Altium's
     repour message and says it did.
3. **From schematic to board**: A10, A11, A16.
   - A10: tools to create a `.PrjPcb`, to add a document to it (an existing one, or a new
     `.SchDoc` or `.PcbDoc`), and to set the board shape from an outline (mils or mm,
     arcs allowed) or a closed shape on a mechanical layer; `build_schematic` given a
     project to add its sheet to.
   - A11, a probe first: the ECO from a script, by a process with its parameters
     (`dev/altium_process_catalog.txt`) or by the API, with no dialog left open. Found: a
     tool that updates the board from the schematic, `dry_run` first, returning what was
     added, changed and removed and what could not be. Not found: stays Open, as A8.
   - A16: a `FOOTPRINT` record (model name, library, current or not) in the symbol batch
     and in `create_schematic_symbol`.
4. **The board's setup and its outputs**: A13, A14, A12.
   - A13: a tool that sets the stack from a list top to bottom, in the form
     `get_pcb_layer_stackup` gives, read back equal; presets 2-layer 1.6 mm and 4-layer
     1.6 mm with 7628 prepreg.
   - A14: rule kinds differential pair, length and matched length, routing layers, plane
     connect, component clearance, silkscreen clearances, hole to hole, and `priority`.
     The fabricator preset is a data file naming its source page and the date read, its
     values from that page, not from memory; no page read, no preset.
   - A12: a tool that writes an OutJob from a preset or edits the outputs of one (Gerber
     layers and format, NC Drill, BOM, pick and place, output folder), read back by
     `get_outjob_settings`; an offline step that turns Altium's BOM and pick and place into
     a named service's columns (JLCPCB first) and zips the Gerbers and drills. The
     per-footprint rotation corrections are a table the owner fills, empty to start.
   - A34 (a), added by the owner on 2026-11-15: the resident's tag hashed from the text
     after the CRLF step, so a release copy and a checkout at the same commit give one
     tag; first in the group, as its live tests run from the checkout. A31 to A33 and the
     rest of A34 stay Open for the next run.
5. **Libraries**: A15, A8.
   - A15: `.IntLib` parts in `build_schematic` and `place_component`; the DbLib search as
     a tool. A supplier lookup and a vendor model import are not in this run (an outside
     service and its terms are the owner's call): that part stays Open.
   - A8, a probe first: `PCB:MakeLibrary` with its parameters; else the library built from
     the board's footprints through the PcbLib API. Found: a tool, which the scenario
     test's library step then uses in place of the hand step.

**Where the run stands** (ticked and committed after each step; a session that starts
reads from the first step not ticked):

Opening answer (the owner, 2026-11-14): yes to all of it, for all five groups: the push of
`ad25` before each release (the two plan commits with the first), the tag, the
registration, the release page, the scenario tests headless, the commit of their entries
unasked, and ending and restarting `X2.EXE` when Altium hangs.

- [x] A19: committed
- [x] A20: committed
- [x] A5: committed
- [x] group 1: offline and live tests, pushed, released (build: `build-20261114-163431`;
  Altium not restarted before the live tests, see the report)
- [x] group 1: scenario test (session id: `abd53408-395b-493b-9258-37a2b678aa3b`, stopped
  once for low memory and resumed), entry committed and sorted, release page; A19, A20 and
  A5 held and Closed
  What group 1 taught the rest of the run (2026-11-14): a subagent's `Stop-Process` on
  `X2.EXE` was refused by the auto mode classifier, so Altium was not restarted before the
  live tests: decided by the run to use the Altium the session started, used only by
  tests, not to retry the kill. The headless scenario test was stopped once by Claude
  Code for low memory (about 600 MB free, Altium 1.7 GB) and went on with `--resume`
  and the same id. An item's subagent writes "Fixed in the commit that moves it here";
  the main session puts in the SHA and the build after the release. Commits made after
  group 1's release go out with group 2's push. The run moved to a new session here, on
  the owner's word.
- [x] A3: committed (fixed through the ratsnest, `Net.Rebuild`; no DRC fallback)
- [x] A9: committed
- [x] A21: committed
- [x] group 2: offline and live tests, pushed, released (build: `build-20261114-180059`;
  295 offline, 23 live; Altium not restarted before the live tests)
- [x] group 2: scenario test (session id: `f712df7c-6b4f-4f46-ad91-dacbeb6807ba`), entry
  committed and sorted, release page; A3, A9 and A21 held and Closed, A23 new (Open)
  Stood here 2026-11-14: the run stopped after group 2 on the owner's word, to go on in a
  new session from A10. Group 2 taught: A3's probe found `Board.AnalyzeNet` was the fault,
  so no DRC fallback; it also met `run_drc` waiting on Altium's repour message, which the
  run added to group 2 as A21 (decided by the run, written into it). The owner reported
  A22 mid-run (Altium takes the keyboard and the front at every call), recorded for the
  next run: nothing is typed on the machine while tests run. The scenario test ran once,
  not stopped (about 1.3 GB free before it). The record commits after the release (the
  entry, the sort, this line) go out with group 3's push. Altium was started by the run
  and left running.
- [x] A10: committed
- [x] A11: left Open (RCW error after the ECO twice; code in a named stash, see A11)
- [x] A16: committed
- [x] group 3: offline and live tests, pushed, released (build: `build-20261114-210622`;
  341 offline, 41 live; Altium restarted before the live tests, by the session)
- [x] group 3: scenario test (session id: `42669980-da08-4c52-856a-ddec5bf03954`), entry
  committed and sorted, release page; A10 and A16 held and Closed, A25 to A28 new (Open)
  Stood here 2026-11-14: the run stopped after group 3 on the owner's word, to take A22
  and A24 (a call meeting Altium's windows: the keyboard, and messages nobody answers) in
  a new session first; groups 4 and 5 wait for a later run, from A13. Group 3 taught: A11's
  ECO works by driving its dialog, but Altium fell into a loop of "COM object that has been
  separated from its underlying RCW" after it twice, so A11 stayed Open with its code in a
  named stash; Altium's own modal messages blocked calls twice ("File Not Open", the RCW
  error), which the owner saw on screen before the run did, hence A24. The owner allowed
  ending `X2.EXE` in this clone's `.claude/settings.local.json` (local, not committed), so
  a session here restarts a hung Altium itself (`Stop-Process -Name X2 -Force`, or
  `taskkill //IM X2.EXE //F` in Bash). The scenario test ran once, not stopped. The record
  commits after the release (the entry, the sort, this line) are not pushed: they go out
  with the next push of `ad25`. Altium was restarted by the run and left running.
- [x] A22: committed (a session of its own, 2026-11-14, before groups 4 and 5)
- [x] A24: committed (the same session)
  Next, on the owner's word of 2026-11-14, in a new session: the release of A22 and A24
  (steps 1 to 5 of *Release and run*, the push of `ad25` with it) and its scenario test,
  then A29 (a tool to answer a message), then A30's probe; groups 4 and 5 after.
  Opening answer of that session (the owner, 2026-11-14): yes to all of it: the push, the
  release, the tag, the registration, the release page, the scenario test headless and the
  commit of its entry unasked, A29 committed, A30 a probe only (its decision back to the
  owner), and ending a hung `X2.EXE`.
- [x] A22 and A24: offline and live tests, pushed, released (build:
  `build-20261114-225815`; 368 offline, 46 live; Altium restarted before the live tests)
- [x] A22 and A24: scenario test (session id: `6faad091-22be-4278-adbf-a02f1cf447ef`), entry
  committed and sorted, release page; A22 and A24 held for what they asked and Closed, A31
  to A33 new (Open, for the next run: decided by the run to keep this session to what the
  owner named, A29 and A30's probe). The scenario test ran once, not stopped, 99 turns.
- [x] A29: committed
- [x] A30: probe, its result written into the item
  A30 built on the owner's word of 2026-11-15 ("Build it, launch as fallback"), in a
  session of its own; then, on the owner's yes of the same day: the release of A29 and A30,
  its scenario test headless and the commit of its entry.
- [x] A30: committed (`f1b1559`)
- [x] A29 and A30: offline and live tests, pushed, released (build:
  `build-20261115-114630`; 415 offline, 55 live through the resident)
- [x] A29 and A30: scenario test (session id: `173d1f40-3911-4aed-a69d-f99eb870248b`),
  entry committed and sorted, release page; A29 and A30 held for what they asked and
  Closed, A34 new (Open), A31 and A32 met again. A first run (session id
  `7b30a860-4934-4fb9-9d6a-c5e1b88d69b2`, from 11:47) was stopped by the owner's word after
  about 2 minutes; run again from the start on the owner's word of 2026-11-15, its copy
  moved aside to `uji/0.7.0-20261115-114630.run1-dihentikan/` in the owner's project,
  Altium started fresh. The second run ran once, not stopped, 93 turns. The record
  commits (the entry, the sort) are not pushed: they go out with the next push of `ad25`.
- [x] A34 (a): committed (as A35 in Waiting; Altium started by the run and left running)
- [x] A13: committed (A36 new from it, Open)
- [x] A14: committed (priority by remove and re-add; JLCPCB preset read 2026-11-15)
- [x] A12: committed
- [x] group 4: offline and live tests, pushed, released (build: `build-20261115-143551`;
  519 offline, 63 live; Altium restarted before the live tests)
- [x] group 4: scenario test (session id: `982a2248-9a1b-4881-b5ee-2da83c636478`), entry
  committed and sorted, release page; A35, A13 and A12 held and Closed, A14 Closed but its
  priority (A38), A37 to A39 new (Open). Stopped once by the 5-hour usage limit after 67
  turns and resumed with the same id (32 turns more). Then the run stopped after group 4 on
  the owner's word of 2026-11-15, to go on in a new session from A15.
- [x] A15: committed (split: A15 (a) done as A40, in Waiting; A15 (b), the supplier lookup
  and vendor import, stays Open by the plan)
- [x] A8: committed (found: `PCB:BuildPCBLibrary` run hidden; `make_pcblib_from_board`)
- [x] group 5: offline and live tests, pushed, released (build: `build-20261115-172812`;
  545 offline, 72 live; Altium restarted before the live tests)
- [x] group 5: scenario test (session id: `72025b3d-6b33-4d9b-867b-6c414f8185ed`), entry committed and
  sorted, release page; A40 and A8 held and Closed (A8 but the footprints' descriptions, A41),
  A41 to A44 new (Open), A26 met again and widened. Ran once, not stopped, 111 turns, about
  12 minutes.
- [x] the report (2026-11-15, in the reply): the run's five groups released (`build-20261114-163431`,
  `-180059`, `-210622`, `build-20261115-143551`, `-172812`); Closed by their scenario tests A19,
  A20, A5, A3, A9, A21, A10, A16, A35, A13, A14 (but its priority, A38), A12, A40 and A8 (but
  its descriptions, A41); left Open A11 (the ECO's RCW error, code in a named stash) and A15 (b)
  (an outside service, the owner's call); new from the scenario tests A23, A25 to A28, A36 to
  A39, A41 to A44, for the next run. The record commits after group 5's push are not pushed.

## Run 2026-11-22

Planned 2026-11-22 under the owner's token rule above. Sixteen items in three groups (the
items that report success with a wrong result, those whose results are largest, and the
four missing tools met most, as small changes to existing tools), and a recipes file for
thirteen more, then phase 2 unattended across as many sessions as it needs, from the first
step not ticked below. The opening question was asked in two sessions of 2026-11-22
(*Opening answer*).

### How it runs

- **Unattended.** After the opening answer nothing is asked. A decision met mid-run is
  the run's: the option that keeps the server's checks honest and its results true, the
  smaller change when two are equal, written into its item as "Decided <date> by the run,
  not the owner: ..., because ..." and listed in the report.
- **The token rule.** No new tool. No new argument but A58's `spec_file`, which the
  opening answer took; A56's op is one more kind of entry in an existing list. A result
  made smaller is made so by default, not behind a flag.
  Each group's release measures the tool listing (names, descriptions and schemas, as
  `main.mcp.list_tools()` gives them) before and after: 80 tools, 164,529 characters at
  `f120b3f` (2026-11-22). A group that grows it by more than 1% says why in its release
  notes. Decided 2026-11-22 in the plan, not the owner: the measure and the 1%, because
  the owner's word of 2026-11-22 (above) asks that features not keep growing token use.
- **Never stop on one item.** A fix that does not hold after a fair try, or a probe that
  finds no way, stays Open with what was tried written into it, its partial code in a
  stash named for it (`git stash push -m "<code> ..." -- <files>`), and the run goes on. A
  permission prompt or a dialog nobody answers is the one thing it cannot pass: it writes
  where it stood below, and stops.
- **One subagent per item**, the main session thin; serial (`serial: true`, one Altium):
  one at a time in the main tree on `ad25`, never beside a live test or a scenario test.
  Models: Sonnet for A27, A70, each group's tests and release; the default model for the
  other items (probes or diagnosis) and for the scenario test.
- **A subagent's brief**: its item as written below and in the item, the decision, the
  files likely touched, and these rules: read `CLAUDE.md`, `README.md`, `dev/README.md`;
  never switch branches, commit, push, tag or reset; a stash only by name and file;
  `findings.md` is not its to edit. First a live test that fails on the current code
  (`server/tests/live_altium.py`'s helpers, `ALTIUM_LIVE=1`, copies of Altium examples
  closed unsaved; read back through Altium or the saved file); an item whose test does not
  fail is closed instead. Then the fix, that test and the live tests of the tools it
  touched, the offline tests (`.github/workflows/tests.yml`'s list, a new module added to
  it). Then in `open_items.md` the item moved to the end of Waiting, `BUILT <date>, proof:
  the scenario test`, with its cause, fix, the test before (its message) and after (with
  counts), "Fixed in the commit that moves it here"; the Open paragraph from `board.py
  --open-line`, `board.py --check` clean. Report in ten lines: outcome, test before, tests
  after with counts, files changed, its "Decided" lines, a commit subject and body.
  Nothing that names where a finding came from (`findings.md`'s top).
- **Per group**: the offline tests and every `test_live_*` once (Altium restarted first);
  the release, `CLAUDE.md` *Release and run* steps 1 to 5 (push `ad25`, copy, venv,
  re-register `altium-mcp` from `C:\Users\Ahmad Aziz\Data\Project\claude_altium`, tag,
  release page); the scenario test (below), its entry committed unasked and sorted, the
  release page's line updated (step 7). The main session puts each Waiting item's SHA and
  build in after the release.
- **Commits**: one per item, its fix with its note, as `git-workflow:pr` gives a commit on
  `ad25` (no trailer); pushed at the group's release.

### The scenario test of a group

A headless session in `C:\Users\Ahmad Aziz\Data\Project\claude_altium`, which loads the
release just registered, by the procedure in its `reports/uji-skenario.md`.

1. **Memory**: read free memory (`(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory`);
   at least 1.5 GB, else close what this run left open (scratch documents in Altium) or
   restart Altium; 1.07 GB free when this plan was written, and a test was stopped at
   about 600 MB on 2026-11-14.
2. **Altium** started from its exe, `C:\Program Files\Altium\AD25\X2.EXE`, never by the
   server's launch, and left to finish loading.
3. **The id first**: a new UUID, written into the group's check line below and committed,
   before the start.
4. **Started detached** by `Start-Process` on a launcher (a `.ps1` in the run's scratchpad)
   that runs, from the test project's folder,
   `claude -p "<sentence>" --session-id <uuid> --permission-mode auto --allowedTools mcp__altium-mcp --add-dir "C:\Users\Ahmad Aziz\Data\Project\altium-mcp" --output-format json`,
   writes stdout and stderr to files beside it and an `EXIT <code>` line at its end. The
   sentence: `Uji skenario release <v>-<stamp> (<items>), menurut reports/uji-skenario.md.
   Tanpa nanya apa-apa. Cek singkat dulu (get_server_status, get_project_info,
   get_board_summary). Skenario baru untuk fitur baru ditulis ke prosedur dengan
   baseline-nya. Finding ke findings.md fork, baris hasil dan pemetaan di prosedur; jangan
   commit. Akhiri dengan laporan sepuluh baris: tiap item lolos atau gagal, finding baru.`
5. **Watched** by its process and the last write of its transcript
   (`~\.claude\projects\C--Users-Ahmad-Aziz-Data-Project-claude-altium\<uuid>.jsonl`), by
   no background task. It should take 60 to 90 minutes. Changed 2026-11-23 by the owner:
   "harusnya run itu tetep bisa jalan tanpa gw": the run never waits on the owner's
   "cek". It watches by a background `Bash` until-loop of its own (the `EXIT` line,
   `tasklist` on the pid, the transcript unwritten over 1800 s, `sleep 60`), re-armed if
   it is ended, and goes on in the same session past 150k tokens (Claude Code compacts
   it; this checklist carries the state). Changed again 2026-11-23 by the owner ("altium udah beres
   kenapa ada nganggur lama? itu harus lo benerin"): the loop polls every 10 s, and the
   next step that uses Altium (a fix again, the next group's first item) starts as soon as
   a check ends, beside the sort; its subagent does not edit `open_items.md` but gives the
   item's text in its report, written in by the main session after the sort.
6. **Stopped with no entry**, or the transcript unwritten 30 minutes with the process
   alive (stopped first by `Stop-Process`): resumed unasked from the same folder,
   `claude -p --resume <uuid> "lanjutkan uji skenario"`, same flags, up to three times;
   then the line below reads Blocked, with why.
7. **What it finds goes four ways**: held (the item to `closed_items.md`, `CLOSED <date>`,
   a `Held` line: the scenario test is its proof); a fix of this group not holding (back
   under `## Open`, fixed and checked again before the next group); a new point, small and
   in the group's files (a later step of the run, a new code); a new point needing the
   owner (a new Open item, for the owner).

### Items

- **Group 1, ERC and the compile** (`get_erc_violations`, `get_project_components`,
  `other_utils.pas`): A49, A50, A48.
  - A49: the result by default grouped by violation type and level, each with its count
    and its first three violations in full; the full list in the file the tool already
    writes, its path given; no new argument. Test first: a live test on a project with
    some hundreds of violations of a few kinds, the result over 30k characters today;
    after, under 10k, the counts summing to the total. Files: `server/main.py`, tests.
  - A50, a probe first: what tells a suppressed violation (a property of the violation,
    else a match of its location against active no-ERC markers with `SuppressAll`). Found:
    left out of the list and counted as `suppressed: n`. Test first: a sheet with a
    floating input pin under a no-ERC marker, its violation listed today. Not found: stays
    Open, what was tried written. Files: `server/AltiumScript/other_utils.pas`,
    `server/main.py`.
  - A48, a probe first: a call that brings the compile up to date after a script edited a
    sheet without marking it modified, short of closing the project. Found: made inside
    `get_erc_violations` and `get_project_components`, no new argument. Test first: a
    script sets a placed part's footprint without `SetModified`, and the compile reads it
    empty today. Not found: stays Open, its usage note (in the item) put where the
    opening answer puts usage notes.
  - A48 (b), taken again: A48's fix did not hold for objects a script removed (point 5 of
    the scenario test of build 0.7.0-20261123-001227). A probe first for a sheet-level
    re-read that also drops removed objects; not found, a short `stale_sheets` in both
    tools' result (or the compile's object count checked against the sheet's) and one line
    in `run_altium_script`'s description on `SCHM_PrimitiveRegistration` after a removal.
  - A74, joining group 1 again (point 2 of the same test): `first` holds the group's first
    three distinct details. Files: `server/erc_summary.py`, tests.
- **Group 2, `build_schematic` and placing parts** (`server/main.py`'s schematic tools,
  their `.pas`): A46, A58, A45, A26, A27, A71.
  - A46: `pin_map` keyed by pin number, the name a field; returned in full only on a call
    with no wires (the pin read the description advises); with wires, a count per part
    and the map written to a JSON file in the server's own folder, its path given.
    Decided 2026-11-22 in the plan, not the owner: the map returned only on a call with
    no wires, because it is the smaller change with no new argument and keeps the read the
    description advises. Test: offline on the keying (pins sharing a name kept), live on
    the result's size with wires.
  - A58, taken by the opening answer: a `spec_file` (the path of a JSON file holding the
    call's other arguments, as the call would give them inline) on `build_schematic` and
    `edit_schematic`; an argument given inline as well as in the file is refused, not
    merged. Decided 2026-11-22 in the plan, not the owner: refused, not merged, because a
    merge rule is one more thing the description must explain. Test first: offline, the
    argument unknown today; then a live build from a file, read back from the saved sheet.
    Files: `server/main.py`, tests.
  - A45: a part entry may carry `part` (letter or number), in `build_schematic`'s parts
    and in `place_component`; an entry with none on a multi-part symbol places part A,
    and the result lists the parts not placed under `warnings`, no longer silent;
    `pin_map` gives only placed parts' pins, each at its own place. Decided 2026-11-22 in
    the plan, not the owner: a key inside an existing list, not an argument, because the
    other parts need places only the caller can give. Test first: a six-part symbol, the
    result silent on parts B to F today.
  - A26: the focused project's modified flag left as found; without `project_path` the
    sheet stays a free document; after a failure the unsaved sheet is taken out again; one
    `detached_from`, and `sheet` the saved name. Test first: a focused project unmodified
    before, modified and holding `Sheet1.SchDoc` after a call with no `project_path`.
  - A27: the footprint given becomes the only current one, the library's mark moved. Test
    first: `IsCurrent` true on two models today.
  - A71: after placing, `PinsMoveable` set True then False inside the modify, in
    `place_component` and `build_schematic`, saved. Test first: ten placements each of an
    8-pin symbol (rectangle and line) and a 2-pin one (four arcs), the saved file read for
    `IsNotAccesible=T` on every child; the fault was intermittent (3 of 6), so a test that
    does not fail leaves the item Open with the count, not Closed.
  - A56 (a), taken by the opening answer: an `edit_schematic` op `set_footprint`
    (designator, footprint name, library path), which replaces the part's current PCB
    implementation (`RemoveSchImplementation`, then `AddSchImplementation`, `ModelType
    'PCBLIB'`, `AddDataFileLink`, `IsCurrent`, inside `SCHM_BeginModify`/`EndModify`, saved),
    the way five sessions did it by script. Test first: a placed part, its footprint
    unchanged by any call today (the op refused as unknown); after, the saved sheet read
    back for the new footprint and its library, one implementation current. (b), which
    library a placed part links to: a recipe (group 3) if a session's script is in the
    record, else stays Open. Decided 2026-11-22 in the plan, not the owner: no
    `footprint_library` field in `get_project_components`, because the token rule asks for
    the smaller change. Files: `server/main.py`, the schematic `.pas`.
- **Group 3, the library tools and the recipes** (`get_symbol_primitives`,
  `get_footprint_primitives`, `create_schematic_symbol`, `make_pcblib_from_board`,
  `add_project_document`, `get_screenshot`, `run_altium_script`'s helpers and description):
  A57, A66, A41, A70, A28, A60 (a), the recipes.
  - A57: the inventory mode (no name given) returns each symbol's or footprint's name,
    description and pin or pad count only; the name argument takes several names
    (comma-separated) for details of several in one call; no new argument. Test first: the
    inventory of a library of some hundreds of symbols, over 60k characters today.
    `get_project_components`' size (A57's line of 2026-11-22) is not in this run.
  - A66: a footprint given by name only gets its library's location from the project's
    libraries, then the installed ones; none found, a line in `problems`. Test first: a
    name held only by an installed library, reported linked with no location today.
  - A41, a probe first: where the descriptions are lost (the hidden run, the filter, the
    save); each footprint given the board's description before the save, and descriptions
    compared. Test first: a board whose components carry descriptions, the library's
    empty today.
  - A70: `OpenSchDoc` opens a `.SchLib` as a library (by extension), and
    `create_symbols_batch`'s "could not open and focus" names the kind it found. Offline
    test, and a live one opening a `.SchLib` through the helper.
  - A28, taken by the opening answer: `add_project_document(create=True)` also makes an
    empty `.SchLib` or `.PcbLib` (by `document_path`'s extension) and adds it to the
    project named, not the one in focus; the `.PcbLib` holds no default `PCBComponent_1`.
    No new argument. Test first: `create=True` on a `.SchLib` path refused today; after,
    the file on disk, in the project, and for a `.PcbLib` no footprint in it. Files:
    `server/main.py`, the project `.pas`.
  - A60 (a), taken by the opening answer: a `sch` capture fits the whole sheet first
    (`Client.SendMessage('SCH:Zoom', 'Action=Document', ...)`, the way that held), by
    default; `zoom_to` on `sch` answered with a warning that it is for PCB only. Decided
    2026-11-22 in the plan, not the owner: fit by default, not `zoom_to="fit"`, because
    `zoom_to` is a list of designators and the token rule asks that a result be right by
    default. Test first: an A3 sheet zoomed in, its capture cut today; after, the whole
    sheet's border in the image. (b), a `.PcbLib` footprint's view, out of the run (a new
    argument). Files: `server/main.py`, the screenshot `.pas`.
  - The recipes, taken by the opening answer: `docs/recipes.md`, one section per item, each
    a DelphiScript a session proved (from the item's record and the `findings.md` entries
    it cites) with the `run_altium_script` call it needs, in English, naming no design of
    the owner's (`findings.md`'s top); one line in `run_altium_script`'s description naming
    the file by its path, computed from `main.py`'s folder at import. The items: A47, A51,
    A52, A54, A55, A59, A62 to A65, A67, A69, A34 (f), A56 (b), and A48's note if its probe
    finds no call. An item whose record holds no script a session proved stays Open, what
    is missing written into it. Each item written goes to Waiting, `BUILT <date>, proof: the
    scenario test`, and to `closed_items.md` as usage (`CLOSED <date>, usage`) when the
    scenario test held for the file: the description line read, the file opened, and three
    recipes run, the run's choice of the most met. Decided 2026-11-22 in the plan, not the
    owner: three recipes run and not all, because a scenario test of thirteen scripts would
    double its time, and the path computed, because a release's folder differs each time.
    Model: the default. Files: `docs/recipes.md`, `server/main.py`'s description.
  - A75 (point 6 of the scenario test of build 0.7.0-20261123-001227): a line in
    `run_altium_script`'s description beside the recipes, that `List1..3` keep strings,
    not objects. Files: `server/main.py`'s description.
  - A77 (point 4 of the scenario test of build 0.7.0-20261123-103915), new: one way of
    filling a placed part's library fields in `build_schematic` and `place_component`, so a
    component's parts placed by both compile as one. Test first: part B by the build and
    part C by place_component, one designator, compiled as two today. Files:
    `server/AltiumScript/schematic_utils.pas`, tests. Decided 2026-11-23 by the run, not the
    owner: a new item in group 3, not A45 fixed again with group 2 checked again, because
    A45's own promise held (point 3) and the fault is in how the two tools fill a part's
    library fields, older than A45.
  - A78 (point 10 of the same test), new: A52's recipe says its script leaves the sheet
    unmodified; it does not. The sentence corrected, offline. Model: Sonnet.
- **For the owner, prepared**: A11, whether the ECO done by hand (Import Changes,
  Validate, Execute, Close), then new projects made, brings Altium's RCW error too; if it
  does, it is Altium's and the stashed tool may go in with a usage note (the item, its
  last lines). Updating `ad25` onto `upstream/main`, 116 commits behind on 2026-11-22
  (upstream's own foreground guard, #100, against A22's; new tools such as
  `dismiss_dialog` and `list_open_documents`, which grow the listing): the owner's call,
  its own session, not in this run.
- **Out of this run**: A23, A25, A31 to A34 (but A34 (f)), A36 to A39, A42 to A44, A53,
  A61, A68, A72 (faults of the bridge, the board and the schematic's smaller points: the
  owner chose three groups); A60 (b) (a new argument); A73, the tool descriptions' size
  (written 2026-11-22 by the opening answer, for a later run); A15 (b), not taken by the
  opening answer, stays Open as it was; A1, A2, A7 (waiting on upstream; A2's following of
  upstream PR #113 not taken by the opening answer).

### Opening answer

The owner, 2026-11-22, two of four:

- Grants: "all, tapi kita pindah sesi dulu", to the option "All": commit the sort now;
  per group: push `ad25`, release folder and venv, re-register `altium-mcp` (scope local,
  `claude_altium`), tag, release page; scenario test headless (`claude -p` via
  `Start-Process`, `--resume` when stuck, `Stop-Process` when hung); commit the scenario
  test's entry unasked; restart `X2.EXE` when it hangs.
- Scope: "Token-first, 3 groups".

The other two, asked again 2026-11-22 in a new session, in Indonesian with each term
explained (the first asking left "op", "recipe" and "usage file" unexplained):

- Small changes to existing tools (multiSelect): "A28 empty library, A60 fit schematic,
  A56 set footprint op, A58 spec_file", all four.
- Extras (multiSelect): "Recipes file, Item: trim descriptions". Not taken: A2 to follow
  upstream PR #113; A15 (b) to Closed as DECIDED AGAINST.

Added by the owner 2026-11-23 02:18, going to sleep while the run works on A48 (b): "gw
tinggal tidur ya, jangan stop krn alasan sepele. semua yang dibutuhkan saya izinkan,
jangan sampe terhambat karena izin. kalau perlu restart altium silakan restart". So what
this plan's steps need is granted without asking, and Altium may be restarted when a step
needs it, not only when it hangs. The plan's scope stands (*Out of this run*, the choices
left to the owner). A restart does not save the owner's documents: what was open modified
is written down before it.

### Where the run stands

- [x] Phase 1: the opening question asked and answered (2026-11-22, in two sessions)
- [x] A49: committed (69f2cf9)
- [x] A50: committed (49ecf2f)
- [x] A48: committed (891ee59)
- [x] Group 1: tests and release (build: 0.7.0-20261123-001227, tag build-20261123-001227)
- [x] Group 1: scenario test (session id: af570230-bb0a-49b3-aac8-e3f16361ede9, started 2026-11-23, free memory 1237 MB after the restart), its outcome sorted
  - Ran 00:14 to 00:22, `EXIT 0`, its entry committed alone (`eeaacd2`), sorted 2026-11-23 (`613fa9a`):
    A49 and A50 held (closed), A48 back to Open as A48 (b), new A74 and A75, A26, A34 and
    A44 met again.
- [x] A48 (b) again: committed (71514df)
  - Ended 2026-11-23 02:29 still Open, partly built (the description's line, the tests): no
    safe re-read found, no `stale_sheets` (the item). About 154k tokens, 14 minutes.
  - **Stopped here 2026-11-23 about 02:11 on the owner's word, to move to a new session**
    ("mending pindah sesi sekarang"): in the probe stage, no test written, no fix, no file
    of the repo changed. Goes on with a fresh subagent from A48's last part, *Probed
    2026-11-23*, its probes not run again. Its cost so far: about 163k tokens, cut once by
    the usage limit and resumed. (The sort's: 116k, 2.5 minutes.)
  - Altium was found closed at 02:14 (pid 20600 gone, not by this session), started again
    from its exe at 02:15 (pid 21380). The owner's documents came back open and read
    unmodified at 02:29 (the subagent's report). `ad25` is pushed at group 1 again's
    release, not before.
- [x] A74: committed (12ce1ca)
- [x] Group 1 again: tests and release (build: 0.7.0-20261123-031122, tag build-20261123-031122)
  - 559 offline and 82 live tests OK (A48 (b)'s two expected failures), Altium restarted
    first with nothing modified. The listing 157,905 to 157,962 characters (+0.04%).
    Decided 2026-11-23 by the run, not the owner: the tests by a Sonnet subagent, the push,
    registration, tag and page by the main session, because what leaves the machine is
    read first where the grant is known.
- [x] Group 1 again: scenario test (session id: ade4c3bd-0444-4d86-b3fc-9aacd600eb5c,
  free memory 1123 MB after a restart of Altium, pid 17308; output and launcher in the
  run's scratchpad, `check_031122.*`), its outcome sorted
  - Ran 03:14 to 03:21, `EXIT 0`, no resume, its entry committed alone (`f6eedbc`): A74
    held (closed); A48 (b)'s built part held, the item still Open as written, so no fix
    again; A76 new, out of this run; A34 met again. A46 began beside the sort.
- [x] A46: committed (a441051)
- [x] A58: committed (cc27c73)
- [x] A45: committed (007672a)
- [x] A26: committed (153c546)
  - Done 2026-11-23 after the owner ended Altium by hand: Altium started again from its exe
    (pid 12520), the stash applied and dropped, the fix held live (4/4, 34/34, 585/585
    offline). About 129k tokens, 19 minutes.
  - **Blocked 2026-11-23 04:17, every step that needs Altium** (A26, A27, A71, A56 (a), A57,
    A66, A41, A70, A28, A60 (a), each group's tests, release and scenario test). A probe's
    clean-up of A26 left Altium (pid 17308) behind a crash message, and its subagent's
    `Stop-Process` on it was denied by the auto mode classifier ("[Destructive or Unwanted
    Actions]"). Not retried, and not done another way by the main session (no kill, no
    close of the window, no press of the message, whose button sends a crash report): the
    owner's word of 02:18 grants a restart, and a denial by the permission system is still
    the owner's to lift.
  - For the owner: end Altium by hand (the message's button, or Task Manager). The 28 open
    documents read unmodified at 04:21. Then, if the session is gone, the sentence
    `backlog:run open_items.md "## Run 2026-11-22", dari langkah pertama yang belum dicentang. Tanpa nanya apa-apa.`
    A26's fix is in the stash `run 2026-11-22 A26`, never run in Altium: its item says what
    to run.
  - Found at the block, by hashes of the owner's 399 files: the run's restart of 03:12 (the
    main session closing Altium's window before the scenario test, nothing modified) was not
    free of writes. Altium wrote one generated `.PrjPcbStructure` again (1401 to 1298 bytes,
    now with no diff against that repo's last commit; the 1401 bytes were not committed and
    no copy was looked for or restored), and touched 12 other generated files, same content.
    No change of content since 04:14. So "nothing modified" does not mean that closing
    Altium writes nothing: hash before a restart and compare after it, and tell the owner.
  - Decided 2026-11-23 by the run, not the owner: the two steps that need no Altium (the
    recipes, A75) taken now, out of their order, offline, because the owner asked at 02:18
    that the run not stop and neither reaches Altium; their proof stays the scenario test.
    Nothing is pushed or released until the live tests can run.
- [x] A27: committed (71f8054)
  - Sonnet, about 116k tokens, 15 minutes; 3 of 5 failed before, 5/5 after.
- [x] A71: committed (9ae6937)
  - About 153k tokens, 22 minutes; 10 of 20 failed before for each tool, 0 of 40 after. Its
    `check_schematic` part is a leftover, to be filed as an item at the run end.
- [x] A56 (a): committed (8f57314)
  - About 161k tokens, 19 minutes; 3/3 live failed before, then held.
- [x] Group 2: tests and release (build: 0.7.0-20261123-103915, tag build-20261123-103915)
  - 588 offline and 107 live tests OK (2 expected failures, A48 (b)), Altium restarted
    first (pid 12520 to 6756), every document unmodified, the 223 files of the test
    project hashed before and after the restart, none changed. The listing 157,962 to
    159,660 characters (+1.07%), why in the release notes. A56 (a) is commit 8f57314.
- [x] Group 2: scenario test (session id: 06cf5507-82ca-4d5d-86ae-310e8c0c0ddd), its outcome sorted
  - Started 10:42 by its launcher (pid 21664), output and launcher in the session's
    scratchpad (`check_103915.*`); Altium restarted for memory first (pid 6756 to 17088,
    the 223 files hashed before and after, none changed); free memory 845 MB.
  - Decided 2026-11-23 by the run, not the owner: started under the plan's 1.5 GB, because
    what holds the rest is the owner's other Claude sessions, not this run's to end, and
    the two checks before ran at 1.1 to 1.2 GB.
  - The owner, 2026-11-23: "beres grup 2, kita pindah sesi ya": once this step is ticked
    and committed, the session hands over, and group 3 starts in a new session.
  - Handed over 2026-11-23 about 11:00, everything committed and pushed (`ad25` at the
    sort's commit). Altium left running (pid 17088), started from its exe. Not in a file:
    the session's scratchpad helpers (an item mover, the check's launcher), rebuilt as
    needed; the run's `learned.md` entry, written at the run's end. Costs this session:
    an item 116k to 161k tokens and 15 to 22 minutes, the test pass 72k and 29 minutes,
    the check 12 minutes, its sort 116k and 3 minutes.
  - Ran 10:42 to 10:54, `EXIT 0`, no resume, 89 turns, about $5.41; its entry committed
    alone (`c1385bb`), sorted 2026-11-23: A46, A58, A45, A26, A27, A71, A56, A75 held
    (closed), A55 closed as usage; A77 and A78 new, steps in group 3; A61, A34, A52 met or
    checked.
- [x] A57: committed (c7aac0a)
  - About 165k tokens, 13 minutes; 4 failures and 1 error of 6 live before, 7/7 after, 596 offline.
    Altium found closed at the session's start, started from its exe (pid 11028).
- [x] A66: committed (3ab04ad)
  - About 172k tokens, 16 minutes; 3 of 3 live failed before, 11/11 after (40/40 with the
    touched tools' live tests), 603 offline.
- [x] A41: committed (e4a6669)
  - About 90k tokens, 20 minutes; the probe found Altium's hidden Make PCB Library empties every
    description; 12 of 12 empty before, 5/5 live after, 604 offline.
- [x] A70: committed (f4ae3d3)
  - Sonnet, about 150k tokens, 25 minutes; 2 live failures before, 4/4 after, 607 offline. One
    run of the touched tools' 32 live tests failed `test_parts_from_an_intlib` once at about
    600 MB free, held alone and in sequence: watched at group 3's full pass.
- [x] A28: committed (ad9e9da)
  - About 130k tokens, 40 minutes; refused before, 14/14 live after, 608 offline.
- [x] A60 (a): committed (4eef324)
  - About 120k tokens, 30 minutes; 2 of 2 live failed before, 2/2 after (twice), 608 offline.
    The capture was cut by DPI scaling as well as by the zoom: images now 2418x1308 here.
- [x] The recipes (A47, A51, A52, A54, A55, A59, A62 to A65, A67, A69, A34 (f), A56 (b)): committed (ba17162)
  - Of fourteen items only A55 had a script proved in full: it waits, the others stay Open,
    each saying what is missing. Built offline: 574 of the 583 offline tests run, OK; the 9
    that start processes or call the real status tool are to run before the release (the
    subagent's report; two of its first runs did call `get_server_status`'s test by mistake).
    The scenario test runs first A55, A34 (f) and A52's removal.
- [x] A75: committed (b764b10)
  - Stopped 2026-11-23 about 04:55 at the usage limit, taken up by the session's hourly
    self-check at 05:54 (Altium still blocked): A75 done offline, its tests in its item.
  - **Blocked since 06:00: every step left needs Altium** (A26's line). The self-check cron
    was deleted with this line, as its own prompt says for a run written down Blocked.
  - The watcher for Altium's end and the subagents' watchdog were stopped by Claude Code
    for low memory (546 MB free, Altium 2.4 GB private) and not started again, so closing
    Altium no longer wakes the run: the owner says "lanjut", or opens a session with the
    sentence in A26's line.
  - Does not travel by file: the commits since `6aa0661` are local, pushed at group 2's
    release; A26's fix is in its stash; the subagents' brief and the helper scripts are in
    the session's scratchpad. Not written yet: the run's `learned.md` entry, and as items at
    the run's end what A46, A45, A58 and A55 list as seen and left.
- [x] A77: committed (afc0fad)
  - About 115k tokens, 40 minutes; failed before, 31/31 live after in eight modules, 608 offline.
    `test_live_symbol_footprint` and `test_live_project_setup` cut by Claude Code for low memory
    (about 0.8 GB free), left to group 3's full pass.
- [x] A78: committed (049670b)
  - Sonnet, offline, about 40k tokens, 6 minutes; 608 offline, `test_recipes` 5/5.
- [x] Group 3: tests and release (build: 0.7.0-20261123-140004, tag build-20261123-140004)
  - Sonnet, about 115k tokens, 33 minutes: 608 offline and 125 live tests OK in 26 modules (2
    expected failures, A48 (b)), Altium restarted first (pid 11028 to 20088), every document
    unmodified, the 242 files of the test project hashed before and after, none changed;
    free memory 918 MB after, 766 MB lowest. The listing 159,660 to 159,813 characters
    (+0.10%), by the subagents' measure of group 2's method. `ad25` pushed at 049670b.
- [x] Group 3: scenario test (session id: 9b50c01a-2013-453c-be37-d4a6e543e2bc), its outcome sorted
  - Started 14:01 by its launcher (pid 16560), free memory 1198 MB, Altium pid 20088 from its
    exe; output and launcher in the session's scratchpad (`check_140004.*`). Stopped 14:09 by
    the usage limit of the account it ran on (`EXIT 1`, 72 turns, no entry); resumed once at
    14:19 after the owner's new login (pid 14760, free memory 1347 MB, Altium pid 1812, which
    the check had started from its exe at 14:06 after the memory guard refused every call).
    `EXIT 0` at 14:23, 30 turns more, about $9.61 in all; its entry committed alone
    (`0c08ac0`), sorted by a subagent (about 75k tokens, 9 minutes): A57, A66, A41, A70, A28,
    A77, A78 held (closed), A60 (a) held, A60 open for (b); A79, A80, A81 new, out of this
    run. The release page's line updated.
- [x] The report
  - Run 2026-11-22 selesai 2026-11-23: tiga grup, 25 item diambil, empat sesi setelah plan.
  - Per item: Closed (lolos uji skenario): A49, A50, A74 (grup 1); A46, A58, A45, A26, A27,
    A71, A56 (a), A75, A55 sebagai usage (grup 2); A57, A66, A41, A70, A28, A77, A78 (grup
    3). A60: (a) lolos, item tetap Open untuk (b), argumen baru di luar run. A48 (b): Open,
    tidak ada re-read aman; yang dibangun (baris deskripsi, tes) lolos. Resep tanpa skrip
    yang terbukti, tetap Open dengan apa yang kurang: A47, A51, A52, A54, A59, A62 sampai
    A65, A67, A69, A34 (f); A56 (b) ditutup bersama A56 di grup 2. Baru, di luar run: A76,
    A79, A80, A81, A82 sampai A87.
  - Release: grup 1 build 0.7.0-20261123-001227, lalu 0.7.0-20261123-031122 (A48 (b), A74
    lagi); grup 2 0.7.0-20261123-103915; grup 3 0.7.0-20261123-140004 (608 offline, 125 live
    OK, listing +0.10%). Uji skenario grup 3 lolos semua, sekali terhenti oleh batas
    pemakaian akun, dilanjutkan dengan --resume.
  - Keputusan run (bukan owner) ada di tiap item sebagai baris "Decided ... by the run";
    yang di luar item: tes per grup oleh subagen Sonnet, push/registrasi/tag/page oleh sesi
    utama; resep dan A75 dikerjakan lebih dulu saat Altium terblokir; uji skenario grup 2
    dan 3 dimulai di bawah 1,5 GB memori bebas karena sisanya dipakai sesi Claude lain milik
    owner; A77 jadi item baru di grup 3, bukan A45 diulang.
  - Untuk owner: A1, A2, A7 menunggu PR upstream (belum dikirim); A11, cek ECO manual di
    bench (lihat itemnya); update ad25 ke upstream/main, keputusan owner di sesi sendiri;
    A73 (ukuran deskripsi tool) dan A60 (b) untuk run berikutnya.
  - Pertanyaan hook yang tidak ditanyakan: catatan `core` soal pindah sesi (pertanyaan owner
    soal pekerjaan yang sedang jalan); tidak ada pertanyaan timer, commit atau PR.
