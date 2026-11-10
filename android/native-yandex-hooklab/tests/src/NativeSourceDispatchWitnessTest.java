import java.lang.reflect.Method;
import java.lang.reflect.Field;
import java.lang.reflect.Constructor;
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

        Constructor<?>[] exactCtors=HookSpec.findLeroConstructors(loader);
        yes(exactCtors.length==2
                    && exactCtors[0].getParameterTypes().length==2
                    && exactCtors[1].getParameterTypes().length==3
                    && exactCtors[0].getParameterTypes()[0]==wzi.class
                    && exactCtors[1].getParameterTypes()[1]==ga4.class,
            "both Lero constructors directly observed, not only kvs.A factory");
        Field leroReader=HookSpec.findLeroReaderField(loader);
        yes(leroReader.getType()==mb4.class
                    &&leroReader.getDeclaringClass()==ero.class,
                "one exact typed Lero->Lmb4 reference");
        Method loaderBody=HookSpec.findReaderExecution(loader);
        yes(loaderBody.getParameterCount()==0
                &&loaderBody.getReturnType()==void.class,
                "one exact Lmb4.a no-arg reader execution");
        for(String op:new String[]{"b","read","close"}){
            Method method=HookSpec.findReaderSourceMethod(loader,op);
            yes(method.getDeclaringClass()==ha4.class,
                    "exact concrete ha4 operation "+op);
        }
        try {
            HookSpec.findReaderSourceMethod(loader,"getUri");
            throw new AssertionError("unknown source method accepted");
        }catch(NoSuchMethodException expected){tests++;}

        NativeSourceDispatchWitness link=new NativeSourceDispatchWitness();
        ero factorySource=new ero();
        ero unrelated=new ero();
        mb4 exact=(mb4)leroReader.get(factorySource);
        link.onFactory(factorySource,1000);
        yes(!link.onOwnedReader(factorySource,exact,1001),
                "reader cannot link before source t() starts");
        link.onLifecycleT(factorySource,1002);
        yes(link.onOwnedReader(factorySource,exact,1003),
                "factory Lero->t->typed Lmb4 linked");
        yes(!link.onCompletedReader((mb4)leroReader.get(unrelated),1004),
                "different reader rejected despite identical class");
        yes(link.onCompletedReader(exact,1005),
                "exact reader completion linked to factory source");
        link.onRemove(factorySource,1006);
        yes(!link.onCompletedReader(exact,1007),
                "remove evicts historical source-reader association");
        yes(!link.onOwnedReader(unrelated,(mb4)leroReader.get(unrelated),1010),
                "background Lero was not factory observed");
        ero stale=new ero();
        link.onFactory(stale,2000);
        link.onLifecycleT(stale,2001);
        yes(link.onOwnedReader(stale,(mb4)leroReader.get(stale),2002),
                "second owned source attached");
        yes(!link.onCompletedReader((mb4)leroReader.get(stale),17003),
                "reader assignment expires after bounded window");
        yes(link.snapshot().sourceReaderLinks==2
                &&link.snapshot().completedReaderChains==1,
                "strict reference counts without audio or identifier data");

        // Direct Locv.i0-like Lero construction bypasses the kvs.A factory.
        // It must be observed, but never treated as a player selection.
        NativeSourceDispatchWitness direct=new NativeSourceDispatchWitness();
        Object fromLocv=exactCtors[1].newInstance(new wzi(),new ga4(),new Object());
        Object fromShort=exactCtors[0].newInstance(new wzi(),new ga4());
        direct.onConstructed(fromLocv,250);
        direct.onConstructed(fromShort,251);
        direct.onLifecycleT(fromLocv,252);
        direct.onLifecycleT(fromShort,253);
        yes(direct.snapshot().constructors==2
                &&direct.snapshot().constructedTCalls==2
                &&direct.snapshot().factoryTCalls==0,
                "direct constructors known, no fictitious factory use");
        yes(direct.onOwnedReader(fromLocv,(mb4)leroReader.get(fromLocv),254),
                "direct Locv source reaches exact typed reader without kvs.A");
        yes(direct.onCompletedReader((mb4)leroReader.get(fromLocv),255),
                "direct-constructed reader evidence is tracked separately");
        direct.onFactory(fromLocv,256);
        yes(direct.snapshot().factories==1
                &&direct.snapshot().constructors==2,
                "factory provenance merge does not fake another constructor");
        direct.onRemove(fromLocv,257);
        yes(!direct.onCompletedReader((mb4)leroReader.get(fromLocv),258),
                "remove cancels direct source identity before completion");
        yes(!direct.onOwnedReader(new ero(),new mb4(),259),
                "neither constructor nor factory tracking accepts unobserved source");

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
