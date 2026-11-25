#!/bin/bash
# Owner-approved dedicated Windows release intake. No sudo rules, root remote
# commands, production pointer changes, new listeners or signing credentials.
# Run only from a root-owned, independently verified copy of these four tools.
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
[[ "$(id -u)" == 0 && $# == 1 ]] || exit 64
tools="$1"
name=celikom-windows-intake
home=/var/lib/celikom-windows-intake
lib=/usr/local/lib/celikom-windows-intake
conf=/etc/celikom-windows-intake
enroll=/home/celops/.celikom-windows-intake-enrollment
pin=/root/celikom-secrets/windows-stable-public.der
source=/root/celikom-release-import/windows-02455
floor=/srv/celikom-releases/windows/stable
if getent passwd "$name" >/dev/null || getent group "$name" >/dev/null; then
  echo WINDOWS_INTAKE_ACCOUNT_ALREADY_EXISTS_REVIEW_FIRST; exit 1
fi
for path in "$home" "$lib" "$conf" "$enroll"; do
  [[ ! -e "$path" && ! -L "$path" ]] || { echo WINDOWS_INTAKE_PATH_EXISTS_REVIEW_FIRST; exit 1; }
done
[[ -d "$tools" && ! -L "$tools" && "$(stat -c '%u:%a' "$tools")" == 0:700 ]]
files=(windows-stable-private-import.py windows-stable-private-intake.py windows-stable-release-verify.mjs windows-stable-existing-latest.mjs)
for f in "${files[@]}"; do
  [[ -f "$tools/$f" && ! -L "$tools/$f" && "$(stat -c '%u:%a' "$tools/$f")" == 0:600 ]]
done
test "$(sha256sum "$pin" | cut -d' ' -f1)" = 46b36bb222154316f2229c35cf65e6c953e0b6524dfb0aad8de05949dc143a95
test "$(readlink "$floor/current")" = versions/0.24.55
test "$(stat -c '%u' /home/celops)" = "$(id -u celops)"
test -f /etc/ssh/ssh_host_ed25519_key.pub
command -v node >/dev/null
command -v sshd >/dev/null
command -v python3 >/dev/null
sshd -t
work=$(mktemp -d /root/celikom-intake-enroll.XXXXXXXX)
created=0
success=0
cleanup() {
  if [[ "$success" != 1 && "$created" == 1 ]]; then
    rm -f -- "$enroll"
    userdel "$name" || true
    rm -rf -- "$home" "$lib" "$conf"
  fi
  rm -rf -- "$work"
}
trap cleanup EXIT
# Prepare and verify the signed transfer before modifying the SSH account.
python3 "$tools/windows-stable-private-import.py" pack --source "$source" \
  --output "$work/transfer.zip" --pin "$pin" --version 0.24.55 --sequence 2
digest=$(sha256sum "$work/transfer.zip" | cut -d' ' -f1)
before=$(sha256sum "$floor/current/manifest.json" "$floor/current/manifest.json.sig" "$floor/current/CELIKOM-Windows-0.24.55.exe")
cat > "$work/gateway" <<'GATE'
#!/bin/bash
set -Eeuo pipefail
umask 077
[[ "$(id -u)" != 0 && "$(id -un)" == celikom-windows-intake ]]
cmd="${SSH_ORIGINAL_COMMAND:-}"
exec /usr/bin/timeout --kill-after=10s 240s /usr/bin/env -i \
  PATH=/usr/bin:/bin LANG=C.UTF-8 SSH_ORIGINAL_COMMAND="$cmd" \
  /usr/bin/python3 /usr/local/lib/celikom-windows-intake/windows-stable-private-intake.py
GATE
bash -n "$work/gateway"
ssh-keygen -q -t ed25519 -N '' -C celikom-windows-intake-data-only -f "$work/key"
useradd --system --user-group --no-create-home --home-dir "$home" --shell /bin/bash "$name"
created=1
install -d -o root -g root -m 755 "$home" "$home/.ssh" "$lib" "$conf"
install -d -o "$name" -g "$name" -m 700 "$home/incoming"
for f in "${files[@]}"; do install -o root -g root -m 644 "$tools/$f" "$lib/$f"; done
install -o root -g root -m 755 "$work/gateway" "$lib/gateway"
install -o root -g root -m 644 "$pin" "$conf/windows-stable-public.der"
printf 'restrict,command="%s/gateway" %s\n' "$lib" "$(cat "$work/key.pub")" > "$work/authorized_keys"
install -o root -g root -m 644 "$work/authorized_keys" "$home/.ssh/authorized_keys"
# This account MUST have no sudo privilege or supplemental group membership.
test "$(id -G "$name")" = "$(id -g "$name")"
# This host's sudo -l -U returns zero even for accounts with no commands.
# Require the explicit denial text, and refuse any listed commands or unknown response.
set +e
sudo_policy=$(LC_ALL=C sudo -n -l -U "$name" 2>&1)
set -e
if ! grep -qiE 'not allowed to run sudo|not allowed to execute|may not run sudo' <<< "$sudo_policy" ||
     grep -qiE 'may run the following commands' <<< "$sudo_policy"; then
  echo WINDOWS_INTAKE_SUDO_UNEXPECTED; exit 1
fi
echo WINDOWS_INTAKE_NO_SUDO_COMMANDS_CONFIRMED
sshd -t
# Exercise the actual forced command over existing loopback SSH, not a new port.
printf '127.0.0.1 %s\n' "$(awk '{print $1 " " $2}' /etc/ssh/ssh_host_ed25519_key.pub)" > "$work/known_hosts"
args=(-T -i "$work/key" -o BatchMode=yes -o IdentitiesOnly=yes \
  -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$work/known_hosts" \
  -o GlobalKnownHostsFile=/dev/null -o ConnectTimeout=15 -o ClearAllForwardings=yes)
if ssh "${args[@]}" "$name@127.0.0.1" id </dev/null >/dev/null 2>&1; then
  echo WINDOWS_INTAKE_SHELL_NOT_REFUSED; exit 1
fi
reply=$(ssh "${args[@]}" "$name@127.0.0.1" "stage-windows 0.24.55 2 $digest" < "$work/transfer.zip")
test "$reply" = "CELIKOM_WINDOWS_DATA_ONLY_INTAKE_OK private-staged 0.24.55 2 $digest"
echo "$reply"
reply=$(ssh "${args[@]}" "$name@127.0.0.1" "stage-windows 0.24.55 2 $digest" < "$work/transfer.zip")
test "$reply" = "CELIKOM_WINDOWS_DATA_ONLY_INTAKE_OK already-staged 0.24.55 2 $digest"
echo "$reply"
file="$home/incoming/windows-0.24.55-2-$digest.zip"
test "$(stat -c '%U:%a' "$file")" = "$name:600"
cmp "$file" "$work/transfer.zip"
mkdir -m 700 "$work/root-import"
python3 "$tools/windows-stable-private-import.py" receive --dest-root "$work/root-import" \
  --floor-root "$floor" --pin "$pin" --version 0.24.55 --sequence 2 < "$file"
cmp "$work/root-import/windows-0.24.55/0.24.55/CELIKOM-Windows-0.24.55.exe" "$source/0.24.55/CELIKOM-Windows-0.24.55.exe"
# Enrollment secret does not yet exist anywhere outside this root workdir.
# Remove only the exact disposable rehearsal archive, not any real candidate.
rm -- "$file"
test "$before" = "$(sha256sum "$floor/current/manifest.json" "$floor/current/manifest.json.sig" "$floor/current/CELIKOM-Windows-0.24.55.exe")"
test "$(curl -sS --max-time 15 -o /dev/null -w '%{http_code}' https://celikom.com/CELIKOM/Windows/Updates/stable/latest.json)" = 401
# One-time enrollment bundle for the owner. Never print private key to CI/chat.
printf '95.133.160.111 %s\n' "$(awk '{print $1 " " $2}' /etc/ssh/ssh_host_ed25519_key.pub)" > "$work/enrollment"
cat "$work/key" >> "$work/enrollment"
install -o celops -g "$(id -gn celops)" -m 600 "$work/enrollment" "$enroll"
success=1
echo CELIKOM_WINDOWS_DEDICATED_DATA_ONLY_INTAKE_READY
echo 'One-time owner secret enrollment required; no stable feed publication.'
