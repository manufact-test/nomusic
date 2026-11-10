import java.lang.reflect.Method;
import pro.celikom.yandex.nativehooklab.HookSpec;
import pro.celikom.yandex.nativehooklab.NativeSourceDispatchWitness;

public final class NativeSourceDispatchWitnessTest {
    private static int tests;
    private static void yes(boolean v,String why) {
        tests++;
        if(!v)throw new AssertionError(why+" (#"+tests+")");
    }
    public static void main(String[] args) throws Exception {
        ClassLoader loader=NativeSourceDispatchWitnessTest.class.getClassLoader();
        Method factory=HookSpec.findSourceFactory(loader);
        yes(factory.getName().equals("A")&&factory.getParameterTypes()[0]==zcb.class
                    &&factory.getParameterTypes()[1]==gmb.class
                    &&factory.getReturnType()==emb.class,
            "factory exact descriptor, not swapped-overload");
        for(String name:HookSpec.SOURCE_IMPLEMENTORS) {
            Method t=HookSpec.findSourceLifecycle(loader,name,"t");
            Method remove=HookSpec.findSourceLifecycle(loader,name,"remove");
            yes(t.getParameterCount()==1&&t.getParameterTypes()[0]==dmb.class
                &&t.getReturnType()==void.class,"exact t signature "+name);
            yes(remove.getParameterCount()==0&&remove.getReturnType()==void.class,
                "exact remove signature "+name);
        }
        try {
            HookSpec.findSourceLifecycle(loader,"kvs","t");
            throw new AssertionError("untrusted receiver unexpectedly allowed");
        } catch(NoSuchMethodException expected){tests++;}
        try {
            HookSpec.findSourceLifecycle(loader,"ero","decode");
            throw new AssertionError("untrusted method unexpectedly allowed");
        } catch(NoSuchMethodException expected){tests++;}

        NativeSourceDispatchWitness w=new NativeSourceDispatchWitness();
        Object selected=new ero();
        Object prefetch=new ero();
        Object unknown=new Object();
        w.onFactory(selected,100);
        w.onLifecycleT(prefetch,101);
        w.onLifecycleT(selected,102);
        w.onRemove(selected,103);
        w.onLifecycleT(selected,104);
        w.onFactory(unknown,105);
        w.onLifecycleT(unknown,106);
        NativeSourceDispatchWitness.Snapshot s=w.snapshot();
        yes(s.factories==1&&s.lifecycleCalls==3&&s.matchedCalls==1
                &&s.unmatchedCalls==2&&s.removals==1&&s.rejectedUnknown==2,
                "same CLASS is insufficient: only same reference counted");

        Object expired=new alt();
        w.onFactory(expired,200);
        w.onLifecycleT(expired,15201);
        yes(w.snapshot().matchedCalls==1,
            "expired factory identity cannot be resurrected");
        Object rollback=new chg();
        w.onFactory(rollback,16000);
        w.onLifecycleT(rollback,15000);
        yes(w.snapshot().clockDiscontinuities>=1,
            "monotonic clock rollback expires identity");
        Object next=new ero();
        w.onFactory(next,20000);
        w.onLifecycleT(selected,20001);
        w.onLifecycleT(next,20002);
        yes(w.snapshot().matchedCalls==2,
            "NEXT different instance must not be misattributed to previous");
        for(int i=0;i<10000;i++) {
            Object item=new ero();
            long time=30000L+i*3L;
            w.onFactory(item,time);
            w.onLifecycleT(item,time+1L);
            w.onRemove(item,time+2L);
            yes(w.snapshot().matchedCalls==i+3,
                "unique same-instance factory/open/close cycle "+i);
        }
        System.out.println("PASS: "+tests+
            " exact native Lemb factory/lifecycle reflection and reference-only"
            +" read-only events; NOT a selected live player / decoder witness");
    }
}
