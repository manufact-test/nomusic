#!/bin/bash
set -Eeuo pipefail
umask 077
[[ "$(id -u)" == 0 ]]
echo WINDOWS_OWNER_DELIVERY_INVENTORY_BEGIN
for base in /usr/local/lib/celikom-windows-intake /root/celikom-release-import /srv/celikom-releases/windows/stable /root/celikom-cutover-prepared; do
  if [[ -d "$base" && ! -L "$base" ]]; then
    stat -c 'WIN_DIRECTORY %n %U:%a' "$base"
  fi
done
for f in /usr/local/lib/celikom-windows-intake/windows-stable-publish-floki.mjs /root/celikom-release-import/windows-0.24.56/manifest-public-key.der /root/celikom-release-import/windows-0.24.56/0.24.56/manifest.json /root/celikom-cutover-prepared/windows-stable-locations.conf; do
  [[ ! -f "$f" ]] || stat -c 'WIN_FILE %n %U:%a %s' "$f"
done
if [[ -L /srv/celikom-releases/windows/stable/current ]]; then
  echo "WIN_CURRENT=$(readlink /srv/celikom-releases/windows/stable/current)"
fi
for root in /etc/nginx/sites-enabled /etc/nginx/conf.d /root/celikom-cutover-prepared; do
  if [[ -d "$root" ]]; then
    grep -RnE -m 4 'downloads/windows|CELIKOM-Windows-0\.24\.55\.exe|windows/stable/current' "$root" 2>/dev/null | grep -v -E 'password|secret|htpasswd' | head -n 24 || true
  fi
done
echo WINDOWS_OWNER_DELIVERY_INVENTORY_END
