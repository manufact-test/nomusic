#!/usr/bin/env bash
set -euo pipefail
umask 077
: "${HOSTINGER_SSH_KEY:?}"
: "${GITHUB_SHA:?}"
mkdir -p dist/admin-bulk-restore
cp .github/scripts/admin-bulk-restore/{install.php,smoke.php,manifest.json} dist/admin-bulk-restore/
cp server/src/Admin/{AdminPanel.php,ModerationService.php,BulkModerationService.php,BulkModerationView.php,bulk-moderation.js,admin-style.css} dist/admin-bulk-restore/
tar -czf dist/admin-bulk-restore.tar.gz -C dist/admin-bulk-restore .
archive_hash=$(sha256sum dist/admin-bulk-restore.tar.gz | awk '{print $1}')
id="admin-bulk-restore-${GITHUB_SHA:0:12}"
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
scp -P 65002 "${opts[@]}" dist/admin-bulk-restore.tar.gz "$target:$root/incoming/$id/payload.tar.gz"
ssh -p 65002 "${opts[@]}" "$target" "bash -s -- '$id' '$archive_hash'" <<'REMOTE'
set -euo pipefail
umask 077
id=$1
archive_hash=$2
[[ "$id" =~ ^admin-bulk-restore-[a-f0-9]{12}$ && "$archive_hash" =~ ^[a-f0-9]{64}$ ]]
root=/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom
php=/opt/alt/php83/usr/bin/php
input="$root/incoming/$id"
candidate="$root/releases/$id"
backup="$root/backups/$id"
public_index="$(dirname "$root")/public_html/index.php"
test "$(sha256sum "$input/payload.tar.gz" | awk '{print $1}')" = "$archive_hash"
mkdir -p "$input/payload"
tar -xzf "$input/payload.tar.gz" -C "$input/payload"
old=$(readlink -f "$root/current")
[[ "$old" == "$root/releases/"* ]]
test ! -e "$candidate" && test ! -e "$backup"
env_hash=$(sha256sum "$root/shared/env" | awk '{print $1}')
public_hash=$(sha256sum "$public_index" | awk '{print $1}')
mkdir "$candidate" "$backup"
cp -a "$old/." "$candidate/"
printf '%s\n' "$old" > "$backup/previous-release"
cp -a "$old/src/Admin" "$backup/Admin"
cp -p "$public_index" "$backup/public-index.php"
"$php" "$input/payload/install.php" "$candidate" "$input/payload"
for name in AdminPanel ModerationService BulkModerationService BulkModerationView; do "$php" -l "$candidate/src/Admin/$name.php"; done
"$php" -r '
$scan=static function(string $root):array{$out=[];$it=new RecursiveIteratorIterator(new RecursiveDirectoryIterator($root,FilesystemIterator::SKIP_DOTS));foreach($it as $entry){$name=substr($entry->getPathname(),strlen($root)+1);$out[$name]=$entry->isLink()?"link:".readlink($entry->getPathname()):hash_file("sha256",$entry->getPathname());}return $out;};
$a=$scan($argv[1]);$b=$scan($argv[2]);foreach(array_unique(array_merge(array_keys($a),array_keys($b)))as $name)if(($a[$name]??null)!==($b[$name]??null)&&!in_array($name,["src/Admin/AdminPanel.php","src/Admin/ModerationService.php","src/Admin/BulkModerationService.php","src/Admin/BulkModerationView.php","src/Admin/bulk-moderation.js","src/Admin/admin-style.css"],true))exit(1);echo "ADMIN_BULK_RESTORE_SINGLE_FILE_PASS\n";
' "$old" "$candidate"
"$php" "$input/payload/smoke.php" "$candidate" candidate
test "$(readlink -f "$root/current")" = "$old"
rollback(){
 status=$?
 if [[ "$status" != 0 && "$(readlink -f "$root/current")" == "$candidate" ]]; then
  ln -s "$old" "$root/.admin-search-rollback-$id"
  mv -Tf "$root/.admin-search-rollback-$id" "$root/current"
  touch -r "$backup/public-index.php" "$public_index"
  echo ADMIN_BULK_RESTORE_ROLLBACK_COMPLETE
 fi
 exit "$status"
}
trap rollback EXIT
ln -s "$candidate" "$root/.admin-search-current-$id"
mv -Tf "$root/.admin-search-current-$id" "$root/current"
touch "$public_index"
sleep 3
"$php" "$input/payload/smoke.php" "$candidate" active
test "$(sha256sum "$root/shared/env" | awk '{print $1}')" = "$env_hash"
test "$(sha256sum "$public_index" | awk '{print $1}')" = "$public_hash"
echo ADMIN_BULK_RESTORE_ACTIVE_OTHER_COMPONENTS_PRESERVED
REMOTE
