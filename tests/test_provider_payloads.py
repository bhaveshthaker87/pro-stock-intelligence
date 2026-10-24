import importlib.util
import unittest
from datetime import datetime, timezone
from pathlib import Path

p=Path(__file__).parents[1]/'tools'/'validate_provider_payloads.py'
spec=importlib.util.spec_from_file_location('provider_validator',p)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
NOW=datetime(2026,10,11,4,0,tzinfo=timezone.utc)

class ProviderPayloadTests(unittest.TestCase):
    def quote(self, **overrides):
        q={"symbol":"INFY","source":"Licensed test vendor","asOf":"2026-10-11T09:25:00+05:30","price":1500.5,"currency":"INR","marketDataStatus":"REALTIME"}
        q.update(overrides); return q
    def test_valid_realtime_quote(self):
        result=m.validate_quote(self.quote(), now=NOW)
        self.assertEqual(result["status"],"REALTIME")
    def test_quote_requires_timezone_aware_timestamp(self):
        with self.assertRaisesRegex(ValueError,"timezone"):
            m.validate_quote(self.quote(asOf="2026-10-11T09:25:00"), now=NOW)
    def test_quote_rejects_stale_realtime(self):
        with self.assertRaisesRegex(ValueError,"stale"):
            m.validate_quote(self.quote(asOf="2026-10-11T08:00:00+05:30"), now=NOW)
    def test_quote_rejects_future_timestamp(self):
        with self.assertRaisesRegex(ValueError,"future"):
            m.validate_quote(self.quote(asOf="2026-10-11T12:00:00+05:30"), now=NOW)
    def test_quote_rejects_wrong_symbol(self):
        with self.assertRaisesRegex(ValueError,"symbol mismatch"):
            m.validate_quote(self.quote(), now=NOW, expected_symbol="TCS")
    def test_delayed_quote_requires_delay_metadata(self):
        with self.assertRaisesRegex(ValueError,"delayMinutes"):
            m.validate_quote(self.quote(marketDataStatus="DELAYED"), now=NOW)
    def test_history_rejects_inconsistent_ohlc(self):
        h={"symbol":"INFY","source":"Vendor","asOf":"2026-10-11T09:25:00+05:30","interval":"1d","rows":[
            {"time":"2026-10-09T10:00:00+05:30","open":100,"high":99,"low":98,"close":99,"volume":10},
            {"time":"2026-10-10T10:00:00+05:30","open":100,"high":102,"low":98,"close":101,"volume":12}]}
        with self.assertRaisesRegex(ValueError,"high is inconsistent"):
            m.validate_history(h)
    def test_history_rejects_duplicate_or_unsorted_times(self):
        row={"time":"2026-10-10T10:00:00+05:30","open":100,"high":102,"low":98,"close":101,"volume":12}
        h={"symbol":"INFY","source":"Vendor","asOf":"2026-10-11T09:25:00+05:30","interval":"1d","rows":[row,row.copy()]}
        with self.assertRaisesRegex(ValueError,"strictly increasing"):
            m.validate_history(h)
    def test_history_rejects_wrong_symbol(self):
        h={"symbol":"INFY","source":"Vendor","asOf":"2026-10-11T09:25:00+05:30","interval":"1d","rows":[
            {"time":"2026-10-09T10:00:00+05:30","open":100,"high":102,"low":98,"close":99,"volume":10},
            {"time":"2026-10-10T10:00:00+05:30","open":100,"high":102,"low":98,"close":101,"volume":12}]}
        with self.assertRaisesRegex(ValueError,"symbol mismatch"):
            m.validate_history(h, expected_symbol="TCS")
    def test_empty_events_do_not_claim_absence_verified(self):
        e={"symbol":"INFY","source":"Vendor","asOf":"2026-10-11T09:25:00+05:30","rows":[]}
        self.assertFalse(m.validate_events(e)["absenceVerified"])
    def test_event_requires_announcement_timestamp(self):
        e={"symbol":"INFY","source":"Vendor","asOf":"2026-10-11T09:25:00+05:30","rows":[{"symbol":"INFY","eventType":"RESULTS","title":"Quarterly results","announcedAt":"2026-10-10","eventDate":"2026-10-20"}]}
        with self.assertRaisesRegex(ValueError,"timezone"):
            m.validate_events(e)
    def test_valid_indices_payload(self):
        p={"source":"Licensed vendor","asOf":"2026-10-11T09:25:00+05:30","marketDataStatus":"REALTIME",
           "rows":[{"symbol":"NIFTY 50","value":25000.5,"previousClose":24900.0,"changePct":0.4},
                   {"symbol":"NIFTY BANK","value":55000.0}]}
        self.assertEqual(m.validate_indices(p, now=NOW)["indicesReturned"],2)
    def test_indices_reject_empty_rows_and_duplicate_symbols(self):
        with self.assertRaisesRegex(ValueError,"non-empty"):
            m.validate_indices({"source":"Vendor","asOf":"2026-10-11T09:25:00+05:30","marketDataStatus":"REALTIME","rows":[]},now=NOW)
        with self.assertRaisesRegex(ValueError,"duplicate"):
            m.validate_indices({"source":"Vendor","asOf":"2026-10-11T09:25:00+05:30","marketDataStatus":"REALTIME","rows":[
                {"symbol":"NIFTY 50","value":25000},{"symbol":"nifty 50","value":25001}]},now=NOW)
    def test_indices_reject_stale_feed(self):
        p={"source":"Vendor","asOf":"2026-10-11T08:00:00+05:30","marketDataStatus":"REALTIME","rows":[{"symbol":"NIFTY 50","value":25000}]}
        with self.assertRaisesRegex(ValueError,"stale"):
            m.validate_indices(p,now=NOW)
    def test_valid_dividend_payload_and_empty_does_not_prove_absence(self):
        p={"source":"Licensed vendor","asOf":"2026-10-11T09:25:00+05:30","marketDataStatus":"EOD","rows":[
            {"symbol":"INFY","exDate":"2026-10-20","amount":25.0,"currency":"INR"}]}
        self.assertEqual(m.validate_dividends(p,now=NOW)["dividendsReturned"],1)
        self.assertFalse(m.validate_dividends({"source":"Vendor","asOf":"2026-10-11T09:25:00+05:30","marketDataStatus":"EOD","rows":[]},now=NOW)["absenceVerified"])
    def test_dividend_requires_date_and_valid_amount(self):
        with self.assertRaisesRegex(ValueError,"requires exDate"):
            m.validate_dividends({"source":"Vendor","asOf":"2026-10-11T09:25:00+05:30","marketDataStatus":"EOD","rows":[{"symbol":"INFY","amount":10,"currency":"INR"}]},now=NOW)
        with self.assertRaisesRegex(ValueError,"positive finite"):
            m.validate_dividends({"source":"Vendor","asOf":"2026-10-11T09:25:00+05:30","marketDataStatus":"EOD","rows":[{"symbol":"INFY","exDate":"2026-10-20","amount":0,"currency":"INR"}]},now=NOW)

    def test_dividend_rejects_stale_snapshot(self):
        p={"source":"Vendor","asOf":"2026-10-01T09:25:00+05:30","marketDataStatus":"EOD","rows":[]}
        with self.assertRaisesRegex(ValueError,"stale"):
            m.validate_dividends(p,now=NOW)

if __name__=='__main__': unittest.main()
