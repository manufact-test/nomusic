#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
echo A1_FLOKI_RUNNER_READONLY_AUDIT_BEGIN
for spec in "celikom-ci-runner.service celikom-floki-ci01" "celikom-ci-runner2.service celikom-floki-ci02"; do
  read -r unit container <<< "$spec"
  echo "RUNNER_UNIT $unit"
  systemctl show "$unit" --property MainPID,Result,NRestarts,ExecMainStatus,ActiveState,SubState,StateChangeTimestamp --no-pager
  echo "RUNNER_CONTAINER $container"
  if docker inspect "$container" >/dev/null 2>&1; then
    docker inspect --format 'status={{.State.Status}} running={{.State.Running}} restarts={{.RestartCount}} started={{.State.StartedAt}}' "$container"
    for proc in Runner.Listener Runner.Worker; do
      count=$(docker exec "$container" sh -c "ps -eo comm= | grep -c '^$proc$' || true" 2>/dev/null || echo unavailable)
      echo "RUNNER_PROCESS $container $proc $count"
    done
  else
    echo "RUNNER_CONTAINER_MISSING $container"
  fi
  echo "RUNNER_RECENT_EVENT_COUNTS $unit"
  journalctl -u "$unit" --since '-30 minutes' --no-pager -o cat 2>/dev/null | grep -Eo 'JOB_COMPLETED|JOB_ABORTED|WORKER_FAILURE|ERROR_GENERIC|Worker process started|JobDispatcher' | sort | uniq -c || true
done
echo A1_FLOKI_RUNNER_READONLY_AUDIT_DONE
