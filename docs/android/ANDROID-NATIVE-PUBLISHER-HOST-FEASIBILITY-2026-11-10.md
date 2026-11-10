# CELIKOM Android — publisher-approved native source access gate (10.11.2026)

**Scope:** investigative review only, no third-party executable modification and no user-device actions. Source branch: `experiment/android-native-yandex-fileinfo-hooklab-20261109`; pre-investigation HEAD `0cf4ee3be8b092a316eacdaa0dce988e20b8c49b`; frozen backup `backup/android-native-publisher-host-gate-20261110`.

## Engineering verdict: NO-GO for real native replacement, not a declaration of universal impossibility

The required product is **the unchanged genuine Yandex.Music Android UI and its single native player**, with a rights-cleared alternative chosen *before that player's decoder prepares*. Current CELIKOM can decide which source is safe **in a pure-Java model**, but has **no authorized execution point in the publisher's real source-selection path**. A separate ordinary Android app cannot write another app's private decoder/media-source state across the default per-UID/process sandbox. This is the **architectural missing capability**, not a missing timeout tuning.

There are two separate unknowns:
1. **Clone launch:** in the isolated #170gpr experiment a different-package clone's MAIN started and exited itself (Android 11 `REASON_EXIT_SELF=1, status=0`). The exact caller/condition is *not* established. Do not claim "anti-tamper" or signature was proven. Fixing this clone's UI alone would *still not* establish a lawful pre-prepare source interface.
2. **Real playback source:** signed six-DEX static FileInfo `trackId` annotation and the `FileInfoDto -> sw7.y0/z0 -> eed` candidate are proven, but no live `trackId + edition + generation -> decoder descriptor -> prepare` association or replacement is proven. Original publisher app is neither debuggable nor shell-profileable, so normal ART tracing cannot establish this without further authorization.

## Current supported surfaces versus what we need

| Candidate | What primary evidence establishes | Why it is insufficient |
| --- | --- | --- |
| Android MediaSession / MediaController | Media sessions accept controller commands/playlist edits **only as supported/allowed by the media app**; player/session owner resolves media items | No generic foreign-UID right to edit decoder source; no shown Yandex source-before-prepare extension. `setMediaItems` describes queue control, not proof of seamless substitution of currently selected native track |
| Android audio capture | `AudioPlaybackCapture` gets a consent- and publisher-policy-limited **output** copy | No injection into a different app's existing decoder |
| VPN/proxy, accessibility, intents, exported providers | Prior pinned-manifest/read-only audits found media browsing, launch and provider surfaces | No verified authorized audio source input, no right to circumvent TLS/DRM or publisher app security |
| Modified Yandex clone / rootless loader | Private native laboratory clone MAIN self-exits; x86 LSPatch failed; own ARM witness is a different app | No functioning permitted publisher host. Do not repeat known failed probes, remove Play Protect, alter signatures or deploy on HONOR |
| Yandex platform/partner SDK | Yandex *publicly mentions* SDK/API integration engineering and a partner example (MTS Music), in **archived job vacancies** | Evidence that B2B integrations exist as a field of work, **not** a published SDK, source-swap permission, partner eligibility, or availability in the Android consumer app |
| Unofficial Yandex Music API | Community project calls itself unofficial, describes private API and account-token use | Not a publisher-granted Android pre-prepare contract; disallowed credential/token route |

**External primary/public sources (checked 10 Nov 2026):**
- Android app sandbox: https://source.android.com/docs/security/app-sandbox
- MediaSession command ownership: https://developer.android.com/media/media3/session/control-playback
- MediaSession.Callback resolution: https://developer.android.com/reference/androidx/media3/session/MediaSession.Callback
- Android AudioPlaybackCapture boundaries: https://developer.android.com/media/platform/av-capture
- Yandex platform SDK/API integration work (archived vacancy): https://yandex.ru/jobs/vacancies/menedzher-proektov-v-muziku-45619
- Partner work including MTS Music (archived vacancy): https://yandex.ru/jobs/vacancies/menedzher-integratsionnih-proektov-v-muziku-17745
- Music support / "Другой вопрос" contact entry: https://www.yandex.ru/support/music/ru/write-to-support
- Unofficial API disclaimer: https://ym.marshal.dev/

**Careful interpretation:** a job posting is NOT proof that the proposed source-selection SDK exists publicly or that CELIKOM may use it. A contact page is NOT partnership approval. No such source SDK, compatibility agreement, publisher-approved instrumented app or extension was verified in this review.

## One feasible next research path: explicit cooperation with Yandex Music

Use the official support/contact channel to ask for referral to the **music playback platform / B2B integrations team**; do not send account data, audio, APKs, keys or private logs. This is a proposal, **no outreach was sent**.

Seek written, version-specific answers to all of the following:
1. Does a **supported, licensed** Android native player/source integration interface exist for a **third-party, independently rights-cleared alternate recording** while preserving Yandex's own UI/account/player and normal subscription/rights checks? If not, this requirement is NO-GO.
2. Can that interface expose/receive authoritative **currently playing trackId + edition/album + playback generation**, and a single alternate descriptor **before** the native decoder prepare, without an independent player or modifying the publisher APK?
3. What is the trusted host/package/version/signing model, security review, allowed client permissions, catalogue and content-rights process, protected-stream/DRM constraints, and whether source replacement is contractually allowed?
4. Can an isolated partner-approved/sandbox build be supplied for **privacy-safe read-only witness** of FileInfo/decoder association and full lifecycle (seek, pause, fast Next, radio), without re-signing or bypassing the official consumer app?

**Acceptance gate before ANY new native substitution code or public APK:**
- Documented/explicit publisher approval of *this exact capability* (not only general API, OAuth or queue control).
- An authorized signed host/integration entry point demonstrably present on the intended Android platform; no root/Play Protect/signature/DRM/auth bypass.
- Real same-generation track+edition FileInfo request AND native decoder descriptor observed immediately before a single prepare, not inferred from UI titles, synthetic fixtures or static DEX.
- Rights/codec/range/crypto/duration checks; no candidate / ambiguous identity => original native source; no mid-play source switch.
- Then isolated authorized ARM device QA for RASKOL 42884423, «Дым» 39949113, initial click, seek/pause, Next/radio, Bluetooth, background/VPN; original installed HONOR untouched.

## Choices if a publisher-supported source extension is not available

**Keep this native-original requirement as NO-GO.** The unrelated content-distribution route (publish an authorized recording into Yandex's own catalogue through distributor) may be discussed with rights holders, but it **does not** let CELIKOM replace Yandex's current audio source per user and is not claimed as equivalent. Browser extension and Test.50 remain separate products/baselines, **not** evidence that Android has a one-player source hook.

Do not waste CI minutes repeating AppMetrica/DEX clone attempts or label synthetic PASS as native replacement. This is documentation/research only; **no new CI was run**, because no runtime code or host was changed. Previous exact [CI 42780177178](https://github.com/manufact-test/nomusic/actions/runs/42780177178) remains SUCCESS 2/2 for **models** only. No app/test binary delivered.

No Test.50, Windows, HONOR, extension, backend, databases, production, or publisher APK were touched.
