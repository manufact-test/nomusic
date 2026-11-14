package pro.celikom.a1exitwitness;

import android.app.Activity;
import android.app.ActivityManager;
import android.app.Application;
import android.accounts.Account;
import android.accounts.AccountManager;
import android.app.ApplicationExitInfo;
import android.content.Context;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Intent;
import android.content.ComponentName;
import android.content.pm.ProviderInfo;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Looper;
import android.provider.MediaStore;
import android.util.Log;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.TextView;
import android.widget.Toast;
import io.github.libxposed.api.XposedInterface;
import io.github.libxposed.api.XposedModule;
import java.lang.reflect.Method;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.WeakHashMap;

/**
 * Laboratory-only early-exit observer. Exactly one independent, disposable
 * CELIKOM package. Never scoped to ru.yandex.music, system or any user app.
 * Read-only diagnostics plus a deliberately isolated clone-owned AccountManager
 * type-namespace compatibility trial. Exactly the original Yandex account type
 * is rewritten to the independently owned CELIKOM type at the Android API
 * boundary; no result is forged, exception suppressed or publisher account read.
 * All unrelated media, protection, process and crash hooks remain read-only.
 * No exception messages, stack traces, account data, paths or URLs are logged.
 */
public final class ExitCallsiteWitness extends XposedModule {
    private static final String PACKAGE = "pro.celikom.yandex.nativeclonelab";
    private static final String TAG = "CELIKOM_A1_EXIT_WITNESS";
    // Manifest source is rewritten only on the disposable own clone, never stock.
    private static final String STOCK_AUTHORITY =
        "com.yandex.preinstallsatellite.appmetrica.provider";
    private static final String CLONE_AUTHORITY =
        PACKAGE + ".provider.7e1ef82da0d52923";
    private static final String DIAGNOSTIC_FILE = "celikom-a1-diagnostics.txt";
    private static final String PASSPORT_DIAGNOSTIC_FILE = "celikom-a1-passport-diagnostics.txt";
    private static final String PASSPORT_PROCESS = PACKAGE + ":passport";
    // The matching resource in authenticator.xml and sync-adapter XML is
    // exclusively rewritten on the own clone; never claim stock's account type.
    private static final String STOCK_ACCOUNT_TYPE = "com.yandex.passport";
    // Own distinct type must follow the verified 2025 Passport SDK's
    // startsWith("com.yandex.passport") accountType validator contract.
    // Never equal the publisher's authenticator type itself.
    private static final String OWN_ACCOUNT_TYPE =
        STOCK_ACCOUNT_TYPE + "." + PACKAGE;
    private static final String DIAGNOSTIC_BUTTON_TAG = "celikom_a1_ondevice_diagnostic_export";
    private static final String DIAGNOSTIC_BUILD = "NAV_V12_ONBOARDING_WRITER_WITNESS";
    private static final Object DIAGNOSTIC_FILE_LOCK = new Object();
    private static final long MAX_DIAGNOSTIC_FILE_BYTES = 64L * 1024L;
    private static volatile Context diagnosticContext;
    private boolean diagnosticUiReady;
    private final java.util.concurrent.atomic.AtomicInteger activityPhasesLogged =
        new java.util.concurrent.atomic.AtomicInteger();
    private final java.util.concurrent.atomic.AtomicInteger onboardingReads =
        new java.util.concurrent.atomic.AtomicInteger();
    private boolean onboardingWriterHooked;
    private final java.util.concurrent.atomic.AtomicInteger onboardingWriterEvents =
        new java.util.concurrent.atomic.AtomicInteger();
    private final Map<Object, Boolean> onboardingPreferenceStores =
        Collections.synchronizedMap(new WeakHashMap<>());
    private final Map<Object, Boolean> yandexMusicPreferenceEditors =
        Collections.synchronizedMap(new WeakHashMap<>());
    private final Map<Object, Boolean> onboardingPreferenceEditors =
        Collections.synchronizedMap(new WeakHashMap<>());
    private final java.util.concurrent.atomic.AtomicInteger newIntentObserved =
        new java.util.concurrent.atomic.AtomicInteger();
    private boolean newIntentObserverArmed;
    private final java.util.concurrent.atomic.AtomicInteger activityFinishesLogged =
        new java.util.concurrent.atomic.AtomicInteger();
    private final java.util.concurrent.atomic.AtomicInteger activityStartsLogged =
        new java.util.concurrent.atomic.AtomicInteger();
    private boolean armed;
    private boolean passportArmed;
    private boolean accountCtorHooked;
    private boolean accountQueryHooked;
    private boolean accountAddHooked;
    private boolean authenticatorTypesHooked;
    private boolean activityResultHooked;
    private boolean activityResultDeliveryHooked;
    private final java.util.concurrent.atomic.AtomicInteger activityResultProducerObservations =
        new java.util.concurrent.atomic.AtomicInteger();
    private final java.util.concurrent.atomic.AtomicInteger activityResultDeliveryObservations =
        new java.util.concurrent.atomic.AtomicInteger();
    private final java.util.concurrent.atomic.AtomicInteger accountSnapshots =
        new java.util.concurrent.atomic.AtomicInteger();
    // Independent event quotas: a long login cannot exhaust the budget
    // before the decisive account-add result.
    private final java.util.concurrent.atomic.AtomicInteger accountCtorObservations =
        new java.util.concurrent.atomic.AtomicInteger();
    private final java.util.concurrent.atomic.AtomicInteger accountQueryObservations =
        new java.util.concurrent.atomic.AtomicInteger();
    private final java.util.concurrent.atomic.AtomicInteger accountAddObservations =
        new java.util.concurrent.atomic.AtomicInteger();
    private final java.util.concurrent.atomic.AtomicInteger accountRegistryObservations =
        new java.util.concurrent.atomic.AtomicInteger();
    private final java.util.concurrent.atomic.AtomicInteger ownAccountCtorRemaps =
        new java.util.concurrent.atomic.AtomicInteger();
    private final java.util.concurrent.atomic.AtomicInteger ownAccountQueryRemaps =
        new java.util.concurrent.atomic.AtomicInteger();
    // Real AccountManager result categories only. Never retain, print or
    // transmit master-token contents, password, names, uid or extras.
    private boolean ownedPasswordReturnHooked;
    private final java.util.concurrent.atomic.AtomicInteger ownedPasswordReturnEvents =
        new java.util.concurrent.atomic.AtomicInteger();
    // The real vendor decryptor returns a result object with an exception field.
    // Only that exception's presence is observed. No encrypted or decrypted
    // master-token value, length, account or error message is inspected.
    // Original vendor key-generation is only brought forward before the first
    // Passport subprocess. No existing account, key or token is overwritten.
    // No vendor cryptography implementation or signature checks are replaced.
    private boolean masterKeyPreinitAttempted;
    private boolean passportDecryptOutcomeHooked;
    private final java.util.concurrent.atomic.AtomicInteger passportDecryptOutcomeEvents =
        new java.util.concurrent.atomic.AtomicInteger();
    private boolean postLoginPipelineHooked;
    private final java.util.concurrent.atomic.AtomicInteger postLoginPipelineEvents =
        new java.util.concurrent.atomic.AtomicInteger();
    private final java.util.concurrent.atomic.AtomicInteger postLoginPipelineSourceEvents =
        new java.util.concurrent.atomic.AtomicInteger();
    private final java.util.concurrent.atomic.AtomicInteger postLoginTokenOutcomeEvents =
        new java.util.concurrent.atomic.AtomicInteger();
    private boolean postLoginFlowHooked;
    private final java.util.concurrent.atomic.AtomicInteger postLoginFlowEvents =
        new java.util.concurrent.atomic.AtomicInteger();
    private boolean postLoginPublishHooked;
    private boolean postLoginConsumeHooked;
    private boolean postLoginNativeRouteHooked;
    private final java.util.concurrent.atomic.AtomicInteger postLoginHookAttempts =
        new java.util.concurrent.atomic.AtomicInteger();
    private final java.util.concurrent.atomic.AtomicInteger postLoginStageEvents =
        new java.util.concurrent.atomic.AtomicInteger();
    private boolean passportDiagnosticCallbacksReady;
    private final java.util.concurrent.atomic.AtomicInteger passportCrashCaptured = new java.util.concurrent.atomic.AtomicInteger();
    private boolean exitCtorHooked;
    private boolean exitRunHooked;
    private final Map<Object, Integer> constructorModes =
        Collections.synchronizedMap(new WeakHashMap<>());
    // Identity-only linkage. No message, raw exception, stack, class name,
    // PID, thread ID or token ever leaves the process or the map.
    private final Map<Throwable, Boolean> metricaConstructed =
        Collections.synchronizedMap(new WeakHashMap<>());
    private final Map<Throwable, String> metricaDetailByThrowable =
        Collections.synchronizedMap(new WeakHashMap<>());
    private final Map<Throwable, String> sdkThrowSourceByObject =
        Collections.synchronizedMap(new WeakHashMap<>());
    private final Map<Throwable, String> sdkMessageHintByObject =
        Collections.synchronizedMap(new WeakHashMap<>());
    private volatile ClassLoader cloneAppClassLoader;
    private volatile Context exactCloneRuntimeContext;
    private boolean mediaDataReadWitnessReady;
    private final java.util.concurrent.atomic.AtomicInteger mediaDataReadCalls =
        new java.util.concurrent.atomic.AtomicInteger();
    private boolean mediaExtractorSourceHookReady;
    private final java.util.concurrent.atomic.AtomicInteger mediaExtractorSourceCalls =
        new java.util.concurrent.atomic.AtomicInteger();
    // Max 8 weak references; identity (==) only. NEVER hashCode(), equals(),
    // toString(), leak an identity hash, emit a vendor name or retain audio.
    // A successful match proves only framework source-object continuity.
    private final java.util.List<java.lang.ref.WeakReference<Object>>
        mediaExtractorObservedSources = new java.util.ArrayList<>();
    private final java.util.concurrent.atomic.AtomicInteger mediaReaderIdentityMatches =
        new java.util.concurrent.atomic.AtomicInteger();

    private void rememberMediaExtractorSource(Object obj) {
        if (obj == null) return;
        synchronized (mediaExtractorObservedSources) {
            for (java.lang.ref.WeakReference<Object> link : mediaExtractorObservedSources)
                if (link.get() == obj) return;
            if (mediaExtractorObservedSources.size() < 8)
                mediaExtractorObservedSources.add(new java.lang.ref.WeakReference<>(obj));
        }
    }

    private boolean readerWasPassedToExtractor(Object obj) {
        if (obj == null) return false;
        synchronized (mediaExtractorObservedSources) {
            for (java.lang.ref.WeakReference<Object> link : mediaExtractorObservedSources)
                if (link.get() == obj) return true;
        }
        return false;
    }
    private boolean ownRouteHooked;
    private final java.util.concurrent.atomic.AtomicInteger ownRouteEvents =
        new java.util.concurrent.atomic.AtomicInteger();
    private boolean privatePushBoolWitnessReady;
    private boolean exactPushProviderReady;
    private final java.util.concurrent.atomic.AtomicInteger exactPushProviderHits =
        new java.util.concurrent.atomic.AtomicInteger();
    private boolean metricaProviderQueryHookReady;
    private boolean metricaServiceHookReady;
    private final java.util.concurrent.atomic.AtomicInteger metricaServiceHitCount =
        new java.util.concurrent.atomic.AtomicInteger();
    private final java.util.concurrent.atomic.AtomicInteger metricaProviderQueryHits =
        new java.util.concurrent.atomic.AtomicInteger();
    private boolean privatePushSitesReady;
    private boolean allFatalGuardsReady;
    private boolean exactFatalObjectReady;
    private static final class ExactPushFrame {
        int yes, no, other, failed;
        boolean providerThrewAfterTrue;
        // In-memory throwable identity only; never expose or stringify object.
        final java.util.IdentityHashMap<Throwable,String> constructed =
            new java.util.IdentityHashMap<>();
    }
    private final ThreadLocal<ExactPushFrame> scopedPushCall=new ThreadLocal<>();
    private static String frameCategory(ExactPushFrame f) {
        if (f.failed>0) return "GUARD_THROW";
        if (f.yes>0 && f.no>0) return "GUARD_MIXED";
        if (f.yes>0) return "GUARD_TRUE_ONLY";
        if (f.no>0) return "GUARD_FALSE_ONLY";
        if (f.other>0) return "GUARD_NONBOOLEAN";
        return "GUARD_NOT_IN_CALL";
    }
    private final java.util.concurrent.atomic.AtomicInteger exactFatalObjectHits =
        new java.util.concurrent.atomic.AtomicInteger();
    private final java.util.concurrent.atomic.AtomicInteger allFatalGuardHitCount =
        new java.util.concurrent.atomic.AtomicInteger();
    private final java.util.concurrent.atomic.AtomicInteger privatePushSiteHits =
        new java.util.concurrent.atomic.AtomicInteger();
    private final java.util.concurrent.atomic.AtomicInteger privatePushBoolHits =
        new java.util.concurrent.atomic.AtomicInteger();

    @Override public void onModuleLoaded(ModuleLoadedParam param) { }

    @Override public void onPackageLoaded(PackageLoadedParam param) {
        if (!PACKAGE.equals(param.getPackageName())) return;
        // Exact prior ordering for *every* clone process; do not alter routing
        // or native startup behavior while adding passive Passport diagnostics.
        installOnboardingWriterWitness();
        installOwnedResourceRouteTrial();
        installCloneAccountTypeBridge();
        if (isPassportProcess()) armPassport();
        else arm();
        try { installExactRunModeWitness(param.getDefaultClassLoader()); }
        catch (Throwable ignored) { }
    }

    @Override public void onPackageReady(PackageReadyParam param) {
        if (!PACKAGE.equals(param.getPackageName())) return;
        installCloneAccountTypeBridge();
        if (isPassportProcess()) armPassport();
        else if (PACKAGE.equals(Application.getProcessName())) arm();
    }


    /**
     * Clone-owned account compatibility. Android's real AccountManager
     * authenticator ownership check remains fully enforced: after the paired
     * resource change the clone owns only PACKAGE+".passport", not the
     * publisher's "com.yandex.passport" type. Never borrow publisher accounts.
     *
     * Hooking the public Account(String,String) constructor catches the
     * issuer SDK's hardcoded compile-time account type without modifying
     * any signed issuer bytecode. No credentials, cookies, names or tokens are
     * observed. Do not simulate AccountManager success or handle exceptions.
     */
    private static String ownAccountTypeCategory(String value) {
        if (OWN_ACCOUNT_TYPE.equals(value)) return "CLONE_OWN";
        if (STOCK_ACCOUNT_TYPE.equals(value)) return "PUBLISHER_TYPE";
        if (value != null && value.startsWith(STOCK_ACCOUNT_TYPE + "."))
            return "PASSPORT_OTHER";
        return "OTHER_TYPE";
    }

    private static String ownAccountCountCategory(Object value) {
        if (!(value instanceof Account[])) return "NON_ARRAY";
        int n=((Account[])value).length;
        return n == 0 ? "ZERO" : n == 1 ? "ONE" : "MULTIPLE";
    }

    /** Diagnostic account-ownership snapshot only. Never reads account names,
     * tokens, numbers, account extras, cookies or passwords. */
    private void observeAccountSnapshot(Activity activity) {
        if (activity == null || accountSnapshots.incrementAndGet() > 16) return;
        try {
            AccountManager am=AccountManager.get(activity);
            if (am == null) {
                emit("ACCOUNT_STATE", "ANDROID", "NO_MANAGER");
                return;
            }
            android.accounts.AuthenticatorDescription[] all=am.getAuthenticatorTypes();
            boolean owned=false, stock=false;
            if (all != null) {
                for (android.accounts.AuthenticatorDescription a : all) {
                    if (a != null && OWN_ACCOUNT_TYPE.equals(a.type)
                            && PACKAGE.equals(a.packageName)) owned=true;
                    if (a != null && STOCK_ACCOUNT_TYPE.equals(a.type)) stock=true;
                }
            }
            emit("ACCOUNT_OWNER", owned ? "OWN_PRESENT" : "OWN_ABSENT",
                stock ? "PUBLISHER_PRESENT" : "PUBLISHER_ABSENT");
            emit("ACCOUNT_STATE", "CLONE_OWN",
                ownAccountCountCategory(am.getAccountsByType(OWN_ACCOUNT_TYPE)));
        } catch (SecurityException e) {
            emit("ACCOUNT_STATE", "CLONE_OWN", "DENIED");
        } catch (Throwable ignored) {
            emit("ACCOUNT_STATE", "CLONE_OWN", "UNAVAILABLE");
        }
    }


    /**
     * The original 2025 Passport account-store code invokes
     * AccountManager.getPassword(account) to recover its own encrypted master
     * token. Observe existence only on clone-owned accounts. In particular,
     * REAL AccountManager return/exception stays completely unchanged.
     */
    private synchronized void observeOwnedPasswordReturn() {
        if (ownedPasswordReturnHooked) return;
        try {
            Method m = AccountManager.class.getDeclaredMethod("getPassword", Account.class);
            hook(m).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                .intercept(chain -> {
                    Object candidate = chain.getArg(0);
                    boolean ours = candidate instanceof Account
                        && OWN_ACCOUNT_TYPE.equals(((Account) candidate).type);
                    Object result;
                    try {
                        result = chain.proceed();
                    } catch (Throwable failure) {
                        if (ours && ownedPasswordReturnEvents.incrementAndGet() <= 16)
                            emit("MASTER_TOKEN_READ", isPassportProcess() ? "PASSPORT" : "MAIN",
                                "THREW");
                        throw failure;
                    }
                    if (ours && ownedPasswordReturnEvents.incrementAndGet() <= 16)
                        emit("MASTER_TOKEN_READ", isPassportProcess() ? "PASSPORT" : "MAIN",
                            result instanceof String && !((String) result).isEmpty()
                                ? "PRESENT" : "NULL_OR_EMPTY");
                    return result;
                });
            ownedPasswordReturnHooked = true;
            emit("MASTER_TOKEN_HOOK", "ANDROID", "REGISTERED");
        } catch (Throwable ignored) {
            emit("MASTER_TOKEN_HOOK", "ANDROID", "NO_HOOK");
        }
    }

