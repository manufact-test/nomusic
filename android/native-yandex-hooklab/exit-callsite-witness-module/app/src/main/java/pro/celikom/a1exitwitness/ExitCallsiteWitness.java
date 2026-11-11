package pro.celikom.a1exitwitness;

import android.app.Application;
import android.content.Context;
import android.os.Looper;
import android.util.Log;
import io.github.libxposed.api.XposedInterface;
import io.github.libxposed.api.XposedModule;
import java.lang.reflect.Method;

/**
 * Laboratory-only early-exit observer. Exactly one independent, disposable
 * CELIKOM package. Never scoped to ru.yandex.music, system or any user app.
 * All hooks forward original args/results untouched: no signature, Passport,
 * media, protection, process lifecycle or exception behavior is overridden.
 * No exception messages, stack traces, account data, paths or URLs are logged.
 */
public final class ExitCallsiteWitness extends XposedModule {
    private static final String PACKAGE = "pro.celikom.yandex.nativeclonelab";
    private static final String TAG = "CELIKOM_A1_EXIT_WITNESS";
    private boolean armed;

    @Override public void onModuleLoaded(ModuleLoadedParam param) { }

    @Override public void onPackageLoaded(PackageLoadedParam param) {
        if (PACKAGE.equals(param.getPackageName())) arm();
    }

    @Override public void onPackageReady(PackageReadyParam param) {
        if (PACKAGE.equals(param.getPackageName())) arm();
    }

    private synchronized void arm() {
        if (armed || !PACKAGE.equals(Application.getProcessName())) return;
        armed = true;
        int count = 0;
        count += observe(Thread.class, "dispatchUncaughtException",
            new Class<?>[] {Throwable.class}, "UNCAUGHT") ? 1 : 0;
        count += observe(System.class, "exit",
            new Class<?>[] {int.class}, "SYSTEM_EXIT") ? 1 : 0;
        count += observe(Runtime.class, "exit",
            new Class<?>[] {int.class}, "RUNTIME_EXIT") ? 1 : 0;
        count += observe(android.os.Process.class, "killProcess",
            new Class<?>[] {int.class}, "PROCESS_KILL") ? 1 : 0;
        count += hookApplicationAttach() ? 1 : 0;
        // Arms only tell us that a hook was registered, not that it ran.
        emit("ARMED", count > 0 ? "REGISTERED" : "NO_HOOK", "NONE");
    }

    private boolean observe(Class<?> clazz, String name, Class<?>[] parameters,
                            String event) {
        try {
            Method method = clazz.getDeclaredMethod(name, parameters);
            method.setAccessible(true);
            hook(method).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                .intercept(chain -> {
                    try {
                        String category = "NONE";
                        if ("UNCAUGHT".equals(event)) {
                            Object value = chain.getArg(0);
                            if (value instanceof SecurityException) category = "SECURITY";
                            else if (value instanceof IllegalStateException) category = "ILLEGAL_STATE";
                            else if (value instanceof LinkageError) category = "LINK";
                            else if (value instanceof Throwable) category = "OTHER_THROWABLE";
                        }
                        emit(event, callerGroup(), category);
                    } catch (Throwable ignored) { }
                    // Unmodified original method, args and throw semantics.
                    return chain.proceed();
                });
            return true;
        } catch (Throwable ignored) {
            return false;
        }
    }


    private boolean prefixHookInstalled;

    private boolean hookApplicationAttach() {
        try {
            Method attach = Application.class.getDeclaredMethod("attach", Context.class);
            attach.setAccessible(true);
            hook(attach).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                .intercept(chain -> {
                    Object result = chain.proceed();
                    try {
                        if (PACKAGE.equals(Application.getProcessName())) {
                            Object context = chain.getArg(0);
                            if (context instanceof Context)
                                installExactPrefixWitness(((Context) context).getClassLoader());
                        }
                    } catch (Throwable ignored) { }
                    return result;
                });
            return true;
        } catch (Throwable ignored) {
            return false;
        }
    }

