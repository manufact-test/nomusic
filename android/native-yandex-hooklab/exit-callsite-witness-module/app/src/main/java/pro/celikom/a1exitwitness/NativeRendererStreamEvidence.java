package pro.celikom.a1exitwitness;

import java.lang.ref.WeakReference;
import java.util.ArrayList;

/**
 * NAV17 / signed 2025.10.4 only. Passive, in-process identities for exact
 * LmQ8.catch -> androidx.media3.exoplayer.b.package -> b.g -> LR29.read.
 *
 * This never opens, reads or persists stream contents or private metadata.
 * Reference equality is ONLY Java ==; no equals/hashCode/toString is called.
 * This is NOT a currently selected track/edition or audible decoder proof.
 */
final class NativeRendererStreamEvidence {
    private static final int MAX_HANDLES = 12;
    private static final int MAX_HOT_READ_OBSERVATIONS = 256;
    private static final int MAX_READS_PER_ATTACH = 8;
    private static final int MAX_COUNT = 1000;

    static final class Scope {
        final Object renderer, holder;
        final Scope parent;
        Scope(Object renderer, Object holder, Scope parent) {
            this.renderer=renderer;
            this.holder=holder;
            this.parent=parent;
        }
    }
    private static final class Link {
        final WeakReference<Object> renderer, holder, stream;
        Link(Object renderer,Object holder,Object stream) {
            this.renderer=new WeakReference<>(renderer);
            this.holder=new WeakReference<>(holder);
            this.stream=new WeakReference<>(stream);
        }
    }

    private final ThreadLocal<Scope> inAttach = new ThreadLocal<>();
    private final ArrayList<Link> links = new ArrayList<>();
    // Unscoped renderer/stream observations are separate: never infer holder identity.
    private final ArrayList<Link> unscopedLinks = new ArrayList<>();
    // 0 not attempted/guarded, 1 registered, -1 failed.
    private int queueHook, attachHook, readHook, detachHook;
    private int scopeEnters, pairedAttaches, unknownAttaches, attachConflicts;
    private int readSame, readDifferent, readUnknown, detachCount;
    private int unscopedReadSame, unscopedReadDifferent;
    private int totalReadObservations;
    private int readSamplesRemaining = 8;
    private boolean poisoned;

    Scope enter(Object renderer,Object holder) {
        Scope frame=new Scope(renderer,holder,inAttach.get());
        inAttach.set(frame);
        synchronized(this) { scopeEnters=inc(scopeEnters); }
        return frame;
    }
    void exit(Scope scope) {
        Scope active=inAttach.get();
        if (active==scope) {
            if (scope.parent==null) inAttach.remove();
            else inAttach.set(scope.parent);
        } else {
            // Fail closed. Never let an incomplete scope attest identity.
            inAttach.remove();
            synchronized(this) { poisoned=true; }
        }
    }

    synchronized void onHookRegistration(String kind, boolean ok) {
        int status=ok?1:-1;
        switch(kind) {
            case "QUEUE_SCOPE": queueHook=status; break;
            case "STREAM_ATTACH": attachHook=status; break;
            case "SAMPLE_READ": readHook=status; break;
            case "STREAM_DETACH": detachHook=status; break;
            default: throw new IllegalArgumentException("Unrecognized hook kind");
        }
    }

    synchronized void onAttach(Object renderer,Object stream) {
        Scope scope=inAttach.get();
        if (poisoned || scope==null || renderer==null || stream==null
                || scope.renderer!=renderer || scope.holder==null) {
            unknownAttaches=inc(unknownAttaches);
            // Attaches without an observed queue scope still allow a weaker
            // renderer→stream→read same-reference check, never holder identity.
            if(!poisoned && renderer!=null && stream!=null) {
                removeRenderer(unscopedLinks,renderer);
                removeRenderer(links,renderer);
                if(unscopedLinks.size()>=MAX_HANDLES)unscopedLinks.remove(0);
                unscopedLinks.add(new Link(renderer,null,stream));
                readSamplesRemaining=MAX_READS_PER_ATTACH;
            }
            return;
        }
        removeRenderer(unscopedLinks,renderer);
        for(int i=links.size()-1;i>=0;i--) {
            Link old=links.get(i);
            Object candidate=old.renderer.get();
            if(candidate==null || old.holder.get()==null || old.stream.get()==null) {
                links.remove(i); continue;
            }
            if(candidate==renderer) {
                // Transition and prepare may attach a different stream.
                if(old.holder.get()!=scope.holder || old.stream.get()!=stream)
                    attachConflicts=inc(attachConflicts);
                links.remove(i);
            }
        }
        if (links.size()>=MAX_HANDLES) links.remove(0);
        links.add(new Link(renderer,scope.holder,stream));
        pairedAttaches=inc(pairedAttaches);
        readSamplesRemaining=MAX_READS_PER_ATTACH;
    }

