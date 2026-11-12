"""open_items.md and findings.md, as a page in the browser.

    python board.py                  serve on http://127.0.0.1:8767 and open it
    python board.py --port 9000 --no-open
    python board.py --check          parse both files, list what does not
                                     parse, exit 1 if anything does not

The markdown stays the source and the page only reads it. It reads both files
on every load and again whenever one changes on disk, so an edit made by hand
or by Claude shows within two seconds. Standard library only. Like the two
files it reads, it lives on ad25 and never goes upstream.

An item is a paragraph that opens with `**A<n>. <title>.**` under `## Open`,
`## Waiting` or `## Closed`; the section is its state, and the paragraphs
after it up to the next item are its text. A findings entry opens with
`**YYYY-MM-DD: <what was done>**`; its `Sorted into ...` line links it to the
items, `A6 (1, 2)` naming the entry's points. The intro's `**Open: A1 to A3,
...**` line is checked against the Open section. A paper size followed by
sheet, size, paper, format or page ("an A4 sheet") is not read as an item.
"""
import argparse
import json
import re
import subprocess
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ITEMS = ROOT / "open_items.md"
FINDINGS = ROOT / "findings.md"
BRANCH = "ad25"
STATES = {"Open": "open", "Waiting": "waiting", "Closed": "closed"}

ITEM_RE = re.compile(r"^\*\*(A\d+)\.\s+(.+?)\*\*\s*(.*)$", re.S)
ITEM_START_RE = re.compile(r"^\*\*A\d+\b")
ENTRY_RE = re.compile(r"^\*\*(\d{4}-\d{2}-\d{2}): (.+?)\*\*$", re.S)
CODE_RE = re.compile(r"\bA(\d+)\b(?! (?:sheet|size|paper|format|page))")
SORT_RE = re.compile(r"((?:A\d+, )*A\d+) \(([\d, ]+)\)")
POINT_RE = re.compile(r"^(\d+)\. (.*)$")
SUMMARY_RE = re.compile(r"^\*\*Open: (.+?)\.\*\*")
UPSTREAM_RE = re.compile(r"\b(PRs?|[Ii]ssues?) (#\d+(?:(?:,| and| or|, and) #\d+)*)")
STAMP_RE = re.compile(r"(?:…-|(\d{8})-)(\d{6})\b")


def blocks_of(lines):
    """('h1'|'h2', line, text) and ('p', line, [lines]) for a markdown file."""
    out, buf, start = [], [], 0
    for i, line in enumerate(lines, 1):
        if line.startswith("# ") or line.startswith("## "):
            if buf:
                out.append(("p", start, buf))
                buf = []
            out.append(("h1" if line.startswith("# ") else "h2", i,
                        line.split(" ", 1)[1].strip()))
        elif not line.strip() or line.strip() == "---":
            if buf:
                out.append(("p", start, buf))
                buf = []
        else:
            if not buf:
                start = i
            buf.append(line)
    if buf:
        out.append(("p", start, buf))
    return out


def code_key(code):
    return int(code[1:])


def codes_in(text, problems, where, known):
    found = []
    for m in CODE_RE.finditer(text):
        c = m.group(0)
        if c not in known:
            problems.append(f"{where}: names {c}, which is no item")
        elif c not in found:
            found.append(c)
    return found


def spec_codes(spec):
    """'A1 to A3, A5, A7 to A9' -> {'A1', 'A2', ...}, 'none' -> set(), or None
    if unreadable."""
    if spec.strip().lower() == "none":
        return set()
    out = set()
    for part in re.split(r",\s*|\s+and\s+", spec):
        m = re.fullmatch(r"A(\d+)(?: to A(\d+))?", part.strip())
        if not m:
            return None
        a = int(m.group(1))
        b = int(m.group(2) or a)
        out.update(f"A{n}" for n in range(a, b + 1))
    return out