    private synchronized void installExactPrefixWitness(ClassLoader appLoader) {
        if (prefixHookInstalled || appLoader == null) return;
        try {
            // This exact method prototype was established in a signed
            // read-only DEX scan. No replacement, no arg changes.
            Class<?> kotlin = Class.forName("kotlin.text.c", false, appLoader);
            Method prefix = kotlin.getDeclaredMethod(
                "r", String.class, String.class, boolean.class);
            prefix.setAccessible(true);
            hook(prefix).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                .intercept(chain -> {
                    Object result = chain.proceed();
                    try {
                        if (callerIsExactExitOwner()) {
                            String category = argumentGroup(chain.getArg(0));
                            if ("UNCLASSIFIED".equals(category))
                                category = argumentGroup(chain.getArg(1));
                            emit("PREFIX_CHECK", category,
                                 Boolean.TRUE.equals(result) ? "MATCH_TRUE" : "MATCH_FALSE");
                        }
                    } catch (Throwable ignored) { }
                    return result;
                });
            prefixHookInstalled = true;
            emit("PREFIX_HOOK", "REGISTERED", "NONE");
        } catch (Throwable ignored) {
            emit("PREFIX_HOOK", "NO_HOOK", "NONE");
        }
    }

    private static boolean callerIsExactExitOwner() {
        try {
            for (StackTraceElement frame : Thread.currentThread().getStackTrace())
                if ("xx0".equals(frame.getClassName()) &&
                        "run".equals(frame.getMethodName()))
                    return true;
        } catch (Throwable ignored) { }
        return false;
    }

    private static String argumentGroup(Object arg) {
        if (!(arg instanceof String)) return "UNCLASSIFIED";
        String s = (String) arg;
        if (PACKAGE.equals(s)) return "OWN_MAIN";
        if (s.startsWith(PACKAGE + ":")) return "OWN_AUX";
        if ("ru.yandex.music".equals(s)) return "ORIGINAL_MAIN";
        if (s.startsWith("ru.yandex.music:")) return "ORIGINAL_AUX";
        return "UNCLASSIFIED";
    }

    private static String callerGroup() {
        try {
            boolean vendor = false, platform = false;
            for (StackTraceElement frame : Thread.currentThread().getStackTrace()) {
                String name = frame.getClassName();
                // Four actual direct-exit owners from a prior scan of signed
                // 2026 host DEX. Emit only fixed family labels: no raw stack.
                if ("ck7".equals(name) && "uncaughtException".equals(frame.getMethodName()))
                    return "STATIC_HANDLER";
                if ("mi7".equals(name) && "run".equals(frame.getMethodName()))
                    return "STATIC_RUN_A";
                if ("xx0".equals(name) && "run".equals(frame.getMethodName()))
                    return "STATIC_RUN_B";
                if ("tn".equals(name) && "invoke".equals(frame.getMethodName()))
                    return "STATIC_INVOKER";
                if (name.startsWith("ru.yandex.") || name.startsWith("com.yandex."))
                    vendor = true;
                else if (name.startsWith("android.") || name.startsWith("java."))
                    platform = true;
            }
            return vendor ? "VENDOR" : platform ? "PLATFORM" : "UNKNOWN";
        } catch (Throwable ignored) {
            return "UNKNOWN";
        }
    }

    private static void emit(String event, String origin, String error) {
        if (!PACKAGE.equals(Application.getProcessName())) return;
        String thread = "OTHER";
        try {
            if (Looper.getMainLooper() != null &&
                    Thread.currentThread() == Looper.getMainLooper().getThread())
                thread = "MAIN";
        } catch (Throwable ignored) { }
        // Entire message is finite enums; never stringifies a Throwable.
        Log.i(TAG, "event=" + event + ";origin=" + origin +
                ";error=" + error + ";thread=" + thread);
    }
}
