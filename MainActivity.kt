package com.prostock.intelligence

import android.app.Activity
import android.os.Bundle
import android.webkit.*
import android.net.Uri
import android.graphics.Color
import androidx.webkit.WebViewAssetLoader
import androidx.webkit.WebViewClientCompat
import org.json.JSONArray
import org.json.JSONObject
import java.io.ByteArrayInputStream
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.util.Locale
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import kotlin.math.abs

class MainActivity : Activity() {
    private lateinit var web: WebView
    private val provider = NativeProvider()

    private fun jsonResponse(json: String): WebResourceResponse =
        WebResourceResponse("application/json", "UTF-8", ByteArrayInputStream(json.toByteArray(Charsets.UTF_8))).apply {
            responseHeaders = mapOf("Cache-Control" to "no-store", "Access-Control-Allow-Origin" to "*")
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        CookieManager.getInstance().setAcceptCookie(true)
        web = WebView(this)
        web.setBackgroundColor(Color.rgb(237, 245, 251))
        web.settings.javaScriptEnabled = true
        web.settings.domStorageEnabled = true
        web.settings.databaseEnabled = true
        web.settings.allowFileAccess = false
        web.settings.allowContentAccess = false
        web.settings.mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
        web.settings.setSupportMultipleWindows(false)
        CookieManager.getInstance().setAcceptThirdPartyCookies(web, true)

        val assetLoader = WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()
        web.webViewClient = object : WebViewClientCompat() {
            private fun api(uri: Uri): WebResourceResponse? {
                if (uri.scheme != "https" || uri.host != "appassets.androidplatform.net" || uri.path?.startsWith("/api/") != true) return null
                return try {
                    provider.jsonResponseFor(uri.encodedPath + (uri.encodedQuery?.let { "?$it" } ?: ""))
                } catch (e: Exception) {
                    jsonResponse(JSONObject().put("ok", false).put("error", e.message ?: "Provider error").toString())
                }
            }
            override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest): WebResourceResponse? =
                api(request.url) ?: assetLoader.shouldInterceptRequest(request.url)
            @Suppress("DEPRECATION")
            override fun shouldInterceptRequest(view: WebView, url: String): WebResourceResponse? {
                val uri = Uri.parse(url)
                return api(uri) ?: assetLoader.shouldInterceptRequest(uri)
            }
            override fun onPageFinished(view: WebView, url: String) {
                super.onPageFinished(view, url)
                if (url.startsWith("https://www.screener.in/")) {
                    CookieManager.getInstance().flush()
                }
                if (url.startsWith("https://appassets.androidplatform.net/assets/index.html")) {
                    CookieManager.getInstance().flush()
                    view.evaluateJavascript("window.refreshScreenerStatus && window.refreshScreenerStatus()", null)
                }
            }
        }
        setContentView(web)
        web.loadUrl("https://appassets.androidplatform.net/assets/index.html")
    }

    @Deprecated("Deprecated in Android API")
    override fun onBackPressed() {
        if (::web.isInitialized && web.canGoBack()) web.goBack() else super.onBackPressed()
    }
}

private class NativeProvider {
    private data class Stock(val symbol: String, val name: String, val sector: String)
    private val stocks = listOf(
        Stock("INFY", "Infosys Ltd", "IT Services"), Stock("TCS", "Tata Consultancy Services Ltd", "IT Services"),
        Stock("HCLTECH", "HCL Technologies Ltd", "IT Services"), Stock("WIPRO", "Wipro Ltd", "IT Services"),
        Stock("TECHM", "Tech Mahindra Ltd", "IT Services"), Stock("LTIM", "LTIMindtree Ltd", "IT Services"),
        Stock("RELIANCE", "Reliance Industries Ltd", "Energy"), Stock("HDFCBANK", "HDFC Bank Ltd", "Banking"),
        Stock("ICICIBANK", "ICICI Bank Ltd", "Banking"), Stock("SBIN", "State Bank of India", "Banking"),
        Stock("AXISBANK", "Axis Bank Ltd", "Banking"), Stock("KOTAKBANK", "Kotak Mahindra Bank Ltd", "Banking"),
        Stock("BAJFINANCE", "Bajaj Finance Ltd", "Financial Services"), Stock("MARUTI", "Maruti Suzuki India Ltd", "Automobiles"),
        Stock("TATAMOTORS", "Tata Motors Ltd", "Automobiles"), Stock("TATASTEEL", "Tata Steel Ltd", "Metals"),
        Stock("NTPC", "NTPC Ltd", "Power"), Stock("POWERGRID", "Power Grid Corporation of India Ltd", "Power"),
        Stock("SUNPHARMA", "Sun Pharmaceutical Industries Ltd", "Pharma"), Stock("ITC", "ITC Ltd", "FMCG"),
        Stock("HINDUNILVR", "Hindustan Unilever Ltd", "FMCG"), Stock("TITAN", "Titan Company Ltd", "Consumer"),
        Stock("BEL", "Bharat Electronics Ltd", "Defence"), Stock("HAL", "Hindustan Aeronautics Ltd", "Defence"),
        Stock("TRENT", "Trent Ltd", "Consumer"), Stock("PERSISTENT", "Persistent Systems Ltd", "IT Services"),
        Stock("TATAELXSI", "Tata Elxsi Ltd", "IT Services"), Stock("DIXON", "Dixon Technologies India Ltd", "Electronics")
    )
    private val queryDefs = listOf(
        JSONObject().put("id", "master").put("name", "Large Cap Quality Stocks").put("description", "Large companies with quality and manageable debt").put("focus", "Market cap, ROCE, debt and valuation").put("query", "Market Capitalization > 10000 AND Current price > 50 AND Return on capital employed > 12 AND Debt to equity < 1"),
        JSONObject().put("id", "midcap").put("name", "Mid Cap Hidden Gems").put("description", "Mid-sized companies with profitability and growth").put("focus", "Market cap ₹5,000–30,000 Cr, ROCE > 15%").put("query", "Market Capitalization > 5000 AND Market Capitalization < 30000 AND Return on capital employed > 15 AND Return on equity > 15"),
        JSONObject().put("id", "smallcap").put("name", "Small Cap Quality").put("description", "Smaller profitable companies; higher risk").put("focus", "Market cap ₹1,000–5,000 Cr").put("query", "Market Capitalization > 1000 AND Market Capitalization < 5000 AND Return on capital employed > 15 AND Debt to equity < 1"),
        JSONObject().put("id", "oversold").put("name", "RSI Oversold Scanner (RSI ≤ 30)").put("description", "Technical scan of tracked stocks using Wilder RSI(14) from Yahoo daily bars; latest bar may be partial during market hours").put("focus", "Wilder RSI(14) ≤ 30; tracked symbols only, daily bars may be delayed or partial").put("query", "Technical scan: RSI(14) <= 30; tracked universe only"),
        JSONObject().put("id", "crash").put("name", "Daily Crash Scanner (drop ≥ 5%)").put("description", "Finds tracked stocks whose latest Yahoo daily bar is down at least 5% versus the prior daily bar; current-session bar may be partial").put("focus", "Latest daily-bar change ≤ -5%; tracked symbols only, not a whole-market scan").put("query", "Technical scan: daily change <= -5%; tracked universe only")
    )

