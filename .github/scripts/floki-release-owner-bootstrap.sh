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
  [[ -f /etc/systemd/system/celikom-extension-owner.service ]]
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
fetch_exact 4e69e2c5acd63fd6e88d3b814eb4abd5aa8beeb4 \
  .github/scripts/floki-windows-signed-root-consumer.py \
  c1cb5505e86d09f6dac0517ac710ad558406df74 \
  "$INTAKE/floki-windows-signed-root-consumer.py" 0600
fetch_exact 1f438a88bca19cbdec95c44dd03b4c3285435046 \
  .github/scripts/floki-windows-owner-download-bootstrap.sh \
  3ba778b967970249a78f8e68e6b1686955cb6f9b \
  "$INTAKE/floki-windows-owner-download-bootstrap.sh" 0600
fetch_exact d4f397ddb3850ea4cf55ec9c01f7bd7644ce3a2d \
  .github/scripts/floki-windows-root-consumer-install.sh \
  833688233cb9bdb28201e75e70e2a49269a1dc43 \
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

# Preinstall the separate customer-signed Windows update channel. It stays
# EMPTY until a checked owner-acceptance record is approved on main.
# Never expose the owner candidate 'stable/current' directly.
fetch_exact 4e81a271472c5ee915d72794e9c114f721bdfd43 \
  .github/scripts/floki-windows-customer-stable-install.sh \
  4088d0e4631cb2ae2c1a492c895f07a17fd2c1dc \
  "$INTAKE/floki-windows-customer-stable-install.sh" 0600
if [[ ! -e /etc/systemd/system/celikom-windows-customer-stable.timer ]]; then
  bash "$INTAKE/floki-windows-customer-stable-install.sh"
  echo CELIKOM_CUSTOMER_WINDOWS_FEED_READY_AWAITING_OWNER_ACCEPTANCE
else
  systemctl is-active celikom-windows-customer-stable.timer
  echo CELIKOM_CUSTOMER_WINDOWS_FEED_ALREADY_ARMED
fi

# Independent extension publisher; no new version-specific Nginx change later.
fetch_exact c78fa1a638d43a12e259e35789700957a58b7b45 \
  .github/scripts/floki-extension-owner-install.sh \
  e0f7cd875648e305f00e95b80e52d3cfbe1dd55d \
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
fetch_exact 8cfda5b4826633800fcd80099e661065c65b330b \
  .github/scripts/floki-android-stable-owner-install.sh \
  f6e68975f52a802d751003fee1c9a2f23a7d9ae1 \
  "$INTAKE/floki-android-stable-owner-install.sh" 0600
if [[ ! -e /etc/systemd/system/celikom-android-stable-owner.timer ]]; then
  bash "$INTAKE/floki-android-stable-owner-install.sh"
else
  systemctl is-active celikom-android-stable-owner.timer
fi

# Prepare stable Android public OTA routes. Public manifest remains ABSENT until
# owner acceptance; legacy installed app still uses Hostinger during the bridge.
fetch_exact 351e855cf43b642450c888ff5679030c6d8ce54a \
  .github/scripts/floki-android-customer-stable-install.sh \
  16d4d3d411e6395e2c42de82ed071dd78ec3a044 \
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
fetch_exact 4d569e5cc13935a9b6e0ec9baaa4b95769e6c68a \
  .github/scripts/floki-release-status-install.sh \
  a22c4102a9cf1e4af8579381592d1d2ec52fe5e9 \
  "$INTAKE/floki-release-status-install.sh" 0600
if [[ ! -e /etc/systemd/system/celikom-release-status.timer ]]; then
  bash "$INTAKE/floki-release-status-install.sh"
else
  systemctl is-active celikom-release-status.timer
fi

# Android is not changed; print only its service status, never capability tokens.
systemctl is-active celikom-a1-signed-owner.timer || true
echo CELIKOM_ALL_RELEASE_CHANNELS_ARMED_CUSTOMER_PUBLICATION_OWNER_GATED
