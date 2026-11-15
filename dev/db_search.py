"""Search the component database behind a .DbLib - read-only.

The search itself is server/dblib.py, which the server's search_dblib tool
runs; this is its command line, and finds the DbLib in a running Altium when
none is given. See server/dblib.py for why the database is queried directly
and how it stays read-only.

Nothing here is specific to one database: the part-number field comes from
the tables' Key= or UserWhereText, and the DbLib itself from Altium's
IntegratedLibraryManager unless given with --dblib or ALTIUM_DBLIB.

Usage:
    python dev/db_search.py --tables
    python dev/db_search.py --columns <TABLE>
    python dev/db_search.py --find "LED DRIVER" [--table <TABLE>] [--all-tables] [--max 40]
    python dev/db_search.py --part <PART NUMBER>
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "server"))

import dblib as _dblib  # noqa: E402

DBLIB_ENV = "ALTIUM_DBLIB"
part_key = _dblib.part_key

# Lists the .DbLib files installed in Altium, '|'-separated
_INSTALLED_DBLIBS = """IntMan := IntegratedLibraryManager;
S1 := '';
for I1 := 0 to IntMan.InstalledLibraryCount - 1 do
begin
    S2 := IntMan.InstalledLibraryPath(I1);
    if (UpperCase(ExtractFileExt(S2)) = '.DBLIB') then
        S1 := S1 + S2 + '|';
end;
ResultText := S1;"""


def installed_dblibs():
    """The .DbLib files installed in Altium, from its IntegratedLibraryManager
    (Altium must be running). Altium's own preference files are not read:
    where they keep the list differs between versions."""
    import sandbox_runner as sr
    sr.inject(_INSTALLED_DBLIBS)
    if not sr.run(timeout=60, quiet=True):
        return []
    text = sr.SANDBOX_RESULT.read_text(encoding="utf-8", errors="replace").strip()
    return [Path(p) for p in text.split("|") if p.strip()]


def resolve_dblib(explicit=None):
    """Locate the .DbLib: explicit path, the ALTIUM_DBLIB environment
    variable, or the one DbLib installed in Altium."""
    for cand in (explicit, os.environ.get(DBLIB_ENV)):
        if cand and Path(cand).is_file():
            return Path(cand)
    found = [p for p in installed_dblibs() if p.is_file()]
    if len(found) == 1:
        return found[0]
    if found:
        listing = "\n  ".join(str(p) for p in found)
        raise SystemExit(f"Several DbLibs are installed in Altium; pass --dblib PATH "
                         f"or set {DBLIB_ENV} to one of:\n  {listing}")
    raise SystemExit(
        f"Could not locate a .DbLib (none installed in a running Altium). "
        f"Pass --dblib PATH or set {DBLIB_ENV}."
    )


def table_info(dblib):
    """The DbLib's tables: [{name, enabled, key}] (see server/dblib.py)."""
    return _dblib.table_info(_dblib.read_text(dblib))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dblib")
    ap.add_argument("--tables", action="store_true", help="list tables")
    ap.add_argument("--columns", metavar="TABLE")
    ap.add_argument("--find", metavar="TERM")
    ap.add_argument("--part", metavar="PART_NUMBER")
    ap.add_argument("--table", help="restrict --find to one table")
    ap.add_argument("--all-tables", action="store_true",
                    help="--find also searches the tables the DbLib does not enable")
    ap.add_argument("--max", type=int, default=40)
    a = ap.parse_args()

    dblib = resolve_dblib(a.dblib)
    print(f"# dblib: {dblib}\n")
    try:
        if a.columns:
            text = _dblib.read_text(dblib)
            for c in _dblib.columns_of(_dblib.connection_string(text, dblib.parent), a.columns):
                print(c)
            return
        if not (a.part or a.find):
            if not a.tables:
                ap.print_help()
                return
            for t in _dblib.search(dblib)["tables"]:
                print(f"{'enabled ' if t['enabled'] else '        '}{t['name']}")
            return
        out = _dblib.search(dblib, term=a.find or "", part_number=a.part or "", table=a.table or "",
                            all_tables=a.all_tables, max_rows=a.max)
    except _dblib.DbLibError as e:
        raise SystemExit(str(e))

    if a.part:
        if not out["part"]:
            print("not found")
            return
        print(f"## {out['part']['table']}")
        for k, v in out["part"]["fields"].items():
            print(f"  {k:<26} {v}")
        return

    for t in out["searched_tables"]:
        rows = [m for m in out["matches"] if m["table"] == t]
        if not rows:
            continue
        print(f"## {t}  ({len(rows)} match)")
        for r in rows:
            print(f"  {r.get('part_number', ''):<12} {r.get('description', '')[:46]:<46} "
                  f"{r.get('manufacturer_part_number', '')[:20]:<20} {r.get('library_ref', '')[:20]:<20} "
                  f"{r.get('footprint_ref', '')}")
        print()


if __name__ == "__main__":
    main()
