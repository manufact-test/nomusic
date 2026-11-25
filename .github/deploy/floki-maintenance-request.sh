#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Read-only pre-activation contract audit; never emit credentials or env contents.
python3 - <<'PY'
import pathlib,re
d=pathlib.Path("/root/celikom-cutover-prepared")
names=["api-https.conf","api-staging.conf","site-https.conf","website-preview.conf","api.env","website-staging-config.php"]
for n in names:
 p=d/n
 assert p.is_file() and not p.is_symlink() and p.stat().st_uid==0,n
 s=p.read_text()
 if n.endswith(".conf"):
  print("CONFIG_CANDIDATE",n,"bytes",p.stat().st_size)
  print("  server",re.findall(r"server_name\s+([^;]+);",s))
  print("  listen",re.findall(r"\blisten\s+([^;]+);",s))
  print("  routes",sorted(set(re.findall(r"\blocation\s+([^\{\n]+)\{",s))))
 elif n=="api.env":
  m=re.findall(r"(?m)^\s*DB_NAME\s*=\s*([A-Za-z0-9_]+)\s*$",s)
  print("API_PREPARED_DB",m)
  assert m==["celikom_cutover_20261124"]
  flags={k:int(v) for k,v in re.findall(r"(?m)^([A-Z][A-Z0-9_]+)=(0|1)\s*$",s)}
  for k in ["FEATURE_ADMIN","FEATURE_REPLACEMENTS","FEATURE_USER_AUTH","FEATURE_USER_ENTITLEMENT","FEATURE_OWNER_UPLOADS","FEATURE_UPLOADS","FEATURE_REWARD_ELIGIBILITY"]:
   assert flags.get(k)==1,k
  for k in ["CELIKOM_APP_DEBUG","FEATURE_ANALYTICS","FEATURE_BILLING_VIEWS","FEATURE_PAID_ENTITLEMENT","FEATURE_REFERRAL_ATTRIBUTION","FEATURE_OWNER_REPORTS"]:
   assert flags.get(k)==0,k
  print("API_PREPARED_FEATURE_FLAGS_VALID")
 else:
  assert "celikom_website_cutover_20261124" in s,n
  print("CMS_PREPARED_CONFIG_CONTAINS_CANDIDATE")
for name in ["celikom-api-https","celikom-api-staging","celikom-site-https","celikom-website-preview"]:
 p=pathlib.Path("/etc/nginx/sites-enabled")/name
 dst=p.resolve()
 assert str(dst).startswith("/etc/nginx/sites-available/") and dst.is_file() and dst.stat().st_uid==0,name
 print("ACTIVE_VHOST",name,dst)
PY
nginx -t
runuser -u www-data -- php -r 'require "/srv/celikom/app/staging-20261122/bootstrap.php";$c=require "/srv/celikom/app/staging-20261122/config/app.php";$p=Celikom\Database\Connection::open($c);echo "CURRENT_API_DB=",$p->query("SELECT DATABASE()")->fetchColumn(),PHP_EOL;'
runuser -u www-data -- env DB_NAME=celikom_cutover_20261124 php -r 'require "/srv/celikom/app/staging-20261122/bootstrap.php";$c=require "/srv/celikom/app/staging-20261122/config/app.php";$p=Celikom\Database\Connection::open($c);echo "PRIVATE_API_DB=",$p->query("SELECT DATABASE()")->fetchColumn(),PHP_EOL;'
echo CELIKOM_PREACTIVATION_CONFIG_READONLY_OK
