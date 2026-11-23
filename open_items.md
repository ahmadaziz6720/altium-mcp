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

**Open: A11, A15, A23, A25, A31 to A34, A36 to A39, A42 to A44, A47, A48, A51 to A54, A59 to A65, A67 to A69, A72, A73, A76, A79 to A87.** The run
of 2026-11-22 is done (2026-11-23): its section, every step ticked and its report the last
step's lines, moved to `closed_items.md`; its open leftovers filed as A82 to A87. Sorted
2026-11-23, the fourth entry of 2026-11-23 (the scenario test of group 3's build,
`build-20261123-140004`): A57, A66, A41, A70, A28, A77 and A78 held and closed; A60 (a)
held, A60 open for (b); A79, A80 and A81, new, out of the run, for the owner. Sorted
2026-11-23, the third entry of 2026-11-23 (the scenario test of group 2's build,
`build-20261123-103915`): A46, A58, A45, A26, A27, A71, A56 and A75 held and closed, A55
closed as usage; A77 and A78, new, taken into group 3; A61, met again; A34 and A52,
checked. Sorted 2026-11-23, the second entry of 2026-11-23 (the scenario test of group
1's second build, `build-20261123-031122`): A74 held and closed; A48 (b) checked, the part built held and the
rest still open; A76, new, not taken into the run; A34, met again. Sorted
2026-11-23, the entry of 2026-11-23 (the scenario test of group 1's build,
`build-20261123-001227`): A49 and A50 held and closed; A48 back to Open, held for edits and
not for objects a script removed, taken again as A48 (b); A74 and A75, new; A26, A34 and
A44, met again. Sorted 2026-11-22, the entry of 2026-11-22 (token cost of seventeen design sessions): A49, A46, A58
and A57, met again, the four where the server's results weigh most. Sorted
2026-11-22, the eighteen entries of 2026-11-18 to 2026-11-20 (schematic and library work on
`build-20261115-172812`): A45 to A72, new; A34 (f), a new part; A26 and A28, met again. Most
of the new items are tools missing for schematic and library work; those that report success
with a wrong result are A45, A48, A50, A66 and A71, and A63 (c) and A64 (a) lost work
silently.

The owner, 2026-11-22, on the items above: "gw gamau bikin fitur tapi terus2an dan konsumsi
token tambah gede" (no stream of features that keeps growing token use). Every tool and
argument is sent in every turn of every session that loads the server, so a new one costs
for good, used or not. Proposed in that session, not decided: first the items that report
success with a wrong result or lose work (A45, A48, A50, A66, A71, A63 (c), A64 (a)) and
those that shrink a result (A49, A46, A57); most "no tool for X" items (A47, A59, A62 to
A65, A69 and the like) to usage notes on how the script does it, or not taken, a few at
most as ops on an existing tool. For `get_erc_violations` (A49, A50), no new argument: the
result grouped by type with a count and two or three details each, the full list left in
the file it already writes, and the suppressed ones counted apart (`suppressed: n`).
Upstream's `get_erc_violations` is the same code as `ad25`'s: both faults are upstream's.

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
Closing Altium is not free of writes: a restart with nothing modified wrote a generated
`.PrjPcbStructure` again and touched other generated files, so a restart hashes the open
projects' files before and compares them after (Run 2026-11-22).

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
Run 2026-11-22 left this check to the owner (its *For the owner, prepared*): it is done by
hand at Altium, not by a run's step.

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
(f) No tool stops the resident bridge on purpose, so the owner can use Altium (a library
search, a vendor's library loader) between sessions. Sorted 2026-11-22 out of five entries
on build `0.7.0-20261115-172812`: 2026-11-19, sixth entry, point 1; seventh, point 7;
eighth, point 6; ninth, point 1; 2026-11-20, point 7. Each time the session wrote the `stop`
file by hand into `resident\<tag>\`, as the README describes for a resident of another
build; an `EnumWindows` search for a window titled `altium-mcp resident` found none 3 s
later. The `stop` file stays in the folder, and the next call started the resident again
without a problem. Local: a `stop_resident` tool (or a `get_server_status` option) that
closes it and reports it gone, or at least a line in `get_server_status`'s description
saying how. Not decided.

Decided 2026-11-22 by the owner (the opening answer of `## Run 2026-11-22`), for (f) only: no tool; written as a recipe in `docs/recipes.md` (a DelphiScript a session proved, with its `run_altium_script` call), pointed to by one line of `run_altium_script`'s description, and closed as usage once the scenario test held for the file. A record with no proven script leaves the item Open.
Met again 2026-11-23 (findings 2026-11-23, point 7), build `0.7.0-20261123-001227`, (e): at
the start of its scenario test the Projects panel held two `MCPResident.PrjScr`, this
build's and an earlier tag's.
Met again 2026-11-23 (findings 2026-11-23, second entry, point 6), build
`0.7.0-20261123-031122`, a small point beside (e): after the test's projects were closed by
script, the focus was left on the resident's own `MCPResident.PrjScr` (Free Documents at
the start, the resident not yet started), which a call without `project_path` would take.
Seen in a workspace read, no tool called so.

(f) written 2026-11-23 in `docs/recipes.md`, marked *No script*: the `stop` file in each
resident's folder, as the sessions did by hand and as `test_live_resident`'s
`stop_all_residents` does. Not run today.
Decided 2026-11-23 by the run, not the owner: (f) written as that file step, not as a
DelphiScript, because no session ran a script for it and the step needs none. A34 stays
Open for its other parts; what is left of (f) is the scenario test of that step.

Checked 2026-11-23 by the run's check: its recipe in docs/recipes.md ran as written in the scenario test of build 0.7.0-20261123-103915 (findings 2026-11-23, the group 2 entry, point 10): A34 (f): the stop file closed the form within about 7 s and the next call started it again.

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
Met again 2026-11-23 (findings 2026-11-23, point 7), build `0.7.0-20261123-001227`, in
kind: at the start of its scenario test the project in focus, not a test project, held three
`PCBn.PcbDoc` with no path, unsaved: a live test made boards while that project had focus.
A live test leaves boards behind as well as a library.

### A47 - No tool sets a sheet's size, title block or document parameters - OPEN 2026-11-22

Sorted out of the entries of 2026-11-18 (second), point 5, and 2026-11-19 (twelfth), point
5. `build_schematic` makes the sheet in Altium's default size; the size (`SheetStyle`) and
the document parameters (Title, DocumentNumber, Revision) went through `run_altium_script`,
one call per sheet (9 in one session). A lesson met on the way: names and values read from
one `TStringList` (`Names`, `ValueFromIndex`) failed with "Could not convert variant of type
(OleStr) into type (Double)"; two lists by index worked.

Proposed: local; `sheet_style` and `parameters` on `build_schematic`, and an
`edit_schematic` op for an existing sheet. Not decided.

Decided 2026-11-22 by the owner (the opening answer of `## Run 2026-11-22`): no tool; written as a recipe in `docs/recipes.md` (a DelphiScript a session proved, with its `run_altium_script` call), pointed to by one line of `run_altium_script`'s description, and closed as usage once the scenario test held for the file. A record with no proven script leaves the item Open.

Not written 2026-11-23, still Open: the record holds no script a session proved, only the
calls (`SheetStyle`, the parameters by an iterator, two lists by index). Missing: the
script that sets a style and the parameters, run and read back from the saved sheet.
`test_live_compile_refresh` has a script setting `UseCustomSheet` and `CustomX/Y` to 2000,
not taken as a recipe: it sets no style and no parameter, saves nothing, and its check
(over 100 objects out of bounds) passes whatever unit the 2000 is in.

### A51 - `build_schematic`'s net labels take no justification - OPEN 2026-11-22

Sorted out of the entry of 2026-11-18 (second), point 8: every sheet's labels went in a
second call through `edit_schematic`'s `add_net_label`.

Proposed: local; a `justification` key on `net_labels`. Not decided.

Decided 2026-11-22 by the owner (the opening answer of `## Run 2026-11-22`): no tool; written as a recipe in `docs/recipes.md` (a DelphiScript a session proved, with its `run_altium_script` call), pointed to by one line of `run_altium_script`'s description, and closed as usage once the scenario test held for the file. A record with no proven script leaves the item Open.

Written 2026-11-23 in `docs/recipes.md`, marked *No script*, still Open: the way the record
proved is a tool call (`edit_schematic`'s `add_net_label` with `justification`), and the
decision asks for a script. Missing: such a script, proved, or a decision that the tool
call is enough to close it as usage.

### A52 - No tool takes a sheet out of a project, so a sheet cannot be built again in place - OPEN 2026-11-22

Sorted out of the entries of 2026-11-18 (second), point 10, and 2026-11-19 (thirteenth),
point 3. No tool removes a document from a project or deletes its file: a sheet rebuilt from
scratch needed `run_altium_script` (`DM_RemoveSourceDocument`, `DeleteFile`) 3 times, and a
removal by script once left two `[DocumentN]` sections for one sheet (A26's line of
2026-11-18). `build_schematic` refuses an existing path; the workaround held: every object
removed by script (title block parameters and notes kept), then the sheet placed again by one
`edit_schematic` call of 209 operations.

Proposed: local; `build_schematic` with `replace: true` on a sheet of the project, keeping
its sheet style and parameters, and a remove in `add_project_document`. Not decided.

Decided 2026-11-22 by the owner (the opening answer of `## Run 2026-11-22`): no tool; written as a recipe in `docs/recipes.md` (a DelphiScript a session proved, with its `run_altium_script` call), pointed to by one line of `run_altium_script`'s description, and closed as usage once the scenario test held for the file. A record with no proven script leaves the item Open.

Written in part 2026-11-23, still Open: `docs/recipes.md` has the one removal script
proved, `remove_by_script` of `test_live_compile_refresh` with its
`SCHM_PrimitiveRegistration` (A48 b): the last no-ERC marker or part of a sheet, one per
call. Missing, each with only its calls in the record: a script that clears a whole sheet
keeping its parameters and notes (the workaround that held), and one that takes a sheet out
of its project and deletes its file (`DM_RemoveSourceDocument`, `DeleteFile`; a removal by
script once left two `[DocumentN]` sections, A26).

Checked 2026-11-23 by the run's check: its recipe in docs/recipes.md ran as written in the scenario test of build 0.7.0-20261123-103915 (findings 2026-11-23, the group 2 entry, point 10): A52: the no-ERC marker removed, the next compile dropping it.

### A53 - `run_altium_script`'s lint refuses scripts that run - OPEN 2026-11-22

(a) 2026-11-18 (second), point 11, and 2026-11-19 (fifth), point 6: a nested `procedure`
with its own `var` block is refused ("'X' is not declared"), the lint reading only the
leading block (declared globally, Altium itself refuses `procedure`: "Unknown identifier").
Workaround: every variable in the leading block, the procedure inlined.
(b) 2026-11-19 (fourteenth), point 2: a script opening several sheets in turn, its groups
balanced at run time, refused with "1 PreProcess but 2 PostProcess call(s)": the lint
counts calls in the text. `skip_lint=True` ran it, no group left open.
A9 (closed) was another declaration fault of the same lint.

Proposed: local; each procedure's `var` block read; for (b), refused only when the text has
fewer `PostProcess` than `PreProcess`; offline tests for both. Not decided.

### A54 - No tool returns the compiled netlist - OPEN 2026-11-22

Sorted out of the entries of 2026-11-18 (second), point 12, and 2026-11-19 (first), point 3:
checking a drawn schematic against its source table needed the nets with pin number and
name, done in each session by `run_altium_script` (`DM_Compile`, `DM_DocumentFlattened`,
`DM_Nets`, `DM_Pins`) saved to a file.

Proposed: local; a read of the flattened netlist (net, designator, pin number, pin name), to
a file when large. Not decided.

Decided 2026-11-22 by the owner (the opening answer of `## Run 2026-11-22`): no tool; written as a recipe in `docs/recipes.md` (a DelphiScript a session proved, with its `run_altium_script` call), pointed to by one line of `run_altium_script`'s description, and closed as usage once the scenario test held for the file. A record with no proven script leaves the item Open.

Not written 2026-11-23, still Open: the record holds no script a session proved, only the
calls. Missing: the script that walks `DM_Nets` and `DM_Pins` (pin number and name, saved
to a file), with how it brings a stale compile up to date first: a script's own
`DM_Compile` reads stale after a script's edit (A48). `test_live_multipart`'s compile
script lists designators only.

### A59 - No tool places sheet symbols, ports, harness connectors or signal harnesses - OPEN 2026-11-22

2026-11-19 (second), point 1, and (fourteenth), point 3: making a schematic hierarchical
(sheet symbols with entries, ports, harness connectors with entries, signal harnesses) went
wholly through `run_altium_script`, a data file per sheet read by one interpreter script (8
connectors, 14 harnesses, 14 ports, 9 sheet symbols in one session; 146 lines for three
sheets in another). `edit_schematic` has no op for any of them.
2026-11-19 (second), point 3: a signal harness from `SchObjectFactory(eSignalHarness,
eCreate_Default)` gets the smallest width; between two sheet entries the compile gave 7
fatal "Missing Harness Type on Signal Harness", every entry carrying every harness's
members; `LineWidth := eMedium` cured it there (but see A48 (c)). The scripts reported
success. API notes from the same entry, point 2: `ISch_HarnessConnector` has no `Side`
property; `Mirror` after registration sets the side, and the type label then needs
`IsMirrored := False`, `Justification := 0` and its `Location` set again.

Proposed: local; `edit_schematic` ops (or a tool) for these objects, the harness width set as
Altium's default. Not decided.

Decided 2026-11-22 by the owner (the opening answer of `## Run 2026-11-22`): no tool; written as a recipe in `docs/recipes.md` (a DelphiScript a session proved, with its `run_altium_script` call), pointed to by one line of `run_altium_script`'s description, and closed as usage once the scenario test held for the file. A record with no proven script leaves the item Open.

Not written 2026-11-23, still Open: the record holds no script a session proved, only the
calls and API notes (the interpreter scripts and their data files are not in it). Missing:
one script per object (sheet symbol with entries, port, harness connector with entries,
signal harness with `LineWidth := eMedium`), each run and its compile read after the
project was reopened (A48 c).

### A60 - `get_screenshot` cannot fit or zoom a schematic, nor show a library footprint - OPEN 2026-11-22

(a) `zoom_to` is for PCB only, and a sheet is captured at its current zoom, the bottom of an
A3 sheet cut: 2026-11-19 (second), point 6 (`Sch:ZoomFit` by script fitted it, `Sch:Zoom`
with `Action=Document` did not); (thirteenth), point 4 (`Client.SendMessage('SCH:Zoom',
'Action=Document', ...)` fitted it); (fourteenth), point 7; (fifteenth), point 5;
2026-11-20, point 3 (for parts: `Action=Selected` left the view where it was).
(b) 2026-11-19 (ninth), point 5: `view_type "pcb"` captured the project's `.PcbDoc` while a
`.PcbLib` was focused: no way to look at a library footprint.

Proposed: local; `fit` and `zoom_to` designators for `sch`, and a view of a `.PcbLib`
footprint by name. Not decided.

Decided 2026-11-22 by the owner (the opening answer of `## Run 2026-11-22`): (a) taken, a `sch` capture fitted to the sheet, no new argument (the run's plan: by default). (b) not in that run.

(a) BUILT 2026-11-23, proof: the scenario test. Cause, two: the capture kept the sheet's
zoom, and the capture itself was cut. Altium is system DPI aware (120 DPI, the main
monitor's); on a 96 DPI monitor its window is drawn at 125% and scaled down by Windows,
while `get_screenshot` measured the window per monitor and copied that many pixels: the
top-left 80% of the window, its bottom and right cut at any zoom. Probed on an A3 sheet:
`Client.SendMessage('SCH:Zoom', 'Action=Document', ...)`, `RunProcess('Sch:Zoom')` with
`Action=Document` and `RunProcess('Sch:ZoomFit')` all fitted the view alike, and the capture
still lost the sheet's bottom quarter; the whole window copied, the fitted sheet was whole.
That fits the sessions that found a fit by script did not help.
Fix: `TakeViewScreenshot` (`other_utils.pas`) fits a sheet in front (kind `SCH`) with
`Client.SendMessage('SCH:Zoom', 'Action=Document', 255, Client.CurrentView)` before the
capture; `get_screenshot` sends no designators for `sch` and answers `zoom_to` there with
`warnings: ["zoom_to is for PCB only; the sheet was fitted whole"]`; the capture measures
the window in its own DPI context (`GetWindowDpiAwarenessContext`), the size its pixels are
drawn at (2418 x 1308 here, was 1934 x 1046). No new tool or argument; the description and
the README's entry say the sheet is fitted whole. The tool listing 159,770 to 159,813
characters (+0.03%).
Decided 2026-11-23 by the run, not the owner:
- the capture measured in the window's own DPI context as well, not the fit alone, because with the fit alone the sheet stayed cut on this display and the result would not be true;
- the image returned at the size Altium draws it, not scaled to the monitor's, because it is the smaller change and keeps Altium's own pixels;
- the fit only for a sheet, not for a library in front, because the server refuses a `sch` capture of a library (A61's case).
Test before (`tests/test_live_screenshot_fit.py`, new: an example sheet copied, set to A3,
zoomed in twice by `SCH:Zoom` `Action=ZoomIn`; the whole sheet read from the image as its
black border closed on four sides in A3's proportion), 2 of 2 failed:
`test_a_sheet_zoomed_in_is_captured_whole`: "AssertionError: unexpectedly None : the
1934x1046 capture shows no closed sheet border: the sheet is cut";
`test_zoom_to_on_a_sheet_is_answered_with_a_warning`: no `warnings` in the result. After:
2/2, twice; `test_live_unrouted` 4/4 (the PCB capture, its view read from the image);
offline 608/608. (a) fixed in the commit that writes this paragraph. A60 stays Open for (b),
out of the run.

(a) built in build `0.7.0-20261123-140004` (tag `build-20261123-140004`), commit `4eef324`.

Held 2026-11-23: the scenario test of build 0.7.0-20261123-140004 (findings 2026-11-23, the group 3 entry, point 6): (a) held: a sheet zoomed in three times by `SCH:Zoom` `Action=ZoomIn`, then `get_screenshot(view_type="sch", zoom_to=[<a part>])`, gave the whole A4 sheet, its border and title block, in a 2418 x 1308 image of the whole window, the panels on the right not cut, and `warnings: ["zoom_to is for PCB only; the sheet was fitted whole"]`. A60 stays Open for (b).

### A61 - `edit_schematic` leaves Altium's focus or selection changed - OPEN 2026-11-22

2026-11-19 (eighth), point 1: `place_component` from a `.SchLib` left the focus on that
library; the next `get_screenshot(view_type="sch")` was refused ("Altium has a SCHLIB
document focused"), twice, each time one script of `Client.ShowDocument` on the sheet first.
Reported success. Near A26. 2026-11-19 (fifteenth), point 4: after `move_component` the last
part moved stayed selected, its handles in the next screenshot; harmless.

Proposed: local; the edit puts the sheet back in front and clears its selection. Not
decided.

Met again 2026-11-23 (findings 2026-11-23, the group 2 entry, point 6), build
0.7.0-20261123-103915: the same in `build_schematic`. After a build the focused project is
Free Documents, and the symbol library the build used, already open, is left in front,
where another project's board was before; a tool called without `project_path` next reads
Free Documents (`get_project_info` did). Not reported in the result. Local: the document
that was in front shown again at the end.

Decided 2026-11-23 by the run, not the owner: into A61, not a step of this run, because A61
is out of this run by the owner's choice of three groups and the point is the same fault in
another tool.

### A62 - No tool changes a project option - OPEN 2026-11-22

Sorted out of the entries of 2026-11-19 (second), point 9, and (fourteenth), point 5: the
project closed by script (`WorkspaceManager:CloseObject`, ObjectKind Project), its
`.PrjPcb` edited, and reopened by `get_erc_violations(project_path)`;
`Client.OpenDocument('PrjPcb', path)` in a script did not put it back in the workspace. The
file Altium writes is LF only; an edit that adds a CR leaves it mixed.

Proposed: local; a tool setting project options by key, closing and reopening the project
itself. Not decided.

Decided 2026-11-22 by the owner (the opening answer of `## Run 2026-11-22`): no tool; written as a recipe in `docs/recipes.md` (a DelphiScript a session proved, with its `run_altium_script` call), pointed to by one line of `run_altium_script`'s description, and closed as usage once the scenario test held for the file. A record with no proven script leaves the item Open.

Written in part 2026-11-23, still Open: `docs/recipes.md` has the proved open by path
(`DM_OpenProject`, `open_project` of `server/tests/live_altium.py`) and the record's steps
around it. Missing: a proved script that saves and closes the project without losing
unsaved work (the record names `WorkspaceManager:CloseObject` only; the live tests' closing
scripts discard changes), and a run showing that the reopened project has the option.

### A63 - No tool copies, deletes or extracts library parts - OPEN 2026-11-22

Met in seven sessions, all done by `run_altium_script`, build `0.7.0-20261115-172812`:
(a) an `.IntLib`'s sources extracted (`IntegratedLibraryManager.ExtractSources(path)`):
2026-11-19 (fifth), point 4; or its footprint read without Altium (its `PCBLib/0.pcblib`
stream, zlib, inflates to a whole `.PcbLib`): (ninth), point 2.
(b) a symbol copied between `.SchLib`s: `ISch_Component.Replicate` copies the parameters,
Comment, Designator and footprint model but none of its lines and pins; the script succeeded
and the copy was saved with 0 primitives, seen only in the inventory. Its children
replicated one by one held: (fifth), point 2; (seventh), point 6.
(c) a footprint copied between `.PcbLib`s with its embedded 3D body: held with
`CreatePCBLibComp`, `RegisterComponent` and each primitive `Replicate`d, moved by minus the
source's `Board.XOrigin`/`YOrigin`: (fifth), point 3; (seventh), point 5; (eighth), point 3;
(ninth), point 3. But in (twelfth), point 3 such a copy showed its primitives before the
save and none after, both runs reporting success; `create_footprints_batch` from the
source's dump, the STEP taken out of the source's embedded models, made it right.
(d) a symbol or footprint deleted (`RemoveSchComponent`, `RemoveComponent`, then `SaveDoc`):
(eighth), point 3; (tenth), point 5; (twelfth), point 2.
Bears on A15 (b) (a vendor's part imported) and A28 (a library made); neither covers these.

Proposed: local; tools to extract an `.IntLib`, copy a symbol or footprint (3D body
included) between libraries and delete one, and `get_footprint_primitives` taking an
`.IntLib` path. Not decided.

Decided 2026-11-22 by the owner (the opening answer of `## Run 2026-11-22`): no tool; written as a recipe in `docs/recipes.md` (a DelphiScript a session proved, with its `run_altium_script` call), pointed to by one line of `run_altium_script`'s description, and closed as usage once the scenario test held for the file. A record with no proven script leaves the item Open.

Not written 2026-11-23, still Open: none of (a) to (d) has a script a session proved in the
record, only calls. Missing: (a) a run of `ExtractSources` with its folder read back, (b)
the script copying a symbol and its children, (c) the footprint copy, with why it was lost
at the save in one of five sessions, (d) the two removals, each saved and read back, with
what notice a library's removal needs (A48 b's was proved on sheets only).

### A64 - No tool edits an existing footprint's primitives, pads or 3D body - OPEN 2026-11-22

`create_footprints_batch` `EDITFOOTPRINT` takes only `MODEL3D`. Met:
(a) 2026-11-19 (ninth), point 4, failed silently: a track added to an existing footprint by
`Comp.AddPCBObject(T)` (with or without `PCBM_BoardRegisteration` to the component) was
counted in the same script, saved, and gone from the file; four runs lost. Held:
`Board.AddPCBObject(T)` on the library's board after `SetBoardToComponentByName`, offset by
the board's origin.
(b) a body's rotation and offset: (seventh), point 4 (`IPCB_Model.GetState` returned 3 in
every var parameter through late binding; `RotateAroundXY` held); (tenth), point 6
(`Model.SetState`, `Body.SetState_FromModel`, `MoveByXY`, held; a pad's `Mode` and
`TopShape` set, held).
(c) reading it back: `get_footprint_primitives` reads the placement from the saved file
only, and on a footprint just made with `MODEL3D` gives the rotations and z offset as null,
"not in the saved library file", whether they were applied not seen ((twelfth), point 4). A
STEP's up axis had to be read outside Altium ((seventh), point 6).

Proposed: local; `EDITFOOTPRINT` records to add, move and delete primitives, set a pad's
stack and a body's rotation and offset; `bodies_3d` read live, with the body's extent. Not
decided.

Decided 2026-11-22 by the owner (the opening answer of `## Run 2026-11-22`): no tool; written as a recipe in `docs/recipes.md` (a DelphiScript a session proved, with its `run_altium_script` call), pointed to by one line of `run_altium_script`'s description, and closed as usage once the scenario test held for the file. A record with no proven script leaves the item Open.

Not written 2026-11-23, still Open: the record holds no script a session proved, only
calls, and (a)'s wrong way reports success. Missing: the script adding a primitive through
`Board.AddPCBObject` after `SetBoardToComponentByName`, and the one setting a body's
rotation and offset and a pad's stack, each read back from the saved file.

### A65 - The symbol tools cannot set colours, Comment, parameters or text positions, nor move a pin - OPEN 2026-11-22

2026-11-19 (tenth), point 1: `create_symbols_batch`'s GRAPHIC `rectangle` takes no line or
fill colour, and no record places the Designator or Comment (`ISch_Rectangle.Color` and
`AreaColor`, `Designator.Location`, `Comment.Location` by script, held). (thirteenth), point
2: `EDITSYMBOL` leaves pins and graphics alone; a pin moved and the body resized by script
(`MoveByXY`, the rectangle's `Corner`), held. 2026-11-20, point 2: `create_schematic_symbol`
cannot set the Comment or add a parameter: the symbols came out with Comment `*`, no
designator prefix and no part number.

Proposed: local; a colour on the rectangle and polygon records,
`DESIGNATOR|x|y|justification` and `COMMENT` with x|y, `MOVEPIN|<number>|x|y` and a rectangle
resize in `EDITSYMBOL`; `comment` and `parameters` on `create_schematic_symbol`. Not decided.

Decided 2026-11-22 by the owner (the opening answer of `## Run 2026-11-22`): no tool; written as a recipe in `docs/recipes.md` (a DelphiScript a session proved, with its `run_altium_script` call), pointed to by one line of `run_altium_script`'s description, and closed as usage once the scenario test held for the file. A record with no proven script leaves the item Open.

Not written 2026-11-23, still Open: the record holds no script a session proved, only
properties and calls. Missing: the scripts setting a rectangle's colours and the text
positions, the Comment, and a pin's move with the body's corner, each saved and read back
from the library; a parameter added to a library symbol was never done by script (the
description says never to register objects into a library).

### A67 - Tool descriptions leave out what a caller needs - OPEN 2026-11-22

(a) `get_component_data` reads the board only ("No component data found" for schematic
designators), which its description does not say: 2026-11-19 (third), point 4; (tenth),
point 3. The schematic reads are `get_project_components` and `get_schematic_data`.
(b) `edit_schematic` `add_power_port` shows the net name by default; on a sheet whose ports
hide it the new port read differently and was redone with `show_net_name: false` (2026-11-19
(eighth), point 2).
(c) `run_altium_script`'s notes: objects kept in a `TStringList` with `AddObject` cannot be
called back (`Undeclared identifier: I_ObjectAddress`); keep `IDispatch` variables (same
entry, point 4).

Proposed: usage; a line in each of the three descriptions. Not decided.

Decided 2026-11-22 by the owner (the opening answer of `## Run 2026-11-22`): no tool; written as a recipe in `docs/recipes.md` (a DelphiScript a session proved, with its `run_altium_script` call), pointed to by one line of `run_altium_script`'s description, and closed as usage once the scenario test held for the file. A record with no proven script leaves the item Open.

Written in part 2026-11-23, still Open: in `docs/recipes.md`, (c) by A52's proved script,
which keeps the object in an `IDispatch` variable; (a) and (b) marked *No script*, the tool
calls the sessions used. Missing for (a) and (b): nothing a script can prove; a decision
that the notes are enough to close them as usage. The description's own line on lists is
A75's.

### A68 - `edit_schematic` `delete_at` removes every object at the point - OPEN 2026-11-22

Sorted out of the entry of 2026-11-19 (third), point 7: with `kind: no_erc` at points
holding two markers it removed both (34 to 22 for six points), while its description says
it removes "the object located there"; reported 6 applied.

Proposed: local; one object per op, or the count removed in the result. Not decided.

### A69 - `edit_schematic` has no op for notes, a part's Comment, a block moved or a part swapped in place - OPEN 2026-11-22

Each done by `run_altium_script` or many ops:
(a) a free text note added or changed: 2026-11-19 (eighth), point 3; (thirteenth), point 3,
where notes had to be kept through a rebuild for want of one; (fifteenth), point 3.
`delete_at` kind `note` held.
(b) a placed part's Comment (`Comp.Comment.Text`): (third), point 9; a parameter removed
(`Remove_Parameter`): (eighth), point 3.
(c) a block of a sheet moved with its wires: (fifteenth), point 2: `move_component` moves the
part only; one `edit_schematic` of 51 operations (23 `delete_at`, 3 `move_component`, 25
adds) did it, the netlist unchanged.
(d) placed parts moved onto another library symbol, keeping their place and text: (eighth),
point 5, 21 parts by setting `LibReference`, `DesignItemId`, `SourceLibraryName`,
`LibraryPath` and `ComponentDescription`, held; (tenth), point 2: `delete_component`,
`place_component` and `move_text` in one call serve a swap, a swap op still missing.

Proposed: local; ops for a note (add and edit), a part's Comment, a parameter removed,
`move_component` with `drag: true` or a `move_region`, and a swap. Not decided.

Decided 2026-11-22 by the owner (the opening answer of `## Run 2026-11-22`): no tool; written as a recipe in `docs/recipes.md` (a DelphiScript a session proved, with its `run_altium_script` call), pointed to by one line of `run_altium_script`'s description, and closed as usage once the scenario test held for the file. A record with no proven script leaves the item Open.

Written in part 2026-11-23, still Open: (d) in `docs/recipes.md`, marked *No script*, the
swap by one `edit_schematic` call that held. Missing, with no script a session proved in
the record: (a) a note added or changed, (b) the Comment set and a parameter removed, (c) a
block moved (done by 51 ops only), (d) the swap in place by `LibReference` and the fields
beside it.

### A72 - `check_schematic` misses overlaps a screenshot shows - OPEN 2026-11-22

2026-11-19 (thirteenth), point 1: a sheet reported clean while a placed symbol's own pin
names crossed (a top pin's vertical name over the left pins' names, three bottom pins' names
over the right side's). (fifteenth), point 1: two power ports overlapping (a ground port 300
mil above a rail port at the same x, twice); `text_overlap` takes a port's text against
wires, pins, parts and other text, but not a port's graphic against another's text.

Proposed: local; a `pin_name_overlap` issue (each shown pin name's box against the part's
others, the library symbol named as the fix), and each power port's box (symbol and shown
name) against the other ports and part bodies. Not decided.

### A73 - The tool listing weighs about 41k tokens - OPEN 2026-11-22

The tools' names, descriptions and schemas, as `main.mcp.list_tools()` gives them, were 80 tools and 164,529 characters at `f120b3f` (about 41k tokens). Whether Claude Code sends it in every turn or defers it to tool search was not measured. Written 2026-11-22 by the owner's choice (the opening answer of `## Run 2026-11-22`), for a later run, not that one: measure what a session is sent, then trim the descriptions (examples and repeated advice first) where it is sent.

### A48 - The project compile reads stale sheets after a script's edit - OPEN 2026-11-23

Three sessions read in the compile what the saved sheets no longer held, each reported
success, build `0.7.0-20261115-172812`:
(a) 2026-11-18 (second), point 6: sheets set to A3 by script (`SheetStyle`, `SheetSizeX/Y`
15500 x 11100, saved, drawn A3), then `get_erc_violations` gave 852 "Object not completely
within sheet boundaries", all past A4's bounds, twice. In a new Altium session on the same
saved sheets none came back (2026-11-19 (first), point 1).
(b) 2026-11-19 (third), point 3: footprints set on five placed parts by script;
`get_project_components` and a script's `DM_Compile` gave them an empty `footprint`, even
after the sheet was saved, closed and reopened; only one more script edit with
`SetModified(True)` made the compile give all five. A script that leaves `Modified` false
also lets Save All skip the sheet. With `SaveDoc` right after the script it did not recur
(2026-11-19 (seventh), point 1).
(c) 2026-11-19 (fourteenth), point 4: harness objects placed by script gave 2 fatal "Missing
Harness Type on Signal Harness", "Unconnected line", one "Multiple Harness Types on harness"
and 16 "Invalid Connection to a Harness Connector", unchanged after `LineWidth` was set and
saved; the project closed by script and reopened by `get_erc_violations(project_path)`: 0
fatal, the netlist right. Which of the two changes was needed is not separated.
Usage until fixed: after a script edits a sheet, mark it modified and save it; before
trusting a compile, close and reopen the project.

Proposed: local; a `reload` option on `get_erc_violations` and `get_project_components` (the
project's sheets closed and reopened first), and a probe for the call that refreshes the
compile. Not decided.

Decided 2026-11-22 in the plan (the owner's token rule): no new argument; a probe first for a
call that brings the compile up to date short of closing the project; found, made inside
both tools before they compile.

Cause: Altium's project compile keeps its own model of each sheet and updates it only from
the change notices the schematic editor sends inside a process. A script that changes an
object without notices on that object (a part's footprint renamed through its
implementation, with the notices sent for the implementation only; a net label's text or a
sheet's size set directly) leaves the model as it was. The modified flag plays no part, and
saving the sheet and closing it does not reset the model either: the compile still read the
old net name from a sheet saved with the new one and closed (as (b) found).

Probe (sandbox scripts on a one-sheet copy of the SpiritLevel-SL1 example's power sheet, a
diode's footprint renamed as in (b), then `get_project_components`), each call and what it
did:
- nothing (the control), `SetModified(True)`, `IDocument.DM_Compile` on the sheet,
  `IDocument.DM_UpdateDateModified`, `RunProcess('WorkspaceManager:Compile')` with
  `ObjectKind=Project` on the project made current, an empty `PreProcess`/`PostProcess`,
  `SCHM_BeginModify`/`SCHM_EndModify` on the sheet object inside them, a broadcast of
  `SCHM_SystemInvalid`/`SCHM_SystemValid`, and the notices on every part with no process
  around them: the old footprint, each.
- `DM_NeedsCompile` and `DM_ScrapCompile` (named in Altium's SDK library): not in AD25's
  script interfaces (undeclared on `IDocument` and `IProject`).
- `SaveDoc` then `IServerDocument.DoFileLoad`: the new footprint, but it saves, and a reload
  from the file drops unsaved edits; not for a read tool.
- `PreProcess`, begin and end notices on the part, `PostProcess`: the new footprint; on every
  object of the sheet, a net label renamed with no notices also came through. But it leaves
  a step in the sheet's undo history: one Undo after it no longer took back the edit before.
  The same notices between broadcasts of `SCHM_ProcessStart` and `SCHM_ProcessEnd` instead:
  also an undo step.
- End notices only (`SCHM_EndModify`) on every object, between `SCHM_ProcessStart` and
  `SCHM_ProcessEnd`: the new footprint and the new net name, and no undo step; without the
  two broadcasts, still old. A sheet size set directly came through only with the end notice
  for the sheet object as well (204 "Object not completely within sheet boundaries" on a
  2000 x 2000 mil sheet, none without it). The notices set the modified flag;
  `SetModified` puts it back. Time: 0.15 to 0.25 s for a sheet of 211 objects, 0.5 to 0.9 s
  for one of 653.
- For a sheet not open: saved and closed after the edit, still old; the file's time moved
  forward, the compile read the file again and came through.

Fix: `RefreshOpenSheets` (`other_utils.pas`), called by `GetProjectComponents` and by
`GetERCViolations` when it compiles, before `DM_Compile`: for each sheet of the project open
in Altium, an `SCHM_EndModify` for each of its first-level objects and for the sheet, between
`SCHM_ProcessStart` and `SCHM_ProcessEnd`, the sheet's modified flag put back as found. No
argument, no description changed.

Decided 2026-11-22 by the run, not the owner: every open sheet of the project refreshed on
every compile, not only the sheets marked modified, because a stale model shows no sign (the
flag was true and false in the probes alike) and the refresh costs about 1 ms an object.

Decided 2026-11-22 by the run, not the owner: end notices inside `SCHM_ProcessStart` and
`SCHM_ProcessEnd`, not `PreProcess`/`PostProcess` with begin and end notices, because both
bring the compile up to date and the latter put an empty step into each open sheet's undo
history, its redo cleared, on every call of a read tool.

Decided 2026-11-22 by the run, not the owner: a sheet not open in Altium is not refreshed,
because the only ways found write to the user's file (its time moved) or open every closed
sheet on each compile. Left, as usage: a sheet a script edited without notices on the
objects it changed, then saved and closed, still compiles stale until it is opened again
before the compile call or the project is closed and reopened.

Seen on the way, not filed: a project file holding only `[Design]` `Version=1.0` and its
document list compiled a sheet not open in Altium as empty (0 components, 0 violations,
`DM_CompileEx(True, '')` too); with the example's own project settings it compiled. The test
keeps the example's settings.

Test before: `tests/test_live_compile_refresh.py` (new; a one-sheet project with the
example's settings, its power sheet open), on the old code 2 of 3 fail:
`test_a_footprint_a_script_set_is_compiled`: `AssertionError: 'DO214' != 'A48_NEW_FP' ... :
the compile reads the footprint from before the script's edit`;
`test_a_sheet_size_a_script_set_is_compiled`: `AssertionError: 0 not greater than 100 : the
compile reads the sheet size from before the script's edit: {}`. The third,
`test_the_users_last_undo_step_stays_the_last`, passes before and after (it guards the undo
history). After: 3/3 pass in AD25, the modified flag as found (false, then true).
`test_live_erc` and `test_live_drc`'s `LiveCompileFolderTest` 4/4 pass (A49: 207 listed, 69
suppressed, 6 groups, 2,164 characters). Offline: the whole list of `tests.yml` 557/557 pass;
the new module is live only, not in it. Tool listing: 80 tools, 164,841 characters before
and after.

Fixed in `891ee59`. Released in `build-20261123-001227`.

Scenario test of build `0.7.0-20261123-001227` (findings 2026-11-23, point 4), held for edits: a
placed part's current footprint renamed through its implementation by script, no notices,
the modified flag left false: `get_project_components` gave the new name, where the control
(the same edit read through a script's own `DM_Compile`) gave the old one; a custom sheet
size of 2000 x 2000 mil set directly: `get_erc_violations` gave 100 "Object not completely
within sheet boundaries". The sheet's and the project's modified flags stayed 0 through
both tools.

Failed on the same build (findings 2026-11-23, point 5), for objects a script removed: a
no-ERC marker removed with `RemoveSchObject` inside `PreProcess`/`PostProcess`, no notice
for the removed object, the sheet open: `get_erc_violations` still compiled it in, its
violation still suppressed. At scale, 92 markers removed from four open sheets and the
sheets saved: `suppressed` stayed 345 over two calls, and read 161 with 92 more listed only
after the project was closed and reopened. Reported success with a stale result.
`RefreshOpenSheets` sends end notices for the objects the sheet still holds, so a removed
one is never named. A marker removed with `SchServer.RobotManager.SendMessage(Doc.I_ObjectAddress,
c_BroadCast, SCHM_PrimitiveRegistration, O.I_ObjectAddress)` after the removal came through
at once.

A48 (b), what is left (the part's name, apart from the three sessions' (a) to (c) above):
the compile brought up to date after a script removed objects without a notice.

Decided 2026-11-23 by the run, not the owner: A48 (b) taken into group 1 again, by the
run's rule for a fix of the group not holding (*The scenario test of a group*, 7): a probe
first for a sheet-level re-read that also drops removed objects; not found, the fallback: a
short `stale_sheets` in `get_erc_violations`' and `get_project_components`' result (or the
equivalent check of the compile's object count against the sheet's) and one line in
`run_altium_script`'s description on sending `SCHM_PrimitiveRegistration` after a removal,
because a stale compile must not pass silently and the token rule asks for the smaller
change.

Probed 2026-11-23 for A48 (b) by the run's subagent, stopped by the owner before a test or
a fix (its report, not checked by the main session). Reproduced by a scratch probe only, on
a temporary copy of an Altium example sheet: a marker removed by script with no notice, the
sheet held 0 markers, and `get_erc_violations` still gave `total 0, suppressed 2`. The
existing `test_live_compile_refresh.py` passed 3/3 before the probes; no other live test
and no offline test was run.

Tried, each leaving `suppressed 2` (in probes 9 and 10 the calls ran one after another on
one stale sheet, so their effects add up):
- probe 4, each on a fresh copy: `SCHM_PrimitiveRegistration` with an existing object, with
  no data, with the sheet as data; `GraphicallyInvalidate`.
- probe 8: the registration from nil with the sheet as data.
- probe 9, compiles: `WorkspaceManager:Compile` (the document; Recompile on the project and
  on the focused project), `DM_CompileEx(True)` and `(False)` on the project.
- probe 9, the document model: `DM_LoadDocument`, `DM_SmartLoad`, `DM_DocumentLoaded`, the
  project's `DM_LoadAllLogicalDocuments`, `DM_ResetLastCompileTimeForAllDocuments`,
  `DM_Validate`, `DM_ClearViolations`.
- probe 10, notices: CancelModify, SystemInvalid and SystemValid, Create, Begin and
  EndModify on the sheet, a registration from the system and of a never-added object, a
  border toggled and back, `UpdateDocumentProperties`, transient NoERC, CompileMask,
  Parameter and SheetSymbol objects.
- probe 10, re-reads: the document's `DM_ScrapCompile(True)` (callable, though the probe of
  2026-11-22 above says undeclared), a load by path, the document opened again,
  `SetFileModifiedDate`, `DM_UpdateDateModified`, the file's time touched, a save alone.

Not usable or not finished:
- Undeclared to scripts: `DM_Reload`, `DM_ResetCache`, `DM_SetNeedsUpdate`,
  `DM_MainCompile`, `DM_InvalidateToolchain`, the document's `DM_CompileEx` and
  `DM_SetModified`. `DM_ScrapCompileWithOptions` failed, its message not captured.
- A script reading the message constants timed out at 180 s (Altium answered afterwards).
- The document model gives counts of components, nets, pins, ports and sheet symbols; no
  name tried gave its no-ERC markers (probes 3, 5, 7). Comparing the model's addresses
  with the sheet's objects ended in a script cast error (probe 6).

The one change seen: a save, then `DoFileLoad`, at the end of probe 10: `total 59, errors
59, suppressed 1`. Not known to be the right result: 59 is also the sheet's component
count, and 1 is still suppressed. The control, a registration notice naming the removed
object, was not run by the subagent; only the scenario test saw it work.

Inferred, not shown: the compiler keeps a list of registered objects that only a notice
naming the object, or a reload, clears. Two cautions follow. A `stale_sheets` from object
counts, the fallback decided above, would miss this very case, as the model's markers
could not be counted. A `DoFileLoad` inside a read tool could lose unsaved edits, as the
modified flag can be false after a script's edit.

Next, in this order (taken since, below):
1. The failing test, in `test_live_compile_refresh.py`.
2. On fresh copies, the true numbers two ways (the notice after the removal; save, close
   and reopen the project), against a save and `DoFileLoad` alone.
3. No safe reload shown: the fallback, its description line as decided, and what
   `stale_sheets` can honestly detect settled before it is built.

The probe scripts are not kept in the repo. Until Windows clears it they are in
`%TEMP%\claude\ffb01ff0902fa28f\d905e04e-513a-472f-9bcf-90e44f580c42\scratchpad`
(`probe_common.py`, `probe1.py` to `probe10.py`, the output of probes 9 and 10).

Taken 2026-11-23 for A48 (b), the list above in its order, in AD25, each probe on a fresh
copy of the one-sheet project: still open, the fallback built only as far as it holds.

Test before, on the code of `891ee59` (a test point off its wire under a no-ERC marker, the
marker then removed by script with no notice; a placed part removed the same way):
`test_a_marker_a_script_removed_is_not_compiled`: `AssertionError: Tuples differ: (2, 0) !=
(0, 2) : the compile still holds the marker the script removed` (suppressed, total);
`test_a_part_a_script_removed_is_not_compiled`: `AssertionError: 59 != 58 : the compile
still holds the part the script removed`. So `get_project_components` is stale too, for a
removed part. A parameter removed from a part came through (14, then 13), so the gap seen is for
objects of the sheet itself.

The true numbers, both ways the same, `total 2` (one floating input pin, one unconnected
object), `suppressed 0`:
- the notice naming the marker after its removal: right at once;
- saved, the project closed and reopened: right, also for a marker the sheet's file held
  when it was opened.
A third gave them too: saved, the sheet closed and opened again. Saved and closed alone was
still stale (`total 0, suppressed 2`).

`DoFileLoad` is no re-read (this corrects the two notes on it above, of 2026-11-22 and
2026-11-23): on a sheet edited and saved in the session, with nothing left unsaved, it
doubled the sheet's objects in the editor (59 parts, then 118), so the compile gave 59
"Duplicate part designators" and `suppressed 1`, the `total 59` seen in probe 10. After the
marker's removal and a save it gave `total 60, suppressed 0`. Closed unsaved and opened
again in the same Altium session the sheet still held 118, the file's size unchanged. A
sheet only opened, not edited, kept its 59.

No safe re-read shown: the three ways that work need the removed object, which is no longer
the sheet's, or a save and a close, which write the user's file or lose edits (the modified
flag can be false after a script's edit).

What `stale_sheets` could detect: the removed marker is in none of the sheet's iterators
(plain, all levels, by area) nor in its hit test, and the document model shows no markers,
so nothing found to read differs from a sheet that never had it. A removed part does show (59 in
the document model, 58 on the sheet).

Decided 2026-11-23 by the run, not the owner: no `stale_sheets`, in neither tool, the
part count included, because it would read clean on the case this part was opened for, a
removed marker, and a field that reads clean on a stale compile is worse than none.

Decided 2026-11-23 by the run, not the owner: the line in `run_altium_script`'s description
put into its sentence on change notices ("naming an object just added or removed, else the
compile keeps a removed one"), because that is where a script's author reads which notice
to send, and it costs less than a point of its own.

Decided 2026-11-23 by the run, not the owner: the two failing tests kept as expected
failures, not deleted or left failing, because the defect stays stated and a fix shows as
two unexpected successes, while the module's other tests still say whether A48's fix holds.

Built, partly: that description line, a comment at `RefreshOpenSheets` on what it cannot
name and against `DoFileLoad`, and four tests: the two above and two that the notice the
line names works, for a marker and for a part. Tests after, in AD25:
`test_live_compile_refresh` 5 pass and 2 fail as expected, of 7; `test_live_erc` and
`test_live_drc`'s `LiveCompileFolderTest` 4/4 pass. Offline: the whole list of `tests.yml`
557/557 pass. Tool listing (names, descriptions, `json.dumps` of the schemas): 80 tools,
157,905 characters before, 157,971 after.

Left, so this stays Open: both tools still report success with a stale result after a
script removed an object without the notice. Usage: send the notice with the removal;
after a removal made without it, save the sheet, close it and open it again, or the
project, before trusting a compile (the reopening probed for a marker, not for a part).
Not tried, for whoever takes it next: prevention where
the removal is written, `run_altium_script` warning of a `RemoveSchObject` with no
`SCHM_PrimitiveRegistration` in the same script; it is outside what the plan decided.

The part built: `71514df`, released in `build-20261123-031122`.

Checked 2026-11-23 by the run's check: the scenario test of build `0.7.0-20261123-031122`
(findings 2026-11-23, second entry, points 2 to 4): the part built held, the notice the
description names, for markers (92 removed from four open sheets, nothing saved, the next
compile following each time: `suppressed` 345, 337, 161; the same lists after a save and a
reopened project) and for a removed part (gone from `get_project_components` at once).
Without the notice still stale, as written, reported success: the marker's violation still
suppressed, the part still listed (15 components where the sheet held 14). The usage (save
the sheet, close it and open it again) cured both, so for a part too: the caveat above,
"probed for a marker, not for a part", is settled. The server's own removals show no gap:
`edit_schematic`'s `delete_at` of a marker and `delete_component`, unsaved, were both in
the next compile. The refresh for edits held again (a footprint and a sheet size set with
no notice, the modified flags still 0).

### A76 - Component revision warnings come and go between compiles, and `total` with them - OPEN 2026-11-23

Sorted out of the second entry of 2026-11-23, point 5, the scenario test of build
`0.7.0-20261123-031122`: Altium's component revision warnings ("Can't perform revision
status validation: Failed to connect to server") come and go between compiles, so
`get_erc_violations`' `total` differs between two compiles of the same sheets. In 2 of 12
compiles all four were absent: `total` 235, then 239 for the same sheets after the project
was reopened; on another copy 1, where 5 was expected. Reported success. Cause not looked
for.

Usage: compare two compiles by `errors` and their groups, not by `total`.

Decided 2026-11-23 by the run, not the owner: not taken into this run, because its cause is
unknown and looks to be Altium's, not a small fix in group 1's files.

### A79 - A footprint linked by name keeps the case it was typed in, not the library's - OPEN 2026-11-23

Sorted out of the group 3 entry of 2026-11-23, point 3, the scenario test of build
`0.7.0-20261123-140004`, the point that held A66. `create_schematic_symbol` given a footprint
name in lower case that the project's saved `.PcbLib` holds in another case linked it to
that library and made it current, as A66 promises, but stored the model name as typed, not
as the library has it; the saved library holds the same, and the compile lists the part's
footprint in that case. Reported success, `problems` []. Whether a board update resolves
the footprint in the other case was not tried.

Proposed: local; the lookup that fills the library (A66's, `server/symbol_footprint.py`)
writes the name as the library holds it too. Not decided.

Decided 2026-11-23 by the run, not the owner: left out of the run, because it came from group 3's scenario test and the run ends with that group.

### A80 - `build_schematic` into the focused project names that project in `detached_from` - OPEN 2026-11-23

Sorted out of the group 3 entry of 2026-11-23, point 9, the scenario test of build
`0.7.0-20261123-140004`. `build_schematic(project_path=P, sheet_path=...)` while P itself is
the focused project returns `detached_from: P`, the project the sheet was added to, as if
the sheet had been taken out of another one. The sheet is in P and in its saved project
file; only the field is wrong. Reported success. Bears on A26 (closed, held in group 2's
scenario test), whose fix gives `detached_from`: the case of a target that is itself the
focused project.

Proposed: local; no `detached_from` when the project the sheet would be detached from is
the target. Not decided.

Decided 2026-11-23 by the run, not the owner: left out of the run, because it came from group 3's scenario test and the run ends with that group.

### A81 - The memory guard refuses a read of the unsaved flags, so a restart cannot be checked first - OPEN 2026-11-23

Sorted out of the group 3 entry of 2026-11-23, point 10, the scenario test of build
`0.7.0-20261123-140004`, given there as a lesson. At the session's start Altium held 3.7 GB
(running since the release's live tests), and the server's memory guard
(`altium_limit_problem` in `server/main.py`, half the machine's RAM) refused every bridge
call ("Altium is using 3.7 GB of memory ... restart it"), and `run_altium_script` with a
script that only lists each open document's unsaved flag as well. The refusal asks the user
to save their work and restart, but what was unsaved could not be read before the restart.
Done instead: `get_project_info` on the focused project (clean), the files of the open
projects hashed, Altium's main window closed (no save prompt, 6 s), Altium started from its
exe, the hashes equal after.

Usage: a session that starts on an Altium of a long live run restarts it first.

Proposed: local; the guard lets a small read of the open documents' modified flags through,
or its refusal says how to check what is unsaved without Altium. Not decided.

Decided 2026-11-23 by the run, not the owner: left out of the run, because it came from group 3's scenario test and the run ends with that group.

### A82 - `check_schematic` does not report a part that lacks its body lock flag - OPEN 2026-11-23

From Run 2026-11-22, the part of A71 its plan left out (`closed_items.md`, A71): a placed
part whose children lack the flag that locks its body (`IsNotAccesible=T` in the saved file)
passes `check_schematic` unreported. A71's toggle fixed the tools' own placements, not
sheets drawn before it or by other means. The flag is not readable from DelphiScript
("Undeclared identifier: IsNotAccesible"), only from the saved file.

Proposed: local; `check_schematic` reads the saved sheet and reports such a part, A71's
toggle named as the fix. Not decided.

### A83 - `get_project_components` returns too much - OPEN 2026-11-23

From Run 2026-11-22, A57's line of 2026-11-22 (`closed_items.md`, A57; findings 2026-11-22,
point 1): `get_project_components` gave 63k characters of results in one session (7
calls). A57's fix took the library reads only; the run left this one out.

Proposed: local; a smaller result by default, by the owner's token rule (the intro). Not
decided.

### A84 - `ad25` is behind `upstream/main` - OPEN 2026-11-23

From Run 2026-11-22 (its *For the owner, prepared*): `ad25` was 116 commits behind
`upstream/main` on 2026-11-22. Upstream has its own foreground guard (#100) beside A22's,
and new tools such as `dismiss_dialog` and `list_open_documents`, which grow the tool
listing (A73).

Local: the update as `CLAUDE.md` says (rebase, the offline tests, a release). The owner's
call, in a session of its own, not a run's step.

### A85 - Small points of `build_schematic` seen by A45 and A46 - OPEN 2026-11-23

From Run 2026-11-22, what A46 and A45 (`closed_items.md`) list as seen and left, by reading
the code, not tested: (a) a build with a missing part comes back as the error text, with no
pin map, and a failed build's warnings are inside that text; (b) `pin_map.txt` in the
exchange folder is read after the bridge's lock is released, so two sessions building at
once could read each other's map; (c) the same part given twice under one designator is
placed twice, unreported; (d) text placement by `param_placement.txt` measures the body
over all of a symbol's parts, not the part placed.

Proposed: local; each confirmed by a test first. Not decided.

### A86 - Every tool drops an argument it does not have, without a word - OPEN 2026-11-23

From Run 2026-11-22, what A58 (`closed_items.md`) lists as seen and left: an inline argument
a tool does not have is dropped silently (the mcp package's argument model), so a misspelt
argument reads as success; A58's test before got its false success so. Only `spec_file`
refuses a name it does not know.

Proposed: upstream, the code is upstream's; an unknown argument refused, if the package
allows it without a new argument. Not decided.

### A87 - Offline tests that reach the real server's folders and Altium's windows - OPEN 2026-11-23

From Run 2026-11-22, its recipes step (`closed_items.md`, A55): `test_build_info`'s
`ServerStatusTest` calls the real `get_server_status`, so an offline run looks for Altium's
windows and may write and prune the resident's folder; `test_symbol_footprint` made and
removed a temporary file in the real exchange folder, and the server's log grew. The step
then ran the list with a scratch exchange and data folder. Nine tests of the offline list
(`InUseTest` 2, `ExchangeLockTest` 2, `test_dblib`'s database tests 4, `ServerStatusTest`
1) start or stop processes or look for Altium's windows.

Proposed: local; the offline tests given a scratch exchange and data folder by default, and
those that touch processes or windows marked apart. Not decided.

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

Run 2026-11-22: following upstream PR #113 was offered in its opening question and not
taken; it stays the owner's choice.

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