    fun jsonResponseFor(path: String): WebResourceResponse = WebResourceResponse(
        "application/json", "UTF-8", ByteArrayInputStream(handle(path).toByteArray(Charsets.UTF_8))
    ).apply { responseHeaders = mapOf("Cache-Control" to "no-store", "Access-Control-Allow-Origin" to "*") }

    private fun parseQuery(path: String): Map<String, String> = path.substringAfter("?", "").split("&").mapNotNull {
        val a = it.split("=", limit = 2)
        if (a.size == 2) URLDecoderCompat.decode(a[0]) to URLDecoderCompat.decode(a[1]) else null
    }.toMap()

    private fun cleanText(s: String): String = s.replace(Regex("(?is)<script.*?</script>|<style.*?</style>"), " ")
        .replace(Regex("(?s)<[^>]+>"), " ").replace("&nbsp;", " ").replace("&amp;", "&")
        .replace("&#39;", "'").replace("&quot;", "\"").replace(Regex("\\s+"), " ").trim()

    private fun canonical(raw: String): String {
        val upper = raw.trim().uppercase(Locale.ROOT)
        val noSuffix = upper.removeSuffix(".NS").removeSuffix(".BO").trim()
        val compact = noSuffix.replace(Regex("[^A-Z0-9]"), "")
        val alias = when {
            compact.contains("INFOSYS") -> "INFY"
            compact.contains("TATACONSULTANCY") || compact == "TCS" -> "TCS"
            compact.contains("RELIANCE") -> "RELIANCE"
            compact.contains("HDFCBANK") -> "HDFCBANK"
            compact.contains("ICICIBANK") -> "ICICIBANK"
            compact.contains("STATEBANKOFINDIA") || compact == "SBIN" -> "SBIN"
            compact.contains("HCLTECH") || compact.contains("HCLTECHNOLOGIES") -> "HCLTECH"
            compact.contains("WIPRO") -> "WIPRO"
            compact.contains("TECHMAHINDRA") -> "TECHM"
            compact.contains("TATAELXSI") -> "TATAELXSI"
            else -> null
        }
        if (alias != null) return alias
        val exact = stocks.firstOrNull { it.symbol == noSuffix || it.name.uppercase(Locale.ROOT).replace(Regex("[^A-Z0-9]"), "") == compact }
        if (exact != null) return exact.symbol
        return noSuffix.replace(Regex("\\s+"), "").replace(Regex("[^A-Z0-9^=.-]"), "")
    }
    private fun stockName(symbol: String): String = stocks.firstOrNull { it.symbol == symbol }?.name ?: symbol
    private fun stockSector(symbol: String): String = stocks.firstOrNull { it.symbol == symbol }?.sector ?: "Equity"
    private fun inputSuffix(raw: String): String = if (raw.trim().uppercase(Locale.ROOT).endsWith(".BO")) ".BO" else ".NS"

