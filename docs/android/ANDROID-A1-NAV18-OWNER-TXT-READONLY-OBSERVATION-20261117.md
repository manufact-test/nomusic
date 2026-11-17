# CELIKOM Android A1 — NAV18 owner handset diagnostic and first bounded fix (17 Nov 2026)

**This supersedes the instruction to await the owner's first NAV18 TXT.** Actual owner report arrived: `CELIKOM-A1-Diagnostics-1794933581039.txt`. Treat the private TXT as user-supplied evidence; do **not** upload it or its entire contents into GitHub.

## Actual owner result: no CELIKOM replacement; native route not yet established live

- Latest relevant build marker: `DIAGNOSTIC_BUILD=NAV_V18_NATIVE_RENDERER_STREAM_READONLY;ACTIVE`. Older `NAV_V17_PASSPORT_PROVIDER_AUTHORITY_FIX` entries coexist because log is aggregated/trimmed (`LOG_TRIMMED=KEEP_LAST_32KB`).
- `AUDIO_STAGE_B_STATUS;CELIKOM_REPLACEMENT;NOT_CONNECTED`: NAV18 is *read-only diagnostic*, NOT a sound replacement build. Owner reports no CELIKOM substitution; expected by design, not evidence of server rejection.
- Exact NAV18 summary: `QUEUE_SCOPE_ENTER=NONE`, `QUEUED_HOLDER_ATTACHED=NONE`, `UNSCOPED_ATTACH=FEW`, `STREAM_REATTACH_TRANSITION=NONE`, `ATTACHED_STREAM_READ_MATCH=NONE`, `ATTACHED_STREAM_READ_DIFFERENT=NONE`, `READ_NO_MATCHED_ATTACHMENT=FEW`, `RENDERER_DETACHED=FEW`, `IDENTITY_STATUS=STRUCTURAL_ONLY`.
- Thus some direct native renderer attaches, read entries, and detach calls *were observed*, but no same-object queue-holder→attached renderer stream claim can be made. No runtime CELIKOM audio proof. `EXO_OPEN_OK=MANY`, `EXO_READ_POSITIVE=MANY`, `EXO_IO_FAILURE=NONE` indicate normal Yandex source activity (coarse bins only), not active current track/decoder.
- No `AUDIO_NATIVE_RENDERER_HOOK` registration lines survive in the trimmed user TXT. It is **unknown** if the queue hook failed registration or registered but never fired. Do NOT infer that signed static `mQ8.catch` path is invalid.
- Aggregated `PREVIOUS_PROCESS_EXIT=JAVA_CRASH` entries precede latest NAV18 session; `METRICA_EXCEPTION=MUSIC_APP/EXC_OTHER` appears after NAV18 startup but its exception class/cause is intentionally hidden. **Neither alone proves NAV18 crashed**. No owner assessment yet of Next/seek/My Wave stability.

## Exact in-repo fix — no new APK shipped

Branch only: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.
Pre-work backup: `backup/android-a1-nav18-owner-diagnostics-before-observer-fix-20261117` @ `a8d6dbc9cf7168a410a1fdb143cfa8d9cc51f9a6`.

- `NativeRendererStreamEvidence.java`: unscoped native `b.package` attachment now keeps a **separately labeled weak renderer/stream reference** so next on-device report can distinguish `UNSCOPED_ATTACHED_STREAM_READ_MATCH` vs `..._DIFFERENT` without falsely claiming the queue holder identity; read-budget rearmed on each valid unscoped attach (previously exhausted after the first few unpaired reads).
- `ExitCallsiteWitness.java`: persistent explicit-save hook statuses `AUDIO_NATIVE_RENDERER_HOOK_STATUS` for `QUEUE_SCOPE`, `STREAM_ATTACH`, `SAMPLE_READ`, `STREAM_DETACH` (REGISTERED/NO_HOOK/NOT_SEEN) are recorded even if the initial event log is truncated.
- `NativeRendererStreamEvidenceTest.java`: regression tests for weak-vs-strong matching, invalid queue inference, detach, late-read budget rearm and persisted hook-status summaries.
- No audio byte changes, no second Player, no hook version mixing, no source/rights policy changes. Strong `ATTACHED_STREAM_READ_MATCH` continues to require a real `mQ8.catch` scope and identical holder+renderer+stream.
- Code commits `500d4600` → `21d490e8` → `089ea2d1`. **JVM CI #44129950827 SUCCESS**; other native ARM13 workflows were automatically triggered and may still be running. This is code+test evidence, **not** owner-runtime proof. NAV18 shipped APK SHA256 `647cbbc348e128ff10e79f50a6a04964cf9253a5e4cacd08f5949fe892793212` remains unchanged in Library.

## Next actual decision

1. Wait for full native ARM13 CI results on the same code base. Do not claim that only JVM green validates the clone.
2. Next private, properly signed *in-place* diagnostic APK **only after** native CI green and owner install-signature/export gates. Do not install a new app or wipe data; do not send GitHub Actions temporary URLs. Publish/verify in ChatGPT Library when warranted.
3. Only in next live report distinguish: (a) queue hook NO_HOOK vs REGISTERED+never ENTER, (b) unscoped attached-stream read alias vs mismatch, (c) current/queued renderer and selected audible audio with new narrowly scoped observations if needed. Unscoped match is weaker proof, not audio/track/decoder or CELIKOM replacement.
4. Preserve accepted NAV17 baseline, Test.50, original vendor 2025 signed APK, Windows/browser/backend. Stage A NAV17 PASS, Stage B NO-GO. Do not redo static read-route chain or use 2026.10.3 HookSpec symbols.
