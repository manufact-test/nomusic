#!/usr/bin/env bash
set -euo pipefail
[[ "${GITHUB_REPOSITORY:-}" == "manufact-test/nomusic" && "${GITHUB_REF:-}" == "refs/heads/feature/api-range" ]] || exit 1
[[ "${GITHUB_SHA:-}" =~ ^[a-f0-9]{40}$ ]] || exit 1
operation="$(node -p "require('./.github/deploy/hostinger-stage9-mail-request.json').operation")"
if [[ "$operation" == 'prepare' ]]; then
  echo 'Stage9 SMTP provisioning prepared only; no server changes or secrets used.'
  exit 0
fi
[[ "$operation" == 'provision' ]] || exit 1
for var in HOSTINGER_SSH_KEY CELIKOM_SMTP_HOST CELIKOM_SMTP_PORT CELIKOM_SMTP_USER CELIKOM_SMTP_PASSWORD CELIKOM_MAIL_FROM CELIKOM_SMTP_TEST_TO; do
  [[ -n "${!var:-}" ]] || { echo "Required protected setting $var is missing." >&2; exit 1; }
done
remote_head="$(git ls-remote origin refs/heads/feature/api-range | cut -f1)"
[[ "$remote_head" == "$GITHUB_SHA" ]] || { echo 'Refusing stale Stage 9 SMTP request.' >&2; exit 1; }
umask 077
work="$(mktemp -d)"
opts=()
base='/home/u235811320/domains/darkred-camel-588676.hostingersite.com'
target='u235811320@92.113.19.189'
incoming="$base/celikom/incoming/stage9-mail-$GITHUB_SHA"
cleanup() {
  if [[ ${#opts[@]} -gt 0 ]]; then
    ssh -T -p 65002 "${opts[@]}" "$target" \
      "rm -f '$incoming/hostinger-stage9-mail-remote.php' '$incoming/hostinger-stage9-mail-request.json' '$incoming/SmtpMailer.php'; rmdir '$incoming'" >/dev/null 2>&1 || true
  fi
  rm -rf -- "$work"
}
trap cleanup EXIT
printf '%s\n' "$HOSTINGER_SSH_KEY" | tr -d '\r' > "$work/key"
ssh-keygen -y -P '' -f "$work/key" > "$work/public"
[[ "$(ssh-keygen -lf "$work/public" | awk '{print $2}')" == 'SHA256:Q6FyifXRq6garceQdIIjBmXhkk81Ic1p/x9JTSYHWUk' ]] || exit 1
printf '%s\n' '[92.113.19.189]:65002 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAf8M2EVwq0oJI8I9KZ0NFE8P8yDOvDATEhkQti/Kk/0' > "$work/known_hosts"
opts=(-i "$work/key" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes
      -o "UserKnownHostsFile=$work/known_hosts" -o GlobalKnownHostsFile=/dev/null
      -o ConnectTimeout=15 -o ServerAliveInterval=10 -o ServerAliveCountMax=2)
ssh -T -p 65002 "${opts[@]}" "$target" \
  "test -d '$base/public_html' && test ! -L '$base/celikom' && umask 077 && mkdir -p '$incoming' && chmod 0700 '$incoming'"
scp -P 65002 "${opts[@]}" .github/scripts/hostinger-stage9-mail-remote.php \
  .github/deploy/hostinger-stage9-mail-request.json server/src/Auth/SmtpMailer.php "$target:$incoming/"
# JSON stays in process memory, streamed through encrypted SSH stdin only.
python3 -c '
import os, json, sys
pairs = [
  ("host", "CELIKOM_SMTP_HOST"),
  ("port", "CELIKOM_SMTP_PORT"),
  ("user", "CELIKOM_SMTP_USER"),
  ("password", "CELIKOM_SMTP_PASSWORD"),
  ("from", "CELIKOM_MAIL_FROM"),
  ("test_to", "CELIKOM_SMTP_TEST_TO")
]
data = {field: os.environ[name] for field, name in pairs}
data["port"] = int(data["port"])
sys.stdout.write(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
' | ssh -T -p 65002 "${opts[@]}" "$target" \
    "/opt/alt/php83/usr/bin/php '$incoming/hostinger-stage9-mail-remote.php' '$incoming/hostinger-stage9-mail-request.json'"
echo 'Stage9 SMTP provisioning completed; owner must still confirm mailbox receipt.'
