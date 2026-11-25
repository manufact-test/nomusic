#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Final post-cutover verification: no live DB writes or config edits.
backup=/srv/celikom/migration/backups/celikom-final-delta-20261125-v2.tar.gpg
[[ -f "$backup" && ! -L "$backup" && "$(stat -c '%u:%a:%s' "$backup")" == 0:600:11668572 ]]
printf '%s  %s\n' 4fa123474c973539fd3a03b424b6f36c89c4fa35aad16a31a104d88fa10fef0d "$backup" | sha256sum -c --status
echo FINAL_LOCAL_ENCRYPTED_CIPHERTEXT_SHA256_MATCH

runuser -u www-data -- php -r '
require "/srv/celikom/app/staging-20261122/bootstrap.php";
$c=require "/srv/celikom/app/staging-20261122/config/app.php";
$p=Celikom\Database\Connection::open($c);
assert($p->query("SELECT DATABASE()")->fetchColumn()==="celikom_cutover_20261124");
$t=(int)$p->query("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_type=\"BASE TABLE\"")->fetchColumn();
if($t!==44)exit(2);
echo "FINAL_LIVE_API_DB_TABLES=", $t,PHP_EOL;
'
runuser -u celikom-site -- php -r '
require "/srv/celikom-site/celikom-private/app/bootstrap.php";
$p=Celikom\Website\Database::connect(Celikom\Website\CmsConfig::databaseSettings());
if($p->query("SELECT DATABASE()")->fetchColumn()!=="celikom_website_cutover_20261124")exit(2);
$t=(int)$p->query("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_type=\"BASE TABLE\"")->fetchColumn();
if($t!==11)exit(2);
echo "FINAL_LIVE_CMS_DB_TABLES=",$t,PHP_EOL;
'
nginx -t
systemctl is-active --quiet nginx
systemctl is-active --quiet php8.3-fpm
systemctl is-active --quiet celikom-mirror-sync.timer

tmp=$(mktemp -d)
trap 'rm -rf -- "$tmp"' EXIT
curl -fsS --max-time 15 https://api.celikom.com/api/v1/config > "$tmp/config"
python3 - "$tmp/config" <<'PY'
import json,sys
v=json.load(open(sys.argv[1]))
f=v["features"]
assert v["api_version"]==1 and v["maintenance"] is False
assert all(f[k] for k in ("replacements","auth","entitlement","rewards"))
assert not any(f[k] for k in ("analytics","billing_views","referrals"))
required=tuple(map(int,v["minimum_extension_version"].split(".")))
current=(0,4,73)
assert current>=required,(required,current)
assert v["upload_enabled"] is True
print("FINAL_API_EXTENSION_0473_COMPATIBLE_WITH_ENABLED_AUTH_AND_REPLACEMENTS")
PY
for path in /api/v1/health /api/v1/config; do
 [[ "$(curl -sS --max-time 10 -o /dev/null -w '%{http_code}' "https://api.celikom.com$path")" == 200 ]]
done
for path in /api/v1/auth/me /api/v1/entitlement; do
 [[ "$(curl -sS --max-time 10 -o /dev/null -w '%{http_code}' "https://api.celikom.com$path")" == 401 ]]
done
[[ "$(curl -sS --max-time 10 -X POST -H 'Content-Type: application/json' -d '{}' -o "$tmp/activate" -w '%{http_code}' https://api.celikom.com/api/v1/auth/activate)" == 401 ]]
python3 - "$tmp/activate" <<'PY'
import json,sys
assert isinstance(json.load(open(sys.argv[1]))["error"],str)
print("FINAL_API_AUTH_ACTIVATE_POST_REAL_JSON_ROUTE_READY")
PY
for path in / /admin/ /downloads/windows/CELIKOM-Windows-0.24.55.exe /downloads/extension/celikom-extension-0.4.73.zip /updates/android/stable.json; do
 [[ "$(curl -sS --max-time 10 -o /dev/null -w '%{http_code}' "https://celikom.com$path")" == 401 ]]
done
echo FINAL_OWNER_SITE_AND_DISTRIBUTION_BASIC_AUTH_INTACT

[[ -f /srv/celikom-releases/private/extension/celikom-extension-0.4.73.zip ]]
printf '%s  %s\n' 968e34ef72927ce5be5007d1ed210a9b6910b45d4fa423b67fdc3db16a75becb /srv/celikom-releases/private/extension/celikom-extension-0.4.73.zip | sha256sum -c --status
echo FINAL_FLOKI_EXTENSION_NEW_ORIGIN_PACKAGE_IMMUTABLE

echo CELIKOM_POSTCUTOVER_FINAL_READONLY_SERVER_ACCEPTANCE_OK
