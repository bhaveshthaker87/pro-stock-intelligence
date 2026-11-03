package com.prostock.intelligence

import android.app.Activity
import android.content.Intent
import android.content.res.AssetManager
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
    private lateinit var provider: NativeProvider

    private fun jsonResponse(json: String): WebResourceResponse =
        WebResourceResponse("application/json", "UTF-8", ByteArrayInputStream(json.toByteArray(Charsets.UTF_8))).apply {
            responseHeaders = mapOf("Cache-Control" to "no-store, max-age=0", "Pragma" to "no-cache", "X-Content-Type-Options" to "nosniff", "Access-Control-Allow-Origin" to "https://appassets.androidplatform.net")
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Keep WebView content below Android system bars on devices using edge-to-edge defaults.
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.R) window.setDecorFitsSystemWindows(true)
        window.statusBarColor = Color.rgb(6, 38, 75)
        window.navigationBarColor = Color.rgb(6, 38, 75)
        @Suppress("DEPRECATION")
        window.decorView.systemUiVisibility = 0
        provider = NativeProvider(assets)
        Log.e("PSI_STARTUP", "ON_CREATE_BEGIN")
        CookieManager.getInstance().setAcceptCookie(true)
        web = WebView(this)
        Log.e("PSI_STARTUP", "WEBVIEW_CREATED")
        // Keep a branded native splash visible while the local dashboard HTML boots.
        // This prevents a blank launch screen from being mistaken for a missing app title.
        val appRoot = android.widget.FrameLayout(this)
        val splashView = android.widget.LinearLayout(this).apply {
            orientation = android.widget.LinearLayout.VERTICAL
            gravity = android.view.Gravity.CENTER
            setBackgroundColor(Color.rgb(6, 38, 75))
            setPadding(24, 24, 24, 24)
        }
        val splashTitle = android.widget.TextView(this).apply {
            text = "PRO STOCK INTELLIGENCE"
            setTextColor(Color.WHITE)
            textSize = 23f
            typeface = android.graphics.Typeface.create("sans-serif", android.graphics.Typeface.BOLD)
            gravity = android.view.Gravity.CENTER
        }
        val splashSubtitle = android.widget.TextView(this).apply {
            text = "NSE  •  BSE  •  MARKET RESEARCH"
            setTextColor(Color.rgb(177, 218, 245))
            textSize = 12f
            gravity = android.view.Gravity.CENTER
            setPadding(0, 10, 0, 20)
        }
        splashView.addView(splashTitle, android.widget.LinearLayout.LayoutParams(
            android.widget.LinearLayout.LayoutParams.MATCH_PARENT, android.widget.LinearLayout.LayoutParams.WRAP_CONTENT
        ))
        splashView.addView(splashSubtitle, android.widget.LinearLayout.LayoutParams(
            android.widget.LinearLayout.LayoutParams.MATCH_PARENT, android.widget.LinearLayout.LayoutParams.WRAP_CONTENT
        ))
        splashView.addView(android.widget.ProgressBar(this), android.widget.LinearLayout.LayoutParams(
            android.widget.LinearLayout.LayoutParams.WRAP_CONTENT, android.widget.LinearLayout.LayoutParams.WRAP_CONTENT
        ))
        web.visibility = android.view.View.INVISIBLE
        appRoot.addView(web, android.widget.FrameLayout.LayoutParams(
            android.widget.FrameLayout.LayoutParams.MATCH_PARENT, android.widget.FrameLayout.LayoutParams.MATCH_PARENT
        ))
        appRoot.addView(splashView, android.widget.FrameLayout.LayoutParams(
            android.widget.FrameLayout.LayoutParams.MATCH_PARENT, android.widget.FrameLayout.LayoutParams.MATCH_PARENT
        ))
        // CI AVDs use SwiftShader; force software composition for this dashboard WebView
        // to avoid Chromium renderer traps in headless virtual-GPU environments.
        web.setLayerType(android.view.View.LAYER_TYPE_SOFTWARE, null)
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
            .setDomain("appassets.androidplatform.net")
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()
        Log.e("PSI_STARTUP", "ASSET_LOADER_READY")
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
            override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest): WebResourceResponse? {
                if (request.url.path == "/assets/index.html") Log.e("PSI_STARTUP", "INDEX_ASSET_REQUEST ${request.url}")
                return api(request.url) ?: assetLoader.shouldInterceptRequest(request.url)
            }
            @Suppress("DEPRECATION")
            override fun shouldInterceptRequest(view: WebView, url: String): WebResourceResponse? {
                val uri = Uri.parse(url)
                return api(uri) ?: assetLoader.shouldInterceptRequest(uri)
            }
            override fun onPageStarted(view: WebView, url: String, favicon: android.graphics.Bitmap?) {
                super.onPageStarted(view, url, favicon)
                Log.e("PSI_STARTUP", "PAGE_STARTED $url")
            }
            override fun onPageCommitVisible(view: WebView, url: String) {
                super.onPageCommitVisible(view, url)
                Log.e("PSI_STARTUP", "PAGE_COMMIT_VISIBLE $url")
            }
            // Use the AndroidX compatibility error type; the platform WebResourceError
            // overload is final in WebViewClientCompat and must not be overridden.
            override fun onReceivedError(view: WebView, request: WebResourceRequest, error: androidx.webkit.WebResourceErrorCompat) {
                super.onReceivedError(view, request, error)
                Log.e("PSI_WEB", "LOAD_ERROR mainFrame=${request.isForMainFrame} code=${error.errorCode} description=${error.description} url=${request.url}")
            }
            override fun onReceivedHttpError(view: WebView, request: WebResourceRequest, response: WebResourceResponse) {
                super.onReceivedHttpError(view, request, response)
                Log.e("PSI_WEB", "HTTP_ERROR mainFrame=${request.isForMainFrame} status=${response.statusCode} url=${request.url}")
            }
            override fun onRenderProcessGone(view: WebView, detail: RenderProcessGoneDetail): Boolean {
                Log.e("PSI_WEB", "RENDER_PROCESS_GONE crashed=${detail.didCrash()} priority=${detail.rendererPriorityAtExit()}")
                return true
            }
            override fun onPageFinished(view: WebView, url: String) {
                super.onPageFinished(view, url)
                if (url.startsWith("https://www.screener.in/")) {
                    CookieManager.getInstance().flush()
                }
                if (url.startsWith("https://appassets.androidplatform.net/assets/index.html")) {
                    CookieManager.getInstance().flush()
                    Log.e("PSI_STARTUP", "INDEX_PAGE_FINISHED")
                    view.evaluateJavascript(
                        "(()=>({ready:document.readyState,root:!!document.querySelector('.app'),title:document.title}))()"
                    ) { value ->
                        if (!value.isNullOrBlank() && value.contains("\"root\":true")) {
                            web.visibility = android.view.View.VISIBLE
                            splashView.visibility = android.view.View.GONE
                            Log.e("PSI_STARTUP", "PSI_DASHBOARD_DOM_READY $value")
                        } else {
                            Log.e("PSI_STARTUP", "DASHBOARD_DOM_NOT_READY $value")
                        }
                    }
                    view.evaluateJavascript("window.refreshScreenerStatus && window.refreshScreenerStatus()", null)
                }
            }
        }
        setContentView(appRoot)
        Log.e("PSI_STARTUP", "CONTENT_VIEW_SET")
        web.loadUrl("https://appassets.androidplatform.net/assets/index.html")
        Log.e("PSI_STARTUP", "LOAD_URL_REQUESTED")
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
            // WebView must be detached from its parent before destroy(); destroying an
            // attached WebView can leave renderer resources and Activity windows behind.
            (web.parent as? android.view.ViewGroup)?.removeView(web)
            web.stopLoading()
            web.webChromeClient = null
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

