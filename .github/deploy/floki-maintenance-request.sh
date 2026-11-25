#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Install the independent root-only signed data consumer, and test a real
# existing current-release replay. No public feed, DB, key or account changes.
lib=/usr/local/lib/celikom-windows-intake
home=/var/lib/celikom-windows-intake
tool="$lib/windows-stable-private-consume.py"
pin=/root/celikom-secrets/windows-stable-public.der
floor=/srv/celikom-releases/windows/stable
source=/root/celikom-release-import/windows-02455
test "$(stat -c '%u:%a' "$lib")" = 0:755
test ! -e "$tool" && test ! -L "$tool"
test "$(id -G celikom-windows-intake)" = "$(id -g celikom-windows-intake)"
test "$(stat -c '%U:%a' /home/celops/.celikom-windows-intake-enrollment)" = celops:600
work=$(mktemp -d /root/celikom-consume-rehearsal.XXXXXXXX)
installed=0
success=0
cleanup(){
  if [[ "$success" != 1 && "$installed" == 1 ]]; then rm -f -- "$tool"; fi
  rm -rf -- "$work"
}
trap cleanup EXIT
systemctl start celikom-mirror-sync.service
mirror=/home/celikom-mirror/github-mirror.git
runuser -u celikom-mirror -- git --git-dir="$mirror" show "4274820e1ffc712ef0f31eea8cb94985140fa020" > "$work/consume.py"
test "$(git hash-object "$work/consume.py")" = 4274820e1ffc712ef0f31eea8cb94985140fa020
python3 -c 'import ast,pathlib,sys;ast.parse(pathlib.Path(sys.argv[1]).read_text())' "$work/consume.py"
install -o root -g root -m 644 "$work/consume.py" "$tool"
installed=1
before=$(sha256sum "$floor/current/manifest.json" "$floor/current/manifest.json.sig" "$floor/current/CELIKOM-Windows-0.24.55.exe")
python3 "$lib/windows-stable-private-import.py" pack --source "$source" \
  --output "$work/transfer.zip" --pin "$pin" --version 0.24.55 --sequence 2
digest=$(sha256sum "$work/transfer.zip" | cut -d' ' -f1)
reply=$(runuser -u celikom-windows-intake -- env -i PATH=/usr/bin:/bin LANG=C.UTF-8 \
  SSH_ORIGINAL_COMMAND="stage-windows 0.24.55 2 $digest" "$lib/gateway" < "$work/transfer.zip")
test "$reply" = "CELIKOM_WINDOWS_DATA_ONLY_INTAKE_OK private-staged 0.24.55 2 $digest"
echo "$reply"
/usr/bin/python3 "$tool"
test ! -e "$home/incoming/windows-0.24.55-2-$digest.zip"
test ! -e /root/celikom-release-import/windows-0.24.55
test "$before" = "$(sha256sum "$floor/current/manifest.json" "$floor/current/manifest.json.sig" "$floor/current/CELIKOM-Windows-0.24.55.exe")"
test "$(curl -sS --max-time 15 -o /dev/null -w '%{http_code}' https://celikom.com/CELIKOM/Windows/Updates/stable/latest.json)" = 401
test "$(stat -c '%U:%a' /home/celops/.celikom-windows-intake-enrollment)" = celops:600
success=1
echo CELIKOM_WINDOWS_ROOT_CONSUMER_REAL_REPLAY_OK
