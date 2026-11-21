# Two approved audio duration failures — 2026-10-14

Owner requested repair of Yandex tracks 50163040 and 48591588 after extension 0.4.37 reported `replacement_duration_or_token_invalid`. No extension/backend source release or global duration tolerance change was necessary.

Read-only private Hostinger audit: https://github.com/manufact-test/nomusic/actions/runs/38546595708
Repair and independent post-update catalog read: https://github.com/manufact-test/nomusic/actions/runs/38546943559

| Track | Replacement | Original duration ms | Old asset ms | New asset ms | Operation |
|---|---:|---:|---:|---:|---|
| 50163040 · SLIMUS — Холодно | 21 | 187520 | 189544 | 187507 | Trim only trailing silence |
| 48591588 · Баста — Моя игра | 18 | 270480 | 268826 | 270472 | Append silent MP3 frames at end |

The first file had approximately 2.563 seconds of trailing silence; the second ended approximately 1.654 seconds before the catalog duration. Input SHA256 matched the existing private asset records. Existing MPEG1 Layer3 44100Hz 320kbps stereo frames were preserved byte-for-byte, without transcoding music. Decoded existing PCM samples compared byte-identically through the edit boundary. The trimmed tail was independently checked below -45dBFS.

Both mappings remained approved and active with the same replacement IDs. New content-addressed assets 25 and 26 were created; mapping versions increased from 2 to 3 in one transaction, invalidating previous signed links. PHP Mp3Inspector independently confirmed the new frame durations and private storage hashes and sizes were verified. A separate post-commit read confirmed the two active mappings and durations. Original files and pre-update metadata were saved in a private `celikom/backups/duration-repair-*` directory; the old audio assets remain unchanged for rollback. Each mapping change has an `audio_trailing_silence_repair` audit record. No track identity, original duration, accounts, permissions, access, other mappings or application configuration were changed.

New hashes:
- 48591588: `d8b2b8bf5759edad3275f8dc7493b0377b2a05e4ab60e5020d7df561996df2e0`
- 50163040: `a311ed311137dfc5306fa2dd585f8d1c9d0bd73db55e84c21ec5875e50b3a3aa`

Owner playback validation is still pending: reload Yandex Music, press Start and play both tracks, checking the start, a seek in the middle and the ending/next-track transition. End-to-end musical alignment with the actual Yandex audio is not proven by file duration checks alone. No reference audio was downloaded from Yandex. PR #6 remains open/unmerged and Issue #7 remains open.
