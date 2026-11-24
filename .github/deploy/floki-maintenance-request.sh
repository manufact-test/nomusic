#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
echo '=== Actual mail transport (safe metadata only) ==='
runuser -u www-data -- php -r '
require "/srv/celikom/app/staging-20261122/bootstrap.php";
$c=require "/srv/celikom/app/staging-20261122/config/app.php";
echo "transport=",($c["mail_transport"]??""),"\n";
echo "brevo_key_configured=",(!empty($c["mail_brevo_api_key"])?"yes":"no"),"\n";
echo "sender_domain=",substr(strrchr((string)($c["mail_from"]??""),"@")?: "",1),"\n";
echo "php_curl=",function_exists("curl_init")?"yes":"no","\n";
'
echo '=== Brevo HTTPS endpoint reachability only; no auth header and no email sent ==='
getent ahostsv4 api.brevo.com | head -n 2
timeout 12 openssl s_client -connect api.brevo.com:443 -servername api.brevo.com -brief </dev/null 2>&1 | grep -E 'CONNECTION ESTABLISHED|Protocol version|Ciphersuite|Verification:|Verify return code|CONNECTED'
echo CELIKOM_BREVO_HTTPS_TRANSPORT_READY
