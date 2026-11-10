package pro.celikom.yandex.nativehooklab;

import android.app.Application;
import android.content.Context;
import android.content.pm.PackageInfo;
import android.media.MediaMetadata;
import android.media.session.MediaSession;
import android.media.session.PlaybackState;
import android.os.SystemClock;
import android.util.Log;

import java.lang.reflect.Method;
import java.util.concurrent.atomic.AtomicInteger;

import io.github.libxposed.api.XposedInterface;
import io.github.libxposed.api.XposedModule;

/**
 * NON-MUTATING in-process witness for a disposable Yandex host.
 *
 * Validated native code discovery (2026.10.3 #170gpr):
 *  FileInfoDto -> sw7.y0(dto,boolean) -> eed
 *  OldGetFileInfoDto -> sw7.z0(dto,boolean) -> eed
 *
 * Never records IDs, accounts, URLs, keys, track files, app data, API tokens
 * or remote requests; doesn't change any argument, result or playback clock.
 * Rootless LSPatch loader supplies libxposed; this APK alone CANNOT modify
 * an unpatched official Yandex application.
 */
public final class NativeHookEntry extends XposedModule {
    private static final String TAG = "CELIKOM-NativeLab";
    private final AtomicInteger newConversions = new AtomicInteger();
    private final AtomicInteger oldConversions = new AtomicInteger();
    private final AtomicInteger modelAccessorCalls = new AtomicInteger();
    // Privacy-safe lifecycle signal: count framework metadata updates without
    // accessing the MediaMetadata fields or MediaSession queue contents.
    private final AtomicInteger metadataUpdates = new AtomicInteger();
    // Diagnostic-only sequence categories; NEVER an audio-source identity gate.
    private final NativeEventOrderProbe eventOrder = new NativeEventOrderProbe(12000);
    // Counts published states only, never actual decoder success or current track.
    private final NativePlaybackStateProbe publishedState = new NativePlaybackStateProbe();
    private final AtomicInteger publishedStateUpdates = new AtomicInteger();
    private String processName;
    private boolean attachHooked;
    private boolean targetHooked;
    // Real host classloader may become available after Application.attach.
    // Store only a verified, exact-version Context; never bind another package.
    private Context verifiedHostContext;
    private ClassLoader readyClassLoader;
    private boolean modernHooked;
    private boolean legacyHooked;
    private boolean accessorHooked;
    private boolean metadataHooked;
    private boolean playbackStateHooked;

    @Override
    public void onModuleLoaded(ModuleLoadedParam param) {
        processName = param.getProcessName();
        if (HookSpec.TARGET_PACKAGE.equals(processName)
                || (processName != null
                    && processName.startsWith(HookSpec.TARGET_PACKAGE + ":"))) {
            Log.i(TAG, "observer: module loaded");
        }
    }

    @Override
    public void onPackageLoaded(PackageLoadedParam param) {
        if (HookSpec.TARGET_PACKAGE.equals(param.getPackageName())) {
            Log.i(TAG, "observer: package loaded");
        }
        maybeInstallAttachHook(param.getPackageName());
    }

    @Override
    public void onPackageReady(PackageReadyParam param) {
        if (HookSpec.TARGET_PACKAGE.equals(param.getPackageName())) {
            Log.i(TAG, "observer: package ready");
        }
        if (HookSpec.TARGET_PACKAGE.equals(param.getPackageName())) {
            synchronized (this) {
                readyClassLoader = param.getClassLoader();
                // Attach can run before all split / secondary classes resolve.
                // Retry only for a version-verified context; no eager unsafe hook.
                if (verifiedHostContext != null
                        && (!targetHooked || !metadataHooked || !playbackStateHooked)) {
                    onAttached(verifiedHostContext);
                }
            }
        }
        maybeInstallAttachHook(param.getPackageName());
    }

