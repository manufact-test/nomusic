package pro.celikom.nativeprobe.identitydiag;

import android.app.*;
import android.app.job.*;
import android.content.*;
import android.content.pm.*;
import android.net.Uri;
import android.os.*;
import android.view.View;
import android.widget.*;
import org.json.JSONObject;
import java.io.*;
import java.net.*;
import java.util.Locale;
import java.util.HashMap;
import java.util.Map;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.concurrent.*;
import javax.net.ssl.HttpsURLConnection;

/** Update discovery and user-initiated browser download; cannot install APKs itself. */
final class UpdateCenter {
    static final String HOST="lemonchiffon-narwhal-791953.hostingersite.com";
    static final String MANIFEST="https://"+HOST+"/updates/android/stable.json";
    static final String CERT="67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f";
    static final String CHANNEL="celikom_app_updates";
    static final int NOTIFICATION_ID=7855, JOB_ID=7856;
    static final long INTERVAL=6*60*60*1000L;
    static final long MAX_APK=200L*1024*1024;
    static final ExecutorService IO=Executors.newSingleThreadExecutor();
    static final Handler MAIN=new Handler(Looper.getMainLooper());
    final RecorderActivity activity;
    final LinearLayout region;
    final TextView summary;
    final Button refresh, install, later;
    volatile Release candidate;
    volatile boolean busy;
    static final long MIN_CHECK_DISPLAY_MS=1500L;
    int checkGeneration;
    boolean checking;
    boolean upToDate;
    UpdateCenter(RecorderActivity activity, LinearLayout region) {
        this.activity=activity;this.region=region;
        summary=activity.label(region,"Проверяем наличие обновлений…",13,RecorderActivity.MUTED);
        summary.setMinHeight(activity.dp(48));
        summary.setGravity(android.view.Gravity.CENTER_VERTICAL);
        summary.setPadding(0,activity.dp(8),0,activity.dp(8));
        refresh=activity.button(region,"Проверить обновление",()->check(true),false);
        install=activity.button(region,"Скачать обновление",this::download,false);
        later=activity.button(region,"Позже",this::deferUpdate,false);
        candidate=loadCandidate(activity);
        UpdateState cached=readState(activity);
        int current=installed(activity);
        boolean recent=cached.shouldSkipAutomaticCheck(System.currentTimeMillis(),INTERVAL,current);
        upToDate=candidate==null&&cached.isVerifiedLatestFor(current)&&recent;
        String initial=candidate!=null?availableMessage(candidate)
            :upToDate?"У вас последняя версия CELIKOM"
            :cached.checkedAt>0?staleMessage(cached.checkedAt):"Статус обновлений ещё не проверен";
        render(initial);
        schedule(activity);
        check(false);
    }
    static int installed(Context ctx) {
        try { PackageInfo p=ctx.getPackageManager().getPackageInfo(ctx.getPackageName(),0);
            return Build.VERSION.SDK_INT>=28?(int)p.getLongVersionCode():p.versionCode;
        } catch(Exception e){return 0;}
    }
    static final class Release {
        final int code; final String name,url,sha,notes; final long size;
        final String manifestJson;
        Release(int c,String n,String u,String h,String t,long s){this(c,n,u,h,t,s,null);}
        Release(int c,String n,String u,String h,String t,long s,String raw){
            code=c;name=n;url=u;sha=h;notes=t;size=s;manifestJson=raw;
        }
    }
    static Release parse(JSONObject j,int current) throws Exception {
        if (j.getInt("schemaVersion")!=1 || !j.getBoolean("enabled")
           || !"stable".equals(j.getString("channel"))
           || !"pro.celikom.nativeprobe".equals(j.getString("packageName"))
           || !CERT.equals(j.getString("signerSha256"))) throw new SecurityException("Неверный источник обновления");
        int code=j.getInt("versionCode");
        if (code<=current)return null;
        String name=j.getString("versionName"),url=j.getString("apkUrl"),sha=j.getString("apkSha256").toLowerCase(Locale.ROOT);
        String notes=j.getString("notesRu");
        long size=j.getLong("sizeBytes");
        if (!name.matches("0\\.3\\.[0-9]{1,4}") || !sha.matches("[a-f0-9]{64}")
          || size<100000 || size>MAX_APK || notes.length()>800
          || notes.contains("<") || notes.contains(">")
          || j.getInt("minSdk")>Build.VERSION.SDK_INT
          || !url.equals("https://"+HOST+"/releases/android/"+code+"-"+sha+".apk"))
            throw new SecurityException("Некорректный релиз");
        return new Release(code,name,url,sha,notes,size,j.toString());
    }
    static HttpsURLConnection connect(String url) throws Exception {
        URL target=new URL(url);
        if (!"https".equals(target.getProtocol()) || !HOST.equals(target.getHost())
            || target.getPort()!=-1 || target.getUserInfo()!=null || target.getRef()!=null)
            throw new SecurityException("Недоверенный адрес");
        HttpsURLConnection c=(HttpsURLConnection)target.openConnection();
        c.setConnectTimeout(10000);c.setReadTimeout(20000);c.setInstanceFollowRedirects(false);
        c.setRequestProperty("Accept-Encoding","identity");
        if(c.getResponseCode()!=200){c.disconnect();throw new IOException("HTTP "+c.getResponseCode());}
        return c;
    }
    static Release fetch(Context context) throws Exception {
        HttpsURLConnection c=connect(MANIFEST);
        try (InputStream stream=c.getInputStream();ByteArrayOutputStream b=new ByteArrayOutputStream()) {
            byte[] buffer=new byte[4096];int n;
            while((n=stream.read(buffer))!=-1){b.write(buffer,0,n);if(b.size()>16384)throw new IOException("Manifest too large");}
            return parse(new JSONObject(b.toString("UTF-8")),installed(context));
        } finally {c.disconnect();}
    }
    static UpdateState readState(Context context) {
        android.content.SharedPreferences p=context.getSharedPreferences("update-center",0);
        Map<String,Object> values=new HashMap<>();
        values.put("checked",p.getLong("checked",0));
        values.put("verifiedInstalledCode",p.getInt("verifiedInstalledCode",-1));
        values.put("verifiedLatest",p.getBoolean("verifiedLatest",false));
        values.put("availableCode",p.getInt("availableCode",0));
        values.put("availableManifest",p.getString("availableManifest",null));
        return UpdateState.restore(values,installed(context));
    }
    static void writeState(Context context,UpdateState state) {
        android.content.SharedPreferences.Editor edit=context.getSharedPreferences("update-center",0).edit()
            .putLong("checked",state.checkedAt)
            .putInt("verifiedInstalledCode",state.verifiedInstalledCode)
            .putBoolean("verifiedLatest",state.verifiedLatest)
            .putInt("availableCode",state.availableCode);
        if(state.availableManifest!=null)edit.putString("availableManifest",state.availableManifest);
        else edit.remove("availableManifest");
        edit.apply();
    }
    static void recordSuccessfulCheck(Context context,Release release) {
        int current=installed(context);
        UpdateState previous=readState(context);
        UpdateState next=previous.successfulCheck(current,release==null?0:release.code,
            release==null?null:release.manifestJson,System.currentTimeMillis());
        writeState(context,next);
    }
    static Release loadCandidate(Context context) {
        UpdateState state=readState(context);
        int current=installed(context);
        if(!state.hasAvailable(current)) {
            android.content.SharedPreferences p=context.getSharedPreferences("update-center",0);
            if(p.getInt("availableCode",0)!=0||p.getString("availableManifest",null)!=null)
                writeState(context,state.clearCandidate());
            return null;
        }
        try {
            Release stored=parse(new JSONObject(state.availableManifest),current);
            if(stored==null||stored.code!=state.availableCode)
                throw new SecurityException("Stored update candidate mismatch");
            return stored;
        } catch(Exception invalid) {
            writeState(context,state.clearCandidate());
            return null;
        }
    }
    static String availableMessage(Release release) {
        return "Доступна новая версия CELIKOM "+release.name+"\n"+release.notes;
    }
    static String checkedAt(long time) {
        return new SimpleDateFormat("dd.MM.yyyy HH:mm",Locale.ROOT).format(new Date(time));
    }
    static String staleMessage(long time) {
        return "Последняя проверка: "+checkedAt(time)+"\nПроверяем актуальность версии…";
    }
    void check(boolean manual) {
        if (busy)return;
        long now=System.currentTimeMillis();
        UpdateState cached=readState(activity);
        if(!manual&&cached.shouldSkipAutomaticCheck(now,INTERVAL,installed(activity)))return;
        busy=true;checking=true;upToDate=false;
        final long started=SystemClock.elapsedRealtime();
        final int generation=++checkGeneration;
        render(candidate!=null?availableMessage(candidate)+"\nПроверяем актуальность…":"Проверяем наличие обновлений…");
        IO.execute(()->{
            Context context=activity.getApplicationContext();
            Release r=null;String error=null;
            try {r=fetch(context);recordSuccessfulCheck(context,r);}
            catch(Exception e){error="Не удалось проверить обновления";}
            final Release found=r;final String failure=error;
            long remaining=Math.max(0,MIN_CHECK_DISPLAY_MS-(SystemClock.elapsedRealtime()-started));
            MAIN.postDelayed(()->{
                if(generation!=checkGeneration)return;
                busy=false;checking=false;
                if(!activity.visible())return;
                if(failure!=null) {
                    candidate=loadCandidate(context);
                    UpdateState state=readState(context);
                    int current=installed(context);
                    boolean recent=state.shouldSkipAutomaticCheck(System.currentTimeMillis(),INTERVAL,current);
                    upToDate=candidate==null&&state.isVerifiedLatestFor(current)&&recent;
                    if(candidate!=null)
                        render(availableMessage(candidate)+"\nНе удалось обновить проверку; найденная версия сохранена");
                    else if(upToDate)
                        render("У вас последняя версия CELIKOM\nПоследняя успешная проверка: "+checkedAt(state.checkedAt)+"\nНе удалось обновить проверку");
                    else render("Не удалось проверить обновления");
                } else {
                    candidate=found;
                    upToDate=found==null;
                    render(found==null?"У вас последняя версия CELIKOM":availableMessage(found));
                    if(found!=null)notifyAvailable(context,found);
                }
            },remaining);
        });
    }
    void deferUpdate() {
        Release found=candidate;
        if(found==null)return;
        NotificationManager manager=activity.getSystemService(NotificationManager.class);
        if(manager!=null)manager.cancel(NOTIFICATION_ID);
        render("Доступна новая версия CELIKOM "+found.name+"\nОбновление сохранено. Можно установить позже.");
    }
    void render(String message) {
        if(candidate!=null&&message!=null&&!message.contains(candidate.name))
            message=availableMessage(candidate)+"\n"+message;
        summary.setText(message);
        summary.setTextColor(upToDate?RecorderActivity.MINT:RecorderActivity.MUTED);
        install.setVisibility(candidate==null?View.GONE:View.VISIBLE);
        later.setVisibility(candidate==null?View.GONE:View.VISIBLE);
        refresh.setEnabled(!busy);install.setEnabled(!busy);later.setEnabled(!busy);
    }
    void download() {
        Release r=candidate;if(r==null || busy)return;
        // Open only the validated HTTPS release URL in a user-selected browser.
        // The application never requests APK-install permission or installs other apps.
        Intent external=new Intent(Intent.ACTION_VIEW,Uri.parse(r.url));
        external.addCategory(Intent.CATEGORY_BROWSABLE);
        try {
            activity.startActivity(external);
            render("Откройте скачанную APK из браузера. Android проверит подпись и попросит подтверждение установки.");
        } catch(ActivityNotFoundException noBrowser) {
            render("Не найден браузер для загрузки обновления CELIKOM "+r.name);
        }
    }
    static void ensureChannel(Context ctx) {
        NotificationManager nm=ctx.getSystemService(NotificationManager.class);
        nm.createNotificationChannel(new NotificationChannel(CHANNEL,"Обновления CELIKOM",NotificationManager.IMPORTANCE_DEFAULT));
    }
    static void notifyAvailable(Context ctx,Release r) {
        if(Build.VERSION.SDK_INT>=33 && ctx.checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)return;
        android.content.SharedPreferences p=ctx.getSharedPreferences("update-center",0);
        if(p.getInt("notified",0)>=r.code)return;
        ensureChannel(ctx);
        Intent view=new Intent(ctx,RecorderActivity.class);
        view.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent pi=PendingIntent.getActivity(ctx,7855,view,PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        Notification n=new Notification.Builder(ctx,CHANNEL)
          .setSmallIcon(android.R.drawable.stat_sys_download_done)
          .setContentTitle("CELIKOM "+r.name+" доступна")
          .setContentText(r.notes).setStyle(new Notification.BigTextStyle().bigText(r.notes))
          .setContentIntent(pi).setAutoCancel(true).build();
        ctx.getSystemService(NotificationManager.class).notify(NOTIFICATION_ID,n);
        p.edit().putInt("notified",r.code).apply();
    }
    static void schedule(Context ctx){
        JobScheduler scheduler=ctx.getSystemService(JobScheduler.class);
        JobInfo job=new JobInfo.Builder(JOB_ID,new ComponentName(ctx,UpdateCheckJob.class))
          .setRequiredNetworkType(JobInfo.NETWORK_TYPE_ANY)
          .setPersisted(false).setPeriodic(INTERVAL).build();
        scheduler.schedule(job);
    }
}
