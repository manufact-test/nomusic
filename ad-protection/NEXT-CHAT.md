# NEXT CHAT — CELIKOM Ad Protection

Checkpoint: 2026-10-19 · Stage 0 COMPLETE · Start **Stage 1**.

Repository: https://github.com/manufact-test/nomusic
Existing branch: feature/api-range
Directory: ad-protection/

## Mandatory reading

Read in this order:
1. ad-protection/README.md
2. ad-protection/MASTER.md
3. ad-protection/ROADMAP.md
4. ad-protection/docs/ARCHITECTURE.md
5. ad-protection/docs/TEST-MATRIX.md
6. ad-protection/docs/RESEARCH-SOURCES.md
7. ad-protection/standalone/manifest.json
8. ad-protection/tests/stage0.test.mjs

## Current situation

The parent project CELIKOM already has a working Chrome replacement extension and a separate active Android PoC. Both are OUT OF BOUNDS here. All stage-0 files are independently scoped and no production code, shared manifests or GitHub workflows should be changed.

Stage 0 provided an inert standalone Manifest V3 research shell and self-contained smoke tests. It intentionally does **not** block ads yet. Full coverage of banners, overlays, video and audio advertisements must be validated in the browser before a GO decision; Android official app is outside this MVP.

## Do next (Stage 1)

Take one meaningful research block rather than splitting into trivial commits: verify live current Yandex Music advertisement behaviors, Chrome MV3 mechanisms and permissions, Chrome Web Store rules, Yandex terms, comparative technical examples and licenses. Produce an evidence matrix and honest GO/NO-GO for full Chrome ad suppression. Do NOT declare full functionality from README claims of other projects.

Write only under ad-protection/. No changes to extension/, android/, server/, website/, docs/ (root), root manifests, CI, open PR #6, or existing branch layout. Do not publish/install production extensions or claim store approval.

After a substantial block or user request, update this file and the local roadmap/checkpoint, then provide the user the concise handoff.

## Stage 0 verification command

    cd ad-protection && npm test

## Owner priorities

- Full advertising coverage rather than partial feature marketed as full
- No damage to replacement engine
- Clear Chrome Web Store path (not guaranteed in advance)
- One-folder removal with zero side effects
- Separate workstream for now; integration is the **last** stage requiring explicit approval
