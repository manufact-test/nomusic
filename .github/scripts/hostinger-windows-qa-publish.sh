#!/usr/bin/env bash
# W99: publish the one fully verified Windows QA package to the public Test folder.
set -euo pipefail
umask 077

package_dir="${1:-}"
[[ -n "$package_dir" && -d "$package_dir" ]] || {
  echo 'W99_PACKAGE_DIRECTORY_REQUIRED'; exit 2;
}
[[ -n "${HOSTINGER_SSH_KEY:-}" ]] || {
  echo 'W99_NO_HOSTINGER_SSH_CREDENTIAL'; exit 2;
}
[[ "${GITHUB_RUN_ID:-}" =~ ^[1-9][0-9]{0,19}$ ]] || {
  echo 'W99_BAD_GITHUB_RUN_ID'; exit 2;
}

exe='CELIKOM-Windows-0.24.36-INTEGRATED-QA-TEST.exe'
zip='CELIKOM-Windows-0.24.36-INTEGRATED-QA-TEST.zip'
manifest='SHA256SUMS.txt'
for file in "$exe" "$zip" "$manifest"; do
  [[ -f "$package_dir/$file" ]] || { echo "W99_PACKAGE_FILE_MISSING file=$file"; exit 2; }
done
(cd "$package_dir" && sha256sum -c "$manifest")

port=65002
target='u235811320@92.113.19.189'
root='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/public_html'
destination="$root/CELIKOM/Windows/Test"
stage="/home/u235811320/.celikom-windows-test-stage-$GITHUB_RUN_ID"
base_url='https://darkred-camel-588676.hostingersite.com/CELIKOM/Windows/Test'

work="$(mktemp -d)"
remote_ready=0
cleanup() {
  local result=$?
  trap - EXIT
  if [[ "$remote_ready" -eq 1 ]]; then
    ssh -T -p "$port" "${ssh_opts[@]}" "$target" "rm -rf '$stage'" >/dev/null 2>&1 || true
  fi
  rm -rf "$work"
  exit "$result"
}
trap cleanup EXIT

printf '%s\n' "$HOSTINGER_SSH_KEY" | tr -d '\r' > "$work/key"
chmod 600 "$work/key"
ssh-keygen -y -P '' -f "$work/key" > "$work/key.pub"
fingerprint="$(ssh-keygen -lf "$work/key.pub" -E sha256 | awk '{print $2}')"
[[ "$fingerprint" == 'SHA256:Q6FyifXRq6garceQdIIjBmXhkk81Ic1p/x9JTSYHWUk' ]] || {
  echo 'W99_BAD_SSH_IDENTITY'; exit 2;
}
printf '%s\n' '[92.113.19.189]:65002 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAf8M2EVwq0oJI8I9KZ0NFE8P8yDOvDATEhkQti/Kk/0' > "$work/known_hosts"
ssh_opts=(-i "$work/key" -o BatchMode=yes -o IdentitiesOnly=yes
  -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$work/known_hosts"
  -o GlobalKnownHostsFile=/dev/null -o ConnectTimeout=15)
remote() { ssh -T -p "$port" "${ssh_opts[@]}" "$target" "$1"; }

remote_ready=1
remote "set -eu; test -d '$root'; for d in '$root/CELIKOM' '$root/CELIKOM/Windows' '$destination'; do test ! -L \"\$d\"; done; test ! -e '$stage'; mkdir -m 700 '$stage'"
for file in "$exe" "$zip" "$manifest"; do
  scp -P "$port" "${ssh_opts[@]}" "$package_dir/$file" "$target:$stage/$file"
done

remote "set -eu
  for d in '$root/CELIKOM' '$root/CELIKOM/Windows' '$destination'; do test ! -L \"\$d\"; done
  mkdir -p '$destination'
  for f in '$exe' '$zip' '$manifest'; do
    if test -e '$destination/'\"\$f\"; then
      old=\$(sha256sum '$destination/'\"\$f\" | awk '{print \$1}')
      new=\$(sha256sum '$stage/'\"\$f\" | awk '{print \$1}')
      test \"\$old\" = \"\$new\" || { echo 'W99_EXISTING_FILE_HASH_CONFLICT'; exit 3; }
      rm -f '$stage/'\"\$f\"
    else
      mv '$stage/'\"\$f\" '$destination/'\"\$f\"
    fi
  done
  cd '$destination'
  sha256sum -c '$manifest'
  chmod 755 '$root/CELIKOM' '$root/CELIKOM/Windows' '$destination'
  chmod 644 '$destination/'* 
  rmdir '$stage'"

for file in "$exe" "$zip" "$manifest"; do
  curl --fail --silent --show-error --retry 3 "$base_url/$file" -o "$work/$file"
done
(cd "$work" && sha256sum -c "$package_dir/$manifest")
echo 'W99_HOSTINGER_WINDOWS_TEST_PUBLISH_PASS'
