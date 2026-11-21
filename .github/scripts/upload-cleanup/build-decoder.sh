#!/usr/bin/env bash
set -euo pipefail
root=$(pwd)
mkdir -p dist/validator
curl --fail --location --retry 3 https://codeload.github.com/FFmpeg/FFmpeg/tar.gz/2f5e4b9521db2ae309e5c2dd6e409fab27e1ad99 -o dist/validator/source.tar.gz
docker run --rm -v "$root/dist/validator:/build" alpine:3.22 sh -ec '
  apk add --no-cache build-base linux-headers
  cd /build
  mkdir source
  tar -xzf source.tar.gz -C source --strip-components=1
  cd source
  ./configure --disable-everything --disable-autodetect --disable-network --disable-doc --disable-debug --disable-x86asm --disable-shared --enable-static --extra-ldflags=-static --enable-ffmpeg --disable-ffplay --disable-ffprobe --enable-decoder=mp3float --enable-demuxer=mp3 --enable-protocol=file --enable-muxer=null --enable-encoder=pcm_s16le --enable-filter=anull,aresample --enable-swresample
  make -j2 ffmpeg
  cp ffmpeg /build/mp3-validator
  strip /build/mp3-validator
  cp COPYING.LGPLv2.1 /build/LICENSE.LGPLv2.1
'
dist/validator/mp3-validator -version | head -3
sha256sum dist/validator/mp3-validator > dist/validator/mp3-validator.sha256
