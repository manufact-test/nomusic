package pro.celikom.yandex.nativehooklab;

import android.app.Application;
import android.content.Context;
import android.content.pm.PackageInfo;
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
    private String processName;
    private boolean attachHooked;
    private boolean targetHooked;

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
        if (targetHooked || !HookSpec.TARGET_PACKAGE.equals(context.getPackageName())) return;
        try {
            PackageInfo p = context.getPackageManager().getPackageInfo(
                    HookSpec.TARGET_PACKAGE, 0);
            if (!HookSpec.isApprovedHost(p.packageName, p.versionName, p.getLongVersionCode())) {
                log(Log.WARN, TAG, "observer: unsupported host version; no hooks");
                return;
            }
            ClassLoader appLoader = context.getClassLoader();
            Method modern = HookSpec.findConversion(
                    appLoader, "y0", HookSpec.FILE_DTO);
            Method old = HookSpec.findConversion(
                    appLoader, "z0", HookSpec.OLD_FILE_DTO);

            hook(modern)
                    .setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                    .intercept(chain -> {
                        Object result = chain.proceed();
                        if (result != null) safeCount("modern", newConversions);
                        return result;
                    });
            hook(old)
                    .setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                    .intercept(chain -> {
                        Object result = chain.proceed();
                        if (result != null) safeCount("legacy", oldConversions);
                        return result;
                    });
            targetHooked = true;
            log(Log.INFO, TAG, "observer: native file-info converter hooks armed; read-only");
            Log.i(TAG, "observer: native file-info converter hooks armed; read-only");
        } catch (Throwable ignored) {
            log(Log.WARN, TAG, "observer: no exact converter pair; original unaffected");
        }
    }

    private void safeCount(String kind, AtomicInteger counter) {
        try {
            int n = counter.incrementAndGet();
            // Count only, throttled. No account, source URL, trackId, key, or timestamp.
            if (n == 1 || n % 20 == 0) {
                log(Log.INFO, TAG, "observer: " + kind + " file-info conversion count=" + n);
                Log.i(TAG, "observer: " + kind + " file-info conversion count=" + n);
            }
        } catch (Throwable ignored) {
            // Logging/observer failures can never interfere with Yandex.
        }
    }
}
