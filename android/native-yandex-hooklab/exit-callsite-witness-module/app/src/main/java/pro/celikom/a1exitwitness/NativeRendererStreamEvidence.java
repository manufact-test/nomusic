package pro.celikom.a1exitwitness;

import java.lang.ref.WeakReference;
import java.lang.reflect.Array;
import java.lang.reflect.Field;
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
    /**
     * A second, exact 2025 renderer attachment caller: b.super(lQ8, formats,
     * LR29, flags...). Counts callsite relation only, never source contents.
     * This is a caller discriminator, NOT an active-audio assertion.
     */
    static final class CallerFrame {
        final Object renderer, stream;
        final CallerFrame parent;
        CallerFrame(Object renderer,Object stream,CallerFrame parent) {
            this.renderer=renderer;
            this.stream=stream;
            this.parent=parent;
        }
    }
    /** Signed 2025 Exo engine e.catch(Lxh6;IZJ)V holder lifetime only. */
    static final class EngineFrame {
        final Object holder;
        final EngineFrame parent;
        EngineFrame(Object holder,EngineFrame parent) {
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
    private final ThreadLocal<CallerFrame> inSecondaryCaller = new ThreadLocal<>();
    private final ThreadLocal<EngineFrame> inEngineEnable = new ThreadLocal<>();
    private Field engineHolderStreamArrayField;
    private final ArrayList<Link> engineHolderLinks = new ArrayList<>();
    private final ArrayList<Link> links = new ArrayList<>();
    // Unscoped renderer/stream observations are separate: never infer holder identity.
    private final ArrayList<Link> unscopedLinks = new ArrayList<>();
    // 0 not attempted/guarded, 1 registered, -1 failed.
    private int queueHook, attachHook, readHook, detachHook, secondaryCallerHook, engineScopeHook;
    private int engineEnters, engineHolderStreamMatch, engineHolderStreamDifferent;
    private int engineHolderArrayUnavailable, engineReadMinus4, engineReadMinus5;
    private int engineReadMinus3, engineReadOther;
    // NAV24 additional *original method* values: renderer kind 1 and state 2
    // observed on the exact same strict engine-holder-to-read link.
    // Numbers alone do not attest audible PCM, selected track or edition.
    private int typeStateAccessHook, bufferEosAccessHook, engineRendererType1, engineRendererTypeOther;
    private int engineType1State2, engineType1StateOther, engineTypeStateUnavailable;
    private int engineAudioState2Minus4, engineAudioState2Minus5;
    private int engineAudioState2Minus3, engineAudioState2Other;
    // NAV25: the original RF2 buffer's inherited EOS flag, never payload.
    // Non-EOS is a read-buffer witness only, NOT audible PCM or track identity.
    private int engineAudioState2BufferNonEos, engineAudioState2BufferEos;
    private int engineAudioState2BufferUnavailable;
    private int secondaryCallerEnters, secondaryCallerStreamMatches, secondaryCallerStreamDiffers;
    private int unscopedSecondaryMatches, unscopedOutsideSecondary, unscopedSecondaryDiffers;
    private int scopeEnters, pairedAttaches, unknownAttaches, attachConflicts;
    private int readSame, readDifferent, readUnknown, detachCount;
    private int unscopedReadSame, unscopedReadDifferent;
    // Return code of original b.g(), only after a matching attached stream
    // remains present across the call. -4 can also be EOS; never claim audible PCM.
    private int returnMinus4,returnMinus5,returnMinus3,returnOther,returnUnlinked;
    // Separate real queue-holder-scoped returns from weaker unscoped aliases.
    // NAV20 aggregated these, so its MANY(-4) could all be unscoped.
    private int strongMinus4,strongMinus5,strongMinus3,strongOther;
    private int weakMinus4,weakMinus5,weakMinus3,weakOther;
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

    CallerFrame enterSecondaryCaller(Object renderer,Object stream) {
        CallerFrame frame=new CallerFrame(renderer,stream,inSecondaryCaller.get());
        inSecondaryCaller.set(frame);
        synchronized(this) { secondaryCallerEnters=inc(secondaryCallerEnters); }
        return frame;
    }

    void exitSecondaryCaller(CallerFrame frame) {
        CallerFrame active=inSecondaryCaller.get();
        if(active==frame) {
            if(frame.parent==null) inSecondaryCaller.remove();
            else inSecondaryCaller.set(frame.parent);
        } else {
            // Never allow broken nested callsite lifetimes to attest identity.
            inSecondaryCaller.remove();
            synchronized(this) { poisoned=true; }
        }
    }

    /**
     * A version-locked, one-time reflection handle to the Lxh6.[LR29 field.
     * Caller verifies its exact declared type and uniqueness before install.
     * No stream contents or private member values are serialized.
     */
    synchronized void setEngineHolderStreamArrayField(Field field) {
        if(field==null || !field.getType().isArray())
            throw new IllegalArgumentException("Exact holder stream array required");
        engineHolderStreamArrayField=field;
    }

    EngineFrame enterEngine(Object holder) {
        EngineFrame frame=new EngineFrame(holder,inEngineEnable.get());
        inEngineEnable.set(frame);
        synchronized(this) { engineEnters=inc(engineEnters); }
        return frame;
    }

    void exitEngine(EngineFrame frame) {
        EngineFrame active=inEngineEnable.get();
        if(active==frame) {
            if(frame.parent==null) inEngineEnable.remove();
            else inEngineEnable.set(frame.parent);
        } else {
            inEngineEnable.remove();
            synchronized(this) { poisoned=true; }
        }
    }

    // Result: 1 exact object member, -1 safely checked but different,
    // 0 unavailable/ambiguous; never infer membership from call nesting alone.
    private int holderArrayHasStream(Object holder,Object stream) {
        Field field=engineHolderStreamArrayField;
        if(holder==null || stream==null || field==null) return 0;
        try {
            Object array=field.get(holder);
            if(array==null || !array.getClass().isArray())return 0;
            int n=Array.getLength(array);
            if(n>32)return 0;
            for(int i=0;i<n;i++)if(Array.get(array,i)==stream)return 1;
            return -1;
        } catch (Throwable ignored) { return 0; }
    }

    synchronized void onHookRegistration(String kind, boolean ok) {
        int status=ok?1:-1;
        switch(kind) {
            case "QUEUE_SCOPE": queueHook=status; break;
            case "STREAM_ATTACH": attachHook=status; break;
            case "SAMPLE_READ": readHook=status; break;
            case "STREAM_DETACH": detachHook=status; break;
            case "SECONDARY_CALLER": secondaryCallerHook=status; break;
            case "ENGINE_HOLDER_SCOPE": engineScopeHook=status; break;
            case "RENDERER_TYPE_STATE_ACCESS": typeStateAccessHook=status; break;
            case "BUFFER_EOS_ACCESS": bufferEosAccessHook=status; break;
            default: throw new IllegalArgumentException("Unrecognized hook kind");
        }
    }

    synchronized void onAttach(Object renderer,Object stream) {
        Scope scope=inAttach.get();
        boolean strongScope=!poisoned && scope!=null && renderer!=null && stream!=null
            && scope.renderer==renderer && scope.holder!=null;
        CallerFrame secondary=inSecondaryCaller.get();
        EngineFrame engine=inEngineEnable.get();
        // Any reattach invalidates the previous engine-to-holder reference.
        // Only a fresh exact membership check may create a new engine link.
        if(renderer!=null)removeRenderer(engineHolderLinks,renderer);
        if(!poisoned && engineScopeHook>0 && engine!=null
                && secondary!=null && secondary.renderer==renderer
                && secondary.stream==stream && renderer!=null && stream!=null) {
            int member=holderArrayHasStream(engine.holder,stream);
            if(member==1) {
                engineHolderStreamMatch=inc(engineHolderStreamMatch);
                if(engineHolderLinks.size()>=MAX_HANDLES)engineHolderLinks.remove(0);
                engineHolderLinks.add(new Link(renderer,engine.holder,stream));
            } else if(member<0) {
                engineHolderStreamDifferent=inc(engineHolderStreamDifferent);
            } else {
                engineHolderArrayUnavailable=inc(engineHolderArrayUnavailable);
            }
        }
        // The secondary caller has no queue-holder identity by itself.
        // Its same-reference link tells us which exact attach route ran.
        if(!poisoned && secondary!=null && secondary.renderer==renderer) {
            if(stream!=null && secondary.stream==stream) {
                secondaryCallerStreamMatches=inc(secondaryCallerStreamMatches);
                if(!strongScope) unscopedSecondaryMatches=inc(unscopedSecondaryMatches);
            } else {
                secondaryCallerStreamDiffers=inc(secondaryCallerStreamDiffers);
                if(!strongScope) unscopedSecondaryDiffers=inc(unscopedSecondaryDiffers);
            }
        } else if(!poisoned && !strongScope && secondary==null
                  && secondaryCallerHook>0 && renderer!=null && stream!=null) {
            // With the second caller hook registered, this was outside that
            // observed scope. It is not proof of an unknown third caller.
            unscopedOutsideSecondary=inc(unscopedOutsideSecondary);
        }
        if (!strongScope) {
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

    synchronized void onReadReturn(Object renderer,Object observedStream,int originalResult) {
        if (poisoned || renderer==null || observedStream==null) {
            returnUnlinked=inc(returnUnlinked);
            return;
        }
        boolean strong=false,weak=false;
        for (Link link:links) {
            if (link.renderer.get()==renderer && link.holder.get()!=null
                    && link.stream.get()==observedStream) { strong=true; break; }
        }
        if (!strong) for (Link link:unscopedLinks) {
            if (link.renderer.get()==renderer
                    && link.stream.get()==observedStream) { weak=true; break; }
        }
        if(!strong && !weak) {
            returnUnlinked=inc(returnUnlinked);
            return;
        }
        // Engine holder is an independent proof cohort: never elevate it to
        // QUEUE_SCOPED counters or audible PCM. Exact holder-array membership,
        // secondary stream alias, and unchanged renderer stream must all match.
        boolean engineMatch=false;
        for(Link link:engineHolderLinks) {
            if(link.renderer.get()==renderer && link.holder.get()!=null
                    && link.stream.get()==observedStream) {
                engineMatch=true;
                break;
            }
        }
        if(engineMatch) {
            switch(originalResult) {
                case -4:engineReadMinus4=inc(engineReadMinus4);break;
                case -5:engineReadMinus5=inc(engineReadMinus5);break;
                case -3:engineReadMinus3=inc(engineReadMinus3);break;
                default:engineReadOther=inc(engineReadOther);break;
            }
        }
        // Preserve NAV20 aggregate read-return bins, but never use them
        // as proof of a queue-scoped holder. A queued holder is strict only
        // if it remains bound at the exact return point.
        switch(originalResult) {
            case -4:
                returnMinus4=inc(returnMinus4);
                if(strong)strongMinus4=inc(strongMinus4);
                else weakMinus4=inc(weakMinus4);
                break;
            case -5:
                returnMinus5=inc(returnMinus5);
                if(strong)strongMinus5=inc(strongMinus5);
                else weakMinus5=inc(weakMinus5);
                break;
            case -3:
                returnMinus3=inc(returnMinus3);
                if(strong)strongMinus3=inc(strongMinus3);
                else weakMinus3=inc(weakMinus3);
                break;
            default:
                returnOther=inc(returnOther);
                if(strong)strongOther=inc(strongOther);
                else weakOther=inc(weakOther);
                break;
        }
    }

    /**
     * NAV24: READ-ONLY status of the original 2025 b.default()I and
     * b.getState()I after untouched original b.g. Only an already verified
     * matching engine holder/renderer stream may count.
     * Track type 1 and state 2 are *numbers*, not audible output assertions.
     */
    synchronized void onRendererTypeStateRead(Object renderer,Object stream,
            int trackType,int state,int originalResult) {
        onRendererTypeStateRead(renderer,stream,trackType,state,originalResult,null);
    }

    synchronized void onRendererTypeStateRead(Object renderer,Object stream,
            int trackType,int state,int originalResult,Boolean endOfStream) {
        if(poisoned || typeStateAccessHook<=0 || renderer==null || stream==null)return;
        boolean matched=false;
        for(Link link:engineHolderLinks) {
            if(link.renderer.get()==renderer && link.holder.get()!=null
                    && link.stream.get()==stream) {
                matched=true;
                break;
            }
        }
        if(!matched)return;
        // A stale engine-only link cannot be counted if the actually sampled
        // original b.g stream no longer matches an attached stream alias.
        boolean attached=false;
        for(Link link:links) {
            if(link.renderer.get()==renderer && link.stream.get()==stream) {
                attached=true;
                break;
            }
        }
        if(!attached)for(Link link:unscopedLinks) {
            if(link.renderer.get()==renderer && link.stream.get()==stream) {
                attached=true;
                break;
            }
        }
        if(!attached)return;
        if(trackType!=1) {
            engineRendererTypeOther=inc(engineRendererTypeOther);
            return;
        }
        engineRendererType1=inc(engineRendererType1);
        if(state!=2) {
            engineType1StateOther=inc(engineType1StateOther);
            return;
        }
        engineType1State2=inc(engineType1State2);
        if(originalResult==-4) {
            // Only the original buffer flag, after a strict same-reference
            // started audio renderer+holder+stream match. Null means unreadable.
            if(bufferEosAccessHook<=0 || endOfStream==null)
                engineAudioState2BufferUnavailable=inc(engineAudioState2BufferUnavailable);
            else if(endOfStream.booleanValue())engineAudioState2BufferEos=inc(engineAudioState2BufferEos);
            else engineAudioState2BufferNonEos=inc(engineAudioState2BufferNonEos);
        }
        switch(originalResult) {
            case -4:engineAudioState2Minus4=inc(engineAudioState2Minus4);break;
            case -5:engineAudioState2Minus5=inc(engineAudioState2Minus5);break;
            case -3:engineAudioState2Minus3=inc(engineAudioState2Minus3);break;
            default:engineAudioState2Other=inc(engineAudioState2Other);break;
        }
    }

    synchronized void onRendererTypeStateUnavailable(Object renderer,Object stream) {
        if(poisoned || typeStateAccessHook<=0 || renderer==null || stream==null)return;
        for(Link link:engineHolderLinks) {
            if(link.renderer.get()==renderer && link.holder.get()!=null
                    && link.stream.get()==stream) {
                engineTypeStateUnavailable=inc(engineTypeStateUnavailable);
                return;
            }
        }
    }

    synchronized void onDetach(Object renderer) {
        if(renderer==null)return;
        removeRenderer(links,renderer);
        removeRenderer(unscopedLinks,renderer);
        removeRenderer(engineHolderLinks,renderer);
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
            registrationLine("SECONDARY_CALLER",secondaryCallerHook),
            registrationLine("ENGINE_HOLDER_SCOPE",engineScopeHook),
            registrationLine("RENDERER_TYPE_STATE_ACCESS",typeStateAccessHook),
            registrationLine("BUFFER_EOS_ACCESS",bufferEosAccessHook),
            line("QUEUE_SCOPE_ENTER",scopeEnters),
            line("SECONDARY_CALLER_ENTER",secondaryCallerEnters),
            line("ENGINE_HOLDER_SCOPE_ENTER",engineEnters),
            line("ENGINE_HOLDER_STREAM_ARRAY_MATCH",engineHolderStreamMatch),
            line("ENGINE_HOLDER_STREAM_ARRAY_DIFFERENT",engineHolderStreamDifferent),
            line("ENGINE_HOLDER_STREAM_ARRAY_UNAVAILABLE",engineHolderArrayUnavailable),
            line("ENGINE_HOLDER_READ_RETURN_MINUS4",engineReadMinus4),
            line("ENGINE_HOLDER_READ_RETURN_MINUS5",engineReadMinus5),
            line("ENGINE_HOLDER_READ_RETURN_MINUS3",engineReadMinus3),
            line("ENGINE_HOLDER_READ_RETURN_OTHER",engineReadOther),
            line("ENGINE_HOLDER_RENDERER_TYPE1",engineRendererType1),
            line("ENGINE_HOLDER_RENDERER_TYPE_OTHER",engineRendererTypeOther),
            line("ENGINE_HOLDER_TYPE1_STATE2",engineType1State2),
            line("ENGINE_HOLDER_TYPE1_STATE_NOT2",engineType1StateOther),
            line("ENGINE_HOLDER_TYPE_STATE_UNAVAILABLE",engineTypeStateUnavailable),
            line("ENGINE_AUDIO_TYPE1_STATE2_RETURN_MINUS4",engineAudioState2Minus4),
            line("ENGINE_AUDIO_TYPE1_STATE2_RETURN_MINUS5",engineAudioState2Minus5),
            line("ENGINE_AUDIO_TYPE1_STATE2_RETURN_MINUS3",engineAudioState2Minus3),
            line("ENGINE_AUDIO_TYPE1_STATE2_RETURN_OTHER",engineAudioState2Other),
            line("ENGINE_AUDIO_TYPE1_STATE2_BUFFER_NON_EOS",engineAudioState2BufferNonEos),
            line("ENGINE_AUDIO_TYPE1_STATE2_BUFFER_EOS",engineAudioState2BufferEos),
            line("ENGINE_AUDIO_TYPE1_STATE2_BUFFER_UNAVAILABLE",engineAudioState2BufferUnavailable),
            line("SECONDARY_CALLER_STREAM_MATCH",secondaryCallerStreamMatches),
            line("SECONDARY_CALLER_STREAM_DIFFERENT",secondaryCallerStreamDiffers),
            line("UNSCOPED_ATTACH_SECONDARY_MATCH",unscopedSecondaryMatches),
            line("UNSCOPED_ATTACH_SECONDARY_DIFFERENT",unscopedSecondaryDiffers),
            line("UNSCOPED_ATTACH_OUTSIDE_SECONDARY",unscopedOutsideSecondary),
            line("QUEUED_HOLDER_ATTACHED",pairedAttaches),
            line("UNSCOPED_ATTACH",unknownAttaches),
            line("STREAM_REATTACH_TRANSITION",attachConflicts),
            line("ATTACHED_STREAM_READ_MATCH",readSame),
            line("ATTACHED_STREAM_READ_DIFFERENT",readDifferent),
            line("UNSCOPED_ATTACHED_STREAM_READ_MATCH",unscopedReadSame),
            line("UNSCOPED_ATTACHED_STREAM_READ_DIFFERENT",unscopedReadDifferent),
            line("READ_NO_MATCHED_ATTACHMENT",readUnknown),
            line("STREAM_ALIASED_READ_RETURN_MINUS4",returnMinus4),
            line("STREAM_ALIASED_READ_RETURN_MINUS5",returnMinus5),
            line("STREAM_ALIASED_READ_RETURN_MINUS3",returnMinus3),
            line("STREAM_ALIASED_READ_RETURN_OTHER",returnOther),
            line("READ_RETURN_LINK_LOST",returnUnlinked),
            line("QUEUE_SCOPED_READ_RETURN_MINUS4",strongMinus4),
            line("QUEUE_SCOPED_READ_RETURN_MINUS5",strongMinus5),
            line("QUEUE_SCOPED_READ_RETURN_MINUS3",strongMinus3),
            line("QUEUE_SCOPED_READ_RETURN_OTHER",strongOther),
            line("UNSCOPED_READ_RETURN_MINUS4",weakMinus4),
            line("UNSCOPED_READ_RETURN_MINUS5",weakMinus5),
            line("UNSCOPED_READ_RETURN_MINUS3",weakMinus3),
            line("UNSCOPED_READ_RETURN_OTHER",weakOther),
            line("RENDERER_DETACHED",detachCount),
            "event=AUDIO_NATIVE_RENDERER_SUMMARY;origin=IDENTITY_STATUS;error="
              + (poisoned ? "INVALID" : "STRUCTURAL_ONLY") + ";thread=OTHER"
        };
    }
}
