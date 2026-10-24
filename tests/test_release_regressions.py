from pathlib import Path
import re
import unittest

ROOT = Path(__file__).parents[1]

class ReleaseRegressionTests(unittest.TestCase):
    def test_emulator_smoke_waits_for_android_services_and_retries_transient_install(self):
        workflow = (ROOT / ".github/workflows/build-apk.yml").read_text(encoding="utf-8")
        script = (ROOT / ".github/scripts/android-smoke-test.sh").read_text(encoding="utf-8")
        self.assertIn("script: bash .github/scripts/android-smoke-test.sh", workflow)
        self.assertIn("service check package", script)
        self.assertIn("service check activity", script)
        self.assertIn("for attempt in 1 2 3 4; do", script)
        self.assertIn("APK installation failed after 4 attempts", script)
        self.assertIn("adb logcat -d -t 1200", script)
        self.assertIn('adb shell am start -W -n "$ACTIVITY"', script)
        self.assertIn('ACTIVITY="com.prostock.intelligence/.MainActivity"', script)
        self.assertNotIn("while [ \"$attempt\" -lt 4 ]; do", workflow)

    def test_emulator_screenshot_does_not_write_to_sdcard(self):
        script = (ROOT / ".github/scripts/android-smoke-test.sh").read_text(encoding="utf-8")
        self.assertIn("adb exec-out screencap -p > app/build/outputs/psi-emulator.png", script)
        self.assertNotIn("adb shell screencap -p /sdcard/psi-emulator.png", script)
        self.assertIn("89504e470d0a1a0a", script)

    def test_autocomplete_has_broad_provider_search_and_disclaimer(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("private fun equitySearch", source)
        self.assertNotIn("query1.finance.yahoo.com", source)
        self.assertNotIn("query2.finance.yahoo.com", source)
        self.assertIn("private fun equitySearch", source)
        self.assertIn("Local symbol list only; broad search unavailable", source)
        self.assertIn("not a complete official NSE/BSE security master", source)
        self.assertIn('"exchange", "LISTING_UNVERIFIED"', source)
        self.assertIn("exchange listing not verified", source)
        self.assertNotIn("NSE public endpoint with disclosed third-party fallback", source)

    def test_ui_and_native_engine_versions_match(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("V40.81 AUTHORIZED GATEWAY + CSV OHLCV FALLBACK", html)
        self.assertIn('"engine", "V40.81 AUTHORIZED GATEWAY + CSV OHLCV FALLBACK"', source)

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
        self.assertIn("V40.81 AUTHORIZED GATEWAY + CSV OHLCV FALLBACK", html)
        self.assertIn('"engine", "V40.81 AUTHORIZED GATEWAY + CSV OHLCV FALLBACK"', source)
        self.assertIn("versionCode 80; versionName '40.81'", gradle)
        self.assertIn("DASHBOARD_VERSION='V40.81'", html)
        self.assertIn("window.__PSI_BOOT_VERSION='V40.81'", html)
        self.assertNotIn("DASHBOARD_VERSION='V40.75'", html)
        self.assertNotIn("window.__PSI_BOOT_VERSION='V40.75'", html)
        self.assertIn(".researchRibbon:after{content:'V40.81'", html)


    def test_screener_session_cookie_checks_both_hosts_and_surfaces_parse_error(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn('CookieManager.getInstance().getCookie(url)', source)
        self.assertIn("avoid stale duplicate cookies", source)
        self.assertIn("private fun screenerCookieHeader()", source)
        self.assertIn("Screener HTTP 403 Forbidden", source)
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

    def test_provider_realtime_claim_never_implies_exchange_certification(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn('.put("isExchangeCertifiedRealtime", false)', source)
        self.assertNotIn('.put("isExchangeCertifiedRealtime", status == "REALTIME")', source)

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
        self.assertIn("val ratioContainer = Regex", source)
        self.assertIn("val ratiosSectionHtml = ratioContainer?.groupValues?.get(2) ?: \"\"", source)
        self.assertIn("section|div|ul|ol", source)
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


    def test_screener_top_ratios_parser_accepts_ul_container_and_reports_403(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        pattern = re.search(r'val ratioContainer = Regex\("""(.*?)"""\)', source)
        self.assertIsNotNone(pattern, "Kotlin top-ratios container regex is missing")
        regex = re.compile(pattern.group(1), re.IGNORECASE | re.DOTALL)
        samples = [
            '<ul id="top-ratios"><li><span class="name">Stock P/E</span><span class="number">24.5</span></li></ul>',
            '<section id="top-ratios"><li><span class="name">Stock P/E</span><span class="number">24.5</span></li></section>',
            '<div id="top-ratios"><li><span class="name">Stock P/E</span><span class="number">24.5</span></li></div>',
        ]
        for sample in samples:
            with self.subTest(sample=sample[:20]):
                match = regex.search(sample)
                self.assertIsNotNone(match)
                self.assertIn("Stock P/E", match.group(2))
        self.assertIn('HTTP_403_FORBIDDEN', source)
        self.assertIn('recommendedAction', source)
        self.assertIn('This app will not bypass access controls', source)

    def test_authorized_indices_gateway_is_validated_and_ci_smoke_is_conditional(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/build-apk.yml").read_text(encoding="utf-8")
        docs = (ROOT / "PROVIDER_GATEWAY.md").read_text(encoding="utf-8")
        self.assertIn('gatewayGet("/v1/indices")', source)
        self.assertIn('put("/v1/indices")', source)
        self.assertIn("Index feed timestamp is in the future", source)
        self.assertIn("Index feed is stale for declared", source)
        self.assertIn("/v1/indices", workflow)
        self.assertIn("PROVIDER_GATEWAY_BASE_URL", workflow)
        gateway_step = workflow.split("- name: Validate configured authorized provider gateway", 1)[1].split("- name: Build debug APK", 1)[0]
        self.assertIn("LIVE DATA NOT VERIFIED", gateway_step)
        self.assertIn("REQUIRE_LIVE_PROVIDER_GATEWAY", gateway_step)
        self.assertIn("REQUIRE_LIVE_DATA_INPUT", gateway_step)
        self.assertIn('exit 0', gateway_step)
        self.assertIn('exit 1', gateway_step)
        self.assertIn("timestamp or status is absent", docs)


    def test_v4081_screener_cookie_is_not_treated_as_verified_session(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        self.assertIn("d.connected&&d.loggedIn&&d.validated&&d.requestValidated", html)
        self.assertIn("Screener Access Denied (403)", html)
        self.assertIn("Official Screener login is opening", html)
        self.assertNotIn("✓ Screener Cookie Found — verify", html)

    def test_v4081_mobile_indices_and_chart_are_compact_and_stale_chart_clears(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        self.assertIn("grid-template-columns:repeat(2,minmax(0,1fr))!important", html)
        self.assertIn("Never leave the prior symbol/range chart visible after a failed refresh.", html)
        self.assertIn("No synthetic candles are shown.", html)
        self.assertIn("max-height:150px!important", html)


    def test_screener_connect_endpoint_performs_real_company_page_validation(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        start = source.index("private fun screenerConnectionTest()")
        end = source.index("/**", start)
        probe = source[start:end]
        self.assertIn('screener("INFY")', probe)
        self.assertIn('"CONNECTED_VERIFIED"', probe)
        self.assertIn('"HTTP_403_FORBIDDEN"', probe)
        self.assertIn('put("requestValidated", true)', probe)
        self.assertIn('"/api/screener/connect" -> JSONObject().put("ok", true).put("data", screenerConnectionTest())', source)

    def test_screener_ui_uses_simple_connect_and_connection_test_language(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        self.assertIn('id="session">Connect Screener</button>', html)
        self.assertIn('Official Screener login is opening', html)
        self.assertIn('Screener Access Denied (403)', html)
        self.assertIn('Official Screener login is opening', html)

    def test_screener_status_exposes_forbidden_state_to_ui(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        start = source.index("private fun screenerStatus()")
        end = source.index("/**", start)
        status = source[start:end]
        self.assertIn('put("requestValidated", false)', status)
        self.assertIn('"HTTP_403_FORBIDDEN"', status)
        self.assertIn('put("httpStatus", if (blocked) 403', status)
        self.assertIn('put("recommendedAction"', status)


    def test_screener_request_uses_exact_host_cookie_not_merged_sessions(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        start = source.index("private fun get(url: String)")
        end = source.index("private fun finite", start)
        request = source[start:end]
        self.assertIn("CookieManager.getInstance().getCookie(url)", request)
        self.assertNotIn('manager.getCookie("https://screener.in")', request)
        self.assertIn("avoid stale duplicate cookies", request)


    def test_screener_status_uses_one_canonical_cookie_jar(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        helper = source[source.index("private fun screenerCookieHeader()"):source.index("private fun screenerLoggedIn()")]
        self.assertIn('getCookie("https://www.screener.in/company/INFY/")', helper)
        self.assertNotIn('getCookie("https://screener.in")', helper)
        self.assertIn("Never combine", helper)

    def test_unconfigured_gateway_never_claims_live_provider_coverage(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn('else "NOT_CONFIGURED"', source)
        self.assertIn('AUTHORIZED_NSE_FEED_NOT_CONFIGURED', source)
        self.assertIn('Corporate events unavailable: configure an authorized HTTPS provider gateway', source)


    def test_gateway_configuration_is_not_mislabeled_as_health_verified(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("GATEWAY_URL_CONFIGURED_SCREENER_VALIDATED_GATEWAY_HEALTH_UNVERIFIED", source)
        self.assertIn("GATEWAY_URL_CONFIGURED_NOT_HEALTH_CHECKED", source)
        self.assertNotIn('"GATEWAY_CONFIGURED_AND_SCREENER_VALIDATED"', source)

    def test_index_snapshot_rejects_empty_duplicate_and_invalid_rows(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("Index feed returned no index rows; snapshot rejected", source)
        self.assertIn("Index feed contains duplicate index name", source)
        self.assertIn("has invalid value/changePct; snapshot rejected", source)


    def test_screener_login_opens_official_page_before_probing_and_stops_after_403(self):
        html = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
        handler_start = html.index("$('session').onclick=async()=>{")
        handler_end = html.index("window.refreshScreenerStatus=refreshScreenerStatus;", handler_start)
        handler = html[handler_start:handler_end]
        self.assertLess(handler.index("api('/api/screener/status'"), handler.index("api('/api/screener/connect'"))
        self.assertLess(handler.index("if(!current.cookieDetected)"), handler.index("api('/api/screener/connect'"))
        self.assertIn("https://www.screener.in/login/", handler)
        self.assertIn("Screener Access Denied (403)", handler)
        self.assertIn("Re-login once", handler)
        self.assertIn("use permitted CSV import or authorized access", handler)
        self.assertIn("Refusing an unexpected login URL", handler)

    def test_provider_validator_supports_every_gateway_payload_type(self):
        import subprocess
        import sys
        validator = ROOT / "tools/validate_provider_payloads.py"
        result = subprocess.run([sys.executable, str(validator), "--help"], capture_output=True, text=True, check=True)
        for kind in ("quote", "history", "events", "indices", "dividends"):
            self.assertIn(kind, result.stdout)

    def test_manual_release_mode_requires_verified_provider_gateway(self):
        workflow = (ROOT / ".github/workflows/build-apk.yml").read_text(encoding="utf-8")
        self.assertIn("require_live_data:", workflow)
        self.assertIn("REQUIRE_LIVE_DATA_INPUT", workflow)
        self.assertIn('if [ "$require_gateway" = "true" ]; then', workflow)

    def test_manual_workflow_defaults_to_live_data_release_gate(self):
        workflow = (ROOT / ".github/workflows/build-apk.yml").read_text(encoding="utf-8")
        dispatch = workflow.split("workflow_dispatch:", 1)[1].split("  # Feature-branch commits", 1)[0]
        self.assertIn("require_live_data:", dispatch)
        self.assertIn("default: true", dispatch)
        self.assertIn("LIVE DATA NOT VERIFIED", workflow)
        self.assertIn("does not qualify as a live-data release", workflow)

    def test_gateway_workflow_checks_requested_symbol_and_dividend_status(self):
        workflow = (ROOT / ".github/workflows/build-apk.yml").read_text(encoding="utf-8")
        self.assertIn("quote /tmp/psi-provider/quote.json --expected-symbol INFY", workflow)
        self.assertIn("history /tmp/psi-provider/history.json --expected-symbol INFY", workflow)
        self.assertIn('Dividend payload missing valid marketDataStatus', workflow)


if __name__ == "__main__":
    unittest.main()

    def test_screener_financial_section_parser_handles_nested_div_containers(self):
        source = (ROOT / "app/src/main/java/com/prostock/intelligence/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("Locate the matching close tag for the exact id-bearing container", source)
        self.assertIn("var depth = 1", source)
        self.assertIn("for (m in token.findAll(html, open.range.last + 1))", source)
        self.assertNotIn('html.indexOf("</div>", start)', source)
