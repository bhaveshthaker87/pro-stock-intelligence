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
    private fun nseQuote(raw: String): JSONObject {
        val symbol = canonical(raw)
        if (symbol.isBlank() || symbol.startsWith("^") || symbol.endsWith("=F")) throw IOException("NSE quote supports equity symbols only")
        var cookie = ""
        val home = (URL("https://www.nseindia.com/").openConnection() as HttpURLConnection)
        try {
            home.connectTimeout = 4000; home.readTimeout = 5000; home.instanceFollowRedirects = true
            home.setRequestProperty("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36")
            home.setRequestProperty("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
            home.setRequestProperty("Accept-Language", "en-IN,en;q=0.9")
            home.responseCode
            cookie = home.headerFields.entries.filter { it.key?.equals("Set-Cookie", true) == true }
                .flatMap { it.value ?: emptyList() }.map { it.substringBefore(";") }.distinct().joinToString("; ")
        } finally { home.disconnect() }
        val c = URL("https://www.nseindia.com/api/quote-equity?symbol=${Uri.encode(symbol)}").openConnection() as HttpURLConnection
        try {
            c.connectTimeout = 5000; c.readTimeout = 6000; c.instanceFollowRedirects = true
            c.setRequestProperty("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36")
            c.setRequestProperty("Accept", "application/json,text/plain,*/*")
            c.setRequestProperty("Referer", "https://www.nseindia.com/get-quotes/equity?symbol=${Uri.encode(symbol)}")
            c.setRequestProperty("Accept-Language", "en-IN,en;q=0.9")
            if (cookie.isNotBlank()) c.setRequestProperty("Cookie", cookie)
            val code = c.responseCode
            val body = (if (code in 200..299) c.inputStream else c.errorStream)?.bufferedReader(Charsets.UTF_8)?.use { it.readText() } ?: ""
            if (code !in 200..299) throw IOException("NSE quote endpoint returned HTTP $code")
            val root = JSONObject(body)
            val priceInfo = root.optJSONObject("priceInfo") ?: throw IOException("NSE response has no priceInfo")
            val price = priceInfo.optDouble("lastPrice", Double.NaN)
            if (!finite(price) || price <= 0) throw IOException("NSE response has no valid last price")
            val prev = priceInfo.optDouble("previousClose", Double.NaN)
            val week = priceInfo.optJSONObject("weekHighLow") ?: JSONObject()
            val out = JSONObject().put("symbol", symbol).put("resolvedSymbol", symbol).put("currency", "INR")
                .put("provider", "NSE India (public website endpoint)")
                .put("quoteStatus", "NSE_WEBSITE_RESPONSE_NOT_LICENSED_REALTIME_FEED")
                .put("marketDataStatus", "NSE_PUBLIC_ENDPOINT_MAY_RATE_LIMIT_OR_CHANGE")
                .put("marketDataDisclaimer", "NSE public website response; not a licensed real-time feed. Confirm quote timestamp and exchange before trading.")
                .put("responseReceivedAt", System.currentTimeMillis() / 1000L)
                .put("price", price).put("rows", JSONArray())
            putFinite(out, "previousClose", prev)
            if (finite(prev) && prev > 0) putFinite(out, "dayChangePct", (price / prev - 1.0) * 100.0)
            putFinite(out, "high52", week.optDouble("max", Double.NaN)); putFinite(out, "low52", week.optDouble("min", Double.NaN))
            return out
        } finally { c.disconnect() }
    }

    private fun yahoo(raw: String, range: String = "1y"): JSONObject {
        val symbol = canonical(raw)
        if (symbol.isBlank()) throw IOException("Enter a valid NSE/BSE symbol, e.g. INFY or TCS")
        val isIndex = symbol.startsWith("^") || symbol.endsWith("=F")
        val suffixes = if (isIndex) listOf("") else if (raw.trim().uppercase(Locale.ROOT).endsWith(".BO")) listOf(".BO", ".NS") else listOf(".NS", ".BO")
        val errors = mutableListOf<String>()
        for (host in listOf("query1.finance.yahoo.com", "query2.finance.yahoo.com")) {
            for (suffix in suffixes) {
                try {
                    val ticker = if (isIndex || symbol.endsWith("=F")) symbol else symbol + suffix
                    val yahooRange = when (range.lowercase(Locale.ROOT)) {
                        "1d" -> "1d"; "1w" -> "5d"; "3y" -> "5y"; "all" -> "max"; else -> range
                    }
                    val interval = when (range.lowercase(Locale.ROOT)) { "1d" -> "5m"; "1w" -> "30m"; else -> "1d" }
                    val url = "https://$host/v8/finance/chart/${Uri.encode(ticker)}?range=${Uri.encode(yahooRange)}&interval=$interval&events=div,splits"
                    val root = JSONObject(get(url))
                    val chart = root.optJSONObject("chart") ?: throw IOException("Yahoo response missing chart data")
                    val err = chart.optJSONObject("error")
                    if (err != null) throw IOException(err.optString("description", "Yahoo Finance rejected $ticker"))
                    val results = chart.optJSONArray("result") ?: throw IOException("No quote result for $ticker")
                    if (results.length() == 0) throw IOException("No price history found for $ticker")
                    val r = results.getJSONObject(0)
                    val meta = r.optJSONObject("meta") ?: JSONObject(); val q = r.getJSONObject("indicators").getJSONArray("quote").getJSONObject(0); val ts = r.optJSONArray("timestamp") ?: JSONArray()
                    val opens = q.optJSONArray("open"); val highs = q.optJSONArray("high"); val lows = q.optJSONArray("low"); val closes = q.optJSONArray("close"); val volumes = q.optJSONArray("volume")
                    val rows = JSONArray()
                    for (i in 0 until ts.length()) {
                        val close = closes?.optDouble(i, Double.NaN) ?: Double.NaN
                        if (!finite(close) || close <= 0.0) continue
                        val time = ts.optLong(i) * 1000L
                        val row = JSONObject().put("time", time).put("date", time).put("close", close)
                        val open = opens?.optDouble(i, Double.NaN) ?: Double.NaN
                        val high = highs?.optDouble(i, Double.NaN) ?: Double.NaN
                        val low = lows?.optDouble(i, Double.NaN) ?: Double.NaN
                        if (finite(open)) row.put("open", open) else row.put("open", JSONObject.NULL)
                        if (finite(high)) row.put("high", high) else row.put("high", JSONObject.NULL)
                        if (finite(low)) row.put("low", low) else row.put("low", JSONObject.NULL)
                        row.put("volume", volumes?.optLong(i, 0L) ?: 0L)
                        rows.put(row)
                    }
                    if (rows.length() == 0) throw IOException("No usable closing prices for $ticker")
                    val lastClose = rows.getJSONObject(rows.length() - 1).optDouble("close", Double.NaN)
                    val marketPrice = meta.optDouble("regularMarketPrice", Double.NaN)
                    val hasProviderQuote = finite(marketPrice) && marketPrice > 0
                    val price = if (hasProviderQuote) marketPrice else lastClose
                    val prev = meta.optDouble("chartPreviousClose", meta.optDouble("previousClose", Double.NaN))
                    val out = JSONObject().put("symbol", symbol).put("resolvedSymbol", ticker).put("currency", meta.optString("currency", "INR"))
                        .put("rows", rows).put("provider", "Yahoo Finance")
                        .put("priceSource", if (hasProviderQuote) "PROVIDER_QUOTE_METADATA" else "HISTORICAL_CLOSE_FALLBACK")
                        .put("quoteStatus", if (hasProviderQuote) "THIRD_PARTY_PROVIDER_DATA_DELAY_NOT_GUARANTEED" else "HISTORICAL_ONLY_NOT_A_CURRENT_QUOTE")
                    if (meta.has("regularMarketTime") && !meta.isNull("regularMarketTime")) out.put("quoteTimestamp", meta.optLong("regularMarketTime"))
                    val eventRows = JSONArray()
                    val events = r.optJSONObject("events")
                    listOf("dividends", "splits").forEach { eventType ->
                        val group = events?.optJSONObject(eventType) ?: return@forEach
                        val keys = group.keys()
                        while (keys.hasNext()) {
                            val ev = group.optJSONObject(keys.next()) ?: continue
                            val epoch = ev.optLong("date", 0L)
                            val dateText = if (epoch > 0) java.text.SimpleDateFormat("dd MMM yyyy", Locale.ENGLISH).format(java.util.Date(epoch * 1000L)) else "Date unavailable"
                            val item = JSONObject().put("date", dateText).put("type", if (eventType == "dividends") "Dividend" else "Stock Split")
                                .put("event", if (eventType == "dividends") "Cash dividend" else "Stock split")
                            if (eventType == "dividends") putFinite(item, "dividend", ev.optDouble("amount", Double.NaN))
                            else item.put("ratio", "${ev.optInt("numerator", 0)}:${ev.optInt("denominator", 0)}")
                            eventRows.put(item)
                        }
                    }
                    out.put("events", eventRows)
                    out.put("marketDataStatus", "THIRD_PARTY_QUOTE_DELAY_POSSIBLE")
                    out.put("marketDataDisclaimer", "Third-party data may be delayed or incomplete; verify with the exchange before trading.")
                    out.put("priceTimestamp", if (meta.has("regularMarketTime")) meta.optLong("regularMarketTime") else (ts.optLong(ts.length() - 1)))
                    putFinite(out, "price", price); putFinite(out, "previousClose", prev)
                    if (finite(prev) && prev > 0 && finite(price)) putFinite(out, "dayChangePct", (price / prev - 1.0) * 100.0)
                    putFinite(out, "high52", meta.optDouble("fiftyTwoWeekHigh", Double.NaN))
                    putFinite(out, "low52", meta.optDouble("fiftyTwoWeekLow", Double.NaN))
                    return out
                } catch (e: Exception) { errors.add("$host $suffix: ${e.message ?: "provider error"}") }
            }
        }
        throw IOException("Yahoo Finance data unavailable for ${stockName(symbol)} ($symbol). ${errors.takeLast(3).joinToString(" | ")}")
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
        val looksLikeLogin = Regex("(?is)<title[^>]*>.*?(?:login|sign in).*?</title>").containsMatchIn(html) ||
            html.contains("name=\"password\"", ignoreCase = true)
        if (looksLikeLogin) throw IOException("Screener returned a login page instead of company data; sign in again and retry.")
        if (pageTitle.isNullOrBlank() || !hasRatioSection) {
            throw IOException("Screener company page could not be validated for '$s' (wrong symbol, blocked page, or changed markup). No fundamentals accepted.")
        }
        // Match the visible label and value in the same ratio list item. Never guess from nearby text.
        fun number(label: String, percent: Boolean = false): Double? {
            val items = Regex("(?is)<li\\b[^>]*>(.*?)</li>").findAll(html).map { it.groupValues[1] }
            val matches = items.mapNotNull { item ->
                val name = Regex("(?is)<span\\b[^>]*class=[\"'][^\"']*\\bname\\b[^\"']*[\"'][^>]*>(.*?)</span>")
                    .find(item)?.groupValues?.getOrNull(1)?.let { cleanText(it) } ?: return@mapNotNull null
                if (!name.equals(label, ignoreCase = true)) return@mapNotNull null
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
        val fieldKeys = listOf("price", "marketCap", "pe", "bookValue", "dividendYield", "roce", "roe", "debtEquity", "eps", "netProfit", "operatingProfit", "opm", "sales3y", "profit3y", "eps3y", "currentRatio", "interestCoverage", "quarterly", "shareholding")
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
        val quoteFuture = executor.submit<JSONObject> {
            var nse: JSONObject? = null
            var nseError: String? = null
            val bseListingSelected = raw.trim().uppercase(Locale.ROOT).endsWith(".BO")
            try {
                if (bseListingSelected) nseError = "BSE listing selected; use the .BO third-party quote path; NSE quote endpoint is not exchange-specific"
                else nse = nseQuote(raw)
            } catch (e: Exception) { nseError = e.message ?: "NSE public quote unavailable" }
            try {
                val hist = yahoo(raw, "1y")
                val out = nse ?: JSONObject()
                // Historical candles currently come from Yahoo; keep that provenance separate and never label it NSE.
                out.put("rows", hist.optJSONArray("rows") ?: JSONArray())
                out.put("historyProvider", hist.optString("provider", "Yahoo Finance"))
                out.put("historyStatus", "THIRD_PARTY_HISTORICAL_BARS_NOT_NSE_VERIFIED")
                if (!out.has("price") && hist.has("price")) {
                    out.put("price", hist.get("price")).put("provider", "Yahoo Finance fallback (not NSE/Moneycontrol)")
                    if (hist.has("previousClose")) out.put("previousClose", hist.get("previousClose"))
                    if (hist.has("dayChangePct")) out.put("dayChangePct", hist.get("dayChangePct"))
                    if (hist.has("high52")) out.put("high52", hist.get("high52"))
                    if (hist.has("low52")) out.put("low52", hist.get("low52"))
                    out.put("quoteStatus", "THIRD_PARTY_FALLBACK_NOT_EXCHANGE_VERIFIED")
                    out.put("marketDataDisclaimer", "NSE quote unavailable. Yahoo Finance fallback may be delayed; do not treat as an NSE/Moneycontrol live quote.")
                    out.put("priceTimestamp", hist.optLong("priceTimestamp", 0L))
                }
                if (!nseError.isNullOrBlank()) out.put("nseProviderWarning", nseError)
                if (!out.has("price")) out.put("providerError", nseError ?: "No usable quote")
                out
            } catch (e: Exception) {
                val out = nse ?: JSONObject().put("symbol", s).put("provider", "Unavailable")
                out.put("rows", JSONArray())
                if (!out.has("price")) out.put("providerError", "NSE: ${nseError ?: "unavailable"}; historical fallback: ${e.message ?: "unavailable"}")
                if (!nseError.isNullOrBlank()) out.put("nseProviderWarning", nseError)
                out
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
        val quote = result(quoteFuture, JSONObject().put("symbol", s).put("rows", JSONArray()).put("provider", "Unavailable").put("providerError", "NSE/third-party quote lookup timed out"))
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
                // Prefer exchange quote when available; Screener price is only a disclosed fallback.
                if (k != "providerError" && !(k == "price" && quote.has("price"))) market.put(k, f.get(k))
            }
        }
        val rows = quote.optJSONArray("rows") ?: JSONArray()
        val history = JSONObject().put("rows", rows).put("provider", quote.optString("provider", "Yahoo Finance"))
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
        val y = yahoo(raw, range)
        return JSONObject().put("symbol", y.optString("symbol")).put("rows", y.optJSONArray("rows") ?: JSONArray())
            .put("provider", y.optString("provider", "Yahoo Finance")).put("historyStatus", "THIRD_PARTY_HISTORICAL_BARS_NOT_NSE_VERIFIED").put("chartMode", "OHLCV")
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
        // Explicit Callable avoids Kotlin selecting ExecutorService.submit(Runnable),
        // which can fail type inference for the value-returning lambda in CI.
        val jobs: List<java.util.concurrent.Future<JSONObject>> = stocks.map { stock ->
            completion.submit(java.util.concurrent.Callable<JSONObject> {
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
            })
        }
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

    /**
     * Reads the public NSE index snapshot once for all Indian indices. This endpoint may block
     * automated clients and is not a licensed guaranteed-real-time feed; Yahoo is only fallback.
     */
    private fun nseIndexSnapshot(): Map<String, JSONObject> {
        var cookie = ""
        val home = URL("https://www.nseindia.com/").openConnection() as HttpURLConnection
        try {
            home.connectTimeout = 2000
            home.readTimeout = 2500
            home.instanceFollowRedirects = true
            home.setRequestProperty("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36")
            home.setRequestProperty("Accept", "text/html,application/xhtml+xml,*/*")
            home.setRequestProperty("Accept-Language", "en-IN,en;q=0.9")
            home.responseCode
            cookie = home.headerFields.entries
                .filter { it.key?.equals("Set-Cookie", true) == true }
                .flatMap { it.value ?: emptyList() }
                .map { it.substringBefore(";") }.distinct().joinToString("; ")
        } finally { home.disconnect() }

        val c = URL("https://www.nseindia.com/api/allIndices").openConnection() as HttpURLConnection
        try {
            c.connectTimeout = 2500
            c.readTimeout = 3500
            c.instanceFollowRedirects = true
            c.setRequestProperty("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36")
            c.setRequestProperty("Accept", "application/json,text/plain,*/*")
            c.setRequestProperty("Referer", "https://www.nseindia.com/market-data/live-market-indices")
            c.setRequestProperty("Accept-Language", "en-IN,en;q=0.9")
            if (cookie.isNotBlank()) c.setRequestProperty("Cookie", cookie)
            val code = c.responseCode
            val stream = if (code in 200..299) c.inputStream else c.errorStream
            val body = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() } ?: ""
            if (code !in 200..299) throw IOException("NSE index snapshot HTTP $code")
            val data = JSONObject(body).optJSONArray("data") ?: throw IOException("NSE index snapshot has no data array")
            val result = linkedMapOf<String, JSONObject>()
            val aliases = mapOf(
                "NIFTY 50" to listOf("NIFTY 50"),
                "NIFTY BANK" to listOf("NIFTY BANK"),
                "NIFTY MIDCAP 100" to listOf("NIFTY MIDCAP 100", "NIFTY MIDCAP 100 INDEX"),
                "NIFTY SMALLCAP 100" to listOf("NIFTY SMALLCAP 100", "NIFTY SMALLCAP 100 INDEX"),
                "NIFTY IT" to listOf("NIFTY IT"),
                "NIFTY AUTO" to listOf("NIFTY AUTO"),
                "NIFTY FMCG" to listOf("NIFTY FMCG"),
                "NIFTY PHARMA" to listOf("NIFTY PHARMA"),
                "NIFTY METAL" to listOf("NIFTY METAL"),
                "NIFTY PSU BANK" to listOf("NIFTY PSU BANK"),
                "NIFTY PRIVATE BANK" to listOf("NIFTY PRIVATE BANK"),
                "NIFTY ENERGY" to listOf("NIFTY ENERGY"),
                "NIFTY INFRA" to listOf("NIFTY INFRA"),
                "NIFTY FIN SERVICE" to listOf("NIFTY FINANCIAL SERVICES", "NIFTY FIN SERVICE")
            )
            val wanted = aliases.flatMap { (label, names) -> names.map { normalizeIndexName(it) to label } }.toMap()
            for (i in 0 until data.length()) {
                val item = data.optJSONObject(i) ?: continue
                val rawName = item.optString("index", item.optString("indexName", ""))
                val label = wanted[normalizeIndexName(rawName)] ?: continue
                val value = item.optDouble("last", item.optDouble("lastPrice", Double.NaN))
                if (!finite(value) || value <= 0) continue
                val previous = item.optDouble("previousClose", item.optDouble("previous", Double.NaN))
                val change = item.optDouble("percentChange", Double.NaN)
                val timeText = item.optString("timeVal", item.optString("timestamp", ""))
                val timestamp = try {
                    val parser = java.text.SimpleDateFormat("dd-MMM-yyyy HH:mm:ss", Locale.ENGLISH)
                    parser.timeZone = java.util.TimeZone.getTimeZone("Asia/Kolkata")
                    parser.parse(timeText)?.time?.div(1000L) ?: 0L
                } catch (_: Exception) { 0L }
                val obj = JSONObject()
                    .put("value", value)
                    .put("status", "QUOTE_RETURNED_FRESHNESS_UNVERIFIED")
                    .put("priceSource", "NSE_PUBLIC_INDEX_SNAPSHOT")
                    .put("provider", "NSE public website")
                    .put("currency", "INR")
                    .put("sourceType", "PUBLIC_ENDPOINT_NOT_LICENSED_REALTIME")
                    .put("isExchangeCertifiedRealtime", false)
                    .put("quoteTimeText", timeText)
                    .put("marketDataDisclaimer", "NSE public website snapshot; availability and freshness are not guaranteed. Verify with your broker/exchange.")
                if (finite(previous) && previous > 0) obj.put("previousClose", previous)
                if (finite(change)) obj.put("changePct", change)
                else if (finite(previous) && previous > 0) obj.put("changePct", (value / previous - 1.0) * 100.0)
                if (timestamp > 0) obj.put("quoteTimestamp", timestamp)
                result[label] = obj
            }
            return result
        } finally { c.disconnect() }
    }

    private fun normalizeIndexName(value: String): String =
        value.uppercase(Locale.ROOT).replace(Regex("[^A-Z0-9]"), "")

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

        // One NSE snapshot supplies most Indian indices in one network round-trip.
        try {
            nseIndexSnapshot().forEach { (label, data) -> out.put(label, data) }
        } catch (_: Exception) {
            // Fall through to provider-per-symbol requests below.
        }

        val needsFallback = specs.filter { (label, _) ->
            out.optJSONObject(label)?.optString("priceSource") == "NONE"
        }
        val executor = Executors.newFixedThreadPool(6)
        try {
            val tasks = needsFallback.map { (label, symbol) ->
                java.util.concurrent.Callable {
                    val data = yahoo(symbol, "5d")
                    val rows = data.optJSONArray("rows") ?: JSONArray()
                    val last = if (rows.length() > 0) rows.getJSONObject(rows.length() - 1) else JSONObject()
                    val prev = if (rows.length() > 1) rows.getJSONObject(rows.length() - 2) else JSONObject()
                    val currentQuote = data.optDouble("price", Double.NaN)
                    val previousQuote = data.optDouble("previousClose", Double.NaN)
                    val priceSource = data.optString("priceSource", "HISTORICAL_CLOSE_FALLBACK")
                    val value = if (finite(currentQuote) && currentQuote > 0) currentQuote else last.optDouble("close", Double.NaN)
                    val previous = if (finite(previousQuote) && previousQuote > 0) previousQuote else prev.optDouble("close", Double.NaN)
                    val hasValue = finite(value) && value > 0
                    val status = when {
                        !hasValue -> "NO_VALID_PRICE"
                        priceSource == "HISTORICAL_CLOSE_FALLBACK" -> "HISTORICAL_ONLY"
                        else -> "QUOTE_RETURNED_FRESHNESS_UNVERIFIED"
                    }
                    val obj = JSONObject()
                        .put("status", status).put("provider", data.optString("provider", "Yahoo Finance"))
                        .put("priceSource", priceSource).put("sourceType", "THIRD_PARTY_DELAY_POSSIBLE")
                        .put("currency", data.optString("currency", if (label.contains("GLOBAL")) "USD" else "INR"))
                        .put("isExchangeCertifiedRealtime", false)
                        .put("marketDataDisclaimer", "Third-party data may be delayed or unavailable; verify with the exchange before trading.")
                    putFinite(obj, "value", value)
                    if (finite(value) && finite(previous) && previous > 0) putFinite(obj, "changePct", (value / previous - 1.0) * 100.0)
                    val timestamp = when {
                        data.optLong("quoteTimestamp") > 0 -> data.optLong("quoteTimestamp")
                        data.optLong("priceTimestamp") > 0 -> data.optLong("priceTimestamp")
                        last.optLong("time") > 0 -> last.optLong("time") / 1000L
                        else -> 0L
                    }
                    if (timestamp > 0) obj.put("quoteTimestamp", timestamp)
                    if (data.has("quoteTimeText")) obj.put("quoteTimeText", data.optString("quoteTimeText"))
                    label to obj
                }
            }
            // Global deadline prevents one blocked provider from stalling the whole panel.
            val futures = executor.invokeAll(tasks, 9000, TimeUnit.MILLISECONDS)
            futures.forEachIndexed { index, future ->
                if (!future.isCancelled) {
                    try {
                        val (label, data) = future.get()
                        if (data.optString("status") != "NO_VALID_PRICE") out.put(label, data)
                    } catch (_: Exception) { }
                }
            }
        } finally { executor.shutdownNow() }
        return out
    }

    /**
     * Broad Indian equity autocomplete using Yahoo Finance's public search response.
     * This is discovery only, not an exchange-authoritative security master or a licensed feed.
     * Preserve .NS/.BO suffixes so quote lookup uses the selected listing when available.
     */
    private fun equitySearch(term: String, limit: Int = 12): List<JSONObject> {
        val q = term.trim()
        if (q.length < 1) return emptyList()
        val url = "https://query1.finance.yahoo.com/v1/finance/search?q=${URLEncoder.encode(q, "UTF-8")}&quotesCount=${limit.coerceIn(1, 20)}&newsCount=0"
        val root = JSONObject(get(url))
        val quotes = root.optJSONArray("quotes") ?: JSONArray()
        val out = mutableListOf<JSONObject>()
        val seen = mutableSetOf<String>()
        for (i in 0 until quotes.length()) {
            val item = quotes.optJSONObject(i) ?: continue
            val ticker = item.optString("symbol", "").uppercase(Locale.ROOT)
            val type = item.optString("quoteType", "")
            if (type.isNotBlank() && type != "EQUITY") continue
            if (!ticker.endsWith(".NS") && !ticker.endsWith(".BO")) continue
            if (!seen.add(ticker)) continue
            val base = ticker.removeSuffix(".NS").removeSuffix(".BO")
            val exchange = if (ticker.endsWith(".BO")) "BSE" else "NSE"
            out.add(JSONObject().put("symbol", ticker).put("name", item.optString("shortname", item.optString("longname", base)))
                .put("exchange", exchange).put("sector", "Equity").put("provider", "Yahoo Finance search"))
            if (out.size >= limit.coerceIn(1, 20)) break
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
                "/api/health" -> JSONObject().put("ok", true).put("engine", "V40.77 LIVE-REFRESH + CHART READABILITY").put("data", JSONObject().put("ok", true).put("moneycontrolIntegration", "PUBLIC_VIEW_ONLY_AUTOMATED_FEED_NOT_CONFIGURED").put("screenerSessionStatus", if (screenerLoggedIn()) "COOKIE_DETECTED_NOT_YET_VALIDATED" else "LOGIN_REQUIRED").put("providerDiagnostics", true).put("screenerCsvImport", true)).toString()
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
                        .put("searchProvider", if (external.isNotEmpty()) "Yahoo Finance search + local fallback" else "Local fallback; broad search unavailable")
                        .put("coverageDisclaimer", "Autocomplete is broad best-effort discovery, not a complete official NSE/BSE security master. Quotes can be delayed or unavailable.").toString()
                }
                "/api/quote", "/api/fast" -> {
                    val history = try { yahoo(raw, "5d") } catch (_: Exception) { JSONObject().put("rows", JSONArray()).put("provider", "Unavailable") }
                    val quote = try {
                        if (raw.trim().uppercase(Locale.ROOT).endsWith(".BO")) throw IOException("BSE listing selected; using .BO third-party quote lookup")
                        nseQuote(raw)
                    } catch (nseError: Exception) {
                        val fallback = JSONObject().put("symbol", s).put("providerError", "Exchange quote fallback: ${nseError.message ?: "NSE public quote unavailable"}")
                        if (history.has("price")) {
                            fallback.put("price", history.get("price")).put("provider", "Yahoo Finance fallback (not exchange-certified real-time)")
                            listOf("previousClose", "dayChangePct", "high52", "low52", "priceTimestamp", "quoteTimestamp").forEach { k -> if (history.has(k)) fallback.put(k, history.get(k)) }
                            fallback.put("marketDataDisclaimer", "Third-party quote may be delayed, incomplete or unavailable; it is not a licensed NSE/BSE real-time feed.")
                        }
                        fallback
                    }
                    quote.put("rows", history.optJSONArray("rows") ?: JSONArray())
                    annotateQuoteQuality(quote)
                    quote.put("exchange", if (raw.trim().uppercase(Locale.ROOT).endsWith(".BO")) "BSE" else if (raw.trim().uppercase(Locale.ROOT).endsWith(".NS")) "NSE" else "NSE primary; BSE availability varies")
                    quote.put("historyProvider", history.optString("provider", "Unavailable"))
                    quote.put("historyStatus", "THIRD_PARTY_HISTORICAL_BARS_NOT_NSE_VERIFIED")
                    val data = JSONObject().put("symbol", s).put("name", stockName(s)).put("quote", quote)
                        .put("provider", quote.optString("provider", "Unavailable")).put("rows", quote.optJSONArray("rows") ?: JSONArray())
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
                    val f = screener(s); val y = yahoo(s, "5d")
                    JSONObject().put("ok", true).put("data", JSONObject().put("symbol", s).put("name", f.optString("name", stockName(s))).put("quote", y).put("fundamentals", f).put("dataConfidence", "SESSION-BASED / MIXED SOURCES — VERIFY PROVIDERS AND TIMESTAMPS")).toString()
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
                    JSONObject().put("ok", true).put("data", JSONObject().put("symbol", s).put("name", stockName(s)).put("rows", events).put("statusText", if (events.length() > 0) "Third-party Yahoo Finance dividend/split events returned; confirm dates with the exchange" else "No dividend or split events were returned by Yahoo Finance; this does not establish that no events exist. Confirm against official exchange/company filings.").put("provider", y.optString("provider", "Yahoo Finance"))).toString()
                }
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
