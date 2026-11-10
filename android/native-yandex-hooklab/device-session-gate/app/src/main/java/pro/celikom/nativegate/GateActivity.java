package pro.celikom.nativegate;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.content.pm.ServiceInfo;
import android.content.pm.Signature;
import android.media.session.MediaSessionManager;
import android.media.session.PlaybackState;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.graphics.Color;

import androidx.media3.common.Player;
import androidx.media3.session.MediaController;
import androidx.media3.session.SessionToken;

import com.google.common.util.concurrent.ListenableFuture;

import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * CELIKOM NEW-NATIVE feasibility gate, not an alternative audio player.
 *
 * There are deliberately NO playback/queue/network commands anywhere.
 * A public service binder is tried first with zero sensitive permissions.
 * Optionally, when the user explicitly grants notification-listener access,
 * use the platform getActiveSessions() API to inspect existing session
 * CAPABILITY FLAGS ONLY. No metadata, track ID, credentials, audio, URIs,
 * notification contents or source bytes are read or stored.
 *
 * A positive Media3 playlist command does NOT prove a publisher-approved
 * foreign source, decoder preprepare, or CELIKOM native replacement.
 */
public final class GateActivity extends Activity {
    private static final String YANDEX="ru.yandex.music";
    // Publisher certificate SHA-256 verified in original pinned #170gpr.
    private static final String PUBLISHER_CERT=
            "aca405ded8b25cb2e8c6da69425d2b4307d087c1276fc06ad5942731ccc51dba";
    private static final String[] MEDIA_ACTIONS={
            "android.media.browse.MediaBrowserService",
            "androidx.media3.session.MediaSessionService",
            "androidx.media3.session.MediaLibraryService"
    };
    private static final int DARK=0xff0b1013;
    private static final int LIGHT=0xffebf2f5;
    private static final int ACCENT=0xff66e0ff;
    private static final int MUTED=0xff96adb8;
    private final Handler main=new Handler(Looper.getMainLooper());
    private TextView result;
    private int revision;
    private ListenableFuture<SessionToken> tokenFuture;
    private ListenableFuture<MediaController> controllerFuture;
    private boolean destroyed;

