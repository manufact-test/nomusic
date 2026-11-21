#!/usr/bin/env bash
set -euo pipefail
umask 077
: "${HOSTINGER_SSH_KEY:?}"
key_dir=$(mktemp -d)
trap 'rm -rf "$key_dir"' EXIT
printf '%s\n' "$HOSTINGER_SSH_KEY" | tr -d '\r' > "$key_dir/key"
chmod 600 "$key_dir/key"
ssh-keygen -y -P '' -f "$key_dir/key" > "$key_dir/key.pub"
test "$(ssh-keygen -lf "$key_dir/key.pub" -E sha256 | awk '{print $2}')" = 'SHA256:Q6FyifXRq6garceQdIIjBmXhkk81Ic1p/x9JTSYHWUk'
printf '%s\n' '[92.113.19.189]:65002 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAf8M2EVwq0oJI8I9KZ0NFE8P8yDOvDATEhkQti/Kk/0' > "$key_dir/known_hosts"
opts=(-i "$key_dir/key" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$key_dir/known_hosts" -o GlobalKnownHostsFile=/dev/null -o ConnectTimeout=15)
target=u235811320@92.113.19.189
root=/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom
ssh -p 65002 "${opts[@]}" "$target" 'bash -s' <<'REMOTE'
set -euo pipefail
root=/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom
live=$(readlink -f "$root/current")
[[ "$live" == "$root/releases/"* ]]
echo "ACTIVE_RELEASE:$(basename "$live")"
echo "ADMIN_FILES"
find "$live/src/Admin" -maxdepth 1 -type f -printf '%f\n' | sort
sha256sum "$live/src/Admin/"{AdminPanel.php,ModerationService.php,BulkModerationService.php,BulkModerationView.php,bulk-moderation.js,admin-style.css}
/opt/alt/php83/usr/bin/php <<'PHP'
<?php
require '/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom/current/bootstrap.php';
$c=require '/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom/current/config/app.php';
$p=Celikom\Database\Connection::open($c);
$r=$p->query("SELECT COUNT(*) AS rejected, SUM(EXISTS(SELECT 1 FROM upload_submissions u WHERE u.replacement_id=r.id)) AS with_upload_history FROM track_replacements r WHERE r.status='rejected'")->fetch(PDO::FETCH_ASSOC);
echo 'REJECTED_HISTORY_COUNTS:'.json_encode($r).PHP_EOL;
PHP
REMOTE
