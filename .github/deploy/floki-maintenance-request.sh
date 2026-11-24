#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
root=/srv/celikom-releases/windows/stable
echo '=== Feed path permissions (read-only) ==='
namei -l "$root/current/manifest.json"
namei -l "$root/current/CELIKOM-Windows-0.24.55.exe"
if runuser -u www-data -- test -r "$root/current/manifest.json"; then echo NGINX_MANIFEST_READABLE; else echo NGINX_MANIFEST_NOT_READABLE; fi
if runuser -u www-data -- test -r "$root/current/CELIKOM-Windows-0.24.55.exe"; then echo NGINX_INSTALLER_READABLE; else echo NGINX_INSTALLER_NOT_READABLE; fi
echo '=== Probe errors (only exact local route) ==='
if test -f /var/log/nginx/error.log; then
  grep '18083' /var/log/nginx/error.log | grep 'Windows/Updates/stable/latest.json' | tail -n 5 || true
fi
echo '=== Cleanup ==='
test ! -e /etc/nginx/conf.d/celikom-windows-feed-probe.conf
test ! -e /root/celikom-cutover-prepared/windows-stable-locations.conf
nginx -t
echo WINDOWS_FEED_PROBE_DIAGNOSTICS_OK
