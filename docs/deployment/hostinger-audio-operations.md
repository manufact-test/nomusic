# Stage 5: restricted private-audio operations

The owner-reviewed single-file import and replacement flag are separate actions. This operation deliberately does **not** run with normal deploy and never accepts arbitrary remote commands. Hostinger remains the temporary private-test backend.

## Safety and trigger

- Workflow: `.github/workflows/hostinger-audio.yml`; input: `.github/deploy/hostinger-audio-request.json`, on `feature/api-range` only.
- Operations: `inspect`, `import`, `enable`, `disable`. Request JSON contains **no** credentials, song file, original filename or audio URL.
- Existing pinned SSH identity and Hostinger Actions secret are reused; no secrets are printed or reset.
- The remote tool is copied and executed only under `celikom/incoming`; it checks the dedicated website, active release and shared storage; PHP 8.3 is invoked explicitly.
- The staging folder must contain **exactly one** regular, supported MP3/WAV file with an ASCII basename. Reject symlinks, public uploads and files larger than 30 MiB. The owner must confirm rights/review and supply measured file duration and exact Yandex Track ID before import.
- On import the existing `TestAudioImporter` handles MIME, SHA-256, dedupe, DB mapping and storage. **The feature flag stays disabled.**
- On enable an approved active mapping and an existing private storage object are required. Analytics must remain disabled. The single feature flag is replaced atomically in the shared private environment.
- The workflow checks the public HTTPS config after completion and refuses a stale branch commit. Re-run an old request only after checking current state; stale revisions are refused.
- Never commit the beta bearer code, server environment, private song file, private filename or secret material to Git or workflow logs. The owner retrieves the beta test token privately, separately from this operation.

## Requests

Read-only validation:

```json
{"operation":"inspect"}
```

After the owner has uploaded exactly one reviewed file to private `celikom/shared/staging` and supplied its exact Track ID / measured duration:

```json
{"operation":"import","track_id":"EXACT_YANDEX_TRACK_ID","duration_ms":200000,"confirm_reviewed":true}
```

Only after the import workflow has succeeded:

```json
{"operation":"enable","track_id":"EXACT_YANDEX_TRACK_ID"}
```

Kill switch (always available):

```json
{"operation":"disable"}
```

The example duration is illustrative; never use it as a measured value. Any requested change is made by a reviewed commit to the request JSON, using the existing current branch. The workflow is serialized with server deployment and does not modify other Hostinger sites.

After successful enable, run the private beta build on real Yandex Music, then record the 2–3 minute playback gate and remaining Stage 5 operations. This automation is not an end-user upload/moderation workflow.
