"""Release-blocking check: no direct Android audio commands outside the authority."""
from pathlib import Path
import re
root=Path(__file__).resolve().parent.parent/'addon/src/pro/celikom/nativeprobe/identitydiag'
engine=(root/'ReplacementEngine.java').read_text()
owner=(root/'AudioOwnership.java').read_text()
service=(root/'ProbeService.java').read_text()
api=(root/'NativeApi.java').read_text()
# Test.23 cherry-picks only Test.16 anonymous observation and Test.17 bounded verified cache.
# Unproven extra direct session controller and Test.22 transport must never enter baseline.
if 'directSessionObserver' in service or 'DirectSessionObserver' in service:
    raise AssertionError('Test.17 direct Media3 observer must not be active in safe merged Test.23')
if 'FastAudioTransfer' in api:
    raise AssertionError('Test.22 experimental multi-range transport must not enter Test.23')
if ('replacement_lookahead_cache_reused' not in engine
    or 'replacement_interrupted_file_retained' not in engine
    or 'retainInterruptedCompleteFile(reason);' not in engine):
    raise AssertionError('Test.17 complete-file cache reuse and retention must be present')


if ('final ExecutorService audioWork=Executors.newSingleThreadExecutor()' not in api
    or 'final ExecutorService lookaheadAudioWork=Executors.newSingleThreadExecutor()' not in api
    or 'enqueueDownload(audioWork,"current"' not in api
    or 'main.postDelayed(()->enqueueDownload(lookaheadAudioWork,"lookahead"' not in api
    or 'foregroundAudioDemand.get()>0' not in api
    or 'foregroundAudioDemand.incrementAndGet()' not in api
    or 'foregroundAudioDemand.decrementAndGet()' not in api
    or 'LOOKAHEAD_ENQUEUE_YIELD_MS=1100' not in api
    or 'api.downloadLookahead(j,' not in engine):
    raise AssertionError('speculative lookahead must never queue before or compete with current audio demand')
for label,pattern in [
    ('direct decoder command',r'\b(?:player|p|old|mp)\.(?:start|pause|seekTo)\s*\('),
    ('native gain change bypass',r'\.setInputGainAllChannelsTo\s*\('),
    ('source effect activation bypass',r'\bcandidate\.setEnabled\s*\(true\)'),
]:
    found=re.search(pattern,engine)
    if found:raise AssertionError(label+': '+engine[max(0,found.start()-60):found.end()+50])
for required in ['void prepareSourceEffect(', 'void startDecoder(', 'void pauseDecoder(',
                 'void seekDecoder(', 'void grantReplacement(', 'RestoreResult restoreSource(',
                 'void retireDecoder(', 'void event(Event event)', 'boolean dataCurrent(', 'boolean commandCurrent(']:
    if required not in owner:raise AssertionError('missing audio authority: '+required)
if 'audioOwner.event(AudioOwnership.Event.RETURN);' not in engine or 'audioOwner.commandCurrent(returnTicket' not in engine:
    raise AssertionError('return to original must revoke old handover and use owner command ticket')
if 'audioOwner.event(AudioOwnership.Event.HANDOVER);' not in engine or 'audioOwner.event(AudioOwnership.Event.SEEK);' not in engine:
    raise AssertionError('seek/handover bypass unified event generation')
if 'audioOwner.sourceGainDuringAlignment(effect);' not in engine:
    raise AssertionError('slow decoder seek must restore original through AudioOwnership')
if 'void sourceGainDuringAlignment(' not in owner:
    raise AssertionError('native seek source gain must use sole audio authority')
for expected in [
    'audioOwner.mayConsumeCompletion(mp)',
    'accountLeaseCurrent()',
    'audioOwner.seekInFlight(mp)',
]:
    if expected not in engine:
        raise AssertionError('decoder callback lacks unified completion/account fence: '+expected)
if 'boolean mayConsumeCompletion(' not in owner:
    raise AssertionError('native decoder completion must be classified by single audio owner')
if 'handoverPending' in engine:
    raise AssertionError('duplicate handover clock flag: AudioOwnership is authoritative')