    private synchronized void maybeInstallAttachHook(String packageName) {
        if (attachHooked || !HookSpec.TARGET_PACKAGE.equals(packageName)) return;
        if (processName == null || !(processName.equals(HookSpec.TARGET_PACKAGE)
                || processName.startsWith(HookSpec.TARGET_PACKAGE + ":"))) return;
        try {
            Method attach = Application.class.getDeclaredMethod("attach", Context.class);
            attach.setAccessible(true);
            hook(attach)
                    .setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                    .intercept(chain -> {
                        Object result = chain.proceed();
                        // ALWAYS let real Yandex attach complete, even if the observer throws.
                        try {
                            Context ctx = (Context) chain.getThisObject();
                            if (ctx != null) onAttached(ctx);
                        } catch (Throwable ignored) {
                            log(Log.WARN, TAG, "observer: context unavailable; original unaffected");
                        }
                        return result;
                    });
            attachHooked = true;
        } catch (Throwable ignored) {
            log(Log.WARN, TAG, "observer: cannot attach; original unaffected");
        }
    }

    @SuppressWarnings("deprecation")
    private synchronized void onAttached(Context context) {
        if (!HookSpec.TARGET_PACKAGE.equals(context.getPackageName())) return;
        try {
            PackageInfo p = context.getPackageManager().getPackageInfo(
                    HookSpec.TARGET_PACKAGE, 0);
            if (!HookSpec.isApprovedHost(p.packageName, p.versionName, p.getLongVersionCode())) {
                log(Log.WARN, TAG, "observer: unsupported host version; no hooks");
                return;
            }
            verifiedHostContext = context;
            armPlatformMetadataWitness();
            armPublishedPlaybackStateWitness();
            if (targetHooked) return;
            // Only an exact pair from a SINGLE verified loader may be used.
            HookSpec.ResolvedPair pair = HookSpec.findConversionPair(
                    readyClassLoader, context.getClassLoader());
            ClassLoader appLoader = pair.loader;
            Method modern = pair.modern;
            Method old = pair.legacy;

            // onAttached and onPackageReady may race. Idempotent flags make
            // a partial registration safe to retry after runtime class loading.
            if (!modernHooked) {
                hook(modern)
                        .setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                        .intercept(chain -> {
                            Object result = chain.proceed();
                            if (result != null) {
                                eventOrder.onFileInfo(SystemClock.elapsedRealtime());
                                safeCount("modern", newConversions);
                            }
                            return result;
                        });
                modernHooked = true;
            }
            if (!legacyHooked) {
                hook(old)
                        .setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                        .intercept(chain -> {
                            Object result = chain.proceed();
                            if (result != null) {
                                eventOrder.onFileInfo(SystemClock.elapsedRealtime());
                                safeCount("legacy", oldConversions);
                            }
                            return result;
                        });
                legacyHooked = true;
            }
            targetHooked = modernHooked && legacyHooked;
            // Optional secondary boundary. Exact DEX signature was confirmed
            // on the publisher-signed host; it may be a getter not a decoder.
            // Count invocations only, never inspect the returned String.
            if (!accessorHooked) {
                try {
                    Method downstream = HookSpec.findModelStringAccessor(appLoader);
                    hook(downstream)
                        .setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                        .intercept(chain -> {
                            Object result = chain.proceed();
                            if (result != null) safeCount("model-accessor",
                                    modelAccessorCalls);
                            return result;
                        });
                    accessorHooked = true;
                    Log.i(TAG, "observer: downstream model accessor armed (counts only)");
                } catch (Throwable ignored) {
                    log(Log.WARN, TAG, "observer: downstream accessor unavailable; converters unaffected");
                }
            }
            log(Log.INFO, TAG, "observer: native file-info converter hooks armed; read-only");
            Log.i(TAG, "observer: native file-info converter hooks armed; read-only");
        } catch (Throwable ignored) {
            log(Log.WARN, TAG, "observer: no exact converter pair; original unaffected");
        }
    }

