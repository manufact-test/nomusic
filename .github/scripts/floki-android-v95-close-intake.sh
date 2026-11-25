#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Finalize only three pinned bytes; ALWAYS restore the original SSH gateway.
state=/root/celikom-android-v95-intake
gate=/usr/local/sbin/celikom-deploy-gateway
handler=/usr/local/sbin/celikom-android-v95-receive
rule=/etc/sudoers.d/celikom-android-v95-receive
out=/srv/celikom-releases/private/android-v95
[[ -d "$state" && ! -L "$state" && -f "$state/gateway.original" ]]
ok=0
cleanup(){
  rc=$?
  if [[ -f "$state/gateway.original" ]]; then
    install -o root -g root -m 755 "$state/gateway.original" "$state/gateway.restore"
    mv -T "$state/gateway.restore" "$gate"
  fi
  rm -f -- "$handler" "$rule" "$state/expires"
  visudo -c >/dev/null || rc=1
  if [[ "$ok" != 1 ]]; then
    echo CELIKOM_ANDROID_V95_INTAKE_ABORTED_AND_GATEWAY_RESTORED
  fi
  exit "$rc"
}
trap cleanup EXIT
bash -n "$state/gateway.original"
[[ ! -e "$out" && ! -L "$out" ]]
for entry in \
 'CELIKOM-Android-0.3.94-SIGNED.apk 8845385 d43d2dd12dfa6a4cd79094abccabad67080c6f02542cd25edff55b3d36018469' \
 'stable-floki-candidate.json 520 8e5205b64ea65b8a9879b7034a3e5c141a8e96b79a0e1a07c1d849def358478e' \
 'stable-hostinger-bridge-candidate.json 554 011386d2bb9c1fdb504f2b802c590b2076f07a1132c79082282f4b8846fc005f'; do
  read -r name length sha <<< "$entry"
  f="$state/$name"
  [[ -f "$f" && ! -L "$f" && "$(stat -c '%u:%a:%s' "$f")" == "0:600:$length" ]]
  printf '%s  %s\n' "$sha" "$f" | sha256sum -c --status
done
python3 - "$state/stable-floki-candidate.json" "$state/stable-hostinger-bridge-candidate.json" <<'PY'
import json,sys
f=json.load(open(sys.argv[1]));h=json.load(open(sys.argv[2]))
required=['schemaVersion','enabled','channel','packageName','versionCode','versionName','signerSha256','apkSha256','sizeBytes','minSdk','apkUrl','notesRu']
assert set(f)==set(h)==set(required)
for m in (f,h):
 assert m['schemaVersion']==1 and m['enabled'] is True and m['channel']=='stable'
 assert m['packageName']=='pro.celikom.nativeprobe'
 assert m['versionName']=='0.3.94' and m['versionCode']==95
 assert m['signerSha256']=='67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f'
 assert m['apkSha256']=='d43d2dd12dfa6a4cd79094abccabad67080c6f02542cd25edff55b3d36018469'
 assert m['sizeBytes']==8845385 and m['minSdk']==28
 assert m['notesRu']
assert {k for k in f if f[k]!=h[k]}=={'apkUrl'}
suffix='/releases/android/95-d43d2dd12dfa6a4cd79094abccabad67080c6f02542cd25edff55b3d36018469.apk'
assert f['apkUrl']=='https://celikom.com'+suffix
assert h['apkUrl']=='https://lemonchiffon-narwhal-791953.hostingersite.com'+suffix
print('CELIKOM_ANDROID_V95_DUAL_ORIGIN_MANIFESTS_VALIDATED')
PY
install -d -o root -g root -m 700 "$out"
for name in CELIKOM-Android-0.3.94-SIGNED.apk stable-floki-candidate.json stable-hostinger-bridge-candidate.json; do
  install -o root -g root -m 600 "$state/$name" "$out/$name"
done
ok=1
echo CELIKOM_ANDROID_V95_PRIVATE_BYTES_STAGED_SIGNED_HASH_VERIFIED_NO_PUBLIC_RELEASE
