#!/bin/bash
# One-time trusted owner bootstrap for Windows and extension publication.
# Android A1 is already live and MUST NOT be reconfigured by this installer.
# Never run this on a GitHub Actions self-hosted CI runner.
set -Eeuo pipefail
umask 077
# Fail with an actionable line number; no secrets or command expansion in logs.
trap 'rc=$?; echo "CELIKOM_RELEASE_ACTIVATION_STOPPED line=$LINENO exit=$rc" >&2' ERR
[[ "$(id -u)" == 0 ]]
MIRROR=/home/celikom-mirror/github-mirror.git
[[ -d "$MIRROR" && ! -L "$MIRROR" ]]
systemctl start celikom-mirror-sync.service

# Preflight first: no alteration to working services on an unexpected host.
WIN_CURRENT=$(readlink /srv/celikom-releases/windows/stable/current)
case "$WIN_CURRENT" in
  versions/0.24.55)
    [[ ! -e /etc/systemd/system/celikom-windows-signed-owner.service &&
       ! -e /etc/systemd/system/celikom-windows-signed-owner.timer ]] ;;
  versions/0.24.56)
    [[ -f /etc/systemd/system/celikom-windows-signed-owner.service &&
       -f /etc/systemd/system/celikom-windows-signed-owner.timer ]] ;;
  *) echo "CELIKOM_WINDOWS_UNEXPECTED_CURRENT_VERSION $WIN_CURRENT"; exit 1 ;;
esac
[[ -d /srv/celikom/ci-runner/runner/celikom-windows-signed-spool ]]
[[ -d /srv/celikom/ci-runner/runner/celikom-build-spool ]]
[[ -d /srv/celikom-releases/owner-downloads ]]
if [[ -e /etc/systemd/system/celikom-extension-owner.timer ]]; then
  [[ -f /etc/systemd/system/celikom-extension-owner.service ]]
else
  [[ ! -e /etc/systemd/system/celikom-extension-owner.service ]]
fi
[[ "$(sha256sum /root/celikom-secrets/windows-stable-public.der | cut -d' ' -f1)" == 46b36bb222154316f2229c35cf65e6c953e0b6524dfb0aad8de05949dc143a95 ]]
nginx -t
for cmd in git python3 node systemctl; do command -v "$cmd" >/dev/null; done
for exe in /usr/bin/apksigner /usr/bin/aapt; do [[ -x "$exe" ]]; done
# The original website owner auth is maintained by 'celops' (UID 1000).
# Do not chown/chmod the live website file or break existing CMS/access.
OWNER_BASIC_ORIGINAL=/srv/celikom/migration/sites-20261124/android-private/staging-owner-credentials.txt
OWNER_BASIC_PRIVATE=/root/celikom-secrets/celikom-owner-basic-verification.txt
[[ -f "$OWNER_BASIC_ORIGINAL" && ! -L "$OWNER_BASIC_ORIGINAL" ]] || {
  echo CELIKOM_OWNER_BASIC_SOURCE_MISSING_OR_SYMLINK >&2; exit 1;
}
OWNER_CELOPS_UID=$(id -u celops)
OWNER_BASIC_UID=$(stat -c '%u' "$OWNER_BASIC_ORIGINAL")
if [[ "$OWNER_BASIC_UID" != 0 && "$OWNER_BASIC_UID" != "$OWNER_CELOPS_UID" ]]; then
  echo CELIKOM_OWNER_BASIC_UNEXPECTED_SOURCE_UID >&2
  exit 1
