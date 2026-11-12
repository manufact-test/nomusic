# CELIKOM Android A1 — real native ARM13 read-only AppMetrica exception witness (12.11.2026)

## Verified results

Owner-uploaded **publisher-signed 2025.10.4 120.1gpr** still verified from private draft. Frozen main and accepted Test.50 NOT modified. In isolated experimental branch `experiment/android-a1-2025-metrica-exception-witness-arm13-20261112`, LSPatch level 2 wraps verified publisher base first, then own clone name and signed 16→1 APK; original publisher 16 APK installed first and remains intact.

**[GitHub Actions run #43209513063](https://github.com/manufact-test/nomusic/actions/runs/43209513063)**, latest isolated lab with read-only own LibXposed module:

- Own module compile PASS. Module embedded, scoped to `pro.celikom.yandex.nativeclonelab`; fixed-event `ARMED` observed on exact MAIN PID. No vendor binary/logcat artifact published.
- Owner-visible exact Android application `Context.getPackageName()` and `ApplicationInfo.packageName` both classify as **CLONE** (not publisher-original). Their categorization is read-only and redacted, not a proof of all later SDK contexts.
- **Three constructor interceptions** for `IllegalStateException(String)` within AppMetrica SDK frames, all categorized **EXC_SDK_INIT**, background worker `OTHER`. The exception constructors' args and execution unchanged.
- JVM main fatal remains `JAVA_CRASH` / `ILLEGAL_STATE` on `KOTLIN_COROUTINE`, 1/25 resumed. **NO 75s native clone boot**, despite official publisher original 75s PASS, both apps concurrently installed.
- The witness did **not** observe `UNCAUGHT`; do not claim that a constructor interception is proven to be the exact fatal throwable or that there is no uncaught exception. It may be missed by a restricted hook or different throwable path.
- Additional previous [#43208287959](https://github.com/manufact-test/nomusic/actions/runs/43208287959) also observed 3 AppMetrica constructor interceptions (broad category OTHER). [#43209478139](https://github.com/manufact-test/nomusic/actions/runs/43209478139) matches latest; [#43209436952](https://github.com/manufact-test/nomusic/actions/runs/43209436952) had ARMED but 0 Metrica intercepts, consistent with versioned startup timing/instrumentation visibility. All product verdicts NO-GO.
- Earlier removing eight AppMetrica provider/service/receiver manifest components did **not** suppress SDK initialization nor fix clone [#43206543625](https://github.com/manufact-test/nomusic/actions/runs/43206543625).

### Engineering conclusion / required next discriminator

This is materially tighter than a generic `IllegalStateException`: the independent namespace has correct root `Context` package identifiers and an AppMetrica SDK init exception occurs. But a *causal* identity/SDK exception mechanism is **not yet proven**. Next: compare the in-process SDK `Context` and app lifecycle prerequisites in a controlled original-name vs separately named build, and determine whether the observed constructor exception is fatal or merely concurrent. Do not broadly suppress SDK exceptions, strip additional components blindly, spoof signing/user identity, leak raw stack/message/credentials, or report working audio before main 75s PASS.

**Landmark success remains** [#43204916823](https://github.com/manufact-test/nomusic/actions/runs/43204916823): independent one-APK LSPatch2 with `ru.yandex.music` preserved **75s native MAIN PASS**, proving split merge itself works; cannot coexist with stock publisher installation under same Android package name.

**Gates:** Stage A NO-GO / Stage B LOCKED. B42 signed audio/Range contract exists but has not been connected to verified native host. No owner handset, login, music, pause, seek, Next, MyWave, real audible swap, production files or Play Protect acceptance tested.

Backup before scoped witness experiments: `backup/android-a1-2025-before-metrica-exception-witness-20261112`; fixed prior observed witness backup: `backup/android-a1-2025-readonly-metrica-3exceptions-native-evidence-20261112`; current branch must be snapshotted before next mutating step.
