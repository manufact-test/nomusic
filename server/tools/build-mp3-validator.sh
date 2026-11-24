#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
archive="${1:?Usage: build-mp3-validator.sh /path/to/ffmpeg-source.tar.gz}"
expected=82ce458e07914714c28028caed59326d1ac1b97fdf800201934162cc9434ff69
printf '%s  %s\n' "$expected" "$archive" | sha256sum --check --status
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
tar -xzf "$archive" -C "$work"
source="$work/FFmpeg-2f5e4b9521db2ae309e5c2dd6e409fab27e1ad99"
test -x "$source/configure"
(
  cd "$source"
  ./configure \
    --disable-everything \
    --disable-autodetect \
    --disable-network \
    --disable-doc \
    --disable-debug \
    --disable-x86asm \
    --disable-shared \
    --enable-static \
    --extra-ldflags=-static \
    --enable-ffmpeg \
    --disable-ffplay \
    --disable-ffprobe \
    --enable-decoder=mp3float \
    --enable-demuxer=mp3 \
    --enable-protocol=file \
    --enable-muxer=null \
    --enable-encoder=pcm_s16le \
    --enable-filter=anull,aresample \
    --enable-swresample
  make -j"${JOBS:-2}" ffmpeg
  strip ffmpeg
  install -m 0755 ffmpeg "$(cd "$(dirname "$0")" && pwd)/mp3-validator"
)
sha256sum "$(cd "$(dirname "$0")" && pwd)/mp3-validator"
