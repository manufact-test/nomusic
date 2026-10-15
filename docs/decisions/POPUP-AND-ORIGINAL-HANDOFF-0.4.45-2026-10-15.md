# Popup recovery and old-original handoff — 0.4.45 (2026-10-15)

Owner reports picker cancellation followed by frozen Start/version UI in0.4.43,
and the same other-song fragment after installing0.4.44. Both remain one client
update. No server/media/moderation/gain mutation is required.

## Playback: missing original-audio transition

The0.4.44 protection stopped the previous replacement, but automatic guard
release on metadata-first track change immediately unmuted the previous native
ORIGINAL stream. That stream can still be playing the previous recording.
The new two-world regression fails against the0.4.44 MAIN bundle with the old
original physically unmuted; the updated regression passes. This establishes a
second concrete leak path, not an independent recording of the owner's clip.

For track-unknown/ambiguous/changed on the same native source, MAIN silences the
replacement but retains the original mute for a bounded1000ms handoff. Native
source change releases the old lease; verified replacement guard acquisition
can transfer the same-element lease without unmuting. An old controller's
cleanup acknowledgement cannot unmute the transition, and stale token cleanup
cannot affect a newer lease. Latest user volume/mute intent is preserved.
Explicit Stop/Return original/page shutdown release immediately; the independent
one-second deadline fails open if the fresh binding/controller never arrives.
Other errors and source-rebinding fail-open behavior remain immediate.

## Popup: finite waits and cancellation

Screenshot says «Загрузка версии песни…» and «Проверяем доступ…» with the
controller STOPPED and healthy bridge/network. The first label was a READ of
version availability, not an actual upload. File picker cancellation alone does
not persist any upload-in-progress flag; its exact causal connection to the
stalled requests is unproven. Do not claim a known uploaded-file/DB lock.

Shared read recovery now rejects on its20s deadline/reset even when config,
response/cleanup or a transport ignores AbortSignal. Retained shared read
promises are released; writes are not automatically retried. Popup messages and
standalone access/version presentation have finite waits; Start has60s and
other messages30s. Failures unlock retry, late replies cannot repaint results,
and explicit Start resets old worker read checks. Polling does not pile up
while its prior status request is pending. Local config/file inspection also
has a finite wait. Status wording now says «Проверяем наличие версии CELIKOM…».

Stop remains available while Start checks access; its UI generation invalidates
a late Start response and the worker's existing generation fence keeps a later
Stop authoritative. A native input cancel event clears an empty selection's
presentation/progress without sending a file or locking the next song. An
existing selection remains intact on cancel.

## Verification and delivery

245 extension tests PASS locally: stalled read ignoring abort, reset recovery,
access/version timeout then retry, empty picker cancel/next song, Start timeout,
Stop during Start/late response, old-original mute, immediate Stop, one-second
fail-open, lease handoff/user intent and earlier playback/upload regressions.
The0.4.44 old-original baseline fails the new physical-mute assertion.

Native Chrome checks extended for actual decoded media and actual MAIN guard
lease transfer. A new real-popup module fixture exercises input cancel, another
song, Start/Stop/late reply, finite timeout and fresh retry (test clock shortens
the30/60s waits only inside the fixture). It does not automate the OS dialog.
CI/native results and final ZIP checksum recorded after execution.

Client-only update, live server remains0.4.43-d7c2ab8b6ce142a2595573dcfb34d673b377e68d.
PR6 open/unmerged; Issue7 open. Owner listening/real picker acceptance pending.
