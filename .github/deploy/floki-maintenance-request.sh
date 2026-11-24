#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
echo '=== Restricted deploy gateway and sudo policy ==='
sed -n '1,120p' /usr/local/sbin/celikom-deploy-gateway
cat /etc/sudoers.d/celikom-deploy
echo '=== Android baseline permissions ==='
stat -c '%n %F mode=%a owner=%U:%G size=%s' /srv/celikom-releases/private/android-build-inputs /srv/celikom-releases/private/android-build-inputs/CELIKOM-0.3.22-install.apk
echo '=== Windows import and local feed staging ==='
for p in /root/celikom-release-import /root/celikom-release-import/windows-02455 /root/celikom-release-tools /root/celikom-secrets/windows-stable-public.der /srv/celikom-releases/windows/stable /srv/celikom-releases/windows/stable/current /srv/celikom/releases/private/extension/celikom-extension-0.4.73.zip; do
  if [[ -e "$p" || -L "$p" ]]; then stat -c '%n %F mode=%a owner=%U:%G size=%s' "$p"; [[ -L "$p" ]] && readlink "$p"; else echo "MISSING $p"; fi
done
echo '=== Verified extension spool ==='
p=/srv/celikom/ci-runner/runner/celikom-build-spool/61d17d9eb97f3db5c58c906e30da6c19ee737090-45446268377-1
if [[ -d "$p" ]]; then find "$p" -maxdepth 1 -type f -printf '%f %s bytes\n' | sort; else echo MISSING; fi
echo CELIKOM_RELEASE_AND_ANDROID_STAGING_INVENTORY_OK
