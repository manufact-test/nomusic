#!/bin/bash
# Trusted one-time FlokiNET installer. Never run in an unprivileged CI runner.
# Future releases require only an approved manifest on main and a CI ZIP;
# the root-owned timer promotes automatically after verifying exact bytes.
set -Eeuo pipefail
umask 077
[[ "$(id -u)" == 0 ]]

MIRROR=/home/celikom-mirror/github-mirror.git
COMMIT=eee6e0a466c4fc985323ab6bf2e1b688fb4679de
BLOB=99dc1fb5d7b1b52c20b758df37f2d7dfbbbf1c11
SOURCE=.github/scripts/floki-extension-owner-consumer.py
DEST=/usr/local/lib/celikom-extension-release/consumer.py
SERVICE=/etc/systemd/system/celikom-extension-owner.service
TIMER=/etc/systemd/system/celikom-extension-owner.timer
SITE=/etc/nginx/sites-enabled/celikom-site-https
[[ -d "$MIRROR" && ! -L "$MIRROR" ]]
[[ -f "$SITE" ]]
REAL=$(readlink -f "$SITE")
[[ "$REAL" == /etc/nginx/sites-available/* && ! -L "$REAL" ]]

d=$(mktemp -d /root/celikom-extension-activation.XXXXXXXX)
trap 'rm -rf -- "$d"' EXIT
runuser -u celikom-mirror -- git --git-dir="$MIRROR" show \
  "$COMMIT:$SOURCE" > "$d/consumer.py"
[[ "$(git hash-object "$d/consumer.py")" == "$BLOB" ]]
python3 -m py_compile "$d/consumer.py"

# Permanent version + latest routes are added once. They inherit the site's
# existing owner Basic protection and do not expose other release directories.
cp -a "$REAL" "$d/site.conf"
python3 - "$REAL" <<'PY'
import os,pathlib,stat,sys,tempfile
p=pathlib.Path(sys.argv[1]); s=p.read_text()
end="    # END CELIKOM OWNER DOWNLOADS\n"
marker="    # CELIKOM EXTENSION OWNER VERSIONED ROUTES"
assert s.count(end)==1, "EXTENSION_NGINX_MARKER"
assert 'auth_basic "CELIKOM private review";' in s and 'auth_basic_user_file' in s, "EXTENSION_OWNER_BASIC"
assert "location = /downloads/extension/celikom-extension-0.4.73.zip" in s, "EXTENSION_EXISTING_DOWNLOAD_MISSING"
if marker not in s:
    assert "celikom-extension-latest.zip" not in s, "EXTENSION_LATEST_ROUTE_CONFLICT"
    routes=r'''    # CELIKOM EXTENSION OWNER VERSIONED ROUTES
    # Restricted to independently approved ZIP bytes in owner-downloads.
    location ~ "^/downloads/extension/celikom-extension-(?<celikomextver>(?:0|[1-9][0-9]{0,4})\.(?:0|[1-9][0-9]{0,4})\.(?:0|[1-9][0-9]{0,4}))\.zip$" {
        alias /srv/celikom-releases/owner-downloads/celikom-extension-$celikomextver.zip;
        default_type application/zip;
        add_header Content-Disposition 'attachment; filename="celikom-extension-$celikomextver.zip"' always;
        add_header X-Robots-Tag "noindex, nofollow" always;
        add_header Cache-Control "private, no-store" always;
        access_log off;
        limit_except GET { deny all; }
    }
    location = /downloads/extension/celikom-extension-latest.zip {
        alias /srv/celikom-releases/owner-downloads/celikom-extension-latest.zip;
        default_type application/zip;
        add_header Content-Disposition 'attachment; filename="celikom-extension-latest.zip"' always;
        add_header X-Robots-Tag "noindex, nofollow" always;
        add_header Cache-Control "private, no-store" always;
        access_log off;
        limit_except GET { deny all; }
    }
'''
    st=p.stat()
    fd,tmp=tempfile.mkstemp(prefix=".celikom-extension-nginx-",dir=p.parent)
    try:
        with os.fdopen(fd,"w") as f:
            f.write(s.replace(end,routes+end))
            f.flush();os.fsync(f.fileno())
        os.chown(tmp,st.st_uid,st.st_gid)
        os.chmod(tmp,stat.S_IMODE(st.st_mode))
        os.replace(tmp,p)
    finally:
        if os.path.lexists(tmp): os.unlink(tmp)
    print("EXTENSION_OWNER_NGINX_ROUTES_ADDED")
else:
    assert s.count(marker)==1 and "celikom-extension-latest.zip" in s, "EXTENSION_OWNER_ROUTES_CONFLICT"
    print("EXTENSION_OWNER_NGINX_ROUTES_ALREADY_PRESENT")
PY
if ! nginx -t; then
  cp -a "$d/site.conf" "$REAL"
  nginx -t || true
  echo EXTENSION_NGINX_ROLLBACK
  exit 1
fi
systemctl reload nginx

install -d -o root -g root -m 0755 /usr/local/lib/celikom-extension-release
install -d -o root -g root -m 0750 /srv/celikom-releases/private/extension
install -d -o root -g root -m 0750 /srv/celikom-releases/private/extension/versions
if [[ -e "$DEST" || -L "$DEST" ]]; then
  [[ ! -L "$DEST" && "$(git hash-object "$DEST")" == "$BLOB" ]]
else
  install -o root -g root -m 0644 "$d/consumer.py" "$DEST"
fi
[[ "$(git hash-object "$DEST")" == "$BLOB" ]]
[[ ! -e "$SERVICE" && ! -L "$SERVICE" && ! -e "$TIMER" && ! -L "$TIMER" ]]

cat > "$SERVICE" <<'UNIT'
[Unit]
Description=CELIKOM verified extension owner ZIP publisher
After=local-fs.target
ConditionPathIsDirectory=/srv/celikom/ci-runner/runner/celikom-build-spool

[Service]
Type=oneshot
User=root
Group=root
UMask=0077
ExecStart=/usr/bin/python3 /usr/local/lib/celikom-extension-release/consumer.py
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
Description=Poll verified extension owner releases

[Timer]
OnBootSec=120s
OnUnitInactiveSec=60s
RandomizedDelaySec=5s
Persistent=yes
Unit=celikom-extension-owner.service

[Install]
WantedBy=timers.target
UNIT
chmod 0644 "$SERVICE" "$TIMER"
systemctl daemon-reload
systemctl start celikom-mirror-sync.service
# First publish exact approved 0.4.82 before enabling unattended promotions.
if ! systemctl start celikom-extension-owner.service; then
  systemctl disable --now celikom-extension-owner.timer 2>/dev/null || true
  journalctl -u celikom-extension-owner.service -n 25 --no-pager -o cat
  echo EXTENSION_OWNER_ACTIVATION_FAILED_KEEP_TIMER_DISABLED
  exit 1
fi
# The owner withdrew 0.4.82 after a playback regression; until a future
# candidate is explicitly approved, install the timer but publish NO new ZIP.
# Keep the previously live owner download untouched.
if [[ -f /srv/celikom-releases/private/extension/current-owner.json ]]; then
  [[ -f /srv/celikom-releases/owner-downloads/celikom-extension-latest.zip ]]
  echo EXTENSION_OWNER_ALREADY_VERIFIED_LATEST_PRESENT
else
  echo EXTENSION_OWNER_AWAITING_NEXT_APPROVED_CANDIDATE
fi
systemctl enable --now celikom-extension-owner.timer
systemctl is-active celikom-extension-owner.timer
echo EXTENSION_OWNER_PERMANENT_PUBLISHER_ARMED
