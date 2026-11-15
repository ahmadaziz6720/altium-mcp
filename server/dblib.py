"""Searching the component database behind an Altium .DbLib, read-only.

Altium's API exposes a DbLib's schema (IDatabaseLibDocument: its tables,
fields and parameters) but cannot list its parts: a table that is a
parameterised single-part lookup (UserWhereText=[<key>] = '{<key>}') returns
no rows to GetAllComponentKeys, as nothing is bound. The search therefore
queries the database itself, through the connection string the .DbLib holds,
by default in the tables the DbLib enables (the ones Altium places parts
from). Needs no Altium.

Read-only by construction: only a SELECT is ever sent. The database may live
on a shared drive that must never be written to.
"""
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# Columns searched for a term, besides the part-number field and the columns
# whose name says they hold a part number
SEARCHED_COLUMNS = ("description", "comment", "value", "manufacturer", "class", "category")


class DbLibError(Exception):
    pass


def read_text(dblib: Path) -> str:
    data = Path(dblib).read_bytes()
    for enc in ("utf-8-sig", "mbcs" if os.name == "nt" else "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1")


def table_info(text: str) -> List[dict]:
    """A DbLib's tables, in its order: [{name, enabled, key}]. key is the
    field a part number is looked up by - Key=, or the field of a
    UserWhereText "[<field>] = '{<field>}'" - or "" for a plain table."""
    tables = []
    for m in re.finditer(r"^\[Table\d+\][ \t]*\r?\n((?:(?!\[).*(?:\r?\n|$))*)", text, re.M):
        body = m.group(1)
        name = re.search(r"^TableName=(.*?)\s*$", body, re.M)
        if not name:
            continue
        enabled = re.search(r"^Enabled=(.*?)\s*$", body, re.M)
        key = (re.search(r"^Key=\[?([^\]\r\n]+?)\]?\s*$", body, re.M)
               or re.search(r"^UserWhereText=\[([^\]]+)\]\s*=", body, re.M))
        tables.append({
            "name": name.group(1),
            "enabled": bool(enabled) and enabled.group(1).lower() == "true",
            "key": key.group(1).strip() if key else "",
        })
    return tables


def part_key(tables: List[dict]) -> str:
    """The part-number field: the one the tables use most, or ""."""
    keys = [t["key"] for t in tables if t["key"]]
    return max(sorted(set(keys)), key=keys.count) if keys else ""


def connection_string(text: str, folder: Path) -> str:
    """The DbLib's connection string, a relative Data Source resolved against
    the DbLib's folder (Altium can store it relative)."""
    m = re.search(r"^ConnectionString=(.+?)\s*$", text, re.M)
    if not m:
        raise DbLibError("the DbLib holds no ConnectionString")
    conn = m.group(1)

    def resolve(src):
        path = src.group(2).strip().strip('"')
        if path and not os.path.isabs(path) and (Path(folder) / path).exists():
            return src.group(1) + str((Path(folder) / path).resolve())
        return src.group(0)

    return re.sub(r"(Data Source\s*=\s*)([^;]*)", resolve, conn, count=1, flags=re.I)


def quote_name(name: str) -> str:
    """A table or column name for SQL, in brackets."""
    return "[" + name.replace("]", "]]") + "]"


