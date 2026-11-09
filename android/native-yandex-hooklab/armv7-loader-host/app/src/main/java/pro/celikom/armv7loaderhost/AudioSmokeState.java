package pro.celikom.armv7loaderhost;
public final class AudioSmokeState {
    private static volatile boolean hookArmed, sourceSwapped;
    private AudioSmokeState(){}
    public static void arm(){hookArmed=true;}
    public static void swap(){sourceSwapped=true;}
    public static boolean armed(){return hookArmed;}
    public static boolean swapped(){return sourceSwapped;}
}
