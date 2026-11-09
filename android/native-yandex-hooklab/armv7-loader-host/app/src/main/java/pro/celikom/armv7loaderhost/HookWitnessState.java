package pro.celikom.armv7loaderhost;

/** In-process non-sensitive witness flags; no disk, network, logs or permissions. */
public final class HookWitnessState {
    private static volatile boolean hookArmed;
    private static volatile boolean entryIntercepted;
    private HookWitnessState() {}
    public static void markArmed() { hookArmed = true; }
    public static void markIntercepted() { entryIntercepted = true; }
    public static boolean armed() { return hookArmed; }
    public static boolean intercepted() { return entryIntercepted; }
}
