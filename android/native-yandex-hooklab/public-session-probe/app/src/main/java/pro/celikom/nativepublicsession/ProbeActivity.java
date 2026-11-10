package pro.celikom.nativepublicsession;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.content.pm.ServiceInfo;
import android.media.browse.MediaBrowser;
import android.media.session.PlaybackState;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;

import androidx.media3.common.Player;
import androidx.media3.session.MediaController;
import androidx.media3.session.SessionToken;

import com.google.common.util.concurrent.ListenableFuture;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Read-only platform MediaSession capability observer. Own APK, no hook or
 * player and no commands that would mutate a publisher-owned media session.
 * Only run on a disposable emulator with the genuine pinned source app.
 */
public final class ProbeActivity extends Activity {
    private static final String TAG = "CELIKOMPublicSessionProbe";
    private static final String YANDEX = "ru.yandex.music";
    private static final String NAME = "2026.10.3 #170gpr";
    private static final long CODE = 24026531L;
    private static final String[] ACTIONS = {
        "android.media.browse.MediaBrowserService",
        "androidx.media3.session.MediaSessionService",
        "androidx.media3.session.MediaLibraryService",
    };
    private final AtomicBoolean finished = new AtomicBoolean();
    private final Handler main = new Handler(Looper.getMainLooper());
    private ListenableFuture<MediaController> future;
    private ComponentName serviceComponent;
    private MediaBrowser browser;
    private boolean browserConnected, platformPlayFromUri, platformPlayFromMediaId;
    private int eligible;
    private boolean sessionConnected;
    private boolean changeItems;
    private boolean setItem;
    private boolean getItem;
    private boolean playPause;
    private boolean seek;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        // No file system, private app state or account access; only package
        // manager's publicly exported binder declarations are inspected.
        try {
            PackageManager pm = getPackageManager();
            PackageInfo target = pm.getPackageInfo(YANDEX, 0);
            if (!NAME.equals(target.versionName) || target.getLongVersionCode() != CODE) {
                complete("VERSION_UNPINNED");
                return;
            }
            Map<String, ComponentName> possible = new HashMap<>();
            for (String action : ACTIONS) {
                Intent intent = new Intent(action).setPackage(YANDEX);
                List<ResolveInfo> results = pm.queryIntentServices(intent, 0);
                for (ResolveInfo resolved : results) {
                    ServiceInfo service = resolved.serviceInfo;
                    if (service == null || !YANDEX.equals(service.packageName)
                            || !service.exported || !service.enabled
                            || service.permission != null
                            || service.applicationInfo == null
                            || !service.applicationInfo.enabled
                            || service.applicationInfo.permission != null) continue;
                    possible.put(service.name,
                            new ComponentName(service.packageName, service.name));
                }
            }
            eligible = possible.size();
            if (eligible == 0) { complete("NO_PUBLIC_SERVICE"); return; }
            // Never pick an arbitrary service if the set is ambiguous.
            if (eligible != 1) { complete("AMBIGUOUS_SERVICE"); return; }
            serviceComponent = possible.values().iterator().next();
            SessionToken token;
            try {
                token = new SessionToken(this, serviceComponent);
                future = new MediaController.Builder(this, token).buildAsync();
            } catch (Throwable ignored) {
                tryPlatformBrowser();
                return;
            }
            future.addListener(() -> {
                if (finished.get()) return;
                try {
                    MediaController controller = future.get();
                    sessionConnected = controller.isConnected();
                    if (sessionConnected) {
                        // Boolean capability flags only. Never inspect track,
                        // title, queue, current URI, metadata, or source content.
                        changeItems = controller.isCommandAvailable(Player.COMMAND_CHANGE_MEDIA_ITEMS);
                        setItem = controller.isCommandAvailable(Player.COMMAND_SET_MEDIA_ITEM);
                        getItem = controller.isCommandAvailable(Player.COMMAND_GET_CURRENT_MEDIA_ITEM);
                        playPause = controller.isCommandAvailable(Player.COMMAND_PLAY_PAUSE);
                        seek = controller.isCommandAvailable(Player.COMMAND_SEEK_IN_CURRENT_MEDIA_ITEM);
                    }
                    if (sessionConnected) complete("CONNECTED_READONLY");
                    else tryPlatformBrowser();
                } catch (Throwable ignored) {
                    tryPlatformBrowser();
                }
            }, getMainExecutor());
            main.postDelayed(() -> complete("TIMEOUT"), 12000);
        } catch (PackageManager.NameNotFoundException ignored) {
            complete("PUBLISHER_PACKAGE_MISSING");
        } catch (Throwable ignored) {
            complete("PUBLIC_SESSION_PROBE_UNAVAILABLE");
        }
    }

    /** Public Android MediaBrowser fallback: no playback or queue mutation. */
    private void tryPlatformBrowser() {
        if (finished.get() || serviceComponent == null) return;
        try {
            browser = new MediaBrowser(this, serviceComponent,
                new MediaBrowser.ConnectionCallback() {
                    @Override public void onConnected() {
                        if (finished.get()) return;
                        browserConnected = true;
                        try {
                            android.media.session.MediaController platform =
                                new android.media.session.MediaController(
                                    ProbeActivity.this, browser.getSessionToken());
                            PlaybackState state = platform.getPlaybackState();
                            if (state != null) {
                                long actions = state.getActions();
                                platformPlayFromUri =
                                    (actions & PlaybackState.ACTION_PLAY_FROM_URI) != 0L;
                                platformPlayFromMediaId =
                                    (actions & PlaybackState.ACTION_PLAY_FROM_MEDIA_ID) != 0L;
                            }
                        } catch (Throwable ignored) {
                            // Connected binder is genuine; command flags unknown.
                        }
                        complete("PLATFORM_BROWSER_CONNECTED");
                    }
                    @Override public void onConnectionFailed() {
                        complete("PUBLIC_BIND_REJECTED");
                    }
                    @Override public void onConnectionSuspended() {
                        complete("PUBLIC_BIND_REJECTED");
                    }
                }, null);
            browser.connect();
        } catch (Throwable ignored) {
            complete("PUBLIC_BIND_UNAVAILABLE");
        }
    }

    private void complete(String state) {
        if (!finished.compareAndSet(false, true)) return;
        // The *only* log emitted by this app is a fixed-categorical result.
        Log.i(TAG, "PROBE_RESULT state=" + state + " eligible=" + eligible
                + " connected=" + sessionConnected
                + " change_items=" + changeItems
                + " set_item=" + setItem
                + " get_item=" + getItem
                + " play_pause=" + playPause
                + " seek=" + seek
                + " browser_connected=" + browserConnected
                + " platform_play_from_uri=" + platformPlayFromUri
                + " platform_play_from_media_id=" + platformPlayFromMediaId
                + " source_replace_proven=false"
                + " audio_tested=false");
        if (future != null) {
            try { MediaController.releaseFuture(future); }
            catch (Throwable ignored) { /* release is best effort */ }
        }
        if (browser != null) {
            try { browser.disconnect(); }
            catch (Throwable ignored) { /* never mutates publisher state */ }
        }
        finish();
    }
}
