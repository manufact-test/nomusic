#!/bin/bash
# One-time sanitized root-verified release status: SHA-only JSON, no secrets.
set -Eeuo pipefail
umask 077
[[ "$(id -u)" == 0 ]]
MIRROR=/home/celikom-mirror/github-mirror.git
COMMIT=23efa0e782deb944fb4a3752120de54d99667fa1
BLOB=fa975f6d4b31c7d8dbbb26aa324bf45b7a4906a2
SOURCE=.github/scripts/floki-release-public-receipt.py
DEST=/usr/local/lib/celikom-release-status/receipt.py
SERVICE=/etc/systemd/system/celikom-release-status.service
TIMER=/etc/systemd/system/celikom-release-status.timer
SITE=/etc/nginx/sites-enabled/celikom-site-https
[[ ! -e "$SERVICE" && ! -e "$TIMER" ]]
[[ -d "$MIRROR" && ! -L "$MIRROR" ]]
[[ -f "$SITE" ]]
REAL=$(readlink -f "$SITE")
[[ "$REAL" == /etc/nginx/sites-available/* && ! -L "$REAL" ]]
[[ -d /srv/celikom-releases/windows/stable/versions ]]
[[ ! -e /srv/celikom-releases/release-status ]]
tmp=$(mktemp -d /root/celikom-release-status-install.XXXXXXXX)
ready=0
cleanup() {
  local rc=$?
  if [[ "$ready" != 1 && -f "$tmp/site.conf" ]]; then
    cp -a "$tmp/site.conf" "$REAL"
    nginx -t && systemctl reload nginx || true
    systemctl disable --now celikom-release-status.timer >/dev/null 2>&1 || true
    rm -f -- "$SERVICE" "$TIMER" "$DEST"
    systemctl daemon-reload || true
    echo RELEASE_STATUS_FIRST_INSTALL_ROLLED_BACK
  fi
  rm -rf -- "$tmp"
  return "$rc"
}
trap cleanup EXIT

runuser -u celikom-mirror -- git --git-dir="$MIRROR" show "$COMMIT:$SOURCE" > "$tmp/receipt.py"
[[ "$(git hash-object "$tmp/receipt.py")" == "$BLOB" ]]
python3 -m py_compile "$tmp/receipt.py"
cp -a "$REAL" "$tmp/site.conf"
python3 - "$REAL" <<'PY'
import os,pathlib,stat,sys,tempfile
p=pathlib.Path(sys.argv[1]);s=p.read_text()
end="    # END CELIKOM OWNER DOWNLOADS\n"
marker="    # CELIKOM SANITIZED SHA-ONLY RELEASE RECEIPTS"
assert s.count(end)==1 and marker not in s, "STATUS_NGINX_MARKER"
assert "location = /.well-known/celikom-release-receipt.json" not in s,"STATUS_ROUTE_CONFLICT"
routes=r'''    # CELIKOM SANITIZED SHA-ONLY RELEASE RECEIPTS
    # Does NOT contain internal links, source refs, identities or A1 capabilities.
    location = /.well-known/celikom-release-receipt.json {
        auth_basic off;
        allow all;
        alias /srv/celikom-releases/release-status/receipt.json;
        default_type application/json;
        add_header Cache-Control "no-store" always;
        add_header X-Robots-Tag "noindex, nofollow" always;
        limit_except GET { deny all; }
    }
'''
st=p.stat()
fd,t=tempfile.mkstemp(prefix=".celikom-status-nginx-",dir=p.parent)
try:
 with os.fdopen(fd,"w") as f:
  f.write(s.replace(end,routes+end));f.flush();os.fsync(f.fileno())
 os.chown(t,st.st_uid,st.st_gid);os.chmod(t,stat.S_IMODE(st.st_mode))
 os.replace(t,p)
finally:
 if os.path.lexists(t):os.unlink(t)
PY
nginx -t
systemctl reload nginx
install -d -o root -g root -m 0755 /srv/celikom-releases/release-status
install -d -o root -g root -m 0755 /usr/local/lib/celikom-release-status
install -o root -g root -m 0644 "$tmp/receipt.py" "$DEST"
cat > "$SERVICE" <<'UNIT'
[Unit]
Description=CELIKOM release SHA-only publication readiness receipt
After=local-fs.target celikom-windows-signed-owner.service celikom-extension-owner.service celikom-android-stable-owner.service

[Service]
Type=oneshot
User=root
Group=root
UMask=0077
ExecStart=/usr/bin/python3 /usr/local/lib/celikom-release-status/receipt.py
TimeoutStartSec=60
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
Description=Refresh non-sensitive CELIKOM release SHA receipts

[Timer]
OnBootSec=90s
OnUnitInactiveSec=120s
RandomizedDelaySec=5s
Persistent=yes
Unit=celikom-release-status.service

[Install]
WantedBy=timers.target
UNIT
chmod 0644 "$SERVICE" "$TIMER"
systemctl daemon-reload
systemctl start celikom-release-status.service
python3 - <<'PY'
import urllib.request,json,pathlib
path=pathlib.Path("/srv/celikom-releases/release-status/receipt.json")
with urllib.request.urlopen(
 "https://celikom.com/.well-known/celikom-release-receipt.json",timeout=30
) as r:
 assert r.status==200 and r.read(4097)==path.read_bytes(),"PUBLIC_STATUS_SHA_RECEIPT_HTTP"
j=json.loads(path.read_bytes())
assert j["schema"]==1 and set(j["channels"])=={
 "windows_owner_sha256","windows_customer_sha256",
 "extension_owner_sha256","android_owner_sha256","android_customer_sha256"
}
print("CELIKOM_RELEASE_PUBLIC_SHA_RECEIPTS_HTTP_200_VERIFIED")
PY
systemctl enable --now celikom-release-status.timer
systemctl is-active celikom-release-status.timer
ready=1
echo CELIKOM_RELEASE_SHA_ONLY_STATUS_VERIFIED_AND_RECURRING
