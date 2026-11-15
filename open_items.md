# Open Items

What sessions found in this fork's server and what was decided about each, A-numbered.
The raw entries are in [`findings.md`](findings.md); this file holds the items. Each item
names where it goes: **upstream** (an issue or PR at `coffeenmusic/altium-mcp`), **local**
(a fix on `ad25`, sent upstream as a PR when it is general), **usage** (a note for the
sessions that use the server), or **not taken**.

Two sections: **Open**, not yet fixed; **Waiting**, fixed and not yet settled (a PR not
merged, a fix not yet run in a session), its status naming who proves it. An item merged
upstream, run and held, or decided against moves with its record to
[`closed_items.md`](closed_items.md), and so does a run's section once every step of it is
ticked. The layout is the `backlog` plugin's `format.md` (v0.1, since 2026-11-15).

**Open: A11, A15, A23, A25 to A28, A31 to A34, A36 to A39, A41 to A44.**

A2, A7, A4 and A6 went out together in `build-20261112-120520` (owner, 2026-11-12), so one
scenario test covers them; A3 and A8 were not waited for. That test ran and held for
all four (findings 2026-11-12, third entry). A live test uses the helpers in
`server/tests/live_altium.py` (`ALTIUM_LIVE=1`, the server's own tools, its own boards
closed unsaved). A board a test saves and reopens is a copy of an existing one: a new
document saved by script writes no file, and a net a script creates is gone after a save.
Altium's 16-layer example board is opened once per run at most: three opens filled its
memory (findings 2026-11-12, second entry, 3 to 5).
After `run_drc` the focused document is its report: a script takes the board by
`PCBServer.GetPCBBoardByPath`, not `GetCurrentPCBBoard` (findings 2026-11-14, 1).
A script that opens a project does so with `GetWorkspace.DM_OpenProject(<path>, True)`
before its board: `Client.OpenDocument('PrjPcb', <path>)` put the board under Free
Documents. The DRC report is open under a `file:///` name, and
`Client.GetDocumentByPath` on its path returns nil (findings 2026-11-14, second entry, 5).

A17 and A18 went out together in `build-20261114-145312` (owner, 2026-11-14): one scenario
test covers both. That test ran and held for both (findings 2026-11-14, second entry).
A29 and A30 went out together in `build-20261115-114630` (owner, 2026-11-15): one scenario
test covers both. It ran, the second time from the start, and held for both (findings
2026-11-15, first entry); what it left is A31, A32 and A34.
A35, A13, A14 and A12 (group 4 of the run) went out together in `build-20261115-143551`
(the run, 2026-11-15): one scenario test covers them. It ran (stopped once by the usage limit
and resumed) and held for A35, A13 and A12, and for A14 but its priority (findings
2026-11-15, second entry); what it left is A37 to A39.
A40 and A8 (group 5 of the run) went out together in `build-20261115-172812` (the run,
2026-11-15): one scenario test covers them. It ran once, not stopped, and held for both
(findings 2026-11-15, third entry); what it left is A41 to A44, and A26 met again.

A10 to A16 come from a review of the tools against a whole design flow (schematic and
missing library parts, ERC; a board with its rules and layer stack; placement; routing,
DRC; fabrication outputs for an assembly service), not from a session's entry: what the
flow needs that no tool does (2026-11-12). They are features, not faults.

## Open

### A11 - No tool to update the board from the schematic - OPEN 2026-11-12

