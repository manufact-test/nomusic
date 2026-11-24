#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Prepare configuration only. Do not switch live traffic in this operation.
dir=/root/celikom-cutover-prepared
install -d -m 700 "$dir"
python3 - <<'PY'
import pathlib,re,os
d=pathlib.Path("/root/celikom-cutover-prepared")
outer=pathlib.Path("/etc/nginx/sites-enabled/celikom-api-https").resolve()
inner=pathlib.Path("/etc/nginx/sites-enabled/celikom-api-staging").resolve()
website=pathlib.Path("/etc/nginx/sites-enabled/celikom-site-https").resolve()
preview=pathlib.Path("/etc/nginx/sites-enabled/celikom-website-preview").resolve()
for p in [outer,inner,website,preview]:
    assert str(p).startswith("/etc/nginx/sites-available/")
    assert p.is_file() and p.stat().st_uid==0
s=outer.read_text()
assert s.count("    location / {")==1 and "server_name api.celikom.com;" in s and "access_log off;" in s
route="""    location ^~ /api/v1/ {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header Authorization $http_authorization;
        client_max_body_size 32m;
        proxy_read_timeout 120s;
        proxy_buffering off;
    }
    location ~ ^/admin(?:/|$) {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header Authorization $http_authorization;
        client_max_body_size 32m;
        proxy_read_timeout 120s;
    }
"""
# Keep explicit health/config locations (they have precedence).
s=s.replace("    location / {",route+"    location / {")
(d/"api-https.conf").write_text(s)
s=inner.read_text()
assert s.count("client_max_body_size 1m;")==1 and "listen 127.0.0.1:8081;" in s and "fastcgi_param SCRIPT_FILENAME $document_root/index.php;" in s
s=s.replace("client_max_body_size 1m;","client_max_body_size 32m;\n    set_real_ip_from 127.0.0.1;\n    real_ip_header X-Real-IP;")
s=s.replace("fastcgi_param SCRIPT_FILENAME $document_root/index.php;","fastcgi_param SCRIPT_FILENAME $document_root/index.php;\n        fastcgi_param HTTPS on;\n        fastcgi_param HTTP_AUTHORIZATION $http_authorization;\n        fastcgi_read_timeout 120s;")
(d/"api-staging.conf").write_text(s)
s=website.read_text()
assert s.count("proxy_set_header X-Forwarded-Proto https;")==1
s=s.replace("proxy_set_header X-Forwarded-Proto https;","proxy_set_header X-Forwarded-Proto https;\n        proxy_set_header X-Real-IP $remote_addr;")
(d/"site-https.conf").write_text(s)
s=preview.read_text()
assert s.count("listen 127.0.0.1:8082;")==1
s=s.replace("listen 127.0.0.1:8082;","listen 127.0.0.1:8082;\n    set_real_ip_from 127.0.0.1;\n    real_ip_header X-Real-IP;")
(d/"website-preview.conf").write_text(s)
env=pathlib.Path("/srv/celikom/app/staging-20261122/.env")
assert env.is_file() and not env.is_symlink()
data=env.read_bytes()
flags={k: b"1" for k in [b"FEATURE_ADMIN",b"FEATURE_REPLACEMENTS",b"FEATURE_USER_AUTH",b"FEATURE_USER_ENTITLEMENT",b"FEATURE_OWNER_UPLOADS",b"FEATURE_UPLOADS",b"FEATURE_REWARD_ELIGIBILITY"]}
flags.update({k:b"0" for k in [b"CELIKOM_APP_DEBUG",b"FEATURE_ANALYTICS",b"FEATURE_BILLING_VIEWS",b"FEATURE_PAID_ENTITLEMENT",b"FEATURE_REFERRAL_ATTRIBUTION",b"FEATURE_OWNER_REPORTS"]})
for k,v in flags.items():
    pattern=rb"(?m)^\s*"+re.escape(k)+rb"\s*=[^\r\n]*$"
    data,n=re.subn(pattern,k+b"="+v,data)
    assert n<=1
    if not n: data+=b"\n"+k+b"="+v+b"\n"
(d/"api.env").write_bytes(data)
for p in d.iterdir(): os.chmod(p,0o600)
print("CUTOVER_CONFIG_CANDIDATES_READY")
PY
# Verify PHP FPM limits (effective values, no environment or secret data).
php-fpm8.3 -i 2>/dev/null | grep -E '^(upload_max_filesize|post_max_size|max_execution_time|memory_limit) =>'
echo '=== Current API application readiness ==='
runuser -u www-data -- php -r 'require "/srv/celikom/app/staging-20261122/bootstrap.php";$c=require "/srv/celikom/app/staging-20261122/config/app.php";$p=Celikom\Database\Connection::open($c);foreach(["admins","users","tracks","audio_assets","track_replacements","subscriptions","billing_payments"] as $t)echo "TARGET_COUNT ",$t," ",$p->query("SELECT COUNT(*) FROM ".$t)->fetchColumn(),PHP_EOL;'
echo CELIKOM_CUTOVER_CONFIGURATION_PREPARED
