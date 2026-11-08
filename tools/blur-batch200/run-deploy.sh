#!/usr/bin/env bash
# Only two fixed batches of 50. Resuming a partially successful workflow
# replays the same immutable IDs; it never selects a new hundred.
set -euo pipefail
test -n "${HOST_KEY:-}" && test -n "${KNOWN_HOSTS:-}"
test -f tools/blur-batch200/fixed-plan100.json
umask 077
mkdir -p "$RUNNER_TEMP/private" "$RUNNER_TEMP/twohundred-state" "$RUNNER_TEMP/audio"
chmod 700 "$RUNNER_TEMP/private" "$RUNNER_TEMP/twohundred-state" "$RUNNER_TEMP/audio"
printf '%s\n' "$HOST_KEY" > "$RUNNER_TEMP/private/key"
printf '%s\n' "$KNOWN_HOSTS" > "$RUNNER_TEMP/private/hosts"
chmod 600 "$RUNNER_TEMP/private/"*
host=u235811320@92.113.19.189
base='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom'
php=/opt/alt/php83/usr/bin/php
ssh_args=(-p 65002 -i "$RUNNER_TEMP/private/key" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile="$RUNNER_TEMP/private/hosts" -o ConnectTimeout=15)
scp_args=(-P 65002 -i "$RUNNER_TEMP/private/key" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile="$RUNNER_TEMP/private/hosts")
stages=()
cleanup() {
  for stage in "${stages[@]}"; do
    ssh "${ssh_args[@]}" "$host" "test -d '$stage' && rm -f -- '$stage/'*.mp3 '$stage/'*.json '$stage/'*.php && rmdir -- '$stage'" || true
  done
  rm -rf -- "$RUNNER_TEMP/private" "$RUNNER_TEMP/audio"
}
trap cleanup EXIT
started="$(date +%s)"
release_baseline="$(ssh "${ssh_args[@]}" "$host" "readlink -f '$base/current'")"
[[ "$release_baseline" == "$base"/releases/* ]] || { echo UNSAFE_PRODUCTION_RELEASE;exit 2; }
python3 tools/blur-batch200/fetch-fixed.py tools/blur-batch200/fixed-plan100.json "$RUNNER_TEMP/audio" "$RUNNER_TEMP/twohundred-state"
test "$(find "$RUNNER_TEMP/audio" -maxdepth 1 -type f -name '*.mp3' | wc -l)" -eq 200
for batch in 1 2 3 4; do
  stage="$base/incoming/blur-fifty-$((GITHUB_RUN_ID*10+batch))"
  stages+=("$stage")
  echo "PRIVATE_BATCH_START $batch/4"
  release_now="$(ssh "${ssh_args[@]}" "$host" "readlink -f '$base/current'")"
  test "$release_now" = "$release_baseline" || { echo RELEASE_CHANGED_ABORT;exit 2; }
  # Both the private staging path and the batch's exact list are unique.
  ssh "${ssh_args[@]}" "$host" "umask 077; test ! -e '$stage' && mkdir -m 700 '$stage'"
  scp "${scp_args[@]}" tools/blur-batch50/import.php tools/blur-batch200/verify-pending-files.php "$host:$stage/"
  scp "${scp_args[@]}" "$RUNNER_TEMP/twohundred-state/selected-$batch.json" "$host:$stage/selected.json"
  mapfile -t ids < <(jq -r '.selected[].id' "$RUNNER_TEMP/twohundred-state/selected-$batch.json")
  test "${#ids[@]}" -eq 50
  to_send=()
  for id in "${ids[@]}"; do
    [[ "$id" =~ ^[1-9][0-9]{0,19}$ ]] || exit 2
    test -f "$RUNNER_TEMP/audio/$id.mp3"
    to_send+=("$RUNNER_TEMP/audio/$id.mp3")
  done
  bytes="$(jq '[.selected[].size]|add' "$RUNNER_TEMP/twohundred-state/selected-$batch.json")"
  free="$(ssh "${ssh_args[@]}" "$host" "df -B1 --output=avail '$base/shared/audio' | tail -1 | tr -d '[:space:]'")"
  test "$free" -gt "$((bytes*2+100000000))" || { echo "INSUFFICIENT_STORAGE_BATCH_$batch";exit 1; }
  moved="$(date +%s)"
  scp "${scp_args[@]}" "${to_send[@]}" "$host:$stage/"
  echo "STAGING_BATCH_${batch}_SECONDS=$(( $(date +%s) - moved ))"
  ssh "${ssh_args[@]}" "$host" "CELIKOM_BLUR_DRY_RUN=1 $php '$stage/import.php'" | tee "$RUNNER_TEMP/twohundred-state/dry-$batch.json"
  jq -e '.status=="DRY_RUN_PASS" and .verified_files==50 and .writes==0' "$RUNNER_TEMP/twohundred-state/dry-$batch.json" >/dev/null
  ssh "${ssh_args[@]}" "$host" "$php '$stage/import.php'" | tee "$RUNNER_TEMP/twohundred-state/import-$batch.json"
  jq -e '.status=="PASS" and .requested==50 and (.new_pending+.resumed)==50 and .approved==0 and .active==0 and .rights_confirmed==false' "$RUNNER_TEMP/twohundred-state/import-$batch.json" >/dev/null
  ssh "${ssh_args[@]}" "$host" "$php '$stage/verify-pending-files.php'" | tee "$RUNNER_TEMP/twohundred-state/verify-$batch.json"
  jq -e '.status=="LIVE50_PENDING_VERIFIED" and .pending_count==50 and .files_verified==50 and .pass==true and .active==0 and .writes==0' "$RUNNER_TEMP/twohundred-state/verify-$batch.json" >/dev/null
  echo "PRIVATE_BATCH_DONE $batch/4"
  # Cleanup verified staging for this batch immediately after its commit.
  ssh "${ssh_args[@]}" "$host" "rm -f -- '$stage/'*.mp3 '$stage/'*.json '$stage/'*.php; rmdir -- '$stage'"
  rm -f -- "${to_send[@]}"
done
# Independent full 200-track audit after all four batches (never writes).
final_stage="$base/incoming/blur-fifty-$((GITHUB_RUN_ID*10+5))"
stages+=("$final_stage")
ssh "${ssh_args[@]}" "$host" "umask 077; test ! -e '$final_stage' && mkdir -m 700 '$final_stage'"
scp "${scp_args[@]}" tools/blur-batch200/verify-pending-files.php "$host:$final_stage/"
scp "${scp_args[@]}" tools/blur-batch200/fixed-plan200.json "$host:$final_stage/selected.json"
ssh "${ssh_args[@]}" "$host" "$php '$final_stage/verify-pending-files.php'" | tee "$RUNNER_TEMP/twohundred-state/verify-all200.json"
jq -e '.status=="LIVE200_PENDING_VERIFIED" and .checked==200 and .files_verified==200 and .pending_count==200 and .pass==true and (.issues|length)==0 and .writes==0' "$RUNNER_TEMP/twohundred-state/verify-all200.json" >/dev/null
ssh "${ssh_args[@]}" "$host" "rm -f -- '$final_stage/'*.json '$final_stage/'*.php; rmdir -- '$final_stage'"
jq -n \
  --slurpfile a "$RUNNER_TEMP/twohundred-state/import-1.json" \
  --slurpfile b "$RUNNER_TEMP/twohundred-state/import-2.json" \
  --slurpfile c "$RUNNER_TEMP/twohundred-state/import-3.json" \
  --slurpfile d "$RUNNER_TEMP/twohundred-state/import-4.json" '{
  status:"LIVE200_PENDING_VERIFIED",
  batches:4,
  new_pending:([$a[0].new_pending,$b[0].new_pending,$c[0].new_pending,$d[0].new_pending]|add),
  resumed:([$a[0].resumed,$b[0].resumed,$c[0].resumed,$d[0].resumed]|add),
  total:([$a[0].new_pending,$b[0].new_pending,$c[0].new_pending,$d[0].new_pending,$a[0].resumed,$b[0].resumed,$c[0].resumed,$d[0].resumed]|add),
  automatic_approvals:([$a[0].approved,$b[0].approved,$c[0].approved,$d[0].approved]|add),
  active:([$a[0].active,$b[0].active,$c[0].active,$d[0].active]|add),
  rights_confirmed:false
}' | tee "$RUNNER_TEMP/twohundred-state/twohundred-summary.json"
jq -e '.status=="LIVE200_PENDING_VERIFIED" and .total==200 and .automatic_approvals==0 and .active==0' "$RUNNER_TEMP/twohundred-state/twohundred-summary.json" >/dev/null
echo "TWOHUNDRED_END_TO_END_SECONDS=$(( $(date +%s) - started ))"
echo '### CELIKOM: exactly 200 fixed private pending versions confirmed; no auto-approval' >> "$GITHUB_STEP_SUMMARY"
echo '[Open 50-per-page pending list](https://darkred-camel-588676.hostingersite.com/admin?tab=uploads&status=pending&per_page=50)' >> "$GITHUB_STEP_SUMMARY"
jq . "$RUNNER_TEMP/twohundred-state/twohundred-summary.json" >> "$GITHUB_STEP_SUMMARY"