    private fun get(url: String): String {
        val c = URL(url).openConnection() as HttpURLConnection
        c.connectTimeout = 4000
        c.readTimeout = 6000
        c.instanceFollowRedirects = true
        c.setRequestProperty("User-Agent", "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/126.0.0.0 Mobile Safari/537.36 PRO-STOCK-INTELLIGENCE/1.0")
        c.setRequestProperty("Accept", "application/json,text/html,application/xhtml+xml,*/*")
        c.setRequestProperty("Accept-Language", "en-IN,en;q=0.9")
        val host = URL(url).host.lowercase(Locale.ROOT)
        if (host == "screener.in" || host.endsWith(".screener.in")) {
            c.setRequestProperty("Referer", "https://www.screener.in/")
            val cookie = CookieManager.getInstance().getCookie("https://www.screener.in")
            if (!cookie.isNullOrBlank()) c.setRequestProperty("Cookie", cookie)
        }
        try {
            val code = c.responseCode
            val stream = if (code in 200..299) c.inputStream else c.errorStream
            val body = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() } ?: ""
            if (code !in 200..299) throw IOException("HTTP $code from $host${if (body.isNotBlank()) ": ${body.take(120)}" else ""}")
            return body
        } finally { c.disconnect() }
    }

    private fun finite(n: Double): Boolean = !n.isNaN() && !n.isInfinite()
    private fun putFinite(o: JSONObject, key: String, n: Double) { if (finite(n)) o.put(key, n) }

    // V40.82 policy guard: external Yahoo-based fallbacks are disabled.
    // Do not silently substitute an unapproved source for NSE live/historical data.
    private fun yahoo(raw: String, range: String = "1y"): JSONObject {
        val symbol = canonical(raw)
        return JSONObject()
            .put("symbol", symbol)
            .put("rows", JSONArray())
            .put("events", JSONArray())
            .put("provider", "UNAVAILABLE — authorized market-data gateway not configured")
            .put("marketDataStatus", "UNAVAILABLE")
            .put("providerError", "Yahoo Finance fallback is disabled by app policy. Configure an authorized provider gateway for quote/history/events.")
            .put("requestedRange", range)
    }

    private fun sectionTableRows(html: String, sectionId: String): List<List<String>> {
        val idRegex = Regex("(?is)<section\\b[^>]*id=[\"']" + Regex.escape(sectionId) + "[\"'][^>]*>")
        val sectionMatch = idRegex.find(html)
        val section = if (sectionMatch != null) {
            val start = sectionMatch.range.last + 1
            val end = html.indexOf("</section>", start).let { if (it >= 0) it else html.length }
            html.substring(start, end)
        } else {
            val divRegex = Regex("(?is)<div\\b[^>]*id=[\"']" + Regex.escape(sectionId) + "[\"'][^>]*>")
            val divMatch = divRegex.find(html) ?: return emptyList()
            val start = divMatch.range.last + 1
            val end = html.indexOf("</div>", start).let { if (it >= 0) it else html.length }
            html.substring(start, end)
        }
        val table = Regex("(?is)<table\\b[^>]*>(.*?)</table>").find(section)?.groupValues?.getOrNull(1) ?: return emptyList()
        return Regex("(?is)<tr\\b[^>]*>(.*?)</tr>").findAll(table).mapNotNull { row ->
            val cells = Regex("(?is)<t[hd]\\b[^>]*>(.*?)</t[hd]>").findAll(row.groupValues[1]).map { cleanText(it.groupValues[1]) }.toList()
            if (cells.isEmpty()) null else cells
        }.toList()
    }

    private fun asNumber(raw: String?): Double? {
        if (raw.isNullOrBlank() || raw == "—" || raw == "-" || raw.equals("NA", true)) return null
        val normalized = raw.replace(",", "").replace("₹", "").replace("%", "").replace("Cr.", "").trim()
        return Regex("-?[0-9]+(?:\\.[0-9]+)?").find(normalized)?.value?.toDoubleOrNull()
    }

    private fun jsonRows(rows: List<List<String>>): JSONArray = JSONArray().apply {
        rows.forEach { row -> put(JSONArray().apply { row.forEach { put(it) } }) }
    }

    private fun quarterlyRows(rows: List<List<String>>): JSONArray {
        if (rows.size < 2) return JSONArray()
        val header = rows.first()
        if (header.size < 2) return JSONArray()
        val metricRows = rows.drop(1).associateBy { it.firstOrNull()?.trim()?.lowercase(Locale.ROOT).orEmpty() }
        fun value(label: String, col: Int): String? = metricRows.entries.firstOrNull { (key, _) -> key == label || key.startsWith("$label ") }?.value?.getOrNull(col)
        return JSONArray().apply {
            for (col in 1 until header.size) {
                val period = header[col].trim()
                if (period.isBlank()) continue
                val item = JSONObject().put("period", period)
                listOf(
                    "sales" to "sales", "expenses" to "expenses", "operating_profit" to "operating profit",
                    "opm" to "opm %", "other_income" to "other income", "interest" to "interest",
                    "depreciation" to "depreciation", "profit_before_tax" to "profit before tax",
                    "tax" to "tax %", "net_profit" to "net profit", "eps" to "eps in rs"
                ).forEach { (outKey, label) -> value(label, col)?.let { item.put(outKey, it) } }
                put(item)
            }
        }
    }

    private fun screener(raw: String): JSONObject {
        val s = canonical(raw)
        val html = get("https://www.screener.in/company/${Uri.encode(s)}/")
        fun number(label: String, percent: Boolean = false): Double? {
            val idx = html.indexOf(label, ignoreCase = true)
            if (idx < 0) return null
            val fragment = html.substring(idx, minOf(html.length, idx + 900))
            val plain = cleanText(fragment)
            val after = plain.substringAfter(label, "")
            if (after.isBlank()) return null
            val match = Regex("(?:₹\\s*)?(-?[0-9][0-9,]*(?:\\.[0-9]+)?)\\s*${if (percent) "%" else ""}").find(after)
            return match?.groupValues?.get(1)?.replace(",", "")?.toDoubleOrNull()
        }
        val f = JSONObject()
        number("Current Price")?.let { f.put("price", it) }
        number("Market Cap")?.let { f.put("marketCap", it) }
        number("Stock P/E")?.let { f.put("pe", it) }
        number("Book Value")?.let { f.put("bookValue", it) }
        number("Dividend Yield", true)?.let { f.put("dividendYield", it) }
        number("ROCE", true)?.let { f.put("roce", it) }
        number("ROE", true)?.let { f.put("roe", it) }
        number("Debt / Equity")?.let { f.put("debtEquity", it) }
        number("EPS in Rs")?.let { f.put("eps", it) }
        val pnlRows = sectionTableRows(html, "profit-loss")
        val qRows = sectionTableRows(html, "quarters")
        val ownershipRows = sectionTableRows(html, "shareholding")
        val balanceRows = sectionTableRows(html, "balance-sheet")
        fun rowFor(rows: List<List<String>>, label: String): List<String>? = rows.drop(1).firstOrNull { it.firstOrNull()?.trim()?.equals(label, true) == true }
        fun setLatestFromTable(rows: List<List<String>>, label: String, key: String) {
            val row = rowFor(rows, label) ?: return
            val value = row.drop(1).firstNotNullOfOrNull { asNumber(it) }
            if (value != null) f.put(key, value)
        }
        setLatestFromTable(pnlRows, "Net Profit", "netProfit")
        setLatestFromTable(pnlRows, "Operating Profit", "operatingProfit")
        setLatestFromTable(pnlRows, "OPM %", "opm")
        setLatestFromTable(pnlRows, "Interest", "interestExpense")
        // Calculate 3-year CAGR only when both the oldest and latest table values are positive and present.
        fun setCagr(rows: List<List<String>>, label: String, key: String) {
            val row = rowFor(rows, label) ?: return
            val values = row.drop(1).mapNotNull { asNumber(it) }.take(4)
            if (values.size == 4 && values.first() > 0 && values.last() > 0) {
                val cagr = (Math.pow(values.first() / values.last(), 1.0 / 3.0) - 1.0) * 100.0
                if (cagr.isFinite()) f.put(key, cagr)
            }
        }
        setCagr(pnlRows, "Sales", "sales3y")
        setCagr(pnlRows, "Net Profit", "profit3y")
        setCagr(pnlRows, "EPS in Rs", "eps3y")
        val currentAssets = rowFor(balanceRows, "Current Assets")?.drop(1)?.firstNotNullOfOrNull { asNumber(it) }
        val currentLiabilities = rowFor(balanceRows, "Current Liabilities")?.drop(1)?.firstNotNullOfOrNull { asNumber(it) }
        if (currentAssets != null && currentLiabilities != null && currentLiabilities > 0) f.put("currentRatio", currentAssets / currentLiabilities)
        val latestOperating = rowFor(pnlRows, "Operating Profit")?.drop(1)?.firstNotNullOfOrNull { asNumber(it) }
        val latestInterest = rowFor(pnlRows, "Interest")?.drop(1)?.firstNotNullOfOrNull { asNumber(it) }
        if (latestOperating != null && latestInterest != null && latestInterest > 0) f.put("interestCoverage", latestOperating / latestInterest)
        if (pnlRows.isNotEmpty()) f.put("pnl", jsonRows(pnlRows))
        if (qRows.isNotEmpty()) {
            val qData = quarterlyRows(qRows)
            f.put("quarterly", qData)
            // Compare the two most recent reported quarters only when both values exist and the prior quarter is non-zero.
            if (qData.length() >= 2) {
                val latest = qData.optJSONObject(0)?.optString("net_profit", "")?.let { asNumber(it) }
                val prior = qData.optJSONObject(1)?.optString("net_profit", "")?.let { asNumber(it) }
                if (latest != null && prior != null && prior != 0.0) {
                    val qGrowth = ((latest / prior) - 1.0) * 100.0
                    if (qGrowth.isFinite()) f.put("qProfit", qGrowth)
                }
            }
        }
        if (ownershipRows.isNotEmpty()) {
            f.put("shareholding", jsonRows(ownershipRows))
            val header = ownershipRows.first()
            ownershipRows.drop(1).forEach { row ->
                val label = row.firstOrNull()?.trim()?.lowercase(Locale.ROOT).orEmpty()
                val lastValue = row.drop(1).firstOrNull()
                val n = asNumber(lastValue)
                if (n != null) {
                    if (label == "promoters" || label.startsWith("promoters ")) f.put("promoter", n)
                    if (label == "public" || label.startsWith("public ")) f.put("public", n)
                    if (label.contains("pledged")) f.put("pledged", n)
                }
            }
        }
        val name = Regex("(?is)<h1[^>]*>(.*?)</h1>").find(html)?.groupValues?.get(1)?.let { cleanText(it) } ?: stockName(s)
        f.put("name", name).put("symbol", s).put("sector", stockSector(s)).put("provider", "Screener.in")
        return f
    }

    private fun screenerLoggedIn(): Boolean {
        val cookie = CookieManager.getInstance().getCookie("https://www.screener.in") ?: return false
        return cookie.split(";").any { it.trim().startsWith("sessionid=") }
    }
    private fun screenerStatus(validate: Boolean = false): JSONObject {
        val cookiePresent = screenerLoggedIn()
        var validated = false
        var httpStatus = 0
        var message = if (cookiePresent) {
            "Screener session cookie detected; server access has not yet been verified."
        } else {
            "No Screener session cookie detected. Sign in through the official login page."
        }
        if (validate) {
            try {
                val html = get("https://www.screener.in/company/INFY/")
                httpStatus = 200
                // A successful HTTP response alone is insufficient: a login/challenge page can also return 200.
                validated = html.contains("company-ratios", ignoreCase = true) &&
                    (html.contains("Current Price", ignoreCase = true) || html.contains("Market Cap", ignoreCase = true))
                message = if (validated) {
                    "Screener protected company page returned usable company data."
                } else {
                    "Screener returned HTTP 200, but expected company metrics were absent. Sign in again or use permitted CSV import."
                }
            } catch (e: Exception) {
                val match = Regex("HTTP\\s+(\\d{3})", RegexOption.IGNORE_CASE).find(e.message ?: "")
                httpStatus = match?.groupValues?.getOrNull(1)?.toIntOrNull() ?: 0
                message = when (httpStatus) {
                    401 -> "Screener returned HTTP 401. Sign in again through the official login page."
                    403 -> "Screener returned HTTP 403. The session or access policy rejected this request; re-login may not resolve it. Do not retry or bypass the restriction."
                    else -> "Screener validation failed: " + (e.message ?: "network error")
                }
            }
        }
        val result = JSONObject()
            .put("connected", cookiePresent)
            .put("loggedIn", cookiePresent)
            .put("cookieDetected", cookiePresent)
            .put("validated", validated)
            .put("requestValidated", validated)
            .put("httpStatus", if (httpStatus == 0) JSONObject.NULL else httpStatus)
            .put("status", when { validated -> "VALIDATED"; httpStatus == 403 -> "HTTP_403_FORBIDDEN"; httpStatus == 401 -> "HTTP_401_UNAUTHORIZED"; validate -> "LIVE_VALIDATION_FAILED"; else -> "SESSION_UNVERIFIED" })
            // Always expose the official login URL so a stale session can be replaced.
            .put("loginUrl", "https://www.screener.in/login/")
            .put("message", message)
        return result
    }

    private fun coreCoverage(f: JSONObject): JSONObject {
        val keys = arrayOf("marketCap", "pe", "roce", "roe", "debtEquity", "eps", "bookValue")
        var count = 0
        keys.forEach { if (f.has(it) && !f.isNull(it)) count++ }
        return JSONObject().put("coreFields", count).put("coreTotal", keys.size)
    }

    private fun combined(raw: String, includeFundamentals: Boolean): JSONObject {
        val s = canonical(raw)
        // Keep fundamentals and market data separate. Never label a third-party
        // fallback as live; use a Screener snapshot only for the displayed reference price.
        val executor = Executors.newFixedThreadPool(2)
        val quoteFuture = executor.submit<JSONObject> {
            try { screenerQuote(s) } catch (e: Exception) {
                JSONObject().put("symbol", s).put("rows", JSONArray())
                    .put("provider", "Authorized market-data feed not configured")
                    .put("marketDataStatus", "UNAVAILABLE")
                    .put("providerError", e.message ?: "Screener snapshot unavailable; authorized quote feed is not configured")
            }
        }
        val fundamentalFuture = executor.submit<JSONObject> {
            try { screener(s) } catch (e: Exception) {
                JSONObject().put("symbol", s).put("name", stockName(s)).put("providerError", e.message ?: "Screener unavailable")
            }
        }
        val deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(11)
        fun result(future: java.util.concurrent.Future<JSONObject>, fallback: JSONObject): JSONObject {
            val remaining = deadline - System.nanoTime()
            if (remaining <= 0L) return fallback
            return try { future.get(remaining, TimeUnit.NANOSECONDS) } catch (e: Exception) {
                future.cancel(true)
                fallback
            }
        }
        val quote = result(quoteFuture, JSONObject().put("symbol", s).put("rows", JSONArray()).put("provider", "Authorized market-data feed not configured").put("marketDataStatus", "UNAVAILABLE").put("providerError", "Screener snapshot timed out; authorized quote feed is not configured"))
        val f = result(fundamentalFuture, JSONObject().put("symbol", s).put("name", stockName(s)).put("providerError", "Screener.in request timed out"))
        executor.shutdownNow()

        val market = JSONObject()
        val keys = arrayOf("symbol", "resolvedSymbol", "price", "previousClose", "dayChangePct", "currency", "high52", "low52", "rows", "provider")
        keys.forEach { k -> if (quote.has(k)) market.put(k, quote.get(k)) }
        if (includeFundamentals) {
            val iter = f.keys()
            while (iter.hasNext()) {
                val k = iter.next()
                // Keep live Yahoo CMP when available; otherwise use Screener's displayed price.
                if (k != "providerError" && !(k == "price" && quote.has("price"))) market.put(k, f.get(k))
            }
        }
        val rows = quote.optJSONArray("rows") ?: JSONArray()
        val history = JSONObject().put("rows", rows).put("provider", quote.optString("provider", "Yahoo Finance"))
        val hasFundamentals = arrayOf("marketCap", "pe", "roce", "roe", "debtEquity", "eps", "bookValue").any { f.has(it) && !f.isNull(it) }
        val data = JSONObject().put("symbol", s).put("name", f.optString("name", stockName(s)))
            .put("quote", quote).put("market", market).put("fundamentals", f).put("history", history)
            .put("ohlcv", rows).put("technicalSeries", rows)
            .put("dataConfidence", when { quote.has("price") && hasFundamentals -> "PARTIAL"; quote.has("price") -> "LIVE QUOTE"; hasFundamentals -> "FUNDAMENTALS ONLY"; else -> "UNAVAILABLE" })
            .put("dataSources", JSONObject().put("Live Quote", if (quote.has("providerError")) "UNAVAILABLE" else quote.optString("provider", "Yahoo Finance"))
                .put("Screener.in", if (f.has("providerError")) "UNAVAILABLE" else if (screenerLoggedIn()) "AUTHENTICATED APP SESSION" else "PUBLIC COMPANY PAGE"))
            .put("fundamentalCoverage", coreCoverage(f))
        val warnings = JSONArray()
        if (quote.has("providerError")) warnings.put(quote.optString("providerError"))
        if (f.has("providerError")) warnings.put(f.optString("providerError"))
        if (warnings.length() > 0) data.put("providerWarnings", warnings)
        return data
    }

    private fun historyData(raw: String, range: String): JSONObject {
        // Do not fabricate candles or silently substitute an unapproved third-party feed.
        // Screener company pages provide fundamentals/snapshot metrics, not a licensed OHLCV feed.
        return JSONObject().put("symbol", canonical(raw)).put("rows", JSONArray())
            .put("provider", "Authorized market-data feed not configured")
            .put("providerError", "Historical candles are unavailable until an authorized market-data provider is configured.")
            .put("chartMode", "UNAVAILABLE").put("requestedRange", range)
            .put("marketDataStatus", "UNAVAILABLE")
    }
    private fun screenerQuote(raw: String): JSONObject {
        val symbol = canonical(raw)
        val f = screener(symbol)
        val q = JSONObject().put("symbol", symbol).put("resolvedSymbol", symbol)
            .put("name", f.optString("name", stockName(symbol)))
            .put("provider", "Screener.in company-page snapshot (not real-time)")
            .put("marketDataStatus", "SNAPSHOT_NOT_REALTIME")
            .put("rows", JSONArray())
            .put("asOf", JSONObject.NULL)
            .put("providerError", "Screener company-page price is a snapshot, not a verified live quote. Authorized quote feed is not configured.")
        if (f.has("price") && !f.isNull("price")) q.put("price", f.get("price"))
        if (f.has("previousClose") && !f.isNull("previousClose")) q.put("previousClose", f.get("previousClose"))
        if (f.has("dayChangePct") && !f.isNull("dayChangePct")) q.put("dayChangePct", f.get("dayChangePct"))
        return q
    }

    private fun htmlEntities(s: String): String = s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<")
        .replace("&gt;", ">").replace("&quot;", "\"").replace("&#39;", "'").replace(Regex("\\s+"), " ").trim()

    private fun runScreenerQuery(query: String): JSONObject {
        if (!screenerLoggedIn()) throw IOException("Screener login is not active. Tap Screener Login, sign in, return to the app, then run the scan again.")
        val url = "https://www.screener.in/screen/raw/?query=" + URLEncoder.encode(query, "UTF-8")
        val html = get(url)
        val table = Regex("(?is)<table[^>]*>(.*?)</table>").find(html)?.groupValues?.get(1)
            ?: throw IOException("Screener returned no results table. Confirm login and try again.")
        val rowsHtml = Regex("(?is)<tr[^>]*>(.*?)</tr>").findAll(table).map { it.groupValues[1] }.toList()
        val columns = JSONArray()
        val resultRows = JSONArray()
        var count = 0
        rowsHtml.forEachIndexed { index, rowHtml ->
            val cells = Regex("(?is)<t[hd][^>]*>(.*?)</t[hd]>").findAll(rowHtml).map { htmlEntities(cleanText(it.groupValues[1])) }.toList()
            if (cells.isEmpty()) return@forEachIndexed
            if (index == 0 && Regex("(?is)<th").containsMatchIn(rowHtml)) { cells.forEach { columns.put(it) }; return@forEachIndexed }
            if (columns.length() == 0) return@forEachIndexed
            val obj = JSONObject()
            cells.forEachIndexed { i, cell -> if (i < columns.length()) obj.put(columns.getString(i), cell) }
            if (obj.length() > 0) { count++; if (!obj.has("S.No.")) obj.put("S.No.", count); resultRows.put(obj) }
        }
        return JSONObject().put("columns", columns).put("rows", resultRows).put("count", count)
            .put("provider", "Screener.in authenticated session").put("pagesFetched", 1).put("allResultsLoaded", false)
            .put("statusText", "Parsed first available Screener results table; pagination may be partial.")
    }

    private fun technicalScan(kind: String): JSONObject {
        val executor = Executors.newFixedThreadPool(8)
        val completion = java.util.concurrent.ExecutorCompletionService<JSONObject>(executor)
        val submittedAt = System.nanoTime()
        val jobs: List<java.util.concurrent.Future<JSONObject>> = stocks.map { stock -> completion.submit<JSONObject> {
            val y = yahoo(stock.symbol, "1y")
            val arr = y.optJSONArray("rows") ?: JSONArray()
            val closes = (0 until arr.length()).mapNotNull { i ->
                val v = arr.optJSONObject(i)?.optDouble("close", Double.NaN) ?: Double.NaN
                if (finite(v) && v > 0) v else null
            }
            val out = JSONObject().put("symbol", stock.symbol).put("Company", stock.name)
            if (closes.size >= 2) {
                val last = closes.last(); val prev = closes[closes.lastIndex - 1]
                val change = (last / prev - 1.0) * 100.0
                putFinite(out, "CMP Rs.", last); putFinite(out, "Day Change %", change)
                if (closes.size >= 15) {
                    // Wilder RSI(14), aligned with the dashboard chart calculation.
                    var avgGain = 0.0; var avgLoss = 0.0
                    for (i in 1..14) { val delta = closes[i] - closes[i - 1]; avgGain += maxOf(delta, 0.0); avgLoss += maxOf(-delta, 0.0) }
                    avgGain /= 14.0; avgLoss /= 14.0
                    for (i in 15 until closes.size) { val delta = closes[i] - closes[i - 1]; avgGain = (avgGain * 13.0 + maxOf(delta, 0.0)) / 14.0; avgLoss = (avgLoss * 13.0 + maxOf(-delta, 0.0)) / 14.0 }
                    val rsi = when { avgLoss == 0.0 && avgGain > 0 -> 100.0; avgLoss == 0.0 -> 50.0; else -> 100.0 - (100.0 / (1.0 + avgGain / avgLoss)) }
                    putFinite(out, "RSI(14)", rsi)
                }
                out.put("Data Date", java.text.SimpleDateFormat("dd MMM yyyy", Locale.ENGLISH).format(java.util.Date(arr.getJSONObject(arr.length()-1).optLong("time", 0L))))
                out.put("Provider", "Yahoo Finance third-party daily-bar data; latest bar may be partial during market hours")
            }
            out
        } }
        val found = mutableListOf<JSONObject>()
        var completed = 0
        try {
            while (completed < jobs.size && (System.nanoTime() - submittedAt) < TimeUnit.SECONDS.toNanos(24)) {
                val future = completion.poll(250, TimeUnit.MILLISECONDS) ?: continue
                completed++
                try {
                    val row = future.get()
                    val hasPrice = row.has("CMP Rs.")
                    if (!hasPrice) continue
                    val match = if (kind == "oversold") row.optDouble("RSI(14)", Double.NaN).let { finite(it) && it <= 30.0 }
                        else row.optDouble("Day Change %", Double.NaN).let { finite(it) && it <= -5.0 }
                    if (match) found.add(row)
                } catch (_: Exception) { }
            }
        } finally { jobs.forEach { it.cancel(true) }; executor.shutdownNow() }
        found.sortBy { if (kind == "oversold") it.optDouble("RSI(14)", 100.0) else it.optDouble("Day Change %", 0.0) }
        val rows = JSONArray().apply { found.forEachIndexed { i, row -> row.put("S.No.", i + 1); put(row) } }
        val columns = JSONArray(listOf("S.No.", "Company", "CMP Rs.", "RSI(14)", "Day Change %", "Data Date", "Provider"))
        val elapsed = TimeUnit.NANOSECONDS.toSeconds(System.nanoTime() - submittedAt)
        val criteria = if (kind == "oversold") "RSI(14) ≤ 30" else "latest daily-bar change ≤ -5%"
        return JSONObject().put("columns", columns).put("rows", rows).put("count", rows.length())
            .put("provider", "Yahoo Finance third-party daily data").put("pagesFetched", 1).put("allResultsLoaded", completed == jobs.size)
            .put("scanUniverse", stocks.size).put("symbolsChecked", completed).put("elapsedSeconds", elapsed)
            .put("statusText", "$criteria; $completed/${stocks.size} tracked symbols checked. Daily-bar data can be delayed or partial during market hours; this is not a whole-market scan.")
    }

    private fun yahooNews(raw: String): JSONObject {
        val symbol = canonical(raw)
        val q = URLEncoder.encode(symbol, "UTF-8")
        val root = JSONObject(get("https://query1.finance.yahoo.com/v1/finance/search?q=$q&quotesCount=0&newsCount=12"))
        val items = root.optJSONArray("news") ?: JSONArray()
        val out = JSONArray()
        for (i in 0 until items.length()) {
            val n = items.optJSONObject(i) ?: continue
            val title = n.optString("title", "").trim()
            if (title.isBlank()) continue
            val item = JSONObject().put("title", title).put("publisher", n.optString("publisher", "Yahoo Finance"))
                .put("link", n.optString("link", "")).put("time", n.optLong("providerPublishTime", 0L))
                .put("provider", "Yahoo Finance")
            out.put(item)
        }
        return JSONObject().put("symbol", symbol).put("news", out).put("provider", "Yahoo Finance")
            .put("statusText", if (out.length() > 0) "Latest available company news" else "No news returned by Yahoo Finance")
    }

    private fun marketIndices(): JSONObject {
        // No unlicensed third-party fallback: the ribbon must not imply that
        // cached/reference values are live market prices.
        val labels = listOf(
            "NIFTY 50", "SENSEX", "NIFTY BANK", "NIFTY MIDCAP 100",
            "NIFTY SMALLCAP 100", "NIFTY IT", "NIFTY AUTO", "NIFTY FMCG",
            "NIFTY PHARMA", "NIFTY METAL", "NIFTY PSU BANK", "NIFTY PRIVATE BANK",
            "NIFTY ENERGY", "NIFTY INFRA", "NIFTY FIN SERVICE",
            "GOLD (MCX)", "SILVER (MCX)", "BRENT CRUDE"
        )
        val out = JSONObject()
        labels.forEach { label ->
            out.put(label, JSONObject()
                .put("value", JSONObject.NULL)
                .put("changePct", JSONObject.NULL)
                .put("status", "UNAVAILABLE")
                .put("message", "Authorized live market-data feed is not configured"))
        }
        return out
    }

    fun handle(path: String): String {
        val p = path.substringBefore("?")
        val q = parseQuery(path)
        val raw = q["symbol"] ?: q["q"] ?: "INFY"
        val s = canonical(raw)
        return try {
            when (p) {
                "/api/health" -> JSONObject().put("ok", true).put("engine", "V40.52 ANDROID MOBILE DATA + UI SMOKE TESTS + PEER INDICATORS + TECHNICAL SCANNERS").put("data", JSONObject().put("ok", true)).toString()
                "/api/screener/status" -> JSONObject().put("ok", true).put("data", screenerStatus()).toString()
                "/api/screener/connect" -> JSONObject().put("ok", true).put("data", screenerStatus(validate = true)).toString()
                "/api/screener/disconnect" -> JSONObject().put("ok", true).put("data", JSONObject().put("connected", false).put("loggedIn", false).put("message", "Sign out from Screener inside the web page to end the session.")).toString()
                "/api/search-suggestions" -> {
                    val term = (q["q"] ?: "").uppercase(Locale.ROOT).replace(Regex("[^A-Z0-9]"), "")
                    val matches = stocks.filter { term.isBlank() || it.symbol.contains(term) || it.name.uppercase(Locale.ROOT).replace(Regex("[^A-Z0-9]"), "").contains(term) || (term.contains("INFOSYS") && it.symbol == "INFY") }
                        .take(12).map { JSONObject().put("symbol", it.symbol).put("name", it.name).put("exchange", "NSE").put("sector", it.sector) }
                    val arr = JSONArray(); matches.forEach { arr.put(it) }
                    JSONObject().put("ok", true).put("data", arr).toString()
                }
                "/api/quote", "/api/fast" -> {
                    val q = screenerQuote(s)
                    val data = JSONObject().put("symbol", s).put("name", q.optString("name", stockName(s)))
                        .put("quote", q).put("provider", q.optString("provider"))
                        .put("marketDataStatus", q.optString("marketDataStatus"))
                        .put("rows", JSONArray())
                    JSONObject().put("ok", true).put("data", data).toString()
                }
                "/api/history", "/api/screener-chart" -> JSONObject().put("ok", true).put("data", historyData(s, q["range"] ?: "1y")).toString()
                "/api/analyze", "/api/bootstrap" -> {
                    val data = combined(raw, true)
                    if (p == "/api/bootstrap") data.put("diagnostics", JSONObject().put("quoteProvider", "Screener snapshot only; live quote feed not configured").put("fundamentalProvider", if (data.optJSONObject("fundamentals")?.has("providerError") == true) "Unavailable" else "Screener.in"))
                    JSONObject().put("ok", true).put("data", data).toString()
                }
                "/api/screener/live" -> {
                    if (!screenerLoggedIn()) throw IOException("Screener login is not active. Tap Screener Login first.")
                    val f = screener(s); val q = screenerQuote(s)
                    JSONObject().put("ok", true).put("data", JSONObject().put("symbol", s)
                        .put("name", f.optString("name", stockName(s))).put("quote", q)
                        .put("fundamentals", f).put("dataConfidence", "SCREENER_SESSION_ONLY")
                        .put("marketDataStatus", "SNAPSHOT_NOT_REALTIME")).toString()
                }
                "/api/indices" -> JSONObject().put("ok", true).put("data", marketIndices()).toString()
                "/api/queries" -> JSONObject().put("ok", true).put("data", JSONArray().apply { queryDefs.forEach { put(it) } }).toString()
                "/api/screen/query", "/api/screen/querytext" -> {
                    val kind = q["kind"] ?: "master"
                    val query = if (p.endsWith("querytext")) q["query"] ?: "" else queryDefs.firstOrNull { it.optString("id") == kind }?.optString("query") ?: throw IOException("Unknown saved query")
                    val data = if (!p.endsWith("querytext") && (kind == "oversold" || kind == "crash")) technicalScan(kind) else runScreenerQuery(query)
                    data.put("queryId", if (p.endsWith("querytext")) "custom" else kind).put("queryName", if (p.endsWith("querytext")) "Custom Live Query" else queryDefs.firstOrNull { it.optString("id") == kind }?.optString("name", "Live Screener Query") ?: "Live Screener Query")
                    JSONObject().put("ok", true).put("data", data).toString()
                }
                "/api/resolve-stock" -> JSONObject().put("ok", true).put("data", JSONObject().put("symbol", s).put("name", stockName(s)).put("sector", stockSector(s))).toString()
                "/api/peers" -> {
                    val candidates = mapOf(
                        "TCS" to listOf("INFY", "HCLTECH", "WIPRO", "TECHM", "LTIM"),
                        "INFY" to listOf("TCS", "HCLTECH", "WIPRO", "TECHM", "LTIM"),
                        "HCLTECH" to listOf("TCS", "INFY", "WIPRO", "TECHM", "LTIM"),
                        "WIPRO" to listOf("TCS", "INFY", "HCLTECH", "TECHM", "LTIM"),
                        "TECHM" to listOf("TCS", "INFY", "HCLTECH", "WIPRO", "LTIM"),
                        "RELIANCE" to listOf("ONGC", "IOC", "BPCL", "ADANIENT", "COALINDIA"),
                        "HDFCBANK" to listOf("ICICIBANK", "KOTAKBANK", "AXISBANK", "SBIN", "INDUSINDBK"),
                        "ICICIBANK" to listOf("HDFCBANK", "KOTAKBANK", "AXISBANK", "SBIN", "INDUSINDBK"),
                        "ITC" to listOf("HINDUNILVR", "NESTLEIND", "BRITANNIA", "DABUR", "MARICO"),
                        "SUNPHARMA" to listOf("CIPLA", "DRREDDY", "DIVISLAB", "TORNTPHARM", "LUPIN"),
                        "MARUTI" to listOf("M&M", "TATAMOTORS", "HEROMOTOCO", "EICHERMOT", "BAJAJ-AUTO")
                    )
                    val names = candidates[s] ?: emptyList()
                    val executor = Executors.newFixedThreadPool(4)
                    val tasks = names.map { symbol -> executor.submit<JSONObject?> {
                        try {
                            val f = screener(symbol)
                            val y = yahoo(symbol, "1y")
                            val rows = y.optJSONArray("rows") ?: JSONArray()
                            val closes = (0 until rows.length()).mapNotNull { i -> rows.optJSONObject(i)?.optDouble("close", Double.NaN)?.takeIf { finite(it) && it > 0 } }
                            if (closes.isEmpty()) return@submit null
                            val item = JSONObject().put("symbol", symbol).put("name", f.optString("name", stockName(symbol)))
                                .put("sector", f.optString("sector", stockSector(symbol))).put("dataStatus", "PARTIAL_PROVIDER_VALIDATED")
                                .put("provider", "Screener.in fundamentals + Yahoo Finance price history")
                            putFinite(item, "price", y.optDouble("price", closes.last()))
                            putFinite(item, "marketCap", f.optDouble("marketCap", Double.NaN))
                            putFinite(item, "pe", f.optDouble("pe", Double.NaN))
                            putFinite(item, "roce", f.optDouble("roce", Double.NaN))
                            putFinite(item, "roe", f.optDouble("roe", Double.NaN))
                            putFinite(item, "qProfit", f.optDouble("qProfit", Double.NaN))
                            putFinite(item, "high52", y.optDouble("high52", Double.NaN))
                            putFinite(item, "low52", y.optDouble("low52", Double.NaN))
                            // Peer trend metrics need daily history, not the five-day quote window.
                            if (closes.size >= 50) putFinite(item, "dma50", closes.takeLast(50).average())
                            if (closes.size >= 200) putFinite(item, "dma200", closes.takeLast(200).average())
                            if (closes.size >= 15) {
                                var avgGain = 0.0; var avgLoss = 0.0
                                for (i in 1..14) { val d = closes[i] - closes[i - 1]; avgGain += maxOf(d, 0.0); avgLoss += maxOf(-d, 0.0) }
                                avgGain /= 14.0; avgLoss /= 14.0
                                for (i in 15 until closes.size) {
                                    val d = closes[i] - closes[i - 1]
                                    avgGain = (avgGain * 13.0 + maxOf(d, 0.0)) / 14.0
                                    avgLoss = (avgLoss * 13.0 + maxOf(-d, 0.0)) / 14.0
                                }
                                putFinite(item, "rsi14", when { avgLoss == 0.0 && avgGain > 0 -> 100.0; avgLoss == 0.0 -> 50.0; else -> 100.0 - 100.0 / (1.0 + avgGain / avgLoss) })
                            }
                            // Require at least a price and two independent fundamental fields; otherwise do not present the row as validated.
                            val core = listOf("marketCap", "pe", "roce", "roe").count { item.has(it) && !item.isNull(it) }
                            if (core < 2) null else item
                        } catch (_: Exception) { null }
                    } }
                    val peers = JSONArray()
                    try {
                        tasks.forEach { task ->
                            try {
                                val item = task.get(7, TimeUnit.SECONDS)
                                if (item != null) peers.put(item)
                            } catch (_: Exception) { }
                        }
                    } finally {
                        tasks.forEach { it.cancel(true) }
                        executor.shutdownNow()
                    }
                    JSONObject().put("ok", true).put("data", JSONObject().put("symbol", s).put("industry", stockSector(s)).put("peers", peers)
                        .put("candidateCount", names.size).put("validatedCount", peers.length())
                        .put("method", "Curated same-industry candidates; returned rows require live price history and at least two available fundamental fields. This validates data presence, not an exchange-certified industry classification.")
                        .put("partial", peers.length() < names.size).put("statusText", "${peers.length()}/${names.size} peer candidates passed live data-completeness checks. Missing metrics are left blank; candidates are not a fully validated industry universe.")).toString()
                }
                "/api/news" -> {
                    val news = try { yahooNews(raw) } catch (e: Exception) { JSONObject().put("symbol", s).put("news", JSONArray()).put("statusText", "Yahoo Finance news unavailable: ${e.message ?: "provider error"}").put("provider", "Unavailable") }
                    JSONObject().put("ok", true).put("data", news).toString()
                }
                "/api/company-events" -> {
                    val y = try { yahoo(raw, "5y") } catch (e: Exception) { JSONObject().put("symbol", s).put("rows", JSONArray()).put("statusText", "Corporate event provider unavailable: ${e.message ?: "provider error"}").put("provider", "Unavailable") }
                    val events = y.optJSONArray("events") ?: JSONArray()
                    JSONObject().put("ok", true).put("data", JSONObject().put("symbol", s).put("name", stockName(s)).put("rows", events).put("statusText", if (events.length() > 0) "Verified dividend and split events from Yahoo Finance" else "No dividend or split events returned by Yahoo Finance").put("provider", y.optString("provider", "Yahoo Finance"))).toString()
                }
                "/api/dividend-stocks" -> {
                    val d = runScreenerQuery("Market Capitalization > 1000 AND Dividend yield > 1 AND Return on capital employed > 10")
                    val rows = d.optJSONArray("rows") ?: JSONArray()
                    JSONObject().put("ok", true).put("data", JSONObject().put("rows", rows).put("statusText", "Authenticated Screener dividend-yield candidate screen; first result page only.").put("provider", d.optString("provider", "Screener.in")).put("partial", true)).toString()
                }
                "/api/upcoming-events" -> JSONObject().put("ok", true).put("data", JSONObject().put("rows", JSONArray())
                    .put("statusText", "Live calendar data is not embedded because NSE's page is dynamically served and this standalone app has no authorized, stable calendar feed. Open the official NSE event calendar to verify current dates; no events are fabricated.")
                    .put("provider", "NSE official calendar link").put("officialUrl", "https://www.nseindia.com/companies-listing/corporate-filings-event-calendar")
                    .put("resultsUrl", "https://www.nseindia.com/companies-listing/corporate-filings-financial-results").put("liveData", false)).toString()
                "/api/upcoming-results" -> JSONObject().put("ok", true).put("data", JSONObject().put("rows", JSONArray())
                    .put("sourcesChecked", JSONArray().put("NSE official event calendar URL configured; live extraction not enabled"))
                    .put("providerErrors", JSONArray().put("Standalone client cannot guarantee stable, authorized NSE calendar extraction"))
                    .put("statusText", "No dates are inferred. Use the official NSE event calendar for announced board-meeting/result dates and the financial-results filings page for submitted results.")
                    .put("officialUrl", "https://www.nseindia.com/companies-listing/corporate-filings-event-calendar")
                    .put("resultsUrl", "https://www.nseindia.com/companies-listing/corporate-filings-financial-results").put("liveData", false)).toString()
                "/api/cache-clear" -> JSONObject().put("ok", true).put("data", JSONObject().put("cleared", true)).toString()
                else -> JSONObject().put("ok", false).put("error", "Mobile API endpoint not implemented: $p").toString()
            }
        } catch (e: Exception) {
            JSONObject().put("ok", false).put("error", e.message ?: "Verified data provider unavailable").toString()
        }
    }
}

private object URLDecoderCompat {
    fun decode(s: String): String = try { java.net.URLDecoder.decode(s, "UTF-8") } catch (_: Exception) { s }
}
