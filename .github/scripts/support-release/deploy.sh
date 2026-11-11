#!/usr/bin/env bash
set -euo pipefail
umask 077
: "${HOSTINGER_SSH_KEY:?}"
: "${GITHUB_SHA:?}"
python3 .github/scripts/support-release/build-payload.py
tar -czf dist/browser-support-payload.tar.gz -C dist/browser-support-payload .
payload_hash=$(sha256sum dist/browser-support-payload.tar.gz | awk '{print $1}')
release_id="browser-support-076-${GITHUB_SHA:0:12}"
key_dir=$(mktemp -d)
trap 'rm -rf "$key_dir"' EXIT
printf '%s\n' "$HOSTINGER_SSH_KEY" | tr -d '\r' > "$key_dir/key"
chmod 600 "$key_dir/key"
ssh-keygen -y -P '' -f "$key_dir/key" > "$key_dir/key.pub"
test "$(ssh-keygen -lf "$key_dir/key.pub" -E sha256 | awk '{print $2}')" = 'SHA256:Q6FyifXRq6garceQdIIjBmXhkk81Ic1p/x9JTSYHWUk'
printf '%s\n' '[92.113.19.189]:65002 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAf8M2EVwq0oJI8I9KZ0NFE8P8yDOvDATEhkQti/Kk/0' > "$key_dir/known_hosts"
opts=(-i "$key_dir/key" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$key_dir/known_hosts" -o GlobalKnownHostsFile=/dev/null -o ConnectTimeout=15)
target=u235811320@92.113.19.189
root=/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom
ssh -p 65002 "${opts[@]}" "$target" "umask 077; mkdir -p '$root/incoming/$release_id'"
scp -P 65002 "${opts[@]}" dist/browser-support-payload.tar.gz "$target:$root/incoming/$release_id/payload.tar.gz"
ssh -p 65002 "${opts[@]}" "$target" "bash -s -- '$release_id' '$payload_hash'" <<'REMOTE'
set -euo pipefail
umask 077
id=$1
archive_hash=$2
[[ "$id" =~ ^browser-support-076-[a-f0-9]{12}$ ]]
[[ "$archive_hash" =~ ^[a-f0-9]{64}$ ]]
root=/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom
php=/opt/alt/php83/usr/bin/php
candidate="$root/releases/$id"
input="$root/incoming/$id"
backup="$root/backups/$id"
test "$(sha256sum "$input/payload.tar.gz" | awk '{print $1}')" = "$archive_hash"
mkdir "$input/payload"
tar -xzf "$input/payload.tar.gz" -C "$input/payload"
old=$(readlink -f "$root/current")
[[ "$old" == "$root/releases/"* ]]
if [[ "$old" == "$candidate" ]]; then
  "$php" "$input/payload/smoke.php" "$id"
  echo SUPPORT_ALREADY_ACTIVE_VERIFIED
  exit 0
fi
test ! -e "$candidate" && test ! -e "$backup"
# Source hashes are checked again by patch.php on the clone before any activation.
env_hash=$(sha256sum "$root/shared/env" | awk '{print $1}')
mkdir -p "$candidate" "$backup"
cp -a "$old/." "$candidate/"
printf '%s\n' "$old" > "$backup/previous-release"
cp "$input/payload/manifest.json" "$backup/manifest.json"
for path in src/Application.php src/Admin/AdminPanel.php src/Support/SongReport.php src/Support/SupportService.php src/Support/SupportAdminView.php; do
  mkdir -p "$backup/$(dirname "$path")"
  cp -p "$old/$path" "$backup/$path"
done
"$php" "$input/payload/patch.php" "$candidate" "$input/payload" "$input/payload/manifest.json"
for path in src/Application.php src/Admin/AdminPanel.php src/Support/SongReport.php src/Support/SupportService.php src/Support/SupportAdminView.php src/Support/SupportReport.php src/Support/WindowsSupportDiagnostics.php; do
  "$php" -l "$candidate/$path"
done
# No unrelated server file, environment file or symlink may have changed.
"$php" -r '
$old=$argv[1];$next=$argv[2];$allowed=array_keys(json_decode(file_get_contents($argv[3]),true)["files"]);
$walk=static function(string $root):array {$out=[];$iterator=new RecursiveIteratorIterator(new RecursiveDirectoryIterator($root,FilesystemIterator::SKIP_DOTS));foreach($iterator as $entry){$name=substr($entry->getPathname(),strlen($root)+1);$out[$name]=$entry->isLink()?"link:".readlink($entry->getPathname()):hash_file("sha256",$entry->getPathname());}return $out;};
$a=$walk($old);$b=$walk($next);foreach(array_unique(array_merge(array_keys($a),array_keys($b))) as $name){if(($a[$name]??null)!==($b[$name]??null)&&!in_array($name,$allowed,true))exit(12);}echo "SUPPORT_ONLY_FILE_DELTA_PASS\n";
' "$old" "$candidate" "$input/payload/manifest.json"
test "$(readlink -f "$root/current")" = "$old"
active=0
rollback(){
  status=$?
  if [[ "$active" == 1 && "$status" != 0 && "$(readlink -f "$root/current")" == "$candidate" ]]; then
    ln -s "$old" "$root/.support-rollback-$id"
    mv -Tf "$root/.support-rollback-$id" "$root/current"
    echo SUPPORT_AUTOMATIC_ROLLBACK_COMPLETE
  fi
  exit "$status"
}
trap rollback EXIT
ln -s "$candidate" "$root/.support-current-$id"
mv -Tf "$root/.support-current-$id" "$root/current"
active=1
"$php" "$input/payload/smoke.php" "$id"
test "$(sha256sum "$root/shared/env" | awk '{print $1}')" = "$env_hash"
test "$(readlink -f "$root/current")" = "$candidate"
echo SUPPORT_RELEASE_ACTIVE_ENV_PRESERVED
REMOTE