    private TextView label(LinearLayout parent,String text,int size,int color){
        TextView view=new TextView(this);
        view.setText(text);
        view.setTextColor(color);
        view.setTextSize(size);
        view.setPadding(0,8,0,12);
        parent.addView(view);
        return view;
    }
    private void button(LinearLayout parent,String text,Runnable action){
        Button button=new Button(this);
        button.setText(text);
        button.setAllCaps(false);
        button.setTextColor(DARK);
        button.setBackgroundTintList(android.content.res.ColorStateList.valueOf(ACCENT));
        parent.addView(button);
        button.setOnClickListener(v->action.run());
    }
    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        getWindow().setStatusBarColor(DARK);
        getWindow().setNavigationBarColor(DARK);
        ScrollView scroll=new ScrollView(this);
        scroll.setBackgroundColor(DARK);
        LinearLayout layout=new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        int padding=(int)(20f*getResources().getDisplayMetrics().density);
        layout.setPadding(padding,padding,padding,padding);
        scroll.addView(layout);
        label(layout,"CELIKOM Native Gate",22,ACCENT);
        label(layout,"Проверка доступа к родной MediaSession Яндекс.Музыки. "
                +"Никакой подмены, второго плеера или команд воспроизведения.",14,LIGHT);
        button(layout,"1. Проверить без дополнительных разрешений",
                ()->startPublicCheck());
        button(layout,"2. Проверить активную сессию (по желанию)",
                ()->startActiveSessionCheck());
        label(layout,"Второй способ требует разрешения Android «Доступ к уведомлениям». "
                +"Это широкое разрешение: система позволяет такому приложению читать "
                +"уведомления устройства. Наш код их НЕ читает, НЕ сохраняет и НЕ отправляет, "
                +"но разрешение можно не выдавать. Если Android блокирует доступ, "
                +"не обходи системные ограничения.",12,MUTED);
        button(layout,"Настройки доступа к уведомлениям",
                ()->openListenerSettings());
        result=label(layout,"Готов к проверке. Сначала запусти музыку в Яндексе "
                +"и нажми первую кнопку. Проверка ничего не переключит.",14,LIGHT);
        setContentView(scroll);
    }

    private void show(String state,String details){
        if(destroyed)return;
        result.setText("Результат: "+state+"\n\n"+details
                +"\n\nВажно: это только доступные публичные команды. "
                +"Даже команда смены элементов не доказывает право "
                +"заменить аудиоисточник Яндекса до декодера.");
    }

    private void reset(){
        revision++;
        if(controllerFuture!=null){
            try{MediaController.releaseFuture(controllerFuture);}catch(Throwable ignored){}
            controllerFuture=null;
        }
        if(tokenFuture!=null){
            tokenFuture.cancel(true);
            tokenFuture=null;
        }
    }

    @SuppressWarnings("deprecation")
    private String verifyPublisher(){
        try{
            PackageManager pm=getPackageManager();
            PackageInfo pkg=pm.getPackageInfo(YANDEX,
                    PackageManager.GET_SIGNING_CERTIFICATES);
            if(pkg.signingInfo==null)return "SIGNING_INFO_UNAVAILABLE";
            Signature[] signers=pkg.signingInfo.getApkContentsSigners();
            if(signers==null||signers.length!=1)return "AMBIGUOUS_SIGNER";
            MessageDigest hash=MessageDigest.getInstance("SHA-256");
            byte[] bytes=hash.digest(signers[0].toByteArray());
            StringBuilder fingerprint=new StringBuilder(64);
            for(byte item:bytes)
                fingerprint.append(Character.forDigit((item>>>4)&15,16))
                        .append(Character.forDigit(item&15,16));
            if(!PUBLISHER_CERT.equals(fingerprint.toString()))
                return "UNKNOWN_PUBLISHER_SIGNER";
            return null;
        }catch(PackageManager.NameNotFoundException error){
            return "YANDEX_NOT_INSTALLED";
        }catch(Throwable error){
            return "PUBLISHER_CHECK_UNAVAILABLE";
        }
    }

    private void startPublicCheck(){
        reset();
        int task=revision;
        String blocked=verifyPublisher();
        if(blocked!=null){
            show(blocked,"Проверяем только настоящий установленный Яндекс.");
            return;
        }
        try{
            PackageManager pm=getPackageManager();
            Map<String,ComponentName> exported=new HashMap<>();
            for(String action:MEDIA_ACTIONS){
                Intent intent=new Intent(action).setPackage(YANDEX);
                List<ResolveInfo> results=pm.queryIntentServices(intent,0);
                for(ResolveInfo info:results){
                    ServiceInfo service=info.serviceInfo;
                    if(service==null||!YANDEX.equals(service.packageName)
                            ||!service.exported||!service.enabled
                            ||service.permission!=null
                            ||service.applicationInfo==null
                            ||!service.applicationInfo.enabled
                            ||service.applicationInfo.permission!=null)continue;
                    exported.put(service.name,
                            new ComponentName(service.packageName,service.name));
                }
            }
            if(exported.size()!=1){
                show(exported.isEmpty()?"NO_PUBLIC_SERVICE":"AMBIGUOUS_PUBLIC_SERVICES",
                        "Без дополнительного разрешения найдено подходящих публичных "
                        +"сервисов: "+exported.size()
                        +". Не выбираю произвольный сервис.");
                return;
            }
            show("CONNECTING_PUBLIC","Пытаюсь только соединиться с публичной сессией.");
            SessionToken token=new SessionToken(this,
                    exported.values().iterator().next());
            connectController(token,task,"PUBLIC_BIND");
        }catch(Throwable error){
            show("PUBLIC_SERVICE_UNAVAILABLE","Соединение не установлено.");
        }
    }

    private void startActiveSessionCheck(){
        reset();
        int task=revision;
        String blocked=verifyPublisher();
        if(blocked!=null){
            show(blocked,"Настоящий подписанный Яндекс не подтверждён.");
            return;
        }
        try{
            MediaSessionManager manager=
                    (MediaSessionManager)getSystemService(MEDIA_SESSION_SERVICE);
            ComponentName listener=new ComponentName(this,NativeSessionListener.class);
            List<android.media.session.MediaController> sessions=
                    manager.getActiveSessions(listener);
            List<android.media.session.MediaController> yandex=new ArrayList<>();
            for(android.media.session.MediaController item:sessions)
                if(YANDEX.equals(item.getPackageName()))yandex.add(item);
            if(yandex.size()!=1){
                show(yandex.isEmpty()?"NO_ACTIVE_YANDEX_SESSION"
                                   :"MULTIPLE_YANDEX_SESSIONS",
                        "Проверка нашла сессий Яндекса: "+yandex.size()
                        +". Запусти обычное воспроизведение в Яндексе и вернись сюда.");
                return;
            }
            android.media.session.MediaController platform=yandex.get(0);
            PlaybackState state=platform.getPlaybackState();
            long actions=state==null?0L:state.getActions();
            final boolean uri=(actions&PlaybackState.ACTION_PLAY_FROM_URI)!=0L;
            final boolean mediaId=
                    (actions&PlaybackState.ACTION_PLAY_FROM_MEDIA_ID)!=0L;
            final boolean pause=(actions&PlaybackState.ACTION_PLAY_PAUSE)!=0L;
            String flags="Публичные platform actions:"
                    +"\nPLAY_FROM_URI="+uri
                    +"\nPLAY_FROM_MEDIA_ID="+mediaId
                    +"\nPLAY_PAUSE="+pause
                    +"\nНикаких команд Яндексу не отправлено.";
            show("PLATFORM_SESSION_FOUND",flags);
            // Only convert a genuine platform session token into a READ-ONLY
            // Media3 controller, to inspect advertised playlist permissions.
            tokenFuture=SessionToken.createSessionToken(
                    this,platform.getSessionToken());
            final ListenableFuture<SessionToken> future=tokenFuture;
            future.addListener(()->{
                if(!active(task))return;
                try{
                    SessionToken token=future.get();
                    connectController(token,task,flags);
                }catch(Throwable ignored){
                    show("MEDIA3_TOKEN_UNAVAILABLE",flags
                            +"\nMedia3 команды этой сессии недоступны.");
                }
            },getMainExecutor());
            main.postDelayed(()->{
                if(active(task)&&controllerFuture==null)
                    show("MEDIA3_TOKEN_TIMEOUT",flags
                            +"\nСессия платформы доступна, Media3 не подтвердился.");
            },12000L);
        }catch(SecurityException denied){
            show("NOTIFICATION_ACCESS_NOT_GRANTED",
                    "Android не разрешил смотреть активные media sessions. "
                    +"Второй режим необязателен; первый не требует этого доступа.");
        }catch(Throwable error){
            show("ACTIVE_SESSION_UNAVAILABLE",
                    "Список сессий недоступен. Приложение Яндекса не изменено.");
        }
    }

    private boolean active(int task){return !destroyed&&revision==task;}

    private void connectController(SessionToken token,int task,String origin){
        if(!active(task))return;
        try{
            controllerFuture=new MediaController.Builder(this,token).buildAsync();
            final ListenableFuture<MediaController> future=controllerFuture;
            future.addListener(()->{
                if(!active(task)){
                    MediaController.releaseFuture(future);
                    return;
                }
                try{
                    MediaController controller=future.get();
                    if(!controller.isConnected()){
                        show("MEDIA3_NOT_CONNECTED",origin
                                +"\nMedia3 контроллер отклонён владельцем сессии.");
                        return;
                    }
                    boolean change=controller.isCommandAvailable(
                            Player.COMMAND_CHANGE_MEDIA_ITEMS);
                    boolean setItem=controller.isCommandAvailable(
                            Player.COMMAND_SET_MEDIA_ITEM);
                    boolean getItem=controller.isCommandAvailable(
                            Player.COMMAND_GET_CURRENT_MEDIA_ITEM);
                    boolean play=controller.isCommandAvailable(
                            Player.COMMAND_PLAY_PAUSE);
                    boolean seek=controller.isCommandAvailable(
                            Player.COMMAND_SEEK_IN_CURRENT_MEDIA_ITEM);
                    show("MEDIA3_CONNECTED_READONLY",origin
                            +"\n\nMedia3 flags:"
                            +"\nCHANGE_MEDIA_ITEMS="+change
                            +"\nSET_MEDIA_ITEM="+setItem
                            +"\nGET_CURRENT_ITEM="+getItem
                            +"\nPLAY_PAUSE="+play
                            +"\nSEEK="+seek
                            +"\nВызовов setMediaItems / play / seek НЕ было.");
                }catch(Throwable ignored){
                    show("MEDIA3_CONNECTION_FAILED",origin
                            +"\nMedia3 API не дал проверенного соединения.");
                }finally{
                    try{MediaController.releaseFuture(future);}catch(Throwable ignored){}
                    if(controllerFuture==future)controllerFuture=null;
                }
            },getMainExecutor());
            main.postDelayed(()->{
                if(active(task)&&controllerFuture==future){
                    show("MEDIA3_CONNECT_TIMEOUT",origin
                            +"\nВремя ожидания публичного контроллера истекло.");
                    try{MediaController.releaseFuture(future);}catch(Throwable ignored){}
                    controllerFuture=null;
                }
            },12000L);
        }catch(Throwable ignored){
            show("MEDIA3_CONNECT_UNAVAILABLE",origin
                    +"\nПодключение не поддерживается этой сессией.");
        }
    }

    private void openListenerSettings(){
        try{
            startActivity(new Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS));
        }catch(Throwable ignored){
            show("SETTINGS_UNAVAILABLE","Android не открыл настройки разрешения.");
        }
    }
    @Override protected void onDestroy(){
        destroyed=true;
        reset();
        super.onDestroy();
    }
}
