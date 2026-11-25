#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Read-only post-cutover inventory: update feeds, legacy bridge, recovery and mirror.
app=/srv/celikom/app/staging-20261122
site=/srv/celikom-site/celikom-private
test -f /root/celikom-cutover-prepared/android-updates.conf
test -f /root/celikom-cutover-prepared/windows-stable-locations.conf
readlink -f /etc/nginx/sites-enabled/celikom-api-https
readlink -f /etc/nginx/sites-enabled/celikom-site-https
nginx -t
runuser -u www-data -- php -r 'require $argv[1]."/bootstrap.php";$c=require $argv[1]."/config/app.php";$p=Celikom\Database\Connection::open($c);$db=$p->query("SELECT DATABASE()")->fetchColumn();if($db!=="celikom_cutover_20261124")exit(2);echo "ACTIVE_API_DB_NEW=1",PHP_EOL;foreach(["tracks","audio_assets","track_replacements","users"] as $t){echo "LIVE_API_COUNT ",$t," ",$p->query("SELECT COUNT(*) FROM ".$t)->fetchColumn(),PHP_EOL;}' "$app"
runuser -u celikom-site -- php -r 'require $argv[1]."/app/bootstrap.php";$p=Celikom\Website\Database::connect(Celikom\Website\CmsConfig::databaseSettings());$db=$p->query("SELECT DATABASE()")->fetchColumn();if($db!=="celikom_website_cutover_20261124")exit(2);echo "ACTIVE_CMS_DB_NEW=1",PHP_EOL;' "$site"
python3 - <<'PY'
import pathlib,re
base=pathlib.Path('/root/celikom-cutover-prepared')
for name in ('android-updates.conf','windows-stable-locations.conf'):
 s=(base/name).read_text()
 loc=[x.strip() for x in re.findall(r'(?m)^\s*location\s+([^\n{]+)\{',s)]
 print('CANDIDATE_NGINX_EXACT_ROUTES',name,loc)
pub=pathlib.Path('/srv/celikom-releases/public/android')
print('ANDROID_PUBLIC_STAGE_EXISTS',pub.is_dir())
if pub.is_dir():
 files=list(pub.rglob('*'))
 print('ANDROID_PUBLIC_STAGE_OBJECT_COUNT',len(files))
 for p in files:
  if p.is_file():
   print('ANDROID_PUBLIC_STAGE_FILE',str(p.relative_to(pub)),p.stat().st_size)
legacy=pathlib.Path('/srv/celikom-releases/private/android-build-inputs')
print('ANDROID_BUILD_INPUT_PRIVATE_READY',legacy.is_dir())
win=pathlib.Path('/srv/celikom-releases/windows/stable/current')
print('WINDOWS_STABLE_CURRENT_RESOLVES',str(win.resolve()) if win.exists() else 'ABSENT')
PY
for unit in nginx php8.3-fpm celikom-ci-runner.service celikom-mirror-sync.timer; do
 printf 'SERVICE %s ' "$unit"
 systemctl is-active "$unit"
done
systemctl is-enabled celikom-mirror-sync.timer
journalctl -u celikom-mirror-sync.service --since '2026-11-25 10:30:00 UTC' --no-pager -o cat | grep -E 'CELIKOM_MIRROR_SYNC_OK|VERIFIED_REFS=' | tail -n 6 || true
for path in / /admin/ /downloads/windows/CELIKOM-Windows-0.24.55.exe /downloads/extension/celikom-extension-0.4.73.zip /updates/android/stable.json; do
 printf 'CLOSED_SITE_ROUTE %s %s\n' "$path" "$(curl -sS --max-time 10 -o /dev/null -w '%{http_code}' "https://celikom.com$path")"
done
echo CELIKOM_POST_CUTOVER_INFRA_AND_UPDATER_READONLY_INVENTORY_OK