    private synchronized void installCloneAccountTypeBridge() {
        String process;
        try { process=Application.getProcessName(); }
        catch (Throwable ignored) { return; }
        if (!PACKAGE.equals(process) && !PASSPORT_PROCESS.equals(process)) return;

        if (!accountCtorHooked) {
            try {
                Constructor<Account> ctor=Account.class.getDeclaredConstructor(
                    String.class, String.class);
                hook(ctor).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                    .intercept(chain -> {
                        if (STOCK_ACCOUNT_TYPE.equals(chain.getArg(1))) {
                            // Preserve the actual account name untouched and
                            // pass the new owned type to the REAL constructor.
                            Object value=chain.proceed(new Object[]{
                                chain.getArg(0), OWN_ACCOUNT_TYPE});
                            if (ownAccountCtorRemaps.getAndIncrement()<8)
                                emit("ACCOUNT_BRIDGE", "CONSTRUCTOR", "STOCK_TO_OWN");
                            return value;
                        }
                        Object value=chain.proceed();
                        if (accountCtorObservations.incrementAndGet()<=16)
                            emit("ACCOUNT_CTOR", ownAccountTypeCategory(
                                chain.getArg(1) instanceof String
                                    ? (String)chain.getArg(1) : null), "REAL_RETURN");
                        return value;
                    });
                accountCtorHooked=true;
            } catch (Throwable ignored) { }
        }

        if (!accountQueryHooked) {
            try {
                Method query=AccountManager.class.getDeclaredMethod(
                    "getAccountsByType", String.class);
                hook(query).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                    .intercept(chain -> {
                        boolean remap=STOCK_ACCOUNT_TYPE.equals(chain.getArg(0));
                        String type=chain.getArg(0) instanceof String
                            ? (String)chain.getArg(0) : null;
                        try {
                            // Preserve the original NAV7 scoped remap; observe
                            // only the returned array length (never its content).
                            Object value=remap
                                ? chain.proceed(new Object[]{OWN_ACCOUNT_TYPE})
                                : chain.proceed();
                            if (remap && ownAccountQueryRemaps.getAndIncrement()<8)
                                emit("ACCOUNT_BRIDGE", "QUERY", "STOCK_TO_OWN");
                            if (accountQueryObservations.incrementAndGet()<=32)
                                emit("ACCOUNT_QUERY",
                                    ownAccountTypeCategory(type),
                                    ownAccountCountCategory(value));
                            return value;
                        } catch (Throwable failure) {
                            if (accountQueryObservations.incrementAndGet()<=32)
                                emit("ACCOUNT_QUERY",
                                    ownAccountTypeCategory(type),
                                    failure instanceof SecurityException
                                        ? "DENIED" : "THREW");
                            throw failure;
                        }
                    });
                accountQueryHooked=true;
            } catch (Throwable ignored) { }
        }

        // Exactly the system API that reported the owner's original
        // authorizeByCookie denial. Always forward the REAL operation
        // and boolean, without reading any password or Bundle value.
        if (!accountAddHooked) {
            try {
                Method add=AccountManager.class.getDeclaredMethod("addAccountExplicitly",
                    Account.class,String.class,Bundle.class);
                hook(add).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                    .intercept(chain -> {
                        Object raw=chain.getArg(0);
                        String type=raw instanceof Account ? ((Account)raw).type : null;
                        String family=ownAccountTypeCategory(type);
                        try {
                            Object result=chain.proceed();
                            if (accountAddObservations.incrementAndGet()<=16)
                                emit("ACCOUNT_ADD", family,
                                    Boolean.TRUE.equals(result) ? "ADDED"
                                        : "NOT_ADDED");
                            return result;
                        } catch (Throwable failure) {
                            if (accountAddObservations.incrementAndGet()<=16)
                                emit("ACCOUNT_ADD", family,
                                    failure instanceof SecurityException
                                        ? "DENIED" : "THREW");
                            throw failure;
                        }
                    });
                accountAddHooked=true;
            } catch (Throwable ignored) { }
        }
        if (!authenticatorTypesHooked) {
            try {
                Method types=AccountManager.class.getDeclaredMethod(
                    "getAuthenticatorTypes");
                hook(types).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                    .intercept(chain -> {
                        Object result=chain.proceed();
                        // Account types only: snapshot above performs the
                        // explicit unique owned-vs-stock registry checks.
                        if (accountRegistryObservations.incrementAndGet()<=16)
                            emit("ACCOUNT_REGISTRY", "ANDROID",
                                result instanceof android.accounts.AuthenticatorDescription[]
                                    ? "RETURN" : "UNAVAILABLE");
                        return result;
                    });
                authenticatorTypesHooked=true;
            } catch (Throwable ignored) { }
        }
        observeOwnedPasswordReturn();
        emit("ACCOUNT_BRIDGE", "REGISTERED",
            accountCtorHooked && accountQueryHooked && accountAddHooked
                ? "BOTH_PLUS_ADD_OBS" : accountCtorHooked && accountQueryHooked
                ? "BOTH" : accountCtorHooked ? "CTOR_ONLY"
                : accountQueryHooked ? "QUERY_ONLY" : "NO_HOOK");
    }

    private static boolean isPassportProcess() {
        try { return PASSPORT_PROCESS.equals(Application.getProcessName()); }
        catch (Throwable ignored) { return false; }
    }

    /** Minimal clone-only auxiliary process observation; never modify Passport. */
    private synchronized void armPassport() {
        if (passportArmed || !isPassportProcess()) return;
        passportArmed = true;
        int count = 0;
        count += observeApplicationOnCreate() ? 1 : 0;
        // Attach runs before content providers and Passport UI; ensure the
        // clone-owned account bridge is armed before SDK initialization.
        count += hookApplicationAttach() ? 1 : 0;
        count += observeOwnActivityFinish("finish") ? 1 : 0;
        count += observeOwnActivityLaunch("startActivity",
            new Class<?>[]{Intent.class}) ? 1 : 0;
        count += observeOwnActivityLaunch("startActivity",
            new Class<?>[]{Intent.class,Bundle.class}) ? 1 : 0;
        count += observeOwnActivityLaunch("startActivityForResult",
            new Class<?>[]{Intent.class,int.class}) ? 1 : 0;
        count += observeOwnActivityLaunch("startActivityForResult",
            new Class<?>[]{Intent.class,int.class,Bundle.class}) ? 1 : 0;
        count += observePassportResultDelivery() ? 1 : 0;
        count += observe(Thread.class, "dispatchUncaughtException",
            new Class<?>[]{Throwable.class}, "UNCAUGHT") ? 1 : 0;
        count += observe(System.class, "exit",
            new Class<?>[]{int.class}, "SYSTEM_EXIT") ? 1 : 0;
        count += observe(Runtime.class, "exit",
            new Class<?>[]{int.class}, "RUNTIME_EXIT") ? 1 : 0;
        count += observe(android.os.Process.class, "killProcess",
            new Class<?>[]{int.class}, "PROCESS_KILL") ? 1 : 0;
        count += observeFatalDispatches();
        emit("PASSPORT_OBSERVER", "CLONE_PASSPORT", count > 0 ? "REGISTERED" : "NO_HOOK");
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
        count += observeApplicationOnCreate() ? 1 : 0;
        count += observeOwnActivityFinish("finish") ? 1 : 0;
        count += observeOwnActivityFinish("finishAffinity") ? 1 : 0;
        count += observeOwnActivityFinish("finishAfterTransition") ? 1 : 0;
        count += observeOwnActivityFinish("finishAndRemoveTask") ? 1 : 0;
        count += observeOwnActivityLaunch("startActivity",
            new Class<?>[]{Intent.class}) ? 1 : 0;
        count += observeOwnActivityLaunch("startActivity",
            new Class<?>[]{Intent.class,Bundle.class}) ? 1 : 0;
        count += observeOwnActivityLaunch("startActivityForResult",
            new Class<?>[]{Intent.class,int.class}) ? 1 : 0;
        count += observeOwnActivityLaunch("startActivityForResult",
            new Class<?>[]{Intent.class,int.class,Bundle.class}) ? 1 : 0;
        count += observePassportResultDelivery() ? 1 : 0;
        count += observeEntryActivityResultDelivery() ? 1 : 0;
        count += observeLoginResultNewIntent() ? 1 : 0;
        count += observeHi2IllegalStateConstructor() ? 1 : 0;
        count += observeFatalDispatches();
        // Arms only tell us that a hook was registered, not that it ran.
        emit("ARMED", count > 0 ? "REGISTERED" : "NO_HOOK", "NONE");
    }

    /** Passport subprocess fatal-only observer. Never logs exception text,
     * source names, account details, URLs, tokens or raw stack. */
    private static String passportThrowableFamily(Throwable t) {
        if (t == null) return "NONE";
        if (t instanceof IllegalStateException) return "ILLEGAL_STATE";
        if (t instanceof SecurityException) return "SECURITY";
        if (t instanceof IllegalArgumentException) return "ILLEGAL_ARGUMENT";
        if (t instanceof NullPointerException) return "NULL_POINTER";
        if (t instanceof ClassNotFoundException) return "CLASS_NOT_FOUND";
        if (t instanceof NoClassDefFoundError) return "NO_CLASS_DEF";
        if (t instanceof LinkageError) return "LINKAGE";
        if (t instanceof java.io.IOException) return "IO";
        if (t instanceof RuntimeException) return "RUNTIME_OTHER";
        if (t instanceof Error) return "ERROR_OTHER";
        return "OTHER_THROWABLE";
    }

    private static String passportMessageHint(Throwable t) {
        if (t == null) return "NONE";
        try {
            String msg = t.getMessage();
            if (msg == null || msg.length() == 0) return "EMPTY";
            String s = msg.toLowerCase(java.util.Locale.ROOT);
            if (s.contains("signature") || s.contains("certificate") ||
                    s.contains("signing") || s.contains("fingerprint"))
                return "SIGNATURE";
            if (s.contains("not initialized") || s.contains("not initialised") ||
                    s.contains("not been initialized")) return "NOT_INITIALIZED";
            if (s.contains("already initialized") || s.contains("already initialised"))
                return "ALREADY_INITIALIZED";
            if (s.contains("main thread") || s.contains("ui thread"))
                return "THREAD_REQUIREMENT";
            if (s.contains("account") || s.contains("passport") ||
                    s.contains("authentication") || s.contains("authorization") ||
                    s.contains("login") || s.contains("credential") ||
                    s.contains("token")) return "PASSPORT_AUTH";
            if (s.contains("package") || s.contains("application id"))
                return "PACKAGE_ID";
            if (s.contains("activity") || s.contains("fragment") ||
                    s.contains("intent")) return "ACTIVITY_NAV";
            if (s.contains("provider") || s.contains("authority"))
                return "PROVIDER";
            if (s.contains("firebase")) return "FIREBASE";
            if (s.contains("resource") || s.contains("theme"))
                return "RESOURCES";
            if (s.contains("config") || s.contains("property"))
                return "CONFIG";
            if (s.contains("permission") || s.contains("denied"))
                return "PERMISSION";
            if (s.contains("service") || s.contains("bind"))
                return "SERVICE_BIND";
            if (s.contains("coroutine") || s.contains("dispatcher"))
                return "COROUTINE";
            if (s.contains("context")) return "CONTEXT";
            if (s.contains("not registered") || s.contains("unregistered"))
                return "UNREGISTERED";
            if (s.contains("not found") || s.contains("missing"))
                return "MISSING";
            if (s.contains("unsupported") || s.contains("not supported"))
                return "UNSUPPORTED";
            if (s.contains("expected")) return "EXPECTED";
            return "OTHER_MESSAGE";
        } catch (Throwable ignored) { return "MESSAGE_UNAVAILABLE"; }
    }

    private static String passportFrameFamily(String n) {
        if (n == null) return "UNKNOWN";
        if (n.startsWith("com.yandex.passport") ||
                n.startsWith("ru.yandex.passport")) return "PASSPORT";
        if (n.startsWith("ru.yandex.music")) return "MUSIC";
        if (n.startsWith("com.yandex.") || n.startsWith("ru.yandex."))
            return "YANDEX_OTHER";
        if (n.startsWith("android.") || n.startsWith("com.android."))
            return "ANDROID";
        if (n.startsWith("java.") || n.startsWith("javax.")) return "JAVA";
        if (n.startsWith("kotlin.") || n.startsWith("kotlinx."))
            return "KOTLIN";
        if (n.startsWith("io.github.libxposed") ||
                n.startsWith("org.lsposed")) return "HOOK_RUNTIME";
        return "OTHER";
    }

    private static String passportFrameFingerprint(StackTraceElement frame) {
        if (frame == null) return "NO_FRAME";
        try {
            String symbol = frame.getClassName() + "#" + frame.getMethodName();
            byte[] digest = java.security.MessageDigest.getInstance("SHA-256")
                .digest(symbol.getBytes(StandardCharsets.UTF_8));
            char[] digits = "0123456789ABCDEF".toCharArray();
            char[] hex = new char[16];
            for (int i = 0; i < 8; i++) {
                int b = digest[i] & 255;
                hex[2 * i] = digits[b >>> 4];
                hex[2 * i + 1] = digits[b & 15];
            }
            return "SYM_" + new String(hex);
        } catch (Throwable ignored) { return "SYMBOL_UNAVAILABLE"; }
    }

