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

A separate `pro.celikom.nativeprobe.shareprobe` flavor is now supplied for one visible test. It does not replace the accepted native-probe install and cannot handle its equalizer launches. Its notification listener, attenuation service, old launcher/equalizer activities and audio-session receiver are absent. Audio-specific source and tests reside in shared directories included only by full/panelOnly; the shareProbe build does not compile or package them. Their component declarations and permissions live only in the two audio flavors, and are not present in the sharing manifest. No lint checks are suppressed. Accessibility is explicitly enabled by the owner. Android may apply additional installation/permission restrictions; no bypass is implemented.

One armed transaction has a 45-second monotonic deadline, reads only the active Yandex window, and permits up to three deterministic UI steps. It requires one visible `overflow_menu` under `player_container`; it rejects playlist-row/other-app/ambiguous/disabled controls. Then it clicks the unique visible «Поделиться» and, if present, «Ещё». It never selects another recipient or clicks the system chooser: the owner selects CELIKOM — проверка ID. Fresh Media3 state is required and a changed short player-item number aborts the transaction. Returning to the probe cancels unfinished work. The resulting source track ID stays `automatic_current_track_verified=false` until physical owner comparison; a stable short item alias alone does not prove source identity.

If the inspected resource IDs do not appear in the actual accessibility tree, the probe fails closed and reports a bounded list of visible clickable resource IDs/classes; no arbitrary screen text, screenshots, account data, notifications or clipboard contents are collected. Physical acceptance, background operation and locked-screen use remain unproved. This is a feasibility experiment, not the production client or universal automatic ID solution.

### Verified sharing probe delivery

`CELIKOM-ID-0.1.0-install.apk`, package `pro.celikom.nativeprobe.shareprobe`, versionName `0.1.0-share-probe`, versionCode 1. 8421566 bytes; SHA-256 `e44cdd00cc527625ba3c7fa8603631168bdf640648ceeedd0ceca0a894501bd9`. Native build `41e7397514dbf2d30d38aa5642f4989c01064624`, workflow `38369096948`, job `115201324894`, artifact `11798871414`. Lint/assembly succeeded; 15 fullDebug, 15 panelOnlyDebug, and 4 shareProbeDebug instrumentation tests passed on API35.

Verified persistent signing certificate, minSDK33 signature validation, ZIP CRC, non-debuggable APK and absence of debug fixtures. Parsed final APK: audio service/equalizer/old launcher/audio-session receiver and notification listener absent; no INTERNET/RECORD_AUDIO permission. Accessibility configuration resolved through its compiled resource table and restricted to `ru.yandex.music`. Saved APK bytes match the independently verified backup. Physical current-ID acceptance remains pending.

Owner check: play a song and open Yandex's full player; open the separate CELIKOM — проверка ID launcher; explicitly enable its Accessibility service via button 1; use button 2 and wait for fresh song state; button 3 opens Yandex and arms one transaction. If the share chooser opens, manually select CELIKOM — проверка ID. If it does not open within 15 seconds, return without clicking Yandex menus. Copy the report in either case. Keep the screen unlocked for this first test.

## Physical installation rejection — sharing probe, 13 October 2026

Owner reports that Google Play Protect completely blocks the 0.1.0 sharing APK with no Details/install-anyway option. Therefore emulator success is not installation or physical identity acceptance. Do not ask the owner to repeat this package installation or treat the sharing experiment as ready for client distribution.

The sharing flavor introduces BIND_ACCESSIBILITY_SERVICE. Google developer guidance explicitly lists accessibility declarations among sensitive permissions that can cause automatic blocking of internet-sideloaded APKs: https://developers.google.com/android/play-protect/warning-dev-guidance . This is the leading explanation, not a device-verdict attestation. The original accepted 0.3.16 APK remains available and byte-identical (SHA-256 ce162aed28ab7a56ef7c19f2dc4180c4a3de9c4c3f1ad33916fb4619f74eae06); it has no accessibility/notification listener.

The visible auto-share route is blocked under the owner's ordinary sideloading constraints. Removing the accessibility service would also remove its UI-automation capability, so do not issue a permission-stripped APK as a working automated-ID fix. Do not disguise the service, mislabel isAccessibilityTool, rotate identities, suggest disabling Play Protect, or contact Google without authorization. Manual sharing is already established and does not pass the automatic-current-ID gate.

## Post-block investigation: public source identity boundary

Inspected the matching signed GPR base APK (SHA-256 a3e4d3aedd24ea0370ead4f25c4f0085a1f43b94e458ee949da86797df27fc61), not a substituted publisher variant. No new APK, permissions, account access or owner test was introduced.

### Catalogue ID and public item alias are different fields

