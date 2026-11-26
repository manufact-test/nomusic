# Extension0.4.87 — confirmed intro preparation must not flash original
26 November2026. Owner-only candidate, listening pending, NOT public stable.

## Inputs / prior state
Parent main and86 source:43640e4fae5a64d0e46bd32523a15a365ddae60d.
Owner reported recurrent audible startup switches WITHOUT VPN on86. Input file Вставленный текст(20261126-093641).txt reports86. Owner's original testing reference was85; neither its short successful run nor the86 pause correction proved startup solved.

The final three retained starts (tracks78608850,48592437,27317260) ALL reach intro-start-timeout with replacement readyState0. Original play follows; original mute is reacquired about67/43/50ms after that play respectively. The decoder is then ready, and later snapshots align closely. This is a confirmed brief original→replacement handover, not proof of a server outage. Recorded API calls succeed. Preparation history ranges253–852ms excluding a manual mid-song retry; an earlier same-track state-changed and explicit retry are present, and their missing full trace must not be invented.

86's hidden pause fix is kept. No bridge-unhealthy teardown appears in this retained restore history; absence in this bounded window is not a universal proof.

## Correction
MAIN already reserves a bounded one-second transition/admission lease. A separate400ms intro timer nevertheless released that reservation even AFTER the isolated controller had positively resolved/validated the asset and acquired its preparing lease. It then started native audio while the decoder was still finishing; subsequent activation muted it again. Early selected-track resolve85 reduces work but cannot eliminate that contradictory premature release.

87 keeps the400ms fallback for an UNCONFIRMED descriptor. If the existing GUARD_ENGAGE(preparing:true) has successfully validated the exact current master/lease, intro play may wait only for the remainder of its ORIGINAL one-second handoff deadline. No generic snapshot or repeated preparing request can extend/restart it. The native clock stays paused until readiness or bounded fallback, preserving the opening rather than letting it advance silently. Missing assets/negative policy release immediately. Pause, Stop, source/track changes still cancel; mid-song resumes remain outside intro admission. Reservation-before-native-play ordering is also covered, using the SAME original deadline.

This is NOT reinstating the prior unconditional1500ms intro delay. Unconfirmed lookups still fall back at400ms; positively confirmed preparation uses the already-existing reservation cap. It does NOT make byte transfer faster or guarantee a silent handover for audio that exceeds that cap. Very slow/failed loads must still fail open; do not claim all starts/network symptoms are fixed. No new signed grant lifetime or guard authority is created.

Runtime change is confined to main-world-entry plus release version declarations. Replacement controller/player, ranges, sync, adapter, API/auth,85 early resolve and86 background bridge correction are unchanged. No whole-file mid-song expansion, live-join, speculative queue playback, or84 unbuffered-yield mechanism is introduced. No Android/Windows/backend/infra changes.

## Verification
A new packaged MAIN+ISOLATED regression was run AGAINST86: FAILS at original.paused because native original starts before the delayed confirmed decoder is ready. The SAME scenario on87 passes.
409/409 local extension tests PASS. Added direct MAIN and packaged two-world tests at450/650/850ms, checking native clock remains paused, physical original stays muted, one decoder and unchanged lease. Confirmed-but-hanging decode fails open at the original1s deadline; duplicate preparation/snapshots cannot renew it. Pause/source changes cancel the confirmed wait. Existing timeout-renewal test now exercises the actual bounded confirmed deadline (1030ms wait); unknown lookup400ms tests remain intact. Existing eight-minute background pause, Stop, missing/negative, mid-song, disabled-worker, seek, upload and access suites pass.
Manifest validation PASS; security gate PASS (67 client files). No local real Chrome/Brave listening proof; VM/behavior tests are not substituted for it.

## Owner artifact
celikom-extension-0.4.87.zip;2,494,364bytes.
SHA2568bfc456acfa1b9e7888cfb62e876111101e1d2f71666b54d38f82d20489286de.
Library libfile_195bac702f4c8191ab908b78b6c3978b.
86 rollback remains Library libfile_a1a18de43f04819181e286d403e2db38; SHA256c3a95cc15ad296e149ea3d618b8dc74ea56a42c7603ee0ce54a0480981c035f2.
Keep owner promotions empty/public stable unchanged until explicit acceptance.
Owner check SAME unpacked folder→Reload extension AND Yandex→verify87. Listen to opening words on skips and natural endings; pause/seek must remain normal. A delayed song start can now be one continuous bounded wait instead of original briefly sounding then switching; do not describe that as measured download acceleration. Inspect fresh diagnostic after any remaining symptom.
