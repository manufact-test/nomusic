#!/usr/bin/env bash
# Only two fixed batches of 50. Resuming a partially successful workflow
# replays the same immutable IDs; it never selects a new hundred.
set -euo pipefail
test -n "${HOST_KEY:-}" && test -n "${KNOWN_HOSTS:-}"
test -f tools/blur-batch100/fixed-plan100.json
umask 077
mkdir -p "$RUNNER_TEMP/private" "$RUNNER_TEMP/hundred-state" "$RUNNER_TEMP/audio"
chmod 700 "$RUNNER_TEMP/private" "$RUNNER_TEMP/hundred-state" "$RUNNER_TEMP/audio"
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
python3 tools/blur-batch100/fetch-fixed.py tools/blur-batch100/fixed-plan100.json "$RUNNER_TEMP/audio" "$RUNNER_TEMP/hundred-state"
test "$(find "$RUNNER_TEMP/audio" -maxdepth 1 -type f -name '*.mp3' | wc -l)" -eq 100
for batch in 1 2; do
  stage="$base/incoming/blur-fifty-$((GITHUB_RUN_ID*10+batch))"
  stages+=("$stage")
  echo "PRIVATE_BATCH_START $batch/2"
  # Both the private staging path and the batch's exact list are unique.
  ssh "${ssh_args[@]}" "$host" "umask 077; test ! -e '$stage' && mkdir -m 700 '$stage'"
  scp "${scp_args[@]}" tools/blur-batch50/{import.php,verify.php} "$host:$stage/"
  scp "${scp_args[@]}" "$RUNNER_TEMP/hundred-state/selected-$batch.json" "$host:$stage/selected.json"
  mapfile -t ids < <(jq -r '.selected[].id' "$RUNNER_TEMP/hundred-state/selected-$batch.json")
  test "${#ids[@]}" -eq 50
  to_send=()
  for id in "${ids[@]}"; do
    [[ "$id" =~ ^[1-9][0-9]{0,19}$ ]] || exit 2
    test -f "$RUNNER_TEMP/audio/$id.mp3"
    to_send+=("$RUNNER_TEMP/audio/$id.mp3")
  done
  bytes="$(jq '[.selected[].size]|add' "$RUNNER_TEMP/hundred-state/selected-$batch.json")"
  free="$(ssh "${ssh_args[@]}" "$host" "df -B1 --output=avail '$base/shared/audio' | tail -1 | tr -d '[:space:]'")"
  test "$free" -gt "$((bytes*2+100000000))" || { echo "INSUFFICIENT_STORAGE_BATCH_$batch";exit 1; }
  moved="$(date +%s)"
  scp "${scp_args[@]}" "${to_send[@]}" "$host:$stage/"
  echo "STAGING_BATCH_${batch}_SECONDS=$(( $(date +%s) - moved ))"
  ssh "${ssh_args[@]}" "$host" "CELIKOM_BLUR_DRY_RUN=1 $php '$stage/import.php'" | tee "$RUNNER_TEMP/hundred-state/dry-$batch.json"
  jq -e '.status=="DRY_RUN_PASS" and .verified_files==50 and .writes==0' "$RUNNER_TEMP/hundred-state/dry-$batch.json" >/dev/null
  ssh "${ssh_args[@]}" "$host" "$php '$stage/import.php'" | tee "$RUNNER_TEMP/hundred-state/import-$batch.json"
  jq -e '.status=="PASS" and .requested==50 and (.new_pending+.resumed)==50 and .approved==0 and .active==0 and .rights_confirmed==false' "$RUNNER_TEMP/hundred-state/import-$batch.json" >/dev/null
  ssh "${ssh_args[@]}" "$host" "$php '$stage/verify.php'" | tee "$RUNNER_TEMP/hundred-state/verify-$batch.json"
  jq -e '.status=="LIVE_VERIFIED" and .pending_count==50 and .active==0 and .writes==0' "$RUNNER_TEMP/hundred-state/verify-$batch.json" >/dev/null
  echo "PRIVATE_BATCH_DONE $batch/2"
  # Cleanup verified staging for this batch immediately after its commit.
  ssh "${ssh_args[@]}" "$host" "rm -f -- '$stage/'*.mp3 '$stage/'*.json '$stage/'*.php; rmdir -- '$stage'"
  rm -f -- "${to_send[@]}"
done
jq -n --slurpfile a "$RUNNER_TEMP/hundred-state/import-1.json" --slurpfile b "$RUNNER_TEMP/hundred-state/import-2.json" '{
  status:"LIVE_HUNDRED_VERIFIED",
  batches:2,
  new_pending:($a[0].new_pending+$b[0].new_pending),
  resumed:($a[0].resumed+$b[0].resumed),
  total:($a[0].new_pending+$a[0].resumed+$b[0].new_pending+$b[0].resumed),
  automatic_approvals:($a[0].approved+$b[0].approved),
  active:($a[0].active+$b[0].active),
  rights_confirmed:false
}' | tee "$RUNNER_TEMP/hundred-state/hundred-summary.json"
jq -e '.status=="LIVE_HUNDRED_VERIFIED" and .total==100 and .automatic_approvals==0 and .active==0' "$RUNNER_TEMP/hundred-state/hundred-summary.json" >/dev/null
echo "HUNDRED_END_TO_END_SECONDS=$(( $(date +%s) - started ))"
echo '### CELIKOM: exactly 100 fixed private pending versions confirmed; no auto-approval' >> "$GITHUB_STEP_SUMMARY"
echo '[Open 50-per-page pending list](https://darkred-camel-588676.hostingersite.com/admin?tab=uploads&status=pending&per_page=50)' >> "$GITHUB_STEP_SUMMARY"
jq . "$RUNNER_TEMP/hundred-state/hundred-summary.json" >> "$GITHUB_STEP_SUMMARY"
