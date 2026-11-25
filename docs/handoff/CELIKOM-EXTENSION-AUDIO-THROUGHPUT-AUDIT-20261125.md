# Floki extension audio throughput — prepared read-only audit,25 November2026

Baseline-first work continues from `CELIKOM-EXTENSION-BASELINE-AUDIT-20261125.md`. No new extension release is approved.0.4.84 stays held;82/83 withdrawn. No Android/Windows or production application/configuration change.

## Prepared and checked

Script `.github/scripts/floki-extension-audio-readonly-audit.sh`, sourcea6d036cfad5a06c3db448764ac8fbd163d036147,Git blob9976a77259f7d1b40af5e6b86ff4384c25768eb8. Bash/Python/PHP syntax validated on isolated Floki CI45685250950,job139456022317,SUCCESS. CI never executed production code or received production secrets.

The script requires host root for read-only Nginx/FPM/config access. It verifies deployed server blob hashes vs0.4.73, reports whitelisted buffering/timeouts/rate settings and load/memory/disk. PHP opens a READ ONLY DB transaction and uses an already-existing currently authorized session solely to sign short-lived sample URLs internally. It creates no account/session/trial/benefit, does not activate playback, exposes no bearer/HMAC/signing key/session ID/password or private audio URLs. The application rechecks normal signed audio authorization on every request.

Track144530503 Ау, same active raw MP3/ETag, ranges64KiB and512KiB at offset0 and65536, two rounds, loopback HTTPS/SNI vs public DNS HTTPS.16 sequential GETs,180second internal budget and220second wrapper cap. Each response is bounded, checks exact Content-Range/ETag/byte count and SHA256 against the same storage range, records header/body/64KiB milestones. No payload/audio files are saved. Only ordinary web access logs may observe the normal requests. This is not a client VPN measurement; fast server results cannot prove the owner's external network path is healthy.

## Actual execution status

Protected administrative attempt45685421019,source545d97b5ffa1e3dbf99a16aae9dee0e3596f8a3d failed BEFORE any job steps (`maintenance` job139456623937,steps=null). No script execution or server metrics were obtained. Direct SSH fallback using pinned-host verification also failed: network is unreachable from the current executor. Do not change runner networking or expose SSH/root credentials to isolated CI. No throughput or server bottleneck is claimed.

Administrative request is reset to safe no-op after this failed attempt. Existing permanent publication services remain managed by the infrastructure chat. Owner action is necessary only for this already-checked bounded server read, using existing SSH; no new setup/reinstall requested.

## One owner command

```bash
sudo bash <<'BASH'
set -Eeuo pipefail
systemctl start celikom-mirror-sync.service
d=$(mktemp -d /root/celikom-audio-audit.XXXXXXXX)
trap 'rm -rf -- "$d"' EXIT
runuser -u celikom-mirror -- git \
  --git-dir=/home/celikom-mirror/github-mirror.git show \
  a6d036cfad5a06c3db448764ac8fbd163d036147:.github/scripts/floki-extension-audio-readonly-audit.sh > "$d/audit.sh"
test "$(git hash-object "$d/audit.sh")" = 9976a77259f7d1b40af5e6b86ff4384c25768eb8
bash -n "$d/audit.sh"
timeout 220 bash "$d/audit.sh"
BASH
```

Paste the resulting JSON lines back to the extension chat. They contain only sanitized metrics/config values and content digests. An `existing_authorized_session_required` result means the probe deliberately stopped; do not bypass the gate or create new credentials to make it green. `all_verified:false`/timeouts are useful evidence and are not a successful body-speed check. Compare both rounds and routes before proposing a configuration change. Preserve rollback and active clients.
