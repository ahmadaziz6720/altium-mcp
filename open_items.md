# Open Items

What sessions found in this fork's server and what was decided about each, A-numbered.
The raw entries are in [`findings.md`](findings.md); this file holds the items. Each item
names where it goes: **upstream** (an issue or PR at `coffeenmusic/altium-mcp`), **local**
(a fix on `ad25`, sent upstream as a PR when it is general), **usage** (a note for the
sessions that use the server), or **not taken**.

Three sections: **Open**, not yet fixed; **Waiting**, fixed and not yet settled (a PR not
merged, a fix not yet run in a session); **Closed**, merged upstream, run and held, or
decided against, with the record.

**Open: A8, A11 to A15, A22 to A24.**

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

A10 to A16 come from a review of the tools against a whole design flow (schematic and
missing library parts, ERC; a board with its rules and layer stack; placement; routing,
DRC; fabrication outputs for an assembly service), not from a session's entry: what the
flow needs that no tool does (2026-11-12). They are features, not faults.

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
- [ ] group 3: offline and live tests, pushed, released (build: …)
- [ ] group 3: scenario test (session id: …), entry committed and sorted, release page
- [ ] A13: committed (or left Open, why written into it)
- [ ] A14: committed (or left Open, why written into it)
- [ ] A12: committed (or left Open, why written into it)
- [ ] group 4: offline and live tests, pushed, released (build: …)
- [ ] group 4: scenario test (session id: …), entry committed and sorted, release page
- [ ] A15: committed (or left Open, why written into it)
- [ ] A8: committed (or left Open, why written into it)
- [ ] group 5: offline and live tests, pushed, released (build: …)
- [ ] group 5: scenario test (session id: …), entry committed and sorted, release page
- [ ] the report

---

## Open

**A8. No tool to make a PcbLib from a board.** `RunProcess('PCB:MakeLibrary')` and
`Client.SendMessage('PCB:MakeLibrary', ...)` from `run_altium_script` returned success and
did nothing (no document, no dialog); it was done by hand through the menu. Local: find a
way that works from a script (the process with its parameters, or building the library from
the board's footprints through the PcbLib API), then a tool. (2026-11-12, 7.)

**A11. No tool to update the board from the schematic.** No Update PCB Document (ECO):
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

**A12. Output jobs can be run and read, not made.** `run_output_jobs` runs containers of
an OutJob that exists and `get_outjob_settings` reads one from disk; nothing creates an
OutJob or sets its outputs (Gerber layers and format, NC Drill, BOM, pick and place, output
folder). Nor are outputs given in the form an assembly service asks for, e.g. JLCPCB's: a
BOM of Comment, Designator, Footprint and the supplier part number; a placement list of
Designator, Mid X, Mid Y, Layer, Rotation, with the per-footprint rotation corrections it
needs; the Gerbers and drill files zipped. Local: a tool that writes an OutJob from a
preset or edits the outputs of one, and a step that turns Altium's BOM and pick and place
into a named service's columns.

**A13. The layer stack can only be read.** `get_pcb_layer_stackup` reads it; nothing adds
or removes layers or sets copper weight, dielectric thickness, material or constant. Local:
a tool that sets the stack from a list top to bottom, as the read gives it, with presets
for common fabrication stacks (2-layer 1.6 mm; 4-layer 1.6 mm with 7628 prepreg).

**A14. `create_pcb_rule` covers seven rule kinds.** Clearance, width, hole size, routing
via, solder and paste mask expansion, polygon connect. Not differential pairs, length or
matched length, routing layers, plane connect, component clearance, silkscreen clearances
or hole to hole; no preset that sets a fabricator's minimums at once; priority cannot be
set (the tool's own note). Local: more kinds, differential pair and matched length first,
and a capability preset.

**A15. Parts come from local `.SchLib` and `.PcbLib` files only.** `build_schematic` and
`edit_schematic`'s `place_component` need a `.SchLib` path (`.IntLib` is not supported); a
`.DbLib` can be searched only through `dev/db_search.py`, not a tool; nothing searches
Altium's Manufacturer Part Search, a content vault or a supplier's catalogue (LCSC and
others), so no supplier part number is filled in. A missing part is drawn from its
datasheet with the symbol and footprint tools, unchecked against a vendor's model. Local:
`.IntLib` parts in `build_schematic`, the DbLib search as a tool, a supplier lookup that
fills the part number parameters, and an import of a vendor's downloaded symbol and
footprint worth a look.

**A22. A call takes the keyboard and the front of the screen for Altium.** While the server
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

**A23. `get_unrouted_connections` read by net names no pad.** With `nets` only, the
connections come with `from_pad` and `to_pad` null even where an end is a pad's centre;
the same connection read with `designators` names both ends. As the description says
(pads are named with `designators`), but a caller reading by net needs a second call to
know the pads. Local: name a pad whenever an end lies on one, whatever the group was given
by; or, the smaller change, a line in the description. Usage until then: read with the
net's `designators` to get the pads. (2026-11-14, fourth entry, 4.) Not in the run of
2026-11-14's later groups (not in their files): for the next run.

**A24. A modal message no driver knows blocks the call until the bridge's limit.** When
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
Released in `build-20261112-120520`. Scenario test of that build held (2026-11-12, third
entry, 1): mask 0.4 / copper 1.4 / core 60 (FR-4, er 4.8) / copper 1.4 / mask 0.4,
`total_thickness_mils` 63.6, `dielectric_layers` 3, as a `LayerStack_V7` walk gives.
Waits for the upstream PR.

**A7. `get_pcb_rules` repeats each rule's scope.** 9.3k characters for 38 rules, the scope
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

**A10. No tool to set up a project and its board.** `build_schematic` makes its sheet
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
Fixed in the commit that moves it here. Local: on `ad25`, not yet in a build. Upstream: not
yet decided.

**A16. A library symbol cannot be given its footprint.** `create_schematic_symbol` and
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
Fixed in the commit that moves it here. Local: on `ad25`, not yet in a build. Upstream: not
yet decided.


## Closed

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
`build-20261112-120520`. Closed: the scenario test of that build held (2026-11-12, third
entry, 3): on a freshly opened board `analyzed` false and the board still "open" after
the call; on a board with unsaved changes `analyzed` true.

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
`build-20261112-120520`. Closed: the scenario test of that build held (2026-11-12, third
entry, 4): 5.0k characters for the same call, was 8.6k, the two board-wide ground pours
as `beyond_area` entries.

**A17. `run_drc` leaves the board modified.** On a freshly reopened board, after
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

**A18. `run_drc` returns a stale report when the check did not run.** On the first DRC
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

**A19. `run_drc` leaves the project file modified, and `get_project_info` does not say
so.** The first `run_drc` after a project is opened marks the `.PrjPcb` modified while the
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

**A20. `run_drc`'s report ignores the rule filter.** `run_drc(rules=[one kind])` whose
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

**A5. Read calls leave files in the project folder.** `run_drc` writes `Design Rule Check -
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

**A9. `run_altium_script`'s compile check reads one declaration per `var` line.** A
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

**A21. `run_drc` waits on Altium's repour message.** After copper under a pour was deleted,
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
