#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
[[ $# == 1 ]]
operation=$1
PHP=/opt/alt/php83/usr/bin/php
[[ -x "$PHP" ]]
owner=$(id -u)
api=/home/u235811320/domains/darkred-camel-588676.hostingersite.com/public_html
cms=/home/u235811320/domains/lemonchiffon-narwhal-791953.hostingersite.com/public_html
state=/home/u235811320/.celikom-php-write-freeze-20261125
marker=CELIKOM_PHP_WRITE_FREEZE_20261125
entries(){
  cat <<'ENTRIES'
api|index.php|7bf3b3efc7c837b53fcdac01a54697d1e99e533ba1a0389552a1faae767d448b
cms|admin/index.php|558f43c262639ececfc852c28b449d4b8262b36c05521a42f68dcee1eac79b61
cms|download/android/index.php|6fba4ef3521cef4df8eae1be2086005845e45f6336561a6a4b7e0d58adfd0d96
cms|index.php|d6753c9e3d8e3e80bd8f533ae8bc0d7e1a8759e32bbf6a931ce92da5487293ac
cms|releases/android/release.php|6fba4ef3521cef4df8eae1be2086005845e45f6336561a6a4b7e0d58adfd0d96
cms|update-center.php|e128c5e038507ffe0e821eacce74339ee09120d31b2ceed6cc59b2f4dd269f97
cms|updates/android/manifest.php|6fba4ef3521cef4df8eae1be2086005845e45f6336561a6a4b7e0d58adfd0d96
ENTRIES
}
resolve_path(){
  case "$1" in
    api) printf '%s/%s\n' "$api" "$2" ;;
    cms) printf '%s/%s\n' "$cms" "$2" ;;
    *) return 64 ;;
  esac
}
require_original_site_layout(){
  [[ -d "$api" && ! -L "$api" && -d "$cms" && ! -L "$cms" ]]
  echo 'b10b9708b243a8530223be402e277d9eba03d6c9b3b176b5b286bb386d374ce4  '"$api/.htaccess" | sha256sum -c --status
  echo '2dff825db9f5927e38181d3f3dfaf3aa8dfc33775d87f53dbe0243c006a08542  '"$cms/.htaccess" | sha256sum -c --status
  [[ "$(find "$api" -maxdepth 3 -type f -name '*.php' | wc -l)" == 2 ]]
  [[ "$(find "$cms" -maxdepth 3 -type f -name '*.php' | wc -l)" == 7 ]]
  for base in "$api" "$cms"; do
    [[ "$(sha256sum "$base/default.php" | cut -d' ' -f1)" == aba5b5856471c610e4dd52c322c7a72a895fc9bf98ac1d027528d0e7de1f7e45 ]]
  done
}
require_original_php(){
  entries | while IFS='|' read -r kind rel digest; do
    p=$(resolve_path "$kind" "$rel")
    [[ -f "$p" && ! -L "$p" && "$(stat -c %u "$p")" == "$owner" ]]
    [[ "$(sha256sum "$p" | cut -d' ' -f1)" == "$digest" ]] || {
      echo "SOURCE_PHP_ORIGINAL_CHECKSUM_CHANGED $kind/$rel"
      exit 1
    }
  done
}
write_patch_program(){
  local folder=$1
  cat > "$folder/patch.php" <<'PATCHPHP'
<?php
declare(strict_types=1);
if ($argc !== 3) { exit(10); }
$original=file_get_contents($argv[1]);
if (!is_string($original)) { exit(11); }
$pattern='~\A<\?php\s+declare\s*\(\s*strict_types\s*=\s*1\s*\)\s*;~';
if (preg_match($pattern, $original, $match) !== 1) { exit(12); }
$guard=<<<'FREEZE_GATE'

/* CELIKOM_PHP_WRITE_FREEZE_20261125 */
if (isset($_SERVER['REQUEST_METHOD']) && !in_array($_SERVER['REQUEST_METHOD'], ['GET','HEAD','OPTIONS'], true)) {
    if (PHP_SAPI === 'cli') {
        fwrite(STDERR, "CELIKOM_PHP_WRITE_FREEZE_CLI_PROOF\n");
        exit(47);
    }
    http_response_code(503);
    header('X-Celikom-PHP-Write-Freeze: active');
    header('Retry-After: 300');
    header('Cache-Control: no-store');
    exit;
}
FREEZE_GATE;
$updated=substr($original,0,strlen($match[0]))."\n".$guard."\n".substr($original,strlen($match[0]));
if (file_put_contents($argv[2],$updated) !== strlen($updated)) { exit(13); }
PATCHPHP
  "$PHP" -l "$folder/patch.php" >/dev/null
}
make_prepared(){
  local root=$1
  entries | while IFS='|' read -r kind rel digest; do
    local_path=$(resolve_path "$kind" "$rel")
    target="$root/ready/$kind/$rel"
    mkdir -p "$(dirname "$target")"
    "$PHP" "$root/patch.php" "$local_path" "$target"
    "$PHP" -l "$target" >/dev/null
    [[ "$(grep -Fc "$marker" "$target")" == 1 ]]
    chmod --reference="$local_path" "$target"
    proof_file="$root/check.txt"
    set +e
    "$PHP" -r '$_SERVER["REQUEST_METHOD"]="POST"; include $argv[1];' "$target" > "$proof_file" 2>&1
    rc=$?
    set -e
    [[ "$rc" == 47 && "$(cat "$proof_file")" == CELIKOM_PHP_WRITE_FREEZE_CLI_PROOF ]] || {
      echo "SOURCE_PHP_WRITE_FENCE_CLI_TEST_FAILED $kind/$rel"
      exit 1
    }
    rm -f "$proof_file"
  done
}
require_backups(){
  [[ -d "$state" && ! -L "$state" && "$(stat -c %u "$state")" == "$owner" ]]
  entries | while IFS='|' read -r kind rel digest; do
    b="$state/backups/$kind/$rel"
    [[ -f "$b" && ! -L "$b" && "$(sha256sum "$b" | cut -d' ' -f1)" == "$digest" ]] || {
      echo "SOURCE_PHP_BACKUP_MISSING_OR_CHANGED $kind/$rel"
      exit 1
    }
  done
}
restore_originals(){
  require_backups
  entries | while IFS='|' read -r kind rel digest; do
    p=$(resolve_path "$kind" "$rel")
    now=$(sha256sum "$p" | cut -d' ' -f1)
    if [[ "$now" == "$digest" ]]; then continue; fi
    [[ -f "$p" && ! -L "$p" ]] && grep -Fq "$marker" "$p" || {
      echo "SOURCE_PHP_UNKNOWN_CHANGE_REFUSE_RESTORE $kind/$rel"
      exit 1
    }
    work="$state/restore/$kind/$rel"
    mkdir -p "$(dirname "$work")"
    cp -p "$state/backups/$kind/$rel" "$work"
    mv -f -- "$work" "$p"
    [[ "$(sha256sum "$p" | cut -d' ' -f1)" == "$digest" ]]
  done
  echo CELIKOM_SOURCE_PHP_ORIGINALS_RESTORED
}
case "$operation" in
preflight)
  require_original_site_layout
  require_original_php
  tmp=$(mktemp -d /home/u235811320/.celikom-php-preflight-XXXXXXXX)
  trap 'rm -rf -- "$tmp"' EXIT
  chmod 700 "$tmp"
  write_patch_program "$tmp"
  make_prepared "$tmp"
  echo CELIKOM_PHP_WRITE_FENCE_PREFLIGHT_SEVEN_ENTRIES_OK
  ;;
