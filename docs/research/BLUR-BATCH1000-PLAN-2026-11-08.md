# CELIKOM Blur — batch1000 planning, pinned 08.11.2026

- Source: `Hazzz895/FckCensorData` SHA `10187b7af56f311fe141a3c9b75483798bf0f589`.
- Live SELECT-only eligible before reject filter: 407; known rejected filtered: 23; untried: 384.
- Strict independent source validation: 220 tested, 200 valid MP3 pinned (MIME, Git blob, duration by ffprobe & Mp3Inspector), 20 new technical rejects, 0 transient errors, 0 production writes.
- Pin: `tools/blur-batch1000/fixed-plan1000.json` with exactly 200 unique Yandex Track IDs, total 1253877244 bytes, 4x50.
- Cumulative recorded rejects: 93 (previous 73 + 20 new).
- Prior batch 918–1117: 200/200 approved+active, HEAD 200 and Range 206 and bytes PASS, [read-only audit](https://github.com/manufact-test/nomusic/actions/runs/42515169858).
- Plan source [CI](https://github.com/manufact-test/nomusic/actions/runs/42515169953); file uploads are NOT yet made by this plan.
- Remaining after this selection: 164 unverified IDs in original candidate pool; 34 outside original candidate pool require separate triage.
- Never auto-approve, set rights, or modify main/Android/Windows/extension.
