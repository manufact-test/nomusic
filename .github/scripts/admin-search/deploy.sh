#!/usr/bin/env bash
set -euo pipefail
umask 077
: "${HOSTINGER_SSH_KEY:?}"
: "${GITHUB_SHA:?}"
mkdir -p dist/admin-song-search
cp .github/scripts/admin-search/{patch.php,smoke.php,manifest.json} dist/admin-song-search/
tar -czf dist/admin-song-search.tar.gz -C dist/admin-song-search .
archive_hash=$(sha256sum dist/admin-song-search.tar.gz | awk '{print $1}')
id="admin-song-search-${GITHUB_SHA:0:12}"
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
ssh -p 65002 "${opts[@]}" "$target" "umask 077; mkdir -p '$root/incoming/$id'"
scp -P 65002 "${opts[@]}" dist/admin-song-search.tar.gz "$target:$root/incoming/$id/payload.tar.gz"
ssh -p 65002 "${opts[@]}" "$target" "bash -s -- '$id' '$archive_hash'" <<'REMOTE'
set -euo pipefail
umask 077
id=$1
archive_hash=$2
[[ "$id" =~ ^admin-song-search-[a-f0-9]{12}$ && "$archive_hash" =~ ^[a-f0-9]{64}$ ]]
root=/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom
php=/opt/alt/php83/usr/bin/php
input="$root/incoming/$id"
candidate="$root/releases/$id"
backup="$root/backups/$id"
view=src/Admin/AdminPanel.php
public_index="$(dirname "$root")/public_html/index.php"
test "$(sha256sum "$input/payload.tar.gz" | awk '{print $1}')" = "$archive_hash"
mkdir -p "$input/payload"
tar -xzf "$input/payload.tar.gz" -C "$input/payload"
before=$("$php" -r 'echo json_decode(file_get_contents($argv[1]),true,8,JSON_THROW_ON_ERROR)["before"];' "$input/payload/manifest.json")
after=$("$php" -r 'echo json_decode(file_get_contents($argv[1]),true,8,JSON_THROW_ON_ERROR)["after"];' "$input/payload/manifest.json")
[[ "$before" =~ ^[a-f0-9]{64}$ && "$after" =~ ^[a-f0-9]{64}$ ]]

old=$(readlink -f "$root/current")
[[ "$old" == "$root/releases/"* ]]
if [[ "$old" == "$candidate" ]]; then
  "$php" "$input/payload/smoke.php" "$id" active
  exit 0
fi
test "$(sha256sum "$old/$view" | awk '{print $1}')" = "$before"
test ! -e "$candidate" && test ! -e "$backup"
env_hash=$(sha256sum "$root/shared/env" | awk '{print $1}')
public_hash=$(sha256sum "$public_index" | awk '{print $1}')
mkdir "$candidate" "$backup"
cp -a "$old/." "$candidate/"
printf '%s\n' "$old" > "$backup/previous-release"
cp -p "$old/$view" "$backup/AdminPanel.php"
cp -p "$public_index" "$backup/public-index.php"
"$php" "$input/payload/patch.php" "$candidate/$view" "$input/payload/manifest.json"
test "$(sha256sum "$candidate/$view" | awk '{print $1}')" = "$after"
"$php" -l "$candidate/$view"
"$php" -r '
$scan=static function(string $root):array{$out=[];$it=new RecursiveIteratorIterator(new RecursiveDirectoryIterator($root,FilesystemIterator::SKIP_DOTS));foreach($it as $entry){$name=substr($entry->getPathname(),strlen($root)+1);$out[$name]=$entry->isLink()?"link:".readlink($entry->getPathname()):hash_file("sha256",$entry->getPathname());}return $out;};
$a=$scan($argv[1]);$b=$scan($argv[2]);foreach(array_unique(array_merge(array_keys($a),array_keys($b)))as $name)if(($a[$name]??null)!==($b[$name]??null)&&$name!=="src/Admin/AdminPanel.php")exit(1);echo "ADMIN_SEARCH_SINGLE_FILE_PASS\n";
' "$old" "$candidate"
"$php" "$input/payload/smoke.php" "$id" candidate
test "$(readlink -f "$root/current")" = "$old"
rollback(){
 status=$?
 if [[ "$status" != 0 && "$(readlink -f "$root/current")" == "$candidate" ]]; then
  ln -s "$old" "$root/.admin-search-rollback-$id"
  mv -Tf "$root/.admin-search-rollback-$id" "$root/current"
  touch -r "$backup/public-index.php" "$public_index"
  echo ADMIN_SEARCH_ROLLBACK_COMPLETE
 fi
 exit "$status"
}
trap rollback EXIT
ln -s "$candidate" "$root/.admin-search-current-$id"
mv -Tf "$root/.admin-search-current-$id" "$root/current"
touch "$public_index"
sleep 3
"$php" "$input/payload/smoke.php" "$id" active
test "$(sha256sum "$root/shared/env" | awk '{print $1}')" = "$env_hash"
test "$(sha256sum "$public_index" | awk '{print $1}')" = "$public_hash"
echo ADMIN_SEARCH_ACTIVE_OTHER_COMPONENTS_PRESERVED
REMOTE
