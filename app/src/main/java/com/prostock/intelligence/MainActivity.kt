package com.prostock.intelligence

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.webkit.*
import android.net.Uri
import android.util.Log
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
    private var filePathCallback: ValueCallback<Array<Uri>>? = null
    private val csvPickerRequestCode = 4071
    private val provider = NativeProvider()

    private fun jsonResponse(json: String): WebResourceResponse =
        WebResourceResponse("application/json", "UTF-8", ByteArrayInputStream(json.toByteArray(Charsets.UTF_8))).apply {
            responseHeaders = mapOf("Cache-Control" to "no-store, max-age=0", "Pragma" to "no-cache", "X-Content-Type-Options" to "nosniff", "Access-Control-Allow-Origin" to "https://appassets.androidplatform.net")
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        CookieManager.getInstance().setAcceptCookie(true)
        web = WebView(this)
        web.setBackgroundColor(Color.rgb(237, 245, 251))
        web.settings.javaScriptEnabled = true
        web.settings.javaScriptCanOpenWindowsAutomatically = false
        web.settings.safeBrowsingEnabled = true
        web.settings.domStorageEnabled = true
        web.settings.databaseEnabled = true
        web.settings.allowFileAccess = false
        web.settings.allowContentAccess = false
        web.settings.mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
        web.settings.setSupportMultipleWindows(false)
        CookieManager.getInstance().setAcceptThirdPartyCookies(web, false)

        val assetLoader = WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()
        web.webChromeClient = object : WebChromeClient() {
            override fun onShowFileChooser(webView: WebView, callback: ValueCallback<Array<Uri>>, fileChooserParams: FileChooserParams): Boolean {
                filePathCallback?.onReceiveValue(null)
                filePathCallback = callback
                return try {
                    val pick = Intent(Intent.ACTION_GET_CONTENT).apply {
                        addCategory(Intent.CATEGORY_OPENABLE)
                        type = "*/*"
                        putExtra(Intent.EXTRA_MIME_TYPES, arrayOf("text/csv", "text/comma-separated-values", "text/plain", "application/vnd.ms-excel", "application/octet-stream"))
                    }
                    startActivityForResult(Intent.createChooser(pick, "Select authorized CSV export"), csvPickerRequestCode)
                    true
                } catch (e: Exception) {
                    filePathCallback?.onReceiveValue(null)
                    filePathCallback = null
                    Log.e("PSI_FILE_PICKER", "Unable to open CSV picker", e)
                    false
                }
            }
            override fun onConsoleMessage(message: ConsoleMessage): Boolean {
                if (message.messageLevel() == ConsoleMessage.MessageLevel.ERROR) {
                    Log.e("PSI_WEB", "${message.message()} (${message.sourceId()}:${message.lineNumber()})")
                }
                return true
            }
        }
        web.webViewClient = object : WebViewClientCompat() {
            private fun isAllowedInApp(uri: Uri): Boolean {
                if (!uri.scheme.equals("https", ignoreCase = true)) return false
                val host = (uri.host ?: "").lowercase(Locale.ROOT)
                return host == "appassets.androidplatform.net" || host == "screener.in" || host.endsWith(".screener.in")
            }
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val uri = request.url
                if (isAllowedInApp(uri)) return false
                // Never let untrusted pages, javascript:, file:, content:, or cleartext URLs
                // take over the app WebView. Ordinary external HTTPS links open in the browser.
                if (uri.scheme.equals("https", ignoreCase = true)) {
                    return try { startActivity(Intent(Intent.ACTION_VIEW, uri)); true }
                    catch (_: Exception) { true }
                }
                return true
            }
            @Suppress("DEPRECATION")
            override fun shouldOverrideUrlLoading(view: WebView, url: String): Boolean {
                val uri = Uri.parse(url)
                if (isAllowedInApp(uri)) return false
                if (uri.scheme.equals("https", ignoreCase = true)) {
                    return try { startActivity(Intent(Intent.ACTION_VIEW, uri)); true }
                    catch (_: Exception) { true }
                }
                return true
            }
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
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        if (requestCode == csvPickerRequestCode) {
            val callback = filePathCallback
            filePathCallback = null
            callback?.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(resultCode, data))
            return
        }
        super.onActivityResult(requestCode, resultCode, data)
    }

    override fun onDestroy() {
        filePathCallback?.onReceiveValue(null)
        filePathCallback = null
        if (::web.isInitialized) {
            web.stopLoading()
            web.webViewClient = WebViewClient()
            web.destroy()
        }
        super.onDestroy()
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
    ).apply { responseHeaders = mapOf("Cache-Control" to "no-store, max-age=0", "Pragma" to "no-cache", "X-Content-Type-Options" to "nosniff", "Access-Control-Allow-Origin" to "https://appassets.androidplatform.net") }

    private fun parseQuery(path: String): Map<String, String> = path.substringAfter("?", "").split("&").mapNotNull {
        val a = it.split("=", limit = 2)
        if (a.size == 2) URLDecoderCompat.decode(a[0]) to URLDecoderCompat.decode(a[1]) else null
    }.toMap()

    private fun cleanText(s: String): String = s.replace(Regex("(?is)<script.*?</script>|<style.*?</style>"), " ")
        .replace(Regex("(?s)<[^>]+>"), " ").replace("&nbsp;", " ").replace("&amp;", "&")
        .replace("&#39;", "'").replace("&quot;", "\"").replace(Regex("\\s+"), " ").trim()

    private fun canonical(raw: String): String {
        val upper = raw.trim().uppercase(Locale.ROOT)
        // Preserve Yahoo's exchange-index and futures ticker syntax. Stripping punctuation here
        // used to turn ^NSEI into NSEI and GC=F into GCF, silently breaking every index/futures quote.
        if (upper.matches(Regex("^\\^[A-Z0-9]+$")) || upper.matches(Regex("^[A-Z]{1,5}=F$"))) return upper
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
            // WebView may store host-only and parent-domain cookies differently.
            val manager = CookieManager.getInstance()
            val cookieParts = listOf(
                manager.getCookie("https://www.screener.in"),
                manager.getCookie("https://screener.in")
            ).filterNotNull().flatMap { it.split(";") }
                .map { it.trim() }.filter { it.contains("=") && !it.startsWith("=") }
                .distinctBy { it.substringBefore("=") }
            if (cookieParts.isNotEmpty()) c.setRequestProperty("Cookie", cookieParts.joinToString("; "))
        }
        try {
            val code = c.responseCode
            val stream = if (code in 200..299) c.inputStream else c.errorStream
            val body = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() } ?: ""
            if (code !in 200..299) throw IOException("HTTP $code from $host${if (body.isNotBlank()) ": ${body.take(120)}" else ""}")
            return body
        } finally { c.disconnect() }
    }

    /**
     * Attach explicit quote timestamp quality without pretending receipt time is quote time.
     * This is a diagnostic label only; it cannot establish exchange licensing or real-time rights.
     */
    private fun annotateQuoteQuality(quote: JSONObject): JSONObject {
        val timestamp = when {
            quote.has("quoteTimestamp") && !quote.isNull("quoteTimestamp") -> quote.optLong("quoteTimestamp", 0L)
            quote.has("priceTimestamp") && !quote.isNull("priceTimestamp") -> quote.optLong("priceTimestamp", 0L)
            else -> 0L
        }
        val now = System.currentTimeMillis() / 1000L
        val age = if (timestamp > 0L) now - timestamp else -1L
        val status = when {
            timestamp <= 0L -> "UNVERIFIED_NO_PROVIDER_QUOTE_TIMESTAMP"
            age < -60L -> "INVALID_FUTURE_TIMESTAMP"
            age < 0L -> "FUTURE_TIMESTAMP_WITHIN_60S_CLOCK_SKEW"
            age <= 300L -> "TIMESTAMP_WITHIN_5_MINUTES_NOT_A_REALTIME_GUARANTEE"
            else -> "TIMESTAMP_OLDER_THAN_5_MINUTES_OR_MARKET_CLOSED"
        }
        quote.put("quoteTimestampStatus", status)
        quote.put("quoteTimestampSource", if (timestamp > 0L) "provider_quote_timestamp" else "missing_not_inferred_from_response_time")
        if (timestamp > 0L) quote.put("quoteAgeSeconds", age)
        val price = quote.optDouble("price", Double.NaN)
        quote.put("priceValueValid", finite(price) && price > 0.0)
        if (!finite(price) || price <= 0.0) quote.put("quoteQuality", "NO_VALID_PRICE")
        else quote.put("quoteQuality", if (timestamp <= 0L || age > 300L || age < -60L) "PRICE_REQUIRES_SOURCE/TIMESTAMP_VERIFICATION" else "TIMESTAMP_RECENT_PROVIDER_NOT_EXCHANGE_CERTIFIED")
        return quote
    }

    private fun finite(n: Double): Boolean = !n.isNaN() && !n.isInfinite()
    private fun putFinite(o: JSONObject, key: String, n: Double) { if (finite(n)) o.put(key, n) }

    /**
     * Best-effort quote adapter for the official NSE website endpoint. This is not a licensed
     * real-time feed; NSE may rate-limit/block it or change its schema. A successful response
     * is explicitly labelled with provider + timestamp and is never described as guaranteed live.
     */
    /**
     * V40.79 policy: do not scrape NSE's public website endpoint.
     * The public website is not a documented, authorized real-time API contract.
     * Enable quotes only after an authorized NSE/vendor feed is configured.
     */
    private fun nseQuote(raw: String): JSONObject {
        val symbol = canonical(raw)
        if (symbol.isBlank()) throw IOException("Enter a valid NSE equity symbol")
        throw IOException("NSE live quotes are blocked: this installation has no authorized NSE real-time API/feed configured. Public website scraping is disabled; no price was fabricated.")
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

    /**
     * Parse a single numeric financial value without silently accepting a numeric
     * substring from malformed text. Units are intentionally not converted here:
     * callers must know the field's expected unit before applying any conversion.
     */
    private fun asNumber(raw: String?): Double? {
        if (raw.isNullOrBlank()) return null
        val input = raw.trim().replace('−', '-')
        if (input in setOf("—", "–", "-", "N/A", "NA", "NULL", "null", "--")) return null
        val parenthesizedNegative = input.startsWith("(") && input.endsWith(")")
        var normalized = if (parenthesizedNegative) input.substring(1, input.length - 1).trim() else input
        normalized = normalized
            .replace(",", "")
            .replace("₹", "")
            .replace("%", "")
            .replace(Regex("(?i)\\b(?:cr\\.?|rs\\.?)"), "")
            .replace(Regex("\\s+"), "")
        if (!Regex("^[+-]?(?:[0-9]+(?:\\.[0-9]*)?|\\.[0-9]+)$").matches(normalized)) return null
        val parsed = normalized.toDoubleOrNull() ?: return null
        if (!parsed.isFinite()) return null
        return if (parenthesizedNegative) -kotlin.math.abs(parsed) else parsed
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
        val pageUrl = "https://www.screener.in/company/${Uri.encode(s)}/"
        val html = get(pageUrl)
        val pageTitle = Regex("(?is)<h1\\b[^>]*>(.*?)</h1>").find(html)?.groupValues?.get(1)?.let { cleanText(it) }
        val hasRatioSection = Regex("(?is)<(?:section|div)\\b[^>]*id=[\"']top-ratios[\"']").containsMatchIn(html)
        // Restrict ratio matching to the dedicated section to avoid duplicate labels
        // elsewhere in the page being treated as ambiguous.
        val ratiosSectionHtml = Regex("(?is)<section\\b[^>]*id=[\"']top-ratios[\"'][^>]*>(.*?)</section>")
            .find(html)?.groupValues?.get(1) ?: html
        val looksLikeLogin = Regex("(?is)<title[^>]*>.*?(?:login|sign in).*?</title>").containsMatchIn(html) ||
            html.contains("name=\"password\"", ignoreCase = true)
        if (looksLikeLogin) throw IOException("Screener returned a login page instead of company data; sign in again and retry.")
        if (pageTitle.isNullOrBlank() || !hasRatioSection) {
            throw IOException("Screener company page could not be validated for '$s' (wrong symbol, blocked page, or changed markup). No fundamentals accepted.")
        }
        // Match the visible label and value in the same ratio list item. Never guess from nearby text.
        fun number(label: String, percent: Boolean = false): Double? {
            val items = Regex("(?is)<li\\b[^>]*>(.*?)</li>").findAll(ratiosSectionHtml).map { it.groupValues[1] }
            val matches = items.mapNotNull { item ->
                val name = Regex("(?is)<span\\b[^>]*class=[\"'][^\"']*\\bname\\b[^\"']*[\"'][^>]*>(.*?)</span>")
                    .find(item)?.groupValues?.getOrNull(1)?.let { cleanText(it) } ?: return@mapNotNull null
                val normalizedName = name.lowercase(Locale.ROOT).replace(Regex("[^a-z0-9]+"), " ").trim()
                val normalizedLabel = label.lowercase(Locale.ROOT).replace(Regex("[^a-z0-9]+"), " ").trim()
                val acceptedLabels = when (normalizedLabel) {
                    "debt equity" -> setOf("debt equity", "debt to equity")
                    "eps in rs" -> setOf("eps in rs", "eps")
                    else -> setOf(normalizedLabel)
                }
                if (normalizedName !in acceptedLabels) return@mapNotNull null
                val valueHtml = Regex("(?is)<span\\b[^>]*class=[\"'][^\"']*\\bnumber\\b[^\"']*[\"'][^>]*>(.*?)</span>")
                    .find(item)?.groupValues?.getOrNull(1)
                valueHtml?.let { asNumber(cleanText(it)) }
            }.distinct()
            // If repeated labels conflict or the value cannot be parsed, leave it unavailable.
            // Use collection count here: this is a Sequence-derived List, not an array.
            if (matches.count() != 1) return null
            val parsed = matches.single()
            if ((label.equals("Current Price", true) || label.equals("Market Cap", true) || label.equals("Book Value", true) || label.equals("Stock P/E", true)) && parsed <= 0.0) return null
            return parsed
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

        // Parse all explicitly labelled metrics in Screener's top-ratios list.
        // This avoids depending on one exact label spelling across page revisions.
        val ratioItems = Regex("(?is)<li\\b[^>]*>(.*?)</li>").findAll(ratiosSectionHtml).map { it.groupValues[1] }.toList()
        fun normalizeMetricLabel(value: String): String =
            value.lowercase(Locale.ROOT).replace(Regex("[^a-z0-9]+"), " ").trim()
        val aliases = mapOf(
            "industry pe" to "industryPE", "industry p e" to "industryPE", "industry p e ratio" to "industryPE",
            "peg ratio" to "peg", "peg" to "peg",
            "face value" to "faceValue", "piotroski score" to "piotroski",
            "dma 50" to "dma50", "50 dma" to "dma50", "dma 200" to "dma200", "200 dma" to "dma200",
            "promoter holding" to "promoter", "promoters" to "promoter",
            "public holding" to "public", "public" to "public",
            "pledged percentage" to "pledged", "pledged percent" to "pledged",
            "industry pb" to "industryPB", "industry p b" to "industryPB",
            "price to book value" to "pb", "stock p b" to "pb", "p b" to "pb",
            "sales growth 3years" to "sales3y", "profit var 3yrs" to "profit3y",
            "profit growth 3years" to "profit3y", "opm" to "opm"
        )
        val parsedAliases = mutableMapOf<String, MutableList<Double>>()
        ratioItems.forEach { item ->
            val label = Regex("(?is)<span\\b[^>]*class=[\\\"'][^\\\"']*\\bname\\b[^\\\"']*[\\\"'][^>]*>(.*?)</span>")
                .find(item)?.groupValues?.getOrNull(1)?.let { cleanText(it) } ?: return@forEach
            val key = aliases[normalizeMetricLabel(label)] ?: return@forEach
            val valueHtml = Regex("(?is)<span\\b[^>]*class=[\\\"'][^\\\"']*\\bnumber\\b[^\\\"']*[\\\"'][^>]*>(.*?)</span>")
                .find(item)?.groupValues?.getOrNull(1) ?: return@forEach
            val value = asNumber(cleanText(valueHtml)) ?: return@forEach
            parsedAliases.getOrPut(key) { mutableListOf() }.add(value)
        }
        parsedAliases.forEach { (key, values) ->
            val distinct = values.distinct()
            // Conflicting duplicate labels are ambiguous; never select one arbitrarily.
            if (distinct.size == 1 && !f.has(key)) f.put(key, distinct.single())
        }

        val pnlRows = sectionTableRows(html, "profit-loss")
        val qRows = sectionTableRows(html, "quarters")
        val ownershipRows = sectionTableRows(html, "shareholding")
        val balanceRows = sectionTableRows(html, "balance-sheet")
        fun rowFor(rows: List<List<String>>, label: String): List<String>? =
            rows.drop(1).firstOrNull { row ->
                val key = row.firstOrNull()?.trim().orEmpty()
                key.equals(label, true) || key.startsWith("$label ", true) || key.startsWith("$label +", true)
            }
        fun setLatestFromTable(rows: List<List<String>>, label: String, key: String) {
            val row = rowFor(rows, label) ?: return
            val value = row.getOrNull(1)?.let { asNumber(it) }
            if (value != null) f.put(key, value)
        }
        setLatestFromTable(pnlRows, "Net Profit", "netProfit")
        // EPS is commonly present in the profit/loss table, not in the top-ratios list.
        // Prefer the explicit ratio value when present; otherwise use the latest reported EPS cell.
        if (!f.has("eps")) setLatestFromTable(pnlRows, "EPS in Rs", "eps")
        if (!f.has("eps")) setLatestFromTable(pnlRows, "EPS", "eps")
        setLatestFromTable(pnlRows, "Operating Profit", "operatingProfit")
        setLatestFromTable(pnlRows, "OPM %", "opm")
        setLatestFromTable(pnlRows, "Interest", "interestExpense")
        // Calculate 3-year CAGR only when both the oldest and latest table values are positive and present.
        fun setCagr(rows: List<List<String>>, label: String, key: String) {
            val row = rowFor(rows, label) ?: return
            // Preserve fiscal-column positions. mapNotNull would shift periods when
            // a value is blank and could silently calculate a false 3-year CAGR.
            val periods = row.drop(1).take(4).map { asNumber(it) }
            val latest = periods.getOrNull(0) ?: return
            val threeYearsBack = periods.getOrNull(3) ?: return
            if (latest > 0.0 && threeYearsBack > 0.0) {
                val cagr = (Math.pow(latest / threeYearsBack, 1.0 / 3.0) - 1.0) * 100.0
                if (cagr.isFinite()) f.put(key, cagr)
            }
        }
        setCagr(pnlRows, "Sales", "sales3y")
        setCagr(pnlRows, "Net Profit", "profit3y")
        setCagr(pnlRows, "EPS in Rs", "eps3y")
        // Derived ratios must use the newest fiscal column; never skip a blank latest cell.
        val currentAssets = rowFor(balanceRows, "Current Assets")?.getOrNull(1)?.let { asNumber(it) }
        val currentLiabilities = rowFor(balanceRows, "Current Liabilities")?.getOrNull(1)?.let { asNumber(it) }
        if (currentAssets != null && currentLiabilities != null && currentLiabilities > 0) f.put("currentRatio", currentAssets / currentLiabilities)
        val latestOperating = rowFor(pnlRows, "Operating Profit")?.getOrNull(1)?.let { asNumber(it) }
        val latestInterest = rowFor(pnlRows, "Interest")?.getOrNull(1)?.let { asNumber(it) }
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
        val fetchedAt = System.currentTimeMillis()
        val fieldKeys = listOf("price", "marketCap", "pe", "industryPE", "peg", "pb", "industryPB", "faceValue", "piotroski", "dma50", "dma200", "promoter", "public", "pledged", "bookValue", "dividendYield", "roce", "roe", "debtEquity", "eps", "netProfit", "operatingProfit", "opm", "sales3y", "profit3y", "eps3y", "currentRatio", "interestCoverage", "quarterly", "shareholding")
        val available = fieldKeys.count { f.has(it) && !f.isNull(it) }
        val qualityFlags = JSONArray()
        if (available < 6) qualityFlags.put("LOW_FUNDAMENTAL_COVERAGE")
        if (!f.has("pe")) qualityFlags.put("PE_UNAVAILABLE_OR_NON_POSITIVE")
        if (!f.has("eps")) qualityFlags.put("EPS_UNAVAILABLE")
        if (!f.has("roce")) qualityFlags.put("ROCE_UNAVAILABLE")
        f.put("name", pageTitle).put("symbol", s).put("sector", stockSector(s)).put("provider", "Screener.in")
            .put("sourceUrl", pageUrl).put("fetchedAtEpochMs", fetchedAt)
            .put("fundamentalStatus", if (available >= 6) "PAGE_VALIDATED_PARTIAL_FIELDS_MAY_BE_MISSING" else "PAGE_VALIDATED_LOW_COVERAGE")
            .put("availableFundamentalFields", available).put("expectedFundamentalFields", fieldKeys.size)
            .put("qualityFlags", qualityFlags)
        return f
    }

    private fun screenerCookieHeader(): String {
        val manager = CookieManager.getInstance()
        return listOf(
            manager.getCookie("https://www.screener.in"),
            manager.getCookie("https://screener.in")
        ).filterNotNull().flatMap { it.split(";") }
            .map { it.trim() }.filter { it.contains("=") && !it.startsWith("=") }
            .distinctBy { it.substringBefore("=") }.joinToString("; ")
    }

    private fun screenerLoggedIn(): Boolean {
        // Cookie presence is only a pre-check; protected requests still validate the session.
        return screenerCookieHeader().split(";").any {
            it.trim().substringBefore("=").equals("sessionid", ignoreCase = true) &&
                it.substringAfter("=", "").isNotBlank()
        }
    }
    private fun screenerStatus(): JSONObject {
        val active = screenerLoggedIn()
        return JSONObject().put("connected", active).put("loggedIn", active).put("validated", false)
            .put("loginUrl", if (active) JSONObject.NULL else "https://www.screener.in/login/")
            .put("message", if (active) "Screener session cookie detected. Protected company data is not confirmed until a protected request succeeds." else "Tap to sign in to Screener inside this app. After login, return with the Android Back button.")
    }

    /**
     * Report provider capabilities honestly. A public Moneycontrol page can be opened
     * without login, but no automated extraction is performed without an authorized feed.
     */
    private fun providerStatus(raw: String): JSONObject {
        val symbol = canonical(raw)
        val checkedAt = System.currentTimeMillis()
        val screenerActive = screenerLoggedIn()
        val moneycontrolUrl = "https://www.moneycontrol.com/search/?search_str=" + URLEncoder.encode(symbol, "UTF-8")
        val screener = JSONObject()
            .put("provider", "Screener.in")
            .put("mode", "Existing in-app authenticated session")
            .put("sessionCookieDetected", screenerActive)
            .put("requestValidated", false)
            .put("status", if (screenerActive) "SESSION_COOKIE_DETECTED_LIVE_PROBE_PENDING" else "LOGIN_REQUIRED")
            .put("loginRequired", true)
            .put("documentedApiConfigured", false)
            .put("message", if (screenerActive) "A session cookie exists. A live company-page request is being validated; cookie presence alone is not proof of login." else "Use the existing Screener Login button, sign in, return to the dashboard, and retry.")
        if (screenerActive) {
            val probeStarted = System.currentTimeMillis()
            try {
                val fundamentals = screener(symbol)
                val fields = JSONArray()
                val knownFields = arrayOf("price", "marketCap", "pe", "bookValue", "dividendYield", "roce", "roe", "debtEquity", "eps", "name")
                knownFields.filter { fundamentals.has(it) && !fundamentals.isNull(it) }.forEach { fields.put(it) }
                screener
                    .put("requestValidated", true)
                    .put("status", "LIVE_COMPANY_PAGE_VALIDATED")
                    .put("companyName", fundamentals.optString("name", symbol))
                    .put("validatedFieldCount", fields.length())
                    .put("validatedFields", fields)
                    .put("fetchedAtEpochMs", System.currentTimeMillis())
                    .put("validationDurationMs", System.currentTimeMillis() - probeStarted)
                    .put("sourceUrl", "https://www.screener.in/company/${Uri.encode(symbol)}/")
                    .put("message", "Live company page fetched and expected structure parsed. This validates page access and parsing, not independent accuracy of every financial value.")
            } catch (e: Exception) {
                screener
                    .put("requestValidated", false)
                    .put("status", "LIVE_VALIDATION_FAILED")
                    .put("validationDurationMs", System.currentTimeMillis() - probeStarted)
                    .put("errorType", e.javaClass.simpleName)
                    .put("message", "Live Screener request did not validate. Re-login if needed, check connectivity, and retry. No live fundamentals should be claimed from this probe.")
            }
        }
        val moneycontrol = JSONObject()
            .put("provider", "Moneycontrol")
            .put("mode", "Public website viewer + permitted user-export import")
            .put("loginRequiredForPublicViewing", false)
            .put("publicPageUrl", moneycontrolUrl)
            .put("automatedDataIntegration", "DISABLED_NO_AUTHORIZED_FEED_CONFIGURED")
            .put("dataFetched", false)
            .put("message", "Public pages can be viewed without login. Automated extraction is disabled until an authorized documented feed/API or explicit written permission is configured. Public page access is not a data feed.")
        return JSONObject()
            .put("symbol", symbol)
            .put("checkedAtEpochMs", checkedAt)
            .put("Screener.in", screener)
            .put("Moneycontrol", moneycontrol)
            .put("overall", if (screener.optBoolean("requestValidated", false)) "SCREENER_LIVE_VALIDATED_MONEYCONTROL_NOT_AUTOMATED" else "PARTIAL_PROVIDER_COVERAGE_NOT_ALL_SOURCES_LIVE")
    }

    private fun coreCoverage(f: JSONObject): JSONObject {
        val keys = arrayOf("marketCap", "pe", "roce", "roe", "debtEquity", "eps", "bookValue")
        var count = 0
        keys.forEach { if (f.has(it) && !f.isNull(it)) count++ }
        return JSONObject().put("coreFields", count).put("coreTotal", keys.size)
    }

    private fun combined(raw: String, includeFundamentals: Boolean): JSONObject {
        val s = canonical(raw)
        // Run independent providers concurrently. Yahoo failures must never prevent
        // Screener fundamentals from returning, which was a root cause of blank cards.
        val executor = Executors.newFixedThreadPool(2)
        // Quote and candle data fail closed until an authorized NSE feed is configured.
        val quoteFuture = executor.submit<JSONObject> {
            try {
                nseQuote(raw).put("rows", JSONArray())
                    .put("historyProvider", "Unavailable")
                    .put("historyStatus", "AUTHORIZED_NSE_HISTORICAL_FEED_NOT_CONFIGURED")
            } catch (e: Exception) {
                JSONObject().put("symbol", s)
                    .put("provider", "Unavailable")
                    .put("status", "AUTHORIZED_NSE_FEED_NOT_CONFIGURED")
                    .put("rows", JSONArray())
                    .put("historyProvider", "Unavailable")
                    .put("historyStatus", "AUTHORIZED_NSE_HISTORICAL_FEED_NOT_CONFIGURED")
                    .put("providerError", e.message ?: "Authorized NSE quote feed is not configured")
                    .put("marketDataDisclaimer", "No authorized NSE real-time or historical feed is configured. No third-party fallback is used.")
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
        val quote = result(quoteFuture, JSONObject().put("symbol", s).put("rows", JSONArray()).put("provider", "Unavailable").put("status", "AUTHORIZED_NSE_FEED_NOT_CONFIGURED").put("providerError", "Authorized NSE quote feed is not configured"))
        annotateQuoteQuality(quote)
        val f = result(fundamentalFuture, JSONObject().put("symbol", s).put("name", stockName(s)).put("providerError", "Screener.in request timed out"))
        executor.shutdownNow()

        val market = JSONObject()
        val keys = arrayOf("symbol", "resolvedSymbol", "price", "previousClose", "dayChangePct", "currency", "high52", "low52", "rows", "provider", "quoteTimestamp", "priceTimestamp", "quoteTimestampStatus", "quoteTimestampSource", "quoteAgeSeconds", "quoteQuality", "priceValueValid", "quoteStatus", "marketDataStatus", "marketDataDisclaimer")
        keys.forEach { k -> if (quote.has(k)) market.put(k, quote.get(k)) }
        if (includeFundamentals) {
            val iter = f.keys()
            while (iter.hasNext()) {
                val k = iter.next()
                // Never promote Screener fundamentals to an exchange quote.
                if (k != "providerError" && !(k == "price" && quote.has("price"))) market.put(k, f.get(k))
            }
        }
        val rows = quote.optJSONArray("rows") ?: JSONArray()
        val history = JSONObject().put("rows", rows).put("provider", quote.optString("historyProvider", "Unavailable")).put("historyStatus", quote.optString("historyStatus", "AUTHORIZED_NSE_HISTORICAL_FEED_NOT_CONFIGURED"))
        val hasFundamentals = arrayOf("marketCap", "pe", "roce", "roe", "debtEquity", "eps", "bookValue").any { f.has(it) && !f.isNull(it) }
        val selectedExchange = when { raw.trim().uppercase(Locale.ROOT).endsWith(".BO") -> "BSE"; raw.trim().uppercase(Locale.ROOT).endsWith(".NS") -> "NSE"; else -> "NSE primary; BSE availability varies" }
        market.put("exchange", selectedExchange)
        val data = JSONObject().put("symbol", s).put("exchange", selectedExchange).put("name", f.optString("name", stockName(s)))
            .put("quote", quote).put("market", market).put("fundamentals", f).put("history", history)
            .put("ohlcv", rows).put("technicalSeries", rows)
            .put("dataConfidence", when { quote.has("price") && hasFundamentals -> "PARTIAL — VERIFY SOURCE/TIMESTAMP"; quote.has("price") -> "QUOTE AVAILABLE — NOT GUARANTEED REAL-TIME"; hasFundamentals -> "FUNDAMENTALS ONLY"; else -> "UNAVAILABLE" })
            .put("dataSources", JSONObject().put("Quote", if (quote.has("providerError")) "UNAVAILABLE" else quote.optString("provider", "Unknown"))
                .put("History", quote.optString("historyProvider", "Unavailable"))
                .put("Moneycontrol", "NOT INTEGRATED — NO VERIFIED ACCESS/FEED CONFIGURED")
                .put("NSE", if (quote.optString("provider").startsWith("NSE")) "PUBLIC WEBSITE ENDPOINT (NOT LICENSED FEED)" else quote.optString("nseProviderWarning", "UNAVAILABLE"))
                .put("Screener.in", if (f.has("providerError")) "UNAVAILABLE: " + f.optString("providerError") else "Screener.in page parsed; field freshness/accuracy still requires verification"))
            .put("quoteQuality", quote.optString("quoteQuality", "UNVERIFIED")).put("quoteTimestampStatus", quote.optString("quoteTimestampStatus", "UNVERIFIED_NO_PROVIDER_QUOTE_TIMESTAMP")).put("fundamentalCoverage", coreCoverage(f))
        val warnings = JSONArray()
        if (quote.has("providerError")) warnings.put(quote.optString("providerError"))
        if (f.has("providerError")) warnings.put(f.optString("providerError"))
        if (warnings.length() > 0) data.put("providerWarnings", warnings)
        return data
    }

    private fun historyData(raw: String, range: String): JSONObject {
        val symbol = canonical(raw)
        return JSONObject().put("symbol", symbol).put("rows", JSONArray())
            .put("provider", "Unavailable")
            .put("historyStatus", "AUTHORIZED_NSE_HISTORICAL_FEED_NOT_CONFIGURED")
            .put("chartMode", "OHLCV")
            .put("statusText", "Historical candles are unavailable until an authorized NSE historical-data feed is configured. No third-party fallback is used.")
            .put("rangeRequested", range)
            .put("quoteTimestamp", JSONObject.NULL)
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
        return JSONObject().put("rows", JSONArray())
            .put("provider", "Unavailable")
            .put("queryId", kind)
            .put("partial", true)
            .put("statusText", "Technical scans are unavailable until an authorized NSE historical-data feed supplies verified candles. RSI, moving averages and signals are not fabricated.")
            .put("historyStatus", "AUTHORIZED_NSE_HISTORICAL_FEED_NOT_CONFIGURED")
    }

    private fun unavailableNews(raw: String): JSONObject {
        val symbol = canonical(raw)
        return JSONObject().put("symbol", symbol).put("news", JSONArray())
            .put("provider", "Unavailable")
            .put("statusText", "News is unavailable until an authorized NSE/company-filings source is configured. No third-party news fallback is used.")
    }

    private fun yahooNews(raw: String): JSONObject {
        val symbol = canonical(raw)
        return JSONObject().put("symbol", symbol).put("news", JSONArray())
            .put("provider", "Unavailable")
            .put("statusText", "News is unavailable because no authorized NSE/Screener news endpoint is configured.")
    }

    /** No automated scraping of NSE public website endpoints without an authorized feed contract. */
    private fun nseIndexSnapshot(): Map<String, JSONObject> = emptyMap()

    private fun marketIndices(): JSONObject {
        val specs = linkedMapOf(
            "NIFTY 50" to "^NSEI", "SENSEX" to "^BSESN", "NIFTY BANK" to "^NSEBANK",
            "NIFTY MIDCAP 100" to "^CRSMID", "NIFTY SMALLCAP 100" to "^CRSSML", "NIFTY IT" to "^CNXIT",
            "NIFTY AUTO" to "^CNXAUTO", "NIFTY FMCG" to "^CNXFMCG", "NIFTY PHARMA" to "^CNXPHARMA",
            "NIFTY METAL" to "^CNXMETAL", "NIFTY PSU BANK" to "^CNXPSUBANK", "NIFTY PRIVATE BANK" to "^NIFTYPVTBANK",
            "NIFTY ENERGY" to "^CNXENERGY", "NIFTY INFRA" to "^CNXINFRA", "NIFTY FIN SERVICE" to "^CNXFINANCE",
            "GOLD FUTURES (GLOBAL)" to "GC=F", "SILVER FUTURES (GLOBAL)" to "SI=F", "BRENT CRUDE (GLOBAL)" to "BZ=F"
        )
        val out = JSONObject()
        specs.forEach { (label, _) ->
            out.put(label, JSONObject().put("value", JSONObject.NULL).put("changePct", JSONObject.NULL)
                .put("status", "UNAVAILABLE").put("priceSource", "NONE").put("provider", "No quote returned")
                .put("sourceType", "NO_DATA").put("isExchangeCertifiedRealtime", false)
                .put("marketDataDisclaimer", "No usable quote returned. Do not use a blank or historical value as a live price."))
        }

        // Fail closed: no historical or third-party fallback is allowed to masquerade as a current index quote.
        // Keep explicit null values so the UI can show that an authorized feed is not configured.
        specs.keys.forEach { label ->
            out.optJSONObject(label)
                ?.put("status", "AUTHORIZED_NSE_FEED_NOT_CONFIGURED")
                ?.put("sourceType", "NO_AUTHORIZED_FEED")
                ?.put("quoteTimestamp", JSONObject.NULL)
                ?.put("isExchangeCertifiedRealtime", false)
                ?.put("marketDataDisclaimer", "No authorized NSE real-time feed is configured. No live index value is available.")
        }
        return out
    }

    /**
     * Local equity autocomplete; broad provider search is intentionally disabled.
     * This is discovery only, not an exchange-authoritative security master or a licensed feed.
     * Preserve .NS/.BO suffixes so quote lookup uses the selected listing when available.
     */
    /** Search is limited to the locally maintained NSE equity suggestions until an authorized security master is configured. */
    private fun equitySearch(term: String, limit: Int = 12): List<JSONObject> = emptyList()

    fun handle(path: String): String {
        val p = path.substringBefore("?")
        val q = parseQuery(path)
        val raw = q["symbol"] ?: q["q"] ?: "INFY"
        val s = canonical(raw)
        return try {
            when (p) {
                "/api/health" -> JSONObject().put("ok", true).put("engine", "V40.79 NSE-FEED REQUIRED + SCREENER FUNDAMENTALS").put("data", JSONObject().put("ok", true).put("moneycontrolIntegration", "DISABLED_BY_V40_79_PROVIDER_POLICY").put("screenerSessionStatus", if (screenerLoggedIn()) "COOKIE_DETECTED_NOT_YET_VALIDATED" else "LOGIN_REQUIRED").put("providerDiagnostics", true).put("screenerCsvImport", true)).toString()
                "/api/providers/status" -> JSONObject().put("ok", true).put("data", providerStatus(raw)).toString()
                "/api/screener/status" -> JSONObject().put("ok", true).put("data", screenerStatus()).toString()
                "/api/screener/connect" -> JSONObject().put("ok", true).put("data", screenerStatus()).toString()
                "/api/screener/disconnect" -> JSONObject().put("ok", true).put("data", JSONObject().put("connected", false).put("loggedIn", false).put("message", "Sign out from Screener inside the web page to end the session.")).toString()
                "/api/search-suggestions" -> {
                    val originalTerm = (q["q"] ?: "").trim()
                    val term = originalTerm.uppercase(Locale.ROOT).replace(Regex("[^A-Z0-9]"), "")
                    val local = stocks.filter { term.isBlank() || it.symbol.contains(term) || it.name.uppercase(Locale.ROOT).replace(Regex("[^A-Z0-9]"), "").contains(term) || (term.contains("INFOSYS") && it.symbol == "INFY") }
                        .take(12).map { JSONObject().put("symbol", it.symbol).put("name", it.name).put("exchange", "NSE/BSE").put("sector", it.sector).put("provider", "Built-in fallback list") }
                    val external = if (originalTerm.length >= 2) try { equitySearch(originalTerm, 12) } catch (_: Exception) { emptyList() } else emptyList()
                    val combined = (external + local).distinctBy { it.optString("symbol").uppercase(Locale.ROOT) }.take(12)
                    val arr = JSONArray(); combined.forEach { arr.put(it) }
                    JSONObject().put("ok", true).put("data", arr).put("count", combined.size)
                        .put("searchProvider", if (external.isNotEmpty()) "Authorized security-master search" else "Local symbol list only; broad search unavailable")
                        .put("coverageDisclaimer", "Autocomplete is broad best-effort discovery, not a complete official NSE/BSE security master. Quotes can be delayed or unavailable.").toString()
                }
                "/api/quote", "/api/fast" -> {
                    val quote = try { nseQuote(raw) } catch (e: Exception) {
                        JSONObject().put("symbol", s).put("status", "AUTHORIZED_NSE_FEED_NOT_CONFIGURED")
                            .put("provider", "Unavailable").put("price", JSONObject.NULL)
                            .put("quoteTimestamp", JSONObject.NULL)
                            .put("marketDataDisclaimer", "No authorized NSE real-time feed is configured. No third-party fallback is used.")
                            .put("providerError", e.message ?: "Authorized NSE quote feed unavailable")
                    }
                    quote.put("rows", JSONArray()).put("historyProvider", "Unavailable")
                        .put("historyStatus", "AUTHORIZED_NSE_HISTORICAL_FEED_NOT_CONFIGURED")
                    val data = JSONObject().put("symbol", s).put("name", stockName(s)).put("quote", quote)
                        .put("provider", quote.optString("provider", "Unavailable"))
                        .put("rows", JSONArray())
                    JSONObject().put("ok", true).put("data", data).toString()
                }
                "/api/history" -> JSONObject().put("ok", true).put("data", historyData(s, q["range"] ?: "1y")).toString()
                "/api/screener-chart" -> JSONObject().put("ok", false).put("error", "Screener.in does not expose a documented chart-data API in this app. No Screener chart data was returned; use the separately labelled historical provider series or open Screener directly.").toString()
                "/api/analyze", "/api/bootstrap" -> {
                    val data = combined(raw, true)
                    if (p == "/api/bootstrap") data.put("diagnostics", JSONObject().put("quoteProvider", "NSE public endpoint with disclosed third-party fallback").put("fundamentalProvider", if (data.optJSONObject("fundamentals")?.has("providerError") == true) "Unavailable" else "Screener.in"))
                    JSONObject().put("ok", true).put("data", data).toString()
                }
                "/api/screener/live" -> {
                    if (!screenerLoggedIn()) throw IOException("Screener login is not active. Tap Screener Login first.")
                    // Preserve the user's explicit .BO listing for quote resolution.
                    // canonical(s) removes the suffix and can otherwise route a BSE
                    // selection to the NSE Yahoo ticker when the primary quote is unavailable.
                    val f = screener(raw)
                    val unavailableQuote = JSONObject()
                        .put("symbol", s)
                        .put("status", "AUTHORIZED_NSE_FEED_NOT_CONFIGURED")
                        .put("provider", "Unavailable")
                        .put("price", JSONObject.NULL)
                        .put("quoteTimestamp", JSONObject.NULL)
                        .put("marketDataDisclaimer", "Screener provides fundamentals here; it is not used as a quote or candle provider.")
                    JSONObject().put("ok", true).put("data", JSONObject().put("symbol", s)
                        .put("name", f.optString("name", stockName(s)))
                        .put("quote", unavailableQuote).put("fundamentals", f)
                        .put("dataConfidence", "SCREENER FUNDAMENTALS FETCHED; NSE QUOTE UNAVAILABLE UNTIL AUTHORIZED FEED IS CONFIGURED")).toString()
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
                "/api/peers" -> JSONObject().put("ok", true).put("data",
                    JSONObject().put("symbol", s).put("industry", stockSector(s)).put("peers", JSONArray())
                        .put("candidateCount", 0).put("validatedCount", 0).put("partial", true)
                        .put("method", "Peer prices and technical metrics require verified historical candles.")
                        .put("statusText", "Peer comparison is unavailable until an authorized NSE historical-data feed is configured. No third-party price history is used.")).toString()
                "/api/news" -> {
                    val news = try { unavailableNews(raw) } catch (e: Exception) { JSONObject().put("symbol", s).put("news", JSONArray()).put("statusText", "Authorized news source unavailable: ${e.message ?: "provider error"}").put("provider", "Unavailable") }
                    JSONObject().put("ok", true).put("data", news).toString()
                }
                "/api/company-events" -> JSONObject().put("ok", true).put("data",
                    JSONObject().put("symbol", s).put("name", stockName(s)).put("rows", JSONArray())
                        .put("provider", "Unavailable")
                        .put("statusText", "Corporate events are unavailable until an authorized NSE/company-filings source is configured. No third-party event fallback is used.")
                        .put("liveData", false)).toString()
                "/api/dividend-stocks" -> {
                    val d = runScreenerQuery("Market Capitalization > 1000 AND Dividend yield > 1 AND Return on capital employed > 10")
                    val rows = d.optJSONArray("rows") ?: JSONArray()
                    JSONObject().put("ok", true).put("data", JSONObject().put("rows", rows).put("statusText", "Screener session response parsed; authentication validity and field freshness are not independently certified. First result page only.").put("provider", d.optString("provider", "Screener.in")).put("partial", true)).toString()
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
                "/api/cache-clear" -> JSONObject().put("ok", true).put("data", JSONObject().put("cleared", false).put("cacheConfigured", false).put("message", "No persistent provider cache is configured; fresh provider requests will be attempted.")).toString()
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
