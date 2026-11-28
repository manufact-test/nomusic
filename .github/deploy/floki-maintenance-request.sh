#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
[[ "$(id -u)" == 0 ]] || { echo W196_ROOT_REQUIRED; exit 1; }

echo W196_READONLY_PUBLIC_OTA_ACCESS_LOG_AUDIT
mapfile -t logs < <(
  find /var/log/nginx -maxdepth 2 -type f \( -name '*access*.log*' -o -name 'access.log*' \) -print 2>/dev/null | sort
)
if ((${#logs[@]}==0)); then
  echo W196_NO_NGINX_ACCESS_LOG_FILES_FOUND
  exit 0
fi
found=0
for log in "${logs[@]}"; do
  [[ -f "$log" ]] || continue
  case "$log" in
    *.gz) reader=(gzip -cd -- "$log");;
    *) reader=(cat -- "$log");;
  esac
  output=$("${reader[@]}" 2>/dev/null | awk '
    {
      path=$7
      sub(/\?.*/, "", path)
      if (path ~ /^\/CELIKOM\/Windows\/Updates\/stable\/(latest\.json(\.sig)?|0\.24\.62\/(manifest\.json(\.sig)?|CELIKOM-Windows-0\.24\.62\.exe)|0\.24\.63\/(manifest\.json(\.sig)?|CELIKOM-Windows-0\.24\.63\.exe))$/) {
        timestamp=$4
        gsub(/^\[/, "", timestamp)
        print timestamp, path, "status=" $9, "bytes=" $10
      }
    }
  ' | tail -n 80)
  if [[ -n "$output" ]]; then
    found=1
    printf 'W196_LOG %s\n%s\n' "$log" "$output"
  fi
done
if [[ "$found" == 0 ]]; then
  echo W196_NO_MATCHING_PUBLIC_OTA_REQUESTS_IN_AVAILABLE_ACCESS_LOGS
fi
echo W196_AUDIT_COMPLETE_NO_CLIENT_IPS_OR_HEADERS_EXPORTED
