#!/bin/bash
set -Eeuo pipefail
umask 077
state=/root/celikom-cutover-intake
gate=/usr/local/sbin/celikom-deploy-gateway
if [[ -f "$state/gateway.original" ]]; then
  bash -n "$state/gateway.original"
  install -o root -g root -m 755 "$state/gateway.original" "$state/gateway.restore"
  mv -T "$state/gateway.restore" "$gate"
  rm -f /etc/sudoers.d/celikom-cutover-receive /usr/local/sbin/celikom-cutover-receive "$state/expires"
  visudo -c >/dev/null
  dest=$(mktemp -d /root/celikom-cutover-snapshot-XXXXXXXX)
  mv "$state" "$dest/intake"
  echo "CELIKOM_SQL_INTAKE_CLOSED $dest/intake"
fi
