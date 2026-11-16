# CELIKOM Android A1 — documentation entry point

**Last reconciled:** 16 November 2026  
**This is an index, not a history dump.** For current work, follow only the canonical documents below.

## Current source of truth

1. **[NEXT-CHAT.md](NEXT-CHAT.md)** — canonical current status, exact checkpoint, version matrix and next task. If any older note conflicts with it, this file wins.
2. **[ANDROID-A1-LFT2-TRACKWRAPPER-CONTINUATION-20261116.md](ANDROID-A1-LFT2-TRACKWRAPPER-CONTINUATION-20261116.md)** — latest technical proof from CI #229 and exact stopping point.
3. **[NEXT-CHAT-START-MESSAGE-20261116.md](NEXT-CHAT-START-MESSAGE-20261116.md)** — copy/paste prompt for the next chat; it mirrors NEXT-CHAT and is not an independent source of truth.

Read only when needed:
- [ANDROID-A1-EXTERNAL-PLAYBACK-RESEARCH-20261116.md](ANDROID-A1-EXTERNAL-PLAYBACK-RESEARCH-20261116.md) — public Media3/Yandex findings; search guidance, not proof of Yandex internals.
- [ANDROID-A1-NAV17-OWNER-REAL-MUSIC-GREEN-STAGE-B-SOURCE-ADAPTER-20261114.md](ANDROID-A1-NAV17-OWNER-REAL-MUSIC-GREEN-STAGE-B-SOURCE-ADAPTER-20261114.md) — owner-confirmed Stage A / NAV17 acceptance and original playback; replacement audio is still not integrated.
- [ANDROID-A1-TRUE-ARM13-SIGNED-YANDEX-ORIGINAL-CONTROL-20261111.md](ANDROID-A1-TRUE-ARM13-SIGNED-YANDEX-ORIGINAL-CONTROL-20261111.md) — verified 2026.10.3 #170gpr original-only ARM13 control.
- [ANDROID-A1-2025-DISTINCT-ONEAPK-NATIVE-75S-LAB-LEAD-HANDOFF-20261112.md](ANDROID-A1-2025-DISTINCT-ONEAPK-NATIVE-75S-LAB-LEAD-HANDOFF-20261112.md) and [ANDROID-A1-2025-LSPATCH2-NAMESPACED-COEXIST-NATIVE-RESULT-20261112.md](ANDROID-A1-2025-LSPATCH2-NAMESPACED-COEXIST-NATIVE-RESULT-20261112.md) — 2025.10.4 laboratory clone experiments only.

## Version chronology — do not merge these roles

| Yandex build | Verified facts | Role / limitation |
|---|---|---|
| **2025.10.4 #120.1gpr**, code 24025542 | Original signed XAPK 45,961,661 bytes; SHA-256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`; 16 splits / 6 DEX. CI #229 uses this exact specimen. | Static LfT2 audit specimen and earlier LSPatch2 lab-clone input. **Not yet proven as the final CELIKOM runtime target.** |
| **2026.10.3 #170gpr**, code 24026531 | Original publisher-signed XAPK 60,433,885 bytes; SHA-256 `918bd50599dc6a942e190a409303e843b83dcb6d11b90b03c00240331333cf84`; 5 splits. CI [#42990078186](https://github.com/manufact-test/nomusic/actions/runs/42990078186) verified stock original installation and native ARM13 MAIN launch. | Verified newer original-app control; also used by a separate structural clone research helper. **That does not prove it is the selected product runtime target.** The cited control did not test clone, login, audio or Play Protect. |
| **2026.09.5 #167gpr / #167.1gpr** | Previously reported as the owner's handset version. No exact original package + verified SHA is pinned in the current A1 evidence. | Owner-device observation only; not a verified analysis specimen. |

`#170rur` and `#170gpr` are different distribution-channel builds. Do not conflate them. The `<queries><package name="ru.yandex.music"/></queries>` manifest entry means Android package visibility; by itself it proves neither that Yandex code is embedded nor that it is absent. Inspect packaged DEX/resources and build inputs.

**Product target remains unresolved.** The three builds above have different evidence roles. Determine which exact original package the intended CELIKOM A1 product build is based on from packaging/source inputs and owner decisions. If no source-of-truth answer exists, ask the owner once, presenting all three roles. Do not ask the false binary question “2025 or 2026.09.5?” and do not infer target from the newest version number.

## State timeline and precedence

- **12 Nov:** 2025.10.4 #120.1gpr LSPatch2 one-APK experiments. Laboratory outcomes only; old notes saying Stage A NO-GO describe this earlier state.
- **11 Nov:** 2026.10.3 #170gpr untouched original verified on native ARM13 as a control. This is not the current LfT2 static-analysis binary.
- **14 Nov:** NAV17 owner confirmation: real Yandex account/UI and original music work in CELIKOM. **Stage A PASS**; this did not prove CELIKOM replacement audio. [Owner evidence](ANDROID-A1-NAV17-OWNER-REAL-MUSIC-GREEN-STAGE-B-SOURCE-ADAPTER-20261114.md).
- **15 Nov:** static AudioTrack/ByteBuffer sink research; selected Track → decoder identity remained unproven.
- **16 Nov:** CI #229 proves TrackWrapper identity only through `LfT2.<init>` on the 2025.10.4 specimen; no same-object edge to source/Player/decoder. CI #230 reduces audit log output by ~97.3%.
- **Current product gate:** Stage A / NAV17 PASS by owner confirmation. **Stage B NO-GO / not connected** until the selected track is proven at the native source/decoder and an approved replacement is heard.

## Historical material

[archive/README.md](archive/README.md) identifies superseded handoffs and large historical notes. They are retained as evidence, not current instructions. Do not read the whole folder or treat a filename containing “NEXT-CHAT”, “CURRENT” or “HANDOFF” as proof that the file is current.
