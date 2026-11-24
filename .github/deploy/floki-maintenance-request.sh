#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
echo '=== ANDROID SIGNATURE VERIFICATION ==='
if ! command -v apksigner >/dev/null; then
  timeout 240 apt-get update -qq >/dev/null
  timeout 240 env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends apksigner >/dev/null
fi
python3 - <<'PY'
import pathlib, json, hashlib, subprocess, re, stat
root=pathlib.Path("/srv/celikom/migration/sites-20261124/android-private/android-updates")
m=json.loads((root/"stable.json").read_text())
assert m["schemaVersion"]==1 and m["enabled"] is True and m["channel"]=="stable"
assert m["packageName"]=="pro.celikom.nativeprobe"
cert="67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f"
assert m["signerSha256"]==cert
assert m["versionName"]=="0.3.92" and m["versionCode"]==93 and m["minSdk"]==28
sha=m["apkSha256"]
assert re.fullmatch("[a-f0-9]{64}",sha)
assert m["apkUrl"]=="https://lemonchiffon-narwhal-791953.hostingersite.com/releases/android/93-"+sha+".apk"
assert isinstance(m["notesRu"],str) and len(m["notesRu"])<=800 and "<" not in m["notesRu"] and ">" not in m["notesRu"]
apk=root/"releases"/("93-"+sha+".apk")
assert stat.S_ISREG(apk.lstat().st_mode) and apk.stat().st_size==m["sizeBytes"]
assert hashlib.file_digest(apk.open("rb"),"sha256").hexdigest()==sha
p=subprocess.run(["apksigner","verify","--print-certs",str(apk)],capture_output=True,text=True,timeout=60)
assert p.returncode==0,"APK signature verification failed"
matches=re.findall(r"Signer #\d+ certificate SHA-256 digest: ([a-fA-F0-9]+)",p.stdout)
assert [s.lower() for s in matches]==[cert],"unexpected APK signer"
print("ANDROID_LEGACY_SIGNATURE_VERIFIED",m["versionName"],sha)
PY
echo '=== API AND WEBSITE CUTOVER PREFLIGHT ==='
# Output route configuration only, not credentials or .env contents.
for path in /etc/nginx/sites-enabled/celikom-api-https /etc/nginx/sites-enabled/celikom-website-preview /etc/nginx/sites-enabled/celikom-site-https; do
  test -f "$path"
  printf '%s\n' "$path"
  awk '/^[[:space:]]*(listen|server_name|location|proxy_pass|proxy_set_header|real_ip_header|set_real_ip_from|client_max_body_size|fastcgi_pass|fastcgi_param|try_files|access_log|root|auth_basic|return|include)[[:space:]]/ && !/Authorization|PASSWORD|TOKEN|SECRET|COOKIE|KEY/ {print}' "$path"
done
echo '=== API CURRENT FEATURE STATE ==='
runuser -u www-data -- php -r 'require "/srv/celikom/app/staging-20261122/bootstrap.php"; $c=require "/srv/celikom/app/staging-20261122/config/app.php"; foreach($c as $k=>$v){if(is_bool($v))echo $k,"=",($v?"ON":"OFF"),PHP_EOL;} echo "audio_max_bytes=",$c["max_audio_size"],PHP_EOL; echo "mail_transport=",($c["mail_transport"]==="brevo"?"brevo":"other"),PHP_EOL;'
nginx -t
echo CELIKOM_ANDROID_SIGNER_AND_CUTOVER_PREFLIGHT_OK
