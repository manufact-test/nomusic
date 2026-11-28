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

ROOT=/srv/celikom-releases/windows/stable
OWNER=/srv/celikom-releases/owner-downloads
SPOOL=/srv/celikom/ci-runner/runner/celikom-windows-signed-spool
echo WINDOWS_ROOT_CONSUMER_STATE_BEGIN
for unit in celikom-windows-signed-owner.timer celikom-windows-signed-owner.service; do
  printf 'WIN_SYSTEMD %s ' "$unit"
  systemctl show "$unit" -p LoadState -p ActiveState -p UnitFileState --no-pager 2>/dev/null | tr '\n' ' ' || true
  echo
done
if [[ -L "$ROOT/current" ]]; then
  printf 'WIN_STABLE_CURRENT_TARGET='
  readlink "$ROOT/current" || true
  printf 'WIN_STABLE_CURRENT_REALPATH='
  readlink -f "$ROOT/current" || true
else
  echo WIN_STABLE_CURRENT=missing
fi
if [[ -f "$ROOT/current/manifest.json" && ! -L "$ROOT/current/manifest.json" ]]; then
  python3 - "$ROOT/current/manifest.json" <<'PY'
import json,sys
try:
    d=json.load(open(sys.argv[1],encoding="utf-8"))
    print("WIN_STABLE_CURRENT_MANIFEST",
          "version="+str(d.get("version","")),
          "sequence="+str(d.get("sequence","")),
          "sha256="+str(d.get("sha256","")),
          "packageSize="+str(d.get("packageSize","")))
except Exception:
    print("WIN_STABLE_CURRENT_MANIFEST_PARSE_FAILED")
PY
else
  echo WIN_STABLE_CURRENT_MANIFEST=missing
fi
for f in "$ROOT/owner-verified.json" "$OWNER/CELIKOM-Windows-latest.exe"; do
  if [[ -f "$f" && ! -L "$f" ]]; then
    stat -c 'WIN_OWNER_RELEASE_FILE %n %U:%a %s' "$f"
    if [[ "$f" == "$ROOT/owner-verified.json" ]]; then
      python3 - "$f" <<'PY'
import json,sys
try:
    d=json.load(open(sys.argv[1],encoding="utf-8"))
    print("WIN_OWNER_VERIFIED_RECEIPT",
          "version="+str(d.get("version","")),
          "sequence="+str(d.get("sequence","")),
          "sha256="+str(d.get("sha256","")),
          "https_verified="+str(d.get("https_verified","")))
except Exception:
    print("WIN_OWNER_VERIFIED_RECEIPT_PARSE_FAILED")
PY
    fi
  else
    echo "WIN_OWNER_RELEASE_FILE_MISSING $f"
  fi
done
if [[ -d "$SPOOL" && ! -L "$SPOOL" ]]; then
  find "$SPOOL" -maxdepth 1 -type f -printf 'WIN_SPOOL_FILE %f %s bytes\n' | sort
else
  echo WIN_SPOOL_DIRECTORY=missing
fi
echo WIN_PUBLIC_DNS_BEGIN
getent ahostsv4 celikom.com 2>/dev/null | awk '{print "WIN_CELIKOM_DNS "$1}' | sort -u || true
echo WIN_PUBLIC_STABLE_HTTP_BEGIN
curl -sS -I --max-time 12 https://celikom.com/CELIKOM/Windows/Updates/stable/latest.json 2>&1 | sed -n '1,12p' || true
echo WIN_PUBLIC_OWNER_ROUTE_HTTP_BEGIN
curl -sS -I --max-time 12 https://celikom.com/downloads/windows/CELIKOM-Windows-latest.exe 2>&1 | sed -n '1,12p' || true
echo WIN_NGINX_WINDOWS_ROUTE_CONFIG_BEGIN
for root in /etc/nginx/sites-enabled /etc/nginx/conf.d /root/celikom-cutover-prepared; do
  if [[ -d "$root" ]]; then
    grep -RnE -m 8 'CELIKOM/Windows/Updates/stable|downloads/windows|/srv/celikom-releases/windows/stable|owner-downloads|proxy_pass' "$root" 2>/dev/null |
      grep -v -E 'password|secret|htpasswd|authorization|basic_auth' | head -n 40 || true
  fi
done
echo WIN_NGINX_WINDOWS_ROUTE_CONFIG_END
echo WINDOWS_ROOT_CONSUMER_STATE_END

