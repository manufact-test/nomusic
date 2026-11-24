#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Executed on a GitHub-hosted runner, with only the old deployment key.
test "${GITHUB_REPOSITORY:-}" = manufact-test/nomusic
test "${GITHUB_REF:-}" = refs/heads/main
test -n "${HOSTINGER_SSH_KEY:-}"
tmp=$(mktemp -d)
trap 'rm -rf -- "$tmp"' EXIT
printf '%s\n' "$HOSTINGER_SSH_KEY" | tr -d '\r' > "$tmp/key"
unset HOSTINGER_SSH_KEY
ssh-keygen -y -P '' -f "$tmp/key" > "$tmp/pub"
test "$(ssh-keygen -lf "$tmp/pub" | awk '{print $2}')" = 'SHA256:Q6FyifXRq6garceQdIIjBmXhkk81Ic1p/x9JTSYHWUk'
printf '%s\n' '[92.113.19.189]:65002 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAf8M2EVwq0oJI8I9KZ0NFE8P8yDOvDATEhkQti/Kk/0' > "$tmp/known_hosts"
ssh -T -p 65002 -i "$tmp/key" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$tmp/known_hosts" -o GlobalKnownHostsFile=/dev/null -o ConnectTimeout=20 u235811320@92.113.19.189 'bash -s' <<'REMOTE'
set -Eeuo pipefail
umask 077
API=/home/u235811320/domains/darkred-camel-588676.hostingersite.com
WEB=/home/u235811320/domains/lemonchiffon-narwhal-791953.hostingersite.com
PHP=/opt/alt/php83/usr/bin/php
for path in "$API/public_html" "$API/celikom/shared" "$WEB/public_html" "$WEB/celikom-private"; do
  test -d "$path"
  test ! -L "$path"
done
for path in "$API/public_html/.htaccess" "$WEB/public_html/.htaccess"; do
  test -f "$path"; test ! -L "$path"
  sha256sum "$path"
  stat -c 'access mode=%a owner=%u' "$path"
done
command -v mysqldump
command -v rsync
command -v gzip
"$PHP" -r 'require $argv[1]."/celikom/current/bootstrap.php"; $c=require $argv[1]."/celikom/current/config/app.php"; if(!preg_match("/^u235811320_celikom$/D",$c["db_name"]))exit(2); $p=Celikom\Database\Connection::open($c); foreach(["admins","users","tracks","audio_assets","track_replacements","windows_gain_variants","subscriptions","billing_payments"] as $t) echo "API_COUNT ",$t," ",$p->query("SELECT COUNT(*) FROM ".$t)->fetchColumn(),PHP_EOL;' "$API"
"$PHP" -r 'require $argv[1]."/celikom-private/app/bootstrap.php"; $c=Celikom\Website\CmsConfig::databaseSettings(); if(!preg_match("/^u235811320_celikom_stage[a-zA-Z0-9_]*$/D",$c["dbname"]))exit(2); $p=Celikom\Website\Database::connect($c); foreach(["content_revisions","content_drafts","media_assets"] as $t) echo "CMS_COUNT ",$t," ",$p->query("SELECT COUNT(*) FROM ".$t)->fetchColumn(),PHP_EOL; $m=getenv("CELIKOM_SITE_MEDIA_DIR"); if(!is_string($m)||!is_dir($m)||is_link($m)||!str_starts_with(realpath($m),$argv[1]."/celikom-private/"))exit(3); echo "CMS_MEDIA_RELATIVE_PATH ",substr(realpath($m),strlen($argv[1])+1),PHP_EOL;' "$WEB"
# Only count matching cron tasks; do not print commands for unrelated sites.
if command -v crontab >/dev/null; then
  crontab -l 2>/dev/null | awk '/darkred-camel-588676|lemonchiffon-narwhal-791953|celikom/{n++}END{print "CELIKOM_CRON_MATCHES",n+0}' || true
fi
echo HOSTINGER_FINAL_SOURCE_PREFLIGHT_OK
REMOTE
