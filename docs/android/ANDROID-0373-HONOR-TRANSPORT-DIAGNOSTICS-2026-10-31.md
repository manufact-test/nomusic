# Android 0.3.73 — HONOR passive transport diagnostics (2026-10-31)

## Exact rollback point

`backup/android-0372-ota-accepted-before-transport-diagnostics-20261031`
at `5e18fd070dbf6115f643079b03637b0d180e9665`.
Accepted 0.3.72 / versionCode 73: signed OTA, updater, Recents task removal.
Never move this backup ref.

## Release scope

Android-only: versionName 0.3.73, versionCode 74, unchanged signer.
No UI controls, permissions, audio-mix levels, seek tolerance, routing,
installer behavior, backend or website changes. The experimental seek-offset
branch is not merged.

## Passive diagnostic events

- `replacement_seek_request`: local single-flight seekSeq, ALIGNMENT/WARM,
  requestedPositionMs, owner operation epoch. No claim about Media3 gesture.
- `replacement_seek_ack`: paired sequence/kind/target, callback duration,
  projected source transport and decoder positions, signed residual, correction
  pass, HTTP range-wait observed, stale-operation fence, transport-only flags.
  No titles, identity keys, tokens or captured sound. Android ACK is untagged.
- `replacement_join_transport_summary`: one completed cold complementary
  join's transport drift min/max, start/end projected positions, sample count
  and elapsed time. This is not PCM phase or physical speaker measurement.
- Existing `replacement_seek_complete`, source buffer, stream wait and
  `replacement_transition_complete` remain for compatibility.

## Verification / field procedure

Run complete native regressions, strict release contract, API36/JDK17/D8,
pinned offline packaging, and signed publish on guarded production ref only.
Signer SHA256
`67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`
is unchanged. On 0.3.72 tap existing «Проверить обновления», install 0.3.73,
perform several seeks and natural track joins, export existing journal.
Transport clocks alone cannot prove an audible micro-gap or waveform phase.
No PlaybackCapture, MediaProjection or microphone permission.
