#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Exercise the new nonprivileged signed-data receiver on a disposable directory.
# No new login account, key, sudo rule, network listener, DB or feed change.
work=$(mktemp -d /var/tmp/celikom-windows-intake-rehearsal.XXXXXXXX)
trap 'rm -rf -- "$work"' EXIT
chmod 755 "$work"
install -d -m 755 "$work/tools"
install -d -m 700 -o nobody -g nogroup "$work/incoming"
install -d -m 700 "$work/root-import"
systemctl start celikom-mirror-sync.service
mirror=/home/celikom-mirror/github-mirror.git
for spec in windows-stable-private-import.py:6134127d051e8fe5d625c525e5485e9c801e3b24 windows-stable-private-intake.py:18b3d9beff7ef1a33cd9583bb89e8622ab6c90e3 windows-stable-release-verify.mjs:ae38c2c48a032fec0ad1eaae14c444e43dfb2b18 windows-stable-existing-latest.mjs:bb4d19672d45bdd0393497c3b33280308d67ef32; do
  file=${spec%%:*}
  hash=${spec#*:}
  runuser -u celikom-mirror -- git --git-dir="$mirror" show "$hash" > "$work/tools/$file"
  test "$(git hash-object "$work/tools/$file")" = "$hash"
  chmod 644 "$work/tools/$file"
done
source=/root/celikom-release-import/windows-02455
floor=/srv/celikom-releases/windows/stable
pin=/root/celikom-secrets/windows-stable-public.der
install -o root -g root -m 644 "$pin" "$work/public.der"
before=$(sha256sum "$floor/current/manifest.json" "$floor/current/manifest.json.sig" "$floor/current/CELIKOM-Windows-0.24.55.exe")
python3 "$work/tools/windows-stable-private-import.py" pack --source "$source" --output "$work/transfer.zip" --pin "$pin" --version 0.24.55 --sequence 2
digest=$(sha256sum "$work/transfer.zip" | cut -d' ' -f1)
cmd="stage-windows 0.24.55 2 $digest"
cat > "$work/tools/probe.py" <<'PY'
import os,pathlib,runpy,sys
assert os.getuid()!=0
m=runpy.run_path(sys.argv[1])
print("CELIKOM_WINDOWS_DATA_ONLY_INTAKE_OK",*m["receive"](sys.stdin.buffer,pathlib.Path(sys.argv[2]),pathlib.Path(sys.argv[3]),sys.argv[4]))
PY
chmod 644 "$work/tools/probe.py"
receive() {
  runuser -u nobody -- env -i PATH=/usr/bin:/bin LANG=C.UTF-8 python3 "$work/tools/probe.py" "$work/tools/windows-stable-private-intake.py" "$work/incoming" "$work/public.der" "$1"
}
first=$(receive "$cmd" < "$work/transfer.zip")
test "$first" = "CELIKOM_WINDOWS_DATA_ONLY_INTAKE_OK private-staged 0.24.55 2 $digest"
echo "$first"
second=$(receive "$cmd" < "$work/transfer.zip")
test "$second" = "CELIKOM_WINDOWS_DATA_ONLY_INTAKE_OK already-staged 0.24.55 2 $digest"
echo "$second"
if receive 'maintenance' </dev/null >/dev/null 2>&1; then exit 1; fi
if receive "$cmd ; id" </dev/null >/dev/null 2>&1; then exit 1; fi
if receive "$cmd" </dev/null >/dev/null 2>&1; then exit 1; fi
echo WINDOWS_INTAKE_FORBIDDEN_COMMAND_AND_CORRUPT_BYTES_REFUSED
staged="$work/incoming/windows-0.24.55-2-$digest.zip"
test "$(stat -c '%U:%a' "$staged")" = nobody:600
cmp "$staged" "$work/transfer.zip"
# Independent root-side verified import into disposable root tree only.
python3 "$work/tools/windows-stable-private-import.py" receive --dest-root "$work/root-import" --floor-root "$floor" --pin "$pin" --version 0.24.55 --sequence 2 < "$staged"
cmp "$work/root-import/windows-0.24.55/0.24.55/CELIKOM-Windows-0.24.55.exe" "$source/0.24.55/CELIKOM-Windows-0.24.55.exe"
test "$before" = "$(sha256sum "$floor/current/manifest.json" "$floor/current/manifest.json.sig" "$floor/current/CELIKOM-Windows-0.24.55.exe")"
test "$(readlink "$floor/current")" = versions/0.24.55
test "$(curl -sS --max-time 15 -o /dev/null -w '%{http_code}' https://celikom.com/CELIKOM/Windows/Updates/stable/latest.json)" = 401
echo CELIKOM_REAL_NONPRIVILEGED_WINDOWS_INTAKE_REHEARSAL_OK