def quote_text(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def like_pattern(term: str) -> str:
    """'%term%' with the LIKE wildcards in term taken literally (bracket
    escapes, which Access and SQL Server both read)."""
    escaped = re.sub(r"([\[%_])", r"[\1]", str(term))
    return quote_text(f"%{escaped}%")


def is_part_number_column(name: str) -> bool:
    n = name.lower().replace(" ", "_")
    return "part_number" in n or "partnumber" in n or n in ("mpn", "pn")


_PS = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$conn = New-Object System.Data.OleDb.OleDbConnection($env:AMCP_CONN)
$conn.Open()
try {
  $cmd = $conn.CreateCommand()
  $cmd.CommandText = $env:AMCP_SQL
  $rdr = $cmd.ExecuteReader()
  $cols = @()
  for ($i = 0; $i -lt $rdr.FieldCount; $i++) { $cols += $rdr.GetName($i) }
  $rows = New-Object System.Collections.ArrayList
  $n = 0
  while ($n -lt [int]$env:AMCP_LIMIT -and $rdr.Read()) {
    $row = @()
    for ($i = 0; $i -lt $rdr.FieldCount; $i++) {
      $v = $rdr[$i]
      if ($v -is [System.DBNull]) { $v = '' }
      $row += [string]$v
    }
    [void]$rows.Add($row)
    $n++
  }
  $rdr.Close()
} finally { $conn.Close() }
ConvertTo-Json -Compress -Depth 4 -InputObject @{columns = $cols; rows = $rows.ToArray()}
"""


def run_select(conn: str, sql: str, limit: int = 200, timeout: int = 120) -> Tuple[List[str], List[Dict[str, str]]]:
    """(columns, rows) of a SELECT run through OLE DB; rows as {column: text}.
    Anything but a SELECT is refused, so this cannot change the database."""
    if not re.match(r"\s*select\s", sql, re.I) or ";" in sql:
        raise DbLibError("only a single SELECT statement is sent")
    env = dict(os.environ, AMCP_CONN=conn, AMCP_SQL=sql, AMCP_LIMIT=str(int(limit)))
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", _PS],
                           capture_output=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        raise DbLibError(f"the database did not answer within {timeout} s")
    out = r.stdout.decode("utf-8", errors="replace").strip()
    if r.returncode != 0 or not out:
        err = r.stderr.decode("utf-8", errors="replace")
        # PowerShell's error record: the message, then where in the script
        err = " ".join(err.split("At line:")[0].split())[:600]
        raise DbLibError(f"the database query failed: {err or 'no output'}")
    data = json.loads(out)
    cols = data.get("columns") or []
    if isinstance(cols, str):
        cols = [cols]
    rows = data.get("rows") or []
    # One row of one column comes back flattened by ConvertTo-Json
    if rows and not isinstance(rows[0], list):
        rows = [rows] if len(cols) > 1 else [[v] for v in rows]
    return cols, [dict(zip(cols, row)) for row in rows]


def columns_of(conn: str, table: str) -> List[str]:
    cols, _ = run_select(conn, f"SELECT TOP 1 * FROM {quote_name(table)}", limit=1)
    return cols


def search_sql(table: str, columns: List[str], key: str, term: str, max_rows: int) -> str:
    """The SELECT that finds term in a table's searched columns, or "" when
    the table has none of them."""
    hay = [c for c in columns
           if c.lower() in SEARCHED_COLUMNS or (key and c.lower() == key.lower()) or is_part_number_column(c)]
    if not hay:
        return ""
    where = " OR ".join(f"{quote_name(c)} LIKE {like_pattern(term)}" for c in hay)
    return f"SELECT TOP {int(max_rows)} * FROM {quote_name(table)} WHERE {where}"


# The DbLib's system fields (a bracketed ParameterName in its field
# mappings) that say how Altium places a part, by the name summary gives them
SYSTEM_FIELDS = {"description": "description", "library ref": "library_ref", "library path": "library_path",
                 "footprint ref": "footprint_ref", "footprint path": "footprint_path"}


def field_roles(text: str, table: str) -> Dict[str, str]:
    """{column, lower case: summary name} for the columns a table maps to
    one of SYSTEM_FIELDS, from the DbLib's "Options=" field mappings
    (FieldNameOnly, TableNameOnly, ParameterName "[Library Ref]" ...)."""
    roles = {}
    for line in text.splitlines():
        if not line.startswith("Options="):
            continue
        d = dict(kv.split("=", 1) for kv in line[len("Options="):].split("|") if "=" in kv)
        if d.get("TableNameOnly", "").lower() != table.lower():
            continue
        col = (d.get("FieldNameOnly") or "").strip().lower()
        param = (d.get("ParameterName") or "").strip()
        if col and param.startswith("[") and param.endswith("]"):
            role = SYSTEM_FIELDS.get(param.strip("[]").lower())
            if role:
                roles[col] = role
    return roles


def summary(row: Dict[str, str], key: str, roles: Dict[str, str] = None) -> Dict[str, str]:
    """The fields of a found part that say what it is and how Altium places
    it: the columns the DbLib maps to its system fields (roles, from
    field_roles), the others by their column names (they differ between
    databases); empty ones left out."""
    def first(test):
        return next((c for c, v in row.items() if v and test(c.lower())), None)

    out = {}
    for col, role in (roles or {}).items():
        val = next((v for c, v in row.items() if c.lower() == col and v), None)
        if val is not None and role not in out:
            out[role] = val
    picks = [
        ("part_number", (lambda c: c == key.lower()) if key else (lambda c: False)),
        ("description", lambda c: c == "description"),
        ("comment", lambda c: c == "comment"),
        ("value", lambda c: c == "value"),
        ("manufacturer", lambda c: c == "manufacturer" or c == "manufacturer 1"),
        ("manufacturer_part_number", lambda c: is_part_number_column(c) and c != key.lower()),
        ("library_ref", lambda c: c in ("library ref", "libref", "symbol") or "symbol ref" in c),
        ("library_path", lambda c: c == "library path" or "symbol path" in c),
        ("footprint_ref", lambda c: c in ("footprint ref", "footprint") or c.startswith("footprint ref")),
        ("footprint_path", lambda c: c.startswith("footprint path")),
    ]
    for name, test in picks:
        col = first(test)
        if col and name not in out:
            out[name] = row[col]
    # in the order of picks
    order = [name for name, _ in picks]
    return {name: out[name] for name in order if name in out}


def search(dblib: Path, term: str = "", part_number: str = "", table: str = "", all_tables: bool = False,
           max_rows: int = 20) -> dict:
    """Search a DbLib's database. With part_number: the first table holding
    that part number in the part-number field gives the part, every field.
    With term: the parts whose description, comment, value, manufacturer,
    class or part numbers hold it, up to max_rows per table, summarised.
    Neither: the DbLib's tables. table names one table; all_tables searches
    the tables the DbLib does not enable too."""
    dblib = Path(dblib)
    if dblib.suffix.lower() != ".dblib" or not dblib.is_file():
        raise DbLibError(f"dblib_path must be the full path of an existing .DbLib file: {dblib}")
    text = read_text(dblib)
    tables = table_info(text)
    if not tables:
        raise DbLibError("the DbLib names no tables")
    key = part_key(tables)
    conn = connection_string(text, dblib.parent)
    result = {"success": True, "dblib": str(dblib), "part_number_field": key,
              "tables": [dict(t) for t in tables]}
    names = [t["name"] for t in tables]
    if table and table not in names:
        raise DbLibError(f"the DbLib has no table '{table}'; it has {', '.join(names)}")
    enabled = [t["name"] for t in tables if t["enabled"]]
    others = [t["name"] for t in tables if not t["enabled"]]

    if part_number:
        if not key:
            raise DbLibError("the DbLib names no part-number field (no Key= or UserWhereText)")
        for t in [table] if table else enabled + others:
            cols = columns_of(conn, t)
            # Access reports an unknown column as "no value given for one or
            # more required parameters", so check the schema first
            col = next((c for c in cols if c.lower() == key.lower()), None)
            if not col:
                continue
            _, rows = run_select(conn, f"SELECT TOP 1 * FROM {quote_name(t)} WHERE "
                                       f"{quote_name(col)} = {quote_text(part_number)}", limit=1)
            if rows:
                result["part"] = {"table": t, "fields": {c: v for c, v in rows[0].items() if v != ""}}
                return result
        result["part"] = None
        result["note"] = f"no table holds {key} = {part_number}"
        return result

    if term:
        targets = [table] if table else (enabled + others if all_tables else enabled or others)
        matches, searched, skipped = [], [], []
        for t in targets:
            cols = columns_of(conn, t)
            sql = search_sql(t, cols, key, term, max_rows)
            if not sql:
                skipped.append(t)
                continue
            searched.append(t)
            _, rows = run_select(conn, sql, limit=max_rows)
            roles = field_roles(text, t)
            for row in rows:
                matches.append(dict(table=t, **summary(row, key, roles)))
        result.update(term=term, searched_tables=searched, match_count=len(matches), matches=matches)
        if skipped:
            result["tables_without_searchable_columns"] = skipped
        if any(len([m for m in matches if m["table"] == t]) >= max_rows for t in searched):
            result["note"] = f"a table reached max_rows ({max_rows}): narrow the term or raise max_rows"
        return result

    return result
