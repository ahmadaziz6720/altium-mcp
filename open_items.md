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

**Open: A11, A15, A23, A25 to A28, A31 to A34, A36 to A39, A41 to A44, A47, A48, A51 to A54, A56, A57, A59 to A73, A76.** Sorted
2026-11-23, the second entry of 2026-11-23 (the scenario test of group 1's second build,
`build-20261123-031122`): A74 held and closed; A48 (b) checked, the part built held and the
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

A run is planned below, `## Run 2026-11-22`: three groups on the owner's token rule, its
opening question answered, phase 2 under way: group 1 released, its scenario test run and
sorted, A48 (b) and A74 taken into it again.

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
- [ ] A26: committed
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
- [ ] A27: committed
- [ ] A71: committed
- [ ] A56 (a): committed
- [ ] Group 2: tests and release (build: )
- [ ] Group 2: scenario test (session id: ), its outcome sorted
- [ ] A57: committed
- [ ] A66: committed
- [ ] A41: committed
- [ ] A70: committed
- [ ] A28: committed
- [ ] A60 (a): committed
- [x] The recipes (A47, A51, A52, A54, A55, A59, A62 to A65, A67, A69, A34 (f), A56 (b)): committed (ba17162)
  - Of fourteen items only A55 had a script proved in full: it waits, the others stay Open,
    each saying what is missing. Built offline: 574 of the 583 offline tests run, OK; the 9
    that start processes or call the real status tool are to run before the release (the
    subagent's report; two of its first runs did call `get_server_status`'s test by mistake).
    The scenario test runs first A55, A34 (f) and A52's removal.