No Update PCB Document (ECO):
parts and nets reach a board only through Altium's menu, and so does a schematic change
made after layout. Local: find a way that works from a script (the process with its
parameters, or the ECO through the API; A8 found a process call that returned success and
did nothing), then a tool that returns what was added, changed and removed, and what could
not be (a footprint not found).
Probe 2026-11-14 by the run, in AD25, on a project made by the tools (copies of the
SpiritLevel-SL1 example's libraries, three parts on a sheet, a new board): no script call
and no process parameter runs the ECO without its dialog. `WorkspaceManager:Compare` with
`ObjectKind=Project|Action=UpdateOther|Index=1` (the schematic in front) or
`ObjectKind=Project|Action=UpdateMe` (the board in front, Import Changes; the menus' own
parameters, read from `advsch.rcs` and `AdvPcb.rcs`) opens the modal Engineering Change
Order dialog (`TChangeManagementForm`) and `RunProcess` returns once it is closed; with
nothing to change a `TMessageForm` "Comparator Results (No Differences)" comes instead.
`Silent`, `NoDialog`, `SilentCompareMode`, `SilentMode` and `Execute` set to True changed
nothing. `IProject.DM_ExecuteChanges`, `DM_GetDocumentForECO` and
`IWorkspace.DM_ExecuteChanges` (names in `WorkspaceManager.dll`) are undeclared in
DelphiScript. The dialog's list is a `TdxTreeList`, not readable from outside. What
works: its buttons (`TXPBitBtn`) take a posted click, as A21's: Validate Changes or Execute
Changes, then Report Changes opens a `TReportPreviewForm` whose Export... gives a Save
dialog (`#32770`, Excel first of eight types; choosing another type by message did not
take), and the `.XLS` written is Altium's list (Action, Object, Change Document, Status
with Altium's message, e.g. "Footprint Not Found NO_SUCH_FP", empty when good), the same
after Validate as after Execute. Executing writes `Project Logs for <project>\<project>
PCB ECO <date>.LOG` beside the project. A tool on this (`update_pcb_from_schematic`,
`dry_run` default true, the board read before and after) was written with offline tests
(17 in `tests/test_eco.py`) and a live test (`tests/test_live_eco.py`, failing before the
tool: "AttributeError: module 'main' has no attribute 'update_pcb_from_schematic'"), not
committed. Stopped: Altium then fell into a loop of `TShowException` "COM object that has
been separated from its underlying RCW cannot be used" (closed about 280 times, back
within 0.6 s each; Altium left so, not restarted), first met when a new project was made
while another project the ECO dialog had worked on was still open; the same error had come
once before at that point and gone.
Whether the dialog driven by script causes it is not known yet: next, with Altium
restarted, the live test alone, then whether the ECO done by hand does the same.
Second try, 2026-11-14, Altium restarted by the owner. Two faults found and fixed in the
tool: run from the bridge, the process answered a `TMessageForm` "Error" "No top level
document to compare with" instead of the dialog, because the board focused by
`DM_OpenAndFocusDocument` does not focus its project (`GetWorkspace.DM_OpenProject(<path>,
True)` first, then the project compiled, cured it); and the Save dialog's file name box,
set before the dialog had put its own name in it, was overwritten once (the report not
written), so Save is now pressed only when the box reads the path back (`WM_GETTEXT`). A
third: after a validation that met a footprint not found, Altium answers the first board
then added to a project (`add_project_document` with `create`) with a `TMessageForm`
"Information" "File Not Open" (one OK), which held that call until the bridge gave up
(120 s) and stayed open. It came as well with only Validate and Close pressed (no report,
no export), so it is Altium's own after a validation; a later board did not get it, and a
real run with no validation before did not cause it. `add_project_document` was given a
watcher that presses OK on such a message and lists it. With these the live test passed
3/3 twice in a row in one Altium (dry run, real run read back, no differences, a part
removed and a net renamed, a footprint not found and the next board's message answered,
refused calls), and 19 offline tests in `tests/test_eco.py`. Then
`test_live_project_setup` was started for the tools touched (`other_utils.pas`,
`add_project_document`); it was stopped by Claude Code for low memory after a first
failure, and the RCW error form came back on the owner's screen ("COM object that has been
separated from its underlying RCW cannot be used", "Send and Close", over a schematic
sheet), the second time after ECO runs, as the first time when new projects were then
made; Altium needed a restart again.
Decided 2026-11-14 by the run, not the owner: A11 left Open after two tries, because the
RCW error came back after the ECO both times and Altium needed a restart each time; its
code is kept in the stash named below, not committed.
Stash: "A11 ECO tool, not working (RCW error after ECO)",
`c15f30f0de547aae02d4999c19f14170b2da3340` (`server/eco.py`, `server/tests/test_eco.py`, `server/tests/test_live_eco.py`, and the
changes to `server/main.py`, `server/AltiumScript/other_utils.pas`,
`server/AltiumScript/Altium_API.pas`, `.github/workflows/tests.yml`). Next: whether the
ECO done by hand (Import Changes, Validate, Execute, Close), then new projects made, brings
the RCW error too; if it does, it is Altium's, and the tool may go in with a usage note.

### A15 - Parts come from local `.SchLib` and `.PcbLib` files only - OPEN 2026-11-12