echo WINDOWS_CUSTOMER_STABLE_CONSUMER_STATE_BEGIN
MIRROR=/home/celikom-mirror/github-mirror.git
for unit in celikom-mirror-sync.timer celikom-mirror-sync.service; do
  printf 'WIN_MIRROR_SYSTEMD %s ' "$unit"
  systemctl show "$unit" -p LoadState -p ActiveState -p UnitFileState -p LastTriggerUSec -p ExecMainStatus --no-pager 2>/dev/null | tr '\n' ' ' || true
  echo
done
if [[ -d "$MIRROR" && ! -L "$MIRROR" ]]; then
  mirror_head=$(runuser -u celikom-mirror -- git --git-dir="$MIRROR" rev-parse refs/heads/main 2>/dev/null || true)
  echo "WIN_MIRROR_MAIN_COMMIT=$mirror_head"
  runuser -u celikom-mirror -- git --git-dir="$MIRROR" show refs/heads/main:.github/release/windows-customer-stable.json 2>/dev/null |
    python3 -c 'import json,sys; d=json.load(sys.stdin); a=d.get("approved") or {}; print("WIN_MIRROR_CUSTOMER_APPROVAL", "version="+str(a.get("version","none")), "sequence="+str(a.get("sequence","")), "sha256="+str(a.get("sha256","")), "owner_accepted="+str(a.get("owner_accepted","")))' || true
else
  echo WIN_MIRROR_DIRECTORY=missing
fi
journalctl -u celikom-mirror-sync.service -n 25 --no-pager -o cat 2>/dev/null | tail -n 50 || true
CUSTOMER=/srv/celikom-releases/public/windows-customer-stable
for unit in celikom-windows-customer-stable.timer celikom-windows-customer-stable.service; do
  printf 'WIN_CUSTOMER_SYSTEMD %s ' "$unit"
  systemctl show "$unit" -p LoadState -p ActiveState -p UnitFileState -p LastTriggerUSec -p ExecMainStatus --no-pager 2>/dev/null | tr '\n' ' ' || true
  echo
done
if [[ -d "$CUSTOMER" && ! -L "$CUSTOMER" ]]; then
  for f in latest.json accepted.json; do
    if [[ -f "$CUSTOMER/$f" && ! -L "$CUSTOMER/$f" ]]; then
      python3 - "$CUSTOMER/$f" "$f" <<'PY'
import json,sys
d=json.load(open(sys.argv[1],encoding='utf-8'))
if sys.argv[2]=='latest.json':
    print('WIN_CUSTOMER_LATEST', 'version='+str(d.get('version','')), 'sequence='+str(d.get('sequence','')), 'sha256='+str(d.get('sha256','')))
else:
    print('WIN_CUSTOMER_ACCEPTED', 'version='+str(d.get('version','')), 'sequence='+str(d.get('sequence','')), 'sha256='+str(d.get('sha256','')), 'https_verified='+str(d.get('https_verified','')))
PY
    else
      echo "WIN_CUSTOMER_FILE_MISSING $CUSTOMER/$f"
    fi
  done
else
  echo WIN_CUSTOMER_DIRECTORY=missing
fi
journalctl -u celikom-windows-customer-stable.service -n 25 --no-pager -o cat 2>/dev/null | tail -n 50 || true
echo WIN_CUSTOMER_PUBLIC_LATEST_BEGIN
curl --proto '=https' -fsS --max-time 15 https://celikom.com/CELIKOM/Windows/Updates/stable/latest.json 2>&1 |
  python3 -c 'import json,sys; d=json.load(sys.stdin); print("WIN_CUSTOMER_PUBLIC_LATEST", "version="+str(d.get("version","")), "sequence="+str(d.get("sequence","")), "sha256="+str(d.get("sha256","")))' || true
for url in https://celikom.com/CELIKOM/Windows/Updates/stable/0.24.64/manifest.json https://celikom.com/CELIKOM/Windows/Updates/stable/0.24.64/CELIKOM-Windows-0.24.64.exe https://celikom.com/downloads/windows/CELIKOM-Windows-stable.exe; do
  printf 'WIN_CUSTOMER_PUBLIC_HEAD %s ' "$url"
  curl --proto '=https' -sSI --max-time 15 "$url" 2>&1 | sed -n '1,5p' | tr '\n' ' '
  echo
done
echo WINDOWS_CUSTOMER_STABLE_CONSUMER_STATE_END
echo WINDOWS_OWNER_DELIVERY_INVENTORY_END
