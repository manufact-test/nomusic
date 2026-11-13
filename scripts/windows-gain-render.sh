#!/usr/bin/env bash
# W91: OFFLINE/LOCAL ONLY, no remote deployment. Never overwrite original media.
set -euo pipefail
[[ "$#" -eq 3 ]] || { echo 'usage: windows-gain-render.sh INPUT.mp3 OUTPUT.mp3 GAIN_DB' >&2; exit 2; }
input="$1"; output="$2"; gain="$3"
[[ "$gain" =~ ^-?[0-9]{1,2}(\.[0-9])?$ ]] || { echo 'invalid gain' >&2; exit 2; }
awk -v g="$gain" 'BEGIN {if(g < -12 || g > 12 || g == 0) exit 1}' ||
  { echo 'gain must be nonzero and within -12..12' >&2; exit 2; }
command -v ffmpeg >/dev/null && command -v ffprobe >/dev/null ||
  { echo 'offline ffmpeg+ffprobe required' >&2; exit 2; }
[[ -f "$input" && ! -e "$output" && "$input" != "$output" ]] ||
  { echo 'missing source or output already exists' >&2; exit 2; }
[[ "$output" == *.mp3 ]] || { echo 'output must be MP3' >&2; exit 2; }
tmp="${output}.tmp.$$.mp3"
trap 'rm -f "$tmp"' EXIT
# Same native Yandex MP3 decoder; limiter prevents huge instantaneous peaks.
# Fixed +dB for quiet sections, attack/release bounds for transient peaks.
ffmpeg -nostdin -hide_banner -loglevel error -i "$input" -map 0:a:0 -vn \
  -af "volume=${gain}dB,alimiter=limit=0.98:attack=5:release=100:level=0" \
  -c:a libmp3lame -b:a 256k -ar 44100 -ac 2 -map_metadata -1 -y "$tmp"
before="$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$input")"
after="$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$tmp")"
awk -v a="$before" -v b="$after" 'BEGIN {d=a-b;if(d<0)d=-d;if(d>1.5)exit 1}' ||
  { echo 'duration mismatch > 1500ms' >&2; exit 3; }
[[ "$(wc -c < "$tmp")" -ge 1024 && "$(wc -c < "$tmp")" -le 31457280 ]] ||
  { echo 'rendered file is outside private audio size contract' >&2; exit 3; }
mv -n "$tmp" "$output"
sha256sum "$output" | awk '{print "W91_RENDER_SHA256=" $1}'
echo "W91_OFFLINE_GAIN_RENDER_READY_NOT_UPLOADED"
