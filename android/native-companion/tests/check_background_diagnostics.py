from pathlib import Path

ROOT = Path(__file__).resolve().parent
ADDON = ROOT.parent / "addon/src/pro/celikom/nativeprobe/identitydiag"
service = (ADDON / "ProbeService.java").read_text(encoding="utf-8")
activity = (ADDON / "RecorderActivity.java").read_text(encoding="utf-8")
engine = (ADDON / "ReplacementEngine.java").read_text(encoding="utf-8")

def method(source, marker):
    start = source.find(marker)
    assert start >= 0, "Missing method marker: " + marker
    opening = source.find("{", start)
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start:index + 1]
    raise AssertionError("Unclosed method: " + marker)

snapshot = method(service, "Map<String,Object> runtimeSnapshot(String reason)")
for field in (
    '"serviceAgeMs"', '"tickAgeMs"', '"sampleAgeMs"', '"mediaEventAgeMs"',
    '"controllerConnected"', '"controllerPlaybackState"', '"sourceAlias"',
    '"replacementArmed"', '"replacementOwnerState"', '"trustedSessionId"',
    '"effectSessionId"', '"effectHasControl"', '"effectEnabled"',
    '"playerSessionId"', '"playerIsPlaying"', '"lookupRetryRemainingMs"',
    '"wakeLockHeld"', '"networkAvailableAgeMs"', '"networkLostAgeMs"',
):
    assert field in snapshot, "Runtime snapshot misses " + field
for forbidden in (
    "replacement.arm(", "startDecoder(", "pauseDecoder(", "setAuditedVolume(",
    "seek(", "fade(", "mute(", "unmute(", "stop(",
):
    assert forbidden not in snapshot, "Runtime snapshot must remain read-only: " + forbidden

tick = method(service, "final Runnable tick")
assert "handler.postDelayed(this,250)" in tick, "Do not change the service sampling cadence"
assert 'LogStore.log("service_heartbeat"' in tick and "15000" in tick
assert "START_NOT_STICKY" in service, "This diagnostic-only patch must not alter restart policy"
assert 'LogStore.log("media3_connect_attempt"' in service
assert 'LogStore.log("media3_connect_result"' in service
assert '"cellular"' in service and '"wifi"' in service and '"validated"' in service
assert 'LogStore.log("service_task_removed"' in service
assert 'LogStore.log("service_destroying"' in service

activity_logger = method(activity, "void logLifecycle(String event)")
assert 'LogStore.log("activity_lifecycle"' in activity_logger
for forbidden in ("launch(", "beginTrial(", "startForegroundService(", "replacement.arm(", "seek(", "setAuditedVolume("):
    assert forbidden not in activity_logger, "Activity lifecycle diagnostics must not start or control audio: " + forbidden
assert 'logLifecycle("on_start")' in activity
assert 'logLifecycle("on_stop")' in activity
assert 'logLifecycle("on_new_intent")' in activity

assert 'LogStore.log("replacement_stop_state"' in engine
assert 'LogStore.log("replacement_recovery",recovery)' in engine
assert '"retryAtElapsedMs"' in engine and '"failureCount"' in engine
assert 'LogStore.log("audio_effect_control_status",state)' in engine

print("PASS: background/service diagnostics are read-only and preserve the 250ms audio observer")