if 'audioOwner.handoverWaitForClock(alignLive)' not in engine:
    raise AssertionError('native handover clock gate must be owned by AudioOwnership')
if 'warmSeekTransition' in engine:
    raise AssertionError('duplicate warm seek flag: use AudioOwnership native seek flight only')
if 'audioOwner.seekInFlight(p)||position-baseline[0]<40' not in engine:
    raise AssertionError('handover must gate native warm seek from sole audio owner')
if 'audioOwner.retireDecoder();' not in engine:
    raise AssertionError('decoder release must revoke ownership lease on same song')
if 'SourceTransitionGate.currentItemBoundary(' in service or 'SourceTransitionGate.currentPositionSeek(' in service:
    raise AssertionError('Media3 boundary bypasses SourceEventArbiter')
if 'syncPolicy.correct(' in engine or 'driftGuard.confirmed(' in engine:
    raise AssertionError('parallel clock deciders remain active')
if 'if(seeking&&audioOwner.seekInFlight(player)){' not in engine:
    raise AssertionError('seek-time Media3 buffering must not revoke in-flight decoder seek')
if 'if(s.buffering&&s.wantsToPlay)bufferSource(s,sourceJump);' not in engine:
    raise AssertionError('native source buffering classification was lost')
if 'sourceGainDuringAlignment(effect);originalMix=1f;traceAudioCommands();' not in engine:
    raise AssertionError('native source gain restoration must close command-gap telemetry immediately')
if 'service.replacement.accountLeaseCurrent();' not in api or api.count('notifyAudioAccountChange();')<3:
    raise AssertionError('all auth generation changes must notify the audio owner without waiting for transport ticks')
fade=engine[engine.index('void fade(boolean coherentEntry){'):engine.index('void setAuditedVolume(',engine.index('void fade(boolean coherentEntry){'))]
if 'audioOwner.fadeSourceBeforeGrant(fx' in fade or 'final long rampDuration=32;' in fade:
    raise AssertionError('legacy unverified source fade reintroduced')
if 'audioOwner.grantReplacement(fx);originalMix=0f;applyVolume(1f);' not in fade:
    raise AssertionError('retained seek must still grant exclusive output')
if '}else{\n     audioOwner.grantReplacement(fx);originalMix=0f;applyVolume(1f);\n    }' not in fade:
    raise AssertionError('pause/seek immediate exclusive path must mute original before secondary gain')
if 'audioOwner.handoverClockValidated();' not in fade:
    raise AssertionError('decoder must pass the sole clock gate before output grant')
if ('audioOwner.blendSameSong(' not in fade
    or 'if(coherentEntry){' not in fade
    or '"phaseVerified",false' not in fade
    or '"sourcePcmMeasured",false' not in fade
    or 'UNIFIED_JOIN_MS=160' not in engine
    or 'float original=1f-mix;' not in owner):
    raise AssertionError('one production entry must use measured-clock-gated complementary gains and acknowledge unverified phase')
if ('COLD_JOIN_DIP_MS' in engine or 'replacement_exclusive_dip_start' in engine
    or 'experimentalCorrelatedJoin' in engine or 'experimentalCorrelatedJoin' in service
    or 'celikom-join-lab' in service):
    raise AssertionError('two-mode A/B selector and 500ms cold-volume valley must not reappear')
if ('audioOwner.duckSourceForExclusiveJoin(p,fx,progress,ownerKey,ownerEpoch,handoverTicket.operationEpoch);' not in fade
    or 'shapeExclusiveCold=(!coherentEntry&&requireClockGate&&coldJoinExclusiveExperiment)' not in fade
    or 'originalMix=1f-progress;traceAudioCommands();' not in fade
    or 'audioOwner.grantReplacement(fx);originalMix=0f;applyVolume(0f);' not in fade
    or 'exclusiveRiseStarted[0]=now;' not in fade
    or 'float progress=TransitionMix.progress(now-exclusiveRiseStarted[0],48);' not in fade
    or 'if(progress<1f){owner.handler.postDelayed(this,10);return;}' not in fade):
    raise AssertionError('cold source duck must finish before decoder rise; no overlap or seek ramp')
