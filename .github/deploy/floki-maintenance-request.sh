#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
R=/home/celikom-mirror/github-mirror.git
S=/srv/celikom/app/staging-20261122
for rel in server/src/Admin/AdminPanel.php server/src/Admin/ModerationService.php server/src/Application/UploadService.php server/src/Admin/admin-style.css server/config/app.php server/.env.example; do
 stage="$S/${rel#server/}"
 [[ -f "$stage" ]] || { echo "STAGE_MISSING $rel"; continue; }
 tmp=$(mktemp)
 git --git-dir="$R" show "refs/heads/main:$rel" > "$tmp"
 echo "=== THREE-WAY SOURCE DELTA $rel (GitHub main -> Hostinger import) ==="
 diff -U3 "$tmp" "$stage" || true
 rm -f "$tmp"
done
echo CELIKOM_SOURCE_DELTA_DETAILS_OK
