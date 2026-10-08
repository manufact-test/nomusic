#!/usr/bin/env bash
set -euo pipefail

release_id="${1:?release ID required}"
[[ "$release_id" =~ ^[0-9]+\.[0-9]+\.[0-9]+-[a-f0-9]{40}$ ]] || exit 1
site='/home/u235811320/domains/darkred-camel-588676.hostingersite.com'
origin='https://darkred-camel-588676.hostingersite.com'
php_bin='/opt/alt/php83/usr/bin/php'
app="$site/celikom"
public="$site/public_html"
incoming="$app/incoming/$release_id"
release="$app/releases/$release_id"
backup="$app/backups/$release_id-$(date -u +%Y%m%dT%H%M%S)-$$"
probe_name="celikom-runtime-$release_id.php"
[[ -d "$public" && ! -L "$app" && ! -L "$app/shared" ]] || exit 1
[[ ! -L "$public/index.php" && ! -L "$public/.htaccess" ]] || exit 1
[[ ! -e "$app/current" || -L "$app/current" ]] || exit 1
"$php_bin" -r 'exit(PHP_VERSION_ID >= 80300 && extension_loaded("pdo_mysql") && extension_loaded("fileinfo") ? 0 : 1);'
umask 077
mkdir -p "$app/releases" "$app/backups" "$backup"
old_current=''
[[ ! -L "$app/current" ]] || old_current="$(readlink "$app/current")"
for name in index.php .htaccess; do
  if [[ -f "$public/$name" ]]; then cp -p "$public/$name" "$backup/$name"; fi
done
switched=0
rollback() {
  result=$?
  trap - EXIT
  rm -f "$public/$probe_name"
  if [[ "$result" != 0 && "$switched" == 1 ]]; then
    if [[ -n "$old_current" ]]; then
      ln -s "$old_current" "$app/rollback-$$"
      mv -Tf "$app/rollback-$$" "$app/current"
    else
      rm -f "$app/current"
    fi
    for name in index.php .htaccess; do
      if [[ -f "$backup/$name" ]]; then cp -p "$backup/$name" "$public/$name"; else rm -f "$public/$name"; fi
    done
    echo 'HTTPS verification failed; the previous public entry and release were restored.' >&2
  fi
  exit "$result"
}
trap rollback EXIT

cd "$incoming"
sha256sum --check package.zip.sha256
if [[ ! -d "$release" ]]; then
  stage="$app/releases/partial-$release_id-$$"
  mkdir "$stage"
  unzip -q package.zip -d "$stage"
  [[ -f "$stage/public/index.php" && -f "$stage/deploy/initialize-private-test.php" && ! -e "$stage/.env" ]]
  mv "$stage" "$release"
fi
# Credentials arrive on STDIN, never in argv, Git, ZIPs or logs.
"$php_bin" "$release/deploy/initialize-private-test.php"
"$php_bin" "$release/bin/migrate.php"
"$php_bin" "$release/bin/migrate.php"
ln -s "$release" "$app/current-next-$$"
mv -Tf "$app/current-next-$$" "$app/current"
switched=1
cp "$release/deploy/public-entry.php" "$public/index.php"
{
  printf '%s\n' '<FilesMatch "\.(php|phtml)$">' 'SetHandler application/x-lsphp83' '</FilesMatch>'
  printf '%s\n' 'RewriteEngine On' 'RewriteCond %{HTTPS} !=on' "RewriteRule ^ $origin%{REQUEST_URI} [R=302,L,NE]"
  cat "$release/public/.htaccess"
} > "$public/.htaccess"
chmod 0644 "$public/index.php" "$public/.htaccess"
cat > "$public/$probe_name" <<'PHP_PROBE'
<?php
declare(strict_types=1);
ini_set('display_errors', '0');
header('Content-Type: application/json');
header('Cache-Control: no-store');
try {
    require dirname(__DIR__) . '/celikom/current/bootstrap.php';
    $config = require dirname(__DIR__) . '/celikom/current/config/app.php';
    Celikom\Database\Connection::open($config)->query('SELECT 1')->fetchColumn();
    echo json_encode(['php_version' => PHP_VERSION, 'php_version_id' => PHP_VERSION_ID, 'database' => true, 'pdo_mysql' => extension_loaded('pdo_mysql'), 'fileinfo' => extension_loaded('fileinfo')]);
} catch (Throwable) { http_response_code(503); echo '{"database":false}'; }
PHP_PROBE
chmod 0644 "$public/$probe_name"
curl --fail --silent --show-error --retry 2 --connect-timeout 10 --max-time 25 "$origin/$probe_name" > "$backup/runtime.json"
"$php_bin" -r '$v=json_decode(file_get_contents($argv[1]),true,8,JSON_THROW_ON_ERROR); if (($v["php_version_id"]??0)<80300 || !($v["database"]??false) || !($v["pdo_mysql"]??false) || !($v["fileinfo"]??false)) { exit(1); } echo "HTTPS runtime: PHP ", $v["php_version"], "; MySQL and extensions verified.", PHP_EOL;' "$backup/runtime.json"
rm -f "$public/$probe_name"
curl --fail --silent --show-error --retry 2 --connect-timeout 10 --max-time 25 "$origin/api/v1/health" > "$backup/health.json"
curl --fail --silent --show-error --retry 2 --connect-timeout 10 --max-time 25 "$origin/api/v1/config" > "$backup/config.json"
"$php_bin" -r '$h=json_decode(file_get_contents($argv[1]),true,8,JSON_THROW_ON_ERROR); $c=json_decode(file_get_contents($argv[2]),true,8,JSON_THROW_ON_ERROR); if (($h["service"]??null)!=="celikom-api" || ($h["version"]??null)!==explode("-",$argv[3])[0] || !isset($c["features"])) { exit(1); } echo "API health/config verified over HTTPS.", PHP_EOL;' "$backup/health.json" "$backup/config.json" "$release_id"
echo "Active private-test release: $release_id"
