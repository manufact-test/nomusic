package pro.celikom.spike

import android.annotation.SuppressLint
import android.content.Context
import android.webkit.*
import androidx.webkit.WebViewCompat
import androidx.webkit.WebViewFeature
import org.json.JSONObject
import org.json.JSONTokener
import java.net.URI

/** No JavascriptInterface; native tokens are never exposed to remote documents. */
class MobileSurface(context:Context,private val changed:(String)->Unit,private val leaving:()->Unit,private val released:(String)->Unit) {
    val view=WebView(context)
    var closed=false; private set
    @SuppressLint("SetJavaScriptEnabled") fun open() {
        view.settings.apply {
            javaScriptEnabled=true; domStorageEnabled=true; allowFileAccess=false; allowContentAccess=false
            mixedContentMode=WebSettings.MIXED_CONTENT_NEVER_ALLOW; safeBrowsingEnabled=true
            mediaPlaybackRequiresUserGesture=true; setSupportMultipleWindows(false)
            useWideViewPort=true;loadWithOverviewMode=true;builtInZoomControls=true;displayZoomControls=false
        }
        if(!WebViewFeature.isFeatureSupported(WebViewFeature.DOCUMENT_START_SCRIPT)||!WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER)) {
            changed("Обновите Android System WebView: нет поддержки безопасного адаптера"); return
        }
        WebViewCompat.addWebMessageListener(view,"CelikomLease",setOf("https://music.yandex.ru")) { _, message, origin, mainFrame, _ ->
            if(mainFrame&&SurfaceOrigin.allowed(origin.toString())) runCatching {
                val raw=message.data?:return@addWebMessageListener
                require(raw.length<=512)
                val token=JSONObject(raw).getString("released")
                require(token.length in 1..128);released(token)
            }
        }
        val script=view.context.assets.open("mobile-playback.js").bufferedReader().use{it.readText()}
        WebViewCompat.addDocumentStartJavaScript(view,script,setOf("https://music.yandex.ru"))
        view.webChromeClient=WebChromeClient()
        view.webViewClient=object:WebViewClient() {
            override fun shouldOverrideUrlLoading(v:WebView,r:WebResourceRequest):Boolean {
                if(!r.isForMainFrame) return false
                if(!navigationAllowed(r.url.toString())) { changed("Эта внешняя ссылка не открывается в CELIKOM"); return true }
                if(!SurfaceOrigin.allowed(r.url.toString())) leaving()
                return false
            }
            override fun onPageStarted(v:WebView,url:String,icon:android.graphics.Bitmap?) { leaving() }
            override fun onReceivedSslError(v:WebView,h:SslErrorHandler,e:android.net.http.SslError) { h.cancel(); leaving(); changed("Ошибка защищённого соединения") }
            override fun onReceivedError(v:WebView,r:WebResourceRequest,e:WebResourceError) { if(r.isForMainFrame){leaving();changed("Не удалось загрузить Яндекс Музыку")} }
            override fun onRenderProcessGone(v:WebView,d:RenderProcessGoneDetail):Boolean { leaving(); changed("Плеер остановлен. Закройте и откройте приложение"); close(); return true }
        }
        view.loadUrl("https://music.yandex.ru/")
    }
    fun snapshot(callback:(JSONObject?)->Unit) {
        if(closed||!SurfaceOrigin.allowed(view.url?:"")){callback(null);return}
        view.evaluateJavascript("window.__CELIKOM_MOBILE__?.snapshot() || null") { raw ->
            callback(runCatching { require(raw.length<=8192);JSONObject(JSONTokener(raw).nextValue() as String) }.getOrNull())
        }
    }
    fun engage(track:String,media:String,token:String,callback:(Boolean)->Unit) {
        if(closed||!SurfaceOrigin.allowed(view.url?:"")){callback(false);return}
        view.evaluateJavascript("window.__CELIKOM_MOBILE__?.engage(${JSONObject.quote(track)},${JSONObject.quote(media)},${JSONObject.quote(token)}) === true") {callback(it=="true")}
    }
    fun release(token:String?=null) {
        if(!closed&&SurfaceOrigin.allowed(view.url?:"")) view.evaluateJavascript("window.__CELIKOM_MOBILE__?.release(${token?.let{JSONObject.quote(it)}?:"null"})",null)
    }
    fun suspend() { release(); if(!closed){ view.evaluateJavascript("document.querySelectorAll('audio,video').forEach(e=>e.pause())",null);view.onPause() } }
    fun desktopMode(enabled:Boolean){
        if(closed||!SurfaceOrigin.allowed(view.url?:""))return
        leaving()
        val normal=WebSettings.getDefaultUserAgent(view.context)
        view.settings.userAgentString=if(enabled)normal.replace(Regex("\\(Linux; Android.*?\\)"),"(X11; Linux x86_64)").replace(" Mobile "," ") else normal
        view.reload()
    }
    fun resume(){if(!closed)view.onResume()}
    fun close(){if(closed)return;release();closed=true;(view.parent as? android.view.ViewGroup)?.removeView(view);view.stopLoading();view.destroy()}
    companion object {
        fun navigationAllowed(url:String):Boolean=runCatching {
            val u=URI(url)
            u.scheme=="https"&&(u.port==-1||u.port==443)&&u.userInfo==null&&u.host in setOf(
                "music.yandex.ru","passport.yandex.ru","passport.yandex.com","id.yandex.ru","id.yandex.com","oauth.yandex.ru")
        }.getOrDefault(false)
    }
}