    private void capturePassportUncaught(Throwable failure) {
        if (!isPassportProcess() || failure == null ||
                passportCrashCaptured.incrementAndGet() > 1) return;
        try {
            Throwable c = failure;
            for (int depth = 0; c != null && depth < 3; depth++) {
                emit("PASSPORT_FATAL_TYPE", "CAUSE_" + depth,
                    passportThrowableFamily(c));
                emit("PASSPORT_FATAL_HINT", "CAUSE_" + depth,
                    passportMessageHint(c));
                StackTraceElement[] stack = c.getStackTrace();
                if (stack != null) for (int i = 0; i < Math.min(10, stack.length); i++) {
                    StackTraceElement e = stack[i];
                    emit("PASSPORT_FATAL_FRAME",
                        "D" + depth + "_F" + i + "_" +
                            passportFrameFamily(e.getClassName()),
                        passportFrameFingerprint(e));
                }
                Throwable next = c.getCause();
                if (next == c) break;
                c = next;
            }
        } catch (Throwable ignored) { }
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
                            if (isPassportProcess() && value instanceof Throwable)
                                capturePassportUncaught((Throwable) value);
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
                    // Exactly ONE original execution. Observers cannot cause a
                    // constructor to run twice if an instrumentation API fails.
                    String metrica = "NO_METRICA_FRAME";
                    String category = "EXC_UNKNOWN";
                    String detail = "DETAIL_UNKNOWN";
                    String sdkThrowSource = "SDK_NO_FRAME";
                    String sdkMessageHint = "HINT_NONE";
                    String sdkExecution = "EXEC_OTHER";
                    String sdkThreadLoader = "LOADER_UNKNOWN";
                    String pushClassGroup = "PUSH_NONE";
                    String pushMethodGroup = "PUSH_METHOD_NONE";
                    boolean exactHi2 = false;
                    try {
                        Object message = chain.getArg(0);
                        category = redactedErrorCategory(message);
                        detail = redactedMetricaDetail(message);
                        sdkMessageHint = sdkInitializationHint(message);
                        exactHi2 = callerIsExactHi2Coroutine();
                        metrica = callerMetricaFrameGroup();
                        sdkThrowSource = sdkThrowSourceCategory();
                        sdkExecution = sdkThrowExecutionCategory();
                        pushClassGroup = pushThrowableClassGroup();
                        pushMethodGroup = pushThrowableMethodGroup();
                        ClassLoader mainLoader = cloneAppClassLoader;
                        if (mainLoader != null) {
                            ClassLoader threadLoader = Thread.currentThread().getContextClassLoader();
                            sdkThreadLoader = threadLoader == null ? "LOADER_NULL"
                                : threadLoader == mainLoader ? "LOADER_MATCH" : "LOADER_DIFFERENT";
                        }
                    } catch (Throwable ignored) { }
                    Object result = chain.proceed();
                    try {
                        if (exactHi2)
                            emit("HI2_EXCEPTION", "STATIC_COROUTINE", category);
                        if (!"NO_METRICA_FRAME".equals(metrica)) {
                            Object constructed = chain.getThisObject();
                            if ("METRICA_SDK".equals(metrica) &&
                                    constructed instanceof Throwable) {
                                Throwable object = (Throwable) constructed;
                                metricaConstructed.put(object, Boolean.TRUE);
                                // Exact same-call constructor order versus the
                                // already-proven TRUE guard. Observe, never alter.
                                ExactPushFrame frame=scopedPushCall.get();
                                if (frame!=null && frame.constructed.size()<8)
                                    frame.constructed.put(object,
                                        frame.yes>0 ? "CTOR_AFTER_TRUE"
                                                   : "CTOR_BEFORE_TRUE");
                                metricaDetailByThrowable.put(object, detail);
                                sdkThrowSourceByObject.put(object, sdkThrowSource);
                                sdkMessageHintByObject.put(object, sdkMessageHint);
                                emit("METRICA_DETAIL", metrica, detail);
                                emit("METRICA_THROW_HINT", "METRICA_SDK", sdkMessageHint);
                                emit("METRICA_THROW_SITE", "METRICA_SDK", sdkThrowSource);
                                emit("METRICA_THROW_EXEC", "METRICA_SDK", sdkExecution);
                                emit("METRICA_THROW_LOADER", "METRICA_SDK", sdkThreadLoader);
                                emit("METRICA_PUSH_THROW_CLASS", "METRICA_SDK", pushClassGroup);
                                emit("METRICA_PUSH_THROW_METHOD", "METRICA_SDK", pushMethodGroup);
                            }
                            emit("METRICA_EXCEPTION", metrica, category);
                        }
                    } catch (Throwable ignored) { }
                    return result;
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
                        if (arg instanceof Throwable) {
                            Throwable thrown=(Throwable) arg;
                            String category=throwableIdentityCategory(thrown);
                            emit("FATAL_DISPATCH", origin, category);
                            if ("DIRECT_METRICA".equals(category) ||
                                    "CAUSE_METRICA".equals(category))
                                emit("FATAL_DETAIL", origin,
                                    throwableDetailCategory(thrown));
                            if ("DIRECT_METRICA".equals(category)) {
                                String source = sdkThrowSourceByObject.get(thrown);
                                emit("FATAL_THROW_SITE", origin,
                                    source == null ? "SDK_NO_FRAME" : source);
                                String hint = sdkMessageHintByObject.get(thrown);
                                emit("FATAL_THROW_HINT", origin,
                                    hint == null ? "HINT_NONE" : hint);
                            }
                        } else emit("FATAL_DISPATCH", origin, "NON_THROWABLE");
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

    /**
     * Error detail can include credentials and identifiers: process it ONLY
     * into these hard-coded categories. Never emit the actual input text.
     */
    private static String redactedMetricaDetail(Object value) {
        if (!(value instanceof String)) return "DETAIL_UNKNOWN";
        String s=((String)value).toLowerCase(java.util.Locale.ROOT);
        if (s.contains("not initialized") || s.contains("not initialised") ||
                s.contains("isn't initialized") || s.contains("not activated") ||
                s.contains("not activate") || s.contains("not been activated") ||
                s.contains("not been initialized"))
            return "DETAIL_NOT_INITIALIZED";
        if (s.contains("already initialized") || s.contains("already activated") ||
                s.contains("already initialised"))
            return "DETAIL_ALREADY_ACTIVE";
        if (s.contains("api key") || s.contains("apikey") ||
                s.contains("api_key") || s.contains("invalid key"))
            return "DETAIL_API_KEY";
        if (s.contains("package") || s.contains("application id") ||
                s.contains("applicationid") || s.contains("context"))
            return "DETAIL_PACKAGE_CONTEXT";
        if (s.contains("service") || s.contains("provider") ||
                s.contains("component") || s.contains("manifest"))
            return "DETAIL_ANDROID_COMPONENT";
        if (s.contains("configuration") || s.contains("config"))
            return "DETAIL_CONFIG";
        if (s.contains("permission") || s.contains("denied"))
            return "DETAIL_PERMISSION";
        if (s.contains("crash") || s.contains("handler") || s.contains("report"))
            return "DETAIL_CRASH_HANDLER";
        return "DETAIL_OTHER";
    }

    private String throwableDetailCategory(Throwable thrown) {
        try {
            String direct=metricaDetailByThrowable.get(thrown);
            if (direct!=null) return direct;
            Throwable next=thrown.getCause();
            for (int i=0;next!=null&&i<8;i++) {
                String category=metricaDetailByThrowable.get(next);
                if (category!=null) return category;
                if (next==next.getCause()) break;
                next=next.getCause();
            }
        } catch (Throwable ignored) { }
        return "DETAIL_UNOBSERVED";
    }

    // The first SDK frame closest to an IllegalStateException constructor.
    // Never transmit raw class/method names or an actual stack trace.
    private static String sdkThrowSourceCategory() {
        try {
            for (StackTraceElement frame:Thread.currentThread().getStackTrace()) {
                String cls=frame.getClassName();
                if (cls.equals("com.yandex.metrica.YandexMetrica"))
                    return "SDK_LEGACY_PUBLIC";
                if (cls.startsWith("com.yandex.metrica.impl."))
                    return "SDK_LEGACY_IMPL";
                if (cls.startsWith("com.yandex.metrica.coreutils."))
                    return "SDK_COMMON_UTILS";
                if (cls.startsWith("com.yandex.metrica.coreapi."))
                    return "SDK_COMMON_API";
                if (cls.startsWith("com.yandex.metrica.identifiers."))
                    return "SDK_IDENTIFIERS";
                if (cls.startsWith("com.yandex.metrica.push."))
                    return "SDK_PUSH";
                if (cls.startsWith("com.yandex.metrica.network."))
                    return "SDK_NETWORK";
                if (cls.startsWith("com.yandex.metrica.plugins."))
                    return "SDK_PLUGINS";
                if (cls.startsWith("com.yandex.metrica.billing."))
                    return "SDK_BILLING";
                if (cls.startsWith("com.yandex.metrica.analytics."))
                    return "SDK_ANALYTICS";
                if (cls.startsWith("com.yandex.metrica.internal."))
                    return "SDK_COMMON_INTERNAL";
                if (cls.startsWith("com.yandex.metrica.utils.")
                    || cls.startsWith("com.yandex.metrica.util."))
                    return "SDK_UTILS";
                if (cls.startsWith("com.yandex.metrica."))
                    return "SDK_LEGACY_OTHER";
                if (!cls.startsWith("io.appmetrica.analytics.")) continue;
                if (cls.startsWith("io.appmetrica.analytics.impl.crash.")) return "SDK_CRASH";
                if (cls.startsWith("io.appmetrica.analytics.impl.service.")) return "SDK_SERVICE";
                if (cls.startsWith("io.appmetrica.analytics.impl.startup.")) return "SDK_STARTUP";
                if (cls.startsWith("io.appmetrica.analytics.impl.proxy.")) return "SDK_PROXY";
                if (cls.startsWith("io.appmetrica.analytics.impl.reporter.")) return "SDK_REPORTER";
                if (cls.startsWith("io.appmetrica.analytics.impl.")) return "SDK_INTERNAL";
                return "SDK_PUBLIC";
            }
        } catch (Throwable ignored) { }
        return "SDK_NO_FRAME";
    }

    // The exception message is never persisted, only one fixed category.
    private static String sdkInitializationHint(Object value) {
        if (!(value instanceof String)) return "HINT_NONE";
        String s=((String)value).toLowerCase(java.util.Locale.ROOT);
        if (s.contains("yandexmetrica")) return "HINT_LEGACY_API";
        if (s.contains("appmetrica")) return "HINT_MODERN_API";
        if (s.contains("metrica")) return "HINT_METRICA_GENERAL";
        return "HINT_NONE";
    }


    // Classify only the nearest push frame. No class/method name is logged.
    private static String pushThrowableClassGroup() {
        try {
            for (StackTraceElement f : Thread.currentThread().getStackTrace()) {
                String name=f.getClassName();
                if (!name.startsWith("com.yandex.metrica.push.")) continue;
                if (name.startsWith("com.yandex.metrica.push.impl.")) return "PUSH_IMPL";
                if (name.startsWith("com.yandex.metrica.push.common.")) return "PUSH_COMMON";
                if (name.startsWith("com.yandex.metrica.push.service.")) return "PUSH_SERVICE";
                if (name.startsWith("com.yandex.metrica.push.firebase.")) return "PUSH_FIREBASE";
                if (name.startsWith("com.yandex.metrica.push.core.")) return "PUSH_CORE";
                return "PUSH_OTHER";
            }
        } catch (Throwable ignored) { }
        return "PUSH_NONE";
    }

    private static String pushThrowableMethodGroup() {
        try {
            for (StackTraceElement f : Thread.currentThread().getStackTrace()) {
                if (!f.getClassName().startsWith("com.yandex.metrica.push."))
                    continue;
                String name=f.getMethodName();
                if ("init".equals(name)) return "PUSH_METHOD_INIT";
                if ("activate".equals(name)) return "PUSH_METHOD_ACTIVATE";
                if ("a".equals(name)) return "PUSH_METHOD_OBFUSCATED_A";
                if ("l".equals(name)) return "PUSH_METHOD_OBFUSCATED_L";
                return "PUSH_METHOD_OTHER";
            }
        } catch (Throwable ignored) { }
        return "PUSH_METHOD_NONE";
    }

    private static String sdkThrowExecutionCategory() {
        try {
            boolean coroutine=false, executor=false, handler=false;
            for (StackTraceElement frame:Thread.currentThread().getStackTrace()) {
                String cls=frame.getClassName();
                if (cls.startsWith("kotlinx.coroutines.")) coroutine=true;
                if (cls.startsWith("java.util.concurrent.")) executor=true;
                if (cls.startsWith("android.os.Handler")
                    || cls.startsWith("android.os.Looper")) handler=true;
            }
            return coroutine ? "EXEC_COROUTINE" : executor ? "EXEC_EXECUTOR"
                : handler ? "EXEC_HANDLER" : "EXEC_OTHER";
        } catch (Throwable ignored) { return "EXEC_OTHER"; }
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

    // Observe SDK activation on our own clone ONLY. No config/API keys are
    // logged, SDK results/exception behavior are never changed.
    private boolean metricaActivationHookReady;
    private boolean modulesActivationObserverReady;
    private boolean pushActivationObserverReady;
    private final java.util.concurrent.atomic.AtomicInteger modulesObservationCount =
        new java.util.concurrent.atomic.AtomicInteger();
    private final java.util.concurrent.atomic.AtomicInteger pushActivationCount =
        new java.util.concurrent.atomic.AtomicInteger();
    private boolean metricaStateProbeReady;
    private boolean metricaPublicProbeReady;
    private final java.util.Set<Class<?>> reporterClasses =
        Collections.synchronizedSet(Collections.newSetFromMap(
            new WeakHashMap<Class<?>, Boolean>()));
    private final java.util.concurrent.atomic.AtomicInteger reporterHitCount =
        new java.util.concurrent.atomic.AtomicInteger();
    private final java.util.concurrent.atomic.AtomicInteger stateHits =
        new java.util.concurrent.atomic.AtomicInteger();
    private final java.util.concurrent.atomic.AtomicInteger publicHits =
        new java.util.concurrent.atomic.AtomicInteger();
    private volatile boolean appOnCreateEntered;
    private volatile boolean appOnCreateReturned;

    private synchronized void installMetricaActivationWitness(ClassLoader appLoader) {
        if (metricaActivationHookReady || appLoader == null) return;
        int registered=0;
        for (String className : new String[]{
                "com.yandex.metrica.YandexMetrica",
                "io.appmetrica.analytics.AppMetrica"}) {
            final String family=className.startsWith("com.yandex.")
                ? "METRICA_LEGACY" : "METRICA_MODERN";
            try {
                Class<?> sdk=Class.forName(className, false, appLoader);
                emit("SDK_CLASS",family,"CLASS_PRESENT");
                final ClassLoader sdkLoader=sdk.getClassLoader();
                int activationSignatures=0;
                for (Method method : sdk.getDeclaredMethods()) {
                    if (!"activate".equals(method.getName()) ||
                            !java.lang.reflect.Modifier.isStatic(method.getModifiers()))
                        continue;
                    Class<?>[] parameters=method.getParameterTypes();
                    if (parameters.length<1 ||
                            !Context.class.isAssignableFrom(parameters[0]))
                        continue;
                    activationSignatures++;
                    method.setAccessible(true);
                    hook(method).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                        .intercept(chain -> {
                            String contextType="MISSING";
                            try {
                                Object context=chain.getArg(0);
                                if (context instanceof Context)
                                    contextType=packageIdentityCategory(
                                        ((Context) context).getPackageName());
                                emit("METRICA_CONTEXT",family,contextType);
                                String loaderState="MISSING";
                                Object ctx=chain.getArg(0);
                                if (ctx instanceof Context)
                                    loaderState=((Context)ctx).getClassLoader()==sdkLoader
                                        ? "LOADER_MATCH" : "LOADER_DIFFERENT";
                                emit("METRICA_LOADER",family,loaderState);
                                emit("METRICA_PHASE",family,
                                    !appOnCreateEntered ? "BEFORE_ONCREATE"
                                    : appOnCreateReturned ? "AFTER_ONCREATE"
                                    : "DURING_ONCREATE");
                                emit("METRICA_ACTIVATE",family,"ENTER");
                            } catch (Throwable ignored) { }
                            try {
                                Object result=chain.proceed();
                                emit("METRICA_ACTIVATE", family, "RETURN");
                                return result;
                            } catch (Throwable problem) {
                                emit("METRICA_ACTIVATE", family, "THROW");
                                throw problem;
                            }
                        });
                    registered++;
                }
                emit("SDK_ACTIVATE_SIGNATURE",family,
                    activationSignatures>0 ? "ACTIVATE_PRESENT" : "ACTIVATE_ABSENT");
            } catch (Throwable ignored) {
                emit("SDK_CLASS",family,"CLASS_MISSING");
            }
        }
        metricaActivationHookReady=registered>0;
        emit("ACTIVATION_HOOK","METRICA_SDK",
            registered>0 ? "REGISTERED":"NO_HOOK");
    }



    // Read-only observation of exactly the predicate used by AppMetrica Push
    // before throwing "isn't initialized"; does NOT call the predicate itself.
    private synchronized void installModulesActivationObserver(ClassLoader loader) {
        if (modulesActivationObserverReady || loader==null) return;
        int registered=0;
        for (String clsName : new String[]{
                "io.appmetrica.analytics.ModulesFacade",
                "com.yandex.metrica.ModulesFacade"}) {
            final String family=clsName.startsWith("io.")
                ? "METRICA_MODERN" : "METRICA_LEGACY";
            try {
                Class<?> cls=Class.forName(clsName,false,loader);
                Method method=cls.getDeclaredMethod("isActivatedForApp");
                method.setAccessible(true);
                hook(method).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                    .intercept(chain -> {
                        try {
                            Object result=chain.proceed();
                            if (modulesObservationCount.incrementAndGet()<=48)
                                emit("MODULES_IS_ACTIVATED",family,
                                    Boolean.TRUE.equals(result) ? "TRUE":"FALSE");
                            return result;
                        } catch (Throwable fail) {
                            if (modulesObservationCount.incrementAndGet()<=48)
                                emit("MODULES_IS_ACTIVATED",family,"THROW");
                            throw fail;
                        }
                    });
                registered++;
                emit("MODULES_HOOK",family,"REGISTERED");
            } catch (Throwable ignored) {
                emit("MODULES_HOOK",family,"NO_HOOK");
            }
        }
        modulesActivationObserverReady=registered>0;
    }

    // Only observe actual public Push.activate calls if vendor class names
    // have survived minification. No fake/reordered initialization is added.

    // Read-only observation of the actual legacy Push.init, not just activate.
    // Original arguments, return values, and exception semantics are untouched.
    private final java.util.concurrent.atomic.AtomicInteger pushInitCount =
        new java.util.concurrent.atomic.AtomicInteger();
    private synchronized void installPushActivationObserver(ClassLoader loader) {
        if (pushActivationObserverReady || loader==null) return;
        int registered=0;
        for (String clsName : new String[]{
                "io.appmetrica.analytics.push.AppMetricaPush",
                "com.yandex.metrica.push.YandexMetricaPush",
                "com.yandex.metrica.push.AppMetricaPush"}) {
            final String family=clsName.startsWith("io.")
                ? "PUSH_MODERN" : "PUSH_LEGACY";
            int initRegistered=0, activationRegistered=0;
            try {
                Class<?> cls=Class.forName(clsName,false,loader);
                for (Method method:cls.getDeclaredMethods()) {
                    boolean init="init".equals(method.getName());
                    boolean activate="activate".equals(method.getName());
                    if ((!init && !activate) ||
                        !java.lang.reflect.Modifier.isStatic(method.getModifiers()))
                        continue;
                    final String event=init ? "PUSH_INIT":"PUSH_ACTIVATE";
                    method.setAccessible(true);
                    hook(method).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                        .intercept(chain -> {
                            int hit=(init ? pushInitCount : pushActivationCount)
                                .incrementAndGet();
                            if (hit<=32)emit(event,family,"ENTER");
                            try {
                                Object result=chain.proceed();
                                if (hit<=32)emit(event,family,"RETURN");
                                return result;
                            } catch (Throwable fail) {
                                if (hit<=32)emit(event,family,"THROW");
                                throw fail;
                            }
                        });
                    registered++;
                    if (init) initRegistered++; else activationRegistered++;
                }
                emit("PUSH_INIT_HOOK",family,
                    initRegistered>0 ? "REGISTERED":"NO_HOOK");
                emit("PUSH_ACTIVATE_HOOK",family,
                    activationRegistered>0 ? "REGISTERED":"NO_HOOK");
            } catch (Throwable ignored) {
                emit("PUSH_INIT_HOOK",family,"NO_HOOK");
                emit("PUSH_ACTIVATE_HOOK",family,"NO_HOOK");
            }
        }
        pushActivationObserverReady=registered>0;
    }


    // Ephemeral-only read-only hooks. PrivatePushTargets.java is generated
    // inside CI from the exact verified publisher XAPK and NEVER committed,
    // logged, uploaded or shipped. This module builds without that class.
    private synchronized void installPrivatePushBoolWitness(ClassLoader loader) {
        if (privatePushBoolWitnessReady || loader == null) return;
        int registered=0;
        try {
            Class<?> targets=Class.forName(
                "pro.celikom.a1exitwitness.PrivatePushTargets",false,
                ExitCallsiteWitness.class.getClassLoader());
            Method get=targets.getDeclaredMethod("getTargets");
            Object result=get.invoke(null);
            if (!(result instanceof String[][])) {
                emit("PUSH_HELPER_HOOK","PUSH_HELPER","NO_HOOK");
                return;
            }
            String[][] pairs=(String[][])result;
            java.util.Set<Method> unique=new java.util.HashSet<>();
            for (int i=0; i<pairs.length && i<24; i++) {
                String[] pair=pairs[i];
                if (pair==null || pair.length!=2 || pair[0]==null ||
                        pair[1]==null) continue;
                try {
                    Class<?> cls=Class.forName(pair[0],false,loader);
                    for (Method m:cls.getDeclaredMethods()) {
                        if (!pair[1].equals(m.getName()) ||
                                m.getReturnType()!=boolean.class ||
                                !unique.add(m)) continue;
                        m.setAccessible(true);
                        hook(m).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                            .intercept(chain -> {
                                int hit=privatePushBoolHits.incrementAndGet();
                                if (hit<=24)
                                    emit("PUSH_HELPER_BOOL","PUSH_HELPER","ENTER");
                                try {
                                    Object value=chain.proceed();
                                    if (hit<=24)
                                        emit("PUSH_HELPER_BOOL","PUSH_HELPER",
                                            Boolean.TRUE.equals(value)
                                                ? "TRUE":"FALSE");
                                    return value;
                                } catch (Throwable failure) {
                                    if (hit<=24)
                                        emit("PUSH_HELPER_BOOL","PUSH_HELPER","THROW");
                                    throw failure;
                                }
                            });
                        registered++;
                    }
                } catch (Throwable ignored) {
                    // One unavailable class does not disable other exact targets.
                }
            }
        } catch (Throwable ignored) {
            // Public source intentionally does not include private Java targets.
        }
        privatePushBoolWitnessReady=registered>0;
        emit("PUSH_HELPER_HOOK","PUSH_HELPER",
            registered>0 ? "REGISTERED":"NO_HOOK");
    }


    // Exact privately generated callsites. Lab-only, forwards every result/throw.
    private synchronized void installPrivatePushSiteWitness(ClassLoader loader) {
        if (privatePushSitesReady || loader == null) return;
        int guardCount=0, fatalCount=0, nearCount=0;
        try {
            Class<?> targets=Class.forName("pro.celikom.a1exitwitness.PrivatePushTargets",
                false,ExitCallsiteWitness.class.getClassLoader());
            for (String accessor:new String[]{"getGuardTargets","getFatalTargets","getNearFatalGuardTargets"}) {
                final boolean fatal="getFatalTargets".equals(accessor);
                final boolean near="getNearFatalGuardTargets".equals(accessor);
                Object returned=targets.getDeclaredMethod(accessor).invoke(null);
                if (!(returned instanceof String[][])) continue;
                java.util.Set<Method> unique=new java.util.HashSet<>();
                String[][] pairs=(String[][])returned;
                for (int i=0;i<pairs.length && i<16;i++) {
                    String[] pair=pairs[i];
                    if (pair==null || pair.length!=2 || pair[0]==null
                        || pair[1]==null) continue;
                    try {
                        Class<?> cls=Class.forName(pair[0],false,loader);
                        for (Method method:cls.getDeclaredMethods()) {
                            if (!pair[1].equals(method.getName())
                                || !unique.add(method)) continue;
                            if (!fatal && !near && (method.getReturnType()!=boolean.class
                                    || method.getParameterTypes().length!=1
                                    || method.getParameterTypes()[0]!=String.class))
                                continue;
                            if (near && method.getReturnType()!=boolean.class)
                                continue;
                            method.setAccessible(true);
                            hook(method).setExceptionMode(
                                XposedInterface.ExceptionMode.PROTECTIVE)
                                .intercept(chain -> {
                                    int hit=privatePushSiteHits.incrementAndGet();
                                    String event=fatal ? "PUSH_FATAL_CALL"
                                        : near ? "PUSH_NEAR_GUARD_VALUE" : "PUSH_GUARD_VALUE";
                                    String source=fatal ? "PUSH_FATAL"
                                        : near ? "PUSH_NEAR_GUARD" : "PUSH_GUARD";
                                    if (hit<=72) {
                                        emit(event,source,"ENTER");
                                        if (!fatal && !near) {
                                            String state="OTHER_INPUT";
                                            try {
                                                Object input=chain.getArg(0);
                                                state=input==null ? "NULL"
                                                    : input instanceof String
                                                    ? (((String)input).isEmpty()
                                                        ? "EMPTY":"NONEMPTY")
                                                    : "OTHER_INPUT";
                                            } catch (Throwable ignored) { }
                                            emit("PUSH_GUARD_INPUT","PUSH_GUARD",state);
                                        }
                                    }
                                    try {
                                        Object value=chain.proceed();
                                        if (near) {
                                            ExactPushFrame frame=scopedPushCall.get();
                                            if (frame!=null) {
                                                if (Boolean.TRUE.equals(value)) frame.yes++;
                                                else if (Boolean.FALSE.equals(value)) frame.no++;
                                                else frame.other++;
                                            }
                                        }
                                        if (hit<=72) emit(event,source,
                                            fatal ? "RETURN"
                                            : Boolean.TRUE.equals(value) ? "TRUE"
                                            : Boolean.FALSE.equals(value) ? "FALSE"
                                            : "NON_BOOLEAN");
                                        return value;
                                    } catch (Throwable failure) {
                                        if (near) {
                                            ExactPushFrame frame=scopedPushCall.get();
                                            if (frame!=null) frame.failed++;
                                        }
                                        if (hit<=72) emit(event,source,
                                            fatal && "DIRECT_METRICA".equals(
                                                throwableIdentityCategory(failure))
                                                ? "DIRECT_METRICA":"OTHER_THROW");
                                        throw failure;
                                    }
                                });
                            if (fatal) fatalCount++;
                            else if (near) nearCount++;
                            else guardCount++;
                        }
                    } catch (Throwable ignored) { }
                }
            }
        } catch (Throwable ignored) { }
        privatePushSitesReady=guardCount>0 || fatalCount>0 || nearCount>0;
        emit("PUSH_GUARD_HOOK","PUSH_GUARD",guardCount>0?"REGISTERED":"NO_HOOK");
        emit("PUSH_FATAL_HOOK","PUSH_FATAL",fatalCount>0?"REGISTERED":"NO_HOOK");
        emit("PUSH_NEAR_GUARD_HOOK","PUSH_NEAR_GUARD",
            nearCount>0?"REGISTERED":"NO_HOOK");
    }


    // Two exact private DEX-derived Boolean targets (or fewer/more up to 8).
    // Only generated in disposable CI. No method names/argument values logged.
    private static String privateMethodParameterSignature(Method method) {
        StringBuilder key=new StringBuilder();
        Class<?>[] parameters=method.getParameterTypes();
        for (int i=0;i<parameters.length;i++) {
            if (i>0) key.append(',');
            key.append(parameters[i].getName());
        }
        return key.toString();
    }

    private synchronized void installAllFatalGuardWitness(ClassLoader loader) {
        if (allFatalGuardsReady || loader==null) return;
        int registered=0;
        try {
            Class<?> source=Class.forName(
                "pro.celikom.a1exitwitness.PrivatePushTargets",
                false, ExitCallsiteWitness.class.getClassLoader());
            Object targets=source.getDeclaredMethod(
                "getAllFatalGuardExactTargets").invoke(null);
            if (targets instanceof String[][]) {
                String[][] methods=(String[][])targets;
                for (int i=0;i<methods.length && i<8;i++) {
                    String[] row=methods[i];
                    if (row==null || row.length!=3 || row[0]==null
                        || row[1]==null || row[2]==null) continue;
                    final String caseLabel="CASE_"+i;
                    try {
                        Class<?> type=Class.forName(row[0],false,loader);
                        for (Method method:type.getDeclaredMethods()) {
                            if (!method.getName().equals(row[1])
                                || method.getReturnType()!=boolean.class
                                || !privateMethodParameterSignature(method).equals(row[2]))
                                continue;
                            method.setAccessible(true);
                            hook(method).setExceptionMode(
                                XposedInterface.ExceptionMode.PROTECTIVE)
                                .intercept(chain -> {
                                    int hit=allFatalGuardHitCount.incrementAndGet();
                                    if (hit<=64)
                                        emit("PUSH_ALL_FATAL_GUARD_VALUE",caseLabel,"ENTER");
                                    try {
                                        Object result=chain.proceed();
                                        if (hit<=64)
                                            emit("PUSH_ALL_FATAL_GUARD_VALUE",caseLabel,
                                                Boolean.TRUE.equals(result) ? "TRUE":"FALSE");
                                        return result;
                                    } catch (Throwable failure) {
                                        if (hit<=64)
                                            emit("PUSH_ALL_FATAL_GUARD_VALUE",caseLabel,"THROW");
                                        throw failure;
                                    }
                                });
                            registered++;
                        }
                    } catch (Throwable ignored) { }
                }
            }
        } catch (Throwable ignored) { }
        allFatalGuardsReady=registered>0;
        emit("PUSH_ALL_FATAL_GUARD_HOOK","PUSH_GUARD",
            registered>0 ? "REGISTERED":"NO_HOOK");
    }

    // Targeted read-only test: is the exact failing Push.a argument/receiver
    // missing a direct object reference? No field names, values or classes logged.
    private static String directReferenceReadiness(Object object) {
        if (object==null) return "OBJECT_NULL";
        int checked=0;
        try {
            for (Class<?> cls=object.getClass(),depthClass=cls; depthClass!=null
                    && depthClass!=Object.class && checked<=16;
                 depthClass=depthClass.getSuperclass()) {
                for (Field field:depthClass.getDeclaredFields()) {
                    if (java.lang.reflect.Modifier.isStatic(field.getModifiers())
                            || field.isSynthetic() || field.getType().isPrimitive())
                        continue;
                    if (++checked>16) return "OBJECT_TOO_MANY_FIELDS";
                    field.setAccessible(true);
                    if (field.get(object)==null) return "OBJECT_NULL_DEPENDENCY";
                }
            }
            return checked==0 ? "OBJECT_NO_REFERENCE_FIELDS" : "OBJECT_ALL_REFERENCES_SET";
        } catch (Throwable ignored) { return "OBJECT_FIELDS_UNREADABLE"; }
    }

    private static String exactReceiverFieldState(Object receiver, String[] ref) {
        if (receiver==null) return "FIELD_UNREADABLE";
        try {
            Class<?> owner=Class.forName(ref[0],false,receiver.getClass().getClassLoader());
            Field field=owner.getDeclaredField(ref[1]);
            if (java.lang.reflect.Modifier.isStatic(field.getModifiers())
                    || field.getType().isPrimitive()) return "FIELD_UNREADABLE";
            field.setAccessible(true);
            return field.get(receiver)==null ? "FIELD_NULL":"FIELD_SET";
        } catch (Throwable ignored) { return "FIELD_UNREADABLE"; }
    }

    private synchronized void installExactFatalObjectWitness(ClassLoader loader) {
        if (exactFatalObjectReady || loader==null) return;
        int registered=0;
        try {
            Class<?> source=Class.forName("pro.celikom.a1exitwitness.PrivatePushTargets",
                false,ExitCallsiteWitness.class.getClassLoader());
            Object target=source.getDeclaredMethod("getFatalExactObjectTargets").invoke(null);
            Object fieldRefs=source.getDeclaredMethod("getFatalReceiverFieldTargets").invoke(null);
            final String[][] directFields=fieldRefs instanceof String[][]
                ? (String[][])fieldRefs:new String[0][];
            if (target instanceof String[][]) {
                for (String[] row:(String[][])target) {
                    if (row==null || row.length!=3) continue;
                    try {
                        Class<?> cls=Class.forName(row[0],false,loader);
                        for (Method method:cls.getDeclaredMethods()) {
                            if (!method.getName().equals(row[1])
                                    || method.getParameterTypes().length!=1
                                    || !privateMethodParameterSignature(method).equals(row[2]))
                                continue;
                            method.setAccessible(true);
                            hook(method).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                                .intercept(chain -> {
                                    int hit=exactFatalObjectHits.incrementAndGet();
                                    if (hit<=8) {
                                        Object arg=chain.getArg(0);
                                        emit("PUSH_FATAL_OBJECT","ARG_ENTER",
                                             directReferenceReadiness(arg));
                                        emit("PUSH_FATAL_OBJECT","RECEIVER_ENTER",
                                             directReferenceReadiness(chain.getThisObject()));
                                        emit("PUSH_FATAL_OBJECT_LOADER","PUSH_ARG",
                                            arg==null ? "LOADER_UNKNOWN"
                                            : arg.getClass().getClassLoader()==cloneAppClassLoader
                                            ? "LOADER_MATCH":"LOADER_DIFFERENT");
                                        for (int i=0;i<directFields.length && i<8;i++)
                                            emit("PUSH_FATAL_READ_FIELD_ENTER","CASE_"+i,
                                                exactReceiverFieldState(chain.getThisObject(),
                                                    directFields[i]));
                                    }
                                    ExactPushFrame previous=scopedPushCall.get();
                                    ExactPushFrame frame=new ExactPushFrame();
                                    scopedPushCall.set(frame);
                                    try {
                                        Object result=chain.proceed();
                                        if (hit<=8) {
                                            emit("PUSH_FATAL_GUARD_RETURN","PUSH_ARG",
                                                 frameCategory(frame));
                                            emit("PUSH_FATAL_OBJECT_OUTCOME","PUSH_ARG","RETURN");
                                        }
                                        return result;
                                    } catch (Throwable failure) {
                                        if (hit<=8) {
                                            emit("PUSH_FATAL_GUARD_THROW","PUSH_ARG",
                                                 frameCategory(frame));
                                            emit("PUSH_FATAL_PROVIDER_LINK","PUSH_ARG",
                                                 frame.providerThrewAfterTrue
                                                     ? "SAME_CALL_PROVIDER_THROW"
                                                     : "NO_PROVIDER_THROW_OBSERVED");
                                            String constructorOrder=frame.constructed.get(failure);
                                            emit("PUSH_FATAL_CONSTRUCTOR_ORDER","PUSH_ARG",
                                                 constructorOrder!=null ? constructorOrder
                                                 : frame.constructed.isEmpty()
                                                 ? "CTOR_NOT_IN_SCOPE"
                                                 : "CTOR_OTHER_IDENTITY");
                                            emit("PUSH_FATAL_OBJECT","ARG_THROW",
                                                 directReferenceReadiness(chain.getArg(0)));
                                            emit("PUSH_FATAL_OBJECT","RECEIVER_THROW",
                                                 directReferenceReadiness(chain.getThisObject()));
                                            for (int i=0;i<directFields.length && i<8;i++)
                                                emit("PUSH_FATAL_READ_FIELD_THROW","CASE_"+i,
                                                    exactReceiverFieldState(chain.getThisObject(),
                                                        directFields[i]));
                                            emit("PUSH_FATAL_OBJECT_OUTCOME","PUSH_ARG",
                                                 "DIRECT_METRICA".equals(
                                                     throwableIdentityCategory(failure))
                                                     ? "DIRECT_METRICA":"OTHER_THROW");
                                        }
                                        throw failure;
                                    } finally {
                                        if (previous==null) scopedPushCall.remove();
                                        else scopedPushCall.set(previous);
                                    }
                                });
                            registered++;
                        }
                    } catch (Throwable ignored) { }
                }
            }
        } catch (Throwable ignored) { }
        exactFatalObjectReady=registered>0;
        emit("PUSH_FATAL_OBJECT_HOOK","PUSH_ARG",
             registered>0 ? "REGISTERED":"NO_HOOK");
    }

    // SDK internal markers might be renamed by R8; NO_HOOK is inconclusive.
    // Read-only hooks: only fixed enums, no internal object/config inspection.
    private synchronized void installMetricaStateProbe(ClassLoader loader) {
        if (metricaStateProbeReady || loader==null) return;
        int registered=0;
        try {
            Class<?> cls=Class.forName(
                "io.appmetrica.analytics.impl.AppMetricaFacade", false, loader);
            for (Method method : cls.getDeclaredMethods()) {
                if (!java.lang.reflect.Modifier.isStatic(method.getModifiers()) ||
                    method.getParameterTypes().length!=0) continue;
                final String label;
                switch (method.getName()) {
                    case "markActivated": label="STATE_MARK_ACTIVATED"; break;
                    case "markFullyInitialized": label="STATE_MARK_FULL"; break;
                    case "killInstance": label="STATE_KILL"; break;
                    case "isActivated": label="STATE_CHECK_ACTIVATED"; break;
                    case "isFullyInitialized": label="STATE_CHECK_FULL"; break;
                    case "isInitializedForApp": label="STATE_CHECK_APP"; break;
                    default: continue;
                }
                method.setAccessible(true);
                hook(method).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                    .intercept(chain -> {
                        if (stateHits.incrementAndGet()<=55)
                            emit("METRICA_STATE",label,"ENTER");
                        try {
                            Object result=chain.proceed();
                            if (stateHits.get()<=55)
                                emit("METRICA_STATE",label,
                                    result instanceof Boolean
                                        ? (Boolean.TRUE.equals(result)?"TRUE":"FALSE")
                                        : "RETURN");
                            return result;
                        } catch (Throwable failure) {
                            if (stateHits.get()<=55)
                                emit("METRICA_STATE",label,"THROW");
                            throw failure;
                        }
                    });
                registered++;
            }
        } catch (Throwable ignored) { }
        metricaStateProbeReady=registered>0;
        emit("METRICA_STATE_HOOK","METRICA_SDK",
            registered>0 ? "REGISTERED" : "NO_HOOK");
    }

    // Identify the public SDK call producing the failed initialization
    // without inspecting any method argument, return value or exception.
    private synchronized void installMetricaPublicProbe(ClassLoader loader) {
        if (metricaPublicProbeReady || loader==null) return;
        int registered=0;
        try {
            Class<?> cls=Class.forName("io.appmetrica.analytics.AppMetrica", false, loader);
            for (Method method : cls.getDeclaredMethods()) {
                if (!java.lang.reflect.Modifier.isStatic(method.getModifiers())) continue;
                final String label;
                switch (method.getName()) {
                    case "getReporter": label="API_GET_REPORTER"; break;
                    case "activateReporter": label="API_ACTIVATE_REPORTER"; break;
                    case "reportEvent": label="API_REPORT_EVENT"; break;
                    case "reportError": label="API_REPORT_ERROR"; break;
                    case "reportUnhandledException": label="API_REPORT_FATAL"; break;
                    case "enableActivityAutoTracking": label="API_ACTIVITY_TRACK"; break;
                    case "getDeviceId": label="API_DEVICE_ID"; break;
                    default: continue;
                }
                method.setAccessible(true);
                hook(method).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                    .intercept(chain -> {
                        if (publicHits.incrementAndGet()<=55)
                            emit("METRICA_API",label,"ENTER");
                        try {
                            Object result=chain.proceed();
                            // Only observe actual returned SDK reporter objects.
                            if ("API_GET_REPORTER".equals(label)) {
                                try { installReturnedReporterWitness(result); }
                                catch (Throwable ignored) { }
                            }
                            if (publicHits.get()<=55)
                                emit("METRICA_API",label,"RETURN");
                            return result;
                        } catch (Throwable failure) {
                            if (publicHits.get()<=55)
                                emit("METRICA_API",label,"THROW");
                            throw failure;
                        }
                    });
                registered++;
            }
        } catch (Throwable ignored) { }
        metricaPublicProbeReady=registered>0;
        emit("METRICA_API_HOOK","METRICA_SDK",
            registered>0 ? "REGISTERED" : "NO_HOOK");
    }


    // Reporter interface returns successfully, but the later Kotlin coroutine
    // may fail inside its implementation. Observe ONLY fixed method families
    // of the concrete returned reporter, without calling it or reading args.
    private void installReturnedReporterWitness(Object reporter) {
        if (reporter==null) return;
        Class<?> type=reporter.getClass();
        synchronized (reporterClasses) {
            if (!reporterClasses.add(type) || reporterClasses.size()>12) return;
        }
        int registered=0;
        for (Class<?> scan=type;scan!=null && scan!=Object.class;
                scan=scan.getSuperclass()) {
            for (Method method : scan.getDeclaredMethods()) {
                if (java.lang.reflect.Modifier.isAbstract(method.getModifiers()) ||
                    java.lang.reflect.Modifier.isStatic(method.getModifiers())) continue;
                final String kind;
                switch (method.getName()) {
                    case "reportEvent": kind="REPORTER_EVENT"; break;
                    case "reportError": kind="REPORTER_ERROR"; break;
                    case "reportUnhandledException": kind="REPORTER_FATAL"; break;
                    case "resumeSession":
                    case "pauseSession": kind="REPORTER_SESSION"; break;
                    case "reportRevenue":
                    case "reportECommerce": kind="REPORTER_REVENUE"; break;
                    case "setDataSendingEnabled": kind="REPORTER_DATA"; break;
                    default: continue;
                }
                try {
                    method.setAccessible(true);
                    hook(method).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                        .intercept(chain -> {
                            if (reporterHitCount.incrementAndGet()<=32)
                                emit("REPORTER_CALL",kind,"ENTER");
                            try {
                                Object result=chain.proceed();
                                if (reporterHitCount.get()<=32)
                                    emit("REPORTER_CALL",kind,"RETURN");
                                return result;
                            } catch (Throwable failure) {
                                if (reporterHitCount.get()<=32)
                                    emit("REPORTER_CALL",kind,"THROW");
                                throw failure;
                            }
                        });
                    registered++;
                } catch (Throwable ignored) { }
            }
        }
        emit("REPORTER_HOOK","METRICA_SDK",
            registered>0 ? "REGISTERED" : "NO_HOOK");
    }

    // Android callback observation ONLY. Calls original implementation once.
    private boolean observeApplicationOnCreate() {
        try {
            Method method=android.app.Instrumentation.class.getDeclaredMethod(
                "callApplicationOnCreate", Application.class);
            method.setAccessible(true);
            hook(method).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                .intercept(chain -> {
                    try {
                        Object candidate = chain.getArg(0);
                        if (candidate instanceof Application) {
                            if (isPassportProcess())
                                preparePassportDiagnostics((Application) candidate);
                            else
                                prepareOwnerDiagnostics((Application) candidate);
                        }
                    } catch (Throwable ignored) { }
                    // Diagnostics Context now exists in this process. Make
                    // hook-registration status observable and retry if
                    // package initialization happened before process naming.
                    try { installCloneAccountTypeBridge(); }
                    catch (Throwable ignored) { }
                    appOnCreateEntered=true;
                    emit("APP_LIFECYCLE","APPLICATION","ENTER");
                    try {
                        Object result=chain.proceed();
                        appOnCreateReturned=true;
                        emit("APP_LIFECYCLE","APPLICATION","RETURN");
                        return result;
                    } catch (Throwable failure) {
                        emit("APP_LIFECYCLE","APPLICATION","THROW");
                        throw failure;
                    }
                });
            return true;
        } catch (Throwable ignored) {
            emit("APP_LIFECYCLE","APPLICATION","NO_HOOK");
            return false;
        }
    }

    private boolean prefixHookInstalled;


    // Read-only provider metadata and actual SDK URI access. Never query any
    // provider ourselves, inspect cursor data, print authorities, or alter args.
    private static String privateProviderOwner(ProviderInfo provider) {
        if (provider == null) return "ABSENT";
        return PACKAGE.equals(provider.packageName) ? "CLONE_OWNER"
            : "ru.yandex.music".equals(provider.packageName) ? "STOCK_OWNER"
            : "OTHER_OWNER";
    }

    private static String privateAuthorityFamily(Uri uri) {
        if (uri == null) return "UNKNOWN_AUTH";
        String name;
        try { name=uri.getAuthority(); }
        catch (Throwable ignored) { return "UNKNOWN_AUTH"; }
        if (STOCK_AUTHORITY.equals(name)) return "STOCK_AUTH";
        if (CLONE_AUTHORITY.equals(name)) return "CLONE_AUTH";
        return "OTHER_AUTH";
    }

    private static boolean privateMetricaSdkCaller() {
        try {
            for (StackTraceElement frame : Thread.currentThread().getStackTrace()) {
                String name=frame.getClassName();
                if (name.startsWith("io.appmetrica.analytics.")
                        || name.startsWith("com.yandex.metrica."))
                    return true;
            }
        } catch (Throwable ignored) { }
        return false;
    }

    private void observeProviderRegistration(Context context) {
        try {
            ProviderInfo stock=context.getPackageManager()
                .resolveContentProvider(STOCK_AUTHORITY,0);
            emit("METRICA_PROVIDER_RESOLVE","STOCK_AUTH",
                privateProviderOwner(stock));
        } catch (Throwable ignored) {
            emit("METRICA_PROVIDER_RESOLVE","STOCK_AUTH","PROBE_ERROR");
        }
        try {
            ProviderInfo clone=context.getPackageManager()
                .resolveContentProvider(CLONE_AUTHORITY,0);
            emit("METRICA_PROVIDER_RESOLVE","CLONE_AUTH",
                privateProviderOwner(clone));
        } catch (Throwable ignored) {
            emit("METRICA_PROVIDER_RESOLVE","CLONE_AUTH","PROBE_ERROR");
        }
    }

    private synchronized void installPrivateMetricaProviderQueryWitness() {
        if (metricaProviderQueryHookReady) return;
        int registered=0;
        try {
            for (Method method : ContentResolver.class.getDeclaredMethods()) {
                if (!"query".equals(method.getName())) continue;
                Class<?>[] params=method.getParameterTypes();
                if (params.length<1 || params[0]!=Uri.class) continue;
                method.setAccessible(true);
                hook(method).setExceptionMode(
                    XposedInterface.ExceptionMode.PROTECTIVE)
                    .intercept(chain -> {
                        boolean sdk=privateMetricaSdkCaller();
                        int hit=sdk ? metricaProviderQueryHits.incrementAndGet() : 1000;
                        String family="UNKNOWN_AUTH";
                        if (sdk && hit<=32) {
                            try {
                                Object arg=chain.getArg(0);
                                if (arg instanceof Uri)
                                    family=privateAuthorityFamily((Uri)arg);
                            } catch (Throwable ignored) { }
                            emit("METRICA_PROVIDER_QUERY",family,"ENTER");
                        }
                        try {
                            Object result=chain.proceed();
                            if (sdk && hit<=32)
                                emit("METRICA_PROVIDER_QUERY",family,
                                    result == null ? "NULL_RESULT":"NONNULL_RESULT");
                            return result;
                        } catch (Throwable error) {
                            if (sdk && hit<=32)
                                emit("METRICA_PROVIDER_QUERY",family,"THROW");
                            throw error;
                        }
                    });
                registered++;
            }
        } catch (Throwable ignored) { }
        metricaProviderQueryHookReady=registered>0;
        emit("METRICA_PROVIDER_QUERY_HOOK","METRICA_SDK",
            registered>0 ? "REGISTERED":"NO_HOOK");
    }


    // Observe only target package identity on SDK service operations in
    // the disposable clone MAIN. Intent extras, actions and component
    // names, device/account data, and exceptions are never logged.
    private static String privateServiceIntentFamily(Intent intent) {
        if (intent==null) return "UNKNOWN_TARGET";
        try {
            ComponentName target=intent.getComponent();
            String destination=target!=null ? target.getPackageName()
                : intent.getPackage();
            if (destination==null || destination.isEmpty())
                return "IMPLICIT_TARGET";
            if (PACKAGE.equals(destination)) return "CLONE_TARGET";
            if ("ru.yandex.music".equals(destination)) return "STOCK_TARGET";
        } catch (Throwable ignored) { return "UNKNOWN_TARGET"; }
        return "OTHER_TARGET";
    }

    private synchronized void installPrivateMetricaServiceWitness() {
        if (metricaServiceHookReady) return;
        int installed=0;
        try {
            Class<?> impl=Class.forName("android.app.ContextImpl");
            for (Method method:impl.getDeclaredMethods()) {
                String name=method.getName();
                if (!"startService".equals(name)
                        && !"startForegroundService".equals(name)
                        && !"bindService".equals(name)
                        && !"bindServiceCommon".equals(name))
                    continue;
                Class<?>[] params=method.getParameterTypes();
                if (params.length==0 || params[0]!=Intent.class) continue;
                method.setAccessible(true);
                hook(method).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                    .intercept(chain -> {
                        boolean sdk=privateMetricaSdkCaller();
                        int hit=sdk ? metricaServiceHitCount.incrementAndGet() : 1000;
                        String family="UNKNOWN_TARGET";
                        if (sdk && hit<=48) {
                            try {
                                Object arg=chain.getArg(0);
                                if (arg instanceof Intent)
                                    family=privateServiceIntentFamily((Intent)arg);
                            } catch (Throwable ignored) { }
                            emit("METRICA_SERVICE_CALL",family,"ENTER");
                        }
                        try {
                            Object value=chain.proceed();
                            if (sdk && hit<=48)
                                emit("METRICA_SERVICE_CALL",family,
                                    value==null ? "NULL_RESULT"
                                    : Boolean.FALSE.equals(value)
                                        ? "FALSE_RESULT":"SUCCESS_RESULT");
                            return value;
                        } catch (Throwable failure) {
                            if (sdk && hit<=48)
                                emit("METRICA_SERVICE_CALL",family,"THROW");
                            throw failure;
                        }
                    });
                installed++;
            }
        } catch (Throwable ignored) { }
        metricaServiceHookReady=installed>0;
        emit("METRICA_SERVICE_HOOK","METRICA_SDK",
            installed>0 ? "REGISTERED":"NO_HOOK");
    }

    /**
     * Single exactly resolved Firebase provider implementation call on the TRUE-normal,
     * catch-covered Push.a route.
     * Read-only source-grounded probe: original method runs exactly once.
     * No app/SDK values, config, exceptions, args or results ever changed.
     */
    // Read an existing Throwable message inside the observed exact provider
    // catch; emit only fixed categories. Never log keys, identifiers or text.
    private static String exactProviderFailureReason(Throwable failure) {
        try {
            String message=failure.getMessage();
            if (message==null) return "PROVIDER_MESSAGE_ABSENT";
            String s=message.toLowerCase(java.util.Locale.ROOT);
            if (s.contains("ymp_firebase_default_app_id") ||
                    s.contains("ymp_gcm_default_sender_id"))
                return "PROVIDER_DEFAULT_META_PAIR";
            if (s.contains("ymp_firebase_app_id") ||
                    s.contains("ymp_gcm_sender_id"))
                return "PROVIDER_CUSTOM_META_PAIR";
            if (s.contains("google_app_id") ||
                    s.contains("gcm_defaultsenderid"))
                return "PROVIDER_GOOGLE_RESOURCE_PAIR";
            if (s.contains("expected two identifiers"))
                return "PROVIDER_IDENTIFIERS_GENERIC";
            if (s.contains("push sdk") && s.contains("not activated correctly"))
                return "PROVIDER_NO_VALID_CONTROLLER";
            if (s.contains("firebase") &&
                    (s.contains("missing") || s.contains("invalid") ||
                     s.contains("not initialized") || s.contains("not configured")))
                return "PROVIDER_FIREBASE_OTHER";
            return "PROVIDER_REASON_OTHER";
        } catch (Throwable ignored) {
            return "PROVIDER_REASON_UNKNOWN";
        }
    }

    // The already failing provider is observed in a disposable clone only.
    // Presence categories are finite, no Firebase identifiers/values exported.
    private static boolean exactIdentifierPresent(Context context,Object raw) {
        try {
            if (raw instanceof String)
                return !((String)raw).trim().isEmpty();
            if (raw instanceof Integer) {
                int id=((Integer)raw).intValue();
                if (id<=0) return false;
                String resolved=context.getResources().getString(id);
                return resolved!=null && !resolved.trim().isEmpty();
            }
        } catch (Throwable ignored) { }
        return false;
    }

    private static String exactPairCategory(boolean app,boolean sender) {
        if (app && sender) return "PAIR_BOTH";
        if (app) return "PAIR_APP_ONLY";
        if (sender) return "PAIR_SENDER_ONLY";
        return "PAIR_NONE";
    }


    // LSPatch v1.2 creates a second LoadedApk from the cached intact origin.
    // Read ONLY the existing Application.attach ContextImpl.mPackageInfo.mResDir;
    // compare it privately against the installed outer own APK and the
    // existing LSPatch private cache. Never emit paths or resource values.

    // CI-only own-loader resource experiment. The original LSPatch inner
    // sourceDir, original code, nested signed origin and all SDK return values
    // remain untouched. Select the own outer signed resource APK only before
    // the target LoadedApk constructs its first Resources object.
    private synchronized void installOwnedResourceRouteTrial() {
        if (ownRouteHooked || !BuildConfig.OWN_RESOURCE_ROUTE_TRIAL) return;
        try {
            Class<?> loadedClass=Class.forName("android.app.LoadedApk");
            Method getResources=loadedClass.getDeclaredMethod("getResources");
            getResources.setAccessible(true);
            hook(getResources).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                .intercept(chain -> {
                    Object receiver=chain.getThisObject();
                    if (receiver==null) return chain.proceed();
                    try {
                        Field appInfoField=loadedClass.getDeclaredField("mApplicationInfo");
                        appInfoField.setAccessible(true);
                        Object rawInfo=appInfoField.get(receiver);
                        if (!(rawInfo instanceof android.content.pm.ApplicationInfo))
                            return chain.proceed();
                        android.content.pm.ApplicationInfo runtime=
                            (android.content.pm.ApplicationInfo)rawInfo;
                        if (!PACKAGE.equals(runtime.packageName)
                                || runtime.uid!=android.os.Process.myUid())
                            return chain.proceed();
                        String category="GUARD_REJECTED";
                        try {
                            Field resField=loadedClass.getDeclaredField("mResDir");
                            Field codeField=loadedClass.getDeclaredField("mAppDir");
                            Field cachedField=loadedClass.getDeclaredField("mResources");
                            resField.setAccessible(true);
                            codeField.setAccessible(true);
                            cachedField.setAccessible(true);
                            Object resDir=resField.get(receiver);
                            Object codeDir=codeField.get(receiver);
                            if (cachedField.get(receiver)!=null) {
                                category="LATE_ALREADY_CACHED";
                            } else if (resDir instanceof String
                                    && codeDir instanceof String
                                    && runtime.sourceDir!=null
                                    && runtime.dataDir!=null
                                    && resDir.equals(runtime.sourceDir)
                                    && codeDir.equals(runtime.sourceDir)
                                    && new java.io.File(runtime.sourceDir)
                                        .getCanonicalFile().toPath()
                                        .startsWith(new java.io.File(runtime.dataDir,
                                            "cache/lspatch/origin").getCanonicalFile().toPath())) {
                                Class<?> threadClass=Class.forName("android.app.ActivityThread");
                                Method current=threadClass.getDeclaredMethod("currentActivityThread");
                                current.setAccessible(true);
                                Object activityThread=current.invoke(null);
                                Method systemContext=threadClass.getDeclaredMethod("getSystemContext");
                                systemContext.setAccessible(true);
                                Object system=systemContext.invoke(activityThread);
                                if (system instanceof Context) {
                                    android.content.pm.ApplicationInfo installed=
                                        ((Context)system).getPackageManager()
                                        .getApplicationInfo(PACKAGE,0);
                                    if (installed!=null
                                            && PACKAGE.equals(installed.packageName)
                                            && installed.uid==runtime.uid
                                            && installed.sourceDir!=null
                                            && !installed.sourceDir.equals(runtime.sourceDir)
                                            && new java.io.File(installed.sourceDir).isFile()
                                            && installed.sourceDir.endsWith(".apk")) {
                                        // Preserve mAppDir and all code/classloader paths.
                                        resField.set(receiver,installed.sourceDir);
                                        category="APPLIED";
                                    }
                                }
                            }
                        } catch (Throwable ignored) { }
                        if (ownRouteEvents.incrementAndGet()<=8)
                            emit("OWN_RES_ROUTE","CLONE",category);
                    } catch (Throwable ignored) { }
                    // Always call the unmodified framework implementation.
                    return chain.proceed();
                });
            ownRouteHooked=true;
            emit("OWN_RES_ROUTE","CLONE","HOOKED");
        } catch (Throwable ignored) {
            emit("OWN_RES_ROUTE","CLONE","HOOK_UNAVAILABLE");
        }
    }

    private void observeActualLoadedApkResourceOrigin() {
        String category="UNKNOWN_PATH";
        try {
            Context c=exactCloneRuntimeContext;
            if (c!=null && PACKAGE.equals(c.getPackageName())) {
                android.content.pm.ApplicationInfo runtime=c.getApplicationInfo();
                android.content.pm.ApplicationInfo installed=
                    c.getPackageManager().getApplicationInfo(PACKAGE,0);
                Class<?> type=c.getClass();
                Field loadedField=null;
                while (type!=null && loadedField==null) {
                    try { loadedField=type.getDeclaredField("mPackageInfo"); }
                    catch (NoSuchFieldException ignored) { type=type.getSuperclass(); }
                }
                if (loadedField!=null && installed!=null && runtime!=null) {
                    loadedField.setAccessible(true);
                    Object loaded=loadedField.get(c);
                    if (loaded!=null) {
                        Field resField=loaded.getClass().getDeclaredField("mResDir");
                        resField.setAccessible(true);
                        Object value=resField.get(loaded);
                        if (value instanceof String && !((String)value).isEmpty()) {
                            String dir=(String)value;
                            // Independent PackageManager points to the owned outer
                            // installation. A runtime INNER_CACHE verdict also
                            // requires an exact match to the app's active code
                            // source and a location inside this clone's own cache.
                            if (installed.sourceDir!=null
                                    && dir.equals(installed.sourceDir)) {
                                category="OUTER_OWN";
                            } else if (runtime.sourceDir!=null
                                    && runtime.dataDir!=null
                                    && dir.equals(runtime.sourceDir)
                                    && !dir.equals(installed.sourceDir)
                                    && new java.io.File(dir).getCanonicalFile().toPath()
                                        .startsWith(new java.io.File(runtime.dataDir,
                                            "cache/lspatch/origin").getCanonicalFile().toPath())) {
                                category="INNER_CACHE";
                            } else {
                                category="OTHER_PATH";
                            }
                        }
                    }
                }
            }
        } catch (Throwable ignored) { }
        emit("LOADEDAPK_RESDIR","CLONE",category);
    }

    private void observeExactProviderFirebasePresence() {
        observeActualLoadedApkResourceOrigin();
        Context c=exactCloneRuntimeContext;
        if (c==null) {
            emit("PUSH_PROVIDER_CONFIG_CUSTOM","PUSH_PROVIDER","PAIR_UNKNOWN");
            emit("PUSH_PROVIDER_CONFIG_DEFAULT","PUSH_PROVIDER","PAIR_UNKNOWN");
            emit("PUSH_PROVIDER_CONFIG_RESOURCE","PUSH_PROVIDER","PAIR_UNKNOWN");
            emit("PUSH_PROVIDER_CONFIG_CLONE_ID","PUSH_PROVIDER","PAIR_UNKNOWN");
            emit("PUSH_PROVIDER_CONFIG_STOCK_ID","PUSH_PROVIDER","PAIR_UNKNOWN");
            emit("PUSH_PROVIDER_CONFIG_STOCK_VALUE","PUSH_PROVIDER","PAIR_UNKNOWN");
            return;
        }
        try {
            android.content.pm.ApplicationInfo info=c.getPackageManager()
                .getApplicationInfo(c.getPackageName(),
                    android.content.pm.PackageManager.GET_META_DATA);
            android.os.Bundle m=info==null ? null : info.metaData;
            emit("PUSH_PROVIDER_CONFIG_CUSTOM","PUSH_PROVIDER",
                exactPairCategory(
                    m!=null && exactIdentifierPresent(c,m.get("ymp_firebase_app_id")),
                    m!=null && exactIdentifierPresent(c,m.get("ymp_gcm_sender_id"))));
            emit("PUSH_PROVIDER_CONFIG_DEFAULT","PUSH_PROVIDER",
                exactPairCategory(
                    m!=null && exactIdentifierPresent(c,m.get("ymp_firebase_default_app_id")),
                    m!=null && exactIdentifierPresent(c,m.get("ymp_gcm_default_sender_id"))));
        } catch (Throwable ignored) {
            emit("PUSH_PROVIDER_CONFIG_CUSTOM","PUSH_PROVIDER","PAIR_UNKNOWN");
            emit("PUSH_PROVIDER_CONFIG_DEFAULT","PUSH_PROVIDER","PAIR_UNKNOWN");
        }
        try {
            android.content.res.Resources res=c.getResources();
            String pkg=c.getPackageName();
            int app=res.getIdentifier("google_app_id","string",pkg);
            int sender=res.getIdentifier("gcm_defaultSenderId","string",pkg);
            emit("PUSH_PROVIDER_CONFIG_CLONE_ID","PUSH_PROVIDER",exactPairCategory(app>0,sender>0));
            int stockApp=res.getIdentifier("google_app_id","string","ru.yandex.music");
            int stockSender=res.getIdentifier("gcm_defaultSenderId","string","ru.yandex.music");
            emit("PUSH_PROVIDER_CONFIG_STOCK_ID","PUSH_PROVIDER",exactPairCategory(stockApp>0,stockSender>0));
            emit("PUSH_PROVIDER_CONFIG_STOCK_VALUE","PUSH_PROVIDER",
                exactPairCategory(
                    stockApp>0 && exactIdentifierPresent(c,Integer.valueOf(stockApp)),
                    stockSender>0 && exactIdentifierPresent(c,Integer.valueOf(stockSender))));
            emit("PUSH_PROVIDER_CONFIG_RESOURCE","PUSH_PROVIDER",
                exactPairCategory(
                    app>0 && exactIdentifierPresent(c,Integer.valueOf(app)),
                    sender>0 && exactIdentifierPresent(c,Integer.valueOf(sender))));
        } catch (Throwable ignored) {
            emit("PUSH_PROVIDER_CONFIG_RESOURCE","PUSH_PROVIDER","PAIR_UNKNOWN");
            emit("PUSH_PROVIDER_CONFIG_CLONE_ID","PUSH_PROVIDER","PAIR_UNKNOWN");
            emit("PUSH_PROVIDER_CONFIG_STOCK_ID","PUSH_PROVIDER","PAIR_UNKNOWN");
            emit("PUSH_PROVIDER_CONFIG_STOCK_VALUE","PUSH_PROVIDER","PAIR_UNKNOWN");
        }
    }

    private synchronized void installExactPostTruePushProvider(ClassLoader loader) {
        if (exactPushProviderReady || loader == null) return;
        try {
            Class<?> privateClass=Class.forName(
                "pro.celikom.a1exitwitness.PrivatePostTrueProviderTarget",false,
                ExitCallsiteWitness.class.getClassLoader());
            Object privateRow=privateClass.getDeclaredMethod("exact").invoke(null);
            if (!(privateRow instanceof String[])) {
                emit("PUSH_PROVIDER_HOOK","PUSH_PROVIDER","NO_HOOK");
                return;
            }
            String[] target=(String[])privateRow;
            if (target.length!=2 ||
                !"getPushServiceController".equals(target[1])) {
                emit("PUSH_PROVIDER_HOOK","PUSH_PROVIDER","NO_HOOK");
                return;
            }
            Class<?> provider=Class.forName(target[0],false,loader);
            Method exact=null;
            for (Method m:provider.getDeclaredMethods()) {
                if (!"getPushServiceController".equals(m.getName()) ||
                        m.getParameterCount()!=0) continue;
                if (exact!=null) {
                    emit("PUSH_PROVIDER_HOOK","PUSH_PROVIDER","NO_HOOK");
                    return; // cannot pick a fuzzy overload
                }
                exact=m;
            }
            if (exact==null) {
                emit("PUSH_PROVIDER_HOOK","PUSH_PROVIDER","NO_HOOK");
                return;
            }
            exact.setAccessible(true);
            hook(exact).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                .intercept(chain -> {
                    int hit=exactPushProviderHits.incrementAndGet();
                    if (hit<=12) {
                        ExactPushFrame f=scopedPushCall.get();
                        emit("PUSH_PROVIDER_PHASE","PUSH_PROVIDER",
                            f==null ? "OUTSIDE_FATAL_CALL" :
                              f.yes>0 ? "AFTER_TRUE" : "BEFORE_TRUE");
                        emit("PUSH_PROVIDER_CALL","PUSH_PROVIDER","ENTER");
                    }
                    try {
                        Object result=chain.proceed();
                        if (hit<=12) {
                            emit("PUSH_PROVIDER_CALL","PUSH_PROVIDER","RETURN");
                            // Read-only: verify the *successful* provider's
                            // resource namespace. Previously only failures
                            // emitted lookup/path categories.
                            observeExactProviderFirebasePresence();
                        }
                        return result;
                    } catch (Throwable failure) {
                        ExactPushFrame frame=scopedPushCall.get();
                        if (frame!=null && frame.yes>0)
                            frame.providerThrewAfterTrue=true;
                        if (hit<=12) {
                            emit("PUSH_PROVIDER_CALL","PUSH_PROVIDER","THROW");
                            emit("PUSH_PROVIDER_ERROR","PUSH_PROVIDER",
                                failure instanceof IllegalStateException ?
                                    "ILLEGAL_STATE" :
                                failure instanceof SecurityException ?
                                    "SECURITY" : "OTHER_THROWABLE");
                            emit("PUSH_PROVIDER_REASON","PUSH_PROVIDER",
                                 exactProviderFailureReason(failure));
                            if (failure instanceof IllegalStateException)
                                observeExactProviderFirebasePresence();
                        }
                        throw failure;
                    }
                });
            exactPushProviderReady=true;
            emit("PUSH_PROVIDER_HOOK","PUSH_PROVIDER","REGISTERED");
        } catch (Throwable ignored) {
            emit("PUSH_PROVIDER_HOOK","PUSH_PROVIDER","NO_HOOK");
        }
    }

    private boolean hookApplicationAttach() {
        try {
            Method attach = Application.class.getDeclaredMethod("attach", Context.class);
            attach.setAccessible(true);
            hook(attach).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                .intercept(chain -> {
                    // The app may create Account objects in attachBaseContext.
                    // Install our scoped type mapping before that code runs.
                    try { installCloneAccountTypeBridge(); }
                    catch (Throwable ignored) { }
                    Object result = chain.proceed();
                    try { installCloneAccountTypeBridge(); }
                    catch (Throwable ignored) { }
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
                                cloneAppClassLoader = loader;
                                exactCloneRuntimeContext = caller;
                                observeProviderRegistration(caller);
                                installPrivateMetricaProviderQueryWitness();
                                installPrivateMetricaServiceWitness();
                                installExactPrefixWitness(loader);
                                installExactRunModeWitness(loader);
                                installMetricaActivationWitness(loader);
                                installModulesActivationObserver(loader);
                                installPushActivationObserver(loader);
                                installPrivatePushBoolWitness(loader);
                                installPrivatePushSiteWitness(loader);
                                installAllFatalGuardWitness(loader);
                                installExactFatalObjectWitness(loader);
                                installExactPostTruePushProvider(loader);
                                installPrivateMediaDataReadWitness(loader);
                                installMetricaStateProbe(loader);
                                installMetricaPublicProbe(loader);
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


    // Only the two exact, issuer-verified 2025 implementations are selected
    // by ephemeral CI. This is a read-only observation of readAt() calls.
    // No buffers, offsets, filenames, URLs, ids or byte payloads are read.
    private synchronized void installPrivateMediaDataReadWitness(ClassLoader appLoader) {
        if (mediaDataReadWitnessReady || appLoader==null
                || !PACKAGE.equals(Application.getProcessName())) return;
        int hooked=0;
        try {
            Class<?> own=Class.forName(
                "pro.celikom.a1exitwitness.PrivateMediaDataSourceTargets",
                false,ExitCallsiteWitness.class.getClassLoader());
            Method selector=own.getDeclaredMethod("classes");
            selector.setAccessible(true);
            Object raw=selector.invoke(null);
            if (!(raw instanceof String[])) {
                emit("MEDIA_DS_HOOK","MEDIA_DATA_SOURCE","NO_HOOK");
                return;
            }
            String[] candidates=(String[])raw;
            if (candidates.length!=2 || candidates[0].equals(candidates[1])) {
                emit("MEDIA_DS_HOOK","MEDIA_DATA_SOURCE","NO_HOOK");
                return;
            }
            for (int i=0;i<candidates.length;i++) {
                String className=candidates[i];
                // Candidate index is stable: exact sorted signed-2025 class table.
                // Never emit the real class name, object identity, or media data.
                final String privateReaderKind=i==0 ? "CANDIDATE_0":"CANDIDATE_1";
                if (!className.matches("[A-Za-z0-9_$.]{2,180}")) break;
                Class<?> impl=Class.forName(className,false,appLoader);
                if (!android.media.MediaDataSource.class.isAssignableFrom(impl)) break;
                Method exact=impl.getDeclaredMethod("readAt",
                    long.class,byte[].class,int.class,int.class);
                exact.setAccessible(true);
                hook(exact).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                    .intercept(chain -> {
                        int count=mediaDataReadCalls.incrementAndGet();
                        // Diagnostic code is isolated from the vendor call:
                        // no observer exception may change playback behaviour.
                        try {
                            if (count<=12) {
                                emit("MEDIA_DS_SOURCE","MEDIA_DATA_SOURCE",privateReaderKind);
                                emit("MEDIA_DS_READ","MEDIA_DATA_SOURCE","ENTER");
                            }
                            if (readerWasPassedToExtractor(chain.getThisObject())
                                    && mediaReaderIdentityMatches.incrementAndGet()<=8)
                                emit("MEDIA_DS_EXTRACTOR_LINK","MEDIA_DATA_SOURCE",privateReaderKind);
                        } catch (Throwable ignored) { }
                        Object result;
                        try {
                            // Exactly one unmodified original call.
                            result=chain.proceed();
                        } catch (Throwable failure) {
                            try {
                                if (count<=12)
                                    emit("MEDIA_DS_READ","MEDIA_DATA_SOURCE","THROW");
                            } catch (Throwable ignored) { }
                            throw failure;
                        }
                        try {
                            if (count<=12)
                                emit("MEDIA_DS_READ","MEDIA_DATA_SOURCE","RETURN");
                        } catch (Throwable ignored) { }
                        return result;
                    });
                hooked++;
            }
            if (hooked==2) installExactMediaExtractorSourceWitness(candidates);
        } catch (Throwable ignored) { }
        mediaDataReadWitnessReady=hooked==2;
        emit("MEDIA_DS_HOOK","MEDIA_DATA_SOURCE",
             hooked==2 ? "TWO_REGISTERED" : "NO_HOOK");
    }

    /**
     * The signed 2025 DEX has exactly one direct invocation of Android's
     * MediaExtractor.setDataSource(MediaDataSource). Observe the *object*
     * supplied to that framework method, not its contents. A registered
     * observer or a method entry is NOT proof of music playback.
     */
    private synchronized void installExactMediaExtractorSourceWitness(String[] candidates) {
        if (mediaExtractorSourceHookReady
                || !PACKAGE.equals(Application.getProcessName())) return;
        boolean registered=false;
        try {
            if (candidates==null || candidates.length!=2
                    || candidates[0].equals(candidates[1])) {
                emit("MEDIA_EXTRACTOR_HOOK","MEDIA_EXTRACTOR","NO_HOOK");
                return;
            }
            final String[] expectedClasses=candidates.clone(); // private, never logged
            Method method=android.media.MediaExtractor.class.getDeclaredMethod(
                "setDataSource",android.media.MediaDataSource.class);
            hook(method).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                .intercept(chain -> {
                    int count=mediaExtractorSourceCalls.incrementAndGet();
                    try {
                        Object source=chain.getArg(0);
                        String category="OTHER_SOURCE";
                        if (source==null) category="NULL_SOURCE";
                        else if (expectedClasses[0].equals(source.getClass().getName()))
                            category="CANDIDATE_0";
                        else if (expectedClasses[1].equals(source.getClass().getName()))
                            category="CANDIDATE_1";
                        if ("CANDIDATE_0".equals(category) || "CANDIDATE_1".equals(category))
                            rememberMediaExtractorSource(source);
                        if (count<=8) {
                            emit("MEDIA_EXTRACTOR_SOURCE","MEDIA_EXTRACTOR",category);
                            emit("MEDIA_EXTRACTOR_CALL","MEDIA_EXTRACTOR","ENTER");
                        }
                    } catch (Throwable ignored) { }
                    Object result;
                    try {
                        result=chain.proceed(); // exactly one unmodified original call
                    } catch (Throwable problem) {
                        try {
                            if (count<=8)
                                emit("MEDIA_EXTRACTOR_CALL","MEDIA_EXTRACTOR","THROW");
                        } catch (Throwable ignored) { }
                        throw problem;
                    }
                    try {
                        if (count<=8)
                            emit("MEDIA_EXTRACTOR_CALL","MEDIA_EXTRACTOR","RETURN");
                    } catch (Throwable ignored) { }
                    return result;
                });
            registered=true;
        } catch (Throwable ignored) { }
        mediaExtractorSourceHookReady=registered;
        emit("MEDIA_EXTRACTOR_HOOK","MEDIA_EXTRACTOR",
            registered ? "REGISTERED":"NO_HOOK");
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

    /**
     * Owner-phone diagnostic export. Events are finite enums and are stored
     * only inside the disposable clone's private files directory. The button
     * is an ordinary in-window view: no overlay permission or storage
     * permission is requested. The report is copied to MediaStore Downloads
     * only after the owner taps the button.
     */

    /** Exact 2025.10.4 real vendor master-token decoder outcome only.
     * Never call a decoder ourselves; the real invocation must occur naturally.
     * Reading just the exception field never reads ciphertext or plaintext.
     */

    /**
     * Exact publisher 2025.10.4 method-order repair for the independent clone
     * signer: its master token must use the private yandex_am_storage key.
     * Bring the vendor's OWN normal key initialization into clone MAIN before
     * :passport starts, only on a fresh (no own account, no key) installation.
     *
     * This neither reads/writes auth values nor manufactures login success.
     * Existing account/key states are strictly left untouched. SDK only.
     */
    private synchronized void preinitializeOriginalMasterKeyIfFresh(Application app) {
        if (masterKeyPreinitAttempted || app == null
                || !PACKAGE.equals(Application.getProcessName())
                || !PACKAGE.equals(app.getPackageName())) return;
        masterKeyPreinitAttempted = true;
        try {
            android.content.SharedPreferences prefs = app.getSharedPreferences(
                "yandex_am_storage", Context.MODE_PRIVATE);
            if (prefs.contains("master_token_key")) {
                emit("MASTER_KEY_PREINIT", "MAIN", "EXISTING_UNCHANGED");
                return;
            }
            Account[] ownAccounts = AccountManager.get(app).getAccountsByType(OWN_ACCOUNT_TYPE);
            if (ownAccounts == null) {
                emit("MASTER_KEY_PREINIT", "MAIN", "ACCOUNT_QUERY_UNAVAILABLE");
                return;
            }
            if (ownAccounts.length != 0) {
                // NEVER rotate the encryption key of an existing real account.
                emit("MASTER_KEY_PREINIT", "MAIN", "ACCOUNT_EXISTS_NO_KEY_UNCHANGED");
                return;
            }
            ClassLoader loader = app.getClass().getClassLoader();
            if (loader == null) loader = app.getClassLoader();
            if (loader == null) {
                emit("MASTER_KEY_PREINIT", "MAIN", "NO_LOADER");
                return;
            }
            Class<?> storeClass = Class.forName(
                "com.yandex.passport.internal.storage.a", false, loader);
            Class<?> cipherClass = Class.forName(
                "com.yandex.passport.internal.core.accounts.v", false, loader);
            Constructor<?> storageCtor = storeClass.getDeclaredConstructor(Context.class);
            storageCtor.setAccessible(true);
            Constructor<?> cryptoCtor = cipherClass.getDeclaredConstructor(
                Context.class, storeClass);
            cryptoCtor.setAccessible(true);
            Method originalKeyMethod = cipherClass.getDeclaredMethod("try");
            originalKeyMethod.setAccessible(true);
            Object originalStorage = storageCtor.newInstance(app);
            Object originalCipher = cryptoCtor.newInstance(app, originalStorage);
            // The issuer's real private method generates/persists its key as-is.
            // Its returned key object is not retained or inspected.
            originalKeyMethod.invoke(originalCipher);
            if (!prefs.contains("master_token_key")) {
                emit("MASTER_KEY_PREINIT", "MAIN", "SDK_DID_NOT_PERSIST");
                return;
            }
            // Serialization fence for the SDK's earlier Editor.apply(); there
            // are no new values in this Editor and no key values are read.
            boolean committed = prefs.edit().commit();
            emit("MASTER_KEY_PREINIT", "MAIN",
                committed ? "ORIGINAL_KEY_PERSISTED" : "PERSISTENCE_UNCONFIRMED");
        } catch (SecurityException failure) {
            emit("MASTER_KEY_PREINIT", "MAIN", "ACCOUNT_ACCESS_DENIED");
        } catch (Throwable failure) {
            // Do not force a key, touch an existing account or suppress SDK exceptions.
            emit("MASTER_KEY_PREINIT", "MAIN", "SDK_UNAVAILABLE");
        }
    }

    private synchronized void observeOriginalPassportDecryptOutcome(Application app) {
        if (passportDecryptOutcomeHooked || app == null
                || !PACKAGE.equals(app.getPackageName())) return;
        try {
            ClassLoader loader = app.getClass().getClassLoader();
            if (loader == null) loader = app.getClassLoader();
            if (loader == null) {
                emit("MASTER_TOKEN_DECRYPT_HOOK", "VENDOR", "NO_LOADER");
                return;
            }
            Class<?> decoder = Class.forName(
                "com.yandex.passport.internal.core.accounts.v", false, loader);
            Class<?> outcome = Class.forName(
                "com.yandex.passport.internal.core.accounts.v$c", false, loader);
            Field failureField = outcome.getDeclaredField("for");
            failureField.setAccessible(true);
            Method m = decoder.getDeclaredMethod("if", String.class);
            hook(m).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                .intercept(chain -> {
                    String process = isPassportProcess() ? "PASSPORT" : "MAIN";
                    Object result;
                    try {
                        result = chain.proceed();
                    } catch (Throwable failure) {
                        if (passportDecryptOutcomeEvents.incrementAndGet() <= 12)
                            emit("MASTER_TOKEN_DECRYPT", process, "THREW");
                        throw failure;
                    }
                    if (passportDecryptOutcomeEvents.incrementAndGet() <= 12) {
                        String status = "UNAVAILABLE";
                        try {
                            if (outcome.isInstance(result))
                                status = failureField.get(result) == null
                                    ? "NO_EXCEPTION" : "DECRYPT_EXCEPTION";
                        } catch (Throwable ignored) { }
                        emit("MASTER_TOKEN_DECRYPT", process, status);
                    }
                    return result;
                });
            passportDecryptOutcomeHooked = true;
            emit("MASTER_TOKEN_DECRYPT_HOOK", "VENDOR", "REGISTERED");
        } catch (Throwable ignored) {
            emit("MASTER_TOKEN_DECRYPT_HOOK", "VENDOR", "NO_HOOK");
        }
    }

    private synchronized void preparePassportDiagnostics(Application app) {
        if (passportDiagnosticCallbacksReady || app == null || !isPassportProcess() ||
                !PACKAGE.equals(app.getPackageName())) return;
        try {
            Context c = app.getApplicationContext();
            diagnosticContext = c == null ? app : c;
            observeOriginalPassportDecryptOutcome(app);
            emit("PASSPORT_PROCESS", "CLONE_PASSPORT", "APPLICATION_READY");
            app.registerActivityLifecycleCallbacks(new Application.ActivityLifecycleCallbacks() {
                @Override public void onActivityCreated(Activity a, Bundle state) {
                    logActivityPhase(a,"CREATED");
                }
                @Override public void onActivityStarted(Activity a) {
                    logActivityPhase(a,"STARTED");
                }
                @Override public void onActivityResumed(Activity a) {
                    logActivityPhase(a,"RESUMED");
                    observeAccountSnapshot(a);
                }
                @Override public void onActivityPaused(Activity a) {
                    logActivityPhase(a,"PAUSED");
                }
                @Override public void onActivityStopped(Activity a) {
                    logActivityPhase(a,"STOPPED");
                }
                @Override public void onActivitySaveInstanceState(Activity a, Bundle state) {
                    logActivityPhase(a,"SAVE_STATE");
                }
                @Override public void onActivityDestroyed(Activity a) {
                    logActivityPhase(a, a != null && a.isFinishing()
                        ? "DESTROYED_FINISHING" : "DESTROYED_OTHER");
                }
            });
            passportDiagnosticCallbacksReady = true;
        } catch (Throwable ignored) {
            emit("PASSPORT_PROCESS", "CLONE_PASSPORT", "CALLBACKS_FAILED");
        }
    }

    private synchronized void prepareOwnerDiagnostics(Application app) {
        if (app == null || !PACKAGE.equals(app.getPackageName())) return;
        try {
            Context appContext = app.getApplicationContext();
            diagnosticContext = appContext == null ? app : appContext;
            observeOriginalPassportDecryptOutcome(app);
            preinitializeOriginalMasterKeyIfFresh(app);
            capturePreviousProcessExits(diagnosticContext);
            emit("DIAGNOSTIC_CAPTURE", "LOCAL_FILE", "READY");
            emit("DIAGNOSTIC_BUILD", DIAGNOSTIC_BUILD, "ACTIVE");
        } catch (Throwable ignored) { }
        if (diagnosticUiReady) return;
        try {
            app.registerActivityLifecycleCallbacks(new Application.ActivityLifecycleCallbacks() {
                @Override public void onActivityCreated(Activity activity, Bundle state) {
                    logActivityPhase(activity,"CREATED");
                    observeOriginalPostLoginReceipts(activity);
                }
                @Override public void onActivityStarted(Activity activity) {
                    logActivityPhase(activity,"STARTED");
                }
                @Override public void onActivityResumed(Activity activity) {
                    logActivityPhase(activity,"RESUMED");
                    observeAccountSnapshot(activity);
                    observeOnboardingReadOnly(activity);
                    attachDiagnosticExportButton(activity);
                }
                @Override public void onActivityPaused(Activity activity) {
                    logActivityPhase(activity,"PAUSED");
                }
                @Override public void onActivityStopped(Activity activity) {
                    logActivityPhase(activity,"STOPPED");
                }
                @Override public void onActivitySaveInstanceState(Activity activity, Bundle state) {
                    logActivityPhase(activity,"SAVE_STATE");
                }
                @Override public void onActivityDestroyed(Activity activity) {
                    try {
                        logActivityPhase(activity,
                            activity != null && activity.isFinishing()
                                ? "DESTROYED_FINISHING":"DESTROYED_OTHER");
                    } catch (Throwable ignored) { }
                }
            });
            diagnosticUiReady = true;
        } catch (Throwable ignored) {
            emit("DIAGNOSTIC_UI", "ACTIVITY_CALLBACKS", "NO_HOOK");
        }
    }

    /**
     * Narrow, clone-only navigation witness, enabled by owner-device evidence
     * showing a single process session and no fatal dispatch. We observe
     * framework navigation and activity lifecycle phases without changing
     * intents, URLs, authentication, results or the app's exit behavior.
     */
    private static String activityFamily(Activity activity) {
        if (activity == null) return "UNKNOWN_ACTIVITY";
        try {
            String name = activity.getClass().getName();
            if ("ru.yandex.music.main.MainScreenActivity".equals(name))
                return "MAIN_ACTIVITY";
            if ("ru.yandex.music.entry.EntryScreenActivity".equals(name))
                return "ENTRY_ACTIVITY";
            if ("ru.yandex.music.wizard3.WizardActivity".equals(name)
                    || "ru.yandex.music.wizard.WizardActivityOld".equals(name))
                return "WIZARD_ACTIVITY";
            if (name.startsWith("com.yandex.passport.")
                    || name.startsWith("ru.yandex.passport."))
                return "PASSPORT_ACTIVITY";
            if (name.startsWith("ru.yandex.") || name.startsWith("com.yandex."))
                return "VENDOR_ACTIVITY";
            return "OTHER_ACTIVITY";
        } catch (Throwable ignored) {
            return "UNKNOWN_ACTIVITY";
        }
    }


    /**
     * Read-only exact Yandex_Music/onboarding write witness.
     *
     * Tracks only SharedPreferences instances requested under the exact
     * Yandex_Music filename, their Editor instances, and putBoolean("onboarding").
     * It records the caller class/method and whether the real Editor commit/apply
     * returns. No preference is read or written by this observer.
     */
    private static String onboardingWriterCaller() {
        try {
            for (StackTraceElement frame : Thread.currentThread().getStackTrace()) {
                String owner = frame.getClassName();
                if (owner == null || owner.isEmpty()
                        || owner.startsWith(ExitCallsiteWitness.class.getName())
                        || owner.startsWith("pro.celikom.a1exitwitness.")
                        || owner.startsWith("io.github.libxposed.")
                        || owner.startsWith("org.lsposed.")
                        || owner.startsWith("de.robv.android.xposed.")
                        || owner.startsWith("com.android.")
                        || owner.startsWith("android.")
                        || owner.startsWith("java.")
                        || owner.startsWith("dalvik.")
                        || owner.startsWith("sun.")) continue;
                String method = frame.getMethodName();
                if (method == null || method.isEmpty()) method = "UNKNOWN";
                return owner + "_" + method;
            }
        } catch (Throwable ignored) { }
        return "UNKNOWN";
    }

    private synchronized void installOnboardingWriterWitness() {
        if (onboardingWriterHooked) return;
        try {
            Class<?> contextImpl = Class.forName("android.app.ContextImpl", false, null);
            Method getPrefs = contextImpl.getDeclaredMethod(
                "getSharedPreferences", String.class, int.class);
            getPrefs.setAccessible(true);
            hook(getPrefs).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                .intercept(chain -> {
                    Object result = chain.proceed();
                    try {
                        Object name = chain.getArg(0);
                        if ("Yandex_Music".equals(name) && result != null)
                            onboardingPreferenceStores.put(result, Boolean.TRUE);
                    } catch (Throwable ignored) { }
                    return result;
                });

            Class<?> prefsImpl = Class.forName("android.app.SharedPreferencesImpl", false, null);
            Method edit = prefsImpl.getDeclaredMethod("edit");
            edit.setAccessible(true);
            hook(edit).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                .intercept(chain -> {
                    Object result = chain.proceed();
                    try {
                        if (onboardingPreferenceStores.containsKey(chain.getThisObject())
                                && result != null)
                            yandexMusicPreferenceEditors.put(result, Boolean.TRUE);
                    } catch (Throwable ignored) { }
                    return result;
                });

            Class<?> editorImpl = Class.forName(
                "android.app.SharedPreferencesImpl$EditorImpl", false, null);
            Method putBoolean = editorImpl.getDeclaredMethod(
                "putBoolean", String.class, boolean.class);
            putBoolean.setAccessible(true);
            hook(putBoolean).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                .intercept(chain -> {
                    Object editor = chain.getThisObject();
                    Object key = chain.getArg(0);
                    boolean value = Boolean.TRUE.equals(chain.getArg(1));
                    Object result = chain.proceed();
                    try {
                        if (yandexMusicPreferenceEditors.containsKey(editor)
                                && "onboarding".equals(key)
                                && onboardingWriterEvents.incrementAndGet() <= 24) {
                            onboardingPreferenceEditors.put(editor, value);
                            emit("ONBOARDING_WRITE", onboardingWriterCaller(),
                                value ? "TRUE" : "FALSE");
                        }
                    } catch (Throwable ignored) { }
                    return result;
                });

            Method commit = editorImpl.getDeclaredMethod("commit");
            commit.setAccessible(true);
            hook(commit).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                .intercept(chain -> {
                    Object editor = chain.getThisObject();
                    boolean tracked = onboardingPreferenceEditors.containsKey(editor);
                    Object result = chain.proceed();
                    if (tracked) {
                        onboardingPreferenceEditors.remove(editor);
                        yandexMusicPreferenceEditors.remove(editor);
                        emit("ONBOARDING_WRITE_PERSIST", "COMMIT",
                            Boolean.TRUE.equals(result) ? "TRUE" : "FALSE");
                    }
                    return result;
                });

            Method apply = editorImpl.getDeclaredMethod("apply");
            apply.setAccessible(true);
            hook(apply).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                .intercept(chain -> {
                    Object editor = chain.getThisObject();
                    boolean tracked = onboardingPreferenceEditors.containsKey(editor);
                    Object result = chain.proceed();
                    if (tracked) {
                        onboardingPreferenceEditors.remove(editor);
                        yandexMusicPreferenceEditors.remove(editor);
                        emit("ONBOARDING_WRITE_PERSIST", "APPLY", "RETURN");
                    }
                    return result;
                });

            onboardingWriterHooked = true;
            emit("ONBOARDING_WRITER_HOOK", "ANDROID", "REGISTERED");
        } catch (Throwable ignored) {
            emit("ONBOARDING_WRITER_HOOK", "ANDROID", "NO_HOOK");
        }
    }

    /**
     * Real, clone-owned original Yandex startup gate. The exact issuer-signed
     * 2025 MainScreenActivity reads this boolean from Yandex_Music prefs;
     * an issuer onboarding callback also writes it. Observe it ONLY.
     * No preference edit, login change, forced navigation or account access.
     */
    private void observeOnboardingReadOnly(Activity activity) {
        if (activity==null || !PACKAGE.equals(activity.getPackageName())
                || !PACKAGE.equals(Application.getProcessName())
                || onboardingReads.incrementAndGet()>20) return;
        try {
            android.content.SharedPreferences prefs=activity.getSharedPreferences(
                "Yandex_Music", Context.MODE_PRIVATE);
            String state=!prefs.contains("onboarding") ? "UNSET"
                : prefs.getBoolean("onboarding",false) ? "TRUE" : "FALSE";
            emit("ONBOARDING_PREF",activityFamily(activity),state);
        } catch (Throwable ignored) {
            emit("ONBOARDING_PREF",activityFamily(activity),"UNAVAILABLE");
        }
    }


    /**
     * Return only a fixed category for the two exact original callers of qY5.if.
     * Stack contents and arbitrary class names are never emitted.
     */
    private static String originalPostLoginCallerCategory() {
        try {
            StackTraceElement[] frames = Thread.currentThread().getStackTrace();
            int limit = Math.min(frames.length, 48);
            for (int i = 0; i < limit; i++) {
                StackTraceElement frame = frames[i];
                String owner = frame.getClassName();
                String method = frame.getMethodName();
                if ("oY5$a".equals(owner) && "emit".equals(method))
                    return "PASSPORT_LOGIN_RESULT";
                if ("pY5$a".equals(owner) && "emit".equals(method))
                    return "AUTOLOGIN_UID_RESULT";
            }
        } catch (Throwable ignored) { }
        return "OTHER_CALLER";
    }

    /**
     * Exact immutable 2025.10.4 publisher result chain, read-only:
     * ZX5.if(WS3) -> hT3.try(Bundle,String) -> YS3.if(lw4,boolean).
     * Strict, version-pinned method signatures; no payload/extras/token reads.
     * Only armed in clone MAIN when a real Entry Activity is created.
     * There is NO synthetic Success(userInfo), preference write or launch.
     */
    /**
     * Closed, no-secret reason classes from the original coroutine's token
     * request. Never serialize the continuation result, token, exception,
     * message, stack, UID, account, or request arguments.
     */
    private static String tokenRequestErrorCategory(Throwable error) {
        if (error == null) return "NO_THROWABLE";
        if (error instanceof java.net.SocketTimeoutException) return "TIMEOUT";
        if (error instanceof java.net.UnknownHostException) return "DNS";
        if (error instanceof java.io.IOException) return "NETWORK_OR_IO";
        if (error instanceof SecurityException) return "SECURITY";
        String name = error.getClass().getName();
        if ("com.yandex.passport.api.exception.a".equals(name)) return "PASSPORT_API_A";
        if ("com.yandex.passport.api.exception.b".equals(name)) return "PASSPORT_API_B";
        if (name.startsWith("com.yandex.passport.")) return "PASSPORT_OTHER";
        if (error instanceof IllegalStateException) return "ILLEGAL_STATE";
        return "OTHER_FAILURE";
    }

    private synchronized void observeOriginalPostLoginReceipts(Activity activity) {
        if (activity == null || !PACKAGE.equals(Application.getProcessName())
                || !"ENTRY_ACTIVITY".equals(activityFamily(activity))
                || (postLoginPipelineHooked && postLoginFlowHooked
                    && postLoginPublishHooked && postLoginConsumeHooked
                    && postLoginNativeRouteHooked)
                || postLoginHookAttempts.incrementAndGet() > 3) return;
        ClassLoader loader = activity.getClass().getClassLoader();
        if (loader == null) loader = activity.getClassLoader();
        if (loader == null) {
            emit("POSTLOGIN_HOOK", "ENTRY", "NO_LOADER");
            return;
        }
        // Original 2025 qY5 coroutine: observe the stage and terminal subtype.
        // At token-resume only, classify the return object's TYPE and a fixed
        // failure-family enum; never serialize, copy, log, or modify any token,
        // account, error message, userInfo, or callback payload.
        // No synthetic login or invocation of the vendor coroutine is allowed.
        if (!postLoginPipelineHooked) {
            try {
                Class<?> owner = Class.forName("qY5", false, loader);
                Class<?> passportUser =
                    Class.forName("com.yandex.passport.api.n0", false, loader);
                Class<?> continuation = Class.forName("Oe2", false, loader);
                Class<?> resumed = Class.forName("nY5", false, loader);
                Field stateField = resumed.getDeclaredField("continue");
                stateField.setAccessible(true);
                // Exact original nY5.invokeSuspend writes its result into
                // private:Object before resuming qY5. Inspect ONLY type.
                Field tokenResumeResult = resumed.getDeclaredField("private");
                tokenResumeResult.setAccessible(true);
                Class<?> tokenFailure = Class.forName("zW8$b", false, loader);
                Field tokenFailureCause = tokenFailure.getDeclaredField("default");
                tokenFailureCause.setAccessible(true);
                Method m = owner.getDeclaredMethod("if", owner, boolean.class,
                    passportUser, continuation);
                hook(m).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                    .intercept(chain -> {
                        String stage = "INITIAL";
                        boolean initialCall = true;
                        try {
                            Object frame = chain.getArg(3);
                            if (resumed.isInstance(frame)) {
                                initialCall = false;
                                int state = stateField.getInt(frame) & Integer.MAX_VALUE;
                                stage = state == 1 ? "AFTER_TOKEN_REQUEST" :
                                    state == 2 ? "AFTER_USERINFO_REQUEST" :
                                    state == 3 ? "AFTER_SYNC" : "OTHER_STAGE";
                            }
                        } catch (Throwable ignored) { stage = "UNKNOWN_STAGE"; }
                        if (initialCall &&
                                postLoginPipelineSourceEvents.incrementAndGet() <= 8) {
                            emit("LOGIN_PIPELINE_SOURCE", "ENTRY",
                                originalPostLoginCallerCategory());
                        }
                        if ("AFTER_TOKEN_REQUEST".equals(stage)
                                && postLoginTokenOutcomeEvents.incrementAndGet() <= 12) {
                            try {
                                Object frame = chain.getArg(3);
                                Object reply = tokenResumeResult.get(frame);
                                boolean isFailure = reply != null
                                    && tokenFailure.isInstance(reply);
                                String category = reply == null ? "NULL" :
                                    isFailure ? "FAILURE" :
                                    reply instanceof String ? "STRING_RESULT" :
                                    "OTHER_NONFAILURE_RESULT";
                                emit("LOGIN_TOKEN_OUTCOME", "ENTRY", category);
                                if (isFailure) {
                                    Object cause = tokenFailureCause.get(reply);
                                    emit("LOGIN_TOKEN_ERROR_KIND", "ENTRY",
                                        cause instanceof Throwable
                                            ? tokenRequestErrorCategory((Throwable) cause)
                                            : "NO_THROWABLE");
                                }
                            } catch (Throwable ignored) {
                                emit("LOGIN_TOKEN_OUTCOME", "ENTRY", "UNAVAILABLE");
                            }
                        }
                        Object result;
                        try {
                            result = chain.proceed();
                        } catch (Throwable failure) {
                            if (postLoginPipelineEvents.incrementAndGet() <= 32)
                                emit("LOGIN_PIPELINE_RESULT", stage, "THREW");
                            throw failure;
                        }
                        try {
                            if (postLoginPipelineEvents.incrementAndGet() <= 32) {
                                String type = result == null ? "" :
                                    result.getClass().getName();
                                String category =
                                    "qY5$a$a".equals(type) ? "NO_USERINFO_RESULT" :
                                    "qY5$a$b".equals(type) ? "EXTERNAL_HANDOFF" :
                                    "qY5$a$c".equals(type) ? "USERINFO_READY" :
                                    "NONTERMINAL_OR_OTHER";
                                emit("LOGIN_PIPELINE_RESULT", stage, category);
                            }
                        } catch (Throwable ignored) { }
                        return result;
                    });
                postLoginPipelineHooked = true;
                emit("POSTLOGIN_HOOK", "PIPELINE", "REGISTERED");
            } catch (Throwable ignored) {
                emit("POSTLOGIN_HOOK", "PIPELINE", "NO_HOOK");
            }
        }
        // Original LoginFragment flow emission: only class identity, never
        // a user-info object, result payload, URL, token, account or exception.
        if (!postLoginFlowHooked) {
            try {
                Class<?> receiver = Class.forName("eY5$a", false, loader);
                Class<?> continuation =
                    Class.forName("kotlin.coroutines.Continuation", false, loader);
                Method m = receiver.getDeclaredMethod(
                    "emit", Object.class, continuation);
                hook(m).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                    .intercept(chain -> {
                        try {
                            if (postLoginFlowEvents.incrementAndGet() <= 24) {
                                Object event = chain.getArg(0);
                                String type = event == null ? "" :
                                    event.getClass().getName();
                                String category =
                                    "qY5$a$a".equals(type) ? "NO_USERINFO_RESULT" :
                                    "qY5$a$b".equals(type) ? "EXTERNAL_HANDOFF" :
                                    "qY5$a$c".equals(type) ? "USERINFO_READY" :
                                    "OTHER_FLOW_STATE";
                                emit("LOGIN_FLOW_RESULT", "ENTRY", category);
                            }
                        } catch (Throwable ignored) { }
                        return chain.proceed();
                    });
                postLoginFlowHooked = true;
                emit("POSTLOGIN_HOOK", "FLOW", "REGISTERED");
            } catch (Throwable ignored) {
                emit("POSTLOGIN_HOOK", "FLOW", "NO_HOOK");
            }
        }
        if (!postLoginPublishHooked) {
            try {
                Class<?> receiver = Class.forName("ZX5", false, loader);
                Class<?> resultType = Class.forName("WS3", false, loader);
                Method m = receiver.getDeclaredMethod("if", resultType);
                hook(m).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                    .intercept(chain -> {
                        try {
                            if (postLoginStageEvents.incrementAndGet() <= 32) {
                                Object event = chain.getArg(0);
                                // Exact type comparison only: no String from the event.
                                String kind = event != null
                                    && "WS3$b".equals(event.getClass().getName())
                                    ? "REAL_USERINFO_SUCCESS" : "OTHER_RESULT";
                                emit("POSTLOGIN_PUBLISH", "ENTRY", kind);
                            }
                        } catch (Throwable ignored) { }
                        return chain.proceed();
                    });
                postLoginPublishHooked = true;
                emit("POSTLOGIN_HOOK", "PUBLISH", "REGISTERED");
            } catch (Throwable ignored) {
                emit("POSTLOGIN_HOOK", "PUBLISH", "NO_HOOK");
            }
        }
        if (!postLoginConsumeHooked) {
            try {
                Class<?> receiver = Class.forName("hT3", false, loader);
                Method m = receiver.getDeclaredMethod("try", Bundle.class, String.class);
                hook(m).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                    .intercept(chain -> {
                        try {
                            Object key = chain.getArg(1);
                            if ("EntryScreenCloseLoginKey".equals(key)
                                    && postLoginStageEvents.incrementAndGet() <= 32)
                                emit("POSTLOGIN_CONSUME", "ENTRY", "RESULT_KEY_DELIVERED");
                        } catch (Throwable ignored) { }
                        return chain.proceed();
                    });
                postLoginConsumeHooked = true;
                emit("POSTLOGIN_HOOK", "CONSUME", "REGISTERED");
            } catch (Throwable ignored) {
                emit("POSTLOGIN_HOOK", "CONSUME", "NO_HOOK");
            }
        }
        if (!postLoginNativeRouteHooked) {
            try {
                Class<?> receiver = Class.forName("YS3", false, loader);
                Class<?> info = Class.forName("lw4", false, loader);
                Method m = receiver.getDeclaredMethod("if", info, boolean.class);
                hook(m).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                    .intercept(chain -> {
                        boolean tracked = false;
                        try {
                            if (postLoginStageEvents.incrementAndGet() <= 32) {
                                Object flag = chain.getArg(1);
                                emit("POSTLOGIN_MAIN_ROUTE", "ENTRY",
                                    Boolean.TRUE.equals(flag) ? "MAIN_REQUESTED"
                                        : "OTHER_ROUTE");
                                tracked = true;
                            }
                        } catch (Throwable ignored) { }
                        try {
                            Object result = chain.proceed();
                            if (tracked) emit("POSTLOGIN_MAIN_ROUTE", "ENTRY", "RETURN");
                            return result;
                        } catch (Throwable failure) {
                            if (tracked) emit("POSTLOGIN_MAIN_ROUTE", "ENTRY", "THREW");
                            throw failure;
                        }
                    });
                postLoginNativeRouteHooked = true;
                emit("POSTLOGIN_HOOK", "NATIVE_ROUTE", "REGISTERED");
            } catch (Throwable ignored) {
                emit("POSTLOGIN_HOOK", "NATIVE_ROUTE", "NO_HOOK");
            }
        }
    }

    /** Only compare the Intent action against the known fixed result action.
     * Never inspect Intent fields, identity, URL, account or token extras. */
    private synchronized boolean observeLoginResultNewIntent() {
        if (newIntentObserverArmed) return true;
        try {
            Method m=android.app.Instrumentation.class.getDeclaredMethod(
                "callActivityOnNewIntent",Activity.class,Intent.class);
            hook(m).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                .intercept(chain -> {
                    try {
                        Object receiver=chain.getArg(0);
                        Object data=chain.getArg(1);
                        if (receiver instanceof Activity
                                && PACKAGE.equals(((Activity)receiver).getPackageName())
                                && newIntentObserved.incrementAndGet()<=24) {
                            String action=data instanceof Intent
                                ? ((Intent)data).getAction() : null;
                            emit("ACTIVITY_NEW_INTENT",
                                activityFamily((Activity)receiver),
                                "com.yandex.passport.ACTION_LOGIN_RESULT".equals(action)
                                    ? "LOGIN_RESULT" : "OTHER");
                        }
                    } catch (Throwable ignored) { }
                    return chain.proceed();
                });
            newIntentObserverArmed=true;
            return true;
        } catch (Throwable ignored) {
            emit("ACTIVITY_NEW_INTENT_HOOK","ANDROID","NO_HOOK");
            return false;
        }
    }

    private static String intentActionCategory(Intent intent) {
        if (intent == null) return "NULL";
        try {
            String action = intent.getAction();
            if (action == null) return "NONE";
            if (Intent.ACTION_VIEW.equals(action)) return "VIEW";
            if (Intent.ACTION_MAIN.equals(action)) return "MAIN";
            if (Intent.ACTION_SEND.equals(action)) return "SEND";
            if (Intent.ACTION_GET_CONTENT.equals(action)) return "GET_CONTENT";
            if (Intent.ACTION_CHOOSER.equals(action)) return "CHOOSER";
            return "OTHER";
        } catch (Throwable ignored) { return "UNKNOWN"; }
    }

    private static String intentDestinationCategory(Intent intent) {
        if (intent == null) return "NULL";
        try {
            ComponentName component = intent.getComponent();
            String target = component != null ? component.getPackageName() : intent.getPackage();
            if (target == null) return "IMPLICIT";
            if (PACKAGE.equals(target)) return "OWN";
            if ("ru.yandex.music".equals(target)) return "PUBLISHER";
            return "EXTERNAL";
        } catch (Throwable ignored) { return "UNKNOWN"; }
    }

    private void logActivityPhase(Activity activity, String phase) {
        try {
            if (activity == null || !PACKAGE.equals(activity.getPackageName())) return;
            if (activityPhasesLogged.incrementAndGet() <= 96)
                emit("ACTIVITY_PHASE", activityFamily(activity), phase);
        } catch (Throwable ignored) { }
    }

    // Emit no identifiers, URLs, extras or argument values from navigation.
    private static String ownActivityTargetShape(Intent intent) {
        // Only Intent's already-in-memory fields: no PackageManager IPC,
        // no package resolution, no Activity launch, no URL/extras.
        if (intent == null) return "NULL_INTENT";
        try {
            ComponentName component = intent.getComponent();
            if (component != null) {
                if (!PACKAGE.equals(component.getPackageName()))
                    return "EXPLICIT_OTHER_PACKAGE";
                String cls = component.getClassName();
                if ("ru.yandex.music.main.MainScreenActivity".equals(cls))
                    return "EXPLICIT_OWN_MAIN";
                if ("ru.yandex.music.entry.EntryScreenActivity".equals(cls))
                    return "EXPLICIT_OWN_ENTRY";
                if ("ru.yandex.music.wizard.WizardActivityOld".equals(cls) ||
                        "ru.yandex.music.wizard3.WizardActivity".equals(cls))
                    return "EXPLICIT_OWN_WIZARD";
                if (cls.startsWith("com.yandex.passport."))
                    return "EXPLICIT_OWN_PASSPORT";
                if (cls.startsWith("ru.yandex.music."))
                    return "EXPLICIT_OWN_MUSIC_OTHER";
                if (cls.startsWith("com.yandex.plus."))
                    return "EXPLICIT_OWN_PLUS";
                if (cls.startsWith("ru.yandex.") || cls.startsWith("com.yandex."))
                    return "EXPLICIT_OWN_VENDOR_OTHER";
                return "EXPLICIT_OWN_OTHER";
            }
            String target = intent.getPackage();
            if (PACKAGE.equals(target)) return "IMPLICIT_OWN_PACKAGE";
            if ("ru.yandex.music".equals(target)) return "IMPLICIT_PUBLISHER_PACKAGE";
            if (target != null) return "IMPLICIT_OTHER_PACKAGE";
            return "IMPLICIT_UNSCOPED";
        } catch (Throwable ignored) {
            return "INTENT_SHAPE_UNAVAILABLE";
        }
    }

    private static String ownActivityFlagsCategory(Intent intent) {
        if (intent == null) return "NO_INTENT";
        try {
            int flags = intent.getFlags();
            if ((flags & Intent.FLAG_ACTIVITY_CLEAR_TASK) != 0) return "CLEAR_TASK";
            if ((flags & Intent.FLAG_ACTIVITY_CLEAR_TOP) != 0) return "CLEAR_TOP";
            if ((flags & Intent.FLAG_ACTIVITY_NEW_TASK) != 0) return "NEW_TASK";
            if ((flags & Intent.FLAG_ACTIVITY_SINGLE_TOP) != 0) return "SINGLE_TOP";
            return "OTHER_OR_NONE";
        } catch (Throwable ignored) {
            return "FLAGS_UNAVAILABLE";
        }
    }

    private static String ownActivityStartErrorCategory(Throwable failure) {
        if (failure instanceof android.content.ActivityNotFoundException)
            return "ACTIVITY_NOT_FOUND";
        if (failure instanceof SecurityException) return "SECURITY_EXCEPTION";
        if (failure instanceof IllegalArgumentException) return "ILLEGAL_ARGUMENT";
        return "OTHER_THROW";
    }

    /** Only coarse RESULT_OK/CANCELED categories. Never inspect Intent,
     * extras, tokens, names or authorization data. */
    private synchronized boolean observePassportResultDelivery() {
        if (activityResultHooked) return true;
        int registered=0;
        // Only the result category is observed; no Intent fields or extras.
        for (Class<?>[] signature : new Class<?>[][] {
                new Class<?>[]{int.class},
                new Class<?>[]{int.class, Intent.class}}) {
            try {
                Method method=Activity.class.getDeclaredMethod("setResult",signature);
                hook(method).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                    .intercept(chain -> {
                        try {
                            Object receiver=chain.getThisObject();
                            if (receiver instanceof Activity
                                    && PACKAGE.equals(((Activity)receiver).getPackageName())
                                    && "PASSPORT_ACTIVITY".equals(activityFamily((Activity)receiver))
                                    && activityResultProducerObservations.incrementAndGet()<=32) {
                                Object result=chain.getArg(0);
                                String category=!(result instanceof Integer)
                                    ? "UNKNOWN" : ((Integer)result)==Activity.RESULT_OK
                                    ? "OK" : ((Integer)result)==Activity.RESULT_CANCELED
                                    ? "CANCELED" : "OTHER";
                                emit("ACTIVITY_RESULT",activityFamily((Activity)receiver),
                                    category);
                            }
                        } catch (Throwable ignored) { }
                        return chain.proceed();
                    });
                registered++;
            } catch (Throwable ignored) { }
        }
        activityResultHooked=registered==2;
        emit("ACTIVITY_RESULT_HOOK","ANDROID",
            registered==2 ? "BOTH" : registered==1 ? "PARTIAL" : "NO_HOOK");
        return registered>0;
    }

    /**
     * Observe framework delivery of an Activity result to the real Entry host.
     * setResult() in Passport is only the producer side; this hook records the
     * receiver-side dispatch category without inspecting who, request code,
     * Intent, extras or any authentication payload.
     */
    private synchronized boolean observeEntryActivityResultDelivery() {
        if (activityResultDeliveryHooked) return true;
        try {
            Method method = Activity.class.getDeclaredMethod(
                "dispatchActivityResult", String.class, int.class, int.class, Intent.class, String.class);
            method.setAccessible(true);
            hook(method).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                .intercept(chain -> {
                    try {
                        Object receiver = chain.getThisObject();
                        if (receiver instanceof Activity
                                && PACKAGE.equals(((Activity) receiver).getPackageName())
                                && "ENTRY_ACTIVITY".equals(activityFamily((Activity) receiver))
                                && activityResultDeliveryObservations.incrementAndGet() <= 48) {
                            Object raw = chain.getArg(2);
                            String category = !(raw instanceof Integer) ? "UNKNOWN"
                                : ((Integer) raw) == Activity.RESULT_OK ? "OK"
                                : ((Integer) raw) == Activity.RESULT_CANCELED
                                    ? "CANCELED" : "OTHER";
                            emit("ACTIVITY_RESULT_DELIVERY", "ENTRY_ACTIVITY", category);
                        }
                    } catch (Throwable ignored) { }
                    return chain.proceed();
                });
            activityResultDeliveryHooked = true;
            emit("ACTIVITY_RESULT_DELIVERY_HOOK", "ANDROID", "REGISTERED");
            return true;
        } catch (Throwable ignored) {
            emit("ACTIVITY_RESULT_DELIVERY_HOOK", "ANDROID", "NO_HOOK");
            return false;
        }
    }

    private boolean observeOwnActivityFinish(String methodName) {
        try {
            Method method = Activity.class.getDeclaredMethod(methodName);
            method.setAccessible(true);
            hook(method).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                .intercept(chain -> {
                    try {
                        Object receiver = chain.getThisObject();
                        if (receiver instanceof Activity &&
                                PACKAGE.equals(((Activity) receiver).getPackageName()) &&
                                activityFinishesLogged.incrementAndGet() <= 24) {
                            String action = "finish".equals(methodName) ? "FINISH"
                                : "finishAffinity".equals(methodName) ? "FINISH_AFFINITY"
                                : "finishAndRemoveTask".equals(methodName) ? "FINISH_REMOVE_TASK"
                                : "FINISH_AFTER_TRANSITION";
                            emit("ACTIVITY_FINISH", activityFamily((Activity) receiver), action);
                        }
                    } catch (Throwable ignored) { }
                    return chain.proceed();
                });
            emit("ACTIVITY_FINISH_HOOK","ANDROID", "REGISTERED");
            return true;
        } catch (Throwable ignored) {
            emit("ACTIVITY_FINISH_HOOK","ANDROID", "NO_HOOK");
            return false;
        }
    }

    private boolean observeOwnActivityLaunch(String methodName, Class<?>[] args) {
        try {
            Method method = Activity.class.getDeclaredMethod(methodName,args);
            method.setAccessible(true);
            hook(method).setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                .intercept(chain -> {
                    boolean record = false;
                    try {
                        Object receiver = chain.getThisObject();
                        if (receiver instanceof Activity &&
                                PACKAGE.equals(((Activity) receiver).getPackageName()) &&
                                activityStartsLogged.incrementAndGet() <= 48) {
                            record = true;
                            Activity activity = (Activity) receiver;
                            Object raw = chain.getArg(0);
                            Intent intent = raw instanceof Intent ? (Intent) raw : null;
                            emit("ACTIVITY_START", intentActionCategory(intent),
                                intentDestinationCategory(intent));
                            // Minimal unconditional marker before any PackageManager
                            // call; exposes whether this exact new hook is running.
                            emit("NAV_V3_START", "CLONE_ACTIVITY", "SEEN");
                            emit("ACTIVITY_TARGET", ownActivityTargetShape(intent),
                                ownActivityFlagsCategory(intent));
                        }
                    } catch (Throwable ignored) { }
                    // The former observer only logged that a start was attempted.
                    // Preserve the result/exception, and distinguish a failed
                    // start from a resolved transition without modifying Intents.
                    try {
                        Object result = chain.proceed();
                        try {
                            if (record) emit("ACTIVITY_START_RESULT","ANDROID","RETURN");
                        } catch (Throwable ignored) { }
                        return result;
                    } catch (Throwable failure) {
                        try {
                            if (record) emit("ACTIVITY_START_RESULT","ANDROID",
                                ownActivityStartErrorCategory(failure));
                        } catch (Throwable ignored) { }
                        throw failure;
                    }
                });
            emit("ACTIVITY_START_HOOK","ANDROID","REGISTERED");
            return true;
        } catch (Throwable ignored) {
            emit("ACTIVITY_START_HOOK","ANDROID","NO_HOOK");
            return false;
        }
    }

    private static void capturePreviousProcessExits(Context context) {
        if (context == null) return;
        if (Build.VERSION.SDK_INT < 30) {
            emit("PREVIOUS_EXIT_INFO", "ANDROID", "API_UNAVAILABLE");
            return;
        }
        try {
            ActivityManager manager = (ActivityManager)
                context.getSystemService(Context.ACTIVITY_SERVICE);
            if (manager == null) {
                emit("PREVIOUS_EXIT_INFO", "ANDROID", "SERVICE_UNAVAILABLE");
                return;
            }
            List<ApplicationExitInfo> exits =
                manager.getHistoricalProcessExitReasons(PACKAGE, 0, 4);
            if (exits == null || exits.isEmpty()) {
                emit("PREVIOUS_EXIT_INFO", "ANDROID", "NONE");
                return;
            }
            int count = 0;
            for (ApplicationExitInfo info : exits) {
                if (info == null || count++ >= 4) continue;
                String process = info.getProcessName();
                String family = PASSPORT_PROCESS.equals(process) ? "PASSPORT"
                    : PACKAGE.equals(process) ? "MAIN" : "OTHER_CLONE";
                String reason = exitReasonCategory(info.getReason());
                emit("PREVIOUS_PROCESS_EXIT", "ANDROID_EXIT_INFO", reason);
                emit("EXIT_PROCESS_FAMILY", family, reason);
                long age = System.currentTimeMillis() - info.getTimestamp();
                emit("EXIT_RECENCY", family,
                    age >= 0 && age <= 300000L ? "WITHIN_FIVE_MINUTES" : "OLDER");
            }
        } catch (Throwable ignored) {
            emit("PREVIOUS_EXIT_INFO", "ANDROID", "UNAVAILABLE");
        }
    }

    private static String exitReasonCategory(int reason) {
        switch (reason) {
            case ApplicationExitInfo.REASON_EXIT_SELF: return "EXIT_SELF";
            case ApplicationExitInfo.REASON_SIGNALED: return "SIGNALED";
            case ApplicationExitInfo.REASON_LOW_MEMORY: return "LOW_MEMORY";
            case ApplicationExitInfo.REASON_CRASH: return "JAVA_CRASH";
            case ApplicationExitInfo.REASON_CRASH_NATIVE: return "NATIVE_CRASH";
            case ApplicationExitInfo.REASON_ANR: return "ANR";
            case ApplicationExitInfo.REASON_INITIALIZATION_FAILURE: return "INIT_FAILURE";
            case ApplicationExitInfo.REASON_PERMISSION_CHANGE: return "PERMISSION_CHANGE";
            case ApplicationExitInfo.REASON_EXCESSIVE_RESOURCE_USAGE: return "RESOURCE_LIMIT";
            case ApplicationExitInfo.REASON_USER_REQUESTED: return "USER_REQUESTED";
            case ApplicationExitInfo.REASON_USER_STOPPED: return "USER_STOPPED";
            case ApplicationExitInfo.REASON_DEPENDENCY_DIED: return "DEPENDENCY_DIED";
            case ApplicationExitInfo.REASON_OTHER: return "OTHER";
            default: return "UNKNOWN";
        }
    }

    private static int diagnosticDp(Context context, int value) {
        return (int) (value * context.getResources().getDisplayMetrics().density + 0.5f);
    }

    private void attachDiagnosticExportButton(Activity activity) {
        if (activity == null || !PACKAGE.equals(activity.getPackageName())) return;
        try {
            if (activity.getWindow() == null) return;
            View decor = activity.getWindow().getDecorView();
            if (!(decor instanceof FrameLayout)) return;
            FrameLayout root = (FrameLayout) decor;
            if (root.findViewWithTag(DIAGNOSTIC_BUTTON_TAG) != null) return;

            TextView button = new TextView(activity);
            button.setTag(DIAGNOSTIC_BUTTON_TAG);
            button.setText("Диагностика NAV9");
            button.setTextColor(Color.WHITE);
            button.setTextSize(12.0f);
            button.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
            button.setGravity(Gravity.CENTER);
            button.setPadding(diagnosticDp(activity, 12), diagnosticDp(activity, 9),
                diagnosticDp(activity, 12), diagnosticDp(activity, 9));
            GradientDrawable background = new GradientDrawable();
            background.setColor(Color.rgb(20, 32, 40));
            background.setCornerRadius(diagnosticDp(activity, 18));
            background.setStroke(diagnosticDp(activity, 1), Color.rgb(102, 224, 255));
            button.setBackground(background);
            button.setElevation(diagnosticDp(activity, 8));
            button.setClickable(true);
            button.setFocusable(true);
            button.setOnClickListener(view -> {
                try {
                    emit("DIAGNOSTIC_EXPORT", "DOWNLOADS", "REQUESTED");
                    // Query Android exit reasons only when owner taps, not on navigation.
                    emit("DIAGNOSTIC_EXIT_SNAPSHOT", "ANDROID", "ON_EXPORT");
                    capturePreviousProcessExits(activity);
                    Uri saved = saveDiagnosticReportToDownloads(activity);
                    if (saved != null) {
                        Toast.makeText(activity,
                            "Отчёт сохранён: Загрузки / CELIKOM A1",
                            Toast.LENGTH_LONG).show();
                    } else {
                        Toast.makeText(activity,
                            "Не удалось сохранить отчёт. Попробуй ещё раз.",
                            Toast.LENGTH_LONG).show();
                    }
                } catch (Throwable ignored) {
                    emit("DIAGNOSTIC_EXPORT", "DOWNLOADS", "FAILED");
                    Toast.makeText(activity,
                        "Не удалось сохранить отчёт. Попробуй ещё раз.",
                        Toast.LENGTH_LONG).show();
                }
            });
            FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT,
                ViewGroup.LayoutParams.WRAP_CONTENT,
                Gravity.TOP | Gravity.END);
            params.topMargin = diagnosticDp(activity, 52);
            params.rightMargin = diagnosticDp(activity, 12);
            root.addView(button, params);
        } catch (Throwable ignored) {
            emit("DIAGNOSTIC_UI", "BUTTON", "ATTACH_FAILED");
        }
    }

    private static Uri saveDiagnosticReportToDownloads(Context context) throws IOException {
        if (context == null || Build.VERSION.SDK_INT < 29) return null;
        File source = new File(context.getFilesDir(), DIAGNOSTIC_FILE);
        if (!source.isFile()) {
            emit("DIAGNOSTIC_EXPORT", "LOCAL_FILE", "MISSING");
            return null;
        }
        ContentResolver resolver = context.getContentResolver();
        String displayName = "CELIKOM-A1-Diagnostics-" +
            System.currentTimeMillis() + ".txt";
        ContentValues values = new ContentValues();
        values.put(MediaStore.MediaColumns.DISPLAY_NAME, displayName);
        values.put(MediaStore.MediaColumns.MIME_TYPE, "text/plain");
        values.put(MediaStore.MediaColumns.RELATIVE_PATH,
            Environment.DIRECTORY_DOWNLOADS + "/CELIKOM A1");
        values.put(MediaStore.MediaColumns.IS_PENDING, 1);
        Uri target = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
        if (target == null) throw new IOException("DOWNLOAD_INSERT_FAILED");
        boolean complete = false;
        try {
            try (InputStream input = new FileInputStream(source);
                 OutputStream output = resolver.openOutputStream(target, "w")) {
                if (output == null) throw new IOException("DOWNLOAD_STREAM_UNAVAILABLE");
                byte[] buffer = new byte[8192];
                int read;
                while ((read = input.read(buffer)) != -1) output.write(buffer, 0, read);
                // The :passport process has its own private bounded log: no
                // cross-process file writes/locks and no account data collected.
                File passport = new File(context.getFilesDir(), PASSPORT_DIAGNOSTIC_FILE);
                if (passport.isFile() && passport.length() > 0) {
                    output.write(("\nevent=PASSPORT_LOG_SECTION;origin=CLONE_PASSPORT;"
                        + "error=START;thread=MAIN\n").getBytes(StandardCharsets.UTF_8));
                    try (InputStream second = new FileInputStream(passport)) {
                        while ((read = second.read(buffer)) != -1)
                            output.write(buffer, 0, read);
                    }
                }
                output.flush();
            }
            ContentValues ready = new ContentValues();
            ready.put(MediaStore.MediaColumns.IS_PENDING, 0);
            resolver.update(target, ready, null, null);
            complete = true;
            return target;
        } finally {
            if (!complete) {
                try { resolver.delete(target, null, null); }
                catch (Throwable ignored) { }
            }
        }
    }

    private static String safeDiagnosticToken(String value) {
        if (value == null) return "UNKNOWN";
        String clean = value.replaceAll("[^A-Z0-9_]", "_");
        if (clean.length() > 64) clean = clean.substring(0, 64);
        return clean.isEmpty() ? "UNKNOWN" : clean;
    }

    private static void appendLocalDiagnosticEvent(String line) {
        Context context = diagnosticContext;
        if (context == null || line == null) return;
        try {
            synchronized (DIAGNOSTIC_FILE_LOCK) {
                String name = isPassportProcess() ? PASSPORT_DIAGNOSTIC_FILE : DIAGNOSTIC_FILE;
                File file = new File(context.getFilesDir(), name);
                if (file.exists() && file.length() > MAX_DIAGNOSTIC_FILE_BYTES) {
                    byte[] old = new byte[(int) Math.min(file.length(), 128L * 1024L)];
                    try (FileInputStream input = new FileInputStream(file)) {
                        int offset = 0;
                        while (offset < old.length) {
                            int read = input.read(old, offset, old.length - offset);
                            if (read < 0) break;
                            offset += read;
                        }
                    }
                    int start = Math.max(0, old.length - 32 * 1024);
                    while (start < old.length && old[start] != (byte) '\n') start++;
                    try (FileOutputStream output = new FileOutputStream(file, false)) {
                        output.write("event=LOG_TRIMMED;origin=LOCAL_FILE;error=KEEP_LAST_32KB;thread=OTHER\n"
                            .getBytes(StandardCharsets.UTF_8));
                        if (start < old.length) output.write(old, start, old.length - start);
                    }
                }
                try (FileOutputStream output = new FileOutputStream(file, true)) {
                    output.write(line.getBytes(StandardCharsets.UTF_8));
                    output.write('\n');
                    output.flush();
                }
            }
        } catch (Throwable ignored) { }
    }

    private static void emit(String event, String origin, String error) {
        String process = Application.getProcessName();
        if (!PACKAGE.equals(process) && !PASSPORT_PROCESS.equals(process)) return;
        String thread = "OTHER";
        try {
            if (Looper.getMainLooper() != null &&
                    Thread.currentThread() == Looper.getMainLooper().getThread())
                thread = "MAIN";
        } catch (Throwable ignored) { }
        // Entire message is finite enums; never stringifies a Throwable.
        String line = "event=" + safeDiagnosticToken(event) +
            ";origin=" + safeDiagnosticToken(origin) +
            ";error=" + safeDiagnosticToken(error) + ";thread=" + thread;
        Log.i(TAG, line);
        // Keep readAt hot-path instrumentation memory-light: audio-read events
        // remain in logcat but are not synchronously written to flash storage.
        if (!"MEDIA_DS_READ".equals(event) &&
                !"MEDIA_DS_SOURCE".equals(event) &&
                !"MEDIA_DS_EXTRACTOR_LINK".equals(event) &&
                !"MEDIA_EXTRACTOR_SOURCE".equals(event))
            appendLocalDiagnosticEvent(line);
    }
}