freeze)
  require_original_site_layout
  if [[ -d "$state" && ! -L "$state" ]]; then
    # Recover a failed earlier attempt ONLY if all original sites were restored.
    require_original_php
    require_backups
    [[ -z "$(find "$state" -type l -print -quit)" ]]
    rm -rf -- "$state"
    echo CELIKOM_ABANDONED_PHP_PRE_FREEZE_CLEANED
  fi
  [[ ! -e "$state" && ! -L "$state" ]]
  require_original_php
  if command -v crontab >/dev/null; then
    jobs=$(crontab -l 2>/dev/null || true)
    if printf '%s\n' "$jobs" | grep -E 'darkred-camel-588676|lemonchiffon-narwhal-791953|celikom' >/dev/null; then
      echo SOURCE_CELIKOM_CRON_WRITER_REQUIRES_COORDINATION
      exit 1
    fi
  fi
  install -d -m 700 "$state"
  ok=0
  cleanup(){
    rc=$?
    if [[ "$ok" != 1 ]]; then
      restore_originals || echo SOURCE_PHP_FREEZE_RESTORE_REQUIRES_ATTENTION
    fi
    exit "$rc"
  }
  trap cleanup EXIT
  write_patch_program "$state"
  entries | while IFS='|' read -r kind rel digest; do
    p=$(resolve_path "$kind" "$rel")
    b="$state/backups/$kind/$rel"
    mkdir -p "$(dirname "$b")"
    cp -p "$p" "$b"
  done
  require_backups
  make_prepared "$state"
  entries | while IFS='|' read -r kind rel digest; do
    p=$(resolve_path "$kind" "$rel")
    source="$state/ready/$kind/$rel"
    [[ "$(stat -c %d "$p")" == "$(stat -c %d "$state")" ]] || {
      echo SOURCE_PHP_DIFFERENT_DEVICE_REFUSE_NONATOMIC_REPLACE
      exit 1
    }
    mv -f -- "$source" "$p"
    grep -Fq "$marker" "$p"
  done
  ok=1
  echo CELIKOM_PHP_WRITE_FENCE_INSTALLED_ALL_SEVEN_HANDLERS
  ;;
status)
  require_backups
  entries | while IFS='|' read -r kind rel digest; do
    p=$(resolve_path "$kind" "$rel")
    [[ -f "$p" && ! -L "$p" ]] && grep -Fq "$marker" "$p"
    "$PHP" -l "$p" >/dev/null
  done
  echo CELIKOM_PHP_WRITE_FENCE_ACTIVE_ALL_SEVEN_HANDLERS
  ;;
rollback)
  restore_originals
  echo CELIKOM_PHP_WRITE_FENCE_ROLLED_BACK
  ;;
*)
  echo SOURCE_PHP_FREEZE_OPERATION_DENIED
  exit 64
  ;;
esac
