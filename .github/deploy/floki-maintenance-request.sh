#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Rehearsal with already-present signed Windows files. Never fetch drafts via
# an unapproved identity, install a new SSH command or publish a stable feed.
work=$(mktemp -d /root/celikom-private-windows-rehearsal.XXXXXXXX)
trap 'rm -rf -- "$work"' EXIT
commit=6c7fb4d09434cb1e6f336cd4362c8bb674803fe2
mirror=/home/celikom-mirror/github-mirror.git
for spec in windows-stable-private-import.py:dd4cc219b568bc508d7a6a86f8ef27e2f4557e4f windows-stable-release-verify.mjs:ae38c2c48a032fec0ad1eaae14c444e43dfb2b18 windows-stable-existing-latest.mjs:bb4d19672d45bdd0393497c3b33280308d67ef32; do
  file=${spec%%:*}
  hash=${spec#*:}
  runuser -u celikom-mirror -- git --git-dir="$mirror" show "$commit:.github/scripts/$file" > "$work/$file"
  test "$(git hash-object "$work/$file")" = "$hash"
done
source=/root/celikom-release-import/windows-02455
floor=/srv/celikom-releases/windows/stable
pin=/root/celikom-secrets/windows-stable-public.der
test "$(readlink "$floor/current")" = versions/0.24.55
before=$(sha256sum "$floor/current/manifest.json" "$floor/current/manifest.json.sig" "$floor/current/CELIKOM-Windows-0.24.55.exe")
mkdir -m 700 "$work/import"
python3 "$work/windows-stable-private-import.py" pack --source "$source" --output "$work/transfer.zip" --pin "$pin" --version 0.24.55 --sequence 2
for i in 1 2; do
  python3 "$work/windows-stable-private-import.py" receive --dest-root "$work/import" --floor-root "$floor" --pin "$pin" --version 0.24.55 --sequence 2 < "$work/transfer.zip"
done
dest="$work/import/windows-0.24.55"
cmp "$dest/0.24.55/CELIKOM-Windows-0.24.55.exe" "$source/0.24.55/CELIKOM-Windows-0.24.55.exe"
cmp "$dest/latest.json" "$source/latest.json"
cmp "$dest/latest.json.sig" "$source/latest.json.sig"
cmp "$dest/manifest-public-key.der" "$pin"
test "$(readlink "$floor/current")" = versions/0.24.55
test "$before" = "$(sha256sum "$floor/current/manifest.json" "$floor/current/manifest.json.sig" "$floor/current/CELIKOM-Windows-0.24.55.exe")"
test "$(curl -sS --max-time 15 -o /dev/null -w '%{http_code}' https://celikom.com/CELIKOM/Windows/Updates/stable/latest.json)" = 401
echo CELIKOM_REAL_SIGNED_WINDOWS_PRIVATE_TRANSFER_REHEARSAL_OK
