package pro.celikom.a1publicbrowserprobe;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.content.pm.ResolveInfo;
import android.media.browse.MediaBrowser;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import java.util.ArrayList;
import java.util.List;
import org.json.JSONObject;

/**
 * OWN unprivileged Android 13 read-only probe of a documented PUBLIC browser IPC.
 * Never queries catalog, sends playback commands, reads credentials or accesses DRM.
 */
public final class ProbeActivity extends Activity {
    private static final String TAG = "CELIKOM_NATIVE_IPC";
    private static final String TARGET = "ru.yandex.music";
    private static final String ACTION = "android.media.browse.MediaBrowserService";
    private final Handler handler = new Handler(Looper.getMainLooper());
    private MediaBrowser browser;
    private boolean published = false;
    private int matches = 0;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        // Bound runtime: no account data, media, titles, or private component names.
        handler.postDelayed(() -> publish("TIMEOUT_NO_BROWSER_CALLBACK", false, false), 12000);
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
            ResolveInfo target = exported.get(0);
            ComponentName component = new ComponentName(
                    target.serviceInfo.packageName, target.serviceInfo.name);
            browser = new MediaBrowser(this, component, new MediaBrowser.ConnectionCallback() {
                @Override public void onConnected() {
                    boolean root = false;
                    boolean token = false;
                    try {
                        root = browser.getRoot() != null;
                        token = browser.getSessionToken() != null;
                    } catch (RuntimeException ignored) {
                        // Fail closed, don't print third-party exception/message.
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
            JSONObject output = new JSONObject();
            output.put("status", status);
            output.put("public_browser_matches", matches);
            output.put("native_android_browser_client_executed", true);
            output.put("public_browser_root_available", root);
            output.put("public_browser_session_token_available", token);
            output.put("transport_or_custom_commands_sent", false);
            output.put("private_media_or_account_read", false);
            output.put("before_decoder_source_replacement_proven", false);
            Log.i(TAG, "RESULT " + output.toString());
        } catch (Exception ignored) {
            Log.i(TAG, "RESULT {\"status\":\"SAFE_RESULT_SERIALIZATION_FAILED\"}");
        }
        try {
            if (browser != null) browser.disconnect();
        } catch (RuntimeException ignored) {}
        finish();
    }
}
