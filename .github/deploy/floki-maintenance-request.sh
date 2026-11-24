#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
S=/srv/celikom/app/staging-20261122
D=/srv/celikom-releases/private/runtime-tools
A=ffmpeg-7.1.5-2f5e4b9521db2ae309e5c2dd6e409fab27e1ad99.tar.gz
archive_sha=82ce458e07914714c28028caed59326d1ac1b97fdf800201934162cc9434ff69
validator_sha=d9c6e49ef3246c77a112a0832a44a179f28fd0f0b147bd10572b2b79ab2d2939
printf '%s  %s\n' "$archive_sha" "$S/tools/source.tar.gz" | sha256sum -c -
printf '%s  %s\n' "$validator_sha" "$S/tools/mp3-validator" | sha256sum -c -
gzip -t "$S/tools/source.tar.gz"
test -d /srv/celikom-releases/private
if [[ ! -e "$D" ]]; then install -d -o root -g root -m 700 "$D"; fi
[[ -d "$D" && ! -L "$D" && $(stat -c '%u:%a' "$D") == 0:700 ]]
if [[ ! -e "$D/$A" ]]; then install -o root -g root -m 600 "$S/tools/source.tar.gz" "$D/$A"; fi
[[ -f "$D/$A" && ! -L "$D/$A" && $(stat -c '%u:%a:%s' "$D/$A") == 0:600:15948344 ]]
printf '%s  %s\n' "$archive_sha" "$D/$A" | sha256sum -c -
gzip -t "$D/$A"
echo CELIKOM_MATCHING_FFMPEG_SOURCE_PRESERVED
work=$(mktemp -d /tmp/celikom-mp3-check.XXXXXXXX)
trap 'rm -rf -- "$work"' EXIT
chgrp www-data "$work"
chmod 750 "$work"
install -d -o root -g www-data -m 750 "$work/tools" "$work/src" "$work/src/Application"
install -o root -g www-data -m 750 "$S/tools/mp3-validator" "$work/tools/mp3-validator"
install -o root -g www-data -m 660 /dev/null "$work/tools/decode-slot-0.lock"
install -o root -g www-data -m 660 /dev/null "$work/tools/decode-slot-1.lock"
for f in Mp3DecodeValidator.php Mp3Normalizer.php Mp3Inspector.php; do
  install -o root -g www-data -m 640 "$S/src/Application/$f" "$work/src/Application/$f"
  php -l "$work/src/Application/$f"
done
runuser -u www-data -- test -x "$work/tools/mp3-validator"
runuser -u www-data -- test ! -w "$work/tools"
runuser -u www-data -- test ! -w "$work/tools/mp3-validator"
runuser -u www-data -- test -w "$work/tools/decode-slot-0.lock"
runuser -u www-data -- test -w "$work/tools/decode-slot-1.lock"
runuser -u www-data -- "$work/tools/mp3-validator" -version | sed -n '1,3p'
echo CELIKOM_MP3_RUNTIME_ISOLATED_PERMISSIONS_PASS
if command -v ffmpeg >/dev/null && ffmpeg -hide_banner -encoders 2>/dev/null | grep -F libmp3lame >/dev/null; then
  ffmpeg -hide_banner -loglevel error -f lavfi -i sine=frequency=440:sample_rate=44100 -t 2.612 -ac 1 -c:a libmp3lame -b:a 128k -write_xing 0 -id3v2_version 0 "$work/synthetic.mp3"
  chgrp www-data "$work/synthetic.mp3"
  chmod 640 "$work/synthetic.mp3"
  runuser -u www-data -- php -r '
  require $argv[1]."/src/Application/Mp3Inspector.php";
  require $argv[1]."/src/Application/Mp3Normalizer.php";
  require $argv[1]."/src/Application/Mp3DecodeValidator.php";
  $p=(new Celikom\Application\Mp3Normalizer())->prepare($argv[1]."/synthetic.mp3");
  try {
      (new Celikom\Application\Mp3DecodeValidator())->check($p["path"]);
      echo "SYNTHETIC_MP3_DECODE_PASS duration_ms=",$p["duration_ms"]," size=",$p["size"],PHP_EOL;
  } finally { unlink($p["path"]); }
  ' "$work"
else
  echo SYNTHETIC_MP3_DECODE_DEFERRED_TO_CI_ENCODER_NOT_INSTALLED
fi
echo CELIKOM_RUNTIME_ARCHIVE_AND_ISOLATED_VALIDATOR_CHECK_OK
