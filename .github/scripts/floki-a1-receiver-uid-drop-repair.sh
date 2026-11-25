#!/usr/bin/env bash
# Floki trusted ROOT-only, one-time A1 receiver UID-drop repair.
# No production/nginx/SSH config changes and no weakening NoNewPrivileges.
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
[[ "$(id -u)" == 0 && $# == 0 ]] || { echo A1_ROOT_REQUIRED; exit 64; }

MIRROR=/home/celikom-mirror/github-mirror.git
COMMIT=28a6d279c6c5cfe481ef776203a91391ed868839
BLOB=338221072cf4f65e03467e94fc753a1bf4c9eec6
PREVIOUS=547babe434317a6790d26a64891b1085c3f7aa21
DEST=/usr/local/lib/celikom-a1-signed-owner/consumer.py
UNIT=celikom-a1-signed-owner.service
TIMER=celikom-a1-signed-owner.timer
DROPIN=/etc/systemd/system/celikom-a1-signed-owner.service.d
OVERRIDE=$DROPIN/10-deploy-child-drop.conf
RECEIPT=/srv/celikom/ci-runner/runner/celikom-a1-signed-spool/receipts/a1-45652314715-1.json

[[ -d "$MIRROR" && ! -L "$MIRROR" && -f "$DEST" && ! -L "$DEST" ]]
[[ "$(stat -c '%u:%a:%h' "$DEST")" == 0:644:1 ]]
installed=$(git hash-object "$DEST")
[[ "$installed" == "$PREVIOUS" || "$installed" == "$BLOB" ]] || {
  echo A1_ROOT_REFUSE_UNKNOWN_EXISTING_CONSUMER
  exit 1
}
[[ "$(systemctl show "$UNIT" --property NoNewPrivileges --value)" == yes ]] || {
  echo A1_ROOT_REFUSE_UNEXPECTED_NNP
  exit 1
}
[[ ! -L "$DROPIN" && ! -L "$OVERRIDE" ]]
[[ ! -e "$OVERRIDE" ]] || {
  grep -Fxq 'AmbientCapabilities=CAP_SETUID CAP_SETGID' "$OVERRIDE" || {
    echo A1_ROOT_REFUSE_UNEXPECTED_OVERRIDE
    exit 1
  }
}

tmp=$(mktemp -d /root/celikom-a1-uid-drop.XXXXXXXX)
trap 'rm -rf -- "$tmp"' EXIT
runuser -u celikom-mirror -- git --git-dir="$MIRROR" show \
  "$COMMIT:.github/scripts/floki-a1-root-signed-spool-consumer.py" > "$tmp/consumer.py"
[[ "$(git hash-object "$tmp/consumer.py")" == "$BLOB" ]] || {
  echo A1_ROOT_REFUSE_BLOB_MISMATCH
  exit 1
}
python3 -m py_compile "$tmp/consumer.py"
getent passwd celikom-deploy > "$tmp/account"
test "$(cut -d: -f3 "$tmp/account")" -gt 0
test "$(cut -d: -f4 "$tmp/account")" -gt 0

systemctl stop "$TIMER"
systemctl stop "$UNIT" || true
if [[ "$installed" != "$BLOB" ]]; then
  desttmp=$(mktemp /usr/local/lib/celikom-a1-signed-owner/.consumer.py.XXXXXXXX)
  install -o root -g root -m 0644 "$tmp/consumer.py" "$desttmp"
  [[ "$(git hash-object "$desttmp")" == "$BLOB" ]]
  mv -T -- "$desttmp" "$DEST"
fi
[[ "$(git hash-object "$DEST")" == "$BLOB" ]]
install -d -o root -g root -m 0755 "$DROPIN"
cat > "$tmp/override.conf" <<'OVERRIDE_CONTENT'
[Service]
# Preserve NoNewPrivileges and grant only the two capabilities needed to
# drop the receiver child into the already-installed celikom-deploy identity.
AmbientCapabilities=CAP_SETUID CAP_SETGID
OVERRIDE_CONTENT
install -o root -g root -m 0644 "$tmp/override.conf" "$OVERRIDE"
systemctl daemon-reload
[[ "$(systemctl show "$UNIT" --property NoNewPrivileges --value)" == yes ]] || {
  echo A1_ROOT_NNP_MUST_REMAIN_ENABLED
  exit 1
}
systemctl reset-failed "$UNIT" || true
if ! systemctl start "$UNIT"; then
  echo A1_ROOT_UID_DROP_REPAIR_FAILED_TIMER_STOPPED
  journalctl -u "$UNIT" -n 40 --no-pager -o cat
  exit 1
fi

[[ -f "$RECEIPT" && ! -L "$RECEIPT" ]] || {
  echo A1_ROOT_BETA16_RECEIPT_MISSING_TIMER_STOPPED
  exit 1
}
echo A1_ROOT_BETA16_RECEIPT
cat "$RECEIPT"
systemctl start "$TIMER"
echo A1_ROOT_BETA16_PUBLICATION_AND_TIMER_READY
