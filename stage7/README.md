# Stage 7 isolated owner upload test

This is a **separate local sandbox** for CELIKOM. It cannot use the Hostinger production database, production Track 144530503 or any existing approved AudioAsset. The PHP server is bound only to `127.0.0.1:8787`, MySQL has no published ports, and two disposable named Docker volumes hold audio and database files. Ordinary end-user uploads remain disabled in the API config.

## Quick start on Windows

Requirements: Docker Desktop running and a checkout of `manufact-test/nomusic` on branch `feature/api-range`. PowerShell 5.1 or newer. Chrome.

From the repository root run:

```powershell
.\stage7\start-local.ps1
```

The script creates **unique local credentials** in an ignored `stage7/.runtime/local.env`, starts PHP 8.3 + MySQL 8.0, migrates only the disposable `celikom_test_stage7` database, and builds a separate Chrome extension with API origin `http://127.0.0.1:8787`. Node.js 24 is run inside Docker. No Hostinger SSH connection or external API deployment occurs. First startup may need several minutes to pull Docker images.

The terminal prints a one-time private owner upload code for the popup and the unpacked extension folder `extension/dist/unpacked`. Do not paste or screenshot the token into GitHub/chat. Open `chrome://extensions`, enable Developer mode, **disable the working CELIKOM** to prevent two extensions from injecting into the same page, and Load unpacked from the printed folder. Refresh the Yandex Music tab after loading the temporary extension.

## Manual acceptance (10–15 minutes)

1. Start any track in Yandex Music. Under Add version, the current Track ID must be detected confidently and be **read-only**. If no ID, the upload stays disabled.
2. Select a legal MP3 up to 30 MiB, affirm rights and paste the local owner code from your own terminal. Upload and expect `pending` with a progress bar, never `approved`.
3. Rename exactly the same MP3 without changing its bytes and upload again for the same Track ID. Expect the duplicate message. This creates no second AudioAsset.
4. Confirm that CELIKOM does not start replacing the original with this pending upload. A malformed file or changing the Yandex track before sending must not attach an incorrect file.
5. After checking, remove/disable the **temporary** extension and re-enable the original CELIKOM. Restore the original Yandex tab if needed.

To stop the containers while retaining isolated test data:

```powershell
.\stage7\stop-local.ps1
```

To fully reset the sandbox (its audio, MySQL and generated tokens), intentionally run:

```powershell
.\stage7\stop-local.ps1 -Reset
```

**Never run `docker volume prune`**, which could destroy unrelated volumes. The scripts use the fixed Compose project name `celikom-stage7-local` only.

## Security boundaries and limitations

- `server/.dockerignore` excludes `.env`, `tests`, storage and `vendor` from the Docker image. The temporary `.runtime` is Git ignored.
- Port 8787 is local HTTP by design; never bind it to a public IP, expose it with a tunnel, or use it for other users.
- This sandbox is for the owner, not public upload. `FEATURE_OWNER_UPLOADS=1` is enabled **only in local Docker** and protected by its randomly generated bearer token.
- `API_TEST_TOKEN` read-only code is separate from `UPLOAD_OWNER_TOKEN`.
- The local database starts empty: no production mapping, existing approved MP3 or production token is copied into it.
- Fingerprint jobs are recorded as pending; similarity fingerprint computation remains deferred.
- A Windows system without Docker Desktop cannot run this isolated sandbox. The GitHub Actions `Stage 7 localhost sandbox` workflow independently verifies it and publishes a loopback-targeted extension artifact.
