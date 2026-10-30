from pathlib import Path
import subprocess,os
r=Path(__file__).resolve().parent;addon=r.parent/'addon/src/pro/celikom/nativeprobe/identitydiag';out=r/'classes';out.mkdir(exist_ok=True);json=Path(os.environ.get('CELIKOM_ANDROID_DEPS',str(r.parent/'deps')))/'json.jar'
subprocess.run(['python3',r/'write_fakes.py'],check=True)
src=[*sorted((r/'fakes').rglob('*.java')),r/'TestEngine.java',r/'TestAudioOwnershipRegression.java',r/'TestUnifiedAudioTransactions.java',r/'TestHonor059Journal.java',r/'TestAudioContinuityMonitor.java',r/'TestRealFailures.java',r/'TestAudioLifecycle.java',r/'TestClockSupervisor.java',r/'TestAudioCommandGateway.java',r/'TestSourceEventArbiter.java',r/'TestHonor051Journal.java',r/'TestPhoneReplay.java',r/'TestResumeClock.java',r/'TestLongRun.java',r/'TestCarRecovery.java',r/'TestStreamingEngine.java',r/'TestHandoverClock.java',*[addon/n for n in ['ApiContract.java','AlbumMatch.java','PlaybackSource.java','PlaybackDuration.java','AudioOwnership.java','AudioContinuityMonitor.java','SyncPolicy.java','DriftGuard.java','ClockSupervisor.java','SourceTransitionGate.java','SourceEventArbiter.java','BufferRecoveryGate.java','TransitionMix.java','AudioTransfer.java','BufferedAudio.java','StreamingAudio.java','ReplacementEngine.java']]]
subprocess.run(['java','com.sun.tools.javac.Main','-encoding','UTF-8','-source','8','-target','8','-cp',str(json),'-d',str(out),*map(str,src)],check=True)
subprocess.run(['java','-cp',str(out)+os.pathsep+str(json),'pro.celikom.nativeprobe.identitydiag.TestEngine'],check=True)

subprocess.run(['java','-cp',str(out)+os.pathsep+str(json),'pro.celikom.nativeprobe.identitydiag.TestPhoneReplay',str(r/'phone-0.3.20-replay.tsv')],check=True)

subprocess.run(['java','-cp',str(out)+os.pathsep+str(json),'pro.celikom.nativeprobe.identitydiag.TestResumeClock'],check=True)
subprocess.run(['java','-cp',str(out)+os.pathsep+str(json),'pro.celikom.nativeprobe.identitydiag.TestLongRun'],check=True)
subprocess.run(['java','-cp',str(out)+os.pathsep+str(json),'pro.celikom.nativeprobe.identitydiag.TestCarRecovery',str(r/'car-0.3.26-clock.tsv')],check=True)

subprocess.run(['java','-cp',str(out)+os.pathsep+str(json),'pro.celikom.nativeprobe.identitydiag.TestStreamingEngine'],check=True)

subprocess.run(['java','-cp',str(out)+os.pathsep+str(json),'pro.celikom.nativeprobe.identitydiag.TestHandoverClock'],check=True)

# Mandatory interleavings of preparation, seek, pause, route and boundary.
subprocess.run(['java','-cp',str(out)+os.pathsep+str(json),'pro.celikom.nativeprobe.identitydiag.TestUnifiedAudioTransactions'],check=True)

# Non-negotiable regression gate for user-reported HONOR overlapping audio and stale pause callbacks.
subprocess.run(['java','-cp',str(out)+os.pathsep+str(json),'pro.celikom.nativeprobe.identitydiag.TestAudioOwnershipRegression'],check=True)
subprocess.run(['java','-cp',str(out)+os.pathsep+str(json),'pro.celikom.nativeprobe.identitydiag.TestAudioContinuityMonitor'],check=True)
subprocess.run(['java','-cp',str(out)+os.pathsep+str(json),'pro.celikom.nativeprobe.identitydiag.TestHonor059Journal'],check=True)

subprocess.run(['java','-cp',str(out)+os.pathsep+str(json),'pro.celikom.nativeprobe.identitydiag.TestRealFailures'],check=True)

# Mandatory lifecycle / wrong-completion replay.
subprocess.run(['java','-cp',str(out)+os.pathsep+str(json),'pro.celikom.nativeprobe.identitydiag.TestAudioLifecycle'],check=True)

# One clock decision point: real HONOR drift, small BT offsets and bounded stalls.
subprocess.run(['java','-cp',str(out)+os.pathsep+str(json),'pro.celikom.nativeprobe.identitydiag.TestClockSupervisor'],check=True)

# Android application tests, not just fake audio engine. Fail GitHub CI if missing SDK.
subprocess.run(['python3',r/'run_addon_host.py'],check=True)

# All decoder play/seek/pause commands are gated by the same lifecycle authority.
subprocess.run(['java','-cp',str(out)+os.pathsep+str(json),'pro.celikom.nativeprobe.identitydiag.TestAudioCommandGateway'],check=True)

# Media3 boundary and seek arbitration from the 0.3.51 device recording.
subprocess.run(['java','-cp',str(out)+os.pathsep+str(json),'pro.celikom.nativeprobe.identitydiag.TestSourceEventArbiter'],check=True)

# Sanitized latest 0.3.51 HONOR clock journal; observe safe per-track fallback.
subprocess.run(['java','-cp',str(out)+os.pathsep+str(json),'pro.celikom.nativeprobe.identitydiag.TestHonor051Journal',str(r/'honor-0.3.51-clock-replay.tsv')],check=True)

# Structural regression: no direct decoder or source FX commands can bypass ownership.
subprocess.run(['python3',r/'check_audio_architecture.py'],check=True)
