#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Temporarily extend the existing pinned SSH gateway with three exact binary
# receivers. Root-only private staging; no HTTP route, source upload or public release.
state=/root/celikom-android-v95-intake
gate=/usr/local/sbin/celikom-deploy-gateway
handler=/usr/local/sbin/celikom-android-v95-receive
rule=/etc/sudoers.d/celikom-android-v95-receive
[[ ! -e "$state" && ! -e "$handler" && ! -e "$rule" ]]
[[ -f "$gate" && ! -L "$gate" && "$(stat -c '%u:%a' "$gate")" == 0:755 ]]
install -d -m 700 "$state"
cp -a "$gate" "$state/gateway.original"
date -d '+30 minutes' +%s > "$state/expires"
cat > "$state/receive" <<'RECEIVE'
#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
[[ $(id -u) == 0 && $# == 1 ]]
state=/root/celikom-android-v95-intake
[[ -f "$state/expires" && ! -L "$state/expires" ]]
read -r expires < "$state/expires"
[[ "$expires" =~ ^[0-9]+$ && $(date +%s) -lt "$expires" ]]
case "$1" in
  apk) filename=CELIKOM-Android-0.3.94-SIGNED.apk; size=8845385; digest=d43d2dd12dfa6a4cd79094abccabad67080c6f02542cd25edff55b3d36018469 ;;
  floki) filename=stable-floki-candidate.json; size=520; digest=8e5205b64ea65b8a9879b7034a3e5c141a8e96b79a0e1a07c1d849def358478e ;;
  bridge) filename=stable-hostinger-bridge-candidate.json; size=554; digest=011386d2bb9c1fdb504f2b802c590b2076f07a1132c79082282f4b8846fc005f ;;
  *) exit 64 ;;
esac
exec 9>/run/lock/celikom-floki-ops.lock
flock -n 9
out="$state/$filename"
[[ ! -e "$out" && ! -L "$out" ]]
tmp=$(mktemp "$state/.incoming-XXXXXXXX")
trap 'rm -f -- "$tmp"' EXIT
timeout 180 python3 -c '
import sys
path=sys.argv[1];limit=int(sys.argv[2])
content=sys.stdin.buffer.read(limit+1)
if len(content)!=limit: raise SystemExit("Unexpected exact payload length")
with open(path,"wb") as stream: stream.write(content)
' "$tmp" "$size"
[[ "$(stat -c %s "$tmp")" == "$size" ]]
printf '%s  %s\n' "$digest" "$tmp" | sha256sum -c --status
chmod 600 "$tmp"
mv -T "$tmp" "$out"
echo "$digest"
RECEIVE
cat > "$state/sudoers" <<'SUDOERS'
celikom-deploy ALL=(root) NOPASSWD: /usr/local/sbin/celikom-android-v95-receive apk, /usr/local/sbin/celikom-android-v95-receive floki, /usr/local/sbin/celikom-android-v95-receive bridge
SUDOERS
python3 - "$gate" "$state/gateway.next" <<'PY'
import pathlib,sys
s=pathlib.Path(sys.argv[1]).read_text()
anchor='  *) echo FLOKI_DEPLOY_COMMAND_REFUSED >&2; exit 64 ;;'
assert s.count(anchor)==1
assert 'receive-android-v95-' not in s
new='''  receive-android-v95-apk) exec sudo -n /usr/local/sbin/celikom-android-v95-receive apk ;;
  receive-android-v95-floki) exec sudo -n /usr/local/sbin/celikom-android-v95-receive floki ;;
  receive-android-v95-bridge) exec sudo -n /usr/local/sbin/celikom-android-v95-receive bridge ;;
'''
pathlib.Path(sys.argv[2]).write_text(s.replace(anchor,new+anchor))
PY
bash -n "$state/receive"
bash -n "$state/gateway.next"
visudo -cf "$state/sudoers"
ok=0
restore(){
  if [[ "$ok" != 1 ]]; then
    cp -a "$state/gateway.original" "$gate" || true
    rm -f "$handler" "$rule"
    echo CELIKOM_ANDROID_V95_TEMP_GATEWAY_INSTALL_ROLLBACK
  fi
}
trap restore EXIT
install -o root -g root -m 755 "$state/receive" "$handler"
install -o root -g root -m 440 "$state/sudoers" "$rule"
visudo -c >/dev/null
install -o root -g root -m 755 "$state/gateway.next" "$state/gateway.install"
mv -T "$state/gateway.install" "$gate"
ok=1
echo CELIKOM_ANDROID_V95_EXACT_PRIVATE_INTAKE_READY
