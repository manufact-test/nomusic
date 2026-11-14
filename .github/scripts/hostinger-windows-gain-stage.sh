#!/usr/bin/env bash
# W98: private, all-or-nothing offline Windows gain staging.
# Real audio exists only in this ephemeral runner's scratch directory; it is
# never committed, uploaded as an artifact, or printed to logs.
set -euo pipefail
umask 077

expected_branch='main'
[[ "${GITHUB_REF:-}" == "refs/heads/$expected_branch" ]] || {
  echo 'W98_WRONG_BRANCH_REF'; exit 2;
}
[[ "${GITHUB_SHA:-}" =~ ^[a-f0-9]{40}$ ]] || {
  echo 'W98_BAD_COMMIT_SHA'; exit 2;
}
[[ -n "${HOSTINGER_SSH_KEY:-}" ]] || {
  echo 'W98_NO_HOSTINGER_SSH_CREDENTIAL'; exit 2;
}
[[ -n "${CELIKOM_W98_TEST_EMAIL:-}" && ${#CELIKOM_W98_TEST_EMAIL} -le 254 ]] || {
  echo 'W98_EXPLICIT_OWNER_EMAIL_SECRET_REQUIRED'; exit 2;
}
command -v ssh >/dev/null && command -v scp >/dev/null &&
command -v ssh-keygen >/dev/null && command -v ffmpeg >/dev/null &&
command -v ffprobe >/dev/null && command -v node >/dev/null || {
  echo 'W98_REQUIRED_TOOL_MISSING'; exit 2;
}

port=65002
target='u235811320@92.113.19.189'
site='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom'
php_bin='/opt/alt/php83/usr/bin/php'
incoming="$site/incoming/windows-gain-$GITHUB_SHA"
helper_remote="$incoming/hostinger-windows-gain-remote.php"
stage_dir="$site/shared/audio/incoming/windows-gain"
backup_dir="$site/backups/windows-gain"
manifest_remote="$backup_dir/windows-gain-$GITHUB_SHA.json"

work="$(mktemp -d)"
success=0
remote_ready=0
: > "$work/attempted.tsv"
: > "$work/uploaded.tsv"
: > "$work/metrics.tsv"

cleanup() {
  local result=$?
  trap - EXIT
  if [[ "$remote_ready" -eq 1 && "$success" -ne 1 ]]; then
    if [[ -s "$work/attempted.tsv" && -n "${release:-}" ]]; then
      while IFS=$'\t' read -r id version gain source_sha render_sha; do
        [[ -n "$id" ]] || continue
        if ! remote "cd '$release' && CELIKOM_W93_ENABLE_ROLLBACK=YES_EXPLICIT_PRIVATE_ROLLBACK '$php_bin' '$release/bin/windows-gain-rollback.php' --replacement='$id' --source-sha='$source_sha' --source-version='$version' --gain-db='$gain' --render-sha='$render_sha'"; then
          echo "W98_ROLLBACK_FAILED replacement=$id"
          result=2
        fi
      done < "$work/attempted.tsv"
    fi
    if [[ -n "${manifest_remote:-}" ]]; then
      remote "rm -f '$manifest_remote'" >/dev/null 2>&1 || true
    fi
  fi
  if [[ "$remote_ready" -eq 1 && -s "$work/uploaded.tsv" ]]; then
    while IFS= read -r remote_file; do
      [[ -n "$remote_file" ]] || continue
      remote "rm -f '$remote_file'" >/dev/null 2>&1 || true
    done < "$work/uploaded.tsv"
  fi
  if [[ "$remote_ready" -eq 1 && -n "${helper_remote:-}" ]]; then
    remote "rm -f '$helper_remote'" >/dev/null 2>&1 || true
  fi
  rm -rf "$work"
  exit "$result"
}
trap cleanup EXIT

printf '%s\n' "$HOSTINGER_SSH_KEY" | tr -d '\r' > "$work/key"
ssh-keygen -y -P '' -f "$work/key" > "$work/pub"
fingerprint="$(ssh-keygen -lf "$work/pub" | awk '{print $2}')"
[[ "$fingerprint" == 'SHA256:Q6FyifXRq6garceQdIIjBmXhkk81Ic1p/x9JTSYHWUk' ]] || {
  echo 'W98_BAD_SSH_IDENTITY'; exit 2;
}
printf '%s\n' '[92.113.19.189]:65002 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAf8M2EVwq0oJI8I9KZ0NFE8P8yDOvDATEhkQti/Kk/0' > "$work/known_hosts"
ssh_opts=(-i "$work/key" -o BatchMode=yes -o IdentitiesOnly=yes
  -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$work/known_hosts"
  -o GlobalKnownHostsFile=/dev/null -o ConnectTimeout=15)
remote() {
  ssh -T -p "$port" "${ssh_opts[@]}" "$target" "$1"
}
copy_to_remote() {
  [[ "$2" != "$target:"* ]] || {
    echo 'W98_COPY_TARGET_ALREADY_PREFIXED'; return 2;
  }
  scp -P "$port" "${ssh_opts[@]}" "$1" "$target:$2"
}
remote_ready=1

remote "set -e; mkdir -p '$incoming' '$stage_dir' '$backup_dir'; chmod 700 '$incoming' '$stage_dir' '$backup_dir'; test ! -L '$incoming'; test ! -L '$stage_dir'; test ! -L '$backup_dir'"
release="$(remote "readlink -f '$site/current'")"
[[ "$release" == "$site"/releases/* && "$release" != *$'\n'* ]] || {
  echo 'W98_ACTIVE_RELEASE_PATH_REJECTED'; exit 2;
}
copy_to_remote "$GITHUB_WORKSPACE/.github/scripts/hostinger-windows-gain-remote.php" "$helper_remote"
remote "'$php_bin' '$helper_remote' prepare '$GITHUB_SHA'" | grep -F 'W98_PRIVATE_STAGE_READY' >/dev/null

remote "'$php_bin' '$helper_remote' inventory '$GITHUB_SHA'" > "$work/inventory.json"
node - "$work/inventory.json" "$work/rows.tsv" <<'NODE'
const fs = require('node:fs');
const data = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
if (data.schema_020 !== true || !Array.isArray(data.rows) ||
    data.count !== data.rows.length || data.count < 1 || data.count > 50) {
  throw new Error('W98_LIVE_GAIN_INVENTORY_REJECTED');
}
const rows = data.rows.map(row => {
  const id = String(row.replacement_id);
  const track = String(row.track_id);
  const version = String(row.version);
  const gain = String(row.gain_db);
  const source = String(row.source_sha256);
  const duration = String(row.duration_ms);
  const size = String(row.source_size_bytes);
  const staged = row.already_staged === true ? '1' : '0';
  const render = String(row.render_sha256 || '');
  const renderSize = String(row.render_size_bytes || 0);
  if (!/^[1-9][0-9]{0,17}$/.test(id) || !/^[1-9][0-9]{0,23}$/.test(track) ||
      !/^[1-9][0-9]{0,8}$/.test(version) || !/^-?[0-9]{1,2}(\.[0-9])?$/.test(gain) ||
      !/^[a-f0-9]{64}$/.test(source) || !/^\d+$/.test(duration) ||
      !/^\d+$/.test(size) || (staged === '1' && !/^[a-f0-9]{64}$/.test(render))) {
    throw new Error('W98_LIVE_GAIN_ROW_INVALID');
  }
  return [id,track,version,gain,source,duration,size,staged,render,renderSize].join('\t');
});
fs.writeFileSync(process.argv[3], rows.join('\n') + '\n', {mode:0o600});
NODE

count="$(wc -l < "$work/rows.tsv" | tr -d ' ')"
[[ "$count" -ge 1 && "$count" -le 50 ]] || {
  echo 'W98_ACTIVE_GAIN_COUNT_REJECTED'; exit 2;
}

while IFS=$'\t' read -r id track version gain source_sha duration_ms source_size already_staged render_sha render_size; do
  [[ -n "$id" ]] || continue
  if [[ "$already_staged" == "1" ]]; then
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$id" "$track" "$version" "$gain" "$source_sha" "$duration_ms" \
      "$render_sha" "$render_size" "existing" "" >> "$work/metrics.tsv"
    echo "W98_EXISTING_VARIANT_VERIFIED replacement=$id track=$track gain=${gain}dB"
    continue
  fi

  source_file="$work/source-$id.mp3"
  render_file="$work/render-$id.mp3"
  source_log="$work/source-decode-$id.log"
  render_log="$work/render-$id.log"
  input_meter="$work/input-meter-$id.log"
  output_meter="$work/output-meter-$id.log"

  remote "'$php_bin' '$helper_remote' source '$GITHUB_SHA' '$id' '$source_sha'" > "$source_file"
  actual_source_sha="$(sha256sum "$source_file" | awk '{print $1}')"
  actual_source_size="$(wc -c < "$source_file" | tr -d ' ')"
  [[ "$actual_source_sha" == "$source_sha" && "$actual_source_size" == "$source_size" ]] || {
    echo "W98_SOURCE_COPY_INTEGRITY_FAILED replacement=$id"; exit 2;
  }
  ffmpeg -nostdin -hide_banner -v error -i "$source_file" -f null - > /dev/null 2>"$source_log" || {
    echo "W98_SOURCE_DECODE_FAILED replacement=$id"; exit 2;
  }
  source_seconds="$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$source_file")"
  source_duration="$(awk -v d="$source_seconds" 'BEGIN{if(d!~/^[0-9]+(\.[0-9]+)?$/)exit 1;printf "%d",d*1000+0.5}')"
  awk -v a="$source_duration" -v b="$duration_ms" 'BEGIN{d=a-b;if(d<0)d=-d;exit !(d<=1500)}' || {
    echo "W98_SOURCE_DURATION_MISMATCH replacement=$id"; exit 2;
  }

  bash "$GITHUB_WORKSPACE/scripts/windows-gain-render.sh" "$source_file" "$render_file" "$gain" >"$render_log" 2>&1 || {
    echo "W98_OFFLINE_RENDER_FAILED replacement=$id"; exit 2;
  }
  ffmpeg -nostdin -hide_banner -v error -i "$render_file" -f null - > /dev/null 2>"$source_log" || {
    echo "W98_RENDER_DECODE_FAILED replacement=$id"; exit 2;
  }
  render_seconds="$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$render_file")"
  render_duration="$(awk -v d="$render_seconds" 'BEGIN{if(d!~/^[0-9]+(\.[0-9]+)?$/)exit 1;printf "%d",d*1000+0.5}')"
  awk -v a="$render_duration" -v b="$duration_ms" 'BEGIN{d=a-b;if(d<0)d=-d;exit !(d<=1500)}' || {
    echo "W98_RENDER_DURATION_MISMATCH replacement=$id"; exit 2;
  }
  render_size="$(wc -c < "$render_file" | tr -d ' ')"
  [[ "$render_size" -ge 1024 && "$render_size" -le 31457280 ]] || {
    echo "W98_RENDER_SIZE_REJECTED replacement=$id"; exit 2;
  }
  render_sha="$(sha256sum "$render_file" | awk '{print $1}')"

  ffmpeg -nostdin -hide_banner -i "$source_file" -af volumedetect -f null - > /dev/null 2>"$input_meter" || {
    echo "W98_SOURCE_METER_FAILED replacement=$id"; exit 2;
  }
  ffmpeg -nostdin -hide_banner -i "$render_file" -af volumedetect -f null - > /dev/null 2>"$output_meter" || {
    echo "W98_RENDER_METER_FAILED replacement=$id"; exit 2;
  }
  input_mean="$(sed -nE 's/.*mean_volume: (-?[0-9]+(\.[0-9]+)?|-inf) dB.*/\1/p' "$input_meter" | tail -1)"
  input_peak="$(sed -nE 's/.*max_volume: (-?[0-9]+(\.[0-9]+)?|-inf) dB.*/\1/p' "$input_meter" | tail -1)"
  output_mean="$(sed -nE 's/.*mean_volume: (-?[0-9]+(\.[0-9]+)?|-inf) dB.*/\1/p' "$output_meter" | tail -1)"
  output_peak="$(sed -nE 's/.*max_volume: (-?[0-9]+(\.[0-9]+)?|-inf) dB.*/\1/p' "$output_meter" | tail -1)"
  [[ "$input_mean" != "-inf" && "$input_peak" != "-inf" &&
     "$output_mean" != "-inf" && "$output_peak" != "-inf" ]] || {
    echo "W98_INVALID_AUDIO_LEVEL_METRICS replacement=$id"; exit 2;
  }
  delta="$(awk -v a="$input_mean" -v b="$output_mean" 'BEGIN{printf "%.2f",b-a}')"
  awk -v g="$gain" -v d="$delta" -v p="$output_peak" 'BEGIN{
    if(g>0 && d<0.25)exit 1;
    if(g<0 && d>-0.05)exit 1;
    if(p>0.30)exit 1;
  }' || {
    echo "W98_GAIN_OR_PEAK_MEASUREMENT_REJECTED replacement=$id"; exit 2;
  }

  remote_file="$stage_dir/$render_sha.mp3"
  printf '%s\n' "$remote_file" >> "$work/uploaded.tsv"
  copy_to_remote "$render_file" "$remote_file"
  stage_args="--replacement=$id --source-sha=$source_sha --source-version=$version --gain-db=$gain --render-sha=$render_sha --file=$remote_file"
  remote "cd '$release' && '$php_bin' '$release/bin/windows-gain-stage.php' $stage_args" |
    grep -F 'W93_PRIVATE_WINDOWS_GAIN_DRY_RUN_PASS_NO_WRITE' >/dev/null
  printf '%s\t%s\t%s\t%s\t%s\n' "$id" "$version" "$gain" "$source_sha" "$render_sha" >> "$work/attempted.tsv"
  remote "cd '$release' && CELIKOM_W93_ENABLE_STAGE=YES_EXPLICIT_PRIVATE_STAGE '$php_bin' '$release/bin/windows-gain-stage.php' $stage_args --commit" |
    grep -F 'W93_PRIVATE_WINDOWS_GAIN_STAGED' >/dev/null
  remote "rm -f '$remote_file'"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$id" "$track" "$version" "$gain" "$source_sha" "$duration_ms" \
    "$render_sha" "$render_size" "rendered" "$delta" "$output_peak" >> "$work/metrics.tsv"
  rm -f "$source_file" "$render_file" "$source_log" "$render_log" "$input_meter" "$output_meter"
  echo "W98_GAIN_RENDER_MEASURED replacement=$id track=$track gain=${gain}dB rms_delta=${delta}dB peak=${output_peak}dB"
done < "$work/rows.tsv"

remote "'$php_bin' '$helper_remote' inventory '$GITHUB_SHA'" > "$work/inventory-after.json"
# Send the account email through SSH stdin, never in the remote command line.
printf '%s\n' "$CELIKOM_W98_TEST_EMAIL" |
  remote "'$php_bin' '$helper_remote' live-verify '$GITHUB_SHA'" > "$work/live-verify.json"
node .github/scripts/hostinger-windows-gain-verify.mjs \
  "$work/inventory.json" \
  "$work/inventory-after.json" \
  "$work/metrics.tsv" \
  "$work/live-verify.json" \
  "$GITHUB_SHA" \
  "$work/manifest.json"

copy_to_remote "$work/manifest.json" "$manifest_remote"
remote "chmod 600 '$manifest_remote'"
success=1
echo "W98_PRIVATE_GAIN_STAGE_PASS count=$count live_signed_range=206 manifest=private"
