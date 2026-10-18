#!/usr/bin/env bash
# One-time, guarded, NON-PRODUCTION Hostinger owner-review staging installer.
set -euo pipefail
[[ "${GITHUB_REPOSITORY:-}" == "manufact-test/nomusic" ]]
[[ "${GITHUB_REF:-}" == "refs/heads/feature/api-range" ]]
request=$(php -r '$r=json_decode(file_get_contents(".github/deploy/celikom-site-staging-request.json"),true,512,JSON_THROW_ON_ERROR); if(!is_array($r)||array_keys($r)!==["operation","target"]||$r["target"]!=="hostinger-owner-review"||!in_array($r["operation"],["prepare","install"],true))exit(2); echo $r["operation"];')
if [[ "$request" == "prepare" ]]; then
  echo 'STAGING_PREPARED: pipeline verified; no Hostinger files/database changed.'
  exit 0
fi
: "${CELIKOM_HOSTINGER_SSH_KEY:?GitHub SSH key missing}"
: "${CELIKOM_HOSTINGER_KNOWN_HOSTS:?GitHub verified known_hosts missing}"
: "${CELIKOM_STAGING_DB_NAME:?Dedicated Hostinger MySQL name missing}"
: "${CELIKOM_STAGING_DB_USER:?Dedicated Hostinger MySQL user missing}"
: "${CELIKOM_STAGING_DB_PASSWORD:?Dedicated Hostinger MySQL password missing}"
[[ "$CELIKOM_STAGING_DB_NAME" =~ ^u235811320_celikom_stage[a-zA-Z0-9_]*$ ]] || { echo 'Use a dedicated u235811320_celikom_stage* database'; exit 1; }
[[ "$CELIKOM_STAGING_DB_USER" =~ ^u235811320_[a-zA-Z0-9_]+$ ]] || { echo 'Expected own Hostinger-prefixed website DB user'; exit 1; }
umask 077
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
printf '%s\n' "$CELIKOM_HOSTINGER_SSH_KEY" > "$scratch/key"
printf '%s\n' "$CELIKOM_HOSTINGER_KNOWN_HOSTS" > "$scratch/known_hosts"
chmod 600 "$scratch/key" "$scratch/known_hosts"
sshopt=(-T -p 65002 -i "$scratch/key" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile="$scratch/known_hosts" -o ConnectTimeout=15)
scpopt=(-P 65002 -i "$scratch/key" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile="$scratch/known_hosts")
target=u235811320@92.113.19.189
root=/home/u235811320/domains/lemonchiffon-narwhal-791953.hostingersite.com

# Refuse any other domain, pre-existing website installation, or shared CMS DB.
ssh "${sshopt[@]}" "$target" 'bash -se' <<'REMOTE'
set -euo pipefail
root=/home/u235811320/domains/lemonchiffon-narwhal-791953.hostingersite.com
test -d "$root/public_html"
test -f "$root/public_html/default.php"
test ! -e "$root/public_html/index.php"
test ! -e "$root/public_html/.htaccess"
test ! -e "$root/celikom-private"
test -x /opt/alt/php83/usr/bin/php
echo 'STAGING_TARGET_VERIFIED: dedicated placeholder domain'
REMOTE

# Credential values never enter logs, commands, the URL or the Git repo.
php -r '
$root="/home/u235811320/domains/lemonchiffon-narwhal-791953.hostingersite.com/celikom-private";
$vars=[
 "CELIKOM_SITE_DB_HOST"=>"localhost",
 "CELIKOM_SITE_DB_NAME"=>getenv("CELIKOM_STAGING_DB_NAME"),
 "CELIKOM_SITE_DB_USER"=>getenv("CELIKOM_STAGING_DB_USER"),
 "CELIKOM_SITE_DB_PASSWORD"=>getenv("CELIKOM_STAGING_DB_PASSWORD"),
 "CELIKOM_SITE_AUTH_HMAC_KEY"=>bin2hex(random_bytes(40)),
 "CELIKOM_SITE_WRITE_GATE_FILE"=>$root."/.celikom-cms-writes.lock",
 "CELIKOM_SITE_MEDIA_DIR"=>$root."/media",
];
foreach($vars as $v){if(!is_string($v)||$v==="")exit(2);}
file_put_contents($argv[1],"<?php\nreturn ".var_export($vars,true).";\n",LOCK_EX);
chmod($argv[1],0600);
' "$scratch/staging-config.php"

