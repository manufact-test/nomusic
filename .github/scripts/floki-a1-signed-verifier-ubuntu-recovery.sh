#!/bin/bash
# Narrow recovery of A1 verifier after Ubuntu apksigner/aapt symlink refusal.
# Root-only local operation, no CI runner privileges, no Nginx/Windows changes.
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
[[ "$(id -u)" == 0 && $# == 0 ]] || { echo A1_ROOT_REQUIRED; exit 64; }
MIRROR=/home/celikom-mirror/github-mirror.git
COMMIT=7366d6bd7b6fdddcea3ae27b2cf0658473dda4b3
BLOB=a9e915186e7c0e3bbce0b8ffda7c046500ca99a3
ORIGINAL_BLOB=a00a77580a413c9cf9babb57efb0225b244d6757
DEST=/usr/local/lib/celikom-a1-signed-owner/consumer.py
SERVICE=celikom-a1-signed-owner.service
TIMER=celikom-a1-signed-owner.timer
[[ -d "$MIRROR" && ! -L "$MIRROR" ]]
[[ -f "$DEST" && ! -L "$DEST" ]]
[[ "$(stat -c '%u:%a:%h' "$DEST")" == 0:644:1 ]]
[[ "$(git hash-object "$DEST")" == "$ORIGINAL_BLOB" || "$(git hash-object "$DEST")" == "$BLOB" ]] ||
  { echo A1_ROOT_UNEXPECTED_INSTALLED_CONSUMER; exit 1; }
tmp=$(mktemp -d /root/celikom-a1-verifier-fix.XXXXXXXX)
trap 'rm -rf -- "$tmp"' EXIT
runuser -u celikom-mirror -- git --git-dir="$MIRROR" show \
  "$COMMIT:.github/scripts/floki-a1-root-signed-spool-consumer.py" > "$tmp/consumer.py"
[[ "$(git hash-object "$tmp/consumer.py")" == "$BLOB" ]]
python3 -m py_compile "$tmp/consumer.py"
# Ensure installed verification tools exist before activating the new consumer.
for bin in /usr/bin/apksigner /usr/bin/aapt /usr/sbin/runuser; do
  [[ -x "$bin" ]] || { echo "A1_MISSING_SYSTEM_VERIFIER $bin"; exit 1; }
done
systemctl stop "$TIMER"
restore_timer() { systemctl start "$TIMER" || true; }
trap 'restore_timer; rm -rf -- "$tmp"' EXIT
systemctl stop "$SERVICE"
next=$(mktemp /usr/local/lib/celikom-a1-signed-owner/.consumer.py.XXXXXXXX)
trap 'rm -f -- "$next"; restore_timer; rm -rf -- "$tmp"' EXIT
install -o root -g root -m 0644 "$tmp/consumer.py" "$next"
[[ "$(git hash-object "$next")" == "$BLOB" ]]
mv -T -- "$next" "$DEST"
[[ "$(git hash-object "$DEST")" == "$BLOB" ]]
systemctl reset-failed "$SERVICE" || true
if systemctl start "$SERVICE"; then
  echo A1_ROOT_SIGNED_PROMOTION_SERVICE_OK
else
  journalctl -u "$SERVICE" -n 40 --no-pager -o cat
  exit 1
fi
receipt=/srv/celikom/ci-runner/runner/celikom-a1-signed-spool/receipts/a1-45652314715-1.json
if [[ -f "$receipt" && ! -L "$receipt" ]]; then
  cat "$receipt"
  echo A1_BETA16_ROOT_RECEIPT_PRESENT
else
  echo A1_BETA16_ROOT_RECEIPT_MISSING
  exit 1
fi
