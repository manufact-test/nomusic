#!/usr/bin/env bash
set -euo pipefail
test -n "${HOST_KEY:-}" && test -n "${KNOWN_HOSTS:-}"
umask 077
mkdir -p "$RUNNER_TEMP/private" "$RUNNER_TEMP/state" "$RUNNER_TEMP/audio"
chmod 700 "$RUNNER_TEMP/private" "$RUNNER_TEMP/state" "$RUNNER_TEMP/audio"
printf '%s\n' "$HOST_KEY" > "$RUNNER_TEMP/private/id_host"
printf '%s\n' "$KNOWN_HOSTS" > "$RUNNER_TEMP/private/known_hosts"
chmod 600 "$RUNNER_TEMP/private/"*
target='u235811320@92.113.19.189'
stage="/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom/incoming/blur-fifty-$GITHUB_RUN_ID"
ssh_opts=(-p 65002 -i "$RUNNER_TEMP/private/id_host" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile="$RUNNER_TEMP/private/known_hosts" -o ConnectTimeout=15)
scp_opts=(-P 65002 -i "$RUNNER_TEMP/private/id_host" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile="$RUNNER_TEMP/private/known_hosts")
clean_stage() {
  ssh "${ssh_opts[@]}" "$target" "test -d '$stage' && rm -f -- '$stage/'*.mp3 '$stage/'*.json '$stage/'*.php && rmdir -- '$stage'" || true
  rm -rf -- "$RUNNER_TEMP/audio" "$RUNNER_TEMP/private"
}
trap clean_stage EXIT
started="$(date +%s)"
ssh "${ssh_opts[@]}" "$target" "umask 077; test ! -e '$stage' && mkdir -m 700 '$stage'"
scp "${scp_opts[@]}" tools/blur-batch50/{candidates.json,live-check.php,import.php,verify.php} "$target:$stage/"
ssh "${ssh_opts[@]}" "$target" "/opt/alt/php83/usr/bin/php '$stage/live-check.php'" > "$RUNNER_TEMP/state/precheck.json"
jq -e '.status=="READ_ONLY" and .writes==0 and (.eligible|length)>=50' "$RUNNER_TEMP/state/precheck.json" >/dev/null
jq '{scanned,eligible:(.eligible|length),existing:(.skipped|length),writes}' "$RUNNER_TEMP/state/precheck.json"
prepared="$(date +%s)"
python3 tools/blur-batch50/prepare.py tools/blur-batch50/candidates.json "$RUNNER_TEMP/state/precheck.json" "$RUNNER_TEMP/audio" "$RUNNER_TEMP/state"
jq -e '(.selected|length)==50' "$RUNNER_TEMP/state/selected.json" >/dev/null
test "$(find "$RUNNER_TEMP/audio" -maxdepth 1 -type f -name '*.mp3' | wc -l)" -eq 50
echo "DOWNLOAD_VALIDATE_WALL_SECONDS=$(( $(date +%s) - prepared ))"
bytes="$(jq '[.selected[].size]|add' "$RUNNER_TEMP/state/selected.json")"
free="$(ssh "${ssh_opts[@]}" "$target" "df -B1 --output=avail '/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom/shared/audio' | tail -1 | tr -d '[:space:]'")"
test "$free" -gt "$(( 2*bytes+100000000 ))" || { echo 'STORAGE_CAPACITY_REFUSED';exit 1; }
scp "${scp_opts[@]}" "$RUNNER_TEMP/state/selected.json" "$target:$stage/"
transferred="$(date +%s)"
scp "${scp_opts[@]}" "$RUNNER_TEMP/audio/"*.mp3 "$target:$stage/"
echo "PRIVATE_STAGE_TRANSFER_SECONDS=$(( $(date +%s) - transferred ))"
ssh "${ssh_opts[@]}" "$target" "CELIKOM_BLUR_DRY_RUN=1 /opt/alt/php83/usr/bin/php '$stage/import.php'" | tee "$RUNNER_TEMP/state/dry-run.json"
jq -e '.status=="DRY_RUN_PASS" and .verified_files==50 and .writes==0' "$RUNNER_TEMP/state/dry-run.json" >/dev/null
imported="$(date +%s)"
ssh "${ssh_opts[@]}" "$target" "/opt/alt/php83/usr/bin/php '$stage/import.php'" | tee "$RUNNER_TEMP/state/actual-import.json"
jq -e '.status=="PASS" and .requested==50 and (.new_pending+.resumed)==50 and .approved==0 and .active==0' "$RUNNER_TEMP/state/actual-import.json" >/dev/null
echo "PRIVATE_IMPORT_SECONDS=$(( $(date +%s) - imported ))"
ssh "${ssh_opts[@]}" "$target" "/opt/alt/php83/usr/bin/php '$stage/verify.php'" | tee "$RUNNER_TEMP/state/live-verification.json"
jq -e '.status=="LIVE_VERIFIED" and .pending_count==50 and .active==0 and .writes==0' "$RUNNER_TEMP/state/live-verification.json" >/dev/null
echo "END_TO_END_SECONDS=$(( $(date +%s) - started ))"
echo '### CELIKOM 50 private pending MP3 — no automatic approval or rights confirmation' >> "$GITHUB_STEP_SUMMARY"
echo '[Open admin pending queue](https://darkred-camel-588676.hostingersite.com/admin?tab=uploads&status=pending&per_page=50)' >> "$GITHUB_STEP_SUMMARY"
jq '{new_pending,resumed,approved,active}' "$RUNNER_TEMP/state/actual-import.json" >> "$GITHUB_STEP_SUMMARY"
