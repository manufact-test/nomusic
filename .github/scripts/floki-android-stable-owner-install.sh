#!/bin/bash
# One-time owner-channel legacy Android installation. Never touches Android A1.
# No APK is published unless a separately signed, root-verified CI stage exists.
set -Eeuo pipefail
umask 077
[[ "$(id -u)" == 0 ]]
MIRROR=/home/celikom-mirror/github-mirror.git
COMMIT=47121924095e0ab205c8bd5236dd3d48abec0eb4
BLOB=7caf3ed79b227802a82a05353b456813575571fd
SOURCE=.github/scripts/floki-android-stable-root-consumer.py
DEST=/usr/local/lib/celikom-android-stable-owner/consumer.py
SERVICE=/etc/systemd/system/celikom-android-stable-owner.service
TIMER=/etc/systemd/system/celikom-android-stable-owner.timer
SITE=/etc/nginx/sites-enabled/celikom-site-https
ROOT=/srv/celikom-releases/private/android-stable
SPOOL=/srv/celikom/ci-runner/runner/celikom-build-spool/android-stable

[[ -d "$MIRROR" && ! -L "$MIRROR" ]]
[[ ! -e "$SERVICE" && ! -e "$TIMER" ]]
[[ -f "$SITE" ]]
REAL=$(readlink -f "$SITE")
[[ "$REAL" == /etc/nginx/sites-available/* && ! -L "$REAL" ]]
[[ -d /srv/celikom/ci-runner/runner/celikom-build-spool ]]
SPOOL_PARENT=/srv/celikom/ci-runner/runner/celikom-build-spool
SPOOL_UID=$(stat -c '%u' "$SPOOL_PARENT")
SPOOL_GID=$(stat -c '%g' "$SPOOL_PARENT")
[[ "$SPOOL_UID" -gt 0 && "$(stat -c '%a' "$SPOOL_PARENT")" == 700 ]]
[[ -d /srv/celikom-releases/owner-downloads ]]
for bin in /usr/bin/apksigner /usr/bin/aapt; do [[ -x "$bin" ]]; done

tmp=$(mktemp -d /root/celikom-android-stable-activate.XXXXXXXX)
ok=0
rollback() {
  local rc=$?
  if [[ "$ok" != 1 && -f "$tmp/site.conf" ]]; then
    cp -a "$tmp/site.conf" "$REAL"
    nginx -t && systemctl reload nginx || true
    systemctl disable --now celikom-android-stable-owner.timer >/dev/null 2>&1 || true
    rm -f "$SERVICE" "$TIMER" "$DEST"
    systemctl daemon-reload || true
    echo ANDROID_STABLE_OWNER_INSTALL_ROLLBACK
  fi
  rm -rf -- "$tmp"
  return "$rc"
}
trap rollback EXIT

runuser -u celikom-mirror -- git --git-dir="$MIRROR" show "$COMMIT:$SOURCE" > "$tmp/consumer.py"
[[ "$(git hash-object "$tmp/consumer.py")" == "$BLOB" ]]
python3 -m py_compile "$tmp/consumer.py"
cp -a "$REAL" "$tmp/site.conf"

python3 - "$REAL" <<'PY'
import os,pathlib,stat,sys,tempfile
p=pathlib.Path(sys.argv[1]);s=p.read_text()
end="    # END CELIKOM OWNER DOWNLOADS\n"
marker="    # CELIKOM LEGACY ANDROID SIGNED OWNER DOWNLOADS"
assert s.count(end)==1 and marker not in s, "ANDROID_OWNER_NGINX_MARKERS"
assert 'auth_basic "CELIKOM private review";' in s, "ANDROID_OWNER_AUTH_MISSING"
assert "CELIKOM-Android-latest.apk" not in s, "ANDROID_OWNER_ROUTE_EXISTS"
routes=r'''    # CELIKOM LEGACY ANDROID SIGNED OWNER DOWNLOADS
    # Applies site's existing Basic authentication; never serve runner spool.
    location ~ "^/downloads/android/CELIKOM-Android-(?<celikomlegacyandroid>0\.3\.(?:0|[1-9][0-9]{0,3}))-SIGNED\.apk$" {
        alias /srv/celikom-releases/owner-downloads/CELIKOM-Android-$celikomlegacyandroid-SIGNED.apk;
        default_type application/vnd.android.package-archive;
        add_header Cache-Control "private, no-store" always;
        add_header X-Robots-Tag "noindex, nofollow" always;
        limit_except GET { deny all; }
    }
    location = /downloads/android/CELIKOM-Android-latest.apk {
        alias /srv/celikom-releases/owner-downloads/CELIKOM-Android-latest.apk;
        default_type application/vnd.android.package-archive;
        add_header Cache-Control "private, no-store" always;
        add_header X-Robots-Tag "noindex, nofollow" always;
        limit_except GET { deny all; }
    }
'''
st=p.stat();fd,temp=tempfile.mkstemp(prefix=".celikom-android-owner-nginx-",dir=p.parent)
try:
  with os.fdopen(fd,"w") as f:
    f.write(s.replace(end,routes+end));f.flush();os.fsync(f.fileno())
  os.chown(temp,st.st_uid,st.st_gid);os.chmod(temp,stat.S_IMODE(st.st_mode))
  os.replace(temp,p)
finally:
  if os.path.lexists(temp):os.unlink(temp)
PY
nginx -t
systemctl reload nginx

install -d -o "$SPOOL_UID" -g "$SPOOL_GID" -m 0700 "$SPOOL"
install -d -o root -g root -m 0755 /usr/local/lib/celikom-android-stable-owner
install -d -o root -g root -m 0750 "$ROOT"
install -d -o root -g root -m 0750 "$ROOT/versions"
install -o root -g root -m 0644 "$tmp/consumer.py" "$DEST"

cat > "$SERVICE" <<'UNIT'
[Unit]
Description=CELIKOM legacy Android independently signed owner APK publisher
After=local-fs.target
ConditionPathIsDirectory=/srv/celikom/ci-runner/runner/celikom-build-spool/android-stable

[Service]
Type=oneshot
User=root
Group=root
UMask=0077
ExecStart=/usr/bin/python3 /usr/local/lib/celikom-android-stable-owner/consumer.py
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
Description=Poll signed legacy Android stable owner candidates

[Timer]
OnBootSec=120s
OnUnitInactiveSec=120s
RandomizedDelaySec=5s
Persistent=yes
Unit=celikom-android-stable-owner.service

[Install]
WantedBy=timers.target
UNIT
chmod 0644 "$SERVICE" "$TIMER"
systemctl daemon-reload
systemctl start celikom-android-stable-owner.service
systemctl enable --now celikom-android-stable-owner.timer
systemctl is-active celikom-android-stable-owner.timer
ok=1
echo ANDROID_STABLE_SIGNED_OWNER_PUBLISHER_READY
