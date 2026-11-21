#!/usr/bin/env bash
set -euo pipefail
umask 077
: "${HOSTINGER_SSH_KEY:?}"
: "${GITHUB_SHA:?}"
test -f dist/upload-cleanup.tar.gz
archive_hash=$(sha256sum dist/upload-cleanup.tar.gz | awk '{print $1}')
id="upload-cleanup-${GITHUB_SHA:0:12}"
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
scp -P 65002 "${opts[@]}" dist/upload-cleanup.tar.gz "$target:$root/incoming/$id/payload.tar.gz"
ssh -p 65002 "${opts[@]}" "$target" "bash -s -- '$id' '$archive_hash'" <<'REMOTE'
set -euo pipefail
umask 077
id=$1
archive_hash=$2
[[ "$id" =~ ^upload-cleanup-[a-f0-9]{12}$ && "$archive_hash" =~ ^[a-f0-9]{64}$ ]]
root=/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom
php=/opt/alt/php83/usr/bin/php
input="$root/incoming/$id"
candidate="$root/releases/$id"
backup="$root/backups/$id"
public_index="$(dirname "$root")/public_html/index.php"
test "$(sha256sum "$input/payload.tar.gz" | awk '{print $1}')" = "$archive_hash"
mkdir -p "$input/payload"
tar -xzf "$input/payload.tar.gz" -C "$input/payload"
(cd "$input/payload" && sha256sum --check payload.sha256)
old=$(readlink -f "$root/current")
[[ "$old" == "$root/releases/"* ]]
test "$(sha256sum "$old/src/Application/UploadService.php" | awk '{print $1}')" = 'dd4ec0501fb88b06e5aaf8d423fe83581fc7321207138cb0cdcad3128ab95c7b'
test "$(sha256sum "$old/src/Application/Mp3Inspector.php" | awk '{print $1}')" = '0485502c2488a1125bd4b5d898133f68f7fb870914626d9659b330ee9f122a25'
test ! -e "$old/src/Application/Mp3Normalizer.php"
test ! -e "$old/src/Application/Mp3DecodeValidator.php"
test ! -e "$old/tools/mp3-validator"
test ! -e "$candidate" && test ! -e "$backup"
env_hash=$(sha256sum "$root/shared/env" | awk '{print $1}')
public_hash=$(sha256sum "$public_index" | awk '{print $1}')
mkdir "$candidate" "$backup"
cp -a "$old/." "$candidate/"
printf '%s\n' "$old" > "$backup/previous-release"
cp -p "$old/src/Application/UploadService.php" "$backup/UploadService.php"
cp -p "$public_index" "$backup/public-index.php"
cp "$input/payload/UploadService.php" "$candidate/src/Application/UploadService.php"
cp "$input/payload/Mp3Normalizer.php" "$candidate/src/Application/Mp3Normalizer.php"
cp "$input/payload/Mp3DecodeValidator.php" "$candidate/src/Application/Mp3DecodeValidator.php"
mkdir -p "$candidate/tools"
for file in mp3-validator LICENSE.LGPLv2.1 source.tar.gz; do
 test ! -e "$candidate/tools/$file"
 cp "$input/payload/$file" "$candidate/tools/$file"
done
chmod 700 "$candidate/tools/mp3-validator"
for file in UploadService Mp3Normalizer Mp3DecodeValidator; do "$php" -l "$candidate/src/Application/$file.php"; done
"$php" -r '
$scan=static function(string $root):array{$out=[];$it=new RecursiveIteratorIterator(new RecursiveDirectoryIterator($root,FilesystemIterator::SKIP_DOTS));foreach($it as $entry){$name=substr($entry->getPathname(),strlen($root)+1);$out[$name]=$entry->isLink()?"link:".readlink($entry->getPathname()):hash_file("sha256",$entry->getPathname());}return $out;};
$a=$scan($argv[1]);$b=$scan($argv[2]);$allowed=["src/Application/UploadService.php","src/Application/Mp3Normalizer.php","src/Application/Mp3DecodeValidator.php","tools/mp3-validator","tools/LICENSE.LGPLv2.1","tools/source.tar.gz"];
foreach(array_unique(array_merge(array_keys($a),array_keys($b)))as $name)if(($a[$name]??null)!==($b[$name]??null)&&!in_array($name,$allowed,true))exit(1);echo "UPLOAD_CLEANUP_ONLY_DELTA_PASS\n";
' "$old" "$candidate"
"$php" "$input/payload/smoke.php" "$candidate" "$input/payload"
test "$(readlink -f "$root/current")" = "$old"
rollback(){
 status=$?
 if [[ "$status" != 0 && "$(readlink -f "$root/current")" == "$candidate" ]]; then
  ln -s "$old" "$root/.upload-cleanup-rollback-$id"
  mv -Tf "$root/.upload-cleanup-rollback-$id" "$root/current"
  touch -r "$backup/public-index.php" "$public_index"
  echo UPLOAD_CLEANUP_ROLLBACK_COMPLETE
 fi
 exit "$status"
}
trap rollback EXIT
ln -s "$candidate" "$root/.upload-cleanup-current-$id"
mv -Tf "$root/.upload-cleanup-current-$id" "$root/current"
touch "$public_index"
sleep 3
"$php" "$input/payload/smoke.php" "$candidate" "$input/payload"
test "$(sha256sum "$root/shared/env" | awk '{print $1}')" = "$env_hash"
test "$(sha256sum "$public_index" | awk '{print $1}')" = "$public_hash"
curl --fail --silent --show-error https://darkred-camel-588676.hostingersite.com/api/v1/config -o /dev/null
echo UPLOAD_CLEANUP_ACTIVE_OTHER_COMPONENTS_PRESERVED
REMOTE