activity=(root/'RecorderActivity.java').read_text()
if 'requestJoinExperiment' in activity or 'save.setOnLongClickListener' in activity or 'celikom-join-lab' in activity:
    raise AssertionError('Save diagnostics must have no hidden ordinary/linear mode selector')
if ('streaming.holdPrefetchForSeek();' not in fade
    or 'streaming.releasePrefetchAfterSeek();' not in fade
    or 'void holdPrefetchForSeek(' not in (root/'BufferedAudio.java').read_text()):
    raise AssertionError('partial-stream alignment must suspend background prefetch until verified handover')
if 'restoreScrubSourceAtDeadline(' in engine or 'boolean shortScrub=' in engine:
    raise AssertionError('0.3.65 muted-source seek deadline cannot be reintroduced')
if 'pendingStreamScrubJoin=true;' in engine:
    raise AssertionError('partial-stream seek must not restart the cold 500ms dip')
if 'pendingStreamScrubJoin=false;seekHoldActive=false;' not in engine:
    raise AssertionError('every new seek must revoke old scrub handover commands')
if 'setAuditedVolume(player,0f);audioOwner.pauseDecoder(player);' not in engine or 'audioOwner.sourceGainDuringAlignment(effect);originalMix=1f;traceAudioCommands();' not in engine:
    raise AssertionError('seek must silence decoder first, then immediately restore native source using the retained effect')
if 'if(originalMix<=0.001f&&!seekHoldActive)' not in fade or 'seekHoldActive=false;pendingStreamScrubJoin=false;ownerEvent("exclusive_handover")' not in fade:
    raise AssertionError('completed handover must revoke any previous seek/owner lease')
if 'fade(newlyAttached||pendingStreamScrubJoin)' not in engine or 'else if(newlyAttached){setAuditedVolume(player,0f);fade(true);}' not in engine:
    raise AssertionError('every new session attachment including long-pause resume must use the one clock-gated entry')
if ('platform_audio_activity_observed' not in service
    or 'registerAudioPlaybackCallback(playbackActivityObserver,handler)' not in service
    or '"observationOnly",true,"audioCommandSent",false' not in service
    or 'startPlaybackActivityObserver()' not in service
    or 'stopPlaybackActivityObserver()' not in service):
    raise AssertionError('playback callback must be anonymous, read-only and disposable')
if 'media3Router.discontinuity(' not in service or 'media3Router.mediaItem(' not in service:
    raise AssertionError('real ProbeService listeners must use the same Media3 router exercised by the HONOR replay')
if 'audioOwner.commandCurrent(handoverTicket' not in fade or 'token!=transition' not in fade:
    raise AssertionError('same-song blend must recheck command/epoch cancellation every tick')
if 'float blendSameSong(' not in owner or 'state!=State.SAME_SONG_BLEND' not in owner:
    raise AssertionError('legacy guarded same-song blend regression must remain testable')
if 'void duckSourceForExclusiveJoin(' not in owner or 'commandedSecondary>0.001f' not in owner:
    raise AssertionError('source-only attenuation must reject an already audible decoder')
if 'if(effect!=null&&originalMix>0.001f' not in engine or 'audioOwner.state()==AudioOwnership.State.SAME_SONG_BLEND' not in engine:
    raise AssertionError('pause must immediately silence replacement and restore source during blend')
if engine.count('()->transportLeaseCurrent(key,g,account)')!=3:
    raise AssertionError('baseline stream, Test25 verified progressive stream and full download must all keep exact track/account ownership leases')
if '&&Math.abs(residual)>HANDOVER_DRIFT_MS)' not in engine or 'seekCorrections==0?80' in engine:
    raise AssertionError('streaming correction cannot apply a stricter 80ms threshold than the handover budget')
if 'boolean retainedPosition=resumePositionRetained' not in engine or 'boolean retainedPauseResume=resumed&&retainedPosition' not in engine or 'boolean seamlessResume=retainedPauseResume' not in engine:
    raise AssertionError('bounded, verified same-track pause resume must not re-seek')
print('PASS: all audio and Media3 mutations use the single authorities')