`build_schematic` and
`edit_schematic`'s `place_component` need a `.SchLib` path (`.IntLib` is not supported); a
`.DbLib` can be searched only through `dev/db_search.py`, not a tool; nothing searches
Altium's Manufacturer Part Search, a content vault or a supplier's catalogue (LCSC and
others), so no supplier part number is filled in. A missing part is drawn from its
datasheet with the symbol and footprint tools, unchecked against a vendor's model. Local:
`.IntLib` parts in `build_schematic`, the DbLib search as a tool, a supplier lookup that
fills the part number parameters, and an import of a vendor's downloaded symbol and
footprint worth a look.
Split 2026-11-15 by the run: `.IntLib` parts in `build_schematic` and `place_component`
and the DbLib search as a tool are done, as A40 (A15 (a)) in Waiting. What stays Open here
is A15 (b): the supplier lookup that fills the part number parameters (Altium's
Manufacturer Part Search, a content vault, a supplier's catalogue such as LCSC's) and the
import of a vendor's downloaded symbol and footprint. Not in the run of 2026-11-14 by its
plan: an outside service and its terms are the owner's call.

### A23 - `get_unrouted_connections` read by net names no pad - OPEN 2026-11-14

With `nets` only, the
connections come with `from_pad` and `to_pad` null even where an end is a pad's centre;
the same connection read with `designators` names both ends. As the description says
(pads are named with `designators`), but a caller reading by net needs a second call to
know the pads. Local: name a pad whenever an end lies on one, whatever the group was given
by; or, the smaller change, a line in the description. Usage until then: read with the
net's `designators` to get the pads. (2026-11-14, fourth entry, 4.) Not in the run of
2026-11-14's later groups (not in their files): for the next run.

### A25 - `set_board_shape` on a board just made: Altium's region of the outline is wrong - OPEN 2026-11-14

On a board made by `add_project_document(create=True)` (origin at absolute 0, 0) the call
returned the outline and box asked, `get_board_summary` agreed and the board was drawn
right, but `AreaSize` read 1486.6 mm² for a 50 × 40 mm shape with one 5 mm rounded corner
(expected 1994.6), and `PointInPolygon` was false at two points inside and true at one
outside; a plain rectangle next gave 2200 mm² for 2000. `Board.UpdateBoardOutline` again
from a script changed nothing; after save, close and reopen the region was right, and
later calls on that board too. A10's live test checked `PointInPolygon` on a copied board,
not a new one. Reported success with a wrong result: anything reading the board's region
in that session (a pour, a DRC check against the outline, a placement test) may see a wrong
shape. Local: reproduce in a live test on a new board, then a fix (the region rebuilt, or
the board saved and reopened by the tool), or the call refused or flagged on a board never
saved. Usage until then: save, close and reopen a new board before setting its shape is
relied on. (2026-11-14, fifth entry, 2.) For the next run.

### A26 - `build_schematic` leaves the focused project modified, and puts its sheet in it - OPEN 2026-11-14

With
another project in focus, `build_schematic(project_path, sheet_path)` took its sheet back
from that project (`project.detached_from` names it) but left that project's file flag set:
unmodified before, modified after, twice in a row (its file not written);
`add_project_document(create=True)` in the same state puts the flag back. In the same
result the top-level `detached_from` is `""` while the nested one names the project, and
`sheet` gives the unsaved name (`Sheet1.SchDoc`) where `sheet_path` gives the file saved.
Local: the flag put back as `add_project_document` does, one `detached_from`, and `sheet`
the saved name. (2026-11-14, fifth entry, 3 and 6.) For the next run.
Possibly met again (2026-11-15, second entry, 8): at the start of a session Altium had a
project focused with its flag set and a `Sheet1.SchDoc` in it with no path (not open, not on
disk), the file on disk unchanged; nothing in that session made it, and the source is not
known (a new sheet taken into the focused project by an earlier call or live test).
Met again and widened (2026-11-15, third entry, 3): without `project_path`, where the
description promises a new free document, the new sheet (`Sheet1.SchDoc`, no path) went into
the focused project and set its flag, `success` true, `detached_from` `""`; with
`project_path` and a part missing the call failed and the unsaved sheet stayed in the focused
project with its flag set, not mentioned. That is where the `Sheet1.SchDoc` above came from.
Local, besides the above: the sheet in no project without `project_path`, taken out again
after a failure, and the focused project's flag as found in all three cases.

### A27 - `build_schematic` with `footprint` on a symbol that has a current one gives two - OPEN 2026-11-14

