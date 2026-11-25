#!/bin/bash
# One-time, fail-closed data-only spool parity for existing Floki CI runner2.
# Never mounts host root, SSH, Docker socket or production secrets.
# Do not restart the runner while a GitHub Actions worker is active.
set -Eeuo pipefail
umask 077
[[ "$(id -u)" == 0 ]]
UNIT=/etc/systemd/system/celikom-ci-runner2.service
NAME=celikom-floki-ci02
HOST=/srv/celikom/ci-runner/runner
R2=/srv/celikom/ci-runner/runner2
[[ -f "$UNIT" && ! -L "$UNIT" && "$(stat -c '%u' "$UNIT")" == 0 ]]
[[ -d "$R2" && ! -L "$R2" ]]
for name in celikom-build-spool celikom-windows-signed-spool celikom-a1-signed-spool; do
  [[ -d "$HOST/$name" && ! -L "$HOST/$name" ]]
done
for name in celikom-windows-signed-spool celikom-a1-signed-spool; do
  if [[ -d "$R2/$name" ]] && find "$R2/$name" -mindepth 1 -maxdepth 1 -print -quit | grep -q .; then
    echo "RUNNER2_LOCAL_SPOOL_HAS_DATA_PRESERVE_AND_REVIEW $name"
    exit 2
  fi
done

mount_state() {
  docker inspect "$NAME" --format '{{json .Mounts}}' |
    python3 -c '
import json,sys
mounts=json.load(sys.stdin)
roots={m.get("Destination"):m.get("Source") for m in mounts if m.get("Type")=="bind"}
base="/srv/celikom/ci-runner/runner/"
want={
 "/home/runner/celikom-build-spool":base+"celikom-build-spool",
 "/home/runner/celikom-windows-signed-spool":base+"celikom-windows-signed-spool",
 "/home/runner/celikom-a1-signed-spool":base+"celikom-a1-signed-spool"}
assert roots.get("/home/runner/celikom-build-spool")==want["/home/runner/celikom-build-spool"],"SHARED_EXTENSION_SPOOL_MISSING"
assert roots.get("/home/runner")=="/srv/celikom/ci-runner/runner2","RUNNER2_HOME_MOUNT_MISMATCH"
print("all" if all(roots.get(k)==v for k,v in want.items()) else "partial")
'
}
initial=$(mount_state)
if [[ "$initial" == all ]]; then
  echo RUNNER2_ALL_THREE_DATA_SPOOLS_ALREADY_SHARED
  exit 0
fi

# Compute a strictly limited unit amendment. Unknown unit layouts fail
# before the running runner or any server component is touched.
backup=$(mktemp /root/celikom-runner2-unit-before-spool.XXXXXXXX)
cp -a "$UNIT" "$backup"
next=$(mktemp /etc/systemd/system/.celikom-ci02-mount.XXXXXXXX)
trap 'rm -f "$next"' EXIT
python3 - "$UNIT" "$next" <<'PY'
import os,sys
source,target=sys.argv[1:3]
s=open(source).read()
base="/srv/celikom/ci-runner/runner/"
# Runner2 was provisioned using Docker --mount type=bind syntax.
# Never substitute into a partial path or an unknown mount option.
marker="--mount type=bind,src="+base+"celikom-build-spool,dst=/home/runner/celikom-build-spool"
assert s.count(marker)==1,"RUNNER2_UNIT_UNKNOWN_SHARED_BIND"
assert "celikom-floki-ci02" in s and "ExecStart=" in s and "docker" in s,"RUNNER2_UNIT_UNKNOWN_EXEC"
assert "celikom-windows-signed-spool" not in s and "celikom-a1-signed-spool" not in s,"RUNNER2_UNIT_PARTIAL_CUSTOM_BIND"
pos=s.index(marker)+len(marker)
assert pos==len(s) or s[pos].isspace() or s[pos]=="\\", "RUNNER2_UNIT_SHARED_MOUNT_OPTIONS_UNKNOWN"
additions=" --mount type=bind,src="+base+"celikom-windows-signed-spool,dst=/home/runner/celikom-windows-signed-spool"
additions+=" --mount type=bind,src="+base+"celikom-a1-signed-spool,dst=/home/runner/celikom-a1-signed-spool"
s=s.replace(marker,marker+additions)
with open(target,"w") as f:
    f.write(s);f.flush();os.fsync(f.fileno())
PY
bash -n /dev/null
# No Runner.Worker process means no job is actively executing.
for _ in 1 2 3; do
  if docker top "$NAME" | grep -q 'Runner.Worker'; then
    echo RUNNER2_CI_JOB_ACTIVE_DEFER_MOUNT_UPDATE
    exit 3
  fi
  sleep 2
done
echo RUNNER2_CONFIRMED_IDLE_UPDATING_ONLY_DATA_BINDS
chmod --reference="$UNIT" "$next"
chown --reference="$UNIT" "$next"
mv -T "$next" "$UNIT"
if ! systemd-analyze verify "$UNIT" >/dev/null 2>&1; then
  cp -a "$backup" "$UNIT"
  echo RUNNER2_UNIT_VERIFY_FAILED_ROLLED_BACK
  exit 1
fi
systemctl daemon-reload
rollback() {
  cp -a "$backup" "$UNIT"
  systemctl daemon-reload
  systemctl restart celikom-ci-runner2.service || true
}
if ! systemctl restart celikom-ci-runner2.service; then
  rollback
  echo RUNNER2_RESTART_FAILED_ROLLED_BACK
  exit 1
fi
sleep 3
if [[ "$(mount_state)" != all ]]; then
  rollback
  echo RUNNER2_DATA_SPOOL_MOUNTS_NOT_CONFIRMED_ROLLED_BACK
  exit 1
fi
echo RUNNER2_BOTH_SIGNED_DATA_SPOOLS_SHARED_AND_MOUNT_VERIFIED
