# CELIKOM Android A1 — NAV23 exact engine holder-stream array identity (18 Nov 2026)

**Scope:** same owner-signed 2025.10.4 native Yandex clone, no architecture change, no vendor code modifications, CELIKOM replacement **NOT_CONNECTED / NO-GO**. Original playback on owner's phone is normal; no pause, seek, Next or music bugs to fix. This release is **only a bounded diagnostic witness**, not audio replacement.

## Why this is the next grounded hook

The owner's private NAV22 `CELIKOM-A1-Diagnostics-1794950075073.txt` (never commit raw TXT) confirms `SECONDARY_CALLER_ENTER=MANY`, `SECONDARY_CALLER_STREAM_MATCH=MANY`, `UNSCOPED_ATTACH_SECONDARY_MATCH=MANY`, `UNSCOPED_ATTACHED_STREAM_READ_MATCH=MANY`, `READ_RETURN_LINK_LOST=NONE`, but `QUEUE_SCOPE_ENTER=NONE`, `QUEUED_HOLDER_ATTACHED=NONE`. Separate Stage B still `NOT_CONNECTED`.

The pinned exact 2025 signed static scans identify precisely **two interface dispatch calls at PC 131/144** from `Landroidx.media3.exoplayer.e.catch(Lxh6;IZJ)V` to `Landroidx.media3.exoplayer.k.super(LlQ8;[LSr4;LR29;ZZJJLSl6$b;)V`, which dispatches into the NAV22 confirmed `b.super → b.package → b.g`. Exact same `e.catch` method has `Lxh6` holder parameter and reads its `[LR29` stream array at PC 67 and the `Lyh6 → LSl6$b` period identifier path. CI #44179471641 SUCCESS. The static body does **not** by itself prove runtime same-reference holder-to-stream or audible track identity.

## What NAV23 adds, carefully

A sixth read-only exact-native-2025 observation hook on `e.catch(Lxh6;IZJ)V` records its original holder reference in a nested ThreadLocal scoped for the unchanged `chain.proceed()`. The hook only installs in the existing **own clone MAIN package/version 24025542** guard. It resolves precisely one declared `Lxh6.[LR29` field by verified type, and no hook is installed if that gate fails. In existing `b.package` post-call observation, while both the original `e.catch` frame and NAV22 `b.super` secondary caller are active, the code checks whether the **exact stream object is a Java `==` member** of that exact holder array; it does not touch stream contents. Array length capped at 32, read exceptions fail closed. Only a confirmed member can enter a separate ephemeral `engineHolderLinks` cohort. The link is removed upon any reattachment/detach.

Separately exported finite categories:
- `AUDIO_NATIVE_RENDERER_HOOK_STATUS:ENGINE_HOLDER_SCOPE=REGISTERED/NO_HOOK/NOT_SEEN`
- `ENGINE_HOLDER_SCOPE_ENTER`
- `ENGINE_HOLDER_STREAM_ARRAY_MATCH`, `DIFFERENT`, `UNAVAILABLE`
- `ENGINE_HOLDER_READ_RETURN_MINUS4/MINUS5/MINUS3/OTHER` after original `b.g()` returns on the **same** linked renderer and stream.

Prior `QUEUE_SCOPED_*`, `UNSCOPED_*`, `SECONDARY_CALLER_*` and Stage B status remain untouched and separate. **A holder-array match is a stronger structural media-period/renderer stream identity, NOT currently audible track, album, edition or PCM proof.** Do not enable CELIKOM substitution based on structural matches alone. No raw references, data, IDs, URLs, tokens, audio bytes, song titles, stack traces, field names or values are exported.

Six added JVM reference-identity tests cover valid exact member/read result, different array member rejection, absent secondary frame, detach+reattach invalidation, unavailable field, engine-frame lifetime unwind. Existing NAV22 tests preserved; exact JVM CI #44180395176 **SUCCESS**.

## Protected state and owner testing

Single repo/branch: `manufact-test/nomusic` / `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Exact pre-NAV23 backup: `backup/android-a1-nav22-owner-secondary-proven-before-nav23-engine-holder-20261118` @ `892758105a130e496161aef9f1c146e78184923a`. NAV22 library APK preserved SHA256 `06e7dd168f82db2052d8421a050c5d2bf22f12ff250918d4bd943e7b1cdebf86`.

NAV23 one-time in-place original-publisher/owner-signed ARM13 CI `.github/workflows/android-a1-nav23-exact-engine-holder-array-diagnostic-export-once.yml` triggered at `b53af8291c38ac9e7141a186bb48ab682eb30e25`. **Do not claim signed owner APK exists in Library until CI SUCCESS, signer/hash checks and Library round-trip finish.** No new owner phone testing before that gate.

When released: owner installs signed NAV23 over NAV22 (never uninstall/clear app data), listens normally for a few tracks, sends fresh private TXT. Interpret whether engine holder-array match and independently linked read result appear on the real device; only then identify the current selected media-item/period boundary without modifying sound.
