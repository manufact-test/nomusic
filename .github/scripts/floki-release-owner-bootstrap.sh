#!/bin/bash
# One-time trusted owner bootstrap for Windows and extension publication.
# Android A1 is already live and MUST NOT be reconfigured by this installer.
# Never run this on a GitHub Actions self-hosted CI runner.
set -Eeuo pipefail
umask 077
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
  [[ -f /etc/systemd/system/celikom-extension-owner.service &&
     -f /srv/celikom-releases/private/extension/current-owner.json ]]
else
  [[ ! -e /etc/systemd/system/celikom-extension-owner.service ]]
fi
[[ "$(sha256sum /root/celikom-secrets/windows-stable-public.der | cut -d' ' -f1)" == 46b36bb222154316f2229c35cf65e6c953e0b6524dfb0aad8de05949dc143a95 ]]
nginx -t
for cmd in git python3 node systemctl; do command -v "$cmd" >/dev/null; done
echo CELIKOM_RELEASE_BOOTSTRAP_PRECHECK_OK

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
    [[ ! -L "$destination" && "$(git hash-object "$destination")" == "$blob" ]] ||
      { rm -f "$d"; echo CELIKOM_RELEASE_INSTALLED_FILE_CONFLICT; exit 1; }
  else
    install -o root -g root -m "$mode" "$d" "$destination"
  fi
  rm -f "$d"
}
fetch_exact 1f438a88bca19cbdec95c44dd03b4c3285435046 \
  .github/scripts/floki-windows-signed-root-consumer.py \
  9ff780d3719ff6b3f9a00d21f8164bcae9e37140 \
  "$INTAKE/floki-windows-signed-root-consumer.py" 0600
fetch_exact 1f438a88bca19cbdec95c44dd03b4c3285435046 \
  .github/scripts/floki-windows-owner-download-bootstrap.sh \
  3ba778b967970249a78f8e68e6b1686955cb6f9b \
  "$INTAKE/floki-windows-owner-download-bootstrap.sh" 0600
fetch_exact 1f438a88bca19cbdec95c44dd03b4c3285435046 \
  .github/scripts/floki-windows-root-consumer-install.sh \
  ab1750213b98ae8c3ff4e4c901d1edf7c33623bf \
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

# Independent extension publisher; no new version-specific Nginx change later.
fetch_exact 0ab4f261dcc744d150262339a8b2fede34f8c68b \
  .github/scripts/floki-extension-owner-install.sh \
  59f79307212195715695c52d2fc1a2eed3522b15 \
  "$INTAKE/floki-extension-owner-install.sh" 0600
if [[ ! -e /etc/systemd/system/celikom-extension-owner.timer ]]; then
  bash "$INTAKE/floki-extension-owner-install.sh"
  echo CELIKOM_EXTENSION_INITIAL_PROMOTION_RETURNED
else
  systemctl is-active celikom-extension-owner.timer
  echo CELIKOM_EXTENSION_PREVIOUS_PROMOTION_PRESERVED
fi

[[ "$(readlink /srv/celikom-releases/windows/stable/current)" == versions/0.24.56 ]]
[[ -f /srv/celikom-releases/owner-downloads/CELIKOM-Windows-latest.exe ]]
[[ -f /srv/celikom-releases/owner-downloads/celikom-extension-latest.zip ]]
systemctl is-active celikom-windows-signed-owner.timer
systemctl is-active celikom-extension-owner.timer
# Runner2 must see the same DATA-ONLY signed spools; never grant host SSH.
fetch_exact c3e904bbce4f2de2c1cdd022697d43e7ea88dd82 \
  .github/scripts/floki-runner2-signed-spool-parity.sh \
  a98ecaf1e0841846c687026336686a9a72680bcd \
  "$INTAKE/floki-runner2-signed-spool-parity.sh" 0600
if bash "$INTAKE/floki-runner2-signed-spool-parity.sh"; then
  echo CELIKOM_BOTH_RUNNER_DATA_SPOOL_PARITY_VERIFIED
else
  echo CELIKOM_RUNNER2_SPOOL_PARITY_NEEDS_SAFE_FOLLOWUP
fi
# Android is not changed; print only its service status, never capability tokens.
systemctl is-active celikom-a1-signed-owner.timer || true
echo CELIKOM_WINDOWS_AND_EXTENSION_PERMANENT_OWNER_DOWNLOADS_READY
