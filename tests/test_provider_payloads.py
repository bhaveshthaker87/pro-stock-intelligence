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
    def test_delayed_quote_requires_delay_metadata(self):
        with self.assertRaisesRegex(ValueError,"delayMinutes"):
            m.validate_quote(self.quote(marketDataStatus="DELAYED"), now=NOW)

    def test_delayed_quote_rejects_boolean_delay_metadata(self):
        with self.assertRaisesRegex(ValueError,"delayMinutes"):
            m.validate_quote(self.quote(marketDataStatus="DELAYED", delayMinutes=True), now=NOW)
    def test_history_rejects_inconsistent_ohlc(self):
        h={"symbol":"INFY","source":"Vendor","asOf":"2026-10-11T09:25:00+05:30","interval":"1d","rows":[
            {"time":"2026-10-09T10:00:00+05:30","open":100,"high":99,"low":98,"close":99,"volume":10},
            {"time":"2026-10-10T10:00:00+05:30","open":100,"high":102,"low":98,"close":101,"volume":12}]}
        with self.assertRaisesRegex(ValueError,"high is inconsistent"):
            m.validate_history(h)
    def test_history_rejects_asof_timestamp_in_the_future(self):
        h={"symbol":"INFY","source":"Vendor","asOf":"2026-10-11T12:00:00+05:30","interval":"1d","rows":[
            {"time":"2026-10-09T10:00:00+05:30","open":100,"high":102,"low":98,"close":101,"volume":10},
            {"time":"2026-10-10T10:00:00+05:30","open":100,"high":102,"low":98,"close":101,"volume":12}]}
        with self.assertRaisesRegex(ValueError,"future"):
            m.validate_history(h, now=NOW)

    def test_history_rejects_bar_after_asof(self):
        h={"symbol":"INFY","source":"Vendor","asOf":"2026-10-10T09:00:00+05:30","interval":"1d","rows":[
            {"time":"2026-10-09T10:00:00+05:30","open":100,"high":102,"low":98,"close":101,"volume":10},
            {"time":"2026-10-10T10:00:00+05:30","open":100,"high":102,"low":98,"close":101,"volume":12}]}
        with self.assertRaisesRegex(ValueError,"after the history asOf"):
            m.validate_history(h, now=NOW)

    def test_history_rejects_duplicate_or_unsorted_times(self):
        row={"time":"2026-10-10T10:00:00+05:30","open":100,"high":102,"low":98,"close":101,"volume":12}
        h={"symbol":"INFY","source":"Vendor","asOf":"2026-10-11T09:25:00+05:30","interval":"1d","rows":[row,row.copy()]}
        with self.assertRaisesRegex(ValueError,"strictly increasing"):
            m.validate_history(h)
    def test_empty_events_do_not_claim_absence_verified(self):
        e={"symbol":"INFY","source":"Vendor","asOf":"2026-10-11T09:25:00+05:30","rows":[]}
        self.assertFalse(m.validate_events(e)["absenceVerified"])
    def test_event_requires_announcement_timestamp(self):
        e={"symbol":"INFY","source":"Vendor","asOf":"2026-10-11T09:25:00+05:30","rows":[{"symbol":"INFY","eventType":"RESULTS","title":"Quarterly results","announcedAt":"2026-10-10","eventDate":"2026-10-20"}]}
        with self.assertRaisesRegex(ValueError,"timezone"):
            m.validate_events(e)

    def test_global_event_calendar_does_not_require_top_level_symbol(self):
        e={"source":"Licensed test vendor","asOf":"2026-10-11T09:25:00+05:30","rows":[
            {"symbol":"INFY","eventType":"RESULTS","title":"Quarterly results",
             "announcedAt":"2026-10-10T12:00:00+05:30","eventDate":"2026-10-20"}]}
        result=m.validate_events(e)
        self.assertIsNone(result["symbol"])
        self.assertEqual(result["eventsReturned"],1)

    def test_global_event_calendar_still_requires_symbol_on_each_event(self):
        e={"source":"Licensed test vendor","asOf":"2026-10-11T09:25:00+05:30","rows":[
            {"eventType":"RESULTS","title":"Quarterly results",
             "announcedAt":"2026-10-10T12:00:00+05:30","eventDate":"2026-10-20"}]}
        with self.assertRaisesRegex(ValueError,"rows\\[0\\].symbol"):
            m.validate_events(e)


    def test_indices_require_fresh_status_and_valid_numeric_rows(self):
        payload={"source":"Licensed test vendor","asOf":"2026-10-11T09:25:00+05:30","marketDataStatus":"REALTIME",
                 "rows":[{"name":"NIFTY 50","value":25000.5,"changePct":0.42}]}
        result=m.validate_indices(payload, now=NOW)
        self.assertEqual(result["indicesReturned"],1)
        self.assertEqual(result["status"],"REALTIME")

    def test_indices_reject_stale_data_and_invalid_values(self):
        stale={"source":"Vendor","asOf":"2026-10-10T09:25:00+05:30","marketDataStatus":"REALTIME",
               "rows":[{"name":"NIFTY 50","value":25000.5,"changePct":0.42}]}
        with self.assertRaisesRegex(ValueError,"stale"):
            m.validate_indices(stale, now=NOW)
        invalid={"source":"Vendor","asOf":"2026-10-11T09:25:00+05:30","marketDataStatus":"REALTIME",
                 "rows":[{"name":"NIFTY 50","value":0,"changePct":float("nan")}]}
        with self.assertRaisesRegex(ValueError,"positive"):
            m.validate_indices(invalid, now=NOW)

    def test_indices_reject_duplicate_names_and_empty_rows(self):
        base={"source":"Vendor","asOf":"2026-10-11T09:25:00+05:30","marketDataStatus":"REALTIME"}
        with self.assertRaisesRegex(ValueError,"duplicate"):
            m.validate_indices({**base,"rows":[{"name":"NIFTY 50","value":25000,"changePct":0},
                                                {"name":"nifty 50","value":25001,"changePct":0}]}, now=NOW)
        with self.assertRaisesRegex(ValueError,"at least one"):
            m.validate_indices({**base,"rows":[]}, now=NOW)

    def test_dividends_validate_timestamp_and_row_units(self):
        payload={"source":"Licensed test vendor","asOf":"2026-10-11T09:25:00+05:30",
                 "rows":[{"company":"Infosys Ltd","symbol":"INFY","CMP Rs.":1500.5,
                          "Div Yld %":2.1,"Mar Cap Rs.Cr.":620000,"ROCE %":35.2}]}
        self.assertEqual(m.validate_dividends(payload, now=NOW)["rowsReturned"],1)
        bad={**payload,"rows":[{**payload["rows"][0],"CMP Rs.":"1500.5"}]}
        with self.assertRaisesRegex(ValueError,"finite numeric"):
            m.validate_dividends(bad, now=NOW)

    def test_empty_dividend_rows_do_not_prove_no_dividends(self):
        payload={"source":"Vendor","asOf":"2026-10-11T09:25:00+05:30","rows":[]}
        result=m.validate_dividends(payload, now=NOW)
        self.assertFalse(result["absenceVerified"])

if __name__=='__main__': unittest.main()