    private static void removeRenderer(ArrayList<Link> list,Object renderer) {
        for(int i=list.size()-1;i>=0;i--) {
            Object existing=list.get(i).renderer.get();
            if(existing==null || existing==renderer)list.remove(i);
        }
    }

    synchronized boolean shouldSampleRead() {
        if (poisoned || totalReadObservations>=MAX_HOT_READ_OBSERVATIONS
                || readSamplesRemaining<=0) return false;
        totalReadObservations++;
        readSamplesRemaining--;
        return true;
    }

    synchronized void onRead(Object renderer,Object actualFieldStream) {
        if (poisoned || renderer==null || actualFieldStream==null) {
            readUnknown=inc(readUnknown);
            return;
        }
        Link matched=null;
        for(int i=links.size()-1;i>=0;i--) {
            Link link=links.get(i);
            Object candidate=link.renderer.get();
            if(candidate==null || link.stream.get()==null || link.holder.get()==null) {
                links.remove(i);
            } else if(candidate==renderer) {
                if(matched!=null) { poisoned=true; return; }
                matched=link;
            }
        }
        if(matched==null) {
            // A weaker unscoped match cannot increment QUEUED_HOLDER_ATTACHED
            // or ATTACHED_STREAM_READ_MATCH: holder is not established.
            Link unscoped=null;
            for(int i=unscopedLinks.size()-1;i>=0;i--) {
                Link link=unscopedLinks.get(i);
                Object candidate=link.renderer.get();
                if(candidate==null || link.stream.get()==null) {
                    unscopedLinks.remove(i);
                } else if(candidate==renderer) {
                    if(unscoped!=null) { poisoned=true; return; }
                    unscoped=link;
                }
            }
            if(unscoped==null)readUnknown=inc(readUnknown);
            else if(unscoped.stream.get()==actualFieldStream)
                unscopedReadSame=inc(unscopedReadSame);
            else unscopedReadDifferent=inc(unscopedReadDifferent);
        } else if(matched.stream.get()==actualFieldStream) {
            readSame=inc(readSame);
        } else {
            readDifferent=inc(readDifferent);
        }
    }

    synchronized void onDetach(Object renderer) {
        if(renderer==null)return;
        removeRenderer(links,renderer);
        removeRenderer(unscopedLinks,renderer);
        detachCount=inc(detachCount);
    }

    private static int inc(int value) { return Math.min(MAX_COUNT,value+1); }
    private static String band(int value) {
        if(value==0)return "NONE";
        if(value==1)return "ONE";
        if(value<=8)return "FEW";
        return "MANY";
    }
    private static String registrationLine(String category,int status) {
        return "event=AUDIO_NATIVE_RENDERER_HOOK_STATUS;origin="+category
            +";error="+(status>0?"REGISTERED":status<0?"NO_HOOK":"NOT_SEEN")
            +";thread=OTHER";
    }
    private static String line(String category,int value) {
        return "event=AUDIO_NATIVE_RENDERER_SUMMARY;origin=" + category
            + ";error=" + band(value) + ";thread=OTHER";
    }

    synchronized String[] exportLines() {
        // Only fixed finite enums leave MAIN. No raw objects, names or audio.
        return new String[] {
            registrationLine("QUEUE_SCOPE",queueHook),
            registrationLine("STREAM_ATTACH",attachHook),
            registrationLine("SAMPLE_READ",readHook),
            registrationLine("STREAM_DETACH",detachHook),
            line("QUEUE_SCOPE_ENTER",scopeEnters),
            line("QUEUED_HOLDER_ATTACHED",pairedAttaches),
            line("UNSCOPED_ATTACH",unknownAttaches),
            line("STREAM_REATTACH_TRANSITION",attachConflicts),
            line("ATTACHED_STREAM_READ_MATCH",readSame),
            line("ATTACHED_STREAM_READ_DIFFERENT",readDifferent),
            line("UNSCOPED_ATTACHED_STREAM_READ_MATCH",unscopedReadSame),
            line("UNSCOPED_ATTACHED_STREAM_READ_DIFFERENT",unscopedReadDifferent),
            line("READ_NO_MATCHED_ATTACHMENT",readUnknown),
            line("RENDERER_DETACHED",detachCount),
            "event=AUDIO_NATIVE_RENDERER_SUMMARY;origin=IDENTITY_STATUS;error="
              + (poisoned ? "INVALID" : "STRUCTURAL_ONLY") + ";thread=OTHER"
        };
    }
}
