"""Offline tests of the DbLib search (A15): reading a .DbLib's tables and
part-number field, the SQL it sends (a SELECT only, names and terms
quoted), and the summary of a found part. One test searches a real database,
a CSV file read through the Access database engine's text driver, and is
skipped where that engine is not installed (as on CI)."""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import dblib  # noqa: E402

DBLIB = """[OutputDatabaseLinkFile]
Version=1.1

[DatabaseLinks]
ConnectionString={conn}
AddMode=3
RemoveMode=1

[Table1]
SchemaName=
TableName=parts#csv
Enabled=True
UserWhere=0
UserWhereText=[Part Number] = '{{Part Number}}'

[Table2]
SchemaName=
TableName=raw#csv
Enabled=False
Key=Part Number

[Table3]
SchemaName=
TableName=other
Enabled=True
Key=[Code]
"""


def ace_installed():
    if os.name != "nt":
        return False
    import winreg
    try:
        winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "Microsoft.ACE.OLEDB.12.0").Close()
        return True
    except OSError:
        return False


class ReadDbLibTest(unittest.TestCase):
    def test_tables_and_their_keys(self):
        text = DBLIB.format(conn="Provider=X").replace("\n", "\r\n")
        self.assertEqual(dblib.table_info(text), [
            {"name": "parts#csv", "enabled": True, "key": "Part Number"},
            {"name": "raw#csv", "enabled": False, "key": "Part Number"},
            {"name": "other", "enabled": True, "key": "Code"},
        ])

    def test_part_key_is_the_one_most_tables_use(self):
        tables = dblib.table_info(DBLIB.format(conn="x"))
        self.assertEqual(dblib.part_key(tables), "Part Number")
        self.assertEqual(dblib.part_key([{"name": "t", "enabled": True, "key": ""}]), "")

    def test_relative_data_source_is_resolved_against_the_dblib(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        (tmp / "db").mkdir()
        (tmp / "db" / "parts.mdb").write_bytes(b"")
        conn = dblib.connection_string("ConnectionString=Provider=P;Data Source=db\\parts.mdb;Mode=Read\n", tmp)
        self.assertEqual(conn, f"Provider=P;Data Source={(tmp / 'db' / 'parts.mdb').resolve()};Mode=Read")
        # absolute, or not there: as written
        absolute = "ConnectionString=Provider=P;Data Source=C:\\x\\y.mdb\n"
        self.assertEqual(dblib.connection_string(absolute, tmp), "Provider=P;Data Source=C:\\x\\y.mdb")
        self.assertEqual(dblib.connection_string("ConnectionString=Provider=P;Data Source=none.mdb\n", tmp),
                         "Provider=P;Data Source=none.mdb")
        with self.assertRaises(dblib.DbLibError):
            dblib.connection_string("[Table1]\n", tmp)


class SqlTest(unittest.TestCase):
    def test_only_a_select_is_sent(self):
        for sql in ("DELETE FROM t", "UPDATE t SET a=1", "SELECT * FROM t; DROP TABLE t", "  drop table t"):
            with self.assertRaises(dblib.DbLibError, msg=sql):
                dblib.run_select("Provider=X", sql)

    def test_names_and_terms_are_quoted(self):
        self.assertEqual(dblib.quote_name("a]b"), "[a]]b]")
        self.assertEqual(dblib.quote_text("O'Brien"), "'O''Brien'")
        self.assertEqual(dblib.like_pattern("10%_[x]'"), "'%10[%][_][[]x]''%'")

    def test_search_sql_takes_the_searched_columns(self):
        cols = ["Part Number", "Description", "Value", "Library Ref", "Manufacturer Part Number", "Height"]
        sql = dblib.search_sql("parts", cols, "Part Number", "10k", 5)
        self.assertTrue(sql.startswith("SELECT TOP 5 * FROM [parts] WHERE "), sql)
        for col in ("Part Number", "Description", "Value", "Manufacturer Part Number"):
            self.assertIn(f"[{col}] LIKE '%10k%'", sql)
        self.assertNotIn("[Library Ref]", sql)
        self.assertNotIn("[Height]", sql)
        self.assertEqual(dblib.search_sql("t", ["Height", "Width"], "", "x", 5), "")

    def test_summary_names_what_the_part_is(self):
        row = {"Part Number": "RES-1", "Description": "Resistor", "Value": "10k", "Library Ref": "RES",
               "Library Path": "R.SchLib", "Footprint Ref": "R0603", "Footprint Path": "R.PcbLib",
               "Manufacturer Part Number": "RC0603", "Height": "0.5", "Comment": ""}
        self.assertEqual(dblib.summary(row, "Part Number"), {
            "part_number": "RES-1", "description": "Resistor", "value": "10k",
            "manufacturer_part_number": "RC0603", "library_ref": "RES", "library_path": "R.SchLib",
            "footprint_ref": "R0603", "footprint_path": "R.PcbLib"})

    def test_the_dblib_field_mappings_name_the_symbol_and_footprint(self):
        text = ("Options=FieldNameOnly=Sym|TableNameOnly=Parts|ParameterName=[Library Ref]|Visible=0\n"
                "Options=FieldNameOnly=Fp|TableNameOnly=Parts|ParameterName=[Footprint Ref]\n"
                "Options=FieldNameOnly=Fp|TableNameOnly=Other|ParameterName=[Footprint Path]\n"
                "Options=FieldNameOnly=Tolerance|TableNameOnly=Parts|ParameterName=Tolerance\n"
                "Options=FieldNameOnly=Internal|TableNameOnly=Parts|ParameterName=\n")
        roles = dblib.field_roles(text, "parts")
        self.assertEqual(roles, {"sym": "library_ref", "fp": "footprint_ref"})
        row = {"PN": "R-1", "Sym": "RES", "Fp": "R0402", "Footprint Ref": "unused", "Tolerance": "1%"}
        self.assertEqual(dblib.summary(row, "PN", roles), {"part_number": "R-1", "library_ref": "RES",
                                                            "footprint_ref": "R0402"})


class SearchArgumentsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_refuses_what_is_not_a_dblib(self):
        other = self.tmp / "parts.SchLib"
        other.write_text("x")
        for path in (other, self.tmp / "missing.DbLib"):
            with self.assertRaises(dblib.DbLibError):
                dblib.search(path, term="x")

    def test_unknown_table_and_no_tables(self):
        lib = self.tmp / "Parts.DbLib"
        lib.write_text(DBLIB.format(conn="Provider=X"))
        with self.assertRaises(dblib.DbLibError) as e:
            dblib.search(lib, term="x", table="nope")
        self.assertIn("parts#csv", str(e.exception))
        # no term nor part number: the tables, without a query
        out = dblib.search(lib)
        self.assertEqual([t["name"] for t in out["tables"]], ["parts#csv", "raw#csv", "other"])
        self.assertEqual(out["part_number_field"], "Part Number")
        lib.write_text("[DatabaseLinks]\nConnectionString=Provider=X\n")
        with self.assertRaises(dblib.DbLibError):
            dblib.search(lib)


@unittest.skipUnless(ace_installed(), "needs the Access database engine (Microsoft.ACE.OLEDB.12.0)")
class SearchDatabaseTest(unittest.TestCase):
    """A DbLib on CSV files: parts#csv enabled, raw#csv not."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        (self.tmp / "db").mkdir()
        header = "Part Number,Description,Value,Library Ref,Footprint Ref\r\n"
        (self.tmp / "db" / "parts.csv").write_text(
            header + "RES-0001,Resistor 10k 0603 1%,10k,RES,R0603\r\n"
                     "CAP-0001,Capacitor 100n_X7R 50V,100n,CAP,C0603\r\n"
                     "CAP-0002,Capacitor 10u 0805,10u,CAP,C0805\r\n", encoding="ascii")
        (self.tmp / "db" / "raw.csv").write_text(header + "RAW-0001,Raw resistor 10k,10k,RES,R0402\r\n",
                                                 encoding="ascii")
        (self.tmp / "db" / "other.csv").write_text("Code,Height\r\nX1,1\r\n", encoding="ascii")
        conn = 'Provider=Microsoft.ACE.OLEDB.12.0;Data Source=db;Extended Properties="text;HDR=Yes;FMT=Delimited"'
        self.lib = self.tmp / "Parts.DbLib"
        self.lib.write_text(DBLIB.format(conn=conn).replace("TableName=other", "TableName=other#csv"))

    def test_term_in_the_enabled_tables(self):
        out = dblib.search(self.lib, term="10k")
        self.assertEqual(out["searched_tables"], ["parts#csv"], out)
        self.assertEqual(out["tables_without_searchable_columns"], ["other#csv"])
        self.assertEqual(out["matches"], [{"table": "parts#csv", "part_number": "RES-0001",
                                           "description": "Resistor 10k 0603 1%", "value": "10k",
                                           "library_ref": "RES", "footprint_ref": "R0603"}])
        out = dblib.search(self.lib, term="10k", all_tables=True)
        self.assertEqual([m["part_number"] for m in out["matches"]], ["RES-0001", "RAW-0001"])
        # a wildcard in the term is taken literally
        self.assertEqual(dblib.search(self.lib, term="100n_X7R")["match_count"], 1)
        self.assertEqual(dblib.search(self.lib, term="10_k")["match_count"], 0)

    def test_max_rows_says_when_reached(self):
        out = dblib.search(self.lib, term="Capacitor", max_rows=1)
        self.assertEqual(out["match_count"], 1)
        self.assertIn("max_rows", out["note"])
        self.assertNotIn("note", dblib.search(self.lib, term="Capacitor", max_rows=5))

    def test_part_number(self):
        out = dblib.search(self.lib, part_number="CAP-0002")
        self.assertEqual(out["part"], {"table": "parts#csv", "fields": {
            "Part Number": "CAP-0002", "Description": "Capacitor 10u 0805", "Value": "10u",
            "Library Ref": "CAP", "Footprint Ref": "C0805"}})
        # the tables the DbLib does not enable after the others
        self.assertEqual(dblib.search(self.lib, part_number="RAW-0001")["part"]["table"], "raw#csv")
        out = dblib.search(self.lib, part_number="NONE")
        self.assertIsNone(out["part"])
        self.assertIn("NONE", out["note"])

    def test_a_query_that_fails_says_why(self):
        self.lib.write_text(self.lib.read_text().replace("TableName=parts#csv", "TableName=gone#csv"))
        with self.assertRaises(dblib.DbLibError) as e:
            dblib.search(self.lib, term="10k")
        self.assertIn("gone", str(e.exception))


if __name__ == "__main__":
    unittest.main()
