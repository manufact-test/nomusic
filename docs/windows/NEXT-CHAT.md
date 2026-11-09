# W22 CURRENT HANDOFF — independent native source adapter (2026-11-09)

**Owner invariant still unchanged:** one normal CELIKOM installer with the real Yandex Music desktop UI and native Yandex playback, Play/Pause/Seek/Next/queue. No second player, password collection for Yandex, terminal, sandbox/VM or manual mod work for customer. Owner's PC **was not modified** by W20–W22. Do not send any W20/W22 internal artifacts to owner as a working product.

**Latest code branch:** `experiment/windows-companion-integration-20261108`. W20 verified internal installer, W21 independent recovery core, W22 independent source-only file-info adapter. Current handoff source `windows-companion/w22/README.md`, `windows-companion/w21/README.md`, `docs/windows/W22-INDEPENDENT-ADAPTER-HANDOFF-20261109.md`.

## Actual new verified work
- **W20** [CI 42596579243](https://github.com/manufact-test/nomusic/actions/runs/42596579243) SUCCESS. Internal per-user installer installs/uninstalls CELIKOM-owned EXE; never bundles or edits Yandex. Not signed, no audio, not for owner.
- **W21** [CI 42598726742](https://github.com/manufact-test/nomusic/actions/runs/42598726742) SUCCESS. `W21_RECOVERY_CONTRACT_PASS 20`, zero build warnings. Independently written source `windows-companion/w21/Celikom.Recovery`: backup with exact original hashes, no overwrite, registered-known-modification restore, refusal for foreign update/tamper, partial crash recovery. **Fixture tests only; no real Yandex file restored by W21.**
- **W22** [CI 42599679157](https://github.com/manufact-test/nomusic/actions/runs/42599679157) SUCCESS. 13/13 independent source-hook contract tests; 10/10 W15 legacy Node source checks; 44 native .NET bridge/MIME checks. `windows-companion/w22/native-resource-adapter.mjs` uses Yandex file-info resource response structure (studied from MIT FkCensor) without PulseSync Client or PulseSync GPL SDK, retaining Yandex's playback clock, queue and transport methods. Exact licensed CELIKOM signed grant, MP3/AAC transport, bounded request fallback, cancellation on Next/Stop, batch prefetch and clean hook disposal. **NO Yandex host injection or real audio tested**.
- **W15 MIME correction:** `SourceGrant` carries `MimeType` from signed server response to independent adapter; `audio/mpeg` and `audio/mp4` remain validated. 44 native checks pass.
- **Backup before W21:** `backup/windows-w21-before-recovery-engine-20261109`; pre-W20 `backup/windows-w20-pre-safe-installer-20261109` and previous accepted baselines remain untouched.

## Real blockers
1. **Actual source hook has NOT run in the real installed signed Yandex.** W22 is the source mapping kernel only. Need a genuine desktop insertion point and developer-controlled authenticated playback of one approved track with Pause/Seek/Next/fallback.
2. **Unsigned modified third-party EXE.** MIT FkCensor's installer replaces ASAR and EXE hash in its own approach; this, like W17 PulseSync, can invalidate official Yandex Authenticode. W20's own EXE signing alone cannot solve that. No bypass/hidden modification.
3. **Yandex Windows license sections 4.1–4.3** [official terms](https://yandex.ru/legal/music_mobile_agreement/ru/) restrict third-party changes and commercial distribution without permission (subject to statutory exceptions); written rights / legal review needed before commercial modified-client distribution. MIT FkCensor license allows reuse of **its** code, not Yandex EXE/music. W22 itself is newly written and does not import PulseSync GPL SDK.
4. **Installer integration incomplete.** W20 stage still installs only own companion; W21 rollback and W22 source adapter are internal isolated libraries, not wired to a user installer, and no code signing or Win10/11 owner acceptance.

## Next work
- Audit/implement an independent version-gated **host connector** that can attach W22 resource adapter to the actual 5.126.1 renderer in a disposable developer Windows, without extracting user credentials or changing security settings. Keep all patching outside W20 consumer build, and enforce the exact W21 recovery lifecycle before any experimental modification.
- Confirm signed grants + Range 206 and native Yandex Play/Pause/Seek/Next with an authorized separate music test account; static or anonymous launch is NOT audio E2E. Request no Sandbox/VM or development setup from owner.
- Settle contractual rights and Windows trust/distribution design; only then wire W21+W22 to a **single** reversible, transparently consented installer and hand one meaningful candidate to owner. If unable to obtain legal rights, state blocker directly, do not build an unsafe silent patcher.
- No Android, browser extension, API/backend, website or production changes.

---
# W20 VERIFIED INTERNAL INSTALLER CHECKPOINT (2026-11-09)

Read [W20 release-safety decision](W20-RELEASE-SAFETY-AND-INSTALLER-20261109.md). A developer-only single EXE installer stage (Windows [CI 42596579243](https://github.com/manufact-test/nomusic/actions/runs/42596579243) SUCCESS, 43 native contract checks, install/uninstall smoke PASS) and read-only pinned Yandex host signature/hash probe are added to the experimental Windows branch. **NOT a user build or proof of native audio.** Primary Yandex Windows app EULA 4.1–4.3 and PulseSync Client EULA 3.1 make modified/bundled commercial distribution contingent on explicit rights/appropriate legal assessment. The release gate fails closed. No owner Sandbox or other manual work. Last W15.2 verified UI/audio status remains as below. Pre-W20 source protected at `backup/windows-w20-pre-safe-installer-20261109`.

---

# CELIKOM Windows — current handoff after W19 (2026-11-09)

**OWNER'S LATEST DECISION SUPERSEDES EARLIER NEXT-STEPS:** Stop sending the owner through Windows Sandbox, Windows Optional Features, Hyper-V, a manual PulseSync installer, or VM setup. The owner has Windows 10 **Pro** 22H2 (OS build **19045.6456**), runs **official Yandex Music 5.126.1.0**, and has explicitly rejected the fragmented W19 manual test path. **User-facing goal is one normal branded CELIKOM installer/application.** A person installs it once, starts CELIKOM alongside the normal Yandex desktop UI, logs into Yandex *in Yandex*, and CELIKOM automatically swaps only approved track sources. Yandex owns its original decoder, queue, Play/Pause/Seek/Next/media keys. **No second audio player, no embedded web replacement, no manual mods, no security disabling, no terminal/VM work for end users.** Internal integration may involve a disclosed version-compatible modification if safe, recoverable and legally distributable; never secretly modify Yandex, violate user consent or conceal protections.

**Do NOT ask for yet another W19 manual test or to enable Sandbox.** Owner already launched W19 launcher: terminal said `Windows Sandbox is not available on this Windows installation`; nothing installed/changed. A later `winver` screenshot confirmed Windows 10 Pro 22H2, and assistant suggested `optionalfeatures.exe` + enable Sandbox. **Owner explicitly rejected this approach.** No optional Windows feature should be enabled. W19 is CLOSED/UNEXECUTED for audio; see [W19 closure](W19-WINDOWS-SANDBOX-AUDIO-TEST-20261109.md).

## Repository checkpoint

- Repo `manufact-test/nomusic`; branch `experiment/windows-companion-integration-20261108`.
- **Last verified executable build:** W15.2, [Windows CI 42584873865](https://github.com/manufact-test/nomusic/actions/runs/42584873865) SUCCESS, [Actions artifact `CELIKOM-Windows-W15.2-PREVIEW`](https://github.com/manufact-test/nomusic/actions/runs/42584873865) (artifact ID `13659290184`). Contains self-contained `CELIKOM.Companion.exe` + `CELIKOM-Addon.pext`, **not** a consumer installer or proven end-to-end audio integration.
- Windows Companion source `windows-companion/w15/Celikom.Companion` (.NET 10 WinForms), addon `windows-companion/w15/addon`, bridge `windows-companion/w15/{source-controller.mjs,bridge-client.mjs}`, tests `windows-companion/w15/w15-contract.test.mjs`, `.github/workflows/windows-w15-preview.yml`.
- **Owner UI smoke:** W15 native window launched on their PC after SmartScreen unknown-app warning; screenshot confirms window, buttons, pairing code. User did **not** verify music or login.
- **Isolated genuine installations:** W16 [CI 42583615051](https://github.com/manufact-test/nomusic/actions/runs/42583615051) verified authentic signed Yandex installer and exact ASAR checksum. W17 [CI 42584625023](https://github.com/manufact-test/nomusic/actions/runs/42584625023) installed real PulseSync Client 3.0.3-beta/mod v2.1.5 with Defender realtime enabled; **vendor EXE Authenticode became `HashMismatch`**, then both original EXE and ASAR were restored byte-identically and signature valid. W18 [CI 42585206639](https://github.com/manufact-test/nomusic/actions/runs/42585206639) also imported actual CELIKOM addon (.pext) and launched modified Yandex process in disposable Windows Server 2022, original restored afterward. **No account, playback, audible substitution, pause, seek, Next or Windows 10 user security reputation tested**. Green CI cannot certify those things.
- Official owner Yandex `app.asar` SHA256 `5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215`; W10 ASAR integrity enabled. PulseSync-mod v2.1.5 says 5.126.1 but spoofs from 5.125.3 — do not claim guaranteed full compatibility.
- All previous owner-approved backup branches preserved. The new handoff checkpoint gets a **new** backup branch; do not force push or rewrite older refs.
- No Android, browser extension, server, production branch or owner's normal Yandex were changed by W19.

## Product blockers: do not hide

1. **Actual Yandex playback not proven.** Need source substitution on one approved track and native pause/seek/Next/original before calling this an operational music application.
2. **Publisher trust:** PulseSync mod alters Yandex EXE and makes Yandex's original Authenticode **invalid**. Signing only CELIKOM.exe cannot fix Yandex's invalid original signature. Do not claim that code signing alone makes modded Yandex acceptable or that Microsoft Defender/SmartScreen warnings will disappear. Commercial user deployment requires a defensible trust/distribution design and honest installation disclosure.
3. **Distribution rights:** PulseSync-mod MIT does not cover PulseSync Client's restrictive commercial license nor Yandex binaries or music. Obtain rights or design independently licensable integration; don't bundle proprietary components without permission.
4. **Installer and recovery:** no safe one-click installer, update-version gate, real Windows 10/11 test, uninstall/verified backup restore, support policy or production release yet.
5. **W19 sandbox pack** was a *testing artifact*, not a product, and its need for optional Windows features is unacceptable to owner/end users.

## Next work for new lead (one large, coherent block; do not restart W0–W18)

1. Audit W15 actual code and W17/W18 evidence; eliminate unsupported claims and fragile assumptions. Choose a **consumer-grade** integration/distribution design: first evaluate whether a transparent, permissioned, independently licensable and supportable approach can preserve security with normal Windows protections. If PulseSync patch requires an invalid Yandex signature, explicitly assess whether that path is releaseable; do not mask it.
2. Build the **single branded CELIKOM installer + companion + source integration** on an experimental branch, with version checks, atomic backup/recovery and uninstall, no manual mod steps, no separate music player. Do not ship a misleading stand-alone UI pretending that source replacement works.
3. Run every available automated check. For the *necessary* audio validation, arrange a **developer-controlled** isolated, interactive Windows test with a legitimate test music account and no owner's personal login; if unavailable, state exactly the remaining test gate instead of making owner configure Windows. Only request **one** meaningful owner test after a real candidate is ready and safety checked.
4. Do not promise "no false-positive ever"; normal Defender and SmartScreen must remain ON and no hidden injection, signed EXE bypass, profile/token extraction or silent repatching is acceptable.
5. Update the handoff docs and protected backup after a real milestone. Report to owner concisely in Russian: what changed, what works *verified*, what's blocked, and a single next action.

**Important:** older documents below and archived [W0–W19 handoffs](W0-W19-NEXT-CHAT-ARCHIVE-20261109.md) are historical and MUST NOT override this latest scope. Current source of truth: [owner correction](W19-OWNER-PRODUCT-CORRECTION-20261109.md).

