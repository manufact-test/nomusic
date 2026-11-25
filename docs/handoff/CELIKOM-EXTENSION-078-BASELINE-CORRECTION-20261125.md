# Baseline correction — accepted extension0.4.78,25 November2026

## Owner correction and canceled instructions

The owner confirms final pre-migration browser extension was0.4.78. Earlier advice to reinstall0.4.73 as the control was WRONG and is canceled.0.4.73 remains a historical reference, not the latest accepted client. Prior statements warning against importing0.4.77/78 merely because their branch was unmerged are superseded. Do not discard already delivered/accepted branch changes by assuming current main is the complete product.

## Located source and original artifact

- Branch `feature/upload-auto-cleanup-20261121`, head3329f97a7f7de1d74ca8fa8e5f3fd005c88e125c.
- Release/code823c0613c2122d201165ae45952598b60c935c4b; original CI44880432304,artifact14697433285.
- Original extension ZIP downloaded from the existing private CI artifact in this turn:2,491,316bytes,SHA25667873c1085b0926a5f40531d17b06d444cbe0b5124442f2cdfa49245794bb56c verified. The older Library ID in branch documentation returned404,so it is NOT used as a delivery source.
- Source baseline includes accepted0.4.76 support snapshots,0.4.77 My Wave metadata grace,and0.4.78 lossless MP3 upload preflight cleanup. Read `docs/decisions/DESKTOP-WAVE-METADATA-0.4.77.md` and `docs/decisions/UPLOAD-AUTO-CLEANUP-20261121.md` on that branch; those are absent from the incomplete migration main snapshot.

## Confirmed omitted playback fix

0.4.77 introduced `effectiveSessionMetadata` and a nonrenewable40ms grace for a transient null MediaSession assignment on the SAME ready master/source/duration. It prevents tearing down a working replacement during My Wave's null→same-song metadata refresh. Actual new metadata/source/duration/readiness changes bypass the grace. This exact fix is present in0.4.78 adapter blobfc7f3013c1bceedd606bc16ccbf1d0ecabfa0c1f and absent in the inspected migration-derived main adapter3d80cadda8be5c419be52e3793873523422bee03.

Thus the migration client line was based on an older main and omitted released fixes. Comparing73 with79 only proved those two older code snapshots matched; it did NOT establish parity with the actual latest78 product. This is a confirmed migration/release provenance error, independent of the later81 whole-file regression and the not-yet-proven origin of every transfer stall. Do not blame Floki hardware/network for this code omission. Server read-only body metrics from the previous audit remain valid, with the same VPS-origin limitation.

## Recovered0.4.78 control for current Floki API

Built in separate local folder from118 files,including all115 extension files; EACH source file matched its Git blob on3329f97a before building. No main playback source rollback/merge or new production deployment was performed in this recovery.

Original source remains unmodified. Only build environment `CELIKOM_API_BASE_URL=https://api.celikom.com` selects the new endpoint. New control ZIP was compared entry-by-entry with the verified ORIGINAL CI ZIP: exactly TWO entries differ,`api/config.json` and `manifest.json` (API origin/host permission). Every other packaged file,including every JS module and both MAIN/ISOLATED bundles,is byte-identical. No0.4.79–84 playback/guard/retry edits were included. This is stronger evidence than inferring provenance from a version label.

- Control filename `CELIKOM-0.4.78-Floki-control.zip`,manifest0.4.78.
-2,491,275bytes,SHA256ba5c9b611cebaa4f9f3b615272bd0c0e289dd37d1a2c52c5eca73c671ab88e55.
- Local371/371 original extension tests PASS,manifest validation PASS. The current Floki security gate was used as a nonpackaged verification helper because the historical gate allowed only Hostinger; it passed66 packaged files. No runtime source was changed for that verification.
- Exact host permissions only `https://api.celikom.com/*` and `https://music.yandex.ru/*`;no Hostinger strings remain in packaged JS/JSON/HTML/CSS.
- Actual private control delivery:Library libfile_ba66ad969d048191a10900dceae714ae. Do not invent a0.4.78 website URL or treat it as a new customer release. The source branch is not yet merged to main and the central owner promoter requires main-history provenance; do not bypass it with a fake receipt.

Owner control: replace files in the SAME unpacked folder,reload existing extension AND Yandex,confirm0.4.78,test the same track/seek/My Wave on the same failing network setup and export diagnostic. No second extension instance. No request to retest73.0.4.84 remains held and approval manifest empty.

After control,restore the actual78 client baseline to main with only verified current-API delivery changes,retaining other product/server work. Audit any proposed backport against78 rather than layering onto the incomplete73 migration base. Server-side upload cleanup presence on Floki is a separate parity question; this source/package recovery does not prove the deployed normalizer/decoder exists. Do not redeploy backend wholesale or touch Android/Windows to answer it.
