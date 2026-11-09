package pro.celikom.spike

import android.annotation.SuppressLint
import android.content.Context
import android.webkit.*
import androidx.webkit.WebViewCompat
import androidx.webkit.WebViewFeature
import org.json.JSONObject
import org.json.JSONTokener

/** Passive, credentials-free service capability check, no playback or mute command. */
class YandexSurfaceProbe(context: Context) {
    val view = WebView(context)
    var status = "not_loaded"; private set
    private var closed = false
    @SuppressLint("SetJavaScriptEnabled")
    fun load(url: String) {
        require(SurfaceOrigin.allowed(url))
        view.settings.apply {
            javaScriptEnabled = true; domStorageEnabled = true
            allowFileAccess = false; allowContentAccess = false
            mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
            safeBrowsingEnabled = true
            mediaPlaybackRequiresUserGesture = true
        }
        if (!WebViewFeature.isFeatureSupported(WebViewFeature.DOCUMENT_START_SCRIPT)) {
            status = "document_start_unsupported"; return
        }
        val script = view.context.assets.open("shared-surface-probe.js").bufferedReader().use { it.readText() }
        WebViewCompat.addDocumentStartJavaScript(view, script, setOf("https://music.yandex.ru"))
        view.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(v: WebView, r: WebResourceRequest): Boolean {
                if (!r.isForMainFrame) return false
                if (!SurfaceOrigin.allowed(r.url.toString())) { status = "navigation_blocked"; return true }
                return false
            }
            override fun onPageFinished(v: WebView, url: String) {
                if (SurfaceOrigin.allowed(url) && status == "loading") status = "page_loaded"
            }
            override fun onReceivedError(v: WebView, r: WebResourceRequest, e: WebResourceError) {
                if (r.isForMainFrame) status = "network_error_" + e.errorCode
            }
            override fun onReceivedHttpError(v: WebView, r: WebResourceRequest, e: WebResourceResponse) {
                if (r.isForMainFrame) status = "http_" + e.statusCode
            }
            override fun onReceivedSslError(v: WebView, handler: SslErrorHandler, error: android.net.http.SslError) {
                handler.cancel(); status = "tls_error"
            }
            override fun onRenderProcessGone(v: WebView, detail: RenderProcessGoneDetail): Boolean {
                status = "renderer_gone"; close(); return true
            }
        }
        status = "loading"; view.loadUrl(url)
    }
    fun report(callback: (JSONObject) -> Unit) {
        val report = JSONObject().put("surface", "android_system_webview_default_ua")
            .put("status", status).put("authenticated", false)
            .put("playback_confirmed", false)
            .put("webview_version", WebView.getCurrentWebViewPackage()?.versionName ?: "unknown")
        if (closed || !SurfaceOrigin.allowed(view.url ?: "")) { callback(report); return }
        // Only sanitized exact-state diagnostics leave the page; never source URLs/cookies.
        view.evaluateJavascript("""
          (() => {
            const a=window.__CELIKOM_ANDROID_SURFACE__, s=a?.getSnapshot("android-probe");
            const t=s?.track, p=s?.player;
            return JSON.stringify({adapter:!!a, trackId:t?.id || null,
              confidence:t?.confidence || 0, ambiguous:!!t?.ambiguous,
              durationMs:t?.metadata?.durationMs || 0, mediaReadyState:p?.readyState || 0,
              mediaPresent:!!p?.mediaId, catalogSize:t?.catalogSize || 0,
              captcha:!!document.querySelector("form[action*='checkcaptcha'],[id*='captcha'],[class*='Captcha']")});
          })()
        """.trimIndent()) { raw ->
            runCatching {
                require(raw.length <= 8192)
                val value = JSONObject(JSONTokener(raw).nextValue() as String)
                report.put("diagnostics", value)
            }.onFailure { report.put("diagnostics_error", true) }
            callback(report)
        }
    }
    fun playControl(callback: (FloatArray?) -> Unit) {
        if (closed || !SurfaceOrigin.allowed(view.url ?: "")) { callback(null); return }
        view.evaluateJavascript("""
          (() => {
            const b=[...document.querySelectorAll("button")].find(b =>
              /^(слушать|воспроизвести|play)$/i.test((b.getAttribute("aria-label")||b.title||"").trim()) &&
              b.getBoundingClientRect().width>0);
            if(!b) return null;
            const r=b.getBoundingClientRect();
            return JSON.stringify({x:(r.left+r.width/2)*devicePixelRatio,y:(r.top+r.height/2)*devicePixelRatio});
          })()
        """.trimIndent()) { raw ->
            val point = runCatching {
                val p = JSONObject(JSONTokener(raw).nextValue() as String)
                val x=p.getDouble("x").toFloat(); val y=p.getDouble("y").toFloat()
                require(x.isFinite() && y.isFinite() && x>=0 && y>=0 && x<view.width && y<view.height)
                val location=IntArray(2); view.getLocationOnScreen(location)
                floatArrayOf(x+location[0],y+location[1])
            }.getOrNull()
            callback(point)
        }
    }
    fun close() {
        if (closed) return
        closed = true
        (view.parent as? android.view.ViewGroup)?.removeView(view)
        view.stopLoading(); view.destroy()
    }
}
