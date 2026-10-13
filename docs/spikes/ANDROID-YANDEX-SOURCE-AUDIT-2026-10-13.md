# Installed-player source audit: exact track identity

Owner requires an actual source catalogue track ID, including songs absent from CELIKOM. Mutable metadata/artwork matching and Ynison/account-side integration are excluded. No replacement/UI development until automatic identity is physically proved. No USB or Play Protect disabling.

## Source provenance and limits

Yandex's own help links to its official RuStore listing: https://yandex.ru/support/music/ru/new-template/appmusic. Retrieved the public store package without account credentials, unpacked the download container, and verified the inner APK's v3 signature using apksigner. Analysed program files only; never executed the Yandex APK or read phone/private account data.

- Package: `ru.yandex.music`
- Store version: `2026.09.5 #167.1rur`, code `24026502`
- Inner APK SHA-256: `a65972608b532fa578c66649dfe50d37d1b2d1a31c491dd9cc3473629200a71a`
- Signing certificate SHA-256: `aca405ded8b25cb2e8c6da69425d2b4307d087c1276fc06ad5942731ccc51dba`
- Owner's tested installed version is `2026.09.5 #167gpr`, not this store variant. Do not claim the two binaries or runtime feature settings are identical.
- Subsequently obtained the matching GPR release from a public APKPure mirror: base APK version `2026.09.5 #167gpr`, code `24026501`, SHA-256 `a3e4d3aedd24ea0370ead4f25c4f0085a1f43b94e458ee949da86797df27fc61`. Verified its original Yandex v3 signing certificate (same SHA-256 above) and Google source stamp with apksigner before treating it as publisher code. No mirror description used as technical evidence. Its arm64/Russian-resource splits are available for inspection. A matching published release is not proof of the phone's runtime feature configuration.
- Selected source inspection with JADX 1.5.6 and compiled-manifest parsing with Androguard. JADX reported failures in some unrelated dependency methods; the simple selected methods below produced readable code. This is static source evidence, not physical proof on the owner's phone.

## Concrete findings

| Surface | Source finding | Consequence |
| --- | --- | --- |
| Local Relay service | Exported `ru.yandex.music.relay.service.RelayService` registers gRPC `relay.RelayGrpcService`, including `StreamStateUpdates`, `Version`, `CheckAuthorization`, `InvokeCommand`. Its caller policy checks Binder caller UID/package certificate against two allowed SHA-256 signing certificates. | An exported service is not automatically open to CELIKOM. Our signing certificate is not on the inspected allowlist. No live RPC call, command, certificate substitution or access-check bypass attempted. Exact current-ID payload contents are not claimed as verified. |
| Public metadata extras | The producer's `r6b.d` writes `dynamic`/`live` as booleans, duration as milliseconds, podcast/seekable flags, explicit type, widget control type and colour palette. | `dynamic` is not a hidden nested track object or an ID. This explains the observed keys; no metadata-based identification introduced. |
| Session activity | Session construction in `z7i.a` uses MainScreenActivity with action `ACTION_OPEN_PLAYER` and `need_expand=true`. | Inspected intent construction does not include a catalogue ID. Do not build an experiment assuming the session launch intent automatically contains the track link. |
| Equalizer launch | `har.invoke` constructs DISPLAY_AUDIO_EFFECT_CONTROL_PANEL with package name and audio-session number. | In this variant, opening CELIKOM via the equalizer does not deliver a track ID. |
| Audio-effect broadcast | `nkr.Q` constructs OPEN_AUDIO_EFFECT_CONTROL_SESSION with package name and audio-session number. | This broadcast also does not deliver a track ID in the inspected variant. Audio-session numbers remain separate from catalogue IDs. |
| Providers | Exported providers in the inspected manifest serve auth/SSO/analytics, not a declared music-track catalogue provider. | They were not queried. Do not treat auth transaction IDs or auth `track_id` literals as song IDs. |

The isolated literal `No track_id value in intent` resolves to a Passport/auth ActivityResult contract (`ri.parseResult`), not music-track sharing. This was explicitly rejected as an identity lead. Existence of a numeric `track_id` key alone is insufficient without the source's song semantics.

Confirmed the corresponding GPR implementation: RelayService registers the same two certificate hashes; its `glq.a` delegates Binder caller UID, PackageManager and this allowlist to `mxl.c`. Disassembly of `mxl.c` confirms UID package lookup, signing certificate/history lookup and signature comparison with rejection on failure. The GPR metadata extras producer `qtb.g` also writes `dynamic` as a boolean and the same public non-ID fields. This moves these two findings beyond the original RuStore-only comparison.

Also considered whether off-screen UI sharing could use a private virtual display without interrupting the phone. AOSP's Android 10+ activity-launch policy restricts ordinary virtual-display owners to their own activities; foreign activity embedding requires the platform permission and target's allowEmbedded opt-in. The inspected GPR MainScreenActivity does not opt in. No virtual-display capture/embedding or lock-screen workaround implemented or claimed as a background sharing solution. Sources: https://source.android.com/docs/core/display/multi_display/activity-launch and https://source.android.com/docs/core/display/multi_display/recommended-practices.

The AndroidX 1.8.0 standard legacy conversion copies the same MediaItem ID/URI, but Yandex can conditionally grant different permissions or data to a genuinely separate legacy connection. A bounded physical check of that difference is now implemented; its success is **not** assumed from source inspection. The disabled old MusicBrowserService remains untouched.

## Concrete next evidence supplied by 0.3.16

