from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]

class ReleaseRegressionTests(unittest.TestCase):
    def test_emulator_smoke_waits_for_android_services_and_retries_transient_install(self):
        workflow = (ROOT / ".github/workflows/build-apk.yml").read_text(encoding="utf-8")
        self.assertIn("service check package", workflow)
        self.assertIn("service check activity", workflow)
        self.assertIn("while [ \"$attempt\" -lt 4 ]; do", workflow)
        self.assertIn("APK installation failed after 4 attempts", workflow)
        self.assertIn("adb logcat -d -t 1200", workflow)
        self.assertIn("adb shell am start -W -n com.prostock.intelligence/.MainActivity", workflow)
        self.assertNotIn("for attempt in $(seq", workflow)
        self.assertNotIn("seq 1 180", workflow)

    def test_emulator_screenshot_does_not_write_to_sdcard(self):
        workflow = (ROOT / ".github/workflows/build-apk.yml").read_text(encoding="utf-8")
        self.assertIn("adb exec-out screencap -p > app/build/outputs/psi-emulator.png", workflow)
        self.assertNotIn("adb shell screencap -p /sdcard/psi-emulator.png", workflow)
        self.assertIn("89504e470d0a1a0a", workflow)

    def test_autocomplete_has_broad_provider_search_and_disclaimer(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("private fun equitySearch", source)
        self.assertNotIn("query1.finance.yahoo.com", source)
        self.assertNotIn("query2.finance.yahoo.com", source)
        self.assertIn("private fun equitySearch", source)
        self.assertIn("Local symbol list only; broad search unavailable", source)
        self.assertIn("not a complete official NSE/BSE security master", source)

    def test_ui_and_native_engine_versions_match(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("V40.80 AUTHORIZED GATEWAY + SCREENER FUNDAMENTALS", html)
        self.assertIn('"engine", "V40.80 AUTHORIZED GATEWAY + SCREENER FUNDAMENTALS"', source)

    def test_fundamental_parser_fails_closed_instead_of_guessing_nearby_number(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("Match the visible label and value in the same ratio list item", source)
        self.assertIn('matches(normalized)) return null', source)
        self.assertNotIn("val visibleText = cleanText(html)", source)
        self.assertNotIn("label.length + 100", source)

    def test_all_release_version_markers_are_aligned(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        gradle = (ROOT / "app/build.gradle").read_text(encoding="utf-8")
        self.assertIn("V40.80 AUTHORIZED GATEWAY + SCREENER FUNDAMENTALS", html)
        self.assertIn('"engine", "V40.80 AUTHORIZED GATEWAY + SCREENER FUNDAMENTALS"', source)
        self.assertIn("versionCode 79; versionName '40.80'", gradle)
        self.assertIn("DASHBOARD_VERSION='V40.80'", html)
        self.assertIn("window.__PSI_BOOT_VERSION='V40.80'", html)
        self.assertNotIn("DASHBOARD_VERSION='V40.75'", html)
        self.assertNotIn("window.__PSI_BOOT_VERSION='V40.75'", html)
        self.assertIn(".researchRibbon:after{content:'V40.80'", html)


    def test_screener_session_cookie_checks_both_hosts_and_surfaces_parse_error(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn('manager.getCookie("https://www.screener.in")', source)
        self.assertIn('manager.getCookie("https://screener.in")', source)
        self.assertIn("private fun screenerCookieHeader()", source)
        self.assertIn("Protected company data is not confirmed", source)
        self.assertIn('f.optString("providerError")', source)

    def test_ui_surfaces_screener_enrichment_failure(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        self.assertIn("Screener fundamentals not loaded:", html)
        self.assertIn("fundamentalError", html)

    def test_screener_login_or_changed_markup_is_rejected(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("Screener returned a login page instead of company data", source)
        self.assertIn("Screener company page could not be validated", source)
        self.assertIn("No fundamentals accepted", source)

    def test_cagr_preserves_missing_fiscal_column_positions(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("Preserve fiscal-column positions", source)
        self.assertIn("val periods = row.drop(1).take(4).map { asNumber(it) }", source)
        self.assertIn("val threeYearsBack = periods.getOrNull(3) ?: return", source)
        self.assertNotIn("row.drop(1).mapNotNull { asNumber(it) }.take(4)", source)

    def test_screener_data_carries_source_and_quality_metadata(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn('.put("sourceUrl", pageUrl)', source)
        self.assertIn('.put("fetchedAtEpochMs", fetchedAt)', source)
        self.assertIn('.put("qualityFlags", qualityFlags)', source)
        self.assertIn('"PAGE_VALIDATED_LOW_COVERAGE"', source)

    def test_quote_quality_does_not_infer_quote_time_from_response_time(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("UNVERIFIED_NO_PROVIDER_QUOTE_TIMESTAMP", source)
        self.assertIn("missing_not_inferred_from_response_time", source)
        self.assertIn("INVALID_FUTURE_TIMESTAMP", source)
        self.assertIn("quoteAgeSeconds", source)

    def test_exchange_label_does_not_always_claim_both_exchanges(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("q.exchange||'NSE/BSE availability not verified'", html)
        self.assertIn('raw.trim().uppercase(Locale.ROOT).endsWith(".BO") -> "BSE"', source)


    def test_ci_syntax_checks_the_shared_csv_import_module(self):
        workflow = (ROOT / ".github/workflows/build-apk.yml").read_text(encoding="utf-8")
        self.assertIn("node --check app/src/main/assets/csv-import.js", workflow)

    def test_v4071_csv_import_path_is_wired_and_moneycontrol_is_not_claimed_as_scraped(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        importer = (ROOT / "app/src/main/assets/csv-import.js").read_text(encoding="utf-8")
        self.assertIn('id="dataSourcesBtn"', html)
        self.assertIn('id="csvFile"', html)
        self.assertIn('src="csv-import.js"', html)
        self.assertIn("onShowFileChooser", source)
        self.assertIn("Moneycontrol CSV", html)
        self.assertIn("automated extraction", html)
        self.assertIn("parseImportCsv", importer)

    def test_latest_fiscal_column_does_not_skip_blank_cells(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn('row.getOrNull(1)?.let { asNumber(it) }', source)
        self.assertNotIn('row.drop(1).firstNotNullOfOrNull { asNumber(it) }', source)

    def test_future_quote_timestamps_are_not_marked_fresh(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn('age < -60L -> "INVALID_FUTURE_TIMESTAMP"', source)
        self.assertIn('FUTURE_TIMESTAMP_WITHIN_60S_CLOCK_SKEW', source)

    def test_landscape_orientation_is_not_locked_to_portrait(self):
        manifest = (ROOT / "app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
        self.assertNotIn('android:screenOrientation="portrait"', manifest)

    def test_moneycontrol_public_view_is_not_mislabeled_as_live_data_integration(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        self.assertIn("DISABLED_NO_AUTHORIZED_FEED_CONFIGURED", source)
        self.assertIn("/api/providers/status", source)
        self.assertIn("automated extraction is disabled", source.lower())
        self.assertIn("openMoneycontrolStock", html)
        self.assertIn("refreshProviderDiagnostics", html)
        self.assertIn("public viewing is not automated data integration", html.lower())

    def test_provider_diagnostics_disclose_screener_cookie_is_not_validation(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("SESSION_COOKIE_DETECTED_LIVE_PROBE_PENDING", source)
        self.assertIn("/api/providers/status", source)


    def test_provider_diagnostics_runs_a_real_screener_probe_when_session_cookie_exists(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("val fundamentals = screener(symbol)", source)
        self.assertIn('"LIVE_COMPANY_PAGE_VALIDATED"', source)
        self.assertIn('"LIVE_VALIDATION_FAILED"', source)
        self.assertIn('"validationDurationMs"', source)
        self.assertIn('"validatedFieldCount"', source)

    def test_moneycontrol_never_claims_live_data_without_authorized_feed(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn('"DISABLED_NO_AUTHORIZED_FEED_CONFIGURED"', source)
        self.assertIn('"dataFetched", false', source)
        self.assertIn("Public page access is not a data feed", source)


    def test_v4077_chart_refresh_is_provider_honest_and_zoom_preserving(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        self.assertIn("window.__psiAutoRefreshTimer=setInterval", html)
        self.assertIn("document.visibilityState!=='visible'", html)
        start = html.index("window.__psiAutoRefreshTimer=setInterval(async()=>{")
        end = html.index("},60000);", start)
        refresh = html[start:end]
        self.assertNotIn("activeRange!=='1d')return", refresh)
        self.assertIn("if(activeRange==='1d'&&sym===currentChartSymbol())", refresh)
        self.assertIn("loadChart('1d',{preserveView:true})", refresh)
        self.assertIn("NOT certified exchange-live", html)
        self.assertIn("Math.max(46,Math.min(72,w*.13))", html)


    def test_screener_enrichment_never_overwrites_existing_quote_with_history(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        self.assertIn("const currentMarket=cur.market||{}", html)
        self.assertIn("const historicalQuote=live.quote||{}", html)
        self.assertIn("if(validPrice(currentMarket.price)) mergedMarket.price=Number(currentMarket.price)", html)
        self.assertIn("Quote:currentMarket.provider||historicalQuote.provider||'Unavailable'", html)


    def test_quote_auto_refresh_runs_for_all_timeframes(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        start = html.index("window.__psiAutoRefreshTimer=setInterval(async()=>{")
        end = html.index("},60000);", start)
        block = html[start:end]
        self.assertIn("document.visibilityState!=='visible')return", block)
        self.assertNotIn("activeRange!=='1d')return", block)
        self.assertIn("api('/api/quote?symbol='+encodeURIComponent(sym),9000)", block)
        self.assertIn("if(activeRange==='1d'&&sym===currentChartSymbol())", block)


    def test_screener_ratio_parser_scopes_labels_and_accepts_debt_alias(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("val ratiosSectionHtml = Regex", source)
        self.assertIn("findAll(ratiosSectionHtml)", source)
        self.assertIn('"debt to equity"', source)
        self.assertIn('"eps in rs" -> setOf("eps in rs", "eps")', source)


    def test_null_or_zero_price_does_not_count_as_successful_quote(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        self.assertIn("function hasUsablePrice(v){return v!==null&&v!==undefined&&v!==''&&Number.isFinite(Number(v))&&Number(v)>0}", html)
        self.assertIn("const hasQuote=!!(fast.quote&&hasUsablePrice(fast.quote.price));", html)
        self.assertIn("if(b.quote&&hasUsablePrice(b.quote.price))", html)


    def test_screener_enrichment_preserves_explicit_bse_listing(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("val f = screener(raw)", source)
        self.assertIn("AUTHORIZED_NSE_FEED_NOT_CONFIGURED", source)
        self.assertIn("Screener provides fundamentals here; it is not used as a quote or candle provider.", source)
        self.assertIn('raw.trim().uppercase(Locale.ROOT).endsWith(".BO") -> "BSE"', source)


    def test_missing_numeric_values_are_not_coerced_to_zero(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        self.assertIn("function safeNum(v){if(v===null||v===undefined||v==='')return null;", html)
        self.assertIn("f[k]!==null&&f[k]!==undefined&&f[k]!==''&&Number.isFinite(Number(f[k]))", html)
        self.assertIn("Number(f.price)>0", html)


    def test_invalid_refresh_quote_does_not_clear_last_valid_display(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        self.assertIn("Quote refresh returned no valid price; previous display retained.", html)
        self.assertIn("if(hasUsablePrice(q.price))applyQuote(q,d.name||$('company').textContent,sym)", html)

if __name__ == "__main__":
    unittest.main()
