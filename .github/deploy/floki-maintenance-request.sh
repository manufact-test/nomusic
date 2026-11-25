#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# READ-ONLY, NO live edits, no tokens, no credentials printed.
python3 - <<'PY'
import pathlib,zipfile,json,hashlib,os
paths={
  "extension_zip":"/srv/celikom-releases/private/extension/celikom-extension-0.4.73.zip",
  "live_api_env":"/srv/celikom/app/staging-20261122/.env",
  "live_cms_config":"/srv/celikom-site/celikom-private/staging-config.php",
  "api_front":"/etc/nginx/sites-available/celikom-api-https",
  "api_backend":"/etc/nginx/sites-available/celikom-api-staging",
  "site_front":"/etc/nginx/sites-available/celikom-site-https",
  "site_backend":"/etc/nginx/sites-available/celikom-website-preview",
  "basic_credentials":"/etc/nginx/celikom-site.htpasswd",
  "android_private":"/srv/celikom-releases/private/android-v95/CELIKOM-Android-0.3.94-SIGNED.apk"
}
for k,s in paths.items():
 p=pathlib.Path(s)
 if not p.is_file() or p.is_symlink(): print("MISSING_BACKUP_INPUT",k);continue
 st=p.stat()
 print("INPUT_METADATA",k,"uid",st.st_uid,"gid",st.st_gid,"mode",oct(st.st_mode & 0o777),"size",st.st_size)
z=pathlib.Path(paths["extension_zip"])
if z.is_file():
 with zipfile.ZipFile(z) as a:
  assert a.testzip() is None
  j=json.loads(a.read("api/config.json"))
  m=json.loads(a.read("manifest.json"))
  print("EXACT_STAGED_EXTENSION_ORIGIN",j.get("baseUrl"))
  print("EXACT_STAGED_EXTENSION_VERSION",m.get("version"))
  print("EXACT_STAGED_EXTENSION_HOST_PERMISSIONS",sorted(m.get("host_permissions",[])))
  print("EXACT_STAGED_EXTENSION_SHA256",hashlib.file_digest(z.open("rb"),"sha256").hexdigest())
for name in ["celikom-final-delta-20261125.tar.gpg"]:
 p=pathlib.Path("/srv/celikom/migration/backups")/name
 print("FINAL_DELTA_CIPHERTEXT_EXISTS",p.exists())
PY
for url in \
  https://api.celikom.com/api/v1/health \
  https://api.celikom.com/api/v1/config \
  https://api.celikom.com/api/v1/auth/me \
  https://api.celikom.com/api/v1/entitlement \
  https://api.celikom.com/api/v1/auth/activate; do
 code=$(curl -sS --max-time 15 -o /dev/null -w '%{http_code}' "$url")
 echo "LIVE_HTTP_NOAUTH" "${url#https://api.celikom.com}" "$code"
done
echo CELIKOM_READONLY_EXTENSION_AND_BACKUP_ROOT_CAUSE_INVENTORY_OK