private class NativeProvider(private val appAssets: AssetManager) {
    // One short-lived cache is shared by analyze, bootstrap, factor and peer requests.
    // Store immutable JSON snapshots as strings so callers cannot mutate the cached object.
    private data class CachedFundamentals(val payload: String, val fetchedAtMs: Long)
    private val fundamentalsCache = java.util.concurrent.ConcurrentHashMap<String, CachedFundamentals>()
    private val fundamentalsCacheTtlMs = 5L * 60L * 1000L
    @Volatile private var screener403Observed: Boolean = false
    @Volatile private var screenerSessionValidatedAtMs: Long = 0L
    private fun screenerSessionIsValidated(): Boolean = screenerLoggedIn() && !screener403Observed && screenerSessionValidatedAtMs > 0L && System.currentTimeMillis() - screenerSessionValidatedAtMs < 30L * 60L * 1000L
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
        Stock("TATAELXSI", "Tata Elxsi Ltd", "IT Services"), Stock("DIXON", "Dixon Technologies India Ltd", "Electronics"),
        Stock("ONGC", "Oil and Natural Gas Corporation Ltd", "Energy"), Stock("ADANIENT", "Adani Enterprises Ltd", "Diversified")
    )
    private val queryDefs = listOf(
        JSONObject().put("id", "master").put("name", "Large Cap Quality Stocks").put("description", "Large companies with quality and manageable debt").put("focus", "Market cap, ROCE, debt and valuation").put("query", "Market Capitalization > 10000 AND Current price > 50 AND Return on capital employed > 12 AND Debt to equity < 1"),
        JSONObject().put("id", "midcap").put("name", "Mid Cap Hidden Gems").put("description", "Mid-sized companies with profitability and growth").put("focus", "Market cap ₹5,000–30,000 Cr, ROCE > 15%").put("query", "Market Capitalization > 5000 AND Market Capitalization < 30000 AND Return on capital employed > 15 AND Return on equity > 15"),
        JSONObject().put("id", "smallcap").put("name", "Small Cap Quality").put("description", "Smaller profitable companies; higher risk").put("focus", "Market cap ₹1,000–5,000 Cr").put("query", "Market Capitalization > 1000 AND Market Capitalization < 5000 AND Return on capital employed > 15 AND Debt to equity < 1"),
        JSONObject().put("id", "oversold").put("name", "RSI Oversold Scanner (RSI ≤ 30)").put("description", "Technical scan of tracked stocks using Wilder RSI(14); requires authorized NSE historical bars").put("focus", "Wilder RSI(14) ≤ 30; tracked symbols only, unavailable until authorized NSE history is configured").put("query", "Technical scan: RSI(14) <= 30; tracked universe only"),
        JSONObject().put("id", "crash").put("name", "Daily Crash Scanner (drop ≥ 5%)").put("description", "Finds tracked stocks down at least 5% versus the prior daily bar; requires authorized NSE historical bars").put("focus", "Latest daily-bar change ≤ -5%; tracked symbols only; unavailable until authorized NSE history is configured").put("query", "Technical scan: daily change <= -5%; tracked universe only")
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
        // Preserve exchange-index and futures ticker syntax. Stripping punctuation here
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
            // Use the cookie jar for the exact request host. Merging cookies from
            // www and the bare domain can select a stale duplicate sessionid and cause 403.
            // CookieManager already applies domain/path rules for this URL.
            val cookie = CookieManager.getInstance().getCookie(url)
            if (!cookie.isNullOrBlank()) c.setRequestProperty("Cookie", cookie)
        }
        try {
            val code = c.responseCode
            val stream = if (code in 200..299) c.inputStream else c.errorStream
            val body = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() } ?: ""
            if (code in 200..299 && (host == "screener.in" || host.endsWith(".screener.in"))) {
                screener403Observed = false
            }
            if (code == 403 && (host == "screener.in" || host.endsWith(".screener.in"))) {
                screener403Observed = true
                screenerSessionValidatedAtMs = 0L
                val finalHost = runCatching { c.url.host.lowercase(Locale.ROOT) }.getOrDefault(host)
                val responseKind = when {
                    Regex("""(?is)<title[^>]*>.*?(login|sign in).*?</title>|name=["']password["']""").containsMatchIn(body) -> "login page returned"
                    Regex("(?is)cloudflare|captcha|access denied|request blocked|security check").containsMatchIn(body) -> "security/access-control page returned"
                    body.isBlank() -> "empty denial response"
                    else -> "server denied the request"
                }
                throw IOException("Screener HTTP 403 Forbidden ($responseKind; final host $finalHost). Session cookie was taken from the exact request URL to avoid stale duplicate cookies. This app will not bypass access controls. Reopen the official Screener page inside the app, confirm the account is signed in, then run one access check. If it persists, Screener is denying this app request and the fields remain unavailable.")
            }
            if (code == 401 && (host == "screener.in" || host.endsWith(".screener.in"))) {
                throw IOException("Screener returned HTTP 401. Tap Screener Login, sign in again, return to the app and retry.")
            }
            if (code !in 200..299) throw IOException("HTTP $code from $host")
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
    private fun gatewayBaseUrl(): String = BuildConfig.PROVIDER_GATEWAY_BASE_URL.trim().trimEnd('/')

    private fun gatewayConfigured(): Boolean = gatewayBaseUrl().startsWith("https://", ignoreCase = true)


    // Public Downstox endpoints are a supplemental snapshot source only. They are not
    // treated as an authorized real-time quote feed, and no credentials are sent.
    private val downstoxCache = mutableMapOf<String, Pair<Long, String>>()

    private fun downstoxGet(path: String, params: Map<String, String> = emptyMap(), ttlMs: Long = 300_000L): JSONObject {
        if (!path.startsWith("/api/")) throw IOException("Downstox path is not an allowed public API path")
        val query = if (params.isEmpty()) "" else params.entries.joinToString("&", "?") {
            URLEncoder.encode(it.key, "UTF-8") + "=" + URLEncoder.encode(it.value, "UTF-8")
        }
        val key = path + query
        val now = System.currentTimeMillis()
        val cachedBody = synchronized(downstoxCache) {
            val cached = downstoxCache[key]
            if (cached != null && now >= cached.first && now - cached.first < ttlMs) cached.second
            else {
                downstoxCache.remove(key)
                null
            }
        }
        if (cachedBody != null) return JSONObject(cachedBody)

        val c = URL("https://downstox.com" + path + query).openConnection() as HttpURLConnection
        c.connectTimeout = 5000
        c.readTimeout = 8000
        c.requestMethod = "GET"
        c.setRequestProperty("Accept", "application/json")
        c.setRequestProperty("User-Agent", "PRO-STOCK-INTELLIGENCE/40.81 (Android public market-data supplement)")
        c.setRequestProperty("Cache-Control", "no-cache")
        try {
            val code = c.responseCode
            if (code !in 200..299) throw IOException("Downstox public API returned HTTP " + code + ". The snapshot may be unavailable or rate-limited.")
            val body = c.inputStream.bufferedReader(Charsets.UTF_8).use { it.readText() }
            if (body.length > 2_000_000) throw IOException("Downstox response exceeded the 2 MB safety limit")
            val root = JSONObject(body)
            if (!root.optBoolean("success", false)) throw IOException(root.optString("error", "Downstox public API did not report success"))
            synchronized(downstoxCache) { downstoxCache[key] = Pair(now, root.toString()) }
            return root
        } finally {
            c.disconnect()
        }
    }

    private fun downstoxFundamentals(raw: String): JSONObject {
        if (raw.trim().uppercase(Locale.ROOT).endsWith(".BO")) {
            throw IOException("Downstox public stock endpoint is documented for NSE symbols; BSE-selected symbols are not remapped.")
        }
        val symbol = canonical(raw)
        if (symbol.isBlank() || !symbol.matches(Regex("[A-Z0-9&_-]{1,25}"))) throw IOException("Invalid NSE symbol for Downstox lookup")
        val root = downstoxGet("/api/stocks/" + URLEncoder.encode(symbol, "UTF-8"), ttlMs = 900_000L)
        val stock = root.optJSONObject("stock") ?: throw IOException("Downstox stock payload is missing its stock object")
        if (canonical(stock.optString("symbol")) != symbol) throw IOException("Downstox returned a different symbol; supplemental fields rejected")
        val values = root.optJSONObject("fundamentals") ?: throw IOException("Downstox stock payload is missing fundamentals")
        val out = JSONObject()
            .put("symbol", symbol)
            .put("provider", "Downstox public fundamentals snapshot")
            .put("supplementProvider", "Downstox public API")
            .put("supplementStatus", "PARTIAL_PUBLIC_SNAPSHOT")
            .put("supplementTimestampStatus", "PER_STOCK_TIMESTAMP_NOT_SUPPLIED_BY_DOCUMENTED_SCHEMA")
            .put("sourceUrl", "https://downstox.com/api/stocks/" + symbol)
            .put("referencePriceSource", "Downstox public CMP reference (per-stock timestamp unavailable)")
            .put("referencePriceStatus", "PUBLIC_REFERENCE_NOT_LIVE_VERIFIED")
        val companyName = stock.optString("name").trim()
        if (companyName.isNotBlank()) out.put("name", companyName)
        val sector = root.optString("sector").trim()
        if (sector.isNotBlank()) out.put("sector", sector)

        val mappings = linkedMapOf(
            "pe" to "pe",
            "roe" to "roe",
            "roce" to "roce",
            "dividendYield" to "divYield",
            "bookValue" to "bookValue",
            "pb" to "priceToBook"
        )
        for ((target, source) in mappings) {
            val value = values.optDouble(source, Double.NaN)
            if (finite(value) && value > 0.0) out.put(target, value)
        }
        val cmp = values.optDouble("cmp", Double.NaN)
        if (finite(cmp) && cmp > 0.0) out.put("price", cmp)
        val fScore = values.optDouble("fScore", Double.NaN)
        if (finite(fScore) && fScore >= 0.0 && fScore <= 8.0) out.put("piotroski", fScore.toInt())
        // The public schema does not declare mcap units, quarterly/annual statement
        // periods, EPS, dividends by ex-date, or OHLCV history. Never infer those fields.
        return out
    }

    /**
     * NSE/Screener-only policy: Screener is the sole fundamentals source.
     * Never enrich missing fields from an unrelated third-party provider.
     * A missing field stays missing and retains the parser/source error.
     */
    private fun fundamentalsWithDownstox(raw: String): JSONObject {
        // A missing field stays missing. Shared read-through cache: every screen sees the same Screener snapshot.
        // Never cache authorization failures; a fresh login must be able to recover.
        val symbol = canonical(raw)
        val now = System.currentTimeMillis()
        fundamentalsCache[symbol]?.let { cached ->
            if (now - cached.fetchedAtMs in 0..fundamentalsCacheTtlMs) {
                return JSONObject(cached.payload).put("cacheStatus", "HIT")
                    .put("cacheAgeSeconds", ((now - cached.fetchedAtMs) / 1000L))
            } else fundamentalsCache.remove(symbol, cached)
        }
        return try {
            val fresh = screener(raw).apply {
                put("symbol", symbol)
                put("fundamentalSourcePolicy", "SCREENER_ONLY")
                put("cacheStatus", "MISS")
                put("fetchedAtEpochMs", System.currentTimeMillis())
                put("dataPeriodPolicy", "Provider-reported periods only; no inferred reporting period")
            }
            // Do not cache a response with no meaningful fundamentals or a provider error.
            val hasFundamentalData = fresh.keys().asSequence().any { key ->
                key !in setOf("symbol", "name", "sector", "provider", "sourceUrl", "fetchedAtEpochMs",
                    "fundamentalSourcePolicy", "cacheStatus", "dataPeriodPolicy", "sectionCoverage",
                    "fundamentalCoverage", "availableFundamentalFields", "expectedFundamentalFields",
                    "qualityFlags", "fundamentalStatus") && !fresh.isNull(key)
            }
            if (hasFundamentalData && !fresh.has("providerError")) {
                fundamentalsCache[symbol] = CachedFundamentals(fresh.toString(), System.currentTimeMillis())
            }
            fresh
        } catch (e: Exception) {
            JSONObject()
                .put("symbol", symbol)
                .put("name", stockName(symbol))
                .put("provider", "Screener.in unavailable")
                .put("providerError", e.message ?: "Screener.in unavailable")
                .put("fundamentalSourcePolicy", "SCREENER_ONLY")
                .put("cacheStatus", "BYPASS_ON_ERROR")
                .put("sourceStatus", if (screener403Observed) "HTTP_403_FORBIDDEN" else "UNAVAILABLE")
        }
    }

    private fun gatewayGet(path: String, params: Map<String, String> = emptyMap()): JSONObject {
        val base = gatewayBaseUrl()
        if (!base.startsWith("https://", ignoreCase = true)) {
            throw IOException("Authorized provider gateway is not configured. Set Gradle property providerGatewayBaseUrl to your HTTPS gateway URL; keep vendor credentials on the server.")
        }
        val urlText = base + path + if (params.isEmpty()) "" else params.entries.joinToString("&", "?") {
            URLEncoder.encode(it.key, "UTF-8") + "=" + URLEncoder.encode(it.value, "UTF-8")
        }
        val url = URL(urlText)
        if (url.host.isBlank() || urlText.substringAfter("://").substringBefore("/").contains("@")) throw IOException("Invalid provider gateway URL")
        var lastTransientError: IOException? = null
        for (attempt in 0..2) {
            val c = url.openConnection() as HttpURLConnection
            c.connectTimeout = 5000
            c.readTimeout = 8000
            c.requestMethod = "GET"
            c.setRequestProperty("Accept", "application/json")
            c.setRequestProperty("Cache-Control", "no-cache")
            try {
                val code = c.responseCode
                if (code == 401) throw IOException("Provider gateway returned HTTP 401 Unauthorized. Check the gateway service credentials.")
                if (code == 403) throw IOException("Provider gateway returned HTTP 403 Forbidden. Check account permissions; access controls will not be bypassed.")
                if (code == 429 || code in 500..599) {
                    val error = IOException("Provider gateway returned transient HTTP $code.")
                    if (attempt == 2) throw error
                    lastTransientError = error
                    val retryAfter = c.getHeaderField("Retry-After")?.toLongOrNull()?.coerceIn(0L, 2L)
                    val delayMs = (retryAfter?.times(1000L)) ?: (500L * (attempt + 1))
                    try {
                        Thread.sleep(delayMs)
                    } catch (interrupted: InterruptedException) {
                        Thread.currentThread().interrupt()
                        throw IOException("Provider gateway retry interrupted.", interrupted)
                    }
                    continue
                }
                if (code !in 200..299) throw IOException("Provider gateway returned HTTP $code. Check gateway health, authentication and vendor subscription.")
                val body = c.inputStream.bufferedReader(Charsets.UTF_8).use { it.readText() }
                if (body.length > 2_000_000) throw IOException("Provider gateway response exceeded the 2 MB safety limit")
                val parsed = try { JSONObject(body) } catch (malformed: org.json.JSONException) {
                    throw IOException("Provider gateway returned malformed JSON.", malformed)
                }
                if (parsed.optBoolean("ok", true) == false) throw IOException(parsed.optString("error", "Provider gateway reported unavailable data"))
                return parsed.optJSONObject("data") ?: parsed
            } catch (e: java.net.SocketTimeoutException) {
                if (attempt == 2) throw IOException("Provider gateway timed out after three attempts.", e)
                lastTransientError = IOException("Provider gateway timed out (attempt ${attempt + 1}/3).", e)
            } catch (e: java.net.SocketException) {
                if (attempt == 2) throw IOException("Provider gateway connection failed after three attempts.", e)
                lastTransientError = IOException("Provider gateway connection failed (attempt ${attempt + 1}/3).", e)
            } finally {
                c.disconnect()
            }
            try {
                Thread.sleep(500L * (attempt + 1))
            } catch (interrupted: InterruptedException) {
                Thread.currentThread().interrupt()
                throw IOException("Provider gateway retry interrupted.", interrupted)
            }
        }
        throw lastTransientError ?: IOException("Provider gateway request failed after bounded retries.")

    }

    private fun parseGatewayTime(value: String): Long {
        return try { java.time.OffsetDateTime.parse(value).toInstant().toEpochMilli() }
        catch (_: Exception) { throw IOException("Provider gateway timestamp must be ISO-8601 with timezone offset") }
    }

    private fun validatedGatewayQuote(raw: String): JSONObject {
        val symbol = canonical(raw)
        val data = gatewayGet("/v1/quote", mapOf("symbol" to symbol))
        if (canonical(data.optString("symbol")) != symbol) throw IOException("Provider gateway returned a different symbol; quote rejected")
        val source = data.optString("source").trim()
        val status = data.optString("marketDataStatus").uppercase(Locale.ROOT)
        val price = data.optDouble("price", Double.NaN)
        if (source.isBlank() || !price.isFinite() || price <= 0.0) throw IOException("Provider quote missing source or positive price")
        if (status !in setOf("REALTIME", "DELAYED", "EOD")) throw IOException("Provider quote missing valid REALTIME/DELAYED/EOD status")
        val asOf = parseGatewayTime(data.optString("asOf"))
        val ageMs = System.currentTimeMillis() - asOf
        if (ageMs < -60_000L) throw IOException("Provider quote timestamp is in the future; quote rejected")
        val maxAge = when (status) {
            "REALTIME" -> 5 * 60 * 1000L
            "DELAYED" -> {
                if (data.optInt("delayMinutes", 0) <= 0) throw IOException("Delayed quote must disclose delayMinutes")
                24 * 60 * 60 * 1000L
            }
            else -> 72 * 60 * 60 * 1000L
        }
        if (ageMs > maxAge) throw IOException("Provider quote is stale for its declared $status status; quote rejected")
        return JSONObject()
            .put("symbol", symbol).put("price", price).put("currency", data.optString("currency", "INR"))
            .put("provider", source).put("source", source).put("status", status)
            .put("marketDataStatus", status).put("quoteTimestamp", asOf / 1000L)
            .put("quoteAsOf", data.optString("asOf")).put("rows", JSONArray())
            .put("isExchangeCertifiedRealtime", false) // A gateway status claim is not proof of exchange certification.
            .put("marketDataDisclaimer", if (status == "REALTIME") "Provider-declared real-time quote; licensing and SLA must be verified at gateway." else "Quote is $status, not real-time. Use its disclosed timestamp and status.")
    }

    private fun nseQuote(raw: String): JSONObject {
        val symbol = canonical(raw)
        if (symbol.isBlank()) throw IOException("Enter a valid NSE equity symbol")
        if (!gatewayConfigured()) throw IOException("Authorized NSE/vendor gateway is not configured. Live price is unavailable; no website scraping or third-party fallback is used.")
        return validatedGatewayQuote(symbol)
    }

    private fun sectionTableRows(html: String, sectionId: String): List<List<String>> {
        // Screener sections are commonly nested divs. Stopping at the first </div>
        // truncates the section before its table and made quarterly/P&L/ownership look empty.
        // Locate the matching close tag for the exact id-bearing container instead.
        val open = Regex("(?is)<(section|div)\\b(?=[^>]*\\bid=[\"']" + Regex.escape(sectionId) + "[\"'])[^>]*>").find(html)
            ?: return emptyList()
        val tag = Regex("(?is)^<(section|div)\\b").find(open.value)?.groupValues?.getOrNull(1)?.lowercase(Locale.ROOT)
            ?: return emptyList()
        val token = Regex("(?is)</?"+tag+"\\b[^>]*>")
        var depth = 1
        var end = html.length
        for (m in token.findAll(html, open.range.last + 1)) {
            if (m.value.startsWith("</")) depth-- else if (!m.value.endsWith("/>")) depth++
            if (depth == 0) { end = m.range.first; break }
        }
        val section = html.substring(open.range.last + 1, end)
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
        // Screener's company page uses <ul id="top-ratios"> in some layouts.
        // Older code accepted only section/div, causing all valuation ratios to be dropped
        // even when the company page was fetched successfully.
        val ratioContainer = Regex("""(?is)<(section|div|ul|ol)\b[^>]*id=["']top-ratios["'][^>]*>(.*?)</\1>""")
            .find(html)
        val hasRatioSection = ratioContainer != null
        // Parse only the matched container; do not fall back to the entire document,
        // where repeated labels can create ambiguous duplicate values.
        val ratiosSectionHtml = ratioContainer?.groupValues?.get(2) ?: ""
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
            "pledged percentage" to "pledged", "pledged percent" to "pledged", "pledged" to "pledged", "pledge" to "pledged", "promoter pledge" to "pledged",
            "industry pb" to "industryPB", "industry p b" to "industryPB",
            "price to book value" to "pb", "stock p b" to "pb", "p b" to "pb",
            "sales growth 3years" to "sales3y", "sales growth 3 years" to "sales3y",
            "profit var 3yrs" to "profitVariance3y", "profit variance 3 years" to "profitVariance3y",
            "profit variance 3years" to "profitVariance3y", "profit growth 3years" to "profit3y",
            "profit growth 3 years" to "profit3y", "profit growth 3yr" to "profit3y",
            "profit growth 3 yrs" to "profit3y", "industry p e" to "industryPE",
            "industry pe ratio" to "industryPE", "piotroski" to "piotroski",
            "200 dma" to "dma200", "dma 200" to "dma200", "peg ratio" to "peg",
            "opm" to "opm", "rsi" to "rsi14"
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
        // Screener renders the 52-week range as one labelled value, e.g. "₹ 3,350 / 1,976".
        // Parse both numbers from that same row; do not infer them from other fields.
        val highLowRows = ratioItems.filter { item ->
            val label = Regex("(?is)<span\\b[^>]*class=[\\\"'][^\\\"']*\\bname\\b[^\\\"']*[\\\"'][^>]*>(.*?)</span>")
                .find(item)?.groupValues?.getOrNull(1)?.let { cleanText(it) } ?: return@filter false
            normalizeMetricLabel(label) in setOf("high low", "52 week high low", "52 week range")
        }
        if (highLowRows.size == 1) {
            val valueHtml = Regex("(?is)<span\\b[^>]*class=[\\\"'][^\\\"']*\\bnumber\\b[^\\\"']*[\\\"'][^>]*>(.*?)</span>")
                .find(highLowRows.single())?.groupValues?.getOrNull(1)
            val values = valueHtml?.let { cleanText(it) }?.let { text ->
                Regex("(?<![A-Za-z])(?:₹\\s*)?([0-9][0-9,]*(?:\\.[0-9]+)?)").findAll(text)
                    .mapNotNull { asNumber(it.groupValues[1]) }.toList()
            }.orEmpty()
            if (values.size == 2 && values[0] > 0 && values[1] > 0 && values[0] >= values[1]) {
                f.put("high52", values[0]).put("low52", values[1])
            }
        }

        val pnlRows = sectionTableRows(html, "profit-loss")
        val qRows = sectionTableRows(html, "quarters")
        val ownershipRows = sectionTableRows(html, "shareholding")
        val balanceRows = sectionTableRows(html, "balance-sheet")
        val cashFlowRows = sectionTableRows(html, "cash-flow")
        val ratioTableRows = sectionTableRows(html, "ratios")
        val peerRows = sectionTableRows(html, "peers")
        // Derive Industry P/E only from the actual peer table returned on this
        // company page. Never substitute the stock's own P/E or an unrelated sector average.
        fun normHeader(value: String): String = value.lowercase(Locale.ROOT).replace(Regex("[^a-z0-9]+"), " ").trim()
        if (!f.has("industryPE") && peerRows.size > 1) {
            val header = peerRows.first()
            val peColumn = header.indexOfFirst { normHeader(it) in setOf("stock p e", "p e", "pe", "price to earnings") }
            if (peColumn >= 0) {
                val peerPes = peerRows.drop(1).mapNotNull { row ->
                    row.getOrNull(peColumn)?.let { asNumber(it) }?.takeIf { it > 0.0 }
                }.sorted()
                if (peerPes.size >= 3) {
                    val mid = peerPes.size / 2
                    val median = if (peerPes.size % 2 == 0) (peerPes[mid - 1] + peerPes[mid]) / 2.0 else peerPes[mid]
                    if (median.isFinite() && median > 0.0) {
                        f.put("industryPE", median)
                        f.put("industryPEMethod", "Median P/E of valid peers in the Screener peer table; n=" + peerPes.size)
                        f.put("metricMeta", JSONObject().put("industryPE",
                            JSONObject().put("source", "Screener.in peer table").put("period", "Peer-table reporting period not labelled")))
                    }
                }
            }
        }
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
        // Piotroski F-score (0-9): calculate only when all nine inputs can be
        // be reconstructed from the same two annual reporting columns. Never publish
        // a partial score as a complete 0-9 result.
        fun annual(rows: List<List<String>>, labels: List<String>, col: Int): Double? {
            val row = rows.drop(1).firstOrNull { r ->
                val label = normHeader(r.firstOrNull().orEmpty())
                labels.any { label == normHeader(it) || label.startsWith(normHeader(it) + " ") }
            } ?: return null
            return row.getOrNull(col)?.let { asNumber(it) }
        }
        val salesNow = annual(pnlRows, listOf("Sales", "Revenue from Operations"), 1)
        val salesPrev = annual(pnlRows, listOf("Sales", "Revenue from Operations"), 2)
        val netNow = annual(pnlRows, listOf("Net Profit"), 1)
        val netPrev = annual(pnlRows, listOf("Net Profit"), 2)
        val opNow = annual(cashFlowRows, listOf("Cash from Operating Activity", "Cash Flow from Operating Activities", "Operating Cash Flow"), 1)
        val opPrev = annual(cashFlowRows, listOf("Cash from Operating Activity", "Cash Flow from Operating Activities", "Operating Cash Flow"), 2)
        val assetsNow = annual(balanceRows, listOf("Total Assets"), 1)
        val assetsPrev = annual(balanceRows, listOf("Total Assets"), 2)
        val currentAssetsNow = annual(balanceRows, listOf("Current Assets"), 1)
        val currentAssetsPrev = annual(balanceRows, listOf("Current Assets"), 2)
        val currentLiabNow = annual(balanceRows, listOf("Current Liabilities"), 1)
        val currentLiabPrev = annual(balanceRows, listOf("Current Liabilities"), 2)
        val debtNow = annual(balanceRows, listOf("Borrowings", "Long Term Borrowings", "Long Term Debt"), 1)
        val debtPrev = annual(balanceRows, listOf("Borrowings", "Long Term Borrowings", "Long Term Debt"), 2)
        val shareCapitalNow = annual(balanceRows, listOf("Share Capital"), 1)
        val shareCapitalPrev = annual(balanceRows, listOf("Share Capital"), 2)
        val grossNow = annual(pnlRows, listOf("Gross Profit"), 1)
        val grossPrev = annual(pnlRows, listOf("Gross Profit"), 2)
        val roaNow = if (netNow != null && assetsNow != null && assetsNow > 0) netNow / assetsNow else null
        val roaPrev = if (netPrev != null && assetsPrev != null && assetsPrev > 0) netPrev / assetsPrev else null
        val cfoPositive = opNow?.let { it > 0.0 }
        val cfoExceedsNet = if (opNow != null && netNow != null) opNow > netNow else null
        val roaImproved = if (roaNow != null && roaPrev != null) roaNow > roaPrev else null
        val leverageReduced = if (debtNow != null && debtPrev != null && assetsNow != null && assetsPrev != null && assetsNow > 0 && assetsPrev > 0)
            debtNow / assetsNow < debtPrev / assetsPrev else null
        val currentRatioImproved = if (currentAssetsNow != null && currentAssetsPrev != null && currentLiabNow != null && currentLiabPrev != null && currentLiabNow > 0 && currentLiabPrev > 0)
            currentAssetsNow / currentLiabNow > currentAssetsPrev / currentLiabPrev else null
        val noShareIssue = if (shareCapitalNow != null && shareCapitalPrev != null) shareCapitalNow <= shareCapitalPrev else null
        val grossMarginImproved = if (grossNow != null && grossPrev != null && salesNow != null && salesPrev != null && salesNow > 0 && salesPrev > 0)
            grossNow / salesNow > grossPrev / salesPrev else null
        val assetTurnoverImproved = if (salesNow != null && salesPrev != null && assetsNow != null && assetsPrev != null && assetsNow > 0 && assetsPrev > 0)
            salesNow / assetsNow > salesPrev / assetsPrev else null
        val piotroskiInputs = listOf(
            netNow?.let { it > 0.0 }, cfoPositive, roaImproved, cfoExceedsNet,
            leverageReduced, currentRatioImproved, noShareIssue, grossMarginImproved, assetTurnoverImproved
        )
        if (!f.has("piotroski") && piotroskiInputs.all { it != null }) {
            f.put("piotroski", piotroskiInputs.count { it == true })
            f.put("piotroskiMethod", "Calculated Piotroski F-score 0-9 from two consecutive annual Screener P&L, balance-sheet and cash-flow periods")
            f.put("metricMeta", JSONObject(f.optJSONObject("metricMeta")?.toString() ?: "{}").put("piotroski",
                JSONObject().put("source", "Calculated from Screener annual financial statements").put("period", "Latest two reported annual periods")))
        } else if (f.has("piotroski")) {
            // Prefer Screener's explicitly reported score; do not overwrite it with a
            // partial or differently-perioded reconstruction from annual statements.
            f.put("piotroskiMethod", "Reported directly by Screener company-page ratios")
            f.put("metricMeta", JSONObject(f.optJSONObject("metricMeta")?.toString() ?: "{}").put("piotroski",
                JSONObject().put("source", "Screener.in company-page top ratios").put("period", "Provider-reported; period not labelled")))
        } else {
            f.put("piotroskiStatus", "UNAVAILABLE_MISSING_REQUIRED_ANNUAL_INPUTS")
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
        // A transparent 3-year profit-variability measure: population standard
        // deviation divided by absolute mean, expressed as a percentage (CV).
        // It is only emitted when three consecutive annual values are present.
        rowFor(pnlRows, "Net Profit")?.drop(1)?.take(3)?.map { asNumber(it) }?.let { values ->
            if (values.size == 3 && values.all { it != null }) {
                val nums = values.filterNotNull()
                val mean = nums.average()
                if (mean != 0.0 && mean.isFinite()) {
                    val variance = nums.map { (it - mean) * (it - mean) }.average()
                    val cv = kotlin.math.sqrt(variance) / kotlin.math.abs(mean) * 100.0
                    if (cv.isFinite()) f.put("profitVariance3y", cv)
                    f.put("profitVarianceMethod", "3-year population standard deviation / absolute mean × 100")
                }
            }
        }
        // PEG must use EPS growth, not profit growth. Profit growth can diverge
        // materially from per-share growth because of dilution/buybacks and is not a
        // valid substitute. Preserve Screener's reported PEG; derive only from EPS CAGR.
        if (!f.has("peg")) {
            val growth = f.optDouble("eps3y", Double.NaN).takeIf { it.isFinite() && it > 0.0 }
            val pe = f.optDouble("pe", Double.NaN)
            if (growth != null && pe.isFinite() && pe > 0.0) {
                f.put("peg", pe / growth)
                f.put("pegMethod", "P/E divided by 3-year EPS CAGR (%)")
            } else {
                f.put("pegStatus", "UNAVAILABLE_REQUIRES_POSITIVE_EPS_CAGR")
            }
        }
        // Derived ratios must use the newest fiscal column; never skip a blank latest cell.
        val currentAssets = rowFor(balanceRows, "Current Assets")?.getOrNull(1)?.let { asNumber(it) }
        val currentLiabilities = rowFor(balanceRows, "Current Liabilities")?.getOrNull(1)?.let { asNumber(it) }
        if (currentAssets != null && currentLiabilities != null && currentLiabilities > 0) f.put("currentRatio", currentAssets / currentLiabilities)
        val latestOperating = rowFor(pnlRows, "Operating Profit")?.getOrNull(1)?.let { asNumber(it) }
        val latestInterest = rowFor(pnlRows, "Interest")?.getOrNull(1)?.let { asNumber(it) }
        if (latestOperating != null && latestInterest != null && latestInterest > 0) f.put("interestCoverage", latestOperating / latestInterest)
        if (pnlRows.isNotEmpty()) f.put("pnl", jsonRows(pnlRows))
        if (balanceRows.isNotEmpty()) f.put("balanceSheet", jsonRows(balanceRows))
        if (cashFlowRows.isNotEmpty()) f.put("cashFlow", jsonRows(cashFlowRows))
        if (ratioTableRows.isNotEmpty()) f.put("ratios", jsonRows(ratioTableRows))
        if (peerRows.isNotEmpty()) f.put("peerComparison", jsonRows(peerRows))
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
                    // Screener may label this as promoter pledge/pledged shares/encumbered.
                    if (label.contains("pledg") || label.contains("encumber")) f.put("pledged", n)
                }
            }
        }
        val fetchedAt = System.currentTimeMillis()
        val fieldKeys = listOf("price", "marketCap", "pe", "industryPE", "peg", "pb", "industryPB", "faceValue", "piotroski", "dma50", "dma200", "promoter", "public", "pledged", "bookValue", "dividendYield", "roce", "roe", "debtEquity", "eps", "netProfit", "operatingProfit", "opm", "sales3y", "profit3y", "profitVariance3y", "eps3y", "currentRatio", "interestCoverage", "rsi14", "high52", "low52", "quarterly", "shareholding", "pnl", "balanceSheet", "cashFlow", "ratios", "peerComparison")
        val available = fieldKeys.count { f.has(it) && !f.isNull(it) && (f.optJSONArray(it)?.length() ?: 1) > 0 }
        val sectionCoverage = JSONObject()
            .put("profitLoss", pnlRows.isNotEmpty())
            .put("quarterly", qRows.isNotEmpty())
            .put("balanceSheet", balanceRows.isNotEmpty())
            .put("cashFlow", cashFlowRows.isNotEmpty())
            .put("shareholding", ownershipRows.isNotEmpty())
            .put("financialRatios", ratioTableRows.isNotEmpty())
            .put("peerComparison", peerRows.isNotEmpty())
        f.put("sectionCoverage", sectionCoverage)
        val qualityFlags = JSONArray()
        if (available < 6) qualityFlags.put("LOW_FUNDAMENTAL_COVERAGE")
        if (!f.has("pe")) qualityFlags.put("PE_UNAVAILABLE_OR_NON_POSITIVE")
        if (!f.has("eps")) qualityFlags.put("EPS_UNAVAILABLE")
        if (!f.has("roce")) qualityFlags.put("ROCE_UNAVAILABLE")
        f.put("name", pageTitle).put("symbol", s).put("sector", stockSector(s)).put("provider", "Screener.in")
            .put("sourceUrl", pageUrl).put("fetchedAtEpochMs", fetchedAt)
            .put("reportingPeriodStatus", "Provider-reported periods are retained in source tables; top-ratio fields have no explicit period unless metricMeta supplies one")
            .put("fundamentalStatus", if (available >= 6) "PAGE_VALIDATED_PARTIAL_FIELDS_MAY_BE_MISSING" else "PAGE_VALIDATED_LOW_COVERAGE")
            .put("availableFundamentalFields", available).put("expectedFundamentalFields", fieldKeys.size)
            .put("qualityFlags", qualityFlags)
        return f
    }

    /** Batch audit uses the user's existing in-app Screener session; no credentials leave the device. */
    private fun screenerAudit30(): JSONObject {
        val symbols = listOf("RELIANCE","TCS","HDFCBANK","ICICIBANK","INFY","SBIN","BHARTIARTL","ITC","LT","BAJFINANCE",
            "HINDUNILVR","MARUTI","SUNPHARMA","TITAN","NTPC","POWERGRID","AXISBANK","KOTAKBANK","TATASTEEL","ONGC",
            "M&M","WIPRO","HCLTECH","TECHM","ULTRACEMCO","ASIANPAINT","BEL","HAL","TRENT","ADANIPORTS")
        val rows = JSONArray()
        var blocked = false
        var successfulPages = 0
        for (symbol in symbols) {
            val fetchedAt = System.currentTimeMillis()
            val row = JSONObject().put("symbol", symbol).put("source", "Screener.in company page")
                .put("sourceUrl", "https://www.screener.in/company/$symbol/").put("fetchedAtEpochMs", fetchedAt)
            try {
                if (blocked || screener403Observed) throw IOException("Screener access blocked; remaining requests stopped")
                val f = screener(symbol)
                successfulPages++
                val metricKeys = listOf("industryPE", "piotroski", "peg", "pledged")
                val metrics = JSONObject()
                metricKeys.forEach { key ->
                    val value = if (f.has(key) && !f.isNull(key)) f.opt(key) else JSONObject.NULL
                    val meta = f.optJSONObject("metricMeta")?.optJSONObject(key) ?: JSONObject()
                    metrics.put(key, JSONObject().put("value", value)
                        .put("status", if (value !== JSONObject.NULL) "PAGE_VALUE_PARSED" else "UNAVAILABLE_NOT_REPORTED")
                        .put("source", meta.optString("source", "Screener.in company page"))
                        .put("period", meta.optString("period", f.optString("reportingPeriodStatus", "PERIOD_NOT_LABELLED")))
                        .put("unit", when(key) { "industryPE","peg" -> "ratio"; "piotroski" -> "score_0_to_9"; else -> "percent" })
                        .put("method", f.optString(key + "Method", "Reported directly by Screener where present")))
                }
                row.put("name", f.optString("name", symbol)).put("status", f.optString("fundamentalStatus", "PAGE_VALIDATED"))
                    .put("metrics", metrics).put("availableMetricCount", metricKeys.count { f.has(it) && !f.isNull(it) })
            } catch (e: Exception) {
                val message = e.message ?: "Screener request failed"
                if (message.contains("403") || screener403Observed) blocked = true
                row.put("status", if (blocked) "ACCESS_BLOCKED_403" else "FETCH_FAILED")
                    .put("error", message).put("metrics", JSONObject().put("industryPE", JSONObject().put("status","UNAVAILABLE"))
                        .put("piotroski", JSONObject().put("status","UNAVAILABLE"))
                        .put("peg", JSONObject().put("status","UNAVAILABLE"))
                        .put("pledged", JSONObject().put("status","UNAVAILABLE")))
            }
            rows.put(row)
            if (blocked) break
        }
        return JSONObject().put("source", "Screener.in authenticated company-page requests")
            .put("startedAtEpochMs", System.currentTimeMillis()).put("requestedStocks", symbols.size)
            .put("attemptedStocks", rows.length()).put("successfulPages", successfulPages)
            .put("accessBlocked", blocked).put("complete", rows.length() == symbols.size && !blocked)
            .put("metrics", JSONArray().put("industryPE").put("piotroski").put("peg").put("pledged"))
            .put("rows", rows).put("note", "A page response validates only fields parsed on that page. Missing values remain unavailable; reporting periods are never inferred.")
    }

    private fun screenerCookieHeader(): String {
        // Match the same canonical host/path used by screener(raw). Never combine
        // cookies from www and bare-domain jars: duplicate sessionid values can
        // make status checks look authenticated while the actual request is denied.
        return CookieManager.getInstance()
            .getCookie("https://www.screener.in/company/INFY/")
            .orEmpty()
            .split(";")
            .map { it.trim() }
            .filter { it.contains("=") && !it.startsWith("=") }
            .joinToString("; ")
    }

    private fun screenerLoggedIn(): Boolean {
        // Cookie presence is only a pre-check; protected requests still validate the session.
        return screenerCookieHeader().split(";").any {
            it.trim().substringBefore("=").equals("sessionid", ignoreCase = true) &&
                it.substringAfter("=", "").isNotBlank()
        }
    }
    private fun screenerStatus(): JSONObject {
        val cookieDetected = screenerLoggedIn()
        val blocked = screener403Observed
        val validated = screenerSessionIsValidated()
        val message = when {
            blocked -> "Screener denied the app request (HTTP 403). Sign in again on the official Screener page inside the app and run one access check; automated retries are disabled."
            validated -> "Screener session validated successfully in this app. Fundamental fields are still checked individually for coverage and freshness."
            cookieDetected -> "Screener session cookie found. Checking access once against a company page before using fundamentals."
            else -> "Tap Connect Screener to open the official login page. Sign in there; the app will check the session when you return."
        }
        return JSONObject().put("connected", validated).put("loggedIn", cookieDetected).put("sessionAuthenticated", false).put("cookieDetected", cookieDetected)
            .put("blockedBy403", blocked).put("validated", validated).put("requestValidated", validated)
            .put("status", if (blocked) "HTTP_403_FORBIDDEN" else if (validated) "CONNECTED_VERIFIED" else if (cookieDetected) "SESSION_UNVERIFIED" else "LOGIN_REQUIRED")
            .put("httpStatus", if (blocked) 403 else if (validated) 200 else JSONObject.NULL)
            .put("recommendedAction", if (blocked) "Reopen official Screener login inside the app and check access once; no CSV workaround is required or used for automatic metrics." else if (validated) "Select a stock to load available Screener fundamentals automatically." else "Sign in through the official page inside the app; return and check access once.")
            .put("loginUrl", "https://www.screener.in/login/")
            .put("validationExpiresInSeconds", if (validated) ((30L * 60L * 1000L - (System.currentTimeMillis() - screenerSessionValidatedAtMs)).coerceAtLeast(0L) / 1000L) else 0)
            .put("message", message)
    }

    private fun screenerConnectionTest(): JSONObject {
        return try {
            // A public company page can load without an account. Never report a valid
            // session unless the session cookie exists before the protected-page probe.
            if (!screenerLoggedIn()) throw IOException("LOGIN_REQUIRED: no Screener session cookie detected. Open the official login page, sign in, return, and test again.")
            // Use the same company-page path and parser as normal fundamentals retrieval.
            val sample = screener("INFY")
            screenerSessionValidatedAtMs = System.currentTimeMillis()
            screener403Observed = false
            val status = screenerStatus()
            status.put("connected", true).put("loggedIn", true).put("validated", true)
                .put("requestValidated", true).put("httpStatus", 200)
                .put("status", "CONNECTED_VERIFIED")
                .put("sessionAuthenticated", false)
                .put("message", "Screener session cookie was present and the INFY company-page request succeeded. Subscription-only access is not proven by this public-page probe; use the permitted workbook import for protected or unavailable sections. Every field remains subject to coverage and period checks.")
                .put("accessLevel", "PUBLIC_PAGE_WITH_SESSION_COOKIE")
                .put("subscriptionAccessVerified", false)
                .put("sampleSymbol", "INFY")
                .put("sampleFieldCount", sample.keys().asSequence().count { it !in setOf("name", "symbol", "sector", "provider", "sourceUrl", "fetchedAtEpochMs", "fundamentalStatus", "availableFundamentalFields", "expectedFundamentalFields", "qualityFlags") })
            status
        } catch (e: Exception) {
            val status = screenerStatus()
            val blocked = screener403Observed || e.message.orEmpty().contains("403")
            if (blocked || !screenerLoggedIn()) screenerSessionValidatedAtMs = 0L
            status.put("connected", false).put("loggedIn", false).put("validated", false)
                .put("requestValidated", false).put("blockedBy403", blocked)
                .put("status", if (blocked) "HTTP_403_FORBIDDEN" else if (!screenerLoggedIn()) "LOGIN_REQUIRED" else "CONNECTION_FAILED")
                .put("httpStatus", if (blocked) 403 else JSONObject.NULL)
                .put("message", if (blocked) "Screener returned HTTP 403. Sign in through the official page inside the app and check once. If it persists, automated access is denied; no CSV workaround is used for these metrics." else e.message ?: "Screener connection test failed.")
                .put("recommendedAction", if (blocked) "Reopen official Screener login inside the app and check access once; no CSV workaround is required or used for automatic metrics." else "Open official Screener login inside the app, sign in, return, then test once.")
        }
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
                    .put("status", if ((e.message ?: "").contains("HTTP 403", ignoreCase = true)) "HTTP_403_FORBIDDEN" else "LIVE_VALIDATION_FAILED")
                    .put("httpStatus", if ((e.message ?: "").contains("HTTP 403", ignoreCase = true)) 403 else JSONObject.NULL)
                    .put("validationDurationMs", System.currentTimeMillis() - probeStarted)
                    .put("errorType", e.javaClass.simpleName)
                    .put("message", e.message ?: "Live Screener request did not validate. No live fundamentals should be claimed from this probe.")
                    .put("recommendedAction", if ((e.message ?: "").contains("HTTP 403", ignoreCase = true)) "Use permitted Screener CSV export in Data Sources / CSV, or configure an officially authorized API/data provider. Do not retry automated scraping." else "Verify the signed-in account, company symbol and network, then retry once.")
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
            .put("AuthorizedProviderGateway", JSONObject()
                .put("configured", gatewayConfigured())
                .put("baseUrlConfigured", gatewayConfigured())
                .put("credentialsInApk", false)
                .put("requiredRoutes", JSONArray().put("/v1/quote").put("/v1/history").put("/v1/indices").put("/v1/events").put("/v1/dividends"))
                .put("status", if (gatewayConfigured()) "URL_CONFIGURED_LIVE_HEALTH_CHECK_PENDING" else "NOT_CONFIGURED")
                .put("message", if (gatewayConfigured()) "HTTPS gateway URL configured. Actual quote/history/event payloads are validated when requested." else "Configure Gradle property providerGatewayBaseUrl and deploy a licensed provider adapter. Vendor credentials must remain server-side."))
            .put("overall", when { gatewayConfigured() && screener.optBoolean("requestValidated", false) -> "GATEWAY_URL_CONFIGURED_SCREENER_VALIDATED_GATEWAY_HEALTH_UNVERIFIED"; gatewayConfigured() -> "GATEWAY_URL_CONFIGURED_NOT_HEALTH_CHECKED"; screener.optBoolean("requestValidated", false) -> "SCREENER_VALIDATED_AUTHORIZED_GATEWAY_NOT_CONFIGURED"; else -> "PARTIAL_PROVIDER_COVERAGE_NOT_ALL_SOURCES_LIVE" })
    }

    private fun coreCoverage(f: JSONObject): JSONObject {
        val keys = arrayOf("marketCap", "pe", "roce", "roe", "debtEquity", "eps", "bookValue",
            "netProfit", "operatingProfit", "dividendYield", "promoter", "public", "high52", "low52")
        val fields = JSONObject()
        var count = 0
        keys.forEach { key ->
            val present = f.has(key) && !f.isNull(key)
            fields.put(key, present)
            if (present) count++
        }
        val sections = f.optJSONObject("sectionCoverage") ?: JSONObject()
        return JSONObject()
            .put("coreFields", count)
            .put("coreTotal", keys.size)
            .put("fields", fields)
            .put("sections", sections)
            .put("coveragePercent", if (keys.isEmpty()) 0 else (count * 100 / keys.size))
    }

    private fun combined(raw: String, includeFundamentals: Boolean): JSONObject {
        val s = canonical(raw)
        // Keep quote/history independent from Screener fundamentals. Only an
        // authorized HTTPS gateway or validated official NSE EOD bundle is accepted.
        // Yahoo Finance and Moneycontrol are deliberately not quote/chart providers.
        val executor = Executors.newFixedThreadPool(2)
        val quoteFuture = executor.submit<JSONObject> {
            try {
                if (gatewayConfigured()) nseQuote(raw) else eodQuote(raw)
            } catch (e: Exception) {
                JSONObject().put("symbol", s)
                    .put("provider", "Unavailable")
                    .put("status", if (gatewayConfigured()) "PROVIDER_GATEWAY_VALIDATION_FAILED" else "OFFICIAL_NSE_EOD_UNAVAILABLE")
                    .put("rows", JSONArray())
                    .put("historyProvider", "Unavailable")
                    .put("historyStatus", "HISTORICAL_DATA_UNAVAILABLE")
                    .put("providerError", e.message ?: "Market data unavailable")
                    .put("marketDataDisclaimer", "No bundled official NSE EOD close exists and no authorized live feed is configured. No third-party fallback is used; Yahoo/Moneycontrol fallback is disabled. No price or candle is fabricated.")
            }
        }
        val fundamentalFuture = executor.submit<JSONObject> {
            fundamentalsWithDownstox(raw)
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
                // Never promote Screener's displayed/last-close price into an exchange-live quote.
                // Preserve it separately as a reference value so the UI cannot label it as CMP/live.
                if (k == "price") {
                    if (!quote.has("price") && !f.isNull(k)) {
                        market.put("screenerReferencePrice", f.get(k))
                        market.put("referencePriceSource", f.optString("referencePriceSource", f.optString("provider", "Screener.in")))
                        market.put("referencePriceStatus", f.optString("referencePriceStatus", "REFERENCE_ONLY_NOT_LIVE"))
                    }
                } else if (k != "providerError") {
                    market.put(k, f.get(k))
                }
            }
        }
        // Yahoo chart responses expose daily candles as historyRows; the authorized
        // gateway exposes rows. Normalize both shapes once so chart and indicators use
        // the exact same validated OHLCV series. Fall back only to bundled official NSE EOD.
        val rows = quote.optJSONArray("rows")
            ?: quote.optJSONArray("historyRows")
            ?: readBundledNseEod(s)
        quote.put("rows", rows)
        // Calculate technical metrics from the same daily OHLCV series used by the chart.
        // Require 200 closes for 200-DMA; do not estimate missing history.
        val closes = (0 until rows.length()).mapNotNull { index ->
            rows.optJSONObject(index)?.optDouble("close", Double.NaN)?.takeIf { it.isFinite() && it > 0.0 }
        }
        if (closes.size >= 50) {
            val dma50 = closes.takeLast(50).average()
            if (dma50.isFinite() && dma50 > 0.0) {
                market.put("dma50", dma50)
                market.put("dma50Source", quote.optString("historyProvider", quote.optString("provider", "Daily OHLCV")))
            }
        }
        if (closes.size >= 200) {
            val dma200 = closes.takeLast(200).average()
            if (dma200.isFinite() && dma200 > 0.0) {
                market.put("dma200", dma200)
                market.put("dma200Source", quote.optString("historyProvider", quote.optString("provider", "Daily OHLCV")))
            }
        }
        if (closes.size >= 15) {
            val changes = closes.zipWithNext { a, b -> b - a }
            val seed = changes.take(14)
            var averageGain = seed.map { maxOf(it, 0.0) }.average()
            var averageLoss = seed.map { maxOf(-it, 0.0) }.average()
            for (change in changes.drop(14)) {
                averageGain = ((averageGain * 13.0) + maxOf(change, 0.0)) / 14.0
                averageLoss = ((averageLoss * 13.0) + maxOf(-change, 0.0)) / 14.0
            }
            val rsi = if (averageLoss == 0.0) 100.0 else 100.0 - (100.0 / (1.0 + averageGain / averageLoss))
            if (rsi.isFinite()) market.put("rsi14", rsi)
            market.put("technicalMetricsSource", quote.optString("historyProvider", quote.optString("provider", "Daily OHLCV")))
        }
        if (includeFundamentals) {
            if (market.has("dma50")) f.put("dma50", market.get("dma50"))
            if (market.has("dma200")) f.put("dma200", market.get("dma200"))
            if (market.has("rsi14")) f.put("rsi14", market.get("rsi14"))
        }
        val history = JSONObject().put("rows", rows).put("provider", quote.optString("historyProvider", "Unavailable")).put("historyStatus", quote.optString("historyStatus", "AUTHORIZED_NSE_HISTORICAL_FEED_NOT_CONFIGURED"))
        val hasFundamentals = arrayOf("marketCap", "pe", "roce", "roe", "debtEquity", "eps", "bookValue").any { f.has(it) && !f.isNull(it) }
        val selectedExchange = when { raw.trim().uppercase(Locale.ROOT).endsWith(".BO") -> "BSE"; raw.trim().uppercase(Locale.ROOT).endsWith(".NS") -> "NSE"; else -> "NSE primary; BSE availability varies" }
        market.put("exchange", selectedExchange)
        val data = JSONObject().put("symbol", s).put("exchange", selectedExchange).put("name", f.optString("name", stockName(s)))
            .put("quote", quote).put("market", market).put("fundamentals", f).put("history", history)
            .put("ohlcv", rows).put("technicalSeries", rows)
            .put("dataConfidence", when { quote.has("price") && hasFundamentals -> "PARTIAL — VERIFY SOURCE/TIMESTAMP"; quote.has("price") -> "QUOTE AVAILABLE — NOT GUARANTEED REAL-TIME"; hasFundamentals -> "FUNDAMENTALS ONLY — SCREENER PRICE IS REFERENCE ONLY"; else -> "UNAVAILABLE" })
            .put("dataSources", JSONObject().put("Quote", if (quote.has("providerError")) "UNAVAILABLE" else quote.optString("provider", "Unknown"))
                .put("History", quote.optString("historyProvider", "Unavailable"))
                .put("Moneycontrol", "NOT INTEGRATED — NO VERIFIED ACCESS/FEED CONFIGURED")
                .put("NSE", if (quote.optString("provider").startsWith("NSE")) "PUBLIC WEBSITE ENDPOINT (NOT LICENSED FEED)" else quote.optString("nseProviderWarning", "UNAVAILABLE"))
                .put("Screener.in", when {
                    f.has("screenerProviderError") -> "Unavailable/partial: " + f.optString("screenerProviderError")
                    f.has("providerError") -> "UNAVAILABLE: " + f.optString("providerError")
                    else -> "Screener.in page parsed; field freshness/accuracy still requires verification"
                })
                .put("Downstox", when {
                    f.has("supplementProvider") -> "Public fundamentals snapshot; timestamp and field completeness unverified"
                    f.has("downstoxSupplementError") -> "Supplement unavailable: " + f.optString("downstoxSupplementError")
                    else -> "Not used; Screener coverage sufficient or NSE/BSE selection unsupported"
                }))
            .put("quoteQuality", quote.optString("quoteQuality", "UNVERIFIED")).put("quoteTimestampStatus", quote.optString("quoteTimestampStatus", "UNVERIFIED_NO_PROVIDER_QUOTE_TIMESTAMP")).put("fundamentalCoverage", coreCoverage(f))
        val warnings = JSONArray()
        if (quote.has("providerError")) warnings.put(quote.optString("providerError"))
        if (f.has("providerError")) warnings.put(f.optString("providerError"))
        if (f.has("screenerProviderError")) warnings.put("Screener.in partial/unavailable: " + f.optString("screenerProviderError"))
        if (f.has("downstoxSupplementError")) warnings.put("Downstox supplement unavailable: " + f.optString("downstoxSupplementError"))
        if (warnings.length() > 0) data.put("providerWarnings", warnings)
        // Canonical read model consumed by every UI surface. Quote and fundamentals
        // remain separately attributed, while the merged market object is the one
        // source of truth for dashboard, scoring, peer views and filters.
        val normalizedMarket = JSONObject(market.toString())
        val normalizedFundamentals = JSONObject(f.toString())
        val normalizedFinancials = JSONObject()
            .put("profitLoss", f.optJSONArray("pnl") ?: JSONArray())
            .put("quarterly", f.optJSONArray("quarterly") ?: JSONArray())
            .put("balanceSheet", f.optJSONArray("balanceSheet") ?: JSONArray())
            .put("cashFlow", f.optJSONArray("cashFlow") ?: JSONArray())
            .put("ratios", f.optJSONArray("ratios") ?: JSONArray())
            .put("shareholding", f.optJSONArray("shareholding") ?: JSONArray())
            .put("peers", f.optJSONArray("peerComparison") ?: JSONArray())
        data.put("normalizedData", JSONObject()
            .put("schemaVersion", 1)
            .put("symbol", s)
            .put("market", normalizedMarket)
            .put("fundamentals", normalizedFundamentals)
            .put("financials", normalizedFinancials)
            .put("coverage", coreCoverage(f))
            .put("dataSources", data.optJSONObject("dataSources") ?: JSONObject())
            .put("generatedAtEpochMs", System.currentTimeMillis()))
        return data
    }

    private fun historyData(raw: String, range: String): JSONObject {
        val symbol = canonical(raw)
        if (gatewayConfigured()) {
            val data = gatewayGet("/v1/history", mapOf("symbol" to symbol, "range" to range))
            if (canonical(data.optString("symbol")) != symbol) throw IOException("History provider returned a different symbol; candles rejected")
            val source = data.optString("source").trim()
            val asOf = parseGatewayTime(data.optString("asOf"))
            val historyAgeMs = System.currentTimeMillis() - asOf
            if (historyAgeMs < -60_000L || historyAgeMs > 10L * 24 * 60 * 60 * 1000)
                throw IOException("Historical provider timestamp is in the future or too old to verify")
            val interval = data.optString("interval")
            if (source.isBlank() || interval !in setOf("1m", "5m", "15m", "1d", "1wk", "1mo")) throw IOException("History payload missing source or valid interval")
            val inputRows = data.optJSONArray("rows") ?: throw IOException("History payload missing OHLCV rows")
            val rows = JSONArray()
            var previousTime = Long.MIN_VALUE
            for (i in 0 until inputRows.length()) {
                val row = inputRows.optJSONObject(i) ?: continue
                val time = parseGatewayTime(row.optString("time"))
                val o = row.optDouble("open", Double.NaN); val h = row.optDouble("high", Double.NaN)
                val l = row.optDouble("low", Double.NaN); val c = row.optDouble("close", Double.NaN)
                val v = row.optDouble("volume", Double.NaN)
                if (time <= previousTime || !o.isFinite() || !h.isFinite() || !l.isFinite() || !c.isFinite() ||
                    o <= 0 || h <= 0 || l <= 0 || c <= 0 || h < maxOf(o, c, l) || l > minOf(o, c, h) || !v.isFinite() || v < 0) continue
                rows.put(JSONObject().put("time", time).put("date", time).put("open", o).put("high", h).put("low", l).put("close", c).put("volume", v))
                previousTime = time
            }
            if (rows.length() < 2) throw IOException("Provider history must contain at least two valid chronological OHLCV candles; partial or malformed history rejected")
            return JSONObject().put("symbol", symbol).put("rows", rows).put("provider", source)
                .put("historyProvider", source).put("historyStatus", "VALIDATED_GATEWAY_PAYLOAD")
                .put("chartMode", "OHLCV").put("statusText", "Provider OHLCV • as of " + data.optString("asOf"))
                .put("rangeRequested", range).put("interval", interval).put("quoteTimestamp", asOf / 1000L)
        }
        val localRows = readBundledNseEod(symbol)
        if (localRows.length() >= 2) {
            val latest = localRows.optJSONObject(localRows.length() - 1)
            val latestTime = latest?.optLong("time", 0L) ?: 0L
            return JSONObject().put("symbol", symbol).put("rows", localRows)
                .put("provider", "NSE CM-UDiFF Common Bhavcopy Final")
                .put("historyProvider", "NSE official EOD bhavcopy bundled with app")
                .put("historyStatus", "VALIDATED_OFFICIAL_NSE_EOD")
                .put("marketDataStatus", "EOD").put("chartMode", "OHLCV")
                .put("statusText", "Official NSE daily OHLCV • EOD only • latest session " + (latest?.optString("tradingDate") ?: "unknown"))
                .put("rangeRequested", range).put("interval", "1d")
                .put("quoteTimestamp", if (latestTime > 0L) latestTime / 1000L else JSONObject.NULL)
                .put("sourceDisclaimer", "Daily closing data from official NSE CM-UDiFF Bhavcopy. Not live or intraday.")
        }
        return JSONObject().put("symbol", symbol).put("rows", localRows)
            .put("provider", "Unavailable").put("historyStatus", "NSE_EOD_HISTORY_NOT_BUNDLED")
            .put("chartMode", "OHLCV")
            .put("statusText", "No bundled NSE EOD history for this symbol yet. Run the official NSE EOD ingestion workflow; live/intraday data is not included.")
            .put("rangeRequested", range).put("quoteTimestamp", JSONObject.NULL)
    }

    /** Read only validated NSE EQ bhavcopy files copied into assets by the release workflow. */
    private fun readBundledNseEod(symbol: String): JSONArray {
        val byDate = sortedMapOf<String, JSONObject>()
        val files = try { appAssets.list("nse-eod") ?: emptyArray() } catch (_: Exception) { emptyArray() }
        for (file in files.filter { it.endsWith(".csv", true) }.sorted()) {
            try {
                appAssets.open("nse-eod/$file").bufferedReader(Charsets.UTF_8).useLines { lines ->
                    val iterator = lines.iterator()
                    if (!iterator.hasNext()) return@useLines
                    // Strip UTF-8 BOM and normalize headers so an otherwise valid NSE file
                    // is not silently ignored because of BOM/case/whitespace differences.
                    val header = iterator.next().removePrefix("\uFEFF").split(',').map { it.trim().trim('"').lowercase(Locale.ROOT) }
                    val index = header.withIndex().associate { it.value to it.index }
                    val required = listOf("symbol", "date", "open", "high", "low", "close", "volume", "marketdatastatus")
                    if (required.any { !index.containsKey(it) }) return@useLines
                    while (iterator.hasNext()) {
                        val cells = iterator.next().split(',')
                        fun field(name: String): String = cells.getOrNull(index[name.lowercase(Locale.ROOT)] ?: -1)?.trim()?.trim('"').orEmpty()
                        // Fail closed: field("marketDataStatus") != "EOD" rows are never accepted.
                        if (field("symbol").uppercase(Locale.ROOT) != symbol || field("marketDataStatus").uppercase(Locale.ROOT) != "EOD") continue
                        val day = field("date").take(10)
                        val date = try { java.time.LocalDate.parse(day) } catch (_: Exception) { continue }
                        val o = field("open").replace(",", "").toDoubleOrNull() ?: continue
                        val h = field("high").replace(",", "").toDoubleOrNull() ?: continue
                        val l = field("low").replace(",", "").toDoubleOrNull() ?: continue
                        val c = field("close").replace(",", "").toDoubleOrNull() ?: continue
                        val v = field("volume").replace(",", "").toDoubleOrNull() ?: continue
                        if (listOf(o,h,l,c,v).any { !it.isFinite() } || minOf(o,h,l,c) <= 0.0 || v < 0.0 || h < maxOf(o,c,l) || l > minOf(o,c,h)) continue
                        val epoch = date.atStartOfDay(java.time.ZoneOffset.UTC).toInstant().toEpochMilli()
                        byDate[day] = JSONObject().put("time", epoch).put("date", epoch).put("tradingDate", day)
                            .put("open", o).put("high", h).put("low", l).put("close", c).put("volume", v)
                            .put("marketDataStatus", "EOD").put("source", "NSE CM-UDiFF Common Bhavcopy Final")
                    }
                }
            } catch (_: Exception) {
                // A malformed or inaccessible bundled file is skipped; never synthesize candles.
            }
        }
        return JSONArray().apply { byDate.values.forEach { put(it) } }
    }

    // No unlicensed third-party quote/chart adapters are retained. Quotes and candles
    // come only from the authorized gateway or validated official NSE EOD bundle.

    private fun eodQuote(raw: String): JSONObject {
        val symbol = canonical(raw)
        val history = readBundledNseEod(symbol)
        if (history.length() == 0) throw IOException("No bundled official NSE EOD close exists for $symbol")
        val last = history.optJSONObject(history.length() - 1) ?: throw IOException("Latest NSE EOD row is invalid")
        val previous = if (history.length() > 1) history.optJSONObject(history.length() - 2) else null
        val close = last.optDouble("close", Double.NaN)
        if (!close.isFinite() || close <= 0.0) throw IOException("Latest NSE EOD close is invalid")
        val out = JSONObject().put("symbol", symbol).put("price", close).put("currency", "INR")
            .put("provider", "NSE CM-UDiFF Common Bhavcopy Final").put("source", "NSE official EOD bhavcopy")
            .put("status", "EOD").put("marketDataStatus", "EOD")
            .put("quoteTimestamp", last.optLong("time") / 1000L)
            .put("quoteAsOf", last.optString("tradingDate"))
            .put("marketDataDisclaimer", "Official NSE EOD closing price for " + last.optString("tradingDate") + ". Not live, delayed or intraday.")
            .put("isExchangeCertifiedRealtime", false)
        if (previous != null) {
            val prevClose = previous.optDouble("close", Double.NaN)
            if (prevClose.isFinite() && prevClose > 0.0) {
                out.put("previousClose", prevClose)
                out.put("dayChangePct", ((close - prevClose) / prevClose) * 100.0)
            }
        }
        return out
    }

    /** Build peer rows only where both companies have validated bundled NSE EOD closes. */
    private fun peerComparison(symbol: String): JSONObject {
        // Use a maintained sector peer universe rather than only the small stock-search
        // list. The old list had RELIANCE as the sole Energy member, guaranteeing an
        // empty peer panel even when the full-market NSE EOD files were bundled.
        val peerGroups = mapOf(
            "Energy" to listOf("RELIANCE", "ONGC", "IOC", "BPCL", "GAIL", "HINDPETRO", "OIL"),
            "Banking" to listOf("HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK", "INDUSINDBK", "BANKBARODA", "PNB", "CANBK"),
            "Financial Services" to listOf("BAJFINANCE", "BAJAJFINSV", "SHRIRAMFIN", "CHOLAFIN", "MUTHOOTFIN", "HDFCAMC"),
            "IT Services" to listOf("TCS", "INFY", "HCLTECH", "WIPRO", "TECHM", "LTIM", "PERSISTENT", "COFORGE", "MPHASIS"),
            "Automobiles" to listOf("MARUTI", "M&M", "TATAMOTORS", "EICHERMOT", "HEROMOTOCO", "BAJAJ-AUTO", "TVSMOTOR"),
            "Metals" to listOf("TATASTEEL", "JSWSTEEL", "HINDALCO", "VEDL", "JINDALSTEL", "NMDC"),
            "Power" to listOf("NTPC", "POWERGRID", "TATAPOWER", "ADANIPOWER", "NHPC", "JSWENERGY"),
            "FMCG" to listOf("ITC", "HINDUNILVR", "NESTLEIND", "BRITANNIA", "DABUR", "GODREJCP")
        )
        val sector = stockSector(symbol)
        val candidates = (peerGroups[sector] ?: stocks.filter { it.sector == sector }.map { it.symbol })
            .distinct().filter { it != symbol }
        val rows = JSONArray()
        candidates.forEach { peerSymbol ->
            // Equivalent normalized peer lookup: readBundledNseEod(peer.symbol) after symbol resolution.
            val history = readBundledNseEod(peerSymbol)
            if (history.length() == 0) return@forEach
            val latest = history.optJSONObject(history.length() - 1) ?: return@forEach
            val close = latest.optDouble("close", Double.NaN)
            if (!close.isFinite() || close <= 0.0) return@forEach
            val previous = if (history.length() > 1) history.optJSONObject(history.length() - 2) else null
            val previousClose = previous?.optDouble("close", Double.NaN) ?: Double.NaN
            val changePct = if (previousClose.isFinite() && previousClose > 0.0) ((close - previousClose) / previousClose) * 100.0 else Double.NaN
            val known = stocks.firstOrNull { it.symbol == peerSymbol }
            val row = JSONObject().put("symbol", peerSymbol).put("name", known?.name ?: peerSymbol).put("sector", sector)
                .put("price", close).put("period", latest.optString("tradingDate"))
                .put("source", "NSE CM-UDiFF Common Bhavcopy Final")
                .put("marketDataType", "NSE_EOD").put("priceStatus", "OFFICIAL_EOD_CLOSE")
                .put("quoteTimestamp", latest.optLong("time") / 1000L)
                .put("changePct", if (changePct.isFinite()) changePct else JSONObject.NULL)
                .put("pe", JSONObject.NULL).put("marketCap", JSONObject.NULL)
                .put("roce", JSONObject.NULL).put("roe", JSONObject.NULL).put("eps", JSONObject.NULL)
            rows.put(row)
        }
        return JSONObject().put("symbol", symbol).put("industry", sector).put("peers", rows)
            .put("candidateCount", candidates.size).put("validatedCount", rows.length())
            .put("partial", rows.length() < candidates.size)
            .put("provider", "NSE CM-UDiFF Common Bhavcopy Final")
            .put("marketDataType", "NSE_EOD")
            .put("statusText", "Peer closes are official NSE daily EOD prices only. Fundamentals are not inferred: P/E, market cap, ROCE, ROE and EPS remain unavailable unless a dated Screener peer export is imported.")
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
        val label = if (kind == "oversold") "RSI(14) ≤ 30" else "daily-bar change ≤ -5%"
        return JSONObject()
            .put("columns", JSONArray(listOf("S.No.", "Company", "CMP Rs.", "RSI(14)", "Day Change %", "Data Date", "Provider")))
            .put("rows", JSONArray())
            .put("count", 0)
            .put("provider", "UNAVAILABLE — authorized OHLCV gateway not configured")
            .put("pagesFetched", 0)
            .put("allResultsLoaded", false)
            .put("scanUniverse", stocks.size)
            .put("symbolsChecked", 0)
            .put("statusText", "$label requires validated historical data from an authorized provider. No third-party price series is substituted.")
            .put("marketDataStatus", "UNAVAILABLE")
    }


    private fun downstoxAnnouncements(raw: String): JSONObject {
        if (raw.trim().uppercase(Locale.ROOT).endsWith(".BO")) {
            throw IOException("Company announcement lookup for a BSE-selected symbol is not inferred from a numeric BSE code.")
        }
        val symbol = canonical(raw)
        if (symbol.isBlank()) throw IOException("Select a valid company symbol before loading announcements")
        val root = downstoxGet("/api/announcements/", mapOf("symbol" to symbol, "limit" to "50"), 300_000L)
        val rows = root.optJSONArray("announcements") ?: throw IOException("Downstox announcements payload is missing its announcements array")
        val news = JSONArray()
        for (i in 0 until rows.length()) {
            val row = rows.optJSONObject(i) ?: continue
            val title = row.optString("subject").trim()
            val publishedAt = row.optString("publishedAt").trim()
            if (title.isBlank() || publishedAt.isBlank()) continue
            try { parseGatewayTime(publishedAt) } catch (_: Exception) { continue }
            val link = row.optString("pdfUrl").trim()
            if (!link.startsWith("https://", ignoreCase = true) && !link.startsWith("http://", ignoreCase = true)) continue
            news.put(JSONObject()
                .put("title", title)
                .put("link", link)
                .put("publisher", row.optString("exchange", "NSE/BSE") + " corporate filing via Downstox")
                .put("time", publishedAt)
                .put("symbol", row.optString("symbol", symbol))
                .put("category", row.optString("category", "Corporate announcement")))
        }
        return JSONObject().put("symbol", symbol).put("news", news)
            .put("provider", "Downstox public NSE/BSE corporate announcements")
            .put("marketDataStatus", "CORPORATE_ANNOUNCEMENTS_NOT_FULL_NEWS_OR_EVENT_CALENDAR")
            .put("statusText", "Corporate filing announcements only. This is not a full news feed, upcoming results calendar, or dividend ex-date calendar. Only returned rows are shown.")
    }

    private fun yahooNews(raw: String): JSONObject {
        return JSONObject().put("symbol", canonical(raw))
            .put("news", JSONArray())
            .put("provider", "UNAVAILABLE — permitted company-news provider not configured")
            .put("statusText", "News is unavailable until a permitted provider is configured. The app does not substitute Yahoo-derived news.")
            .put("marketDataStatus", "UNAVAILABLE")
    }


    private fun downstoxMarketIndices(specs: Map<String, String>): JSONObject {
        val root = downstoxGet("/api/india-markets/overview", ttlMs = 60_000L)
        val asOfText = root.optString("timestamp").trim()
        if (asOfText.isBlank()) throw IOException("Downstox index snapshot timestamp is missing")
        val asOf = parseGatewayTime(asOfText)
        val ageMs = System.currentTimeMillis() - asOf
        if (ageMs < -60_000L || ageMs > 24L * 60L * 60L * 1000L) throw IOException("Downstox index snapshot timestamp is in the future or older than 24 hours")
        val indices = root.optJSONObject("indices") ?: JSONObject()
        val cached = root.optBoolean("cached", true)
        val out = JSONObject()
        for (label in specs.keys) {
            out.put(label, JSONObject()
                .put("value", JSONObject.NULL).put("changePct", JSONObject.NULL)
                .put("status", "PUBLIC_SNAPSHOT_NOT_RETURNED").put("priceSource", "NONE")
                .put("provider", "Downstox public snapshot")
                .put("sourceType", "NO_DATA").put("quoteTimestamp", asOf / 1000L)
                .put("isExchangeCertifiedRealtime", false)
                .put("marketDataDisclaimer", "Downstox did not return this index in its public snapshot; no value is inferred."))
        }
        val direct = mapOf(
            "NIFTY 50" to indices.optJSONObject("nse"),
            "SENSEX" to indices.optJSONObject("bse")
        )
        val rows = mutableListOf<JSONObject>()
        for (key in listOf("sectors", "extras")) {
            val arr = root.optJSONArray(key) ?: continue
            for (i in 0 until arr.length()) {
                val row = arr.optJSONObject(i) ?: continue
                rows.add(row)
            }
        }
        val tickerAliases = mapOf(
            "NIFTY BANK" to setOf("^NSEBANK", "NSEBANK"),
            "NIFTY MIDCAP 100" to setOf("^CRSMID", "CRSMID"),
            "NIFTY SMALLCAP 100" to setOf("^CRSSML", "CRSSML"),
            "NIFTY IT" to setOf("^CNXIT", "CNXIT"),
            "NIFTY AUTO" to setOf("^CNXAUTO", "CNXAUTO"),
            "NIFTY FMCG" to setOf("^CNXFMCG", "CNXFMCG"),
            "NIFTY PHARMA" to setOf("^CNXPHARMA", "CNXPHARMA"),
            "NIFTY METAL" to setOf("^CNXMETAL", "CNXMETAL"),
            "NIFTY PSU BANK" to setOf("^CNXPSUBANK", "CNXPSUBANK"),
            "NIFTY PRIVATE BANK" to setOf("^NIFTYPVTBANK", "NIFTYPVTBANK"),
            "NIFTY ENERGY" to setOf("^CNXENERGY", "CNXENERGY"),
            "NIFTY INFRA" to setOf("^CNXINFRA", "CNXINFRA"),
            "NIFTY FIN SERVICE" to setOf("^CNXFINANCE", "CNXFINANCE")
        )
        val nameAliases = mapOf(
            "NIFTY BANK" to setOf("bank nifty", "nifty bank"),
            "NIFTY MIDCAP 100" to setOf("nifty midcap 100", "midcap 100"),
            "NIFTY SMALLCAP 100" to setOf("nifty smallcap 100", "smallcap 100"),
            "NIFTY IT" to setOf("nifty it", "nifty information technology"),
            "NIFTY AUTO" to setOf("nifty auto", "nifty automobile"),
            "NIFTY FMCG" to setOf("nifty fmcg"),
            "NIFTY PHARMA" to setOf("nifty pharma"),
            "NIFTY METAL" to setOf("nifty metal"),
            "NIFTY PSU BANK" to setOf("nifty psu bank", "psu bank"),
            "NIFTY PRIVATE BANK" to setOf("nifty private bank", "private bank"),
            "NIFTY ENERGY" to setOf("nifty energy"),
            "NIFTY INFRA" to setOf("nifty infrastructure", "nifty infra"),
            "NIFTY FIN SERVICE" to setOf("nifty financial services", "nifty fin service", "financial services")
        )
        fun normalized(value: String): String = value.lowercase(Locale.ROOT).replace(Regex("[^a-z0-9]+"), " ").trim()
        fun makeSnapshot(row: JSONObject?, label: String): JSONObject? {
            if (row == null) return null
            val price = row.optDouble("price", Double.NaN)
            if (!finite(price) || price <= 0.0) return null
            val change = row.optDouble("change", Double.NaN)
            val liveFlag = row.optBoolean("isLive", false)
            return JSONObject().put("value", price)
                .put("changePct", if (finite(change)) change else JSONObject.NULL)
                .put("status", "PUBLIC_SNAPSHOT").put("priceSource", "DOWNSTOX_PUBLIC_SNAPSHOT")
                .put("provider", "Downstox public API snapshot")
                .put("sourceType", "PUBLIC_SNAPSHOT").put("quoteTimestamp", asOf / 1000L)
                .put("quoteAsOf", asOfText).put("isExchangeCertifiedRealtime", false)
                .put("marketDataDisclaimer", "Public cached snapshot; " +
                    (if (cached) "API says cached; " else "") +
                    (if (!liveFlag) "API does not assert this tile is live; " else "") +
                    "not an exchange-certified live feed • " + label + " • as of " + asOfText)
        }
        for ((label, directRow) in direct) {
            val snap = makeSnapshot(directRow, label)
            if (snap != null) out.put(label, snap)
        }
        for (label in specs.keys) {
            if (direct.containsKey(label)) continue
            val tickers = tickerAliases[label] ?: emptySet()
            val names = nameAliases[label] ?: emptySet()
            val found = rows.firstOrNull { row ->
                val ticker = row.optString("ticker").uppercase(Locale.ROOT).trim()
                val name = normalized(row.optString("name"))
                tickers.contains(ticker) || names.contains(name)
            }
            val snap = makeSnapshot(found, label)
            if (snap != null) out.put(label, snap)
        }
        return out
    }

    private fun marketIndices(): JSONObject {
        val specs = linkedMapOf(
            "NIFTY 50" to "^NSEI", "SENSEX" to "^BSESN", "NIFTY BANK" to "^NSEBANK",
            "NIFTY MIDCAP 100" to "^CRSMID", "NIFTY SMALLCAP 100" to "^CRSSML", "NIFTY IT" to "^CNXIT",
            "NIFTY AUTO" to "^CNXAUTO", "NIFTY FMCG" to "^CNXFMCG", "NIFTY PHARMA" to "^CNXPHARMA",
            "NIFTY METAL" to "^CNXMETAL", "NIFTY PSU BANK" to "^CNXPSUBANK", "NIFTY PRIVATE BANK" to "^NIFTYPVTBANK",
            "NIFTY ENERGY" to "^CNXENERGY", "NIFTY INFRA" to "^CNXINFRA", "NIFTY FIN SERVICE" to "^CNXFINANCE",
            "GOLD FUTURES (GLOBAL)" to "GC=F", "SILVER FUTURES (GLOBAL)" to "SI=F", "BRENT CRUDE (GLOBAL)" to "BZ=F"
        )
        fun unavailable(status: String, message: String): JSONObject {
            val out = JSONObject()
            specs.forEach { (label, _) ->
                out.put(label, JSONObject().put("value", JSONObject.NULL).put("changePct", JSONObject.NULL)
                    .put("status", status).put("priceSource", "NONE").put("provider", "No verified quote")
                    .put("sourceType", "NO_DATA").put("quoteTimestamp", JSONObject.NULL)
                    .put("isExchangeCertifiedRealtime", false).put("marketDataDisclaimer", message))
            }
            return out
        }
        if (!gatewayConfigured()) {
            return unavailable("NSE_INDEX_FEED_NOT_CONFIGURED",
                "No approved NSE index-data feed is configured. Public website pages are not treated as a documented API; no third-party index snapshot is used.")
        }
        return try {
            val data = gatewayGet("/v1/indices")
            val source = data.optString("source").trim()
            val status = data.optString("marketDataStatus").uppercase(Locale.ROOT)
            val asOfText = data.optString("asOf")
            if (source.isBlank()) throw IOException("Index feed source is missing")
            if (status !in setOf("REALTIME", "DELAYED", "EOD")) throw IOException("Index feed marketDataStatus must be REALTIME, DELAYED or EOD")
            val asOf = parseGatewayTime(asOfText)
            val age = System.currentTimeMillis() - asOf
            if (age < -60_000L) throw IOException("Index feed timestamp is in the future")
            val maxAge = when (status) {
                "REALTIME" -> 5 * 60 * 1000L
                "DELAYED" -> {
                    if (data.optInt("delayMinutes", 0) <= 0) throw IOException("Delayed index feed must disclose delayMinutes")
                    24 * 60 * 60 * 1000L
                }
                else -> 72 * 60 * 60 * 1000L
            }
            if (age > maxAge) throw IOException("Index feed is stale for declared $status status")
            val rows = data.optJSONArray("rows") ?: throw IOException("Index feed payload missing rows")
            if (rows.length() == 0) throw IOException("Index feed returned no index rows; snapshot rejected")
            val byName = mutableMapOf<String, JSONObject>()
            for (i in 0 until rows.length()) {
                val row = rows.optJSONObject(i) ?: throw IOException("Index feed row $i is not a JSON object")
                val name = row.optString("name").trim().uppercase(Locale.ROOT)
                if (name.isBlank()) throw IOException("Index feed row $i has no index name")
                if (byName.containsKey(name)) throw IOException("Index feed contains duplicate index name '$name'; snapshot rejected")
                val value = row.optDouble("value", Double.NaN)
                val changePct = row.optDouble("changePct", Double.NaN)
                if (!value.isFinite() || value <= 0.0 || !changePct.isFinite())
                    throw IOException("Index feed row '$name' has invalid value/changePct; snapshot rejected")
                byName[name] = row
            }
            val out = JSONObject()
            specs.forEach { (label, _) ->
                val row = byName[label.uppercase(Locale.ROOT)]
                if (row == null) {
                    out.put(label, JSONObject().put("value", JSONObject.NULL).put("changePct", JSONObject.NULL)
                        .put("status", "INDEX_NOT_RETURNED_BY_AUTHORIZED_PROVIDER").put("priceSource", "NONE")
                        .put("provider", source).put("sourceType", "NO_DATA").put("quoteTimestamp", asOf / 1000L)
                        .put("isExchangeCertifiedRealtime", false)
                        .put("marketDataDisclaimer", "The authorized provider did not return this index. No value is inferred or substituted."))
                } else {
                    out.put(label, JSONObject().put("value", row.optDouble("value"))
                        .put("changePct", row.optDouble("changePct")).put("status", status)
                        .put("priceSource", source).put("provider", source).put("sourceType", status)
                        .put("quoteTimestamp", asOf / 1000L).put("quoteAsOf", asOfText)
                        .put("isExchangeCertifiedRealtime", false)
                        .put("marketDataDisclaimer", "Provider-declared $status index quote • $source • as of $asOfText. Exchange licensing/SLA must be independently verified."))
                }
            }
            out
        } catch (e: Exception) {
            unavailable("PROVIDER_GATEWAY_VALIDATION_FAILED", "Authorized index gateway validation failed: ${e.message ?: "unknown error"}. No fallback is used.")
        }
    }

    /**
     * Search the newest bundled official NSE CM-UDiFF EQ bhavcopy.
     * This expands discovery beyond the legacy 28 hand-maintained suggestions.
     * It is an EOD-observed NSE symbol universe, not a live quote feed or BSE master.
     */
    @Volatile private var bundledNseSymbolCache: List<String>? = null

    private fun bundledNseSymbols(): List<String> {
        bundledNseSymbolCache?.let { return it }
        synchronized(this) {
            bundledNseSymbolCache?.let { return it }
            val files = appAssets.list("nse-eod").orEmpty()
                .filter { it.matches(Regex("\\d{4}-\\d{2}-\\d{2}\\.csv")) }
                .sortedDescending()
            if (files.isEmpty()) return emptyList()
            val symbols = linkedSetOf<String>()
            appAssets.open("nse-eod/" + files.first()).bufferedReader(Charsets.UTF_8).useLines { lines ->
                lines.drop(1).forEach { line ->
                    val symbol = line.substringBefore(',').trim().trim('"').uppercase(Locale.ROOT)
                    if (symbol.matches(Regex("[A-Z0-9&._-]{1,30}"))) symbols.add(symbol)
                }
            }
            val result = symbols.toList().sorted()
            bundledNseSymbolCache = result
            return result
        }
    }

    private fun equitySearch(term: String, limit: Int = 12): List<JSONObject> {
        val normalized = term.trim().uppercase(Locale.ROOT).replace(Regex("[^A-Z0-9]"), "")
        if (normalized.length < 1) return emptyList()
        return bundledNseSymbols()
            .filter { it.replace(Regex("[^A-Z0-9]"), "").contains(normalized) }
            .sortedWith(compareBy<String> { if (it.startsWith(normalized)) 0 else 1 }.thenBy { it })
            .take(limit.coerceIn(1, 50))
            .map { symbol ->
                JSONObject()
                    .put("symbol", symbol)
                    .put("name", stockName(symbol))
                    .put("exchange", "NSE (observed in official EOD EQ bhavcopy)")
                    .put("sector", stockSector(symbol))
                    .put("provider", "NSE CM-UDiFF Common Bhavcopy Final")
                    .put("marketDataStatus", "EOD")
                    .put("listingVerification", "Symbol observed in latest bundled NSE EQ EOD report")
            }
    }

    private fun gatewayEvents(path: String, symbol: String, eventType: String): JSONObject {
        val params = linkedMapOf("eventType" to eventType.uppercase(Locale.ROOT))
        if (symbol.isNotBlank()) params["symbol"] = canonical(symbol)
        val data = gatewayGet(path, params)
        val source = data.optString("source").trim()
        val asOfText = data.optString("asOf")
        val asOf = parseGatewayTime(asOfText)
        if (source.isBlank()) throw IOException("Event feed source is missing")
        val age = System.currentTimeMillis() - asOf
        if (age < -60_000L || age > 72 * 60 * 60 * 1000L) throw IOException("Event feed timestamp is stale or in the future")
        val input = data.optJSONArray("rows") ?: throw IOException("Event feed payload missing rows")
        val rows = JSONArray()
        for (i in 0 until input.length()) {
            val row = input.optJSONObject(i) ?: continue
            val kind = row.optString("eventType").uppercase(Locale.ROOT)
            val title = row.optString("title").trim()
            val eventDate = row.optString("eventDate")
            val announced = row.optString("announcedAt")
            val sym = canonical(row.optString("symbol"))
            if (kind !in setOf("RESULTS", "DIVIDEND", "SPLIT", "BONUS", "RIGHTS", "BOARD_MEETING", "OTHER")) continue
            if (title.isBlank() || !Regex("^\\d{4}-\\d{2}-\\d{2}").containsMatchIn(eventDate) || sym.isBlank()) continue
            try { parseGatewayTime(announced) } catch (_: Exception) { continue }
            if (symbol.isNotBlank() && sym != canonical(symbol)) continue
            if (eventType != "ALL" && kind != eventType.uppercase(Locale.ROOT)) continue
            rows.put(JSONObject()
                .put("symbol", sym)
                .put("company", row.optString("company", stockName(sym)))
                .put("name", row.optString("company", stockName(sym)))
                .put("date", eventDate)
                .put("eventDate", eventDate)
                .put("event", title)
                .put("title", title)
                .put("type", kind)
                .put("eventType", kind)
                .put("announcedAt", announced)
                .put("recordDate", row.optString("recordDate", ""))
                .put("dividend", row.optString("dividend", ""))
                .put("ratio", row.optString("ratio", "")))
        }
        return JSONObject().put("rows", rows).put("provider", source).put("source", source)
            .put("asOf", asOfText).put("liveData", true)
            .put("statusText", "Verified provider response • $source • as of $asOfText. Empty results mean no rows were returned, not that no events exist.")
    }


    // Official exchange RSS aggregation. This is direct in-app retrieval (no CSV upload,
    // no third-party scraping, no credential bypass). RSS records link back to original filings.
    private data class ExchangeFeedItem(val title: String, val description: String, val link: String, val published: String, val source: String, val category: String)
    private val exchangeFeedCache = java.util.concurrent.ConcurrentHashMap<String, Pair<Long, List<ExchangeFeedItem>>>()
    private val exchangeFeedTtlMs = 5L * 60L * 1000L

    private fun fetchOfficialRss(urlText: String, source: String, category: String): List<ExchangeFeedItem> {
        val uri = URL(urlText)
        val host = uri.host.lowercase(Locale.ROOT)
        if (host !in setOf("nsearchives.nseindia.com", "archives.nseindia.com", "www.bseindia.com", "beta.bseindia.com"))
            throw IOException("RSS host is not on the official exchange allowlist")
        val cached = exchangeFeedCache[urlText]
        if (cached != null && System.currentTimeMillis() - cached.first < exchangeFeedTtlMs) return cached.second
        val c = uri.openConnection() as HttpURLConnection
        c.connectTimeout = 5000; c.readTimeout = 7000; c.instanceFollowRedirects = true
        c.setRequestProperty("User-Agent", "PRO-STOCK-INTELLIGENCE/1.0 (official exchange RSS reader)")
        c.setRequestProperty("Accept", "application/rss+xml, application/xml, text/xml, */*")
        try {
            val code = c.responseCode
            if (code !in 200..299) throw IOException("$source RSS returned HTTP $code")
            val bytes = c.inputStream.use { input -> val out = java.io.ByteArrayOutputStream(); val buffer = ByteArray(8192); var total = 0; while (true) { val count = input.read(buffer); if (count < 0) break; total += count; if (total > 2_000_000) throw IOException("$source RSS exceeded 2 MB"); out.write(buffer, 0, count) }; out.toByteArray() }
            if (bytes.size > 2_000_000) throw IOException("$source RSS exceeded 2 MB")
            val factory = javax.xml.parsers.DocumentBuilderFactory.newInstance()
            factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true)
            factory.setFeature("http://xml.org/sax/features/external-general-entities", false)
            factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false)
            factory.isXIncludeAware = false; factory.isExpandEntityReferences = false
            val doc = factory.newDocumentBuilder().parse(ByteArrayInputStream(bytes))
            val nodes = doc.getElementsByTagName("item")
            val out = ArrayList<ExchangeFeedItem>()
            for (i in 0 until minOf(nodes.length, 300)) {
                val node = nodes.item(i)
                fun field(name: String): String {
                    val children = node.childNodes
                    for (j in 0 until children.length) {
                        val child = children.item(j)
                        if (child.nodeName.equals(name, true)) return child.textContent?.trim().orEmpty()
                    }
                    return ""
                }
                val title = cleanText(field("title")).take(500)
                val desc = cleanText(field("description")).take(1800)
                val link = field("link").trim()
                val linkUri = try { URL(link) } catch (_: Exception) { null }
                if (title.isBlank() || linkUri == null || linkUri.protocol != "https") continue
                val linkHost = linkUri.host.lowercase(Locale.ROOT)
                if (!(linkHost == "nseindia.com" || linkHost.endsWith(".nseindia.com") || linkHost == "bseindia.com" || linkHost.endsWith(".bseindia.com"))) continue
                out.add(ExchangeFeedItem(title, desc, link, field("pubDate").trim(), source, category))
            }
            exchangeFeedCache[urlText] = System.currentTimeMillis() to out
            return out
        } finally { c.disconnect() }
    }

    private fun officialExchangeItems(): Pair<List<ExchangeFeedItem>, List<String>> {
        val feeds = listOf(
            Triple("https://nsearchives.nseindia.com/content/RSS/Online_announcements.xml", "NSE", "ANNOUNCEMENT"),
            Triple("https://nsearchives.nseindia.com/content/RSS/Corporate_action.xml", "NSE", "CORPORATE_ACTION"),
            Triple("https://nsearchives.nseindia.com/content/RSS/Board_Meetings.xml", "NSE", "BOARD_MEETING"),
            Triple("https://www.bseindia.com/data/xml/announcements.aspx", "BSE", "ANNOUNCEMENT"),
            Triple("https://www.bseindia.com/Data/XML/FinancialResultsFeed.aspx", "BSE", "FINANCIAL_RESULTS"),
            Triple("https://www.bseindia.com/data/XML/CorpActionFeed.aspx", "BSE", "CORPORATE_ACTION"),
            Triple("https://beta.bseindia.com/Data/XML/BoardMeetingsFeed.xml", "BSE", "BOARD_MEETING")
        )
        val items = ArrayList<ExchangeFeedItem>(); val errors = ArrayList<String>()
        for ((url, source, category) in feeds) try { items.addAll(fetchOfficialRss(url, source, category)) }
        catch (e: Exception) { errors.add("$source $category: ${e.message ?: "feed unavailable"}") }
        return items.distinctBy { it.link }.sortedByDescending { it.published } to errors
    }

    private fun exchangeFeedResponse(symbol: String, mode: String): String {
        val (all, errors) = officialExchangeItems()
        val needle = symbol.trim().uppercase(Locale.ROOT)
        val filtered = all.filter { item ->
            val text = (item.title + " " + item.description).uppercase(Locale.ROOT)
            val symbolMatch = needle.isBlank() || text.contains(needle) || text.contains(stockName(needle).uppercase(Locale.ROOT))
            val dividend = text.contains("DIVIDEND") || text.contains("INTERIM DIV") || text.contains("FINAL DIV")
            val results = text.contains("FINANCIAL RESULT") || text.contains("QUARTERLY RESULT") || text.contains("BOARD MEETING")
            when (mode) {
                "NEWS" -> symbolMatch
                "DIVIDENDS" -> symbolMatch && dividend
                "RESULTS" -> symbolMatch && results
                "EVENTS" -> symbolMatch && (dividend || results || item.category == "CORPORATE_ACTION" || item.category == "BOARD_MEETING")
                else -> symbolMatch
            }
        }.take(150)
        val rows = JSONArray()
        filtered.forEach { item ->
            val text = item.title + " " + item.description
            val company = item.title.substringBefore(" - ").substringBefore(" (").trim().ifBlank { item.source }
            val type = when {
                text.contains("DIVIDEND", true) -> "DIVIDEND"
                text.contains("RESULT", true) -> "RESULTS"
                text.contains("BOARD MEETING", true) -> "BOARD_MEETING"
                text.contains("BONUS", true) -> "BONUS"
                text.contains("SPLIT", true) -> "SPLIT"
                else -> item.category
            }
            rows.put(JSONObject().put("title", item.title).put("event", item.title)
                .put("description", item.description).put("link", item.link)
                .put("date", item.published).put("publishedAt", item.published)
                .put("company", company).put("type", type)
                .put("dividend", if (type == "DIVIDEND") item.title else "")
                .put("ratio", "").put("recordDate", "")
                .put("source", item.source).put("category", item.category)
                .put("symbol", needle).put("verifiedSource", true))
        }
        val successfulSources = all.map { it.source }.distinct()
        val status = if (successfulSources.isNotEmpty()) "OFFICIAL_EXCHANGE_RSS" else "OFFICIAL_FEEDS_UNAVAILABLE"
        val data = JSONObject().put("symbol", needle).put("rows", rows).put("news", rows)
            .put("provider", successfulSources.joinToString(" + ").ifBlank { "Unavailable" })
            .put("sourcesChecked", JSONArray().put("NSE official RSS").put("BSE official RSS"))
            .put("sourceErrors", JSONArray().apply { errors.forEach { put(it) } })
            .put("status", status).put("feedAvailable", successfulSources.isNotEmpty()).put("liveData", false)
            .put("asOf", java.text.SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssXXX", Locale.ROOT).format(java.util.Date()))
            .put("statusText", if (successfulSources.isNotEmpty()) "Official NSE/BSE exchange RSS announcements retrieved. This is not a live market-data feed; publication may be delayed and the feed is not a complete historical database. Open each filing link for the full disclosure." else "Official NSE/BSE exchange feeds could not be reached. Retry later; no empty result is represented as confirmation that no event exists.")
        return JSONObject().put("ok", true).put("data", data).toString()
    }

    fun handle(path: String): String {
        val p = path.substringBefore("?")
        val q = parseQuery(path)
        val raw = q["symbol"] ?: q["q"] ?: "INFY"
        val s = canonical(raw)
        return try {
            when (p) {
                "/api/health" -> JSONObject().put("ok", true).put("engine", "V40.92 OFFICIAL NSE/BSE RSS + AUTHORIZED MARKET DATA").put("data", JSONObject().put("ok", true).put("providerGatewayConfigured", gatewayConfigured()).put("quoteStatus", if (gatewayConfigured()) "GATEWAY_CONFIGURED_NOT_YET_PROVEN" else "UNAVAILABLE_AUTHORIZED_FEED_NOT_CONFIGURED").put("historyStatus", if (gatewayConfigured()) "GATEWAY_CONFIGURED_NOT_YET_PROVEN" else "UNAVAILABLE_AUTHORIZED_HISTORY_NOT_CONFIGURED").put("indicesStatus", if (gatewayConfigured()) "GATEWAY_CONFIGURED_NOT_YET_PROVEN" else "UNAVAILABLE_AUTHORIZED_INDEX_FEED_NOT_CONFIGURED").put("eventsStatus", "OFFICIAL_NSE_BSE_RSS_CONFIGURED_RUNTIME_VALIDATION_REQUIRED").put("moneycontrolIntegration", "DISABLED_BY_V40_79_PROVIDER_POLICY").put("screenerSessionStatus", if (screenerLoggedIn()) "COOKIE_DETECTED_NOT_YET_VALIDATED" else "LOGIN_REQUIRED").put("providerDiagnostics", true).put("screenerCsvImport", true)).toString()
                "/api/providers/status" -> JSONObject().put("ok", true).put("data", providerStatus(raw)).toString()
                "/api/screener/status" -> JSONObject().put("ok", true).put("data", screenerStatus()).toString()
                "/api/screener/connect" -> JSONObject().put("ok", true).put("data", screenerConnectionTest()).toString()
                "/api/screener/disconnect" -> JSONObject().put("ok", true).put("data", JSONObject().put("connected", false).put("loggedIn", false).put("message", "Sign out from Screener inside the web page to end the session.")).toString()
                "/api/search-suggestions" -> {
                    val originalTerm = (q["q"] ?: "").trim()
                    val term = originalTerm.uppercase(Locale.ROOT).replace(Regex("[^A-Z0-9]"), "")
                    val local = stocks.filter { term.isBlank() || it.symbol.contains(term) || it.name.uppercase(Locale.ROOT).replace(Regex("[^A-Z0-9]"), "").contains(term) || (term.contains("INFOSYS") && it.symbol == "INFY") }
                        .take(12).map { JSONObject().put("symbol", it.symbol).put("name", it.name).put("exchange", "LISTING_UNVERIFIED").put("sector", it.sector).put("provider", "Built-in suggestion list; exchange listing not verified") }
                    val external = if (originalTerm.length >= 2) try { equitySearch(originalTerm, 12) } catch (_: Exception) { emptyList() } else emptyList()
                    val combined = (external + local).distinctBy { it.optString("symbol").uppercase(Locale.ROOT) }.take(12)
                    val arr = JSONArray(); combined.forEach { arr.put(it) }
                    JSONObject().put("ok", true).put("data", arr).put("count", combined.size)
                        .put("searchProvider", if (external.isNotEmpty()) "Bundled official NSE EOD EQ symbol universe" else "Legacy local suggestions only; NSE EOD symbol master unavailable")
                        .put("coverageDisclaimer", "Search uses symbols present in the latest bundled official NSE CM-UDiFF EQ bhavcopy. It is NSE EOD discovery, not a BSE security master or live quote feed.").toString()
                }
                "/api/quote", "/api/fast" -> {
                    val quote = try {
                        if (gatewayConfigured()) nseQuote(raw) else eodQuote(raw)
                    } catch (e: Exception) {
                        JSONObject().put("symbol", s)
                            .put("status", if (gatewayConfigured()) "PROVIDER_GATEWAY_VALIDATION_FAILED" else "OFFICIAL_NSE_EOD_UNAVAILABLE")
                            .put("provider", "Unavailable").put("price", JSONObject.NULL)
                            .put("quoteTimestamp", JSONObject.NULL)
                            .put("marketDataDisclaimer", "No authorized quote gateway or validated NSE EOD reference is available. No third-party fallback is used; no Yahoo/Moneycontrol fallback and no price is fabricated.")
                            .put("providerError", e.message ?: "Verified quote unavailable")
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
                    if (p == "/api/bootstrap") data.put("diagnostics", JSONObject().put("quoteProvider", if (gatewayConfigured()) "Authorized gateway configured; each response must pass source/timestamp validation" else "Unavailable — authorized NSE/vendor gateway not configured; no third-party fallback").put("fundamentalProvider", if (data.optJSONObject("fundamentals")?.has("providerError") == true) "Unavailable" else "Screener.in page parser; actual field coverage must be reviewed"))
                    JSONObject().put("ok", true).put("data", data).toString()
                }
                "/api/screener/audit30" -> {
                    if (!screenerLoggedIn()) throw IOException("Screener login is not active. Sign in on the official page first.")
                    JSONObject().put("ok", true).put("data", screenerAudit30()).toString()
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
                "/api/peers" -> JSONObject().put("ok", true).put("data", peerComparison(s)).toString()
                "/api/news" -> exchangeFeedResponse(s, "NEWS")
                "/api/company-events" -> exchangeFeedResponse(s, "EVENTS")
                "/api/dividend-stocks" -> exchangeFeedResponse("", "DIVIDENDS")
                "/api/upcoming-events" -> exchangeFeedResponse("", "EVENTS")
                "/api/upcoming-results" -> exchangeFeedResponse("", "RESULTS")
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
