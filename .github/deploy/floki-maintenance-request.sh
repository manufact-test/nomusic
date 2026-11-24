#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
SRC=/srv/celikom-releases/private/android-updates
APK=93-5ceb9db20d47390e88cd316c3f74c1928534b35bc54e316f5b841f49b951ff6a.apk
PUB=/srv/celikom-releases/public/android
MANIFEST="$SRC/stable.json"
APKPATH="$SRC/releases/$APK"
python3 - "$MANIFEST" "$APKPATH" <<'PY'
import json,pathlib,hashlib,sys
m=json.loads(pathlib.Path(sys.argv[1]).read_text())
apk=pathlib.Path(sys.argv[2]).read_bytes()
assert m["versionName"]=="0.3.92" and m["versionCode"]==93
assert m["packageName"]=="pro.celikom.nativeprobe"
assert m["signerSha256"]=="67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f"
assert m["sizeBytes"]==len(apk)==8845385
digest=hashlib.sha256(apk).hexdigest()
assert digest==m["apkSha256"]=="5ceb9db20d47390e88cd316c3f74c1928534b35bc54e316f5b841f49b951ff6a"
assert m["apkUrl"].startswith("https://lemonchiffon-narwhal-791953.hostingersite.com/releases/android/")
m["apkUrl"]="https://celikom.com/releases/android/"+str(m["versionCode"])+"-"+digest+".apk"
assert m["apkUrl"]=="https://celikom.com/releases/android/"+pathlib.Path(sys.argv[2]).name
out=json.dumps(m,ensure_ascii=False,separators=(",",":"))+"\n"
pathlib.Path("/tmp/celikom-android-stable-candidate.json").write_text(out)
print("ANDROID_CELIKOM_CANDIDATE_JSON_SHA256",hashlib.sha256(out.encode()).hexdigest())
print("ANDROID_CELIKOM_CANDIDATE_URL",m["apkUrl"])
PY
install -d -o root -g www-data -m 750 "$PUB" "$PUB/updates" "$PUB/updates/android" "$PUB/releases"
install -o root -g www-data -m 640 /tmp/celikom-android-stable-candidate.json "$PUB/updates/android/stable.json"
install -o root -g www-data -m 640 "$APKPATH" "$PUB/releases/$APK"
rm -f /tmp/celikom-android-stable-candidate.json
SNIP=/root/celikom-cutover-prepared/android-updates.conf
[[ ! -e "$SNIP" && ! -L "$SNIP" ]]
cat > "$SNIP" <<'NGINX'
# Prepared only; do not include until API/client acceptance and owner approval.
location = /updates/android/stable.json {
    auth_basic off;
    default_type application/json;
    alias /srv/celikom-releases/public/android/updates/android/stable.json;
    add_header Cache-Control "no-store" always;
    add_header X-Content-Type-Options "nosniff" always;
    limit_except GET HEAD { deny all; }
}
location = /releases/android/93-5ceb9db20d47390e88cd316c3f74c1928534b35bc54e316f5b841f49b951ff6a.apk {
    auth_basic off;
    default_type application/vnd.android.package-archive;
    alias /srv/celikom-releases/public/android/releases/93-5ceb9db20d47390e88cd316c3f74c1928534b35bc54e316f5b841f49b951ff6a.apk;
    add_header Cache-Control "public, max-age=31536000, immutable" always;
    add_header X-Content-Type-Options "nosniff" always;
    limit_except GET HEAD { deny all; }
}
NGINX
chown root:root "$SNIP"
chmod 600 "$SNIP"
work=$(mktemp -d /root/celikom-android-nginx-test.XXXXXXXX)
trap 'rm -rf -- "$work"' EXIT
cat > "$work/nginx.conf" <<EOF
pid $work/nginx.pid;
error_log $work/error.log;
events {}
http {
  include /etc/nginx/mime.types;
  server {
    listen 127.0.0.1:18084;
    server_name celikom-android-preview;
    auth_basic "private";
    auth_basic_user_file /etc/nginx/celikom-site.htpasswd;
    include $SNIP;
  }
}
EOF
nginx -t -p "$work/" -c "$work/nginx.conf"
cmp "$MANIFEST" "$SRC/stable.json"
sha256sum "$PUB/updates/android/stable.json" "$PUB/releases/$APK"
stat -c '%n mode=%a owner=%U:%G size=%s' "$PUB" "$PUB/updates/android/stable.json" "$PUB/releases/$APK" "$SNIP"
got=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 15 https://celikom.com/updates/android/stable.json)
[[ "$got" == 401 ]]
echo CELIKOM_ANDROID_UPDATE_PRIVATE_CANDIDATE_READY_NOT_EXPOSED
