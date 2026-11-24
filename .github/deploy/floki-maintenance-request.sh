#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
STAGE=/srv/celikom/app/staging-20261122
LIVE=/srv/celikom/migration/hostinger-import/live-release
FILES=(
 "server/src/Admin/AdminPanel.php|$STAGE/src/Admin/AdminPanel.php"
 "server/src/Admin/ModerationService.php|$STAGE/src/Admin/ModerationService.php"
 "server/src/Admin/admin-style.css|$STAGE/src/Admin/admin-style.css"
 "server/src/Admin/BulkModerationService.php|$STAGE/src/Admin/BulkModerationService.php"
 "server/src/Admin/BulkModerationView.php|$STAGE/src/Admin/BulkModerationView.php"
 "server/src/Admin/bulk-moderation.js|$STAGE/src/Admin/bulk-moderation.js"
 "server/src/Application/UploadService.php|$STAGE/src/Application/UploadService.php"
 "server/src/Application/Mp3DecodeValidator.php|$STAGE/src/Application/Mp3DecodeValidator.php"
 "server/src/Application/Mp3Normalizer.php|$STAGE/src/Application/Mp3Normalizer.php"
 "server/tools/LICENSE.LGPLv2.1|$STAGE/tools/LICENSE.LGPLv2.1"
 "server/tools/mp3-validator|$LIVE/tools/mp3-validator"
)
for item in "${FILES[@]}"; do
  rel=${item%%|*}; file=${item#*|}
  [[ -f "$file" && ! -L "$file" ]] || { echo "SOURCE_FILE_NOT_REGULAR $rel"; exit 1; }
  size=$(stat -c %s "$file")
  sha=$(sha256sum "$file" | cut -d' ' -f1)
  printf 'CELIKOM_SOURCE_FILE|%s|%s|%s\n' "$rel" "$size" "$sha"
  b64=$(base64 -w0 "$file")
  n=${#b64}
  index=1
  for ((offset=0; offset<n; offset+=24000)); do
    chunk=${b64:offset:24000}
    printf 'CELIKOM_B64|%s|%04d|%s\n' "$rel" "$index" "$chunk"
    ((index+=1))
  done
  printf 'CELIKOM_B64_END|%s|%s\n' "$rel" "$index"
done
echo CELIKOM_HOSTINGER_SOURCE_EXPORT_COMPLETE
