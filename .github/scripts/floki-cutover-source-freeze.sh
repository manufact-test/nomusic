#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# This script runs ONLY on the existing Hostinger SSH account, never on Floki.
# Freeze only unsafe HTTP methods on the two exact CELIKOM sites.
# Preserve GET/HEAD for playback and the historical signed updater.
[[ $# == 1 ]]
command=$1
state=/home/u235811320/.celikom-cutover-freeze-20261125
api=/home/u235811320/domains/darkred-camel-588676.hostingersite.com/public_html/.htaccess
site=/home/u235811320/domains/lemonchiffon-narwhal-791953.hostingersite.com/public_html/.htaccess
expected_api=b10b9708b243a8530223be402e277d9eba03d6c9b3b176b5b286bb386d374ce4
expected_site=2dff825db9f5927e38181d3f3dfaf3aa8dfc33775d87f53dbe0243c006a08542
header='# CELIKOM MIGRATION SAFE WRITE FREEZE 2026-11-25'
restore(){
  local key path before tmp
  for key in api site; do
    if [[ "$key" == api ]]; then path=$api; before=$expected_api; else path=$site; before=$expected_site; fi
    [[ -f "$state/$key.original" && ! -L "$state/$key.original" ]] || continue
    [[ "$(sha256sum "$state/$key.original" | cut -d' ' -f1)" == "$before" ]] || { echo "FREEZE_BACKUP_HASH_CONFLICT $key"; return 1; }
    [[ -f "$path" && ! -L "$path" ]] || { echo "FREEZE_TARGET_CONFLICT $key"; return 1; }
    if [[ "$(sha256sum "$path" | cut -d' ' -f1)" == "$before" ]]; then continue; fi
    [[ "$(head -n 1 "$path")" == "$header" ]] || { echo "FREEZE_OWNER_MARKER_CONFLICT $key"; return 1; }
    tmp=$(mktemp ".github/scripts/floki-cutover-source-freeze.sh.restore.XXXXXXXX")
    cp -p "$state/$key.original" "$tmp"
    mv -f -- "$tmp" "$path"
    [[ "$(sha256sum "$path" | cut -d' ' -f1)" == "$before" ]]
  done
}
case "$command" in
freeze)
  [[ ! -e "$state" && ! -L "$state" ]]
  for key in api site; do
    if [[ "$key" == api ]]; then path=$api; before=$expected_api; else path=$site; before=$expected_site; fi
    [[ -f "$path" && ! -L "$path" && "$(stat -c %u "$path")" == "$(id -u)" ]]
    [[ "$(sha256sum "$path" | cut -d' ' -f1)" == "$before" ]] || { echo "SOURCE_HTACCESS_HAS_CHANGED $key"; exit 1; }
  done
  # No unknown background CELIKOM job may keep writing while HTTP writers freeze.
  if command -v crontab >/dev/null 2>&1; then
    jobs=$(crontab -l 2>/dev/null || true)
    if printf '%s\n' "$jobs" | grep -E 'darkred-camel-588676|lemonchiffon-narwhal-791953|celikom' >/dev/null; then
      echo SOURCE_CELIKOM_CRON_WRITER_REQUIRES_COORDINATION
      exit 1
    fi
  fi
  echo SOURCE_NO_RELATED_CRON_WRITERS
  install -d -m 700 "$state"
  ok=0
  cleanup(){ rc=$?; if [[ "$ok" != 1 ]]; then restore || true; fi; exit "$rc"; }
  trap cleanup EXIT
  for key in api site; do
    if [[ "$key" == api ]]; then path=$api; else path=$site; fi
    cp -p "$path" "$state/$key.original"
    tmp=$(mktemp ".github/scripts/floki-cutover-source-freeze.sh.freeze.XXXXXXXX")
    {
      printf '%s\n' "$header"
      cat <<'HTACCESS'
<IfModule mod_rewrite.c>
RewriteEngine On
RewriteCond %{REQUEST_METHOD} !^(GET|HEAD|OPTIONS)$ [NC]
RewriteRule ^ - [R=503,L]
</IfModule>
HTACCESS
      cat "$state/$key.original"
    } > "$tmp"
    chmod --reference="$path" "$tmp"
    mv -f -- "$tmp" "$path"
    [[ "$(head -n 1 "$path")" == "$header" ]]
  done
  printf '%s\n' SOURCE_CELIKOM_WRITE_FREEZE_FILES_INSTALLED
  ok=1
  ;;
status)
  [[ -d "$state" ]]
  for key in api site; do
    if [[ "$key" == api ]]; then path=$api; else path=$site; fi
    [[ "$(head -n 1 "$path")" == "$header" ]]
  done
  echo SOURCE_CELIKOM_WRITE_FREEZE_ACTIVE
  ;;
rollback)
  [[ -d "$state" && ! -L "$state" ]]
  restore
  [[ "$(sha256sum "$api" | cut -d' ' -f1)" == "$expected_api" ]]
  [[ "$(sha256sum "$site" | cut -d' ' -f1)" == "$expected_site" ]]
  echo SOURCE_CELIKOM_WRITE_FREEZE_ROLLED_BACK
  ;;
*) echo SOURCE_FREEZE_OPERATION_DENIED; exit 64 ;;
esac