def parse_items(problems):
    lines = ITEMS.read_text(encoding="utf-8").splitlines()
    title, intro, sections, items = None, [], [], []
    sec, last, seen = None, None, {}
    for kind, ln, val in blocks_of(lines):
        if kind == "h1":
            title = title or val
            continue
        if kind == "h2":
            sec = {"title": val, "state": STATES.get(val), "blocks": []}
            sections.append(sec)
            last = None
            continue
        text = "\n".join(val)
        m = ITEM_RE.match(text)
        if m:
            code = m.group(1)
            if sec is None:
                problems.append(f"open_items.md:{ln}: {code} is above the first section")
            elif sec["state"] is None:
                problems.append(f"open_items.md:{ln}: {code} is under '## {sec['title']}', "
                                "not Open, Waiting or Closed")
            if code in seen:
                problems.append(f"open_items.md:{ln}: {code} used twice "
                                f"(also line {seen[code]})")
            seen[code] = ln
            last = {"code": code, "line": ln,
                    "state": (sec or {}).get("state") or "unknown",
                    "section": (sec or {}).get("title"),
                    "title": " ".join(m.group(2).split()).rstrip("."),
                    "body": m.group(3).strip()}
            items.append(last)
            (sec["blocks"] if sec else intro).append({"item": code})
        elif ITEM_START_RE.match(text):
            problems.append(f"open_items.md:{ln}: an item heading that does not read "
                            "as '**A<n>. <title>.**'")
            (sec["blocks"] if sec else intro).append({"md": text, "line": ln})
        elif last is not None:
            last["body"] += "\n\n" + text
        else:
            (sec["blocks"] if sec else intro).append({"md": text, "line": ln})

    known = {x["code"] for x in items}
    for x in items:
        where = f"open_items.md:{x['line']} {x['code']}"
        x["refs"] = sorted((c for c in codes_in(x["title"] + " " + x["body"],
                                                problems, where, known)
                            if c != x["code"]), key=code_key)
        up = {}
        for m in UPSTREAM_RE.finditer(x["body"]):
            kind = "PR" if m.group(1).startswith("PR") else "issue"
            for n in re.findall(r"#(\d+)", m.group(2)):
                up.setdefault(int(n), kind)
        x["upstream"] = [{"n": n, "kind": k} for n, k in sorted(up.items())]
    if items:
        nums = {code_key(x["code"]) for x in items}
        missing = [f"A{n}" for n in range(1, max(nums) + 1) if n not in nums]
        if missing:
            problems.append("open_items.md: no item numbered " + ", ".join(missing))

    summary = None
    for b in intro:
        m = SUMMARY_RE.match(b.get("md", ""))
        if m:
            summary = b["md"]
            named = spec_codes(m.group(1))
            open_now = {x["code"] for x in items if x["state"] == "open"}
            if named is None:
                problems.append(f"open_items.md:{b['line']}: cannot read the list in "
                                f"'**Open: {m.group(1)}.**'")
            elif named != open_now:
                srt = lambda s: ", ".join(sorted(s, key=code_key))
                if named - open_now:
                    problems.append(f"open_items.md:{b['line']}: the Open line names "
                                    f"{srt(named - open_now)}, not under ## Open")
                if open_now - named:
                    problems.append(f"open_items.md:{b['line']}: ## Open holds "
                                    f"{srt(open_now - named)}, not in the Open line")
    return {"file": "open_items.md", "title": title or "open_items.md",
            "intro": intro, "sections": sections, "items": items, "summary": summary}


def parse_findings(known, problems, notes):
    lines = FINDINGS.read_text(encoding="utf-8").splitlines()
    title, intro, entries, cur = None, [], [], None
    for kind, ln, val in blocks_of(lines):
        if kind == "h1":
            title = title or val
            continue
        text = "\n".join(val)
        if kind == "h2":
            text = "**" + val + "**"
        m = ENTRY_RE.match(text) if kind == "p" else None
        if m:
            cur = {"n": len(entries) + 1, "line": ln, "date": m.group(1),
                   "title": " ".join(m.group(2).split()),
                   "lead": [], "points": [], "tail": [], "sorted": None, "items": []}
            entries.append(cur)
        elif cur is None:
            intro.append({"md": text})
        elif text.startswith("Sorted into"):
            cur["sorted"] = {"md": text, "line": ln}
        elif kind == "p" and POINT_RE.match(val[0]):
            for line in val:
                p = POINT_RE.match(line)
                if p:
                    cur["points"].append({"n": int(p.group(1)), "md": p.group(2)})
                else:
                    cur["points"][-1]["md"] += "\n" + line.strip()
        elif cur["points"]:
            cur["tail"].append(text)
        else:
            cur["lead"].append(text)

    for e in entries:
        where = f"findings.md:{e['line']} entry of {e['date']}"
        if e["sorted"] is None:
            notes.append(f"{where} '{e['title'][:60]}' is not sorted yet "
                         "(no 'Sorted into' line)")
            continue
        text = " ".join(e["sorted"]["md"].split())
        links = {}
        for m in SORT_RE.finditer(text):
            pts = [int(p) for p in re.findall(r"\d+", m.group(2))]
            for c in m.group(1).split(", "):
                links.setdefault(c, [])
                links[c] += [p for p in pts if p not in links[c]]
        for c in codes_in(text, problems, where, known):
            links.setdefault(c, [])
        have = {p["n"] for p in e["points"]}
        for c, pts in links.items():
            for p in pts:
                if p not in have:
                    problems.append(f"{where}: Sorted into {c} ({p}), and the entry "
                                    f"has no point {p}")
        e["items"] = [{"code": c, "points": sorted(p)} for c, p in links.items()
                      if c in known]
    return {"file": "findings.md", "title": title or "findings.md",
            "intro": intro, "entries": entries}


def build_list(items, findings):
    tags = {}
    try:
        out = subprocess.run(["git", "tag", "-l", "build-*"], cwd=ROOT,
                             capture_output=True, text=True).stdout.split()
        for t in out:
            m = re.fullmatch(r"build-(\d{8})-(\d{6})", t)
            if m:
                tags[m.group(2)] = (m.group(1), t)
    except OSError:
        pass
    builds = {}

    def note(text, key, val):
        for m in STAMP_RE.finditer(text):
            b = builds.setdefault(m.group(2), {"time": m.group(2), "date": None,
                                               "tag": None, "items": [], "entries": []})
            if m.group(1):
                b["date"] = m.group(1)
            if val not in b[key]:
                b[key].append(val)

    for x in items["items"]:
        note(x["body"], "items", x["code"])
    for e in findings["entries"]:
        note(" ".join([e["title"]] + e["lead"] + [p["md"] for p in e["points"]]
                      + e["tail"]), "entries", e["n"])
    for t, (d, tag) in tags.items():
        b = builds.setdefault(t, {"time": t, "date": d, "tag": None,
                                  "items": [], "entries": []})
        b["date"], b["tag"] = d, tag
    by_n = {e["n"]: e["date"].replace("-", "") for e in findings["entries"]}

    def order(b):
        # A build named only as `…-HHMMSS` sorts by the first entry naming it.
        d = b["date"] or min((by_n[n] for n in b["entries"]), default="99999999")
        return (d, b["time"])
    return sorted(builds.values(), key=order)