cat > "$scratch/.htaccess" <<'HTACCESS'
DirectoryIndex index.php
Options -Indexes
RewriteEngine On
RewriteCond %{HTTPS} !=on
RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [R=302,L]
AuthType Basic
AuthName "CELIKOM private review"
AuthUserFile /home/u235811320/domains/lemonchiffon-narwhal-791953.hostingersite.com/celikom-private/.htpasswd
Require valid-user
<IfModule mod_headers.c>
Header always set X-Robots-Tag "noindex, nofollow, noarchive"
Header always set Cache-Control "no-store"
</IfModule>
HTACCESS
printf 'User-agent: *\nDisallow: /\n' > "$scratch/robots.txt"

# Create ONLY the private website directory, leave other domains untouched.
ssh "${sshopt[@]}" "$target" 'bash -se' <<'REMOTE'
set -euo pipefail
root=/home/u235811320/domains/lemonchiffon-narwhal-791953.hostingersite.com
umask 077
mkdir -m 700 -p "$root/celikom-private/app" "$root/celikom-private/database" \
  "$root/celikom-private/tools" "$root/celikom-private/media"
chmod 700 "$root/celikom-private" "$root/celikom-private/media"
REMOTE
scp "${scpopt[@]}" "$scratch/staging-config.php" "$target:$root/celikom-private/staging-config.php"
scp "${scpopt[@]}" "$scratch/.htaccess" "$target:$root/public_html/.htaccess"
scp "${scpopt[@]}" "$scratch/robots.txt" "$target:$root/public_html/robots.txt"
scp -r "${scpopt[@]}" website/app/. "$target:$root/celikom-private/app/"
scp -r "${scpopt[@]}" website/database/. "$target:$root/celikom-private/database/"
scp "${scpopt[@]}" website/tools/staging-initialize.php "$target:$root/celikom-private/tools/staging-initialize.php"
scp -r "${scpopt[@]}" website/public/. "$target:$root/public_html/"
ssh "${sshopt[@]}" "$target" \
  "/opt/alt/php83/usr/bin/php '$root/celikom-private/tools/staging-initialize.php'"

# Do not report success unless HTTPS + protection + real CMS are all live.
unauth=$(curl -sS --max-time 20 -o /dev/null -w '%{http_code}' "https://lemonchiffon-narwhal-791953.hostingersite.com/")
test "$unauth" = 401 || { echo "STAGING_PROTECTION_FAILED status=$unauth"; exit 1; }
scp "${scpopt[@]}" "$target:$root/celikom-private/staging-owner-credentials.txt" "$scratch/credentials"
basic=$(sed -n 's/^HTTP Basic password: //p' "$scratch/credentials")
test -n "$basic"
base=https://lemonchiffon-narwhal-791953.hostingersite.com
site=$(curl -sS -u "review:$basic" --max-time 20 -o "$scratch/site.html" -w '%{http_code}' "$base/")
admin=$(curl -sS -u "review:$basic" --max-time 20 -o "$scratch/admin.html" -w '%{http_code}' "$base/admin/")
test "$site" = 200 && grep -q 'CELIKOM' "$scratch/site.html"
test "$admin" = 200 && grep -q 'Вход администратора' "$scratch/admin.html"
echo 'STAGING_LIVE: protected HTTPS website and working CMS login route; initial v10 published.'
echo 'Credentials remain ONLY in the server private staging-owner-credentials.txt; never in GitHub logs.'
