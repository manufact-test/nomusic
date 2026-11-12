package pro.celikom.a1publicbrowserprobe;

import android.app.Service;
import android.content.ComponentName;
import android.content.Intent;
import android.content.pm.ResolveInfo;
import android.media.browse.MediaBrowser;
import android.os.Binder;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.util.Log;
import java.util.ArrayList;
import java.util.List;
import org.json.JSONObject;

/**
 * CELIKOM-owned, short-lived, read-only Android MediaBrowser probe.
 * This Service intentionally starts *after* the launching Activity exits,
 * preserving the genuine Yandex Activity in front. This controls for
 * the previous probe taking foreground away from the media application.
 *
 * Uses only Android public MediaBrowser API and no permissions, account,
 * media catalog, controller command, custom action, audio or source access.
 */
public final class PublicBrowserProbeService extends Service {
    private static final String TAG = "CELIKOM_NATIVE_IPC";
    private static final String TARGET = "ru.yandex.music";
    private static final String ACTION = "android.media.browse.MediaBrowserService";
    private static final long LAUNCHER_FINISH_DELAY_MS = 3500;
    private static final long SAFETY_TIMEOUT_MS = 12000;

    private final Handler handler = new Handler(Looper.getMainLooper());
    private MediaBrowser browser;
    private boolean published = false;
    private int matches = 0;

    @Override public IBinder onBind(Intent intent) {
        return null; // Not an exported binder; no SDK/virtualization APIs.
    }

    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        handler.postDelayed(() -> publish("TIMEOUT_NO_BROWSER_CALLBACK", false, false),
                SAFETY_TIMEOUT_MS);
        handler.postDelayed(this::connectPublicBrowser, LAUNCHER_FINISH_DELAY_MS);
        return START_NOT_STICKY;
    }

    private void connectPublicBrowser() {
        if (published) return;
        try {
            Intent search = new Intent(ACTION).setPackage(TARGET);
            List<ResolveInfo> services = getPackageManager().queryIntentServices(search, 0);
            List<ResolveInfo> exported = new ArrayList<>();
            for (ResolveInfo entry : services) {
                if (entry.serviceInfo != null && entry.serviceInfo.exported
                        && TARGET.equals(entry.serviceInfo.packageName)
                        && entry.serviceInfo.permission == null) {
                    exported.add(entry);
                }
            }
            matches = exported.size();
            if (matches != 1) {
                publish("PUBLIC_BROWSER_NOT_UNAMBIGUOUS", false, false);
                return;
            }
            ResolveInfo resolved = exported.get(0);
            ComponentName component = new ComponentName(
                    resolved.serviceInfo.packageName, resolved.serviceInfo.name);
            browser = new MediaBrowser(this, component, new MediaBrowser.ConnectionCallback() {
                @Override public void onConnected() {
                    boolean root = false;
                    boolean token = false;
                    try {
                        root = browser.getRoot() != null;
                        token = browser.getSessionToken() != null;
                    } catch (RuntimeException ignored) {
                        // Never print third-party account or player exceptions.
                    }
                    publish("CONNECTED", root, token);
                }
                @Override public void onConnectionFailed() {
                    publish("CONNECTION_REJECTED", false, false);
                }
                @Override public void onConnectionSuspended() {
                    publish("CONNECTION_SUSPENDED", false, false);
                }
            }, null);
            browser.connect();
        } catch (SecurityException ignored) {
            publish("PLATFORM_PERMISSION_DENIED", false, false);
        } catch (RuntimeException ignored) {
            publish("PUBLIC_BROWSER_RUNTIME_ERROR", false, false);
        }
    }

    private void publish(String status, boolean root, boolean token) {
        if (published) return;
        published = true;
        try {
            JSONObject result = new JSONObject();
            result.put("status", status);
            result.put("public_browser_matches", matches);
            result.put("native_android_browser_client_executed", true);
            result.put("probe_uses_service_not_foreground_activity", true);
            result.put("public_browser_root_available", root);
            result.put("public_browser_session_token_available", token);
            result.put("transport_or_custom_commands_sent", false);
            result.put("private_media_or_account_read", false);
            result.put("before_decoder_source_replacement_proven", false);
            Log.i(TAG, "RESULT " + result.toString());
        } catch (Exception ignored) {
            Log.i(TAG, "RESULT {\"status\":\"SAFE_RESULT_SERIALIZATION_FAILED\"}");
        } finally {
            try {
                if (browser != null) browser.disconnect();
            } catch (RuntimeException ignored) {}
            handler.removeCallbacksAndMessages(null);
            stopSelf();
        }
    }

    @Override public void onDestroy() {
        try {
            if (browser != null) browser.disconnect();
        } catch (RuntimeException ignored) {}
        handler.removeCallbacksAndMessages(null);
        super.onDestroy();
    }
}
