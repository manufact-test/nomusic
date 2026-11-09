package pro.celikom.armv7loaderhost;
public final class AudioSmokeSource {
    public static final int A_ORIGINAL=0, A_ALT=1, B_ORIGINAL=2;
    private AudioSmokeSource(){}
    /** Dedicated in-process pre-prepare contract; only our lab can hook this. */
    public static int chooseA(){return A_ORIGINAL;}
    public static int originalA(){return A_ORIGINAL;}
    public static int originalB(){return B_ORIGINAL;}
    public static boolean valid(int x){return x>=0&&x<=2;}
    public static byte[] wave(int variant){
        if(!valid(variant))throw new IllegalArgumentException("UNKNOWN_SYNTHETIC_SOURCE");
        int hz=variant==A_ALT?660:variant==B_ORIGINAL?330:440;
        int rate=16000, samples=rate*8, length=samples*2;
        byte[] d=new byte[44+length];
        text(d,0,"RIFF");num32(d,4,36+length);text(d,8,"WAVE");
        text(d,12,"fmt ");num32(d,16,16);num16(d,20,1);num16(d,22,1);
        num32(d,24,rate);num32(d,28,rate*2);num16(d,32,2);num16(d,34,16);
        text(d,36,"data");num32(d,40,length);
        for(int i=0;i<samples;i++){
            double fade=Math.min(1.0, Math.min(i,samples-i-1)/800.0);
            short sample=(short)(Math.sin(2*Math.PI*hz*i/rate)*4200*fade);
            num16(d,44+i*2,sample);
        }
        return d;
    }
    private static void text(byte[] d,int at,String s){for(int i=0;i<s.length();i++)d[at+i]=(byte)s.charAt(i);}
    private static void num16(byte[] d,int at,int x){d[at]=(byte)x;d[at+1]=(byte)(x>>>8);}
    private static void num32(byte[] d,int at,int x){num16(d,at,x);num16(d,at+2,x>>>16);}
}
