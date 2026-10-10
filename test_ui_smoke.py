"""Browser-level dashboard smoke tests with deterministic provider fixtures.

These validate the HTML/JS interaction layer only; live provider accuracy is
covered separately and is never inferred from mocked fixtures.
"""
import json
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError as exc:  # CI installs Playwright; keep the error explicit locally.
    raise RuntimeError("Install Playwright and Chromium to run tests/test_ui_smoke.py") from exc

HTML = Path(__file__).parents[1] / "app/src/main/assets/index.html"
ENGINE = "V40.52 ANDROID MOBILE DATA + UI SMOKE TESTS + PEER INDICATORS + TECHNICAL SCANNERS"


def fixtures():
    rows = []
    for i in range(220):
        close = 100 + i * .12 + ((i % 9) - 4) * .2
        stamp = int((datetime(2025, 1, 1) + timedelta(days=i)).timestamp() * 1000)
        rows.append({"time": stamp, "date": stamp, "open": close-.2, "high": close+.8,
                     "low": close-.7, "close": close, "volume": 100000+i*10})
    quote = {"symbol": "INFY", "resolvedSymbol": "INFY.NS", "price": 1310,
             "previousClose": 1300, "dayChangePct": .77, "currency": "INR",
             "high52": 1800, "low52": 1200, "quoteTimestamp": int(time.time()),
             "rows": rows, "provider": "Mock quote"}
    fundamentals = {"symbol": "INFY", "name": "Infosys Ltd", "price": 1310, "marketCap": 540000,
        "pe": 25, "roce": 35, "roe": 30, "debtEquity": .05, "netProfit": 26000,
        "ttmProfit": 26000, "sales3y": 12, "profit3y": 14, "eps": 55, "bookValue": 250,
        "promoter": 13, "public": 87, "pledged": 0, "interestCoverage": 20,
        "currentRatio": 2.1, "industryPE": 28, "dma200": 1280, "high52": 1800,
        "low52": 1200, "qProfit": 10, "provider": "Screener.in"}
    analysis = {"symbol": "INFY", "name": "Infosys Ltd", "quote": quote, "market": quote,
        "fundamentals": fundamentals, "history": {"rows": rows, "provider": "Mock"},
        "ohlcv": rows, "technicalSeries": rows, "dataConfidence": "PARTIAL",
        "dataSources": {"Quote": "Mock", "Fundamentals": "Mock"},
        "fundamentalCoverage": {"coreFields": 7, "coreTotal": 7}}
    queries = [{"id": ident, "name": name, "description": "test fixture", "focus": "test", 
                "query": "Market Capitalization > 10000"} for ident, name in [
        ("master", "Large Cap Quality Stocks"), ("midcap", "Mid Cap Hidden Gems"),
        ("smallcap", "Small Cap Quality"), ("oversold", "RSI Oversold Scanner"),
        ("crash", "Daily Crash Scanner")]]
    return rows, quote, analysis, queries


class DashboardUISmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.quote, cls.analysis, cls.queries = fixtures()
        cls.mock_api = {
            "/api/health": {"ok": True, "engine": ENGINE, "data": {"ok": True}},
            "/api/fast": {"ok": True, "data": {"symbol": "INFY", "name": "Infosys Ltd", "quote": cls.quote, "rows": cls.rows, "provider": "Mock"}},
            "/api/quote": {"ok": True, "data": {"symbol": "INFY", "name": "Infosys Ltd", "quote": cls.quote, "rows": cls.rows, "provider": "Mock"}},
            "/api/bootstrap": {"ok": True, "data": cls.analysis}, "/api/analyze": {"ok": True, "data": cls.analysis},
            "/api/history": {"ok": True, "data": {"symbol": "INFY", "rows": cls.rows, "provider": "Mock", "chartMode": "OHLCV"}},
            "/api/peers": {"ok": True, "data": {"symbol": "INFY", "industry": "IT Services", "peers": [], "candidateCount": 0, "validatedCount": 0, "method": "mock", "partial": False}},
            "/api/news": {"ok": True, "data": {"symbol": "INFY", "news": [{"title": "Test headline", "publisher": "Mock", "link": "https://example.com", "time": int(time.time())}], "provider": "Mock"}},
            "/api/indices": {"ok": True, "data": {"NIFTY 50": {"value": 25000, "changePct": .2}, "SENSEX": {"value": 82000, "changePct": .3}, "NIFTY BANK": {"value": 55000, "changePct": -.1}}},
            "/api/queries": {"ok": True, "data": cls.queries},
            "/api/screener/status": {"ok": True, "data": {"connected": False, "loggedIn": False, "validated": False, "loginUrl": "https://www.screener.in/login/", "message": "fixture"}},
            "/api/screener/connect": {"ok": True, "data": {"connected": False, "loggedIn": False, "validated": False, "loginUrl": "https://www.screener.in/login/", "message": "fixture"}},
            "/api/screen/query": {"ok": True, "data": {"columns": ["S.No.", "Name", "CMP Rs."], "rows": [{"S.No.": 1, "Name": "Infosys", "CMP Rs.": "1310"}], "count": 1, "provider": "Mock", "statusText": "Mock result", "queryId": "master", "queryName": "fixture"}},
            "/api/search-suggestions": {"ok": True, "data": [{"symbol": "INFY", "name": "Infosys Ltd", "exchange": "NSE", "sector": "IT"}]},
            "/api/dividend-stocks": {"ok": True, "data": {"rows": [], "statusText": "No fixture rows", "provider": "Mock", "partial": True}},
            "/api/upcoming-events": {"ok": True, "data": {"rows": [], "statusText": "No fixture rows", "officialUrl": "https://www.nseindia.com/companies-listing/corporate-filings-event-calendar", "resultsUrl": "https://www.nseindia.com/companies-listing/corporate-filings-financial-results", "liveData": False}},
            "/api/upcoming-results": {"ok": True, "data": {"rows": [], "statusText": "No fixture rows", "officialUrl": "https://www.nseindia.com/companies-listing/corporate-filings-event-calendar", "resultsUrl": "https://www.nseindia.com/companies-listing/corporate-filings-financial-results", "liveData": False, "sourcesChecked": [], "providerErrors": []}},
            "/api/company-events": {"ok": True, "data": {"symbol": "INFY", "name": "Infosys", "rows": [], "statusText": "No fixture rows", "provider": "Mock", "errors": []}},
            "/api/resolve-stock": {"ok": True, "data": {"symbol": "INFY", "name": "Infosys", "sector": "IT"}},
            "/api/cache-clear": {"ok": True, "data": {"cleared": True}},
            "/api/screen/querytext": {"ok": True, "data": {"columns": ["S.No.", "Name"], "rows": [], "count": 0, "provider": "Mock", "statusText": "No results"}},
        }

    def test_core_tabs_buttons_watchlist_alerts_and_query(self):
        errors = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path="/usr/bin/chromium", args=["--no-sandbox"])
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.on("pageerror", lambda e: errors.append(str(e)))
            mock_js = '''
              Object.defineProperty(window,"localStorage",{value:{_s:{},getItem(k){return this._s[k]??null},setItem(k,v){this._s[k]=String(v)},removeItem(k){delete this._s[k]}}});
              const MOCK_API = ''' + json.dumps(self.mock_api, separators=(",", ":")) + ''';
              window.fetch=(u,opts)=>{const path=String(u).split("?")[0];const key=Object.keys(MOCK_API).find(k=>path.endsWith(k));const value=key?MOCK_API[key]:{ok:false,error:"unmocked "+path};return Promise.resolve(new Response(JSON.stringify(value),{status:200,headers:{"Content-Type":"application/json"}}));};
            '''
            html = HTML.read_text(encoding="utf-8")
            pos = html.find("<script")
            html = html[:pos] + "<script>" + mock_js + "</script>" + html[pos:]
            page.set_content(html, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(250)
            self.assertIn("V40.52", page.locator(".taglive").first.inner_text())
            page.locator("#search").fill("INFY")
            page.locator("#analyze").click()
            page.wait_for_function("document.getElementById('company').textContent.includes('Infosys')", timeout=8000)
            self.assertIn("1,310", page.locator("#price").inner_text())
            signal_count = page.evaluate("(window.chartRows||[]).filter(r=>r.nwSignal==='BUY'||r.nwSignal==='SELL').length")
            self.assertLess(signal_count, max(10, len(self.rows)//3), f"NW signals look over-triggered: {signal_count}")
            self.assertEqual(page.locator(".tab").count(), 6)
            for tab in page.locator(".tab").all():
                tab.click()
                self.assertIn("active", tab.get_attribute("class"))
            self.assertEqual(page.locator(".qcard").count(), 5)
            page.locator("[data-qrun='master']").click()
            page.wait_for_timeout(150)
            self.assertTrue(page.locator("#qresult_master").inner_text())
            # Persistent watchlist: add, open, and verify the saved row.
            page.locator(".actions .btn").filter(has_text="Watchlist").click()
            page.locator("#watchlistViewBtn").click()
            self.assertIn("open", page.locator("#watchModal").get_attribute("class"))
            self.assertIn("INFY", page.locator("#watchModalBody").inner_text())
            page.locator("#watchClose").click()
            # Blank price alerts must not silently become a ₹0 alert.
            page.locator(".actions .btn").filter(has_text="Alerts").click()
            page.locator("#alertType").select_option("price")
            page.locator("#alertAdd").click()
            self.assertEqual(page.locator("#alertList .alertrow").count(), 0)
            page.locator("#alertValue").fill("1200")
            page.locator("#alertAdd").click()
            self.assertEqual(page.locator("#alertList .alertrow").count(), 1)
            page.locator("#watchClose").click()
            # Provider-controlled suggestion text must be escaped, not interpreted as HTML.
            page.evaluate("renderSuggestions([{symbol:'<script>',name:'<img src=x onerror=alert(1)>',exchange:'<svg>'}],'test')")
            self.assertEqual(page.locator("#suggestions script, #suggestions img, #suggestions svg").count(), 0)
            for ident in ["tvIntervalBtn", "tvIndicatorsBtn", "tvCrosshairBtn", "tvVolBtn", "tvSmaBtn", "tvNwBtn", "tvRsiBtn", "tvResetBtn", "tvExpandBtn"]:
                page.locator("#" + ident).evaluate("el=>el.click()")
            self.assertIn("chart-expanded", page.locator(".tvwork").get_attribute("class"))
            page.locator("#tvExpandBtn").evaluate("el=>el.click()")
            self.assertNotIn("chart-expanded", page.locator(".tvwork").get_attribute("class"))
            page.locator("[data-eventfilter='dividend']").click()
            page.locator("#eventUseCurrentBtn").click()
            page.wait_for_timeout(100)
            self.assertEqual(errors, [], f"JavaScript errors: {errors}")
            browser.close()

    def test_mobile_layout_has_no_page_wide_horizontal_overflow(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path="/usr/bin/chromium", args=["--no-sandbox"])
            page = browser.new_page(viewport={"width": 390, "height": 844})
            html = HTML.read_text(encoding="utf-8")
            page.set_content(html, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(100)
            dims = page.evaluate("({viewport:innerWidth, document:document.documentElement.scrollWidth, body:document.body.scrollWidth})")
            self.assertLessEqual(dims["document"], dims["viewport"] + 2, f"Horizontal overflow: {dims}")
            browser.close()


if __name__ == "__main__":
    unittest.main()