A part whose library symbol already has a current footprint, placed with `footprint`, gets
the named model added (by name, no library) as current while the library's current one
keeps its mark: two current PCB footprints (`IsCurrent` 1 on both through the API,
`ISCURRENT=T` twice in the saved sheet). Rare before A16, now the common case. Reported
success. Local: the footprint given becomes the only current one, its mark moved when the
symbol already has a model of that name. (2026-11-14, fifth entry, 5.) For the next run.

### A28 - No tool makes an empty library - OPEN 2026-11-14

`create_symbols_batch`'s `LIBRARY` needs an
existing `.SchLib` and `add_project_document`'s `create` makes sheets and boards only, so
a new `.SchLib` or `.PcbLib` is made by script (`CreateNewDocumentFromDocumentKind`,
`DoSafeChangeFileNameAndSave`, then `SetModified(True)` and `DoFileSave('')`), and it went
into the project in focus, as A10's probe found for a sheet. Local: `create` for `.SchLib`
and `.PcbLib` in `add_project_document`, or a library made by the symbol and footprint
tools when missing. (2026-11-14, fifth entry, 7.) For the next run.

### A31 - A22's guard misses a call that starts with no window in front - OPEN 2026-11-14

`ForegroundGuard`
keeps nothing when `GetForegroundWindow` is 0 at the start, so for that whole call Altium
is never sent back: in the scenario test of `build-20261114-225815` it took the foreground
in the middle of a `run_altium_script` (its recovery's `-REditScript:Stop`) and kept it 4
minutes, and every call after found Altium in front and left it there, by design. The 0
came from the server's own path: a probe launch refused by a busy Altium raised its
"Information" box, the guard gave the foreground back, then the box was closed and the
foreground fell to no window (15 s, 15 s, 31 s). Also, a `run_altium_script` that closes one
project and opens another left Altium in front about 3.4 s, 2.75 s of it with no foreground
event (only a 20 ms poll saw it); the same open without the close, 7 ms. Local: keep the
last window that was not Altium's (from the previous call) when the start reads 0, give it
back once more after a box the server closes, and a poll beside the events while a call
runs; a live test for each. (2026-11-14, sixth entry, 2 and 3.) For the next run.
Met again in the scenario test of `build-20261115-114630` (2026-11-15, first entry, 2 (a)
and 3): the resident bridge's start kept Altium's main window in front about 1.5 s, and a
`run_altium_script` closing one project and opening another 2.9 s (the closing script
1.6 s), each with no foreground event, seen by the poll only.

### A32 - `run_altium_script` answers Altium's messages its own way - OPEN 2026-11-14

A24's rule (a message
with choices is left open and named, a call made while one is open is not run) does not
reach `run_altium_script`: (a) a script's own `MessageDlg` with Yes and No is closed after
6 s with `WM_CLOSE`, the script gets 2 (Cancel, not one of its buttons), and the call
reports `success` true, only `dialogs_dismissed` 1 and a picture saying so; (b) a call
made while such a message is open is launched anyway and closes it the same way, the
earlier script running on with that answer, while the call itself reports "Altium never
started the script: a script of ours was stuck and has been stopped", `recovered` true.
Also (c), with a timeout shorter than a message's wait it returned after about 55 s "The
debugger has been stopped, so it is no longer running", `executor_wedged` true, the message
not named, while the script still waited on it and ran to its end once it was closed. Local:
`run_altium_script` follows A24's watch and refusal (and A29's tool), and says a script
waits on a message when it does. (2026-11-14, sixth entry, 5 and 6.) For the next run.
Met again, unchanged, in the scenario test of `build-20261115-114630` (2026-11-15, first
entry, 4): (c) as above, about 55 s, six busy boxes raised by its probes, the message left
open. Also (d) (same entry, 6): `answer_altium_message` on the message such a script left
open gave `outcome` "no_command_waiting", its note guessing a script of the user's own; it
was this server's, its call already ended with "no result", and the script's own answer
is read by no one. The note could say so when the window is a `run_altium_script`'s.

### A33 - An OK-only message open before a bridge call is neither pressed nor named - OPEN 2026-11-14

The
check before the launch lets a lone OK through (leaving it to the watch), Altium refuses
the launch as busy (a modal "Information" `TMessageForm` over the message), and the watch
never runs, as it starts only once the command has started: `get_board_summary` ended after
46 s with "Altium did not start the command (not executed). A script of ours was stuck in
Altium's debugger…", two boxes left open. A click posted to the message did nothing while
the busy box was over it; the busy box first, then the message, closed both. Local: before
the launch, press a lone OK (the topmost box first) and say so, or refuse naming it, as for
a message with choices; a live test with an OK message left open by a script. (2026-11-14,
sixth entry, 7.) For the next run.

