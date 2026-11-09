# CLAUDE.md

Guidance for working in this repository.

## What this is

The owner's fork of [`coffeenmusic/altium-mcp`](https://github.com/coffeenmusic/altium-mcp),
run on **Altium Designer 25**. It is registered in Claude Code as `altium-mcp` (scope local,
in the owner's project). The code, its conventions and its tests are upstream's: read
`README.md`, `dev/README.md` and `PLACEMENT_TOOL_REVIEW.md` before changing it.

How it works, in one paragraph: `server/main.py` (Python, FastMCP) writes a JSON request
into its exchange folder and has Altium run the DelphiScript project
`server/AltiumScript/Altium_API.PrjScr` (`X2.EXE -RScriptingSystem:RunScript`), which calls
Altium's PCB/SCH API and writes the response. A fix is therefore in Python, in DelphiScript,
or both. Several tools (OutJob, `.PcbLib` reading) read files on disk without Altium.

**Read [`open_items.md`](open_items.md) before assuming the server works for a task.** What
sessions found is in [`findings.md`](findings.md). `python board.py` shows both as a page
(read-only, on `127.0.0.1:8767`); `python board.py --check` lists what does not parse,
including an `**Open: …**` line that no longer matches the Open section: run it after
editing either file.

## Branches and remotes

Commits and pull requests follow the `git-workflow:pr` skill (config in
`.claude/git-workflow.json`): read it before the first edit or the first commit. A new
branch and its name are the owner's call. A PR here goes to `upstream`, from a branch on the
fork: the owner opens it from the compare link
`coffeenmusic/altium-mcp/compare/main...ahmadaziz6720:<branch>`.

- `origin` = the fork `ahmadaziz6720/altium-mcp`, `upstream` = `coffeenmusic/altium-mcp`.
- `main` tracks `upstream/main` and carries nothing of ours.
- `ad25` is what is released and run here: upstream plus local fixes, and this file,
  `findings.md`, `open_items.md` and `board.py`.
- **A PR branch starts from `upstream/main`** and holds only the fix (cherry-picked or
  squashed from `ad25`). It is named in `.claude/git-workflow.json`'s `branches` before
  the first commit on it. These three files, `board.py` and `.claude/git-workflow.json`
  never go upstream. Upstream's `.gitignore` ignores `*.json`, so that one is added with
  `git add -f`.
- Update: `git fetch upstream`, `git rebase upstream/main` on `ad25`, run the offline tests
  (below), then release.

## Tests

The offline unit tests need no Altium. Run them from `server/` with the command in
`.github/workflows/tests.yml` (the list of test modules is there), in a venv holding
`requirements.txt`. A change to a DelphiScript or to a call that reaches Altium also gets a
live test in Altium Designer 25 that fails without the change.

## Release and run

**A release is a copy that is registered**, the one sessions in the owner's project run. A
checkout used for a live test while a fix is in progress is not one. A release is named by
its stamp, the time it was made as `yyyyMMdd-HHmmss`; its tag is `build-<stamp>`. `<v>` below
is `"version"` in `manifest.json`, upstream's. Releases run from a copy, never from this
clone, so an edit here never reaches a running session.

1. **From a clean tree, at a commit pushed to `origin/ad25`.**
2. **Copy that commit into a new folder**, and record what it is:
   ```
   $dir = "$env:LOCALAPPDATA\altium-mcp\bin\<v>-<stamp>"
   New-Item -ItemType Directory $dir
   git archive <commit> | tar -x -C $dir
   "<v>-ad25-<stamp> <commit>" | Set-Content "$dir\BUILD.txt"
   ```
   The server finds its DelphiScript project beside `server/main.py`, so the copy runs its
   own scripts. A `script_path` in `%USERPROFILE%\.altium-mcp\config.json` overrides that
   and would run another copy's scripts: there must be none (only a hand-picked path is
   ever written there).
3. **The venv**: `python "$dir\start_server.py" --build` once, and it ends without error. The
   venv is kept in `%USERPROFILE%\.altium-mcp\venvs\`, keyed by the requirements, so a
   release with the same requirements reuses it.
4. **The tag and the registration, in one question to the owner.** On the yes: register
   `altium-mcp` (scope local, in the owner's project) again on the new copy, run from
   that project's folder, as local scope belongs to the folder it is run in:
   `claude mcp remove altium-mcp -s local`, then
   `claude mcp add altium-mcp -s local -- python "<dir>\start_server.py"`. Then tag the
   commit and push the tag alone:
   ```
   git tag -a build-<stamp> -m "build <stamp>" <commit>
   git push origin refs/tags/build-<stamp>
   git ls-remote --tags origin 'build-<stamp>*'
   ```
5. **The release page on the fork, with no files attached**, a record only. `gh` has no
   default repo here (two remotes), so name it:
   ```
   gh release create build-<stamp> --repo ahmadaziz6720/altium-mcp --verify-tag --title "build <stamp>" --notes-file <file>
   ```
   The notes: the upstream commit it stands on (`git merge-base upstream/main <commit>`),
   the A-items this release fixes, each moved to Waiting naming the build, the server
   commits since the previous `build-` tag (`git log --oneline <prev>..<commit> -- server`),
   and "Scenario test: not run yet". English, as the fork is public, and naming no repo,
   file or design of the owner's, as `findings.md`'s top says.
6. **A short check** in Altium Designer 25, in a new session there: `get_server_status`
   shows `script_path` inside the new folder, then one read on an open project
   (`get_project_info`) and one on a board (`get_board_summary`). The server is not
   reloaded in a running session.
7. **After the scenario test**, when its entry is sorted here, its result per item replaces
   "Scenario test: not run yet" (`gh release edit build-<stamp> --repo
   ahmadaziz6720/altium-mcp --notes-file <file>`).

**Rollback**: register the `start_server.py` of an earlier release folder again; its tag
names the commit. Keep the release folders. **A rebase onto upstream** (above) leaves the
old tags off `ad25`'s history. They stay on the remote as the record of what was released,
and the release pages with them.

## Findings, and the entries other sessions leave here

Sessions that use the server write into `findings.md` without being asked; they run in
other repos and never commit here (the owner's global `CLAUDE.md`).

- **Commit what they left, at the start of a session here, before any work, asking the
  owner first.** Read `git status`: a change to `findings.md` or `open_items.md` this
  session did not make is such an entry. Read its diff, ask, and on the owner's yes commit
  it alone on `ad25` with a message that says whose entries they are, then start.
- **Sort the entries into items**, as `findings.md`'s top says: each point to an A-item in
  `open_items.md`, new or existing, and a `Sorted into …` line under the entry.
- **An item that is fixed** moves to Waiting with its commit; to Closed when the fix ran and
  held in a session and, if it was sent upstream, the PR is settled.