The current Media3 metadata producer `aiz.s(int)` obtains the playable through `g0m`, derives NotificationMeta `qfk`, constructs whitelisted metadata with `qtb.g`, and constructs the public MediaItem using `g0m.b()`. The track implementation `oju` exposes the private song through `a()` and a separate `i` field through `b()`. Its own diagnostic string labels these fields `trackId` and `playableId`, respectively: catalogue ID is `jbu.a`; public alias is `oju.i`. The synthetic TrackPlayable constructor supplies this alias using `m0m.b()`, which increments an AtomicInteger and returns its decimal string. Thus the actual catalogue ID exists inside Yandex, but its mere existence does not make it readable from CELIKOM. This explicitly explains the short public IDs in the owner's reports without treating them as source catalogue IDs.

`qfk` carries title, subtitle, album, artist, cover and duration, not catalogue identity. The inspected public metadata assembly adds rating and known boolean/duration extras; it does not publish the internal song object, source ID, source URI or hidden track-ID-bearing text.

### Library commands are restricted by genuine caller identity

The actual public service uses `q7i.a` and an `agi` callback. Its connection path delegates through `xli` to `wni.a(uid, package)`. This checks the package's UID, then distinguishes own/system UID, package+signing-certificate allowlist, platform signing certificate and granted privileged media/notification-binding permissions from an unknown caller. Unknown callers do not receive library access. Ordinary application declarations cannot grant those signature-level permissions. This supports the physical lack of getItem/search/root commands and does not justify another spelling/connection-hint experiment, caller spoof or allowlist impersonation. Granting library commands would not itself prove a catalogue-ID payload.

### Widget and legacy conversion do not expose an independent current ID

`WidgetRecentlyRectangleReceiver` and `WidgetRectangleReceiver` resolve the same `egx.k` / `fzo` implementation. Its current-player `shx` model contains a cover bitmap, title, subtitle, explicit type, button models and color type. `rhx` is the loading model, not a recent-track list. The button models examined contain state flags or singleton commands, not a current source song ID. The widget navigator `wfx.b()` opens MainScreenActivity with ACTION_OPEN_PLAYER and need_expand=true, without a song ID. Therefore do not build a widget host merely to extract its main-player PendingIntent or infer current identity from a recent-item ordering.

Pinned AndroidX 1.8.0 MediaSessionLegacyStub copies current MediaItem.mediaId and requestMetadata.mediaUri; LegacyConversions maps the same values to framework metadata. Access to a framework token would not manufacture an independent source ID. The owner's already-rejected separate framework connection remains final evidence for that tested route.

### Broadcast candidates classified

DEX string and sendBroadcast-call-site scans were followed by source checks; byte-pattern hits are leads, not complete call-graph proof. `rjr.Q` sends OPEN_AUDIO_EFFECT_CONTROL_SESSION with session number and package only; `ybr` closes it with the same fields. `h4p` sends APP_READY under RELAY_PERMISSION with no song payload. `up2` and `fc4` send package-scoped VPN UI events. `bii` launches the SystemUI media-output dialog with package information. `ofz.r` forwards Cast control actions to an explicit component without a song payload; its separate media-button handler reads key events. `b4q.m` is a WhatsApp OTP SDK request, and `ttp` is a GMS registration RPC. Glance's `cwy.K` forwards widget action intents; it is not a song-change publisher. `jyj` was a scanner false positive: its static initializer is a network-subtype enum. No externally readable exact-current-track broadcast was identified in these inspected paths; this is not a proof that all possible future builds or runtime-generated channels are absent.

### Current feasibility result

The exact ID is located in Yandex's internal track model and direct sharing-link construction, but no automatic local channel accessible to an ordinary separately installed CELIKOM application has been demonstrated under the owner's current constraints. Manual sharing remains an actual source-ID channel; it does not meet automatic-current-track requirements. The Accessibility sharing prototype is withdrawn after physical installation rejection. Do not ship another build that merely renames the package or removes the capability and claims the identity problem fixed. Accepted audio/playback-state work remains intact; full replacement and client UI remain gated on source identity. No owner check is pending from this investigation.

## Continued investigation: Android assistant context

Investigated a separate public mechanism after the owner asked to resume: Android AssistContent / AssistStructure delivered to the user-selected assistant. This is not an Accessibility service or notification listener, but it still requires assistant selection and foreground contextual collection; it is not a background ID API. No assistant APK was built or proposed for owner installation.

An exhaustive DEX string/method-table pass over the matching GPR base found no AssistContent type, onProvideAssistContent/onProvideAssistData override, registerOnProvideAssistDataListener call, setWebUri/setStructuredData call, or onGetDirectActions/onPerformDirectAction implementation. The apparent setAppSearchData lead belongs to androidx.appcompat.widget.SearchView, not an AppSearch source-track index. These findings cover statically named implementations in this inspected binary, not hypothetical reflection, downloaded code, or all future releases.

