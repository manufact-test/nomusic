package pro.celikom.armv7witnessmodule;

import android.app.Application;
import android.content.Context;
import android.os.Bundle;
import java.lang.reflect.Method;
import io.github.libxposed.api.XposedInterface;
import io.github.libxposed.api.XposedModule;

/**
 * Own-source safe witness; STRICTLY ONLY pro.celikom.armv7loaderhost.witness.
 * Any third-party package and all audio/media APIs are outside scope.
 */
public final class HookWitnessEntry extends XposedModule {
    private static final String TARGET = "pro.celikom.armv7loaderhost.witness";
    private static final String AUDIO = "pro.celikom.armv7loaderhost.audio";
    private static final String ACTIVITY = "pro.celikom.armv7loaderhost.MainActivity";
    private static final String STATE = "pro.celikom.armv7loaderhost.HookWitnessState";
    private boolean attachHooked;
    private boolean activityHooked;

    @Override public void onModuleLoaded(ModuleLoadedParam param) { }

    @Override public void onPackageLoaded(PackageLoadedParam param) {
        if (TARGET.equals(param.getPackageName()) || AUDIO.equals(param.getPackageName())) installAttach();
    }
    @Override public void onPackageReady(PackageReadyParam param) {
        if (TARGET.equals(param.getPackageName())) installAttach();
    }

    private synchronized void installAttach() {
        if (attachHooked) return;
        try {
            Method attach = Application.class.getDeclaredMethod("attach", Context.class);
            attach.setAccessible(true);
            hook(attach).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                .intercept(chain -> {
                    Object originalResult = chain.proceed();
                    try {
                        Context app = (Context) chain.getThisObject();
                        if (app != null && TARGET.equals(app.getPackageName())) {
                            installActivity(app.getClassLoader());
                        } else if (app != null && AUDIO.equals(app.getPackageName())) {
                            installAudioSource(app.getClassLoader());
                        }
                    } catch (Throwable ignored) {
                        // Never affect the original application lifecycle.
                    }
                    return originalResult;
                });
            attachHooked = true;
        } catch (Throwable ignored) {
            // No hooks armed; host UI must report NOT OBSERVED, never PASS.
        }
    }

    private synchronized void installActivity(ClassLoader appLoader) {
        if (activityHooked) return;
        try {
            Class<?> host = Class.forName(ACTIVITY, false, appLoader);
            Class<?> witness = Class.forName(STATE, false, appLoader);
            Method markArmed = witness.getMethod("markArmed");
            Method markIntercepted = witness.getMethod("markIntercepted");
            Method onCreate = host.getDeclaredMethod("onCreate", Bundle.class);
            onCreate.setAccessible(true);
            hook(onCreate).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                .intercept(chain -> {
                    try {
                        markIntercepted.invoke(null);
                    } catch (Throwable ignored) { }
                    return chain.proceed();
                });
            activityHooked = true;
            markArmed.invoke(null);
        } catch (Throwable ignored) {
            // Module and host versions must match; fail without side effects.
        }
    }
    private boolean audioArmed;
    private synchronized void installAudioSource(ClassLoader appLoader) {
        if (audioArmed) return;
        try {
            Class<?> selector = Class.forName("pro.celikom.armv7loaderhost.AudioSmokeSource", false, appLoader);
            Class<?> witness = Class.forName("pro.celikom.armv7loaderhost.AudioSmokeState", false, appLoader);
            Method armed = witness.getMethod("arm");
            Method swap = witness.getMethod("swap");
            Method chooseA = selector.getDeclaredMethod("chooseA");
            hook(chooseA).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                .intercept(chain -> {
                    Object original = chain.proceed();
                    if (original instanceof Integer && ((Integer) original) == 0) {
                        try { swap.invoke(null); } catch (Throwable ignored) {}
                        // This ONLY changes our synthetic lab tone ID before
                        // prepare. Never accesses or hooks Yandex/other apps.
                        return Integer.valueOf(1);
                    }
                    return original;
                });
            audioArmed = true;
            armed.invoke(null);
        } catch (Throwable ignored) {
            // Fail closed, original tone remains selected.
        }
    }

}
