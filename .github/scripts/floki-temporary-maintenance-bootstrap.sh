#!/bin/bash
# OWNER OPT-IN: temporary administrative access for the existing dedicated
# GitHub deployment key. A maintenance payload can run arbitrary ROOT commands.
# Do not install unless the owner accepts that risk. No CI runner access.
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
[[ $(id -u) == 0 && $# == 0 ]] || exit 64
GATE=/usr/local/sbin/celikom-deploy-gateway
OPS=/usr/local/sbin/celikom-floki-maintenance
RULE=/etc/sudoers.d/celikom-maintenance
STATE=/var/lib/celikom-maintenance
[[ -f "$GATE" && ! -L "$GATE" && $(stat -c '%u:%a' "$GATE") == 0:755 ]]
[[ -f /var/lib/celikom-deploy/.ssh/authorized_keys ]]
[[ ! -e "$OPS" && ! -L "$OPS" && ! -e "$RULE" && ! -L "$RULE" && ! -e "$STATE" && ! -L "$STATE" ]]
work=$(mktemp -d /root/celikom-maintenance-install.XXXXXXXX)
trap 'rm -rf -- "$work"' EXIT
cp -p -- "$GATE" "$work/gateway.original"
python3 - "$GATE" "$work/gateway" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]).read_text()
needle = '  *) echo FLOKI_DEPLOY_COMMAND_REFUSED >&2; exit 64 ;;'
assert p.count(needle) == 1 and "maintenance)" not in p
p = p.replace(needle, '''  maintenance) exec sudo -n /usr/local/sbin/celikom-floki-maintenance run ;;
  revoke-maintenance) exec sudo -n /usr/local/sbin/celikom-floki-maintenance revoke ;;
''' + needle)
pathlib.Path(sys.argv[2]).write_text(p)
PY
cat > "$work/maintenance" <<'OPS'
#!/bin/bash
# The forced SSH key remains non-interactive with forwarding disabled.
# This command is deliberately ROOT-equivalent during its short lease.
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
[[ $(id -u) == 0 && $# == 1 ]] || exit 64
STATE=/var/lib/celikom-maintenance
LEASE="$STATE/expires"
exec 9>/run/lock/celikom-floki-ops.lock
flock -n 9 || { echo FLOKI_DEPLOY_BUSY; exit 75; }
case "$1" in
  revoke)
    rm -f -- "$LEASE"
    echo FLOKI_MAINTENANCE_REVOKED
    exit 0
    ;;
  run)
    [[ -f "$LEASE" && ! -L "$LEASE" && $(stat -c '%u:%a' "$LEASE") == 0:600 ]] || { echo FLOKI_MAINTENANCE_CLOSED; exit 77; }
    read -r expires < "$LEASE"
    [[ "$expires" =~ ^[0-9]{10}$ && $(date +%s) -lt "$expires" ]] || { echo FLOKI_MAINTENANCE_EXPIRED; exit 77; }
    payload=$(mktemp "$STATE/request.XXXXXXXX")
    trap 'rm -f -- "$payload"' EXIT
    # Bounded input, not argv, not evaluated as an SSH command line.
    timeout 45 python3 -c 'import sys; b=sys.stdin.buffer.read(131073); assert 1<=len(b)<=131072 and b.startswith(b"#!/bin/bash\n") and b"\0" not in b; open(sys.argv[1],"wb").write(b)' "$payload"
    /bin/bash -n "$payload"
    digest=$(sha256sum "$payload" | cut -d' ' -f1)
    logger -t celikom-maintenance -- "authorized maintenance payload sha256=$digest"
    echo "FLOKI_MAINTENANCE_REQUEST_SHA256=$digest"
    cd /root
    timeout --kill-after=15s 1200s env -i PATH="$PATH" HOME=/root USER=root LOGNAME=root LANG=C.UTF-8 /bin/bash --noprofile --norc "$payload" </dev/null
    echo FLOKI_MAINTENANCE_OPERATION_OK
    ;;
  *) exit 64 ;;
esac
OPS
cat > "$work/sudoers" <<'SUDOERS'
celikom-deploy ALL=(root) NOPASSWD: /usr/local/sbin/celikom-floki-maintenance run, /usr/local/sbin/celikom-floki-maintenance revoke
SUDOERS
bash -n "$work/gateway"
bash -n "$work/maintenance"
visudo -cf "$work/sudoers"
install -d -o root -g root -m 700 "$STATE"
install -o root -g root -m 600 "$work/gateway.original" "$STATE/gateway.original"
install -o root -g root -m 755 "$work/maintenance" "$OPS"
install -o root -g root -m 440 "$work/sudoers" "$RULE"
if ! visudo -c >/dev/null; then
  rm -f -- "$RULE" "$OPS"
  echo FLOKI_MAINTENANCE_SUDOERS_FAILED
  exit 1
fi
# Eight-hour lease starts only on the owner's explicit local installation.
date -d '+8 hours' +%s > "$STATE/expires"
chmod 600 "$STATE/expires"
install -o root -g root -m 755 "$work/gateway" "$STATE/gateway.next"
mv -T "$STATE/gateway.next" "$GATE"
echo FLOKI_TEMPORARY_MAINTENANCE_READY
echo "Expires UTC: $(date -u -d "@$(cat "$STATE/expires")" '+%F %T')"
echo 'Revoke locally: sudo /usr/local/sbin/celikom-floki-maintenance revoke'