- [x] A75: committed (b764b10)
  - Stopped 2026-11-23 about 04:55 at the usage limit, taken up by the session's hourly
    self-check at 05:54 (Altium still blocked): A75 done offline, its tests in its item.
  - **Blocked since 06:0x: every step left needs Altium** (A26's line). The self-check cron
    was deleted with this line, as its own prompt says for a run written down Blocked.
  - The watcher for Altium's end and the subagents' watchdog were stopped by Claude Code
    for low memory (546 MB free, Altium 2.4 GB private) and not started again, so closing
    Altium no longer wakes the run: the owner says "lanjut", or opens a session with the
    sentence in A26's line. The session's hourly self-check (cron `5d89c99b`, gone with the
    session) is left to resume after the limit resets. It restarts no Altium that runs.
  - Does not travel by file: the commits since `6aa0661` are local, pushed at group 2's
    release; A26's fix is in its stash; the subagents' brief and the helper scripts are in
    the session's scratchpad. Not written yet: the run's `learned.md` entry, and as items at
    the run's end what A46, A45, A58 and A55 list as seen and left.
- [ ] Group 3: tests and release (build: )
- [ ] Group 3: scenario test (session id: ), its outcome sorted
- [ ] The report

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
Met again 2026-11-18 (findings 2026-11-18, second entry, point 3), build
`0.7.0-20261115-172812`: a free sheet from a `build_schematic` call with no `project_path`
was taken into the project by the next call with one, `detached_from` `""`; removing it by
script (`DM_RemoveSourceDocument`, the project saved) left the project file with two
`[DocumentN]` sections for one sheet, fixed by hand (A52).
Met again 2026-11-19 (findings 2026-11-19, second entry, point 4), in kind only: a script's
`CreateNewDocumentFromDocumentKind('SCH')` for a scratch sheet put it into the focused
project and left the project modified; a copied file opened by path stays free.
Met again 2026-11-19 (findings 2026-11-19, fourteenth entry, point 1), same build:
`build_schematic` without `project_path`, a parts-only call to read the pin map as the
description says, put its `Sheet1.SchDoc` into the focused project and left it modified;
`DM_FreeDocumentsProject` did not list it. Reported success.
Met again 2026-11-23 (findings 2026-11-23, point 7), build `0.7.0-20261123-001227`, at the
start of its scenario test: the project Altium had in focus, not a test project, modified
and holding a `Sheet1.SchDoc` with no path, unsaved. Left as found.

Tried 2026-11-23, backlog run: the cause found, a fix written and not run in Altium, so
still Open. Its code is in the stash `run 2026-11-22 A26` (`git stash list`), untracked
test included.

Cause, from a probe in AD25 on a temporary project that had the focus: `DM_CreateNewDocument('SCH')`
puts the sheet into the focused project and sets its flag, and from then on
`DM_FocusedProject` is Free Documents. `build_schematic` reads the focused project only
after that, so it finds nothing to take out and `detached_from` is `""`; with `project_path`
the add takes the sheet out later (by the code, not probed), when the flag is already set,
and so leaves it set.
Read before the sheet is made, the project is the right one: `DM_RemoveSourceDocument` by
the sheet's bare name then left it listed under Free Documents only, and `SetModified(False)`
left the project unmodified, both still so in the next script. Closing a sheet never saved
takes it out of neither list, a project's or Free Documents' (the `Sheet1.SchDoc` with no
path, not open, met above).

The fix in the stash, unproven: the focused project and its flag read before the sheet is
made, the sheet taken out and the flag put back in the same script; one `detached_from`, at
the top; `sheet` the path saved; a build with parts missing says in its error where the
sheet is. The tool listing with it 158,879 to 159,035 characters, 80 tools, no new argument.

Decided 2026-11-23 by the run, not the owner:
- after a failure the sheet is taken out of the project and stays open as a free document,
  named in the error, not closed, because a close leaves its entry in the list and the
  partial sheet is what shows what was placed;
- `detached_from` is the project's full path, because that is what `add_project_document`
  gives and two projects can share a file name.

Tests: offline, `test_project_setup`'s new test failed before ("'Sheet1.SchDoc' != ...
sheet is not the name the sheet was saved as"); with the stash the offline list 580, OK.
Live, the probe met the defect (the temporary project unmodified before; after, modified
and listing `Sheet1.SchDoc`); `tests/test_live_build_focus.py` (4 tests, in the stash) never
ran, before or after, and the DelphiScript was never compiled.

What stopped it: the probe's clean-up closed its project before the project's sheet, which
left the project listed in the workspace with no document. Opening that project again to
close it listed it twice, and Altium then showed "COM object that has been separated from
its underlying RCW cannot be used", whose one button sends a crash report. It was not
pressed, and the restart of Altium was refused by the permission system, so the bridge's
commands are refused behind that message (a read by `run_altium_script` still ran).

Left: Altium restarted by someone allowed to; `test_live_build_focus` seen failing on the
code without the stash's `.pas` and `main.py`, then passing with them; the live tests that
build (`test_live_project_setup`, `test_live_multipart`, `test_live_pin_map`,
`test_live_spec_file`, `test_live_libraries`, `test_live_symbol_footprint`); then Waiting.

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
Met again 2026-11-18 (findings 2026-11-18, second entry, point 4), build
`0.7.0-20261115-172812`: the project's `.SchLib` made by script
(`Client.OpenNewDocument('SCHLIB', ...)`, `SetFileName`, `DoFileSave`).
Met again 2026-11-19 (findings 2026-11-19, third entry, point 1), same build: a new `.PcbLib`
made by script with no project in focus joined none, and `add_project_document(create=False)`
then added it cleanly; it holds Altium's empty default footprint `PCBComponent_1` beside the
one made, and no tool deletes a footprint (A63), so a `create` should make it empty.

Decided 2026-11-22 by the owner (the opening answer of `## Run 2026-11-22`): taken, `add_project_document(create=True)` makes an empty `.SchLib` or `.PcbLib` too, no new argument.

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

### A56 - No tool sets a placed part's footprint or says which library it links to - OPEN 2026-11-22

A footprint given to a library symbol (A16, closed, the library side) does not reach the
parts already placed from it, and no tool sets or changes a placed part's footprint. Done by
`run_altium_script` (`AddSchImplementation`, `ModelType 'PCBLIB'`, `AddDataFileLink`,
`IsCurrent`, inside `SCHM_BeginModify`/`EndModify`, then `SaveDoc`; to repoint,
`RemoveSchImplementation` and a new implementation, no setter for a link's location found) in
five sessions: 2026-11-19 (first), point 6; (third), point 3, the compile then stale
(A48 (b)); (fifth), point 5, 11 parts; (seventh), points 1 and 5; (eighth), point 3.
Also missing (2026-11-19 (seventh), point 2): which library each placed part's footprint
links to. A script showed parts linked to a file that does not hold their footprint (an
older copy of a vendor library at another path), which neither `get_project_components`
(the footprint's name only) nor a compile reports.

Proposed: local; an `edit_schematic` op setting a placed part's footprint (name and
library), or one updating placed parts from their library symbol; a `footprint_library`
field in `get_project_components`, flagged when the linked file lacks the footprint. Not
decided.

Decided 2026-11-22 by the owner (the opening answer of `## Run 2026-11-22`): (a) taken, an `edit_schematic` op setting a placed part's footprint. (b), which library a part links to: a recipe in `docs/recipes.md` if a session's script is in the record, no field in `get_project_components` (the plan, not the owner).

(b) written 2026-11-23 in `docs/recipes.md`: `test_live_symbol_footprint`'s `read_models`,
the script that test ran on a placed part, one designator per call, read from
`ExportToParameters` (`ISCURRENT`, `MODELDATAFILE0`). On a placed part the test asserted the
name and the current mark, and the library's field on library symbols only: that field on a
placed part is not run, for the scenario test. Not covered: every part in one call, and
whether the linked file holds the footprint. A56 stays Open for (a), another step.

### A57 - Library reads return too much, or one symbol per call - OPEN 2026-11-22

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

### A61 - `edit_schematic` leaves Altium's focus or selection changed - OPEN 2026-11-22

2026-11-19 (eighth), point 1: `place_component` from a `.SchLib` left the focus on that
library; the next `get_screenshot(view_type="sch")` was refused ("Altium has a SCHLIB
document focused"), twice, each time one script of `Client.ShowDocument` on the sheet first.
Reported success. Near A26. 2026-11-19 (fifteenth), point 4: after `move_component` the last
part moved stayed selected, its handles in the next screenshot; harmless.

Proposed: local; the edit puts the sheet back in front and clears its selection. Not
decided.

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

### A66 - `create_schematic_symbol` reports a footprint linked by name that no library of the project holds - OPEN 2026-11-22

Sorted out of the entry of 2026-11-20, point 5: `footprints: ["<name>"]` reported the
footprint linked, `problems` empty, but the parts placed from the symbol had no footprint in
Altium: it was in an installed vendor `.PcbLib`, not in the project's libraries, and the link
held no location. Found by the owner. Fixed by setting `DatafileLink(0).Location` on the
symbol and the placed parts by script. Reported success with a wrong result (the caller
should also have given the library).

Proposed: local; a name-only footprint resolved at creation: the location filled from the
library that holds it, else a line in `problems`. Not decided.

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

### A70 - `run_altium_script`'s `OpenSchDoc` opens a `.SchLib` as a sheet - OPEN 2026-11-22

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

### A71 - Parts placed by the tools sometimes lack the flag that locks their body - OPEN 2026-11-22

2026-11-19 (eleventh), point 1: a click on a placed part's body selected its rectangle. In
the saved sheet a placed part's child primitives carry `IsNotAccesible=T`; on 24 parts
placed by script or by the server's tools the body did not, while parts placed in Altium's
own UI all had it. Not reproduced that day. 2026-11-20, points 1 and 6: reproduced; of six
parts placed by `edit_schematic` `place_component` that day three came in without it (an
8-pin symbol's rectangle and line, a 2-pin symbol's four arcs), and 19 more were found on
sheets drawn earlier by `build_schematic` and `edit_schematic`. Reported success. Not
readable from DelphiScript ("Undeclared identifier: IsNotAccesible"); found only in the saved
file. Workaround held: `Comp.PinsMoveable := True`, then `False`, inside
`PreProcess`/`PostProcess` and `SCHM_BeginModify`/`EndModify`, saved.

Proposed: local; the toggle after placing in `place_component` and `build_schematic`, and
`check_schematic` reporting a part with a child lacking the flag; a live test with the
symbols that lost it. Not decided.

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

### A46 - `build_schematic`'s `pin_map` is keyed by pin name and always returned whole - BUILT 2026-11-23, proof: the scenario test

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

### A58 - `build_schematic` and `edit_schematic` take no spec file - BUILT 2026-11-23, proof: the scenario test

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

### A45 - `build_schematic` places only part A of a multi-part symbol - BUILT 2026-11-23, proof: the scenario test

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

### A55 - `get_project_info` takes no `project_path` - BUILT 2026-11-23, proof: the scenario test

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

### A75 - `run_altium_script`'s `List1..3` keep strings, not objects - BUILT 2026-11-23, proof: the scenario test

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