The diagnostic adds one independent framework MediaBrowser connection to the same enabled public Media3 library component, under CELIKOM's genuine package/UID and null hints. The report's `legacy_identity` records whitelisted current metadata, active queue item URI/extras and session/browser/playback extras. It sends zero playback/custom/library commands, stays separate from accepted Media3 state, and releases with the existing two-minute observation lease. Stale prior-process data is marked stale. Exact verification stays false until compared against real song links.

The code-export button provides the owner's actual GPR variant for inspection without USB: only APK manifests, resources tables and DEX code from installed base/splits. It does not read app account data, preferences, downloaded music or history. A deliberate user share grants access to the resulting bounded ZIP. It is an engineering source transfer, not required client onboarding. The inspected RuStore package contains 8 allowed static entries totalling 48,561,440 raw bytes, within the exporter limits.

No exact automatic identity source has passed physical acceptance yet. Do not assert the problem is solved, ask the owner to repeat accepted sound/route checks, or continue UI/replacement development. **Current owner step supersedes the earlier archive-export proposal:** obtain the new legacy report while a known song is playing. The matching signed GPR code was obtained autonomously, so no owner source archive is currently requested. The code-export feature remains available only if a later source/version difference actually requires it. The auto-sharing fallback remains unbuilt and its background/locked-screen operation unproven.

## Verified diagnostic delivery

0.3.16-probe, versionCode 17, same persistent CELIKOM signing key. Ready file: `CELIKOM-0.3.16-install.apk`, 8,433,798 bytes, SHA-256 `ce162aed28ab7a56ef7c19f2dc4180c4a3de9c4c3f1ad33916fb4619f74eae06`. Build at `5d20d9dbb7b7b9e8ecf36d593ece273634524249`, workflow `38314493898`, job `115027770133`, artifact `11776442099`. Lint/assembly passed; all 15 instrumentation tests passed independently on fullDebug and panelOnlyDebug (API35). The UI test now waits for the actual native frame and rejects a blank launch screenshot. Earlier compile/test-fixture failures were corrected; no unresolved product test failure remains.

Distributed APK parsed as panelOnly: only AttenuationService, no MusicListener/Accessibility service, no INTERNET or RECORD_AUDIO permission. v3 signature and ZIP CRC verified; debug fixtures absent. Saved APK bytes rechecked against the verified signed backup after final delivery save. Android physical exact-ID acceptance remains open; emulator fixtures are not Yandex ID evidence.

## Physical 0.3.16 result — 13 October 2026

Owner report generated at `1791875304875` on HONOR NTH-NX9 / Android 13 / Yandex `2026.09.5 #167gpr`. The independent framework connection returned `legacy_identity.status=connection_rejected` at `1791875289834`; the modern Media3 connection succeeded one millisecond later. Its fresh state at `1791875303945` shows «Вспышка», playing, position 185008 ms, duration 268380 ms, media_id `10`. No numeric source candidates or source URI are present. This closes this particular legacy test as unsuccessful; it is not a VPN/whole-player failure and does not justify another identical owner check.

`catalog_match.candidate_track_id=38436680` remains a metadata-derived diagnostic candidate and is explicitly excluded as exact source-ID evidence. The report is valid. Exact automatic catalogue identity is still unproved.

## Direct sharing source — GPR release

Static inspection of `dar.a(p9r, String, String)` confirms the track-specific branch takes `x9r.a` as the track ID and `x9r.b` as the optional album ID. It constructs `/album/{album}/track/{track}` or `/track/{track}`, then adds sharing query parameters. `s9r.a` puts the generated link into `Intent.ACTION_SEND` / `Intent.EXTRA_TEXT`, MIME `text/plain`. Unlike metadata matching, this path uses the source's own track object. These classes are internal code, not an exported callable API; knowing the implementation does not grant CELIKOM access to the live object's fields.

Existing manual ACTION_SEND receipt already proves that a deliberately shared song link can reach CELIKOM. It does not prove that the shared song is the current playing item, that UI sharing is automatic, or that sharing can run in the background/while locked. Do not promote manual link receipt to automatic identity acceptance. Next fallback experiment must operate on the visible current-player UI, distinguish its menu from playlist-row menus, capture the generated source link, and discard the result if the observed player changes during the transaction. No matching by title/artwork or forced private-component access substitutes for this evidence.

## Visible sharing experiment: separate shareProbe install

A separate `pro.celikom.nativeprobe.shareprobe` flavor is now supplied for one visible test. It does not replace the accepted native-probe install and cannot handle its equalizer launches. Its notification listener and attenuation service are absent; old launcher/equalizer activities and audio-session receiver are disabled. Accessibility is explicitly enabled by the owner. Android may apply additional installation/permission restrictions; no bypass is implemented.

One armed transaction has a 45-second monotonic deadline, reads only the active Yandex window, and permits up to three deterministic UI steps. It requires one visible `overflow_menu` under `player_container`; it rejects playlist-row/other-app/ambiguous/disabled controls. Then it clicks the unique visible «Поделиться» and, if present, «Ещё». It never selects another recipient or clicks the system chooser: the owner selects CELIKOM — проверка ID. Fresh Media3 state is required and a changed short player-item number aborts the transaction. Returning to the probe cancels unfinished work. The resulting source track ID stays `automatic_current_track_verified=false` until physical owner comparison; a stable short item alias alone does not prove source identity.

If the inspected resource IDs do not appear in the actual accessibility tree, the probe fails closed and reports a bounded list of visible clickable resource IDs/classes; no arbitrary screen text, screenshots, account data, notifications or clipboard contents are collected. Physical acceptance, background operation and locked-screen use remain unproved. This is a feasibility experiment, not the production client or universal automatic ID solution.
