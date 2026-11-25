#!/usr/bin/env bash
# Trusted Floki root-only surgical diagnostic upgrade.
# Keep the A1 timer STOPPED after failure; never weaken the unprivileged receiver.
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
[[ "$(id -u)" == 0 && $# == 0 ]] || { echo A1_ROOT_ONLY; exit 64; }

MIRROR=/home/celikom-mirror/github-mirror.git
COMMIT=aabb755632d6b4073c551be1c1dec8ed61101e7f
BLOB=547babe434317a6790d26a64891b1085c3f7aa21
DEST=/usr/local/lib/celikom-a1-signed-owner/consumer.py
SERVICE=celikom-a1-signed-owner.service
TIMER=celikom-a1-signed-owner.timer
RECEIPT=/srv/celikom/ci-runner/runner/celikom-a1-signed-spool/receipts/a1-45652314715-1.json

[[ -d "$MIRROR" && ! -L "$MIRROR" && -f "$DEST" && ! -L "$DEST" ]]
[[ "$(stat -c '%u:%a:%h' "$DEST")" == 0:644:1 ]] || { echo A1_ROOT_UNEXPECTED_FILE_PERMISSIONS; exit 1; }

installed=$(git hash-object "$DEST")
case "$installed" in
  a00a77580a413c9cf9babb57efb0225b244d6757|\
  a9e915186e7c0e3bbce0b8ffda7c046500ca99a3|\
  abde17a59570260cb590a4873408577acfa1b56c|\
  547babe434317a6790d26a64891b1085c3f7aa21) ;;
  *) echo A1_ROOT_UNKNOWN_INSTALLED_CONSUMER; exit 1 ;;
esac

d=$(mktemp -d /root/celikom-a1-receiver-diagnostic.XXXXXXXX)
trap 'rm -rf -- "$d"' EXIT
runuser -u celikom-mirror -- git --git-dir="$MIRROR" show \
  "$COMMIT:.github/scripts/floki-a1-root-signed-spool-consumer.py" > "$d/consumer.py"
[[ "$(git hash-object "$d/consumer.py")" == "$BLOB" ]] || { echo A1_ROOT_INVALID_TRUSTED_BLOB; exit 1; }
python3 -m py_compile "$d/consumer.py"

systemctl stop "$TIMER"
systemctl stop "$SERVICE" || true
if [[ "$installed" != "$BLOB" ]]; then
  new=$(mktemp /usr/local/lib/celikom-a1-signed-owner/.consumer.py.XXXXXXXX)
  install -o root -g root -m 0644 "$d/consumer.py" "$new"
  [[ "$(git hash-object "$new")" == "$BLOB" ]]
  mv -T -- "$new" "$DEST"
fi

[[ "$(git hash-object "$DEST")" == "$BLOB" ]]
systemctl reset-failed "$SERVICE" || true
if ! systemctl start "$SERVICE"; then
  echo A1_ROOT_RECEIVER_DIAGNOSTIC_FAILED_TIMER_REMAINS_STOPPED
  journalctl -u "$SERVICE" -n 35 --no-pager -o cat
  exit 1
fi
[[ -f "$RECEIPT" && ! -L "$RECEIPT" ]] || {
  echo A1_ROOT_NO_SIGNED_RECEIPT_TIMER_REMAINS_STOPPED; exit 1;
}
echo A1_ROOT_SIGNED_RECEIPT
cat "$RECEIPT"
systemctl start "$TIMER"
echo A1_ROOT_RECEIVER_AND_TIMER_SUCCESS
