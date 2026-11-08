#!/usr/bin/env bash
# Exactly 50 prechecked multisource MP3. Idempotent private pending-only import.
set -euo pipefail
test -n "${HOST_KEY:-}" && test -n "${KNOWN_HOSTS:-}"
test -f tools/blur-research/pending50-20261109.json
umask 077
mkdir -p "$RUNNER_TEMP/private" "$RUNNER_TEMP/final-state" "$RUNNER_TEMP/audio"
chmod 700 "$RUNNER_TEMP/private" "$RUNNER_TEMP/final-state" "$RUNNER_TEMP/audio"
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
python3 tools/blur-research/pending50/fetch.py "$RUNNER_TEMP/audio" "$RUNNER_TEMP/final-state"
total="$(jq '.selected|length' tools/blur-research/pending50-20261109.json)"
test "$total" -ge 1 && test "$total" -le 200
batches="$(( (total+49)/50 ))"
test "$(find "$RUNNER_TEMP/audio" -maxdepth 1 -type f -name '*.mp3' | wc -l)" -eq "$total"
for (( batch=1; batch<=batches; batch++ )); do
  stage="$base/incoming/blur-fifty-$((GITHUB_RUN_ID*10+batch))"
  stages+=("$stage")
  echo "PRIVATE_BATCH_START $batch/$batches"
  release_now="$(ssh "${ssh_args[@]}" "$host" "readlink -f '$base/current'")"
  test "$release_now" = "$release_baseline" || { echo RELEASE_CHANGED_ABORT;exit 2; }
  # Both the private staging path and the batch's exact list are unique.
  ssh "${ssh_args[@]}" "$host" "umask 077; test ! -e '$stage' && mkdir -m 700 '$stage'"
  scp "${scp_args[@]}" tools/blur-research/pending50/import.php tools/blur-research/pending50/verify-pending-files.php "$host:$stage/"
  scp "${scp_args[@]}" "$RUNNER_TEMP/final-state/selected-$batch.json" "$host:$stage/selected.json"
  mapfile -t ids < <(jq -r '.selected[].id' "$RUNNER_TEMP/final-state/selected-$batch.json")
  n="$(jq '.selected|length' "$RUNNER_TEMP/final-state/selected-$batch.json")"
  test "$n" -ge 1 && test "$n" -le 50
  test "${#ids[@]}" -eq "$n"
  to_send=()
  for id in "${ids[@]}"; do
    [[ "$id" =~ ^[1-9][0-9]{0,19}$ ]] || exit 2
    test -f "$RUNNER_TEMP/audio/$id.mp3"
    to_send+=("$RUNNER_TEMP/audio/$id.mp3")
  done
  bytes="$(jq '[.selected[].size]|add' "$RUNNER_TEMP/final-state/selected-$batch.json")"
  free="$(ssh "${ssh_args[@]}" "$host" "df -B1 --output=avail '$base/shared/audio' | tail -1 | tr -d '[:space:]'")"
  test "$free" -gt "$((bytes*2+100000000))" || { echo "INSUFFICIENT_STORAGE_BATCH_$batch";exit 1; }
  moved="$(date +%s)"
  scp "${scp_args[@]}" "${to_send[@]}" "$host:$stage/"
  echo "STAGING_BATCH_${batch}_SECONDS=$(( $(date +%s) - moved ))"
  ssh "${ssh_args[@]}" "$host" "CELIKOM_BLUR_DRY_RUN=1 $php '$stage/import.php'" | tee "$RUNNER_TEMP/final-state/dry-$batch.json"
  jq -e --argjson n "$n" '.status=="DRY_RUN_PASS" and .verified_files==$n and .writes==0' "$RUNNER_TEMP/final-state/dry-$batch.json" >/dev/null
  ssh "${ssh_args[@]}" "$host" "$php '$stage/import.php'" | tee "$RUNNER_TEMP/final-state/import-$batch.json"
  jq -e --argjson n "$n" '.status=="PASS" and .requested==$n and (.new_pending+.resumed)==$n and .approved==0 and .active==0 and .rights_confirmed==false' "$RUNNER_TEMP/final-state/import-$batch.json" >/dev/null
  ssh "${ssh_args[@]}" "$host" "$php '$stage/verify-pending-files.php'" | tee "$RUNNER_TEMP/final-state/verify-$batch.json"
  jq -e --argjson n "$n" '.status==("LIVE"+($n|tostring)+"_PENDING_VERIFIED") and .pending_count==$n and .files_verified==$n and .pass==true and .active==0 and .writes==0' "$RUNNER_TEMP/final-state/verify-$batch.json" >/dev/null
  echo "PRIVATE_BATCH_DONE $batch/$batches"
  # Cleanup verified staging for this batch immediately after its commit.
  ssh "${ssh_args[@]}" "$host" "rm -f -- '$stage/'*.mp3 '$stage/'*.json '$stage/'*.php; rmdir -- '$stage'"
  rm -f -- "${to_send[@]}"
done
# Independent full 200-track audit after all four batches (never writes).
final_stage="$base/incoming/blur-fifty-$((GITHUB_RUN_ID*10+5))"
stages+=("$final_stage")
ssh "${ssh_args[@]}" "$host" "umask 077; test ! -e '$final_stage' && mkdir -m 700 '$final_stage'"
scp "${scp_args[@]}" tools/blur-research/pending50/verify-pending-files.php "$host:$final_stage/"
scp "${scp_args[@]}" tools/blur-research/pending50-20261109.json "$host:$final_stage/selected.json"
ssh "${ssh_args[@]}" "$host" "$php '$final_stage/verify-pending-files.php'" | tee "$RUNNER_TEMP/final-state/verify-all200.json"
jq -e --argjson n "$total" '.status==("LIVE"+($n|tostring)+"_PENDING_VERIFIED") and .checked==$n and .files_verified==$n and .pending_count==$n and .pass==true and (.issues|length)==0 and .writes==0' "$RUNNER_TEMP/final-state/verify-all200.json" >/dev/null
ssh "${ssh_args[@]}" "$host" "rm -f -- '$final_stage/'*.json '$final_stage/'*.php; rmdir -- '$final_stage'"
jq -s --argjson required "$total" '{
  status:"LIVE_FINAL_PENDING_VERIFIED",
  batches:length,
  new_pending:(map(.new_pending)|add),
  resumed:(map(.resumed)|add),
  total:(map(.new_pending+.resumed)|add),
  automatic_approvals:(map(.approved)|add),
  active:(map(.active)|add),
  rights_confirmed:false
}' "$RUNNER_TEMP/final-state"/import-*.json | tee "$RUNNER_TEMP/final-state/final-summary.json"
jq -e --argjson n "$total" '.status=="LIVE_FINAL_PENDING_VERIFIED" and .total==$n and .automatic_approvals==0 and .active==0' "$RUNNER_TEMP/final-state/final-summary.json" >/dev/null
echo "FINAL_END_TO_END_SECONDS=$(( $(date +%s) - started ))"
echo '### CELIKOM final source residual: exact pinned private pending versions, no auto-approval' >> "$GITHUB_STEP_SUMMARY"
jq . "$RUNNER_TEMP/final-state/final-summary.json" >> "$GITHUB_STEP_SUMMARY"