def load():
    problems, notes = [], []
    items = parse_items(problems)
    known = {x["code"] for x in items["items"]}
    findings = parse_findings(known, problems, notes)
    return {"items": items, "findings": findings,
            "builds": build_list(items, findings),
            "problems": problems, "notes": notes, "version": version(), **REPO}


def version():
    return "-".join(str(p.stat().st_mtime_ns) for p in (ITEMS, FINDINGS) if p.exists())


def repo_info():
    def url(remote):
        try:
            u = subprocess.run(["git", "remote", "get-url", remote], cwd=ROOT,
                               capture_output=True, text=True).stdout.strip()
        except OSError:
            return None
        m = re.search(r"github\.com[:/](.+?)(?:\.git)?$", u)
        return f"https://github.com/{m.group(1)}" if m else None
    return {"repo": url("origin"), "upstream": url("upstream"), "branch": BRANCH}


REPO = repo_info()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            self.send(200, PAGE, "text/html; charset=utf-8")
        elif path == "/api/data":
            self.send(200, json.dumps(load()))
        elif path == "/api/version":
            self.send(200, json.dumps({"version": version()}))
        else:
            self.send(404, "{}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=8767)
    ap.add_argument("--no-open", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        d = load()
        n = {}
        for x in d["items"]["items"]:
            n[x["state"]] = n.get(x["state"], 0) + 1
        print("open_items.md: " + ", ".join(f"{v} {k}" for k, v in n.items()))
        es = d["findings"]["entries"]
        print(f"findings.md: {len(es)} entries, "
              f"{sum(1 for e in es if e['sorted'] is None)} not sorted")
        for p in d["problems"]:
            print("PROBLEM", p)
        for p in d["notes"]:
            print("NOTE", p)
        sys.exit(1 if d["problems"] else 0)
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    except OSError:
        sys.exit(f"port {a.port} is taken: is the board already running? "
                 "Else pass --port.")
    url = f"http://127.0.0.1:{a.port}/"
    print(f"board on {url}  (Ctrl+C stops it)")
    if not a.no_open:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Altium MCP Board</title>
<style>
:root {
  color-scheme: light;
  --bg: #f5f5f3; --surface: #fcfcfb; --surface-2: #f0efec; --border: #e2e1dc;
  --text: #0b0b0b; --text-2: #52514e; --muted: #7a7974; --accent: #2a78d6;
  --hl: rgba(42, 120, 214, .13);
  --st-open: #ec835a; --st-waiting: #fab219; --st-closed: #0ca30c; --st-unknown: #d03b3b;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --bg: #121211; --surface: #1a1a19; --surface-2: #242423; --border: #34342f;
    --text: #f0efec; --text-2: #c3c2b7; --muted: #8f8e86; --accent: #3987e5;
    --hl: rgba(57, 135, 229, .2);
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --bg: #121211; --surface: #1a1a19; --surface-2: #242423; --border: #34342f;
  --text: #f0efec; --text-2: #c3c2b7; --muted: #8f8e86; --accent: #3987e5;
  --hl: rgba(57, 135, 229, .2);
}
* { box-sizing: border-box; }
html, body { margin: 0; background: var(--bg); color: var(--text);
  font: 14px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
code { font: 12.5px ui-monospace, Consolas, monospace; background: var(--surface-2);
  padding: 1px 4px; border-radius: 4px; }
header { position: sticky; top: 0; z-index: 5; background: var(--bg);
  border-bottom: 1px solid var(--border); }
.bar { max-width: 1120px; margin: 0 auto; padding: 10px 16px 0; display: flex;
  align-items: baseline; gap: 12px; }
.bar h1 { font-size: 15px; margin: 0; font-weight: 650; }
.bar .live { margin-left: auto; font-size: 12px; color: var(--muted); }
.live::before { content: ""; display: inline-block; width: 7px; height: 7px;
  border-radius: 50%; background: var(--st-closed); margin-right: 6px; }
.live.down::before { background: var(--st-unknown); }
nav { max-width: 1120px; margin: 0 auto; padding: 0 16px; display: flex; gap: 2px;
  overflow-x: auto; scrollbar-width: none; }
nav a { padding: 9px 12px 8px; color: var(--text-2); border-bottom: 2px solid transparent;
  white-space: nowrap; font-weight: 520; }
nav a:hover { text-decoration: none; color: var(--text); }
nav a.on { color: var(--text); border-bottom-color: var(--accent); }
nav a .n { font-size: 11px; color: var(--muted); margin-left: 5px; font-weight: 400; }
nav a .n.hot { color: var(--st-unknown); }
main { max-width: 1120px; margin: 0 auto; padding: 18px 16px 80px; }
h2 { font-size: 20px; margin: 0 0 2px; }
h3 { font-size: 15px; margin: 26px 0 8px; }
.sub { color: var(--muted); font-size: 12.5px; margin: 0 0 14px; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 16px; margin-bottom: 16px; }
.card h3 { margin-top: 0; }
.warn { border-color: var(--st-unknown); }
.note { border-color: var(--st-waiting); }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px; margin-bottom: 16px; }
.tile { background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 12px 14px; display: block; color: inherit; }
a.tile:hover { text-decoration: none; border-color: var(--accent); }
.tile .v { font-size: 26px; font-weight: 650; line-height: 1.2; }
.tile .k { color: var(--text-2); font-size: 12.5px; display: flex; align-items: center; gap: 6px; }
.dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; flex: none; }
.legend { display: flex; flex-wrap: wrap; gap: 14px; font-size: 12.5px;
  color: var(--text-2); margin-bottom: 12px; }
.legend span { display: inline-flex; align-items: center; gap: 6px; }
.age { display: grid; grid-template-columns: minmax(0, 2.2fr) minmax(0, 1fr); gap: 10px;
  align-items: center; padding: 4px 6px; border-radius: 6px; cursor: pointer; }
.age:hover { background: var(--hl); }
.age .who { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.age .who b { font-family: ui-monospace, Consolas, monospace; font-size: 12.5px; margin-right: 8px; }
.age .track { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--text-2); }
.age .fill { height: 10px; border-radius: 0 4px 4px 0; min-width: 4px; }
.tip { position: fixed; pointer-events: none; z-index: 20; background: var(--text);
  color: var(--bg); padding: 5px 8px; border-radius: 6px; font-size: 12px;
  white-space: nowrap; display: none; }
.tools { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 4px 0 14px; }
.chip { border: 1px solid var(--border); background: var(--surface); color: var(--text-2);
  border-radius: 999px; padding: 3px 10px; font: inherit; font-size: 12.5px; cursor: pointer;
  display: inline-flex; align-items: center; gap: 6px; }
.chip.off { opacity: .45; }
.chip.off .dot { background: transparent !important; outline: 1.5px solid var(--muted); }
input[type=search] { flex: 1; min-width: 160px; max-width: 320px; font: inherit;
  padding: 5px 10px; border: 1px solid var(--border); border-radius: 8px;
  background: var(--surface); color: var(--text); }
details.intro { margin-bottom: 8px; }
details.intro summary { cursor: pointer; color: var(--text-2); font-size: 13px; }
.prose { color: var(--text-2); font-size: 13.5px; }
.prose p { margin: 6px 0; }
.prose ul, .prose ol { margin: 6px 0; padding-left: 20px; }
.prose.clip { max-height: 7.5em; overflow: hidden; position: relative; cursor: pointer; }
.prose.clip::after { content: "more"; position: absolute; right: 0; bottom: 0; padding-left: 40px;
  background: linear-gradient(90deg, transparent, var(--bg) 40%); color: var(--accent); font-size: 12.5px; }
.rows { background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  overflow: hidden; margin: 8px 0 4px; }
.row { border-top: 1px solid var(--border); }
.row:first-child { border-top: 0; }
.row-head { display: grid; grid-template-columns: 46px 96px minmax(0, 1fr); gap: 10px;
  padding: 9px 14px; cursor: pointer; align-items: baseline; }
.row-head.f { grid-template-columns: 92px minmax(0, 1fr); }
.row-head:hover { background: var(--hl); }
.row .code { font: 600 13px ui-monospace, Consolas, monospace; }
.badge { display: inline-flex; align-items: center; gap: 6px; font-size: 12.5px;
  color: var(--text-2); white-space: nowrap; }
.row .title { min-width: 0; }
.meta { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px; }
.pill { font-size: 11.5px; color: var(--text-2); border: 1px solid var(--border);
  border-radius: 999px; padding: 0 7px; white-space: nowrap; display: inline-flex;
  align-items: center; gap: 5px; }
.pill.hot { color: var(--st-unknown); border-color: var(--st-unknown); }
.row .details { display: none; padding: 2px 14px 14px 70px; }
.row-head.f + .details { padding-left: 116px; }
.row.open .details { display: block; }
.row.open .row-head { background: var(--hl); }
.row.flash { animation: flash 1.6s ease-out; }
@keyframes flash { from { background: var(--hl); } to { background: transparent; } }
ol.pts { padding-left: 26px; margin: 8px 0; }
ol.pts li { margin: 6px 0; }
ol.pts li::marker { color: var(--muted); font-size: 12.5px; }
.to { margin-left: 6px; font-size: 12px; color: var(--muted); white-space: nowrap; }
.rel { margin-top: 12px; font-size: 12.5px; color: var(--text-2); display: flex; gap: 6px 18px; flex-wrap: wrap; }
.rel ul { margin: 2px 0 0; padding-left: 18px; }
.src { margin-top: 10px; font-size: 11.5px; color: var(--muted); }
a.ref { font-family: ui-monospace, Consolas, monospace; font-size: 12.5px; white-space: nowrap; }
.list-row { display: grid; grid-template-columns: 110px minmax(0, 1fr); gap: 10px;
  padding: 5px 0; border-top: 1px solid var(--border); align-items: baseline; font-size: 13px; }
.list-row:first-of-type { border-top: 0; }
.list-row .k { font-family: ui-monospace, Consolas, monospace; font-size: 12.5px; }
.list-row .refs { display: flex; flex-wrap: wrap; gap: 4px 12px; }
.empty { color: var(--muted); font-size: 13px; padding: 10px 0; }
@media (max-width: 640px) {
  .row-head { grid-template-columns: 40px minmax(0, 1fr); }
  .row-head .title { grid-column: 1 / -1; }
  .row-head.f { grid-template-columns: minmax(0, 1fr); }
  .row .details, .row-head.f + .details { padding-left: 14px; }
  .age { grid-template-columns: 1fr; gap: 2px; }
  .list-row { grid-template-columns: 1fr; gap: 2px; }
}
</style>
</head>
<body>
<header>
  <div class="bar"><h1>altium-mcp · Open Items</h1><span class="live" id="live">live</span></div>
  <nav id="nav"></nav>
</header>
<main id="main"></main>
<div class="tip" id="tip"></div>
<script>
const ORDER = ["open", "waiting", "closed"];
const LABEL = {open: "Open", waiting: "Waiting", closed: "Closed", unknown: "Unreadable"};
const S = {data: null, version: null, tab: "overview", focus: null, expanded: new Set(),
  clipOpen: new Set(), q: "", fq: "", hide: pref("hide", []), unsorted: false};
let ITEM = {}, CODES = new Set(), BYREF = {}, FED = {}, BUILD = {};

function pref(k, d) { try { const v = localStorage.getItem("adboard." + k);
  return v === null ? d : JSON.parse(v); } catch (e) { return d; } }
function save(k, v) { try { localStorage.setItem("adboard." + k, JSON.stringify(v)); } catch (e) {} }
function esc(s) { return String(s).replace(/[&<>"]/g, c =>
  ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c])); }
