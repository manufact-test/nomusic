#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
S=/srv/celikom/app/staging-20261122
echo '=== Stage-only code and dependency metadata ==='
for f in src/Admin/BulkModerationService.php src/Admin/BulkModerationView.php src/Admin/bulk-moderation.js src/Application/Mp3DecodeValidator.php src/Application/Mp3Normalizer.php tools/LICENSE.LGPLv2.1 tools/mp3-validator tools/source.tar.gz tools/decode-slot-0.lock; do
  p="$S/$f"
  [[ -e "$p" ]] || continue
  stat -c '%n type=%F mode=%a owner=%U:%G size=%s' "$p"
  sha256sum "$p"
  file "$p"
done
echo '=== PHP and JS syntax ==='
for f in "$S/src/Admin/BulkModerationService.php" "$S/src/Admin/BulkModerationView.php" "$S/src/Application/Mp3DecodeValidator.php" "$S/src/Application/Mp3Normalizer.php"; do php -l "$f"; done
node --check "$S/src/Admin/bulk-moderation.js"
echo '=== New component dependencies ==='
grep -RInE 'BulkModeration(Service|View)|Mp3(Normalizer|DecodeValidator)|mp3-validator|source\.tar\.gz|decode-slot' "$S/src" "$S/config" "$S/deploy" | head -n 100
echo '=== Validator executable metadata ==='
ldd "$S/tools/mp3-validator" 2>&1 | head -n 30 || true
timeout 5 "$S/tools/mp3-validator" --version 2>&1 | head -n 20 || true
echo '=== Source archive inventory ==='
tar -tzf "$S/tools/source.tar.gz" | head -n 80
echo '=== License header ==='
sed -n '1,28p' "$S/tools/LICENSE.LGPLv2.1"
echo '=== Root package version ==='
node -p "require('/srv/celikom/app/staging-20261122/../staging-20261122/package.json').version" 2>/dev/null || true
echo CELIKOM_STAGE_ONLY_COMPONENT_AUDIT_OK
