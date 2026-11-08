#!/usr/bin/env bash
set -euo pipefail
test -n "${HOST_KEY:-}" && test -n "${KNOWN_HOSTS:-}"
umask 077
mkdir -p "$RUNNER_TEMP/private" "$RUNNER_TEMP/plan-state" "$RUNNER_TEMP/audio"
chmod 700 "$RUNNER_TEMP/private" "$RUNNER_TEMP/plan-state" "$RUNNER_TEMP/audio"
printf '%s\n' "$HOST_KEY" > "$RUNNER_TEMP/private/key"
printf '%s\n' "$KNOWN_HOSTS" > "$RUNNER_TEMP/private/hosts"
chmod 600 "$RUNNER_TEMP/private/"*
host=u235811320@92.113.19.189
stage="/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom/incoming/blur-fifty-$GITHUB_RUN_ID"
ssh_args=(-p 65002 -i "$RUNNER_TEMP/private/key" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile="$RUNNER_TEMP/private/hosts")
scp_args=(-P 65002 -i "$RUNNER_TEMP/private/key" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile="$RUNNER_TEMP/private/hosts")
clean() {
 ssh "${ssh_args[@]}" "$host" "test -d '$stage' && rm -f -- '$stage/'*.php '$stage/'*.json && rmdir -- '$stage'" || true
 rm -rf "$RUNNER_TEMP/audio" "$RUNNER_TEMP/private"
}
trap clean EXIT
ssh "${ssh_args[@]}" "$host" "umask 077; test ! -e '$stage' && mkdir -m 700 '$stage'"
scp "${scp_args[@]}" tools/blur-batch800/{candidates.json,live-check.php} "$host:$stage/"
ssh "${ssh_args[@]}" "$host" "/opt/alt/php83/usr/bin/php '$stage/live-check.php'" > "$RUNNER_TEMP/plan-state/precheck.json"
jq -e '.writes==0 and (.eligible|length)>=200' "$RUNNER_TEMP/plan-state/precheck.json" > /dev/null
jq '{scanned,eligible:(.eligible|length),skipped:(.skipped|length),writes}' "$RUNNER_TEMP/plan-state/precheck.json"
python3 tools/blur-batch800/plan.py tools/blur-batch800/candidates.json "$RUNNER_TEMP/plan-state/precheck.json" "$RUNNER_TEMP/audio" "$RUNNER_TEMP/plan-state"
jq -e '.fixed_plan==true and .target_pending==200 and (.selected|length)==200' "$RUNNER_TEMP/plan-state/fixed-plan800.json" >/dev/null
test "$(find "$RUNNER_TEMP/audio" -name '*.mp3' -type f | wc -l)" -eq 200
echo 'Read-only plan complete: 200 audio sources verified, 0 production writes'