function col(st) { return `var(--st-${st})`; }
function dot(st) { return `<span class="dot" style="background:${col(st)}"></span>`; }
function ext(url, html) { return `<a href="${esc(url)}" target="_blank" rel="noopener">${html}</a>`; }
function plain(md) { return md.replace(/\*\*|`|\[([^\]]+)\]\([^)]*\)/g, (m, t) => t || ""); }

/* ---------- markdown ---------- */
function codes(t, ctx) {
  t = esc(t);
  if (ctx.nolink) return t;
  t = t.replace(/\bA\d+\b(?! (?:sheet|size|paper|format|page))/g, m => CODES.has(m) && m !== ctx.self
    ? `<a class="ref" href="#items/${m}">${m}</a>` : m);
  if (S.data.upstream) t = t.replace(/(^|[^\w/])#(\d+)\b/g, (all, pre, n) =>
    pre + ext(`${S.data.upstream}/issues/${n}`, "#" + n));
  return t;
}
function codeSpan(c, ctx) {
  const html = `<code>${esc(c)}</code>`;
  if (ctx.nolink || !S.data.repo) return html;
  if (/^[0-9a-f]{7,40}$/.test(c) && /[a-f]/.test(c)) return ext(`${S.data.repo}/commit/${c}`, html);
  const m = c.match(/(?:…-|\d{8}-)(\d{6})$/), b = m && BUILD[m[1]];
  if (b && b.tag) return ext(`${S.data.repo}/releases/tag/${b.tag}`, html);
  return html;
}
function link(text, href, ctx) {
  let url = href, out = true;
  if (!/^[a-z]+:/i.test(href)) {
    const [p, anchor] = href.split("#");
    if (p === "open_items.md") { url = "#items"; out = false; }
    else if (p === "findings.md") { url = "#findings"; out = false; }
    else if (S.data.repo) url = `${S.data.repo}/blob/${S.data.branch}/` +
      p.split("/").map(encodeURIComponent).join("/") + (anchor ? "#" + anchor : "");
  }
  const inner = inline(text, {...ctx, nolink: true});
  return out ? ext(url, inner) : `<a href="${esc(url)}">${inner}</a>`;
}
function inline(md, ctx) {
  ctx = ctx || {};
  const re = /`([^`]+)`|\[([^\]]+)\]\(([^)\s]+)\)|\*\*(.+?)\*\*|\*([^*\s][^*]*?)\*/g;
  let out = "", last = 0, m;
  while ((m = re.exec(md))) {
    out += codes(md.slice(last, m.index), ctx);
    if (m[1] !== undefined) out += codeSpan(m[1], ctx);
    else if (m[2] !== undefined) out += link(m[2], m[3], ctx);
    else if (m[4] !== undefined) out += `<strong>${inline(m[4], ctx)}</strong>`;
    else out += `<em>${inline(m[5], ctx)}</em>`;
    last = re.lastIndex;
  }
  return out + codes(md.slice(last), ctx);
}
function blocks(md, ctx) {
  let html = "", para = [], list = null;
  const flushP = () => { if (para.length) html += `<p>${inline(para.join(" "), ctx)}</p>`; para = []; };
  const flushL = () => { if (list) html += "<ul>" + list.map(x => `<li>${inline(x, ctx)}</li>`).join("") + "</ul>"; list = null; };
  for (const line of md.split("\n")) {
    const m = line.match(/^\s*[-*] (.*)$/);
    if (!line.trim()) { flushP(); flushL(); }
    else if (m) { flushP(); (list = list || []).push(m[1]); }
    else if (list && /^\s/.test(line)) list[list.length - 1] += " " + line.trim();
    else { flushL(); para.push(line.trim()); }
  }
  flushP(); flushL();
  return html;
}

/* ---------- data ---------- */
function index() {
  const d = S.data;
  ITEM = {}; BYREF = {}; FED = {}; BUILD = {};
  for (const x of d.items.items) ITEM[x.code] = x;
  CODES = new Set(Object.keys(ITEM));
  for (const x of d.items.items) for (const r of x.refs) (BYREF[r] = BYREF[r] || []).push(x.code);
  for (const e of d.findings.entries) for (const l of e.items)
    (FED[l.code] = FED[l.code] || []).push({e, points: l.points});
  for (const b of d.builds) BUILD[b.time] = b;
}
function count(rows) { const n = {}; for (const x of rows) n[x.state] = (n[x.state] || 0) + 1; return n; }
function refLink(code) {
  const x = ITEM[code];
  return `<a class="ref" href="#items/${code}" data-tip="${esc(x ? plain(x.title) : "no such item")}">` +
    `${dot(x ? x.state : "unknown")} ${code}</a>`;
}
function unsorted() { return S.data.findings.entries.filter(e => !e.sorted); }
function buildName(b) { return b.date ? `${b.date}-${b.time}` : `…-${b.time}`; }

/* ---------- render ---------- */
function render() {
  const n = count(S.data.items.items), un = unsorted().length;
  const tab = (key, label, badge, hot) => `<a href="#${key}" class="${S.tab === key ? "on" : ""}">${label}` +
    (badge !== undefined ? `<span class="n${hot ? " hot" : ""}">${badge}</span>` : "") + `</a>`;
  document.getElementById("nav").innerHTML = tab("overview", "Overview") +
    tab("items", "Items", (n.open || 0) + (n.waiting || 0)) +
    tab("findings", "Findings", un ? `${un} not sorted` : S.data.findings.entries.length, un > 0);
  const main = document.getElementById("main"), y = window.scrollY;
  main.innerHTML = problems() + (S.tab === "overview" ? overview() : S.tab === "items" ? items()
    : S.tab === "findings" ? findings() : `<p class="empty">No tab ${esc(S.tab)}.</p>`);
  if (S.focus) focusRow(); else window.scrollTo(0, y);
}
function problems() {
  const p = S.data.problems;
  if (!p.length) return "";
  return `<div class="card warn"><h3>${p.length} thing${p.length > 1 ? "s" : ""} the board cannot read</h3>` +
    `<div class="prose"><ul>${p.map(x => `<li>${esc(x)}</li>`).join("")}</ul></div></div>`;
}

function overview() {
  const d = S.data, all = d.items.items, n = count(all), es = d.findings.entries, un = unsorted();
  let h = `<h2>Overview</h2><p class="sub">${all.length} items in <code>open_items.md</code>, ` +
    `${es.length} entries in <code>findings.md</code>, read from the markdown.</p>`;
  h += `<div class="tiles">` + ORDER.map(st => `<a class="tile" href="#items" data-only="${st}"><div class="v">${n[st] || 0}</div>` +
    `<div class="k">${dot(st)}${LABEL[st]}</div></a>`).join("") +
    `<a class="tile" href="#findings"><div class="v">${es.length}</div><div class="k">Findings entries` +
    (un.length ? `, <span style="color:var(--st-unknown)">${un.length} not sorted</span>` : ", all sorted") + `</div></a></div>`;
  if (un.length) h += `<div class="card note"><h3>Entries not sorted into items yet</h3>` +
    `<p class="sub">No <code>Sorted into</code> line under them. Sorting them is the first work of a session here.</p>` +
    un.map(e => `<div class="list-row"><a class="k" href="#findings/${e.n}">${e.date}</a><span>${inline(e.title)}</span></div>`).join("") + `</div>`;
  if (d.items.summary) h += `<div class="card"><h3>Where things stand</h3><div class="prose">` +
    `${blocks(d.items.summary, {})}</div></div>`;
  // items by how many entries were sorted into them
  const met = all.map(x => ({x, k: (FED[x.code] || []).length}))
    .sort((a, b) => b.k - a.k || parseInt(a.x.code.slice(1)) - parseInt(b.x.code.slice(1)));
  const max = Math.max(1, ...met.map(m => m.k));
  h += `<div class="card"><h3>Met in findings entries</h3><p class="sub">How many entries were sorted into each item; ` +
    `an item a session runs into again and again is worth fixing first.</p><div class="legend">` +
    ORDER.map(st => `<span>${dot(st)}${LABEL[st]}</span>`).join("") + `</div>` +
    met.map(({x, k}) => `<div class="age" data-href="#items/${x.code}" data-tip="${x.code} · ${LABEL[x.state]} · ${k} entr${k === 1 ? "y" : "ies"}">` +
      `<div class="who"><b>${x.code}</b>${inline(x.title, {nolink: true})}</div>` +
      `<div class="track"><div class="fill" style="width:${k / max * 80}%;background:${col(x.state)}"></div>${k}</div></div>`).join("") + `</div>`;
  // upstream issues and pull requests
  const up = {};
  for (const x of all) for (const u of x.upstream) (up[u.n] = up[u.n] || {kind: u.kind, items: []}).items.push(x.code);
  const nums = Object.keys(up).map(Number).sort((a, b) => a - b);
  h += `<div class="card"><h3>Upstream</h3><p class="sub">Issues and pull requests at <code>coffeenmusic/altium-mcp</code> ` +
    `the items name.</p>` + (nums.length ? nums.map(k => `<div class="list-row"><span class="k">` +
      (d.upstream ? ext(`${d.upstream}/issues/${k}`, `${up[k].kind} #${k}`) : `${up[k].kind} #${k}`) +
      `</span><span class="refs">${up[k].items.map(refLink).join("")}</span></div>`).join("")
      : `<p class="empty">No item names one.</p>`) + `</div>`;
  // builds
  h += `<div class="card"><h3>Releases</h3><p class="sub">Each release stamp the two files name, with the items and entries that name it. ` +
    `A tagged release links to its release page.</p>` + (d.builds.length ? d.builds.map(b => `<div class="list-row"><span class="k">` +
      (b.tag && d.repo ? ext(`${d.repo}/releases/tag/${b.tag}`, buildName(b)) : buildName(b)) + `</span><span class="refs">` +
      b.items.map(refLink).join("") +
      b.entries.map(n => `<a href="#findings/${n}" class="ref">entry ${es[n - 1].date} #${n}</a>`).join("") +
      (b.tag ? "" : `<span class="pill">no tag</span>`) + `</span></div>`).join("")
      : `<p class="empty">None named.</p>`) + `</div>`;
  return h;
}

function items() {
  const r = S.data.items, n = count(r.items), q = S.q.trim().toLowerCase();
  const show = x => !S.hide.includes(x.state) && (!q || [x.code, x.title, x.body].join(" ").toLowerCase().includes(q));
  let h = `<h2>${esc(r.title)}</h2><p class="sub"><code>${esc(r.file)}</code> · the section an item sits under is its state.</p>`;
  h += `<div class="tools">` + ORDER.concat(["unknown"]).filter(st => n[st]).map(st =>
    `<button class="chip ${S.hide.includes(st) ? "off" : ""}" data-st="${st}">${dot(st)}${LABEL[st]} ${n[st]}</button>`).join("") +
    `<input type="search" id="q" placeholder="Search the items" value="${esc(S.q)}"></div>`;
  if (r.intro.length) h += `<details class="intro"><summary>About this file</summary><div class="prose">` +
    r.intro.map(b => b.md ? blocks(b.md, {}) : "").join("") + `</div></details>`;
  r.sections.forEach((s, si) => {
    const its = s.blocks.filter(b => b.item).map(b => ITEM[b.item]), vis = its.filter(show);
    if (its.length && !vis.length) { h += `<h3>${esc(s.title)} <span class="sub">${its.length} hidden</span></h3>`; return; }
    h += `<h3>${esc(s.title)}${its.length ? ` <span class="sub">${vis.length} of ${its.length}</span>` : ""}</h3>`;
    let run = [];
    const flush = () => { if (run.length) h += `<div class="rows">${run.join("")}</div>`; run = []; };
    s.blocks.forEach((b, bi) => {
      if (b.item) { const x = ITEM[b.item]; if (show(x)) run.push(itemRow(x)); return; }
      flush();
      const id = `items:${si}:${bi}`, long = b.md.length > 480 && !S.clipOpen.has(id);
      h += `<div class="prose${long ? " clip" : ""}" data-clip="${id}">${blocks(b.md, {})}</div>`;
    });
    flush();
    if (!s.blocks.length) h += `<p class="empty">None.</p>`;
  });
  return h;
}
function itemRow(x) {
  const id = "items/" + x.code, ctx = {self: x.code}, fed = FED[x.code] || [], by = BYREF[x.code] || [];
  const meta = x.upstream.map(u => `<span class="pill">${u.kind} #${u.n}</span>`)
    .concat(fed.length ? [`<span class="pill">${fed.length} findings entr${fed.length === 1 ? "y" : "ies"}</span>`] : []);
  return `<div class="row${S.expanded.has(id) ? " open" : ""}" id="r-${id}" data-id="${id}">` +
    `<div class="row-head"><span class="code">${esc(x.code)}</span><span class="badge">${dot(x.state)}${LABEL[x.state]}</span>` +
    `<span class="title">${inline(x.title, ctx)}${meta.length ? `<span class="meta">${meta.join("")}</span>` : ""}</span></div>` +
    `<div class="details"><div class="prose">${blocks(x.body, ctx)}</div>` +
    (x.refs.length || by.length || fed.length ? `<div class="rel">` +
      (x.refs.length ? `<span>Names ${x.refs.map(refLink).join(", ")}</span>` : "") +
      (by.length ? `<span>Named by ${by.map(refLink).join(", ")}</span>` : "") +
      (fed.length ? `<div style="flex-basis:100%">From findings:<ul>${fed.map(f =>
        `<li><a href="#findings/${f.e.n}">${f.e.date}: ${inline(f.e.title, {nolink: true})}</a>` +
        (f.points.length ? ` <span class="to">point${f.points.length > 1 ? "s" : ""} ${f.points.join(", ")}</span>` : "") +
        `</li>`).join("")}</ul></div>` : "") + `</div>` : "") +
    `<div class="src">open_items.md:${x.line} · under ## ${esc(x.section || "?")}</div></div></div>`;
}

function findings() {
  const r = S.data.findings, q = S.fq.trim().toLowerCase(), un = unsorted().length;
  const show = e => (!S.unsorted || !e.sorted) && (!q || [e.date, e.title, ...e.lead, ...e.points.map(p => p.md),
    ...e.tail].join(" ").toLowerCase().includes(q));
  const list = r.entries.slice().reverse().filter(show);
  let h = `<h2>${esc(r.title)}</h2><p class="sub"><code>${esc(r.file)}</code> · newest first · ` +
    `the <code>Sorted into</code> line links an entry to its items.</p>`;
  h += `<div class="tools"><button class="chip ${S.unsorted ? "" : "off"}" id="unsorted">Only not sorted (${un})</button>` +
    `<input type="search" id="fq" placeholder="Search the entries" value="${esc(S.fq)}"></div>`;
  if (r.intro.length) h += `<details class="intro"><summary>About this file</summary><div class="prose">` +
    r.intro.map(b => blocks(b.md, {})).join("") + `</div></details>`;
  h += list.length ? `<div class="rows">${list.map(entryRow).join("")}</div>` : `<p class="empty">No entry.</p>`;
  return h;
}
function entryRow(e) {
  const id = "findings/" + e.n, to = {};
  for (const l of e.items) for (const p of l.points) (to[p] = to[p] || []).push(l.code);
  const meta = e.sorted ? e.items.map(l => refLink(l.code)) : [`<span class="pill hot">not sorted yet</span>`];
  return `<div class="row${S.expanded.has(id) ? " open" : ""}" id="r-${id}" data-id="${id}">` +
    `<div class="row-head f"><span class="code">${e.date}</span><span class="title">${inline(e.title, {nolink: true})}` +
    `<span class="meta">${meta.join("")}</span></span></div>` +
    `<div class="details"><div class="prose">${e.lead.map(t => blocks(t, {})).join("")}` +
    (e.points.length ? `<ol class="pts">${e.points.map(p => `<li value="${p.n}">${inline(p.md.replace(/\n/g, " "), {})}` +
      (to[p.n] ? `<span class="to">→ ${to[p.n].map(refLink).join(", ")}</span>` : "") + `</li>`).join("")}</ol>` : "") +
    e.tail.map(t => blocks(t, {})).join("") +
    (e.sorted ? `<p style="color:var(--muted)">${inline(e.sorted.md.replace(/\n/g, " "), {})}</p>` : "") + `</div>` +
    `<div class="src">findings.md:${e.line} · entry ${e.n} of ${S.data.findings.entries.length}</div></div></div>`;
}

function focusRow() {
  const id = S.focus; S.focus = null;
  const el = document.getElementById("r-" + id);
  if (!el && (S.hide.length || S.q || S.fq || S.unsorted)) {
    S.hide = []; save("hide", S.hide); S.q = S.fq = ""; S.unsorted = false;
    S.expanded.add(id); S.focus = id; render(); return;
  }
  if (!el) return;
  S.expanded.add(id);
  el.classList.add("open", "flash");
  el.scrollIntoView({block: "center"});
}

/* ---------- events ---------- */
const tip = document.getElementById("tip");
document.addEventListener("mousemove", e => {
  const t = e.target.closest("[data-tip]");
  if (!t) { tip.style.display = "none"; return; }
  tip.textContent = t.dataset.tip; tip.style.display = "block";
  tip.style.left = Math.min(e.clientX + 12, innerWidth - tip.offsetWidth - 8) + "px";
  tip.style.top = (e.clientY + 14) + "px";
});
document.addEventListener("click", e => {
  const only = e.target.closest("[data-only]");
  if (only) { S.hide = ORDER.concat(["unknown"]).filter(s => s !== only.dataset.only); save("hide", S.hide); return; }
  if (e.target.closest("a")) return;
  const href = e.target.closest("[data-href]");
  if (href) { location.hash = href.dataset.href.slice(1); return; }
  const chip = e.target.closest(".chip[data-st]");
  if (chip) { const st = chip.dataset.st;
    S.hide = S.hide.includes(st) ? S.hide.filter(s => s !== st) : S.hide.concat([st]); save("hide", S.hide); render(); return; }
  if (e.target.id === "unsorted") { S.unsorted = !S.unsorted; render(); return; }
  const clip = e.target.closest(".prose.clip");
  if (clip) { S.clipOpen.add(clip.dataset.clip); clip.classList.remove("clip"); return; }
  const head = e.target.closest(".row-head");
  if (head) { const r = head.parentElement, id = r.dataset.id;
    r.classList.toggle("open"); r.classList.contains("open") ? S.expanded.add(id) : S.expanded.delete(id); }
});
document.addEventListener("input", e => {
  if (e.target.id !== "q" && e.target.id !== "fq") return;
  const key = e.target.id, pos = e.target.selectionStart;
  S[key] = e.target.value; render();
  const q = document.getElementById(key); q.focus(); q.setSelectionRange(pos, pos);
});
function route() {
  const h = decodeURIComponent(location.hash.slice(1)) || "overview";
  const i = h.indexOf("/");
  S.tab = i < 0 ? h : h.slice(0, i);
  S.focus = i < 0 ? null : h;
  if (i < 0) window.scrollTo(0, 0);
  if (S.data) render();
}
async function fetchData() {
  const r = await fetch("/api/data");
  S.data = await r.json(); S.version = S.data.version; index(); render();
}
window.addEventListener("hashchange", route);
setInterval(async () => {
  const live = document.getElementById("live");
  try {
    const v = (await (await fetch("/api/version")).json()).version;
    live.className = "live"; live.textContent = "live";
    if (v !== S.version) await fetchData();
  } catch (e) { live.className = "live down"; live.textContent = "server stopped"; }
}, 2000);
route();
fetchData();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
