#!/bin/bash
# One-time root-only activation of public customer signed Windows update routes.
# A separate acceptance manifest is null by default: seeds ONLY accepted 0.24.55 baseline.
set -Eeuo pipefail
umask 077
[[ "$(id -u)" == 0 ]]
MIRROR=/home/celikom-mirror/github-mirror.git
COMMIT=06830a1fb62dc3ef7a40286d63378cd37f0d5a76
SOURCE=.github/scripts/floki-windows-customer-stable-consumer.py
BLOB=a4898589f38e051bd2c8a803e5bbc16c52ecc8f9
SITE=/etc/nginx/sites-enabled/celikom-site-https
APP=/usr/local/lib/celikom-windows-intake/customer-stable-consumer.py
SERVICE=/etc/systemd/system/celikom-windows-customer-stable.service
TIMER=/etc/systemd/system/celikom-windows-customer-stable.timer

[[ -d "$MIRROR" && ! -L "$MIRROR" ]]
[[ -f "$SITE" ]]
REAL=$(readlink -f "$SITE")
[[ "$REAL" == /etc/nginx/sites-available/* && ! -L "$REAL" ]]
[[ ! -e "$SERVICE" && ! -e "$TIMER" ]]
[[ -d /srv/celikom-releases/windows/stable/versions ]]
# Install a pinned, self-contained signature verifier from the read-only mirror.
# A fresh VPS is not expected to have this helper preinstalled.
TOOLS=/root/celikom-release-tools
VERIFY_COMMIT=1f438a88bca19cbdec95c44dd03b4c3285435046
VERIFY_BLOB=bb4d19672d45bdd0393497c3b33280308d67ef32
[[ ! -e "$TOOLS" || ( -d "$TOOLS" && ! -L "$TOOLS" && "$(stat -c '%u:%a' "$TOOLS")" == 0:700 ) ]]
if [[ -e "$TOOLS/windows-stable-existing-latest.mjs" ]]; then
  [[ -f "$TOOLS/windows-stable-existing-latest.mjs" &&
     ! -L "$TOOLS/windows-stable-existing-latest.mjs" &&
     "$(git hash-object "$TOOLS/windows-stable-existing-latest.mjs")" == "$VERIFY_BLOB" ]]
fi
[[ "$(sha256sum /root/celikom-secrets/windows-stable-public.der | cut -d' ' -f1)" == 46b36bb222154316f2229c35cf65e6c953e0b6524dfb0aad8de05949dc143a95 ]]

tmp=$(mktemp -d /root/celikom-windows-public-feed.XXXXXXXX)
ready=0
cleanup() {
  local rc=$?
  if [[ "$ready" != 1 && -f "$tmp/site.conf" ]]; then
    # Restore precisely the previous site configuration on a failed first activation.
    cp -a "$tmp/site.conf" "$REAL"
    nginx -t && systemctl reload nginx || true
    systemctl disable --now celikom-windows-customer-stable.timer >/dev/null 2>&1 || true
    rm -f -- "$SERVICE" "$TIMER" "$APP"
    if [[ -f "$tmp/verifier-installed-by-this-run" ]]; then
      rm -f -- "$TOOLS/windows-stable-existing-latest.mjs"
      rmdir "$TOOLS" >/dev/null 2>&1 || true
    fi
    systemctl daemon-reload || true
    echo CUSTOMER_WINDOWS_FIRST_ACTIVATION_ROLLED_BACK
  fi
  rm -rf -- "$tmp"
  return "$rc"
}
trap cleanup EXIT
runuser -u celikom-mirror -- git --git-dir="$MIRROR" show "$COMMIT:$SOURCE" > "$tmp/consumer.py"
[[ "$(git hash-object "$tmp/consumer.py")" == "$BLOB" ]]
python3 -m py_compile "$tmp/consumer.py"
runuser -u celikom-mirror -- git --git-dir="$MIRROR" show \
  "$VERIFY_COMMIT:.github/scripts/windows-stable-existing-latest.mjs" > "$tmp/verifier.mjs"
[[ "$(git hash-object "$tmp/verifier.mjs")" == "$VERIFY_BLOB" ]]
node --check "$tmp/verifier.mjs"
install -d -o root -g root -m 0700 "$TOOLS"
if [[ ! -e "$TOOLS/windows-stable-existing-latest.mjs" ]]; then
  install -o root -g root -m 0600 "$tmp/verifier.mjs" "$TOOLS/windows-stable-existing-latest.mjs"
  touch "$tmp/verifier-installed-by-this-run"
fi
# Validate the approval contract before enabling the timer.
runuser -u celikom-mirror -- git --git-dir="$MIRROR" show \
  refs/heads/main:.github/release/windows-customer-stable.json > "$tmp/approval.json"
python3 - "$tmp/approval.json" <<'PY'
import json,sys
a=json.load(open(sys.argv[1]))
assert a=={"schema":1,"channel":"customer-stable","approved":None},"CUSTOMER_WINDOWS_UNEXPECTED_APPROVAL"
PY

install -d -o root -g root -m 0755 /srv/celikom-releases/windows/customer-stable
install -d -o root -g root -m 0755 /srv/celikom-releases/windows/customer-stable/versions
install -o root -g root -m 0644 "$tmp/consumer.py" "$APP"

cp -a "$REAL" "$tmp/site.conf"
python3 - "$REAL" <<'PY'
import os,pathlib,stat,sys,tempfile
p=pathlib.Path(sys.argv[1]);s=p.read_text()
end="    # END CELIKOM OWNER DOWNLOADS\n"
marker="    # CELIKOM CUSTOMER SIGNED WINDOWS UPDATER"
assert s.count(end)==1, "CUSTOMER_WINDOWS_NO_SAFE_INSERTION_POINT"
assert 'auth_basic "CELIKOM private review";' in s, "PRIVATE_OWNER_GATE_MISSING"
assert marker not in s, "CUSTOMER_WINDOWS_DUPLICATE_ROUTES"
for path in ("/CELIKOM/Windows/Updates/stable/latest.json",
             "/CELIKOM/Windows/Updates/stable/latest.json.sig"):
    assert "location = "+path not in s, "CUSTOMER_WINDOWS_ROUTE_CONFLICT"
assert "location = /downloads/windows/CELIKOM-Windows-stable.exe" not in s, "CUSTOMER_WINDOWS_PUBLIC_INSTALLER_CONFLICT"
routes=r'''    # CELIKOM CUSTOMER SIGNED WINDOWS UPDATER
    # Public read-only metadata ONLY from separately accepted P-256 releases.
    # Customer store starts at accepted 0.24.55; later versions require approval.
    location = /downloads/windows/CELIKOM-Windows-stable.exe {
        # Public installer is absent until the exact signed build is accepted.
        auth_basic off;
        alias /srv/celikom-releases/windows/customer-stable/CELIKOM-Windows-stable.exe;
        default_type application/octet-stream;
        add_header Cache-Control "no-cache" always;
        add_header X-Content-Type-Options "nosniff" always;
        limit_except GET { deny all; }
    }
    location = /CELIKOM/Windows/Updates/stable/latest.json {
        auth_basic off;
        alias /srv/celikom-releases/windows/customer-stable/latest.json;
        default_type application/json;
        add_header Cache-Control "no-store" always;
        limit_except GET { deny all; }
    }
    location = /CELIKOM/Windows/Updates/stable/latest.json.sig {
        auth_basic off;
        alias /srv/celikom-releases/windows/customer-stable/latest.json.sig;
        default_type application/octet-stream;
        add_header Cache-Control "no-store" always;
        limit_except GET { deny all; }
    }
    location ~ "^/CELIKOM/Windows/Updates/stable/(?<celikomstableversion>(?:0|[1-9][0-9]{0,3})\.(?:0|[1-9][0-9]{0,3})\.(?:0|[1-9][0-9]{0,4}))/(?<celikomstablefilename>manifest\.json(?:\.sig)?|CELIKOM-Windows-[0-9]+\.[0-9]+\.[0-9]+\.exe)$" {
        auth_basic off;
        alias /srv/celikom-releases/windows/customer-stable/versions/$celikomstableversion/$celikomstablefilename;
        default_type application/octet-stream;
        add_header Cache-Control "public, max-age=300, immutable" always;
        limit_except GET { deny all; }
    }
'''
st=p.stat()
fd,t=tempfile.mkstemp(prefix=".customer-windows-nginx-",dir=p.parent)
try:
  with os.fdopen(fd,"w") as f:
    f.write(s.replace(end,routes+end))
    f.flush();os.fsync(f.fileno())
  os.chown(t,st.st_uid,st.st_gid);os.chmod(t,stat.S_IMODE(st.st_mode))
  os.replace(t,p)
finally:
  if os.path.exists(t):os.unlink(t)
PY
if ! nginx -t; then
  cp -a "$tmp/site.conf" "$REAL"
  nginx -t || true
  echo CUSTOMER_WINDOWS_NGINX_ROLLBACK
  exit 1
fi
systemctl reload nginx

# Seed only the previously accepted, signed 0.24.55 baseline. A client
# upgrading from 0.24.55 MUST be able to fetch its own immutable signed
# manifest and installer for rollback. Never seed unaccepted owner v56.
python3 - <<'PY'
import importlib.util,json
from pathlib import Path
p=Path("/usr/local/lib/celikom-windows-intake/customer-stable-consumer.py")
spec=importlib.util.spec_from_file_location("customer_baseline",p)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
manifest=json.loads((mod.SIGNED_ROOT/"0.24.55"/"manifest.json").read_bytes())
assert manifest["version"]=="0.24.55" and manifest["sequence"]==2
assert manifest["packageUrl"]=="https://celikom.com/CELIKOM/Windows/Updates/stable/0.24.55/CELIKOM-Windows-0.24.55.exe"
mod.publish({"version":"0.24.55","sequence":2,"sha256":manifest["sha256"],
             "owner_accepted":True})
print("CUSTOMER_WINDOWS_ACCEPTED_BASELINE_02455_SIGNED_AND_HTTPS_VERIFIED")
PY

cat > "$SERVICE" <<'UNIT'
[Unit]
Description=CELIKOM approved P-256 Windows customer updater publisher
After=local-fs.target
ConditionPathIsDirectory=/srv/celikom-releases/windows/customer-stable

[Service]
Type=oneshot
User=root
Group=root
UMask=0077
ExecStart=/usr/bin/python3 /usr/local/lib/celikom-windows-intake/customer-stable-consumer.py
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
Description=Check explicitly accepted Windows signed customer feed

[Timer]
OnBootSec=120s
OnUnitInactiveSec=120s
RandomizedDelaySec=5s
Persistent=yes
Unit=celikom-windows-customer-stable.service

[Install]
WantedBy=timers.target
UNIT
chmod 0644 "$SERVICE" "$TIMER"
systemctl daemon-reload
systemctl start celikom-mirror-sync.service
systemctl start celikom-windows-customer-stable.service
[[ -f /srv/celikom-releases/windows/customer-stable/latest.json &&
   -f /srv/celikom-releases/windows/customer-stable/accepted.json &&
   -f /srv/celikom-releases/windows/customer-stable/CELIKOM-Windows-stable.exe ]]
systemctl enable --now celikom-windows-customer-stable.timer
systemctl is-active celikom-windows-customer-stable.timer
ready=1
echo CUSTOMER_WINDOWS_ACCEPTED_02455_PUBLIC_STABLE_OTA_ARMED_NO_UNACCEPTED_02456
