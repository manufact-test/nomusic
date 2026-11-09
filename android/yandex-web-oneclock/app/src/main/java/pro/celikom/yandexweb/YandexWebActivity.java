package pro.celikom.yandexweb;

import android.app.*;
import android.content.*;
import android.graphics.Color;
import android.net.Uri;
import android.os.*;
import android.text.InputType;
import android.view.*;
import android.webkit.*;
import android.widget.*;

import androidx.webkit.WebMessageCompat;
import androidx.webkit.WebViewCompat;
import androidx.webkit.WebViewFeature;

import org.json.JSONObject;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/**
 * Rootless CELIKOM with the real Yandex Music website and ONE host HTMLMediaElement.
 * Never alters the installed native Yandex Music app or reads its data.
 */
public final class YandexWebActivity extends Activity {
    private static final String MUSIC_URL="https://music.yandex.ru/";
    private final String nonce=UUID.randomUUID().toString()+"-"+UUID.randomUUID();
    private WebView web;
    private TextView status;
    private Switch enabled;
    private CelikomBroker broker;
    private VirtualAudioResource audio;
    private boolean scriptAvailable;
    private String lastCelikomEmail="";
    private int lastStatusGeneration;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        broker=new CelikomBroker(this,new CelikomBroker.Listener(){
            @Override public void status(String text) {
                if(status!=null)status.setText(text);
            }
            @Override public void ready(String id,String albumId,long durationMs) {
                if(web==null||!scriptAvailable)return;
                String js="window.__CELIKOM_WEB_SOURCE_V1__ && window.__CELIKOM_WEB_SOURCE_V1__.ready("
                   +JSONObject.quote(id)+","+JSONObject.quote(albumId)+","+durationMs+","
                   +JSONObject.quote(audio.virtualUrl(id))+");";
                web.evaluateJavascript(js,null);
            }
        });
        audio=new VirtualAudioResource(broker,nonce);
        LinearLayout view=new LinearLayout(this);
        view.setOrientation(LinearLayout.VERTICAL);
        view.setBackgroundColor(Color.rgb(11,16,19));
        LinearLayout head=new LinearLayout(this);
        head.setPadding(12,7,12,7);
        head.setOrientation(LinearLayout.VERTICAL);
        TextView heading=new TextView(this);
        heading.setText("CELIKOM  /  Яндекс Музыка");
        heading.setTextSize(17);
        heading.setTextColor(Color.rgb(102,224,255));
        head.addView(heading);
        LinearLayout controls=new LinearLayout(this);
        controls.setOrientation(LinearLayout.HORIZONTAL);
        enabled=new Switch(this);
        enabled.setText("Подмена");
        enabled.setTextColor(Color.WHITE);
        enabled.setChecked(false);
        enabled.setOnCheckedChangeListener((button,value)->{
            broker.setEnabled(value);
            notifyPageEnabled();
        });
        controls.addView(enabled,new LinearLayout.LayoutParams(0,
            LinearLayout.LayoutParams.WRAP_CONTENT,1.1f));
        Button account=new Button(this);
        account.setText("Войти CELIKOM");
        account.setTextSize(11);
        controls.addView(account,new LinearLayout.LayoutParams(0,
            LinearLayout.LayoutParams.WRAP_CONTENT,1.7f));
        account.setOnClickListener(v->showCelikomLogin());
        Button logout=new Button(this);
        logout.setText("Выйти");
        logout.setTextSize(11);
        controls.addView(logout,new LinearLayout.LayoutParams(0,
            LinearLayout.LayoutParams.WRAP_CONTENT,1f));
        logout.setOnClickListener(v->{
            enabled.setChecked(false);
            broker.logout();
            if(web!=null)web.evaluateJavascript(
                "window.__CELIKOM_WEB_SOURCE_V1__&&window.__CELIKOM_WEB_SOURCE_V1__.clear();",null);
        });
        head.addView(controls);
        status=new TextView(this);
        status.setText("Открой Яндекс Музыку. Вход CELIKOM — отдельно.");
        status.setTextColor(Color.LTGRAY);
        status.setTextSize(12);
        head.addView(status);
        view.addView(head);
        web=new WebView(this);
        view.addView(web,new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,0,1));
        setContentView(view);
        initializeWeb();
    }

    private void initializeWeb() {
        WebSettings s=web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(false);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setSupportMultipleWindows(false);
        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(web,true);
        WebView.setWebContentsDebuggingEnabled(false);
        if(android.os.Build.VERSION.SDK_INT>=26)s.setSafeBrowsingEnabled(true);

        web.setWebChromeClient(new WebChromeClient());
        web.setWebViewClient(new WebViewClient(){
            @Override public WebResourceResponse shouldInterceptRequest(WebView view,WebResourceRequest request){
                return audio.intercept(request);
            }
            @Override public boolean shouldOverrideUrlLoading(WebView view,WebResourceRequest request){
                Uri url=request.getUrl();
                if(!request.isForMainFrame())return false;
                if("https".equals(url.getScheme())&&isYandex(url.getHost()))return false;
                if("https".equals(url.getScheme())||"mailto".equals(url.getScheme())){
                    try{startActivity(new Intent(Intent.ACTION_VIEW,url));}catch(Exception ignored){}
                }
                return true;
            }
            @Override public void onReceivedSslError(WebView view,SslErrorHandler handler,android.net.http.SslError error){
                handler.cancel();
                status.setText("Ошибка защищённого соединения Яндекса");
            }
            @Override public void onPageFinished(WebView view,String address){
                if(address!=null&&address.startsWith(MUSIC_URL)){
                    notifyPageEnabled();
                    broker.announceReady();
                }
            }
        });

        scriptAvailable=WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER)
            &&WebViewFeature.isFeatureSupported(WebViewFeature.DOCUMENT_START_SCRIPT);
        if(scriptAvailable){
            try{
                Set<String> trusted=Collections.singleton("https://music.yandex.ru");
                WebViewCompat.addWebMessageListener(web,"CelikomBridge",trusted,
                    (view,message,origin,isMainFrame,replyProxy)->{
                        if(!isMainFrame||origin==null||
                            !"https".equals(origin.getScheme())||
                            !"music.yandex.ru".equals(origin.getHost()))return;
                        handleBridgeMessage(message);
                    });
                WebViewCompat.addDocumentStartJavaScript(web,joinScripts(),trusted);
            }catch(Exception e){scriptAvailable=false;}
        }
        if(!scriptAvailable){
            status.setText("WebView не поддерживает безопасную загрузку модуля. Обновите Android System WebView.");
            enabled.setEnabled(false);
        }
        web.loadUrl(MUSIC_URL);
    }

    private static boolean isYandex(String host){
        if(host==null)return false;
        return host.equals("yandex.ru")||host.endsWith(".yandex.ru")||
            host.equals("yandex.com")||host.endsWith(".yandex.com")||
            host.equals("yandex.by")||host.endsWith(".yandex.by")||
            host.equals("yandex.net")||host.endsWith(".yandex.net");
    }

    private String joinScripts()throws IOException {
        StringBuilder b=new StringBuilder();
        for(String asset:new String[]{"celikom-core.js","celikom-yandex-adapter.js","celikom-web-source.js"}){
            try(InputStream in=getAssets().open(asset);
                ByteArrayOutputStream out=new ByteArrayOutputStream()){
                byte[] bytes=new byte[8192];int n;
                while((n=in.read(bytes))!=-1){
                    if(out.size()+n>131072)throw new IOException("asset size exceeded");
                    out.write(bytes,0,n);
                }
                b.append(out.toString(StandardCharsets.UTF_8.name())).append("\n;");
            }
        }
        return b.toString();
    }

    private void handleBridgeMessage(WebMessageCompat message){
        try{
            String data=message==null?null:message.getData();
            if(data==null||data.length()>512)return;
            JSONObject j=new JSONObject(data);
            String kind=j.optString("kind","");
            if("track".equals(kind)){
                String id=j.optString("id","");
                String albumId=j.optString("albumId","");
                long duration=j.optLong("durationMs",0);
                broker.prefetch(id,albumId,duration);
            }else if("selected".equals(kind)){
                status.setText("CELIKOM: версия выбрана перед воспроизведением");
            }
        }catch(Exception ignored){}
    }

    private void notifyPageEnabled(){
        if(web==null||!scriptAvailable)return;
        boolean allowed=enabled.isChecked()&&broker.signedIn();
        web.evaluateJavascript("window.__CELIKOM_WEB_SOURCE_V1__&&window.__CELIKOM_WEB_SOURCE_V1__.enable("
            +(allowed?"true":"false")+");",null);
        if(enabled.isChecked()&&!broker.signedIn()){
            status.setText("Для подмены войдите в CELIKOM");
        }
    }

    private void showCelikomLogin(){
        LinearLayout fields=new LinearLayout(this);
        fields.setOrientation(LinearLayout.VERTICAL);
        fields.setPadding(36,8,36,8);
        EditText mail=new EditText(this);
        mail.setHint("Почта CELIKOM");
        mail.setSingleLine(true);
        mail.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS);
        if(!lastCelikomEmail.isEmpty())mail.setText(lastCelikomEmail);
        fields.addView(mail);
        EditText password=new EditText(this);
        password.setSingleLine(true);
        password.setHint("Пароль CELIKOM");
        password.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);
        fields.addView(password);
        new AlertDialog.Builder(this).setTitle("Вход CELIKOM")
            .setView(fields)
            .setPositiveButton("Войти",(dialog,which)->{
                lastCelikomEmail=mail.getText().toString().trim();
                broker.login(lastCelikomEmail,password.getText().toString());
                new Handler(Looper.getMainLooper()).postDelayed(this::notifyPageEnabled,1800);
            })
            .setNeutralButton("Код почты",(dialog,which)->showVerify())
            .setNegativeButton("Отмена",null)
            .show();
    }

    private void showVerify(){
        EditText code=new EditText(this);
        code.setHint("Код подтверждения CELIKOM");
        code.setSingleLine(true);
        new AlertDialog.Builder(this).setTitle("Подтверждение CELIKOM")
            .setView(code)
            .setPositiveButton("Подтвердить",(dialog,which)->{
                broker.verify(lastCelikomEmail,code.getText().toString());
                new Handler(Looper.getMainLooper()).postDelayed(this::notifyPageEnabled,1800);
            }).setNegativeButton("Отмена",null).show();
    }
    @Override public void onBackPressed(){
        if(web!=null&&web.canGoBack())web.goBack();
        else super.onBackPressed();
    }
    @Override protected void onDestroy(){
        if(web!=null){
            web.stopLoading();
            web.loadUrl("about:blank");
            web.destroy();
            web=null;
        }
        super.onDestroy();
    }
}
