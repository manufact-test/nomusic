#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Temporary, upload-only SQL intake for the already authorized deployment key.
# No new SSH key, public port, shell permission, or source credential transfer.
gate=/usr/local/sbin/celikom-deploy-gateway
state=/root/celikom-cutover-intake
handler=/usr/local/sbin/celikom-cutover-receive
rule=/etc/sudoers.d/celikom-cutover-receive
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
case "$1" in api|cms) ;; *) exit 64;; esac
state=/root/celikom-cutover-intake
[[ -f "$state/expires" && ! -L "$state/expires" ]]
read -r expires < "$state/expires"
[[ "$expires" =~ ^[0-9]+$ && $(date +%s) -lt "$expires" ]]
exec 9>/run/lock/celikom-floki-ops.lock
flock -n 9
out="$state/$1.sql.gz"
[[ ! -e "$out" && ! -L "$out" ]]
tmp=$(mktemp "$state/.incoming-XXXXXXXX")
trap 'rm -f -- "$tmp"' EXIT
timeout 180 python3 - "$tmp" <<'NO_STDIN' 
NO_STDIN
RECEIVE
# Replace the placeholder with a Python command that reads the SSH data stream.
python3 - "$state/receive" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1])
s=p.read_text()
s=s.replace("timeout 180 python3 - \"$tmp\" <<'NO_STDIN' \nNO_STDIN\n",'''timeout 180 python3 -c 'import sys
n=0
with open(sys.argv[1],"wb") as f:
 while True:
  b=sys.stdin.buffer.read(1048576)
  if not b: break
  n+=len(b)
  if n>64*1024*1024: raise SystemExit("Snapshot exceeds approved limit")
  f.write(b)
assert n>100
' "$tmp"
gzip -t "$tmp"
mv -T "$tmp" "$out"
sha256sum "$out" | cut -d" " -f1
''')
p.write_text(s)
PY
cat > "$state/sudoers" <<'SUDOERS'
celikom-deploy ALL=(root) NOPASSWD: /usr/local/sbin/celikom-cutover-receive api, /usr/local/sbin/celikom-cutover-receive cms
SUDOERS
python3 - "$gate" "$state/gateway.next" <<'PY'
import pathlib,sys
s=pathlib.Path(sys.argv[1]).read_text()
anchor='  *) echo FLOKI_DEPLOY_COMMAND_REFUSED >&2; exit 64 ;;'
assert s.count(anchor)==1 and "receive-cutover-" not in s
s=s.replace(anchor,'''  receive-cutover-api) exec sudo -n /usr/local/sbin/celikom-cutover-receive api ;;
  receive-cutover-cms) exec sudo -n /usr/local/sbin/celikom-cutover-receive cms ;;
'''+anchor)
pathlib.Path(sys.argv[2]).write_text(s)
PY
bash -n "$state/receive"
bash -n "$state/gateway.next"
visudo -cf "$state/sudoers"
ok=0
trap 'if [[ "$ok" != 1 ]]; then cp -a "$state/gateway.original" "$gate"; rm -f "$handler" "$rule"; fi' EXIT
install -o root -g root -m 755 "$state/receive" "$handler"
install -o root -g root -m 440 "$state/sudoers" "$rule"
visudo -c >/dev/null
install -o root -g root -m 755 "$state/gateway.next" "$state/gateway.install"
mv -T "$state/gateway.install" "$gate"
ok=1
echo CELIKOM_SQL_INTAKE_READY
