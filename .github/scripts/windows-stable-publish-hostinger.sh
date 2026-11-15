#!/usr/bin/env bash
# W155 P-256 signed stable release publisher. Manual protected GitHub environment only.
set -euo pipefail
umask 077
release_dir="$1"; version="$2"; sequence="$3"
origin="$CELIKOM_STABLE_ORIGIN"; root="$CELIKOM_STABLE_DEPLOY_ROOT"
[[ "$version" =~ ^[0-9]{1,4}\.[0-9]{1,4}\.[0-9]{1,5}$ &&
   "$sequence" =~ ^[1-9][0-9]{0,14}$ ]] || { echo W155_BAD_VERSION_SEQUENCE; exit 2; }
[[ "$origin" == "https://celikom.com" ]] || {
  echo W155_ORIGIN_NOT_APPROVED; exit 2; }
[[ "$root" == "/home/u235811320/domains/celikom.com/public_html" ]] || {
  echo W155_HOSTINGER_ROOT_NOT_APPROVED; exit 2; }
[[ -n "$HOSTINGER_SSH_KEY" && -n "$CELIKOM_STABLE_PUBLIC_KEY_DER_BASE64" ]] || {
  echo W155_DEPLOY_SECRETS_MISSING; exit 2; }
node .github/scripts/windows-stable-release-verify.mjs "$release_dir" "$version" "$sequence"
exe="CELIKOM-Windows-$version.exe"
tmp="$(mktemp -d)"
remote_root="/home/u235811320/.celikom-stable-stage-$GITHUB_RUN_ID"
target='u235811320@92.113.19.189'
stage_created=0
ssh_remote() {
  ssh -T -p 65002 -i "$tmp/key" -o BatchMode=yes -o IdentitiesOnly=yes \
    -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$tmp/known_hosts" \
    -o GlobalKnownHostsFile=/dev/null -o ConnectTimeout=15 "$target" "$@"
}
cleanup() {
  code=$?
  trap - EXIT
  if [[ "$stage_created" == 1 ]]; then
    ssh_remote "rm -rf '$remote_root'" >/dev/null 2>&1 || true
  fi
  rm -rf "$tmp"
  exit "$code"
}
trap cleanup EXIT
printf '%s\n' "$HOSTINGER_SSH_KEY" | tr -d '\r' > "$tmp/key"
chmod 600 "$tmp/key"
ssh-keygen -y -P '' -f "$tmp/key" > "$tmp/key.pub"
fingerprint="$(ssh-keygen -lf "$tmp/key.pub" -E sha256 | awk '{print $2}')"
[[ "$fingerprint" == 'SHA256:Q6FyifXRq6garceQdIIjBmXhkk81Ic1p/x9JTSYHWUk' ]] || {
  echo W155_DEPLOY_SSH_IDENTITY_MISMATCH; exit 2; }
printf '%s\n' '[92.113.19.189]:65002 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAf8M2EVwq0oJI8I9KZ0NFE8P8yDOvDATEhkQti/Kk/0' > "$tmp/known_hosts"
cp "$release_dir/$version/$exe" "$tmp/$exe"
cp "$release_dir/$version/manifest.json" "$tmp/manifest.json"
cp "$release_dir/$version/manifest.json.sig" "$tmp/manifest.json.sig"
cp "$release_dir/latest.json" "$tmp/latest.json"
cp "$release_dir/latest.json.sig" "$tmp/latest.json.sig"
(cd "$tmp"; sha256sum "$exe" manifest.json manifest.json.sig latest.json latest.json.sig > SHA256SUMS.txt)
ssh_remote "set -eu; test -d '$root'; test ! -L '$root'; test ! -e '$remote_root'; mkdir -m 700 '$remote_root'"
stage_created=1
for file in "$exe" manifest.json manifest.json.sig latest.json latest.json.sig SHA256SUMS.txt; do
  scp -P 65002 -i "$tmp/key" -o BatchMode=yes -o IdentitiesOnly=yes \
    -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$tmp/known_hosts" \
    -o GlobalKnownHostsFile=/dev/null "$tmp/$file" "$target:$remote_root/$file"
done
ssh_remote "bash -s -- '$root' '$remote_root' '$version' '$sequence' '$exe'" <<'REMOTE'
set -euo pipefail
root="$1"; stage="$2"; version="$3"; seq="$4"; exe="$5"
dest="$root/CELIKOM/Windows/Updates/stable"
(cd "$stage"; sha256sum -c SHA256SUMS.txt)
for d in "$root" "$root/CELIKOM" "$root/CELIKOM/Windows" \
  "$root/CELIKOM/Windows/Updates" "$dest" "$dest/$version"; do
  if [[ -e "$d" && ( -L "$d" || ! -d "$d" ) ]]; then
    echo W155_RELEASE_DIRECTORY_UNSAFE; exit 3
  fi
done
mkdir -p "$dest/$version"
if [[ -e "$dest/latest.json" || -e "$dest/latest.json.sig" ]]; then
  [[ -f "$dest/latest.json" && -f "$dest/latest.json.sig" &&
     ! -L "$dest/latest.json" && ! -L "$dest/latest.json.sig" ]] || {
    echo W155_EXISTING_LATEST_BROKEN; exit 3; }
  old="$(sed -nE 's/^ *"sequence" *: *([0-9]+),? *$/\1/p' "$dest/latest.json" | head -1)"
  [[ "$old" =~ ^[1-9][0-9]{0,14}$ ]] || { echo W155_EXISTING_SEQUENCE_INVALID; exit 3; }
  (( seq > old )) || { echo W155_SEQUENCE_NOT_INCREASING; exit 3; }
fi
for file in "$exe" manifest.json manifest.json.sig; do
  if [[ -e "$dest/$version/$file" ]]; then
    [[ -f "$dest/$version/$file" && ! -L "$dest/$version/$file" ]] &&
      cmp -s "$stage/$file" "$dest/$version/$file" || {
      echo W155_IMMUTABLE_RELEASE_CONFLICT; exit 3; }
  else
    mv "$stage/$file" "$dest/$version/$file"
  fi
  chmod 644 "$dest/$version/$file"
done
# Immutable package + manifest are available BEFORE the advertised latest.
mv -f "$stage/latest.json" "$dest/latest.json"
mv -f "$stage/latest.json.sig" "$dest/latest.json.sig"
chmod 644 "$dest/latest.json" "$dest/latest.json.sig"
chmod 755 "$dest" "$dest/$version"
echo W155_SIGNED_STABLE_REMOTE_PUBLISHED
REMOTE
for file in "$exe" manifest.json manifest.json.sig latest.json latest.json.sig; do
  case "$file" in latest.json|latest.json.sig) suffix="$file";;
    *) suffix="$version/$file";; esac
  curl --fail --silent --show-error --max-time 30 \
    "$origin/CELIKOM/Windows/Updates/stable/$suffix" -o "$tmp/checked-$file"
  cmp -s "$tmp/$file" "$tmp/checked-$file" || {
    echo W155_OFFICIAL_HTTPS_PUBLICATION_MISMATCH; exit 4; }
done
echo W155_OFFICIAL_HTTPS_SIGNED_RELEASE_VERIFIED
