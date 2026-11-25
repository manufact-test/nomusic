#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Dedicated nonprivileged signed Windows data intake. Never modify the API,
# database grants, source, production feed, root administration or CI network.
work=$(mktemp -d /root/celikom-windows-intake-tools.XXXXXXXX)
trap 'rm -rf -- "$work"' EXIT
systemctl start celikom-mirror-sync.service
mirror=/home/celikom-mirror/github-mirror.git
for spec in floki-windows-intake-bootstrap.sh:7d4fae2d60bea363ae0c1ea8325d4e233dd7a585 windows-stable-private-import.py:97e53c4c5247ca555a9483f2517708d097dc5ae6 windows-stable-private-intake.py:cc84094d55f691adf9dff56aad7fb6fe72830341 windows-stable-release-verify.mjs:ae38c2c48a032fec0ad1eaae14c444e43dfb2b18 windows-stable-existing-latest.mjs:bb4d19672d45bdd0393497c3b33280308d67ef32; do
  file=${spec%%:*}
  hash=${spec#*:}
  runuser -u celikom-mirror -- git --git-dir="$mirror" show "$hash" > "$work/$file"
  test "$(git hash-object "$work/$file")" = "$hash"
  test "$(stat -c '%u:%a' "$work/$file")" = 0:600
done
bash -n "$work/floki-windows-intake-bootstrap.sh"
bash "$work/floki-windows-intake-bootstrap.sh" "$work"
