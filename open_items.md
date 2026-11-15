# Open Items

What sessions found in this fork's server and what was decided about each, A-numbered.
The raw entries are in [`findings.md`](findings.md); this file holds the items. Each item
names where it goes: **upstream** (an issue or PR at `coffeenmusic/altium-mcp`), **local**
(a fix on `ad25`, sent upstream as a PR when it is general), **usage** (a note for the
sessions that use the server), or **not taken**.

Three sections: **Open**, not yet fixed; **Waiting**, fixed and not yet settled (a PR not
merged, a fix not yet run in a session); **Closed**, merged upstream, run and held, or
decided against, with the record.

**Open: A8, A11, A12, A14, A15, A23, A25 to A28, A31 to A34.**

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

**A23. `get_unrouted_connections` read by net names no pad.** With `nets` only, the
connections come with `from_pad` and `to_pad` null even where an end is a pad's centre;
the same connection read with `designators` names both ends. As the description says
(pads are named with `designators`), but a caller reading by net needs a second call to
know the pads. Local: name a pad whenever an end lies on one, whatever the group was given
by; or, the smaller change, a line in the description. Usage until then: read with the
net's `designators` to get the pads. (2026-11-14, fourth entry, 4.) Not in the run of
2026-11-14's later groups (not in their files): for the next run.

**A25. `set_board_shape` on a board just made: Altium's region of the outline is wrong.**
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

**A26. `build_schematic` with `project_path` leaves the focused project modified.** With
another project in focus, `build_schematic(project_path, sheet_path)` took its sheet back
from that project (`project.detached_from` names it) but left that project's file flag set:
unmodified before, modified after, twice in a row (its file not written);
`add_project_document(create=True)` in the same state puts the flag back. In the same
result the top-level `detached_from` is `""` while the nested one names the project, and
`sheet` gives the unsaved name (`Sheet1.SchDoc`) where `sheet_path` gives the file saved.
Local: the flag put back as `add_project_document` does, one `detached_from`, and `sheet`
the saved name. (2026-11-14, fifth entry, 3 and 6.) For the next run.

**A27. `build_schematic` with `footprint` on a symbol that has a current one gives two.**
A part whose library symbol already has a current footprint, placed with `footprint`, gets
the named model added (by name, no library) as current while the library's current one
keeps its mark: two current PCB footprints (`IsCurrent` 1 on both through the API,
`ISCURRENT=T` twice in the saved sheet). Rare before A16, now the common case. Reported
success. Local: the footprint given becomes the only current one, its mark moved when the
symbol already has a model of that name. (2026-11-14, fifth entry, 5.) For the next run.

**A28. No tool makes an empty library.** `create_symbols_batch`'s `LIBRARY` needs an
existing `.SchLib` and `add_project_document`'s `create` makes sheets and boards only, so
a new `.SchLib` or `.PcbLib` is made by script (`CreateNewDocumentFromDocumentKind`,
`DoSafeChangeFileNameAndSave`, then `SetModified(True)` and `DoFileSave('')`), and it went
into the project in focus, as A10's probe found for a sheet. Local: `create` for `.SchLib`
and `.PcbLib` in `add_project_document`, or a library made by the symbol and footprint
tools when missing. (2026-11-14, fifth entry, 7.) For the next run.

**A31. A22's guard misses a call that starts with no window in front.** `ForegroundGuard`
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

**A32. `run_altium_script` answers Altium's messages its own way.** A24's rule (a message
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

**A33. An OK-only message open before a bridge call is neither pressed nor named.** The
check before the launch lets a lone OK through (leaving it to the watch), Altium refuses
the launch as busy (a modal "Information" `TMessageForm` over the message), and the watch
never runs, as it starts only once the command has started: `get_board_summary` ended after
46 s with "Altium did not start the command (not executed). A script of ours was stuck in
Altium's debugger…", two boxes left open. A click posted to the message did nothing while
the busy box was over it; the busy box first, then the message, closed both. Local: before
the launch, press a lone OK (the topmost box first) and say so, or refuse naming it, as for
a message with choices; a live test with an OK message left open by a script. (2026-11-14,
sixth entry, 7.) For the next run.

**A34. Small points left by the resident bridge and the message tool.** From A30's work
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
decide, with A31 and A32. Local. For the next run.

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

**A35. A34 (a), the resident's tag differed between a release copy and a checkout.** The tag
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
Fixed in the commit that moves it here. Local: on `ad25`, in the commit that moves it
here; not yet in a build. Upstream: not yet decided.

**A13. The layer stack can only be read.** `get_pcb_layer_stackup` reads it; nothing adds
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
Fixed in the commit that moves it here. Local: on `ad25`, in the commit that moves it here;
not yet in a build. Upstream: not yet decided.

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
Fixed in `b4da4cc`. Local: on `ad25`, released in `build-20261114-210622`. Upstream: not
yet decided.
Closed: the scenario test of that build held (2026-11-14, fifth entry, 4): `FOOTPRINT`
records in the batch, `EDITSYMBOL` moving the current mark, three refused specs ("nothing
was made") and `create_schematic_symbol`, each equal to the saved library read apart from
the server; a part placed by `build_schematic` without `footprint` carried the library's
models and marks. The interplay it found with a part placed with `footprint` is A27.

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

**A29. A message with choices blocks Altium until someone answers it.** Since A24 a
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

**A30. A script launch per call is what brings Altium to the front.** A22's guard gives
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
