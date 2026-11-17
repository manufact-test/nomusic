# CELIKOM Android A1 — exact signed native renderer attached-stream accessor and setter (17 November 2026)

**Status:** NEW bounded static proof: native renderer `k.while()LR29;` is a direct getter of an attached `LR29` field stored by `b.package([LSr4;LR29;JJLSl6$b;)V`. **Stage A NAV17 PASS; Stage B NO-GO**. Actual current audio consumption is NOT verified.

## Input and preserved baseline

Original owner-tested NAV17 embeds publisher-signed Yandex Music **2025.10.4 #120.1gpr**, XAPK SHA-256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`, 16 signed splits/six DEX, embedded original base SHA-256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`. No 2026 obfuscated names transplanted into this original.

Continuation starts from [the exact `Lo96→Lup1$a→Lxh6.[LR29→LmQ8.try/new→k.while()` witness](ANDROID-A1-PERIOD-TO-RENDERER-SAMPLE-STREAM-IDENTITY-20261117.md). The prior proof established **the actual stream-reference comparison exists**, but *not* the concrete `k` implementation or live match.

## Signed static verification

New audit: `android/native-yandex-hooklab/ci/renderer_attached_stream_owner_exact.py`; scoped tests `test_renderer_attached_stream_owner_exact.py`; isolated workflow `.github/workflows/android-a1-renderer-attached-stream-owner-readonly.yml`. Read-only, exact six-DEX/16-split publisher signature/hash checks, ephemeral deletion of private original, no private field names/values or account/audio data logged.

- [Exact interface implementer CI #44113843144 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44113843144): interface `Landroidx/media3/exoplayer/k;` has **one direct implementer** `Landroidx/media3/exoplayer/b;`. A bounded **18-class subclass/implementation subtree** was found. The concrete inherited `b.while()LR29;` is defined with actual body `iget-object LR29` at PC 0, followed by `return-object` at PC 2, reading the same register. This resolves the previously unresolved interface getter implementation. It is **not** a new Player or decoder.
- [Exact attached-field uses CI #44114370270 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44114370270): within **426 methods across only this 18-class implementer subtree**, one exact `LR29` DEX field is touched by `b.while` and other scoped methods. This is a full field-reference equality check, not a type-only guess. Field **writes** occur in `b.package([LSr4;LR29;JJLSl6$b;)V` at PC 7, and `b.case()V` at PC 19; other observed reads are `b.g,b.h,b.implements,b.throws,b.while`.
- [Exact renderer input CI #44114869620 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44114869620): `b.package([LSr4;LR29;JJLSl6$b;)V` stores **its exact incoming `LR29` argument** into **the exact same field** returned by `b.while`. Argument registers and receiver verified, not just matching method signatures. `b.case` performs a clearing write; the field may be null before attachment, after removal or during transition. This is a reliable **native attachment boundary**, but no live renderer stream or audible decoder proof.
- Within the **79 exact `androidx.media3.exoplayer.e` engine methods** audited in this pass, no direct call to that *specific* descriptor on `k/b/l` was found. That negative result is **only** limited to this exact owner and descriptor; it does NOT disprove interface dispatch from a different helper. A new one-signature exact direct-caller audit can resolve the owner without global renderer methods.

**Important version-safety warning:** `android/native-yandex-hooklab/app/src/main/java/pro/celikom/yandex/nativehooklab/HookSpec.java` explicitly pins **2026.10.3 #170gpr**, not the current tested NAV17 original **2025.10.4 #120.1gpr**. Never reuse its obfuscated method/class assumptions in the new 2025 path. No hook or APK changed in this work.

## Interpretation and next proof gate

Known exact static chain is now:

`TrackWrapper → LiLb → Player → Lo96 → Lup1 → (child LR29) → Lup1$a → Lxh6.[LR29 → LmQ8.try/new reference equality with k.while() → inherited b.while() → exact b.attached-LR29 field`

And the **same exact native renderer attached field** is written by `b.package` from its incoming stream parameter, and cleared by `b.case`. The **unresolved** part is the exact caller and live event that attaches `Lup1$a` to that *same active renderer*, then which stream is currently consumed by the actual native decoder with selected Track/album/edition/duration/queue generation. A prepared queue holder, method call or field write alone is **not** a currently audible proof.

Scope next work only to exact `b.package`/interface k attachment dispatch and previous known `LmQ8.try/new` comparator, not all renderer APIs. A privacy-safe live witness at this specific event may be justified **after** static owner/caller is pinned and a new backup is saved. Log only non-identifying counters/boolean matches/queue-generation transitions, NEVER actual object values, metadata, URLs, tokens, field names, or audio. No second Player/decoder/AudioTrack, no replacement attempt or new APK before precise read-only observer is justified.

### Safety checkpoints

- Previous canonical code: `a63a900b16af8a998fc78dde4b111741bbf8390a`, backup `backup/android-a1-verified-stream-adapter-cfg-final-ci-green-20261117`.
- Original before-work backup: `backup/android-a1-pre-concrete-renderer-stream-audit-20261117` @ `98799bba2e94ba3283850357100bbdc713b8521c`.
- Concrete getter PASS backup: `backup/android-a1-renderer-concrete-getter-ci-green-20261117` @ `730e282b42661eab530b2050274bdca66e82213b`.
- Same-field writer PASS backup: `backup/android-a1-concrete-renderer-attached-stream-writes-ci-green-20261117` @ `e7b59f5166ffe7e4629bce7b10c76d4328a09d9d`.
- Native attach parameter PASS backup: `backup/android-a1-exact-renderer-stream-attachment-ci-green-20261117` @ `60fecaa2bcb7c34358a05342a3483cdab5d07062`.
- All changes **Python read-only static audit/fixture/CI/docs only**. Last runtime hooks `a655712d210189f3bc611847235de3ed4d985c1a`; no new APK, original Yandex, NAV17, Test.50, production, Windows, extension, API or database changes.