### A34 - Small points left by the resident bridge and the message tool - OPEN 2026-11-15

From A30's work
and the scenario test of `build-20261115-114630` (2026-11-15, first entry, 2, 3 and 5).
(a) Moved to Waiting (2026-11-15, the run): the resident's tag hashed from the text after
the CRLF step; it is item A35 there.
(b) Calls the resident served still brought Altium in front briefly, each given back by
A22's guard: the first `get_board_summary` after the start, 25 ms (the same call again:
never; a guess, the board brought to view the first time a tool uses it), and after
`answer_altium_message` pressed a button, the resident form then the main window, about
10 ms (closing the modal hands activation to Altium's next window, the form first).
(c) `answer_altium_message`'s picture of a `MessageDlg` cuts its buttons at the bottom.
(d) `run_altium_script` is not served by the resident, each call still a launch (its
description still says `RunScriptFile`); A30 did not say whether that is meant: to
decide, with A31 and A32.
(e) A resident project of an earlier build (another tag, no live form) stays listed in
Altium's Projects panel (2026-11-15, second entry, 1): closing a resident could close its
project too. Local. For the next run.
(e) met again (2026-11-15, third entry, 8): two resident script projects of different tags
open in one Altium.

### A36 - A board open under its short (8.3) path is opened a second time - OPEN 2026-11-15

A tool given a
`board_path` in the short form (`C:\Users\ABCDEF~1\...`) while that board is open under it
opens the file again: `long_path` turns the path into its long form and `FocusBoardByPath`
then does not find the open document by it, so the call works on a second copy while the
first keeps its own state. Met by the run while building A13 (2026-11-15); A13's live test
opens its copies by the long path, as `test_live_project_setup` does. Local: compare
documents by one form of the path (both made long, or Altium's own name read back), and a
live test that opens a board by its short path and then calls a tool with that path. For
the next run.

### A37 - `set_pcb_layer_stackup`'s dry run leaves out the existing dielectric's changes - OPEN 2026-11-15

The 4-layer preset's dry run on a 2-layer board listed in `would_change` only the outer
coppers' thickness (1.4 to 1.378 mil); the call then reported `changed` 15: the existing
core became the top prepreg (type, material, height 60 to 7.874 mil, constant 4.8 to 4.4)
and the new layers' values were set. A dry run that understates what the call does to an
existing layer. Local: `would_change` lists every value the call will write, the kept
dielectrics' included, and the new layers' values under `would_add`; an offline test on that
plan. (2026-11-15, second entry, 3.) For the next run.

### A38 - A rule priority set by the tools is not what `run_drc` uses until the board is reopened - OPEN 2026-11-15

`create_pcb_rule`'s `priority` and `create_pcb_rules_preset` order the rules by
adding at 1 and removing and adding again (A14); `get_pcb_rules`, the iterator's `Priority`
and `FindDominantRuleForObject` all give the order asked, but the batch DRC in the same
session checks by the order the rules were added, the last added winning: a via ring rule
put at 2 by the preset gave 14 violations where the rule at 1 dominates every via, 0 after a
save, close and reopen; a rule then made at the lowest priority gave 17 violations of it.
Reported success with a wrong result for any check run before a reopen. Local: find the
Altium call that refreshes the rule order (or what the rules editor does on OK), else the
tool saves, closes and reopens the board, or refuses `priority` other than 1 and says so;
a live test with a DRC after the move that fails today. Usage until then: save, close and
reopen the board after setting a priority or a preset, before `run_drc`. (2026-11-15,
second entry, 5.) For the next run.

### A39 - `write_outjob` and `set_pcb_layer_stackup` return more than a check needs - OPEN 2026-11-15

Every
`write_outjob` returns the whole read of the file, about 10k characters, 7k of them the
Gerber's 55 plotted layers one by one (the preset plots every copper layer), an edit of two
settings the same 10k; `set_pcb_layer_stackup` returns `requested` and `stack` both, 3 to 5k
for a 2- or 4-layer board. Local: a summary (plotted layers as "every copper layer" plus the
others by name; the stack only where it differs from what was asked) with the full read
behind a flag. (2026-11-15, second entry, 7.) For the next run.

### A41 - `make_pcblib_from_board` loses the footprints' descriptions - OPEN 2026-11-15

Six of the twelve
components of a 2-layer board carry a footprint description
(`IPCB_Component.FootprintDescription`), and the library Altium's menu makes from that board
keeps them; in every library the tool made, read back with `get_footprint_primitives`, every
description is empty, and `problems` stays [] because the comparison checks patterns and pads
only. Reported success with less than the board has. Local: find where they are lost (the
hidden run, the filter or the save), give each footprint the board's description before the
save, and compare descriptions too; a live test that fails today. (2026-11-15, third entry,
5.) For the next run.

### A42 - `edit_schematic` that applies nothing leaves the sheet modified - OPEN 2026-11-15

With only a
`place_component` whose symbol is not in the `.IntLib` (`applied` 0, `saved` false) the sheet
was left marked modified, nothing on it changed. Also seen: a part placed from a `.SchLib` is
saved with library name, library path and target file name `*` and no Design Item ID, where
an `.IntLib` part (A40) is linked to its library, so the two ways differ. Local: the sheet's
flag put back when no operation applied; the `.SchLib` link worth a probe (what Altium's own
placement from a `.SchLib` stores). (2026-11-15, third entry, 6.) For the next run.

### A43 - `search_dblib` warns of `max_rows` at exactly `max_rows` matches - OPEN 2026-11-15

With 20 matches
and the default `max_rows` 20 it says a table reached max_rows (20) though there is no 21st;
every reply repeats the `tables` list (about 0.3k characters), and a search of 20 matches is
8k. Local: fetch one row more to tell; the tables list once, or only when asked. (2026-11-15,
third entry, 7.) For the next run.

### A44 - A live test leaves a temporary `Parts.SchLib` open in Altium - OPEN 2026-11-15

After the release's
live tests a `Parts.SchLib` from a live test's temporary folder was still in Free Documents.
Local: find the test (those that build a `.SchLib`) and close the library in its tear-down,
so a scenario test starts from a clean Altium. (2026-11-15, third entry, 8.) For the next
run.

## Waiting

### A1 - `get_server_status` reports no version or commit - BUILT 2026-11-12, proof: the upstream PR for the version part, not sent yet

It returns the Altium exe and the
script path only, so a result cannot be tied to the code that ran. Until fixed, the release
folder in `script_path` names the stamp, and its `BUILD.txt` the commit (`CLAUDE.md`,
*Release and run*). Local: add the `manifest.json` version and the content of `BUILD.txt`
when present; upstream PR for the version part.
Fixed in `e2ecb5c`: the status adds `version` and `build` (the `BUILD.txt` line, `null` in a
checkout); offline tests in `test_build_info.py`. Released in `build-20261112-101037`.
Scenario test of that build held (2026-11-12, 1): `version` 0.7.0, `build` equal to the
release folder's `BUILD.txt`, `script_path` in the same folder. Waits for the upstream PR
for the version part.

### A2 - `get_pcb_layer_stackup` reports success with the dielectrics missing - BUILT 2026-11-12, proof: the upstream PR, not sent yet

On a 2-layer
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
Released in `build-20261112-120520`. Scenario test of that build held (2026-11-12, third
entry, 1): mask 0.4 / copper 1.4 / core 60 (FR-4, er 4.8) / copper 1.4 / mask 0.4,
`total_thickness_mils` 63.6, `dielectric_layers` 3, as a `LayerStack_V7` walk gives.
Waits for the upstream PR.

### A7 - `get_pcb_rules` repeats each rule's scope - BUILT 2026-11-12, proof: the upstream PR, not sent yet

9.3k characters for 38 rules, the scope
given in `descriptor` and again in `filter1`/`filter2`. Local: one of the two, and upstream
PR. (2026-11-12, 6.)
Fixed in `c011483`: `descriptor` is given as `constraint`, the scope cut from its end
(kept whole when it does not end in the filters), and `filter2` is left out of a unary
rule (`IPCB_Rule.IsUnary`; AD25 reports the Fanout rules binary). Offline tests in
`test_pcb_rules.py`; live test `tests/test_live_pcb_rules.py` (a new board's default
rules): 1/1 pass in AD25, fails on the old script. Released in `build-20261112-120520`.
Scenario test of that build held (2026-11-12, third entry, 2): 38 rules, the scope once,
`filter2` only on binary rules. The reply went from 9.3k to 8.5k characters only (about
9 %): what is left is mostly the key names and indentation repeated on every rule.
Waits for the upstream PR.
