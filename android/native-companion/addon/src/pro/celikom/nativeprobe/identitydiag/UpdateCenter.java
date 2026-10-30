package pro.celikom.nativeprobe.identitydiag;

import android.app.*;
import android.app.job.*;
import android.content.*;
import android.content.pm.*;
import android.net.Uri;
import android.os.*;
import android.provider.Settings;
import android.view.View;
import android.widget.*;
import org.json.JSONObject;
import java.io.*;
import java.net.*;
import java.security.MessageDigest;
import java.security.cert.Certificate;
import java.util.Locale;
import java.util.concurrent.*;
import javax.net.ssl.HttpsURLConnection;

/** Isolated sideload update client; never touches audio state or accounts. */
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
        refresh=activity.button(region,"Проверить обновления",()->check(true),false);
        install=activity.button(region,"Скачать и установить",this::download,false);
        later=activity.button(region,"Позже",()->{candidate=null;render("Напомним позже");},false);
        render("CELIKOM "+AppVersion.NAME+" · Проверить обновления");
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
        Release(int c,String n,String u,String h,String t,long s){code=c;name=n;url=u;sha=h;notes=t;size=s;}
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
        return new Release(code,name,url,sha,notes,size);
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
    void check(boolean manual) {
        if (busy)return;
        long now=System.currentTimeMillis();
        android.content.SharedPreferences p=activity.getSharedPreferences("update-center",0);
        if(!manual && now-p.getLong("checked",0)<INTERVAL)return;
        busy=true;checking=true;upToDate=false;
        final long started=SystemClock.elapsedRealtime();
        final int generation=++checkGeneration;
        render("Проверяем наличие обновлений…");
        IO.execute(()->{
            Release r=null;String error=null;
            try {r=fetch(activity.getApplicationContext());
                p.edit().putLong("checked",System.currentTimeMillis()).apply();
            }catch(Exception e){error="Не удалось проверить обновления";}
            final Release found=r;final String failure=error;
            long remaining=Math.max(0,MIN_CHECK_DISPLAY_MS-(SystemClock.elapsedRealtime()-started));
            MAIN.postDelayed(()->{
                if(generation!=checkGeneration)return;
                busy=false;checking=false;
                if(!activity.visible())return;
                candidate=found;
                upToDate=failure==null && found==null;
                render(failure!=null?"Не удалось проверить обновления":upToDate?"У вас последняя версия CELIKOM · "+AppVersion.NAME:"Доступна CELIKOM "+found.name+"\n"+found.notes);
                if(found!=null)notifyAvailable(activity,found);
            },remaining);
        });
    }
    void render(String message) {
        summary.setText(message);
        summary.setTextColor(upToDate?RecorderActivity.MINT:RecorderActivity.MUTED);
        install.setVisibility(candidate==null?View.GONE:View.VISIBLE);
        later.setVisibility(candidate==null?View.GONE:View.VISIBLE);refresh.setEnabled(!busy);install.setEnabled(!busy);
    }
    static String sha(byte[] bytes) throws Exception {
        MessageDigest d=MessageDigest.getInstance("SHA-256");d.update(bytes);return hex(d.digest());
    }
    static String hex(byte[] bytes) {
        StringBuilder b=new StringBuilder(bytes.length*2);
        for(byte n:bytes)b.append(String.format(Locale.ROOT,"%02x",n&255));
        return b.toString();
    }
    static void verifyApk(Context context,File apk,Release r) throws Exception {
        PackageManager pm=context.getPackageManager();
        PackageInfo p=pm.getPackageArchiveInfo(apk.getAbsolutePath(),PackageManager.GET_SIGNING_CERTIFICATES);
        if(p==null || !context.getPackageName().equals(p.packageName)
             || (Build.VERSION.SDK_INT>=28?p.getLongVersionCode():p.versionCode)!=r.code
             || p.signingInfo==null)throw new SecurityException("APK package/version mismatch");
        android.content.pm.Signature[] signatures=p.signingInfo.getApkContentsSigners();
        if(signatures==null || signatures.length!=1 || !CERT.equals(sha(signatures[0].toByteArray())))
            throw new SecurityException("Подпись APK не совпадает");
    }
    void download() {
        Release r=candidate;if(r==null || busy)return;
        if(Build.VERSION.SDK_INT>=26 && !activity.getPackageManager().canRequestPackageInstalls()){
            Intent i=new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,Uri.parse("package:"+activity.getPackageName()));
            activity.startActivity(i);
            render("Разрешите установку из CELIKOM, затем повторите скачивание");
            return;
        }
        busy=true;render("Загружаем CELIKOM "+r.name+"…");
        IO.execute(()->{
            File tmp=null;
            try {
                if(activity.getCacheDir().getUsableSpace()<r.size*2)throw new IOException("Недостаточно памяти");
                tmp=File.createTempFile("celikom-update-",".apk",activity.getCacheDir());
                MessageDigest digest=MessageDigest.getInstance("SHA-256");
                long total=0;
                HttpsURLConnection c=connect(r.url);
                try(InputStream in=c.getInputStream();FileOutputStream out=new FileOutputStream(tmp)){
                    byte[] b=new byte[32768];int n;
                    while((n=in.read(b))!=-1){
                        total+=n;if(total>r.size||total>MAX_APK)throw new IOException("Oversized APK");
                        out.write(b,0,n);digest.update(b,0,n);
                    }
                    out.getFD().sync();
                }finally{c.disconnect();}
                if(total!=r.size||!r.sha.equals(hex(digest.digest())))throw new SecurityException("Контрольная сумма не совпадает");
                verifyApk(activity.getApplicationContext(),tmp,r);
                installSession(activity.getApplicationContext(),tmp,r);
                MAIN.post(()->{busy=false;if(activity.visible())render("APK проверена. Подтвердите установку в Android.");});
            } catch(Exception e){
                final String msg=e instanceof SecurityException?"Проверка APK не пройдена":"Загрузка или установка не удалась";
                MAIN.post(()->{busy=false;if(activity.visible())render(msg);});
            }finally{if(tmp!=null)tmp.delete();}
        });
    }
    static void installSession(Context ctx,File apk,Release r) throws Exception {
        PackageInstaller installer=ctx.getPackageManager().getPackageInstaller();
        PackageInstaller.SessionParams params=new PackageInstaller.SessionParams(PackageInstaller.SessionParams.MODE_FULL_INSTALL);
        params.setAppPackageName(ctx.getPackageName());
        params.setSize(r.size);
        int id=installer.createSession(params);
        boolean committed=false;
        try(PackageInstaller.Session session=installer.openSession(id)){
            try(InputStream in=new FileInputStream(apk);
                OutputStream out=session.openWrite("CELIKOM.apk",0,r.size)){
                byte[] b=new byte[32768];int n;
                while((n=in.read(b))!=-1)out.write(b,0,n);
                session.fsync(out);
            }
            Intent callback=new Intent(ctx,UpdateInstallReceiver.class);
            callback.setAction("pro.celikom.nativeprobe.UPDATE_INSTALL");
            callback.putExtra("expectedCode",r.code);
            PendingIntent pending=PendingIntent.getBroadcast(ctx,id,callback,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_MUTABLE);
            session.commit(pending.getIntentSender());
            committed=true;
        } finally {if(!committed)installer.abandonSession(id);}
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
