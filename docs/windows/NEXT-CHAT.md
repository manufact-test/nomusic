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

