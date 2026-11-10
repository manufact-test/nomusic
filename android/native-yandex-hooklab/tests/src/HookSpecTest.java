import java.lang.reflect.Method;
import pro.celikom.yandex.nativehooklab.HookSpec;
public final class HookSpecTest {
    public static void main(String[] args) throws Exception {
        if (!HookSpec.isApprovedHost("ru.yandex.music", "2026.10.3 #170gpr", 24026531L))
            throw new AssertionError("exact signed host must pass");
        if (HookSpec.isApprovedHost("ru.yandex.music", "2026.10.3 #170rur", 24026531L)
                || HookSpec.isApprovedHost("org.clone.yandex", "2026.10.3 #170gpr", 24026531L)
                || HookSpec.isApprovedHost("ru.yandex.music", "2026.10.3 #170gpr", 12L))
            throw new AssertionError("nonmatching hosts must fail closed");
        ClassLoader loader = HookSpecTest.class.getClassLoader();
        Method modern = HookSpec.findConversion(loader, "y0", HookSpec.FILE_DTO);
        Method old = HookSpec.findConversion(loader, "z0", HookSpec.OLD_FILE_DTO);
        if (!modern.getReturnType().getName().equals("eed")
                || !old.getReturnType().getName().equals("eed")
                || !modern.getParameterTypes()[1].equals(boolean.class))
            throw new AssertionError("return/argument mismatch");
        boolean rejected = false;
        try { HookSpec.findConversion(loader, "y0", HookSpec.OLD_FILE_DTO); }
        catch (NoSuchMethodException expected) { rejected = true; }
        if (!rejected) throw new AssertionError("approximate hook must fail");
        HookSpec.ResolvedPair pair = HookSpec.findConversionPair(loader, loader);
        if (pair.loader != loader || !pair.modern.equals(modern) || !pair.legacy.equals(old))
            throw new AssertionError("preferred exact host loader did not resolve both converters");

        ClassLoader missing = new ClassLoader(null) {};
        HookSpec.ResolvedPair fallback = HookSpec.findConversionPair(missing, loader);
        if (fallback.loader != loader || !fallback.modern.equals(modern) || !fallback.legacy.equals(old))
            throw new AssertionError("ready loader fallback did not use exact verified Context loader");

        HookSpec.ResolvedPair noPreferred = HookSpec.findConversionPair(null, loader);
        if (noPreferred.loader != loader)
            throw new AssertionError("context class loader missing when no ready loader given");

        boolean missingPairRejected = false;
        try { HookSpec.findConversionPair(missing, missing); }
        catch (ClassNotFoundException | NoSuchMethodException expected) {
            missingPairRejected = true;
        }
        if (!missingPairRejected)
            throw new AssertionError("unresolved host loader must be rejected, not guessed");
        System.out.println("PASS: exact paired model hooks, classloader fallback, unresolved loader rejects");

        Method sourceModelAccessor = HookSpec.findModelStringAccessor(loader);
        if (!sourceModelAccessor.getName().equals("a")
                || !sourceModelAccessor.getReturnType().equals(String.class)
                || sourceModelAccessor.getParameterCount() != 0)
            throw new AssertionError("exact downstream model accessor contract");
        System.out.println("PASS: exact host, FileInfo conversions, optional eed accessor, no fuzzy fallback");
    }
}
