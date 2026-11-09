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
        System.out.println("PASS: exact host, legacy/modern method fingerprints, no fuzzy fallback");
    }
}
