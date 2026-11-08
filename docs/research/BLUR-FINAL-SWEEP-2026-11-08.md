# CELIKOM Blur — exhaustive final residual sweep, 08.11.2026

- 164 source candidates remaining after batch1000; 164 checked in read-only CI [run 42516451544](https://github.com/manufact-test/nomusic/actions/runs/42516451544).
- Strictly audio-valid MP3 sources: 119; technical rejects: 45 (9 Mp3Inspector, 35 MP4 MIME, 1 additional issue; see CSV); temporary download errors 0.
- Source content de-duplication removed one source ID `106479320` (Daleko), same Git blob as already-imported `105630453` (DALEKO); it must never be included again simply to reach a rounded count.
- Immutable final plan: `tools/blur-final/fixed-final.json` has **118 unique new Track IDs and 118 unique audio blobs**, total 761451096 bytes, groups 50+50+18. No production writes made by the sweep.
- Cumulative technical rejected list: **138** (historic 73 + batch1000 20 + final 45).
- Additional content duplicates in already imported sources listed in [BLUR-CONTENT-DUPLICATES.csv](BLUR-CONTENT-DUPLICATES.csv); pair `29508047` RAW and `29508038` Флора is pending and requires OWNER review, not auto-approval.
- 34 files outside source manifest remain separately classified: 28 without reliable artist/title mapping and 6 outside file size bounds.
- Expected 1526-file source balance when final 118 are imported: existing/suppressed 835 + batch800 200 + batch1000 200 + final 118 + cumulative technical rejects 138 + content duplicate 1 + outside manifest 34 = **1526**.
