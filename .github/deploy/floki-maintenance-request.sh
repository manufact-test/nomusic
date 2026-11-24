#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
S=/srv/celikom/app/staging-20261122
echo '=== Bulk moderation implementation ==='
for f in "$S/src/Admin/BulkModerationService.php" "$S/src/Admin/BulkModerationView.php" "$S/src/Admin/bulk-moderation.js"; do
 echo "FILE=$f"; sed -n '1,260p' "$f"
done
echo '=== MP3 normalization implementation ==='
for f in "$S/src/Application/Mp3Normalizer.php" "$S/src/Application/Mp3DecodeValidator.php"; do
 echo "FILE=$f"; sed -n '1,240p' "$f"
done
echo '=== Database dependencies ==='
grep -RInE 'bulk_moderation_tombstones|bulk_moderation|moderation_batch|replacement_id' "$S/migrations" "$S/src" | head -n 100
echo '=== FFmpeg validator binary static metadata (no execution) ==='
readelf -h "$S/tools/mp3-validator" | grep -E 'Class:|Machine:|Type:'
readelf -n "$S/tools/mp3-validator" | grep -A2 'Build ID' | head -n 4
strings "$S/tools/mp3-validator" | grep -E -m 15 'ffmpeg version|configuration:|libavcodec|LAME|mp3-validator|Copyright|LGPL|GPL' || true
echo '=== FFmpeg source archive root metadata ==='
tar -tzf "$S/tools/source.tar.gz" > /tmp/celikom-ffmpeg-source-list.txt
head -n 20 /tmp/celikom-ffmpeg-source-list.txt
tar -xOzf "$S/tools/source.tar.gz" FFmpeg-2f5e4b9521db2ae309e5c2dd6e409fab27e1ad99/LICENSE.md | head -n 80
echo '=== app.php exact differing mail-related lines only ==='
diff -u "$S/config/app.php" <(unzip -p /srv/celikom/ci-runner/runner/celikom-build-spool/d7537830c054a7878b080e21b9ea91e21e29bc56-45433182374-1/celikom-server-0.4.57.zip config/app.php) | grep -E '^[+-].*(mail|brevo|CELIKOM)' || true
echo CELIKOM_HOSTINGER_ONLY_SOURCE_REVIEW_OK
