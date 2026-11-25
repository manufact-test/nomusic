#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Read-only enrollment format and host-key check. Never output enrollment data.
enroll=/home/celops/.celikom-windows-intake-enrollment
test "$(stat -c '%U:%a' "$enroll")" = celops:600
work=$(mktemp -d /root/celikom-intake-enroll-audit.XXXXXXXX)
trap 'rm -rf -- "$work"' EXIT
systemctl start celikom-mirror-sync.service
runuser -u celikom-mirror -- git --git-dir=/home/celikom-mirror/github-mirror.git show 6dce5ff7caa58cab7f20796f939858a84cac0df6 > "$work/parse.py"
test "$(git hash-object "$work/parse.py")" = 6dce5ff7caa58cab7f20796f939858a84cac0df6
python3 "$work/parse.py" "$enroll" "$work"
python3 - "$work/known_hosts" <<'PY'
import pathlib,sys
pin=pathlib.Path(sys.argv[1]).read_text().split()
pub=pathlib.Path('/etc/ssh/ssh_host_ed25519_key.pub').read_text().split()
assert pin==['95.133.160.111',*pub[:2]]
print('WINDOWS_INTAKE_SERVER_HOST_PIN_MATCH')
PY
ssh-keygen -y -P '' -f "$work/key" > "$work/pub"
python3 - "$work/pub" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1]).read_text().split()
a=pathlib.Path('/var/lib/celikom-windows-intake/.ssh/authorized_keys').read_text().split()
assert p[:2]==a[1:3]
print('WINDOWS_INTAKE_SERVER_ENROLLED_KEY_MATCH')
PY
echo WINDOWS_INTAKE_SOURCE_ENROLLMENT_VALID
