# CELIKOM Blur — 34 source files missing from the validated candidate manifest (08.11.2026)

Pinned source tree contains 1526 track files. Original batch800 candidates manifest lists 1442 entries, with 50 historic rejects excluded. The other **34** track files have now been independently enumerated and recorded in [BLUR-SOURCE-GAPS.csv](BLUR-SOURCE-GAPS.csv).

- **28** track IDs have ordinary file sizes but no matching artist/title row in the source README and cannot safely be mapped to the right Yandex track, so they are **unmapped**, not considered tested or imported.
- **2** empty files (0 bytes), **2** files under 1024 bytes and **2** above the 25 MB MP3 importer limit; these 6 cannot pass the existing source-size guard.
- This list is separate from the **93 cumulative technical rejects** among previously examined manifest candidates (includes batch1000 preflight failures).
- Do not fabricate metadata, treat missing labels as valid, or change the importer and existing source policy solely to hit a round number.
