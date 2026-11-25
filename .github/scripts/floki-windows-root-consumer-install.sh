#!/bin/bash
# ONE-TIME OWNER APPROVED ROOT INSTALL. Input must be separately delivered by
# trusted administration, NEVER from the runner-writable signed ZIP spool.
set -Eeuo pipefail
umask 077
[[ "$(id -u)" == 0 ]]
SRC=/root/celikom-windows-bootstrap-intake
DEST=/usr/local/lib/celikom-windows-intake
[[ -d "$SRC" && ! -L "$SRC" && -d "$DEST" && ! -L "$DEST" ]]
[[ "$(stat -c '%u:%a' "$SRC")" == 0:700 ]]
[[ "$(stat -c '%u' "$DEST")" == 0 ]]
consumer="$SRC/floki-windows-signed-root-consumer.py"
route="$SRC/floki-windows-owner-download-bootstrap.sh"
[[ "$(stat -c '%u:%a:%h' "$consumer")" == 0:600:1 ]]
[[ "$(stat -c '%u:%a:%h' "$route")" == 0:600:1 ]]
[[ "$(git hash-object "$consumer")" == 9ff780d3719ff6b3f9a00d21f8164bcae9e37140 ]]
[[ "$(git hash-object "$route")" == aa974b6f7052ce0da2397fe24f93f19555e4907a ]]
python3 -m py_compile "$consumer"
bash -n "$route"
# For the initial migration, preserve the old root-owned 0.24.55 signed floor
# and inherited Basic Auth. Never reconfigure API or the public update feed.
[[ "$(readlink /srv/celikom-releases/windows/stable/current)" == versions/0.24.55 ]]
[[ -f /root/celikom-secrets/windows-stable-public.der ]]
[[ "$(sha256sum /root/celikom-secrets/windows-stable-public.der | cut -d' ' -f1)" == 46b36bb222154316f2229c35cf65e6c953e0b6524dfb0aad8de05949dc143a95 ]]
[[ -d /srv/celikom/ci-runner/runner/celikom-windows-signed-spool ]]
bash "$route"
target="$DEST/floki-windows-signed-root-consumer.py"
if [[ -e "$target" || -L "$target" ]]; then
  [[ ! -L "$target" ]]
  [[ "$(git hash-object "$target")" == 9ff780d3719ff6b3f9a00d21f8164bcae9e37140 ]]
else
  install -o root -g root -m 0644 "$consumer" "$target"
fi
SERVICE=/etc/systemd/system/celikom-windows-signed-owner.service
TIMER=/etc/systemd/system/celikom-windows-signed-owner.timer
[[ ! -e "$SERVICE" && ! -L "$SERVICE" ]]
[[ ! -e "$TIMER" && ! -L "$TIMER" ]]
cat > "$SERVICE" <<'UNIT'
[Unit]
Description=CELIKOM Windows independently verified P-256 signed owner release promoter
After=local-fs.target
ConditionPathIsDirectory=/srv/celikom/ci-runner/runner/celikom-windows-signed-spool

[Service]
Type=oneshot
User=root
Group=root
UMask=0077
ExecStart=/usr/bin/python3 /usr/local/lib/celikom-windows-intake/floki-windows-signed-root-consumer.py
TimeoutStartSec=600
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=full
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictRealtime=yes
RestrictSUIDSGID=yes
LockPersonality=yes
UNIT
cat > "$TIMER" <<'UNIT'
[Unit]
Description=Check private signed Windows data-only runner spool and promote latest owner release

[Timer]
OnBootSec=120s
OnUnitInactiveSec=60s
RandomizedDelaySec=5s
Persistent=yes
Unit=celikom-windows-signed-owner.service

[Install]
WantedBy=timers.target
UNIT
chmod 0644 "$SERVICE" "$TIMER"
systemctl daemon-reload
# First prove and promote the already staged 0.24.56, then schedule updates.
# Avoid racing a timer-fired import against this first install.
systemctl start celikom-windows-signed-owner.service
systemctl enable --now celikom-windows-signed-owner.timer
systemctl is-active celikom-windows-signed-owner.timer
[[ "$(readlink /srv/celikom-releases/windows/stable/current)" == versions/0.24.56 ]]
[[ -f /srv/celikom-releases/owner-downloads/CELIKOM-Windows-0.24.56.exe ]]
echo WINDOWS_SIGNED_ROOT_SPOOL_TIMER_AND_OWNER_02456_READY
