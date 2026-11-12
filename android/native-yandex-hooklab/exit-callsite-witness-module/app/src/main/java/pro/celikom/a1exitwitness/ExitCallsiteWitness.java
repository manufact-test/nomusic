package pro.celikom.a1exitwitness;

import android.app.Application;
import android.content.Context;
import android.os.Looper;
import android.util.Log;
import io.github.libxposed.api.XposedInterface;
import io.github.libxposed.api.XposedModule;
import java.lang.reflect.Method;
import java.lang.reflect.Constructor;
import java.util.Collections;
import java.util.Map;
import java.util.WeakHashMap;

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
    private boolean exitCtorHooked;
    private boolean exitRunHooked;
    private final Map<Object, Integer> constructorModes =
        Collections.synchronizedMap(new WeakHashMap<>());
    // Identity-only linkage. No message, raw exception, stack, class name,
    // PID, thread ID or token ever leaves the process or the map.
    private final Map<Throwable, Boolean> metricaConstructed =
        Collections.synchronizedMap(new WeakHashMap<>());

    @Override public void onModuleLoaded(ModuleLoadedParam param) { }

    @Override public void onPackageLoaded(PackageLoadedParam param) {
        if (PACKAGE.equals(param.getPackageName())) {
            arm();
            try { installExactRunModeWitness(param.getDefaultClassLoader()); }
            catch (Throwable ignored) { }
        }
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
        count += observeHi2IllegalStateConstructor() ? 1 : 0;
        count += observeFatalDispatches();
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
                        } else if ("PROCESS_KILL".equals(event)) {
                            Object value = chain.getArg(0);
                            if (value instanceof Integer) {
                                category = ((Integer) value).intValue()
                                        == android.os.Process.myPid()
                                        ? "KILL_TARGET_SELF" : "KILL_TARGET_OTHER";
                            } else {
                                category = "KILL_TARGET_UNKNOWN";
                            }
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



    /**
     * Observe the message CLASSIFICATION of a normal IllegalStateException
     * constructed inside the exact signed hi2.j coroutine. The constructor,
     * its arguments and exception behavior are not modified. Raw message
     * text (which might include secrets) is NEVER logged or stored.
     */
    private boolean observeHi2IllegalStateConstructor() {
        try {
            Constructor<IllegalStateException> ctor =
                IllegalStateException.class.getDeclaredConstructor(String.class);
            ctor.setAccessible(true);
            hook(ctor).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                .intercept(chain -> {
                    try {
                        Object value = chain.getArg(0);
                        if (callerIsExactHi2Coroutine()) {
                            emit("HI2_EXCEPTION", "STATIC_COROUTINE",
                                 redactedErrorCategory(value));
                        }
                        String metrica = callerMetricaFrameGroup();
                        if (!"NO_METRICA_FRAME".equals(metrica)) {
                            // Mark THIS precise Throwable object, not merely
                            // a timestamp or exception class. A caught SDK
                            // exception must never be called a fatal cause.
                            Object result = chain.proceed();
                            Object constructed = chain.getThisObject();
                            if (constructed instanceof Throwable)
                                metricaConstructed.put((Throwable) constructed, Boolean.TRUE);
                            emit("METRICA_EXCEPTION", metrica,
                                 redactedErrorCategory(value));
                            return result;
                        }
                    } catch (Throwable ignored) { }
                    return chain.proceed();
                });
            return true;
        } catch (Throwable ignored) {
            return false;
        }
    }

    /**
     * Native Android 13 has multiple uncaught-exception dispatch paths.
     * These hooks are independent, read-only witnesses. They never handle,
     * replace, suppress or change exceptions, system kills or user data.
     * Hook registration is an observation, not evidence of a callback.
     */
    private int observeFatalDispatches() {
        int count = 0;
        if (observeFatalMethod(Thread.class, "dispatchUncaughtException",
                new Class<?>[]{Throwable.class}, 0, "THREAD_DISPATCH"))
            count++;
        if (observeFatalMethod(ThreadGroup.class, "uncaughtException",
                new Class<?>[]{Thread.class, Throwable.class}, 1, "THREAD_GROUP"))
            count++;
        for (String handler : new String[]{
                "com.android.internal.os.RuntimeInit$KillApplicationHandler",
                "com.android.internal.os.RuntimeInit$LoggingHandler"}) {
            try {
                Class<?> cls = Class.forName(handler);
                String origin = handler.endsWith("KillApplicationHandler")
                    ? "RUNTIME_KILL_HANDLER" : "RUNTIME_LOG_HANDLER";
                if (observeFatalMethod(cls, "uncaughtException",
                        new Class<?>[]{Thread.class, Throwable.class}, 1, origin))
                    count++;
            } catch (Throwable ignored) {
                emit("FATAL_HOOK", "RUNTIME_LOOKUP", "NO_HOOK");
            }
        }
        return count;
    }

    private boolean observeFatalMethod(Class<?> cls, String methodName,
            Class<?>[] args, int throwableIndex, String origin) {
        try {
            Method m = cls.getDeclaredMethod(methodName, args);
            m.setAccessible(true);
            hook(m).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                .intercept(chain -> {
                    try {
                        Object arg = chain.getArg(throwableIndex);
                        if (arg instanceof Throwable)
                            emit("FATAL_DISPATCH", origin,
                                    throwableIdentityCategory((Throwable) arg));
                        else emit("FATAL_DISPATCH", origin, "NON_THROWABLE");
                    } catch (Throwable ignored) { }
                    return chain.proceed();
                });
            emit("FATAL_HOOK", origin, "REGISTERED");
            return true;
        } catch (Throwable ignored) {
            emit("FATAL_HOOK", origin, "NO_HOOK");
            return false;
        }
    }

    private String throwableIdentityCategory(Throwable failure) {
        try {
            if (metricaConstructed.containsKey(failure))
                return "DIRECT_METRICA";
            Throwable step = failure.getCause();
            for (int i = 0; step != null && i < 8; i++) {
                if (metricaConstructed.containsKey(step))
                    return "CAUSE_METRICA";
                if (step == step.getCause())
                    break;
                step = step.getCause();
            }
        } catch (Throwable ignored) { }
        return "NOT_METRICA";
    }

    /** Only fixed framework labels, no vendor class, method, thread or text. */
    private static String callerMetricaFrameGroup() {
        try {
            boolean sdk = false;
            boolean app = false;
            for (StackTraceElement frame : Thread.currentThread().getStackTrace()) {
                String name = frame.getClassName();
                if (name.startsWith("com.yandex.metrica.")
                        || name.startsWith("io.appmetrica.analytics."))
                    sdk = true;
                if (name.startsWith("ru.yandex.music."))
                    app = true;
            }
            return sdk ? "METRICA_SDK" : app ? "MUSIC_APP" : "NO_METRICA_FRAME";
        } catch (Throwable ignored) {
            return "NO_METRICA_FRAME";
        }
    }

    private static boolean callerIsExactHi2Coroutine() {
        try {
            for (StackTraceElement frame : Thread.currentThread().getStackTrace()) {
                if ("hi2".equals(frame.getClassName())
                        && "j".equals(frame.getMethodName()))
                    return true;
            }
        } catch (Throwable ignored) { }
        return false;
    }

    private static String packageIdentityCategory(String value) {
        if (PACKAGE.equals(value)) return "CLONE";
        if ("ru.yandex.music".equals(value)) return "ORIGINAL";
        if (value == null || value.isEmpty()) return "MISSING";
        return "OTHER";
    }

    private static String redactedErrorCategory(Object value) {
        if (!(value instanceof String)) return "EXC_UNKNOWN";
        String s = ((String) value).toLowerCase(java.util.Locale.ROOT);
        // Fixed small lexical enum, not a transcript or hash of secrets.
        boolean signing = s.contains("signature") || s.contains("certificate")
            || s.contains("signing") || s.contains("sha256");
        boolean identity = s.contains("passport") || s.contains("auth")
            || s.contains("account") || s.contains("credential")
            || s.contains("login") || s.contains("token");
        if (signing && identity) return "EXC_SIGN_AND_AUTH";
        if (signing) return "EXC_SIGNATURE";
        if (identity) return "EXC_AUTH";
        if (s.contains("permission") || s.contains("denied") || s.contains("grant"))
            return "EXC_PERMISSION";
        if (s.contains("locale") || s.contains("language"))
            return "EXC_LOCALE";
        if (s.contains("process") || s.contains("package")
                || s.contains("component") || s.contains("restart"))
            return "EXC_LIFECYCLE";
        if (s.contains("appmetrica") || s.contains("metrica")
                || s.contains("sdk") || s.contains("activate"))
            return "EXC_SDK_INIT";
        if (s.contains("invalid") || s.contains("unsupported")
                || s.contains("configuration") || s.contains("api key"))
            return "EXC_CONFIG";
        if (s.contains("coroutine") || s.contains("dispatcher")
                || s.contains("concurrent"))
            return "EXC_ASYNC";
        return "EXC_OTHER";
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
                            if (context instanceof Context) {
                                Context caller = (Context) context;
                                String rawInfo = caller.getApplicationInfo() == null
                                    ? null : caller.getApplicationInfo().packageName;
                                emit("APP_CONTEXT",
                                     packageIdentityCategory(caller.getPackageName()),
                                     "APPINFO_" + packageIdentityCategory(rawInfo));
                                ClassLoader loader = caller.getClassLoader();
                                installExactPrefixWitness(loader);
                                installExactRunModeWitness(loader);
                            }
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


    /**
     * A1 isolated read-only clone: constructor mode and Runnable enter marker.
     * Both original constructor and run always execute without alterations.
     */
    private synchronized void installExactRunModeWitness(ClassLoader appLoader) {
        if (appLoader == null || (exitCtorHooked && exitRunHooked)) return;
        try {
            Class<?> target = Class.forName("xx0", false, appLoader);
            if (!exitCtorHooked) {
                Constructor<?> constructor = target.getDeclaredConstructor(Context.class, int.class);
                constructor.setAccessible(true);
                hook(constructor).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                    .intercept(chain -> {
                        Object result = chain.proceed();
                        try {
                            Object owner = chain.getThisObject();
                            Object value = chain.getArg(1);
                            if (owner != null && value instanceof Integer) {
                                Integer mode = (Integer) value;
                                constructorModes.put(owner, mode);
                                emit("RUN_CTOR", "STATIC_RUN_B", modeCategory(mode));
                            }
                        } catch (Throwable ignored) { }
                        return result;
                    });
                exitCtorHooked = true;
            }
            if (!exitRunHooked) {
                Method run = target.getDeclaredMethod("run");
                run.setAccessible(true);
                hook(run).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                    .intercept(chain -> {
                        try {
                            Integer mode = constructorModes.get(chain.getThisObject());
                            emit("RUN_ENTER", "STATIC_RUN_B", modeCategory(mode));
                        } catch (Throwable ignored) { }
                        return chain.proceed();
                    });
                exitRunHooked = true;
            }
            emit("RUN_HOOK", "REGISTERED", "NONE");
        } catch (Throwable ignored) {
            emit("RUN_HOOK", "NO_HOOK", "NONE");
        }
    }

    private static String modeCategory(Integer mode) {
        if (mode == null) return "CASE_UNKNOWN";
        switch (mode.intValue()) {
            case 0: return "CASE_0";
            case 1: return "CASE_1";
            case 2: return "CASE_2";
            case 3: return "CASE_3";
            case 4: return "CASE_4";
            case 5: return "CASE_5";
            case 6: return "CASE_6";
            case 7: return "CASE_7";
            default: return "CASE_OTHER";
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