Pinned AOSP Android 13 ActivityThread.handleRequestAssistContextExtras first copies Activity.getIntent() into AssistContent with setDefaultIntent, then invokes onProvideAssistContent. The base Activity hook is empty. Yandex MainScreenActivity.onNewIntent stores the incoming launch intent with setIntent(intent); this is not a song-change-to-source-URI publisher. An incoming deep link may identify the item originally opened, but it is not verified current identity after queue transitions. A default AssistStructure can carry screen text; that cannot replace the owner's exact source-ID requirement with title matching. No current-ID-bearing assistant channel was established, and no owner test is pending.

Primary platform references:
- https://developer.android.com/training/articles/assistant
- https://developer.android.com/reference/android/app/assist/AssistContent
- https://github.com/aosp-mirror/platform_frameworks_base/blob/android-13.0.0_r1/core/java/android/app/ActivityThread.java
- https://github.com/aosp-mirror/platform_frameworks_base/blob/android-13.0.0_r1/core/java/android/app/Activity.java

Engineering limit remains explicit: finding the private catalogue ID in source does not grant a separately installed app access to the live object. Sound replacement and public playback-state feasibility remain accepted; automatic catalogue identity is not solved. Do not disguise protected access as a parser fix or keep creating owner test builds without an actual source-ID-bearing channel.

## Further continuation: command buttons and incoming sharing requests

Investigated Media3 command-button layout separately from the earlier available-command and session-extra report. AndroidX 1.8.0 exposes getCustomLayout and getMediaButtonPreferences as public read-only accessors. The existing 0.3.16 physical report did not inspect button extras, so its empty command extras alone were not used to rule this path out. No playback/like/dislike commands were sent to the owner's device.

Matching GPR source trace: wyf.f (onPostConnect) supplies ycm.t.g as the custom layout. ycm.t is s7i (Media3State); e4j case 8 feeds it from t7i. The playing-state branch of t7i.invokeSuspend constructs its command set from constant f8i commands and the xwq button factory; sessionExtras is a newly allocated empty Bundle. The current source-track object is not put in that bundle. The normal button models are reused from lazy xwq fields, with static resource icons, translated labels and constant commands. The builder tq5 initializes button extras with Bundle.EMPTY; the inspected xwq media-button branch does not replace it. rcq cases 8–15 construct the stub/seek/like/dislike command objects with Bundle.EMPTY. Therefore no source-ID-bearing button payload was found in this inspected ordinary song path; there is no reason to ask the owner to install another button-only diagnostic. This is source evidence for the inspected version/path, not a universal claim about every podcast, future version or runtime extension.

Also inspected MainScreenActivity.F incoming actions and the extra.fragment.on.current.activity route. Its named actions cover opening destinations, playback/video, shortcut reporting and communication; no direct external request to return/share the live current song was identified. The fragment extra is actually a URL passed through hev.d -> dev.a, not an arbitrary fragment constructor. dev registers many route parsers and an explicit sharelogs route; sharing logs is not sharing a song. The full set of those individual route parsers has not been exhausted, so do not claim every deep link is disproved or invent a working current-share URI. TrackShareScreen references found by a string-xref scan were internal screen identifiers, not an exported sharing activity.

The exact-current-ID gate remains open. No new APK was built, no permissions were changed, and no owner checks are pending from this continuation. Preserve working 0.3.16 audio/state and the withdrawn status of the physically blocked Accessibility experiment.

Primary API source: https://github.com/androidx/media/blob/1.8.0/libraries/session/src/main/java/androidx/media3/session/MediaController.java . Static evidence remains tied to the signed matching GPR APK recorded above.

### Follow-through on registered URL patterns

Extracted URI/current/share/player string references from the 52 static route-pattern holder classes named in dev's registration list. The scanner produced 113 references in those classes; none names a current/share/player route. This is a byte-pattern lead scan, not semantic validation of every parser. The direct dev-level sharelogs pattern remains diagnostic-only. Independently decompiled yxh's generic yandexmusic://open pattern and omu's ordinary /track/{value} patterns. These accept navigation inputs; no current-song-to-CELIKOM output channel was established. Dynamic registrations, query-driven behavior and the two helper-added route groups are not claimed exhausted. Do not describe arbitrary incoming /track/current text as an actual catalogue ID returned by the playing source.

Confirmed the button builders separately: tq5 stores Bundle.EMPTY for button extras, rcq's media-control command factories also use Bundle.EMPTY, and xwq's media-control branch does not inject track identifiers. The read-only command-button hypothesis is closed for the inspected ordinary-track construction path. Current automatic identity remains unresolved.
