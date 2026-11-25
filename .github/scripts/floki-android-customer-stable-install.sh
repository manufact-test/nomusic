#!/bin/bash
# Public legacy Android OTA routes and verifier. DISABLED until explicit approval.
# Existing Hostinger old-client bridge and A1 service are never modified.
set -Eeuo pipefail
umask 077
[[ "$(id -u)" == 0 ]]
MIRROR=/home/celikom-mirror/github-mirror.git
COMMIT=fb3cb67b11d7916668d5cd6033090f1cfcf2d264
BLOB=c6ce4e6e6db125cc921663405fcd668d7c71d8b9
SOURCE=.github/scripts/floki-android-customer-stable-consumer.py
DEST=/usr/local/lib/celikom-android-stable-owner/customer-consumer.py
SERVICE=/etc/systemd/system/celikom-android-customer-stable.service
TIMER=/etc/systemd/system/celikom-android-customer-stable.timer
PUBLIC=/srv/celikom-releases/public/android
SITE=/etc/nginx/sites-enabled/celikom-site-https
[[ -d "$MIRROR" && ! -L "$MIRROR" ]]
[[ ! -e "$SERVICE" && ! -e "$TIMER" ]]
[[ -d /srv/celikom-releases/private/android-stable/versions ]]
[[ -f "$SITE" && ! -L /srv/celikom-releases ]]
REAL=$(readlink -f "$SITE")
[[ "$REAL" == /etc/nginx/sites-available/* && ! -L "$REAL" ]]

tmp=$(mktemp -d /root/celikom-public-android.XXXXXXXX)
ready=0
cleanup() {
  local rc=$?
  if [[ "$ready" != 1 && -f "$tmp/site.conf" ]]; then
    cp -a "$tmp/site.conf" "$REAL"
    nginx -t && systemctl reload nginx || true
    systemctl disable --now celikom-android-customer-stable.timer >/dev/null 2>&1 || true
    rm -f -- "$SERVICE" "$TIMER" "$DEST"
    systemctl daemon-reload || true
    echo ANDROID_CUSTOMER_STABLE_FIRST_INSTALL_ROLLED_BACK
  fi
  rm -rf -- "$tmp"
  return "$rc"
}
trap cleanup EXIT

runuser -u celikom-mirror -- git --git-dir="$MIRROR" show "$COMMIT:$SOURCE" > "$tmp/consumer.py"
[[ "$(git hash-object "$tmp/consumer.py")" == "$BLOB" ]]
python3 -m py_compile "$tmp/consumer.py"
runuser -u celikom-mirror -- git --git-dir="$MIRROR" show \
 refs/heads/main:.github/release/android-customer-stable.json > "$tmp/approval.json"
python3 - "$tmp/approval.json" <<'PY'
import json,sys
assert json.load(open(sys.argv[1]))=={
 "schema":1,"channel":"customer-stable","approved":None
}, "ANDROID_PUBLIC_OTA_UNEXPECTED_APPROVAL"
PY
cp -a "$REAL" "$tmp/site.conf"
python3 - "$REAL" <<'PY'
import os,pathlib,stat,sys,tempfile
p=pathlib.Path(sys.argv[1]);s=p.read_text()
end="    # END CELIKOM OWNER DOWNLOADS\n"
mark="    # CELIKOM LEGACY ANDROID PUBLIC VERIFIED STABLE OTA"
assert s.count(end)==1 and mark not in s, "ANDROID_PUBLIC_NGINX_MARKERS"
for loc in ("location = /updates/android/stable.json",
            "location ~ \"^/releases/android/"):
    assert loc not in s, "ANDROID_PUBLIC_ROUTE_ALREADY_EXISTS"
rules=r'''    # CELIKOM LEGACY ANDROID PUBLIC VERIFIED STABLE OTA
    # Source: immutable signed APK checked by a separate ROOT-owned promoter.
    # No public manifest exists until the owner accepts a release.
    location = /updates/android/stable.json {
        auth_basic off;
        alias /srv/celikom-releases/public/android/stable.json;
        default_type application/json;
        add_header Cache-Control "no-store" always;
        limit_except GET { deny all; }
    }
    location ~ "^/releases/android/(?<celikomlegacyapk>[1-9][0-9]{0,8}-[a-f0-9]{64}\.apk)$" {
        auth_basic off;
        alias /srv/celikom-releases/public/android/$celikomlegacyapk;
        default_type application/vnd.android.package-archive;
        add_header Cache-Control "public, max-age=300, immutable" always;
        limit_except GET { deny all; }
    }
'''
st=p.stat();fd,t=tempfile.mkstemp(prefix=".android-public-nginx-",dir=p.parent)
try:
 with os.fdopen(fd,"w") as f:
  f.write(s.replace(end,rules+end));f.flush();os.fsync(f.fileno())
 os.chown(t,st.st_uid,st.st_gid);os.chmod(t,stat.S_IMODE(st.st_mode))
 os.replace(t,p)
finally:
 if os.path.lexists(t):os.unlink(t)
PY

nginx -t
systemctl reload nginx
if [[ -e /srv/celikom-releases/public ]]; then
  [[ -d /srv/celikom-releases/public &&
     ! -L /srv/celikom-releases/public &&
     "$(stat -c '%u' /srv/celikom-releases/public)" == 0 &&
     "$(stat -c '%a' /srv/celikom-releases/public)" == 755 ]]
else
  install -d -o root -g root -m 0755 /srv/celikom-releases/public
fi
[[ ! -e "$PUBLIC" ]]
install -d -o root -g root -m 0755 "$PUBLIC"
install -o root -g root -m 0644 "$tmp/consumer.py" "$DEST"

cat > "$SERVICE" <<'UNIT'
[Unit]
Description=CELIKOM owner-approved legacy Android public stable OTA publisher
After=local-fs.target

[Service]
Type=oneshot
User=root
Group=root
UMask=0077
ExecStart=/usr/bin/python3 /usr/local/lib/celikom-android-stable-owner/customer-consumer.py
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
Description=Monitor explicit legacy Android customer stable approvals

[Timer]
OnBootSec=150s
OnUnitInactiveSec=150s
RandomizedDelaySec=5s
Persistent=yes
Unit=celikom-android-customer-stable.service

[Install]
WantedBy=timers.target
UNIT
chmod 0644 "$SERVICE" "$TIMER"
systemctl daemon-reload
systemctl start celikom-mirror-sync.service
systemctl start celikom-android-customer-stable.service
[[ ! -e "$PUBLIC/stable.json" ]]
systemctl enable --now celikom-android-customer-stable.timer
systemctl is-active celikom-android-customer-stable.timer
ready=1
echo ANDROID_CUSTOMER_STABLE_OTA_ARMED_NO_UNACCEPTED_RELEASE
