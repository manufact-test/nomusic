"""Release-blocking check: no direct Android audio commands outside the authority."""
from pathlib import Path
import re
root=Path(__file__).resolve().parent.parent/'addon/src/pro/celikom/nativeprobe/identitydiag'
engine=(root/'ReplacementEngine.java').read_text()
owner=(root/'AudioOwnership.java').read_text()
service=(root/'ProbeService.java').read_text()
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
print('PASS: all audio and Media3 mutations use the single authorities')
