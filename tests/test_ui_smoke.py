"""Browser-level dashboard smoke tests with deterministic provider fixtures.

These validate the HTML/JS interaction layer only; live provider accuracy is
covered separately and is never inferred from mocked fixtures.
"""
import json
import shutil
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError as exc:  # CI installs Playwright; keep the error explicit locally.
    raise RuntimeError("Install Playwright and Chromium to run tests/test_ui_smoke.py") from exc

HTML = Path(__file__).parents[1] / "app/src/main/assets/index.html"
ENGINE = "V40.80 AUTHORIZED GATEWAY + SCREENER FUNDAMENTALS"


def launch_chromium(playwright):
    """Prefer Playwright's managed browser; use a system Chromium when present."""
    system_chromium = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
    options = {"headless": True, "args": ["--no-sandbox"]}
    if system_chromium:
        options["executable_path"] = system_chromium
    return playwright.chromium.launch(**options)


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
            "/api/indices": {"ok": True, "data": {"NIFTY 50": {"value": 25000, "changePct": 0.2, "status": "QUOTE_RETURNED_FRESHNESS_UNVERIFIED", "priceSource": "NSE_PUBLIC_INDEX_SNAPSHOT", "provider": "Mock", "currency": "INR", "quoteTimestamp": int(time.time())}, "SENSEX": {"value": 25123.4, "changePct": -0.1, "status": "QUOTE_RETURNED_FRESHNESS_UNVERIFIED", "priceSource": "NSE_PUBLIC_INDEX_SNAPSHOT", "provider": "Mock", "currency": "INR", "quoteTimestamp": int(time.time()) - 3600}, "NIFTY BANK": {"value": 25246.8, "changePct": 0.2, "status": "QUOTE_RETURNED_FRESHNESS_UNVERIFIED", "priceSource": "NSE_PUBLIC_INDEX_SNAPSHOT", "provider": "Mock", "currency": "INR", "quoteTimestamp": int(time.time())}, "NIFTY MIDCAP 100": {"value": 25370.2, "changePct": -0.1, "status": "QUOTE_RETURNED_FRESHNESS_UNVERIFIED", "priceSource": "NSE_PUBLIC_INDEX_SNAPSHOT", "provider": "Mock", "currency": "INR", "quoteTimestamp": int(time.time())}, "NIFTY SMALLCAP 100": {"value": 25493.6, "changePct": 0.2, "status": "QUOTE_RETURNED_FRESHNESS_UNVERIFIED", "priceSource": "NSE_PUBLIC_INDEX_SNAPSHOT", "provider": "Mock", "currency": "INR", "quoteTimestamp": int(time.time())}, "NIFTY IT": {"value": 25617, "changePct": -0.1, "status": "QUOTE_RETURNED_FRESHNESS_UNVERIFIED", "priceSource": "NSE_PUBLIC_INDEX_SNAPSHOT", "provider": "Mock", "currency": "INR", "quoteTimestamp": int(time.time())}, "NIFTY AUTO": {"value": 25740.4, "changePct": 0.2, "status": "QUOTE_RETURNED_FRESHNESS_UNVERIFIED", "priceSource": "NSE_PUBLIC_INDEX_SNAPSHOT", "provider": "Mock", "currency": "INR", "quoteTimestamp": int(time.time())}, "NIFTY FMCG": {"value": 25863.8, "changePct": -0.1, "status": "QUOTE_RETURNED_FRESHNESS_UNVERIFIED", "priceSource": "NSE_PUBLIC_INDEX_SNAPSHOT", "provider": "Mock", "currency": "INR", "quoteTimestamp": int(time.time())}, "NIFTY PHARMA": {"value": 25987.2, "changePct": 0.2, "status": "QUOTE_RETURNED_FRESHNESS_UNVERIFIED", "priceSource": "NSE_PUBLIC_INDEX_SNAPSHOT", "provider": "Mock", "currency": "INR", "quoteTimestamp": int(time.time())}, "NIFTY METAL": {"value": 26110.6, "changePct": -0.1, "status": "QUOTE_RETURNED_FRESHNESS_UNVERIFIED", "priceSource": "NSE_PUBLIC_INDEX_SNAPSHOT", "provider": "Mock", "currency": "INR", "quoteTimestamp": int(time.time())}, "NIFTY PSU BANK": {"value": 26234, "changePct": 0.2, "status": "QUOTE_RETURNED_FRESHNESS_UNVERIFIED", "priceSource": "NSE_PUBLIC_INDEX_SNAPSHOT", "provider": "Mock", "currency": "INR", "quoteTimestamp": int(time.time())}, "NIFTY PRIVATE BANK": {"value": 26357.4, "changePct": -0.1, "status": "QUOTE_RETURNED_FRESHNESS_UNVERIFIED", "priceSource": "NSE_PUBLIC_INDEX_SNAPSHOT", "provider": "Mock", "currency": "INR", "quoteTimestamp": int(time.time())}, "NIFTY ENERGY": {"value": 26480.8, "changePct": 0.2, "status": "QUOTE_RETURNED_FRESHNESS_UNVERIFIED", "priceSource": "NSE_PUBLIC_INDEX_SNAPSHOT", "provider": "Mock", "currency": "INR", "quoteTimestamp": int(time.time())}, "NIFTY INFRA": {"value": 26604.2, "changePct": -0.1, "status": "QUOTE_RETURNED_FRESHNESS_UNVERIFIED", "priceSource": "NSE_PUBLIC_INDEX_SNAPSHOT", "provider": "Mock", "currency": "INR", "quoteTimestamp": int(time.time())}, "NIFTY FIN SERVICE": {"value": 26727.6, "changePct": 0.2, "status": "QUOTE_RETURNED_FRESHNESS_UNVERIFIED", "priceSource": "NSE_PUBLIC_INDEX_SNAPSHOT", "provider": "Mock", "currency": "INR", "quoteTimestamp": int(time.time())}, "GOLD FUTURES (GLOBAL)": {"value": 26851, "changePct": -0.1, "status": "QUOTE_RETURNED_FRESHNESS_UNVERIFIED", "priceSource": "NSE_PUBLIC_INDEX_SNAPSHOT", "provider": "Mock", "currency": "USD", "quoteTimestamp": int(time.time())}, "SILVER FUTURES (GLOBAL)": {"value": 26974.4, "changePct": 0.2, "status": "QUOTE_RETURNED_FRESHNESS_UNVERIFIED", "priceSource": "NSE_PUBLIC_INDEX_SNAPSHOT", "provider": "Mock", "currency": "USD", "quoteTimestamp": int(time.time())}, "BRENT CRUDE (GLOBAL)": {"value": 27097.8, "changePct": -0.1, "status": "QUOTE_RETURNED_FRESHNESS_UNVERIFIED", "priceSource": "NSE_PUBLIC_INDEX_SNAPSHOT", "provider": "Mock", "currency": "USD", "quoteTimestamp": int(time.time())}}},
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
            browser = launch_chromium(p)
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.on("pageerror", lambda e: errors.append(str(e)))
            mock_js = '''
              Object.defineProperty(window,"localStorage",{value:{_s:{},getItem(k){return this._s[k]??null},setItem(k,v){this._s[k]=String(v)},removeItem(k){delete this._s[k]}}});
              const MOCK_API = ''' + json.dumps(self.mock_api, separators=(",", ":")) + ''';
              window.__indicesApiCalls=0;
              window.fetch=(u,opts)=>{const path=String(u).split("?")[0];if(path.endsWith("/api/indices"))window.__indicesApiCalls++;const key=Object.keys(MOCK_API).find(k=>path.endsWith(k));const value=key?MOCK_API[key]:{ok:false,error:"unmocked "+path};return Promise.resolve(new Response(JSON.stringify(value),{status:200,headers:{"Content-Type":"application/json"}}));};
            '''
            html = HTML.read_text(encoding="utf-8")
            pos = html.find("<script")
            html = html[:pos] + "<script>" + mock_js + "</script>" + html[pos:]
            page.set_content(html, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(250)
            self.assertIn("V40.79", page.locator(".taglive").first.inner_text())
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
            page.locator(".tab").first.click()  # Return to Overview before testing dashboard-level query controls.
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
            self.assertEqual(page.evaluate("safeNewsHref('javascript:alert(1)')"), "#")
            self.assertEqual(page.evaluate("safeNewsHref('data:text/html,<script>alert(1)</script>')"), "#")
            self.assertTrue(page.evaluate("safeNewsHref('https://example.com/news')").startswith("https://"))
            self.assertEqual(errors, [], f"JavaScript errors: {errors}")
            browser.close()

    def test_index_panel_renders_all_requested_markets_and_source_metadata(self):
        errors = []
        with sync_playwright() as p:
            browser = launch_chromium(p)
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.on("pageerror", lambda e: errors.append(str(e)))
            mock_js = '''
              Object.defineProperty(window,"localStorage",{value:{_s:{},getItem(k){return this._s[k]??null},setItem(k,v){this._s[k]=String(v)},removeItem(k){delete this._s[k]}}});
              const MOCK_API = ''' + json.dumps(self.mock_api, separators=(",", ":")) + ''';
              window.__indicesApiCalls=0;
              window.fetch=(u,opts)=>{const path=String(u).split("?")[0];if(path.endsWith("/api/indices"))window.__indicesApiCalls++;const key=Object.keys(MOCK_API).find(k=>path.endsWith(k));const value=key?MOCK_API[key]:{ok:false,error:"unmocked "+path};return Promise.resolve(new Response(JSON.stringify(value),{status:200,headers:{"Content-Type":"application/json"}}));};
            '''
            html = HTML.read_text(encoding="utf-8")
            pos = html.find("<script")
            html = html[:pos] + "<script>" + mock_js + "</script>" + html[pos:]
            page.set_content(html, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_function("document.querySelectorAll('#indices .icard').length === 18", timeout=8000)
            cards = page.locator("#indices .icard")
            self.assertEqual(cards.count(), 18)
            text = page.locator("#indices").inner_text()
            for label in ["NIFTY 50", "SENSEX", "NIFTY BANK", "MIDCAP 100", "SMALLCAP 100",
                          "NIFTY IT", "NIFTY AUTO", "NIFTY FMCG", "NIFTY PHARMA", "NIFTY METAL",
                          "PSU BANK", "PRIVATE BANK", "NIFTY ENERGY", "NIFTY INFRA", "FIN SERVICE",
                          "GOLD FUTURES (GLOBAL)", "SILVER FUTURES (GLOBAL)", "BRENT CRUDE (GLOBAL)"]:
                self.assertIn(label, text)
            self.assertIn("INR", text)
            self.assertIn("USD", text)
            self.assertIn("QUOTE RETURNED", text)
            self.assertIn("STALE • LAST AVAILABLE PRICE", text)
            self.assertIn("Mock", text)
            self.assertGreaterEqual(page.evaluate("window.__indicesApiCalls"), 1, "Index API must load at startup")
            page.locator("#indicesRefreshBtn").click()
            page.wait_for_function("window.__indicesApiCalls >= 2", timeout=3000)
            page.wait_for_function("document.querySelectorAll('#indices .icard').length === 18", timeout=5000)
            self.assertEqual(errors, [], f"JavaScript errors: {errors}")
            browser.close()

    def test_mobile_layout_has_no_page_wide_horizontal_overflow(self):
        with sync_playwright() as p:
            browser = launch_chromium(p)
            page = browser.new_page(viewport={"width": 390, "height": 844})
            html = HTML.read_text(encoding="utf-8")
            page.set_content(html, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(100)
            dims = page.evaluate("({viewport:innerWidth, document:document.documentElement.scrollWidth, body:document.body.scrollWidth})")
            self.assertLessEqual(dims["document"], dims["viewport"] + 2, f"Horizontal overflow: {dims}")
            browser.close()

    def test_risk_summary_never_claims_low_risk_from_missing_fields(self):
        html = HTML.read_text(encoding="utf-8")
        self.assertIn("Risk evidence is incomplete", html)
        self.assertIn("not a full risk clearance", html)
        self.assertIn("Low factor score — review evidence and coverage", html)

    def test_quote_data_disclaimer_is_explicit(self):
        source = (Path(__file__).parents[1] / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("marketDataDisclaimer", source)
        self.assertIn("No authorized NSE real-time feed is configured", source)


    def test_provider_wording_does_not_claim_unverified_quotes_are_live(self):
        html = HTML.read_text(encoding="utf-8")
        source = (Path(__file__).parents[1] / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertNotIn("dataConfidence:'LIVE QUOTE'", html)
        self.assertNotIn("Verified exchange + Screener HTTP", html)
        self.assertIn("QUOTE RETURNED • FRESHNESS UNVERIFIED", html)
        self.assertIn("UNVERIFIED_NO_PROVIDER_QUOTE_TIMESTAMP", source)
        self.assertNotIn('.put("priceTimestamp", System.currentTimeMillis() / 1000L)', source)

    def test_api_response_headers_are_hardened_and_not_public_wildcard(self):
        source = (Path(__file__).parents[1] / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn('"X-Content-Type-Options" to "nosniff"', source)
        self.assertIn('"Cache-Control" to "no-store, max-age=0"', source)
        self.assertNotIn('"Access-Control-Allow-Origin" to "*"', source)

    def test_version_code_and_name_are_aligned(self):
        gradle = (Path(__file__).parents[1] / "app/build.gradle").read_text(encoding="utf-8")
        self.assertIn("versionCode 78", gradle)
        self.assertIn("versionName '40.79'", gradle)

    def test_workflow_artifact_names_match_release_version(self):
        workflow = (Path(__file__).parents[1] / ".github/workflows/build-apk.yml").read_text(encoding="utf-8")
        self.assertIn("PRO-STOCK-INTELLIGENCE-V40-79-lint-report", workflow)
        self.assertIn("PRO-STOCK-INTELLIGENCE-V40-79-debug", workflow)
        self.assertNotIn("V40-57", workflow)
        self.assertIn("pull_request:", workflow)
        self.assertIn("sha256sum app/build/outputs/apk/debug/app-debug.apk", workflow)

    def test_frontend_and_native_engine_version_contract_matches(self):
        html = HTML.read_text(encoding="utf-8")
        source = (Path(__file__).parents[1] / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        import re
        client = re.search(r"CLIENT_ENGINE_VERSION='([^']+)'", html)
        server = re.search(r'put\("engine", "([^"]+)"\)', source)
        self.assertIsNotNone(client)
        self.assertIsNotNone(server)
        self.assertEqual(client.group(1), server.group(1), "UI must not report a false server-version mismatch")
        self.assertIn("V40.79", html)
        self.assertIn("V40.79", source)


    def test_canonical_preserves_index_and_futures_tickers_without_external_market_provider(self):
        source = (Path(__file__).parents[1] / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        canonical = source[source.index("private fun canonical"):source.index("private fun stockName")]
        self.assertIn('upper.matches(Regex("^\\\\^[A-Z0-9]+$"))', canonical)
        self.assertIn('upper.matches(Regex("^[A-Z]{1,5}=F$"))', canonical)
        # Canonicalization must preserve index/futures syntax without enabling an external provider.
        for ticker in ["^NSEI", "^BSESN", "^NSEBANK", "GC=F", "SI=F", "BZ=F"]:
            self.assertTrue(ticker.startswith("^") or ticker.endswith("=F"))


    def test_indices_panel_never_presents_historical_fallback_as_live(self):
        html = HTML.read_text(encoding="utf-8")
        source = (Path(__file__).parents[1] / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        required = ["NIFTY 50", "SENSEX", "NIFTY BANK", "NIFTY MIDCAP 100", "NIFTY SMALLCAP 100",
                    "NIFTY IT", "NIFTY AUTO", "NIFTY FMCG", "NIFTY PHARMA", "NIFTY METAL",
                    "NIFTY PSU BANK", "NIFTY PRIVATE BANK", "NIFTY ENERGY", "NIFTY INFRA",
                    "NIFTY FIN SERVICE", "GOLD FUTURES (GLOBAL)", "SILVER FUTURES (GLOBAL)", "BRENT CRUDE (GLOBAL)"]
        market_fn = source[source.index("private fun marketIndices()"):source.index("\n    fun handle(path: String)")]
        for label in required:
            self.assertIn(label, market_fn)
            self.assertIn(label, html)
        self.assertIn("AUTHORIZED_NSE_FEED_NOT_CONFIGURED", source)
        self.assertIn("HISTORICAL BAR • NOT LIVE", html)
        self.assertIn("QUOTE RETURNED • FRESHNESS UNVERIFIED", html)
        self.assertIn("quoteTimestamp", market_fn)
        self.assertIn("isExchangeCertifiedRealtime", market_fn)


    def test_webview_navigation_policy_blocks_non_https_and_external_pages_stay_outside_app(self):
        source = (Path(__file__).parents[1] / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("private fun isAllowedInApp(uri: Uri): Boolean", source)
        self.assertIn('host == "appassets.androidplatform.net"', source)
        self.assertIn('host == "screener.in"', source)
        self.assertIn('Intent(Intent.ACTION_VIEW, uri)', source)
        self.assertIn('uri.scheme.equals("https", ignoreCase = true)', source)
        self.assertIn("setAcceptThirdPartyCookies(web, false)", source)

    def test_android_backup_disabled_and_cleartext_blocked(self):
        manifest = (Path(__file__).parents[1] / "app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
        self.assertIn('android:allowBackup="false"', manifest)
        self.assertIn('android:fullBackupContent="false"', manifest)
        self.assertIn('android:usesCleartextTraffic="false"', manifest)

    def test_mixed_provider_session_is_not_mislabeled_fully_authenticated(self):
        source = (Path(__file__).parents[1] / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("SCREENER FUNDAMENTALS FETCHED; NSE QUOTE UNAVAILABLE UNTIL AUTHORIZED FEED IS CONFIGURED", source)
        self.assertNotIn('put("dataConfidence", "AUTHENTICATED")', source)
        html = (Path(__file__).parents[1] / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        self.assertNotIn("dataConfidence:'AUTHENTICATED'", html)
        self.assertIn("NATIVE ENGINE", html)
        self.assertIn("Corporate events are unavailable until an authorized NSE/company-filings source is configured.", source)


    def test_provider_gateway_contract_and_validator_are_present(self):
        root = Path(__file__).parents[1]
        contract = (root / "PROVIDER_GATEWAY.md").read_text(encoding="utf-8")
        validator = (root / "tools/validate_provider_payloads.py").read_text(encoding="utf-8")
        self.assertIn("never in Android resources", contract)
        self.assertIn("marketDataStatus", contract)
        self.assertIn("absenceVerified", validator)
        self.assertIn("strictly increasing", validator)

    def test_workflow_checks_foreground_activity_and_least_privilege(self):
        workflow = (Path(__file__).parents[1] / ".github/workflows/build-apk.yml").read_text(encoding="utf-8")
        self.assertIn("contents: read", workflow)
        # APK artifacts are uploaded before emulator validation, so device instability
        # cannot prevent artifact publication. Reject shell/PTY screenshot capture, but
        # allow binary-safe exec-out capture followed by PNG signature validation.
        self.assertIn("dumpsys activity activities", workflow)
        self.assertIn("com.prostock.intelligence/.MainActivity", workflow)
        self.assertNotIn("adb shell pidof com.prostock.intelligence", workflow)
        self.assertNotIn("adb shell screencap -p", workflow)
        self.assertIn("adb exec-out screencap -p", workflow)
        self.assertIn("Valid emulator screenshot", workflow)
        self.assertIn("Upload APK and checksum", workflow)
        self.assertIn("api-level: 34", workflow)
        self.assertIn("emulator-boot-timeout: 900", workflow)
        self.assertIn("disable-animations: true", workflow)
        self.assertIn("-gpu swiftshader_indirect", workflow)

    def test_source_claims_disclose_unintegrated_moneycontrol_and_history(self):
        source = (Path(__file__).parents[1] / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("NOT INTEGRATED — NO VERIFIED ACCESS/FEED CONFIGURED", source)
        self.assertIn("AUTHORIZED_NSE_HISTORICAL_FEED_NOT_CONFIGURED", source)
        self.assertIn("screenerReferencePrice", source)
        self.assertIn("FUNDAMENTALS ONLY — SCREENER PRICE IS REFERENCE ONLY", source)
        self.assertIn("authorized NSE real-time API/feed configured", source)
        html = HTML.read_text(encoding="utf-8")
        self.assertIn("Screener Reference Price (not live)", html)
        self.assertIn("Screener reference price only • live NSE quote unavailable", html)


    def test_chart_refresh_and_source_links_are_present(self):
        html = HTML.read_text(encoding="utf-8")
        self.assertIn('id="tvRefreshBtn"', html)
        self.assertIn('id="tvScreenerLinkBtn"', html)
        self.assertIn('id="tvMoneycontrolLinkBtn"', html)
        self.assertIn("NOT certified exchange-live", html)
        self.assertIn("chart-expanded", html)


    def test_v4078_disables_yahoo_and_unlicensed_nse_scraping(self):
        source = (Path(__file__).parents[1] / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertNotIn("https://query1.finance.yahoo.com", source)
        self.assertNotIn("https://query2.finance.yahoo.com", source)
        self.assertNotIn("https://www.nseindia.com/api/quote-equity", source)
        self.assertIn("authorized NSE real-time API/feed configured", source)
        self.assertIn("No third-party fallback is used", source)

    def test_screener_chart_endpoint_does_not_mislabel_yahoo_history(self):
        source = (Path(__file__).parents[1] / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("Screener.in does not expose a documented chart-data API", source)

    def test_csv_import_modal_parses_and_persists_authorized_export(self):
        errors = []
        with sync_playwright() as p:
            browser = launch_chromium(p)
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.on("pageerror", lambda e: errors.append(str(e)))
            html = HTML.read_text(encoding="utf-8")
            importer = (Path(__file__).parents[1] / "app/src/main/assets/csv-import.js").read_text(encoding="utf-8")
            html = html.replace('<script src="csv-import.js"></script>', '<script>\n' + importer + '\n</script>')
            mock_js = '''
              Object.defineProperty(window,"localStorage",{value:{_s:{},getItem(k){return this._s[k]??null},setItem(k,v){this._s[k]=String(v)},removeItem(k){delete this._s[k]}}});
              const MOCK_API = ''' + json.dumps(self.mock_api, separators=(",", ":")) + ''';
              window.fetch=(u,opts)=>{const path=String(u).split("?")[0];const key=Object.keys(MOCK_API).find(k=>path.endsWith(k));const value=key?MOCK_API[key]:{ok:false,error:"unmocked "+path};return Promise.resolve(new Response(JSON.stringify(value),{status:200,headers:{"Content-Type":"application/json"}}));};
            '''
            pos = html.find('<script')
            html = html[:pos] + '<script>' + mock_js + '</script>' + html[pos:]
            page.set_content(html, wait_until="domcontentloaded", timeout=30000)
            page.locator('#dataSourcesBtn').click()
            self.assertTrue(page.locator('#dataSourcesModal').is_visible())
            page.locator('#csvSource').select_option('Screener.in CSV')
            page.locator('#csvFile').set_input_files({"name":"sample.csv","mimeType":"text/csv","buffer":b"Name,NSE Code,Market Capitalization,Stock P/E,Dividend yield\nInfosys,INFY,650000,25.4,1.8"})
            page.wait_for_function("document.querySelector('#csvImportStatus').textContent.includes('Imported 1 stock row')", timeout=5000)
            store = page.evaluate("JSON.parse(localStorage.getItem('psi.provider.csv.v1'))")
            self.assertEqual(store['sources']['Screener.in CSV']['rows']['INFY']['fields']['dividendYield'], 1.8)
            # Also exercise the historical CSV path using the selected stock.
            page.locator('#search').fill('INFY')
            page.locator('#csvSource').select_option('User CSV')
            lines = ['Date,Open,High,Low,Close,Volume']
            from datetime import date, timedelta
            for i in range(24, -1, -1):
                day = date(2025, 1, 1) + timedelta(days=i)
                close = 100 + i
                lines.append(f'{day.isoformat()},{close-1},{close+2},{close-2},{close},1000')
            page.locator('#csvFile').set_input_files({"name":"infy-history.csv","mimeType":"text/csv","buffer":("\n".join(lines)).encode()})
            page.wait_for_function("document.querySelector('#csvImportStatus').textContent.includes('Imported 0 stock row(s) and 25 historical bar(s)')", timeout=5000)
            page.locator('#dataSourcesClose').click()
            page.locator('#analyze').click()
            page.wait_for_function("document.querySelector('#providerStatus').textContent.includes('CSV fallback:')", timeout=12000)
            self.assertIn('1 missing field(s) filled', page.locator('#providerStatus').inner_text())
            page.wait_for_function("window.chartRows && window.chartRows.length === 25", timeout=12000)
            self.assertIn('user-imported historical CSV', page.locator('#chartStatus').inner_text())
            self.assertEqual(errors, [])
            browser.close()

    def test_brand_logo_asset_header_and_android_launcher_icon_exist(self):
        root = Path(__file__).parents[1]
        html = (root / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        manifest = (root / "app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
        logo = root / "app/src/main/assets/brand-logo.svg"
        launcher = root / "app/src/main/res/drawable/ic_launcher.xml"
        self.assertTrue(logo.exists())
        self.assertIn('src="brand-logo.svg"', html)
        self.assertIn('class="brand"', html)
        self.assertIn('android:icon="@drawable/ic_launcher"', manifest)
        self.assertTrue(launcher.exists())
        self.assertIn("versionName '40.79'", (root / "app/build.gradle").read_text(encoding="utf-8"))


    def test_v4079_parses_additional_screener_valuation_fields(self):
        source = (Path(__file__).parents[1] / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        for field in ['"industry pe" to "industryPE"', '"peg ratio" to "peg"', '"face value" to "faceValue"',
                      '"piotroski score" to "piotroski"', '"dma 50" to "dma50"', '"dma 200" to "dma200"',
                      '"promoter holding" to "promoter"', '"public holding" to "public"', '"pledged percentage" to "pledged"']:
            with self.subTest(field=field):
                self.assertIn(field, source)
        html = HTML.read_text(encoding="utf-8")
        for metric in ["Industry P/E", "PEG Ratio", "Book Value", "EPS", "Dividend Yield", "Face Value"]:
            with self.subTest(metric=metric):
                self.assertIn("criterion('" + metric + "'", html)

    def test_peg_is_not_falsely_derived_from_profit_growth(self):
        html = HTML.read_text(encoding="utf-8")
        self.assertIn("Number(f.eps3y)>0", html)
        self.assertNotIn("Number(f.profit3y)>0)f.peg=Number(f.pe)/Number(f.profit3y)", html)

    def test_unavailable_calendar_is_not_rendered_as_verified_empty(self):
        html = HTML.read_text(encoding="utf-8")
        self.assertIn("intelEventsLiveAvailable=d.liveData===true", html)
        self.assertIn("This is not confirmation that no events are scheduled", html)
        self.assertIn("Live results calendar is not connected", html)
        self.assertIn("No dividend candidates were returned", html)

    def test_mobile_chart_controls_wrap_without_toolbar_overlap(self):
        html = HTML.read_text(encoding="utf-8")
        self.assertIn(".tvtoolbar.tvtoolbar-pro{height:auto!important", html)
        self.assertIn(".tvtoolbar-pro .tvmaincontrols,.tvtoolbar-pro .tvrightcontrols{flex:1 1 100%!important", html)
        self.assertIn(".tvpane.pricepane{height:390px!important", html)


    def test_v4080_gateway_is_https_configurable_and_secrets_stay_server_side(self):
        gradle = (Path(__file__).parents[1] / "app/build.gradle").read_text(encoding="utf-8")
        source = (Path(__file__).parents[1] / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("providerGatewayBaseUrl", gradle)
        self.assertIn("PROVIDER_GATEWAY_BASE_URL", source)
        self.assertIn('"/v1/quote"', source)
        self.assertIn('"/v1/history"', source)
        self.assertIn('"/v1/events"', source)
        self.assertIn('"/v1/dividends"', source)
        self.assertIn("Provider quote is stale", source)
        self.assertIn("Provider returned a different symbol", source)
        self.assertIn("credentialsInApk", source)

    def test_screener_403_is_reported_without_bypass_or_response_body(self):
        source = (Path(__file__).parents[1] / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("Screener returned HTTP 403 Forbidden", source)
        self.assertIn("will not bypass the restriction", source)
        self.assertIn('if (code !in 200..299) throw IOException("HTTP $code from $host")', source)

    def test_live_events_require_gateway_source_and_timestamp(self):
        source = (Path(__file__).parents[1] / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("Event feed source is missing", source)
        self.assertIn("Event feed timestamp is stale or in the future", source)
        self.assertIn("Empty results mean no rows were returned, not that no events exist.", source)
        self.assertIn("This is not confirmation that no result dates are scheduled.", source)

if __name__ == "__main__":
    unittest.main()