    /**
     * Platform-only read-only witness inspired by the open-source YaMusicLsposed
     * MediaSession.setMetadata hook (Windyx0, MIT-licensed), implemented anew.
     * Scope is enforced by the exact Yandex app version gate in onAttached.
     *
     * No titles, artists, IDs, URLs, durations, MediaMetadata fields, album art,
     * queues, or user data are read. No second player and no source mutation.
     * This ONLY proves that the host process publishes platform metadata,
     * NOT that any particular FileInfo request is the audible track.
     */
    private synchronized void armPlatformMetadataWitness() {
        if (metadataHooked) return;
        try {
            Method method = MediaSession.class.getDeclaredMethod(
                    "setMetadata", MediaMetadata.class);
            hook(method)
                    .setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                    .intercept(chain -> {
                        Object result = chain.proceed();
                        NativeEventOrderProbe.Verdict temporalOrder =
                                eventOrder.onMetadata(SystemClock.elapsedRealtime());
                        safeCount("platform-media-metadata-update", metadataUpdates);
                        int count = metadataUpdates.get();
                        if (count == 1 || count % 20 == 0) {
                            // Only broad sequence category and aggregate count.
                            NativeEventOrderProbe.Snapshot totals = eventOrder.snapshot();
                            Log.i(TAG, "observer: temporal-only aggregate single="
                                    + totals.oneSourceWindows + " ambiguous="
                                    + totals.ambiguousWindows + " no-source="
                                    + totals.noSourceWindows + " clock-reset="
                                    + totals.clockDiscontinuities + " metadata-updates="
                                    + totals.metadataCallbacks + " last-category="
                                    + temporalOrder.name());
                        }
                        return result;
                    });
            metadataHooked = true;
            log(Log.INFO, TAG, "observer: platform metadata witness armed; counts only");
        } catch (Throwable ignored) {
            // A missing platform hook must not prevent native FileInfo observation.
            log(Log.WARN, TAG, "observer: platform metadata witness unavailable");
        }
    }

    /**
     * Exact-host read-only playback-state observation. Only the public Android
     * integer enum is read; no metadata, song ID, position, URL, audio or queue.
     * Multiple MediaSessions/user pause may cause misleading aggregate events.
     */
    private synchronized void armPublishedPlaybackStateWitness() {
        if (playbackStateHooked) return;
        try {
            Method method = MediaSession.class.getDeclaredMethod(
                    "setPlaybackState", PlaybackState.class);
            hook(method)
                    .setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                    .intercept(chain -> {
                        Object result = chain.proceed();
                        try {
                            Object[] args = chain.getArgs();
                            if (args != null && args.length == 1
                                    && args[0] instanceof PlaybackState) {
                                int publishedEnum = ((PlaybackState) args[0]).getState();
                                NativePlaybackStateProbe.Snapshot totals =
                                        publishedState.onPublishedState(
                                                publishedEnum, SystemClock.elapsedRealtime());
                                int n = publishedStateUpdates.incrementAndGet();
                                if (n == 1 || n % 20 == 0) {
                                    Log.i(TAG, "observer: published-playback aggregate reports="
                                            + totals.reports + " transitions=" + totals.transitions
                                            + " rapid-play-pause=" + totals.pausesSoonAfterPlay
                                            + " rapid-pause-play=" + totals.playsSoonAfterPause
                                            + " buffer-pause=" + totals.buffersThenPauses
                                            + " buffering=" + totals.reportedBufferings
                                            + " errors=" + totals.reportedErrors
                                            + " clock-reset=" + totals.timeResets);
                                }
                            }
                        } catch (Throwable ignored) {
                            // An observer cannot break the original state setter.
                        }
                        return result;
                    });
            playbackStateHooked = true;
            log(Log.INFO, TAG, "observer: published playback-state witness armed; counts only");
        } catch (Throwable ignored) {
            log(Log.WARN, TAG, "observer: published playback-state witness unavailable");
        }
    }

    private void safeCount(String kind, AtomicInteger counter) {
        try {
            int n = counter.incrementAndGet();
            // Count only, throttled. No account, source URL, trackId, key, or timestamp.
            if (n == 1 || n % 20 == 0) {
                String category = "platform-media-metadata-update".equals(kind)
                        ? " metadata update count=" : " file-info conversion count=";
                log(Log.INFO, TAG, "observer: " + kind + category + n);
                Log.i(TAG, "observer: " + kind + category + n);
            }
        } catch (Throwable ignored) {
            // Logging/observer failures can never interfere with Yandex.
        }
    }
}
