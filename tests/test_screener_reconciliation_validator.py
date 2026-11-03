import csv, tempfile, unittest
from pathlib import Path
from tools.validate_screener_reconciliation import FIELDS, METRICS, SYMBOLS, validate, write_template

class ScreenerReconciliationTests(unittest.TestCase):
 def test_template_has_360_explicit_not_tested_rows(self):
  with tempfile.TemporaryDirectory() as d:
   p=write_template(Path(d)/"audit.csv")
   with p.open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
   self.assertEqual(len(rows),360)
   self.assertEqual(len({(r["symbol"],r["metric"]) for r in rows}),360)
   self.assertTrue(all(r["status"]=="NOT_TESTED" for r in rows))
   self.assertEqual(len(SYMBOLS),30); self.assertEqual(len(METRICS),12)

 def test_unverified_template_is_partial_not_pass(self):
  with tempfile.TemporaryDirectory() as d:
   p=write_template(Path(d)/"audit.csv")
   result=validate(p)
   self.assertEqual(result["status"],"PARTIAL")
   self.assertEqual(result["verified"],0)
   with self.assertRaisesRegex(ValueError,"Release gate blocked"):
    validate(p,require_complete=True)

 def test_verified_metric_requires_evidence_and_correct_difference(self):
  with tempfile.TemporaryDirectory() as d:
   p=write_template(Path(d)/"audit.csv")
   with p.open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
   r=rows[0]; r.update(app_value="100",screener_value="100",difference="0",status="VERIFIED_MATCH",evidence_ref="authorized-export.xlsx#sheet=Data Sheet")
   with p.open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
   self.assertEqual(validate(p)["verified"],1)
   r["difference"]="1"
   with p.open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
   with self.assertRaisesRegex(ValueError,"difference does not equal"):
    validate(p)

if __name__=="__main__": unittest.main()
