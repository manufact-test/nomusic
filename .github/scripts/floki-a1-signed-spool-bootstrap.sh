#!/usr/bin/env bash
# ONE-TIME TRUSTED ROOT INSTALL. Never run from the untrusted CI runner.
# Uses a pinned Git blob fetched through the existing read-only GitHub mirror.
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
[[ "$(id -u)" == 0 && $# == 0 ]] || { echo A1_ROOT_REQUIRED; exit 64; }
MIRROR=/home/celikom-mirror/github-mirror.git
SOURCE_COMMIT=aa40538e5d8340550469d03e8bae124d3e68cbb6
CONSUMER_BLOB=605cdd410386f5e647b0df1e44b3772dc5c8733a
SPOOL=/srv/celikom/ci-runner/runner/celikom-a1-signed-spool
IMPORT=/root/celikom-a1-signed-import
DEST=/usr/local/lib/celikom-a1-signed-owner
SERVICE=/etc/systemd/system/celikom-a1-signed-owner.service
TIMER=/etc/systemd/system/celikom-a1-signed-owner.timer
RECEIVER=/usr/local/sbin/celikom-a1-apk-receive

[[ -d "$MIRROR" && ! -L "$MIRROR" ]]
[[ -f "$RECEIVER" && ! -L "$RECEIVER" && "$(stat -c '%u' "$RECEIVER")" == 0 ]]
[[ -d /srv/celikom-a1-downloads/files && -d /srv/celikom-a1-downloads/receipts ]]
[[ -d "$SPOOL" && ! -L "$SPOOL" && "$(stat -c '%a' "$SPOOL")" == 700 ]]
[[ "$(stat -c '%u' "$SPOOL")" != 0 ]]
[[ ! -e "$SERVICE" && ! -L "$SERVICE" && ! -e "$TIMER" && ! -L "$TIMER" ]]
[[ ! -e "$DEST" && ! -L "$DEST" ]]
tmp=$(mktemp -d /root/celikom-a1-bootstrap.XXXXXXXX)
trap 'rm -rf -- "$tmp"' EXIT
runuser -u celikom-mirror -- git --git-dir="$MIRROR" show \
  "$SOURCE_COMMIT:.github/scripts/floki-a1-root-signed-spool-consumer.py" > "$tmp/consumer.py"
[[ "$(git hash-object "$tmp/consumer.py")" == "$CONSUMER_BLOB" ]]
python3 -m py_compile "$tmp/consumer.py"
if ! command -v apksigner >/dev/null || ! command -v aapt >/dev/null; then
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends apksigner aapt
fi
[[ -x /usr/bin/apksigner && -x /usr/bin/aapt && -x /usr/sbin/runuser ]]
install -d -o root -g root -m 700 "$IMPORT"
install -d -o root -g root -m 755 "$DEST"
install -d -o root -g root -m 755 "$SPOOL/receipts"
install -o root -g root -m 644 "$tmp/consumer.py" "$DEST/consumer.py"
[[ "$(git hash-object "$DEST/consumer.py")" == "$CONSUMER_BLOB" ]]

cat > "$SERVICE" <<'UNIT'
[Unit]
Description=CELIKOM A1 independently verified signed APK promoter
After=network-online.target
Wants=network-online.target
ConditionPathIsDirectory=/srv/celikom/ci-runner/runner/celikom-a1-signed-spool

[Service]
Type=oneshot
User=root
Group=root
UMask=0077
ExecStart=/usr/bin/python3 /usr/local/lib/celikom-a1-signed-owner/consumer.py
TimeoutStartSec=550
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=full
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictRealtime=yes
LockPersonality=yes
UNIT

cat > "$TIMER" <<'UNIT'
[Unit]
Description=Promote independently verified CELIKOM A1 APKs from private Floki spool

[Timer]
OnBootSec=120s
OnUnitInactiveSec=60s
RandomizedDelaySec=5s
Persistent=yes
Unit=celikom-a1-signed-owner.service

[Install]
WantedBy=timers.target
UNIT
chmod 644 "$SERVICE" "$TIMER"
systemctl daemon-reload
systemctl enable --now celikom-a1-signed-owner.timer
systemctl start celikom-a1-signed-owner.service
systemctl is-active celikom-a1-signed-owner.timer
echo CELIKOM_A1_ROOT_VERIFIED_SPOOL_PROMOTER_READY