fi
echo CELIKOM_OWNER_BASIC_SOURCE_ACCEPTED_WITHOUT_CHOWN
SITE=/etc/nginx/sites-enabled/celikom-site-https
[[ -f "$SITE" ]]
REAL=$(readlink -f "$SITE")
[[ "$REAL" == /etc/nginx/sites-available/* && ! -L "$REAL" ]]
python3 - "$REAL" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
assert s.count("    # END CELIKOM OWNER DOWNLOADS\n")==1, "OWNER_NGINX_MARKER_MISSING"
assert 'auth_basic "CELIKOM private review";' in s
assert "auth_basic_user_file" in s
assert "location = /downloads/windows/CELIKOM-Windows-0.24.55.exe" in s
assert "location = /downloads/extension/celikom-extension-0.4.73.zip" in s
print("CELIKOM_NGINX_OWNER_GATE_AND_BASE_ROUTES_PRESENT")
PY
[[ "$(df -Pk /srv/celikom-releases | awk 'END {print $4}')" -ge 524288 ]]
echo CELIKOM_RELEASE_BOOTSTRAP_PRECHECK_OK

# Snapshot the existing website Basic credentials into a root-only verification
# file used by all three root release consumers. Do NOT alter the live source,
# nginx auth or service accounts. Format/owner/mode validated before copy.
python3 - "$OWNER_BASIC_ORIGINAL" "$OWNER_BASIC_PRIVATE" "$OWNER_CELOPS_UID" <<'PY'
import os, pathlib, re, stat, sys, tempfile
src, dst = map(pathlib.Path, sys.argv[1:3])
allowed = {0, int(sys.argv[3])}
sd = dst.parent.lstat()
assert stat.S_ISDIR(sd.st_mode) and sd.st_uid == 0 and \
       not (sd.st_mode & 0o022), "OWNER_BASIC_PRIVATE_DIR_UNSAFE"
fd = os.open(src, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
try:
    ss = os.fstat(fd)
    assert stat.S_ISREG(ss.st_mode) and ss.st_uid in allowed and \
           ss.st_nlink == 1 and not (ss.st_mode & 0o027) and \
           1 <= ss.st_size <= 4096, "OWNER_BASIC_SOURCE_SECURITY_CHECK_FAILED"
    with os.fdopen(fd, "rb", closefd=False) as inp:
        secret = inp.read(4097)
    assert len(secret) == ss.st_size, "OWNER_BASIC_SOURCE_CHANGED"
finally:
    os.close(fd)
decoded = secret.decode("utf-8")
seen = {}
for line in decoded.splitlines():
    m = re.fullmatch(r"\s*(HTTP Basic username|HTTP Basic password)\s*[:=]\s*(.*?)\s*", line, re.I)
    if m:
        key = m.group(1).lower()
        assert key not in seen and 0 < len(m.group(2)) <= 256, "OWNER_BASIC_DUPLICATE_OR_EMPTY"
        seen[key] = m.group(2)
assert set(seen) == {"http basic username", "http basic password"}, "OWNER_BASIC_FORMAT_INVALID"
if dst.exists() or dst.is_symlink():
    d = dst.lstat()
    assert stat.S_ISREG(d.st_mode) and d.st_uid == 0 and \
           stat.S_IMODE(d.st_mode) == 0o600 and d.st_nlink == 1, \
           "OWNER_BASIC_DESTINATION_UNTRUSTED"
# Atomic replacement avoids a partially copied secret on power loss.
out, temp = tempfile.mkstemp(prefix=".owner-basic-", dir=dst.parent)
try:
    with os.fdopen(out, "wb") as fd:
        fd.write(secret)
        fd.flush()
        os.fsync(fd.fileno())
    os.chown(temp, 0, 0)
    os.chmod(temp, 0o600)
    os.replace(temp, dst)
finally:
    if os.path.lexists(temp):
        os.unlink(temp)
print("CELIKOM_OWNER_BASIC_ROOT_COPY_READY")
PY

INTAKE=/root/celikom-windows-bootstrap-intake
if [[ ! -e "$INTAKE" ]]; then
  install -d -o root -g root -m 0700 "$INTAKE"
fi
[[ "$(stat -c '%u:%a' "$INTAKE")" == 0:700 && ! -L "$INTAKE" ]]

fetch_exact() {
  local commit="$1" path="$2" blob="$3" destination="$4" mode="$5"
  local d
  d=$(mktemp /root/celikom-release-file.XXXXXXXX)
  runuser -u celikom-mirror -- git --git-dir="$MIRROR" show "$commit:$path" > "$d"
  [[ "$(git hash-object "$d")" == "$blob" ]] || { rm -f "$d"; echo CELIKOM_RELEASE_SOURCE_PIN_MISMATCH; exit 1; }
  if [[ -e "$destination" || -L "$destination" ]]; then
    [[ -f "$destination" && ! -L "$destination" ]] ||
      { rm -f "$d"; echo CELIKOM_RELEASE_INSTALLED_FILE_UNSAFE; exit 1; }
    local old_hash
    old_hash=$(git hash-object "$destination")
    if [[ "$old_hash" != "$blob" ]]; then
      # First activation was rolled back during public 403 proof. Upgrade ONLY
      # the exact reviewed Windows customer bootstrap stored in private intake.
      # Never overwrite installed root consumers or any unexpected file.
      if [[ ( "$path" == .github/scripts/floki-windows-customer-stable-install.sh &&
              "$old_hash" == 22499058fd0cab1bb17649ac0bf2a474546a7907 &&
              "$destination" == "$INTAKE/floki-windows-customer-stable-install.sh" ) ||
            ( "$path" == .github/scripts/floki-android-customer-stable-install.sh &&
              "$old_hash" == 4680ed1fb55e5b34b2a947af60874562218587d8 &&
              "$destination" == "$INTAKE/floki-android-customer-stable-install.sh" ) ]] &&
         [[ "$(stat -c '%u:%a:%h' "$destination")" == 0:600:1 ]]; then
        local replacement
        replacement=$(mktemp "$INTAKE/.windows-customer-install.XXXXXXXX")
        install -o root -g root -m "$mode" "$d" "$replacement"
        mv -T "$replacement" "$destination"
        echo CELIKOM_VERIFIED_CUSTOMER_INSTALLER_UPDATED_AFTER_ROLLBACK
      else
        rm -f "$d"
        echo CELIKOM_RELEASE_INSTALLED_FILE_CONFLICT
        exit 1
      fi
    fi
  else
    install -o root -g root -m "$mode" "$d" "$destination"
  fi
  rm -f "$d"
}
fetch_exact 77fe32dc291cb875c918162c7550259fb0f71ff4 \
  .github/scripts/floki-windows-signed-root-consumer.py \
  83c93178a07d9811286163d99ae0c23946013a7c \
  "$INTAKE/floki-windows-signed-root-consumer.py" 0600
fetch_exact 1f438a88bca19cbdec95c44dd03b4c3285435046 \
  .github/scripts/floki-windows-owner-download-bootstrap.sh \
  3ba778b967970249a78f8e68e6b1686955cb6f9b \
  "$INTAKE/floki-windows-owner-download-bootstrap.sh" 0600
fetch_exact 37fb9f931b718ec831a7170abc3cb38c78038d76 \
  .github/scripts/floki-windows-root-consumer-install.sh \
  84da5a8cba38b68453071d31de4f7d829322d70a \
  "$INTAKE/floki-windows-root-consumer-install.sh" 0600

# A prior successful Windows activation must survive a later extension failure.
# Re-running this bootstrap never tries to re-import an accepted version.
if [[ "$WIN_CURRENT" == versions/0.24.55 ]]; then
  bash "$INTAKE/floki-windows-root-consumer-install.sh"
  echo CELIKOM_WINDOWS_INITIAL_PROMOTION_RETURNED
else
  systemctl is-active celikom-windows-signed-owner.timer
  echo CELIKOM_WINDOWS_PREVIOUS_PROMOTION_PRESERVED
fi

# Preinstall customer-signed Windows updater with the already accepted 0.24.55
# baseline; newer versions remain gated by explicit owner acceptance.
# Never expose the owner candidate 'stable/current' directly.
fetch_exact f1a9a5420d7b69f1ae4fd44c263e6f6fb09b3a9b \
  .github/scripts/floki-windows-customer-stable-install.sh \
  b1ca1c8aa0075774f7ea3e88a27c2c3e6c15ccac \
  "$INTAKE/floki-windows-customer-stable-install.sh" 0600
if [[ ! -e /etc/systemd/system/celikom-windows-customer-stable.timer ]]; then
  bash "$INTAKE/floki-windows-customer-stable-install.sh"
  echo CELIKOM_CUSTOMER_WINDOWS_SIGNED_ACCEPTED_02455_BASELINE_READY
else
  systemctl is-active celikom-windows-customer-stable.timer
  echo CELIKOM_CUSTOMER_WINDOWS_FEED_ALREADY_ARMED
fi

# Independent extension publisher; no new version-specific Nginx change later.
fetch_exact bed42205c060dbaad858c8c47eca819bfc61d066 \
  .github/scripts/floki-extension-owner-install.sh \
  4a1c3504ee2f13b7ca1dbb71f655fe78574098e2 \
  "$INTAKE/floki-extension-owner-install.sh" 0600
if [[ ! -e /etc/systemd/system/celikom-extension-owner.timer ]]; then
  bash "$INTAKE/floki-extension-owner-install.sh"
  echo CELIKOM_EXTENSION_INITIAL_PROMOTION_RETURNED
else
  systemctl is-active celikom-extension-owner.timer
  echo CELIKOM_EXTENSION_PREVIOUS_PROMOTION_PRESERVED
fi

# Legacy Android is distinct from A1. This only arms its private signed
# owner download and does not touch public OTA or the old Hostinger bridge.
fetch_exact 6f9181a18bcf2ecf654b3c985e017fd413ef69a2 \
  .github/scripts/floki-android-stable-owner-install.sh \
  618fe95d979fb29c108d207af9a2a33574c3bf17 \
  "$INTAKE/floki-android-stable-owner-install.sh" 0600
if [[ ! -e /etc/systemd/system/celikom-android-stable-owner.timer ]]; then
  bash "$INTAKE/floki-android-stable-owner-install.sh"
else
  systemctl is-active celikom-android-stable-owner.timer
fi

# Prepare stable Android public OTA routes. Public manifest remains ABSENT until
# owner acceptance; legacy installed app still uses Hostinger during the bridge.
fetch_exact c0ea40e92c70efb4a4f48ff54b397bb32c4e0288 \
  .github/scripts/floki-android-customer-stable-install.sh \
  4253ebb4dd5985677160a01688f867dd6e8425dc \
  "$INTAKE/floki-android-customer-stable-install.sh" 0600
if [[ ! -e /etc/systemd/system/celikom-android-customer-stable.timer ]]; then
  bash "$INTAKE/floki-android-customer-stable-install.sh"
else
  systemctl is-active celikom-android-customer-stable.timer
fi

[[ "$(readlink /srv/celikom-releases/windows/stable/current)" == versions/0.24.56 ]]
[[ -f /srv/celikom-releases/owner-downloads/CELIKOM-Windows-latest.exe ]]
# No new extension latest is expected until its owner-approved candidate
# exists; the previously accepted 0.4.80 download stays untouched.
if [[ -f /srv/celikom-releases/private/extension/current-owner.json ]]; then
  [[ -f /srv/celikom-releases/owner-downloads/celikom-extension-latest.zip ]]
else
  echo CELIKOM_EXTENSION_RECURRING_PUBLISHER_READY_NO_CURRENT_CANDIDATE
fi
systemctl is-active celikom-windows-signed-owner.timer
systemctl is-active celikom-windows-customer-stable.timer
systemctl is-active celikom-extension-owner.timer
systemctl is-active celikom-android-stable-owner.timer
systemctl is-active celikom-android-customer-stable.timer
# Runner2 must see the same DATA-ONLY signed spools; never grant host SSH.
fetch_exact c3e904bbce4f2de2c1cdd022697d43e7ea88dd82 \
  .github/scripts/floki-runner2-signed-spool-parity.sh \
  a98ecaf1e0841846c687026336686a9a72680bcd \
  "$INTAKE/floki-runner2-signed-spool-parity.sh" 0600
if bash "$INTAKE/floki-runner2-signed-spool-parity.sh"; then
  echo CELIKOM_BOTH_RUNNER_DATA_SPOOL_PARITY_VERIFIED
else
  echo CELIKOM_RUNNER2_SPOOL_PARITY_INCOMPLETE_KEEP_PREVIOUS_RELEASES
  exit 1
fi
# Publish ONLY SHA-256 proofs (no private URLs or identities) so future ChatGPT
# development chats can verify server publication without an operator SSH visit.
fetch_exact 0300994c183d80286830146f3361464a152d5ab1 \
  .github/scripts/floki-release-status-install.sh \
  bf709c0790a04e1af1672f6bc8c31355619febd2 \
  "$INTAKE/floki-release-status-install.sh" 0600
if [[ ! -e /etc/systemd/system/celikom-release-status.timer ]]; then
  bash "$INTAKE/floki-release-status-install.sh"
else
  systemctl is-active celikom-release-status.timer
fi

# Android is not changed; print only its service status, never capability tokens.
systemctl is-active celikom-a1-signed-owner.timer || true
echo CELIKOM_ALL_RELEASE_CHANNELS_ARMED_CUSTOMER_PUBLICATION_OWNER_GATED
