#!/usr/bin/env bash
# One-time owner-side installation of a restricted GitHub deployment endpoint.
set -Eeuo pipefail
umask 077
[[ $(id -u) == 0 ]] || { echo ROOT_REQUIRED; exit 1; }
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
USER_NAME=celikom-deploy
HOME_DIR=/var/lib/celikom-deploy
ENROLL=/home/celops/.celikom-deploy-enrollment
GATE=/usr/local/sbin/celikom-deploy-gateway
OPS=/usr/local/sbin/celikom-floki-ops
RULE=/etc/sudoers.d/celikom-deploy
if getent passwd "$USER_NAME" >/dev/null || [[ -e "$HOME_DIR" || -e "$ENROLL" || -e "$GATE" || -e "$OPS" || -e "$RULE" ]]; then
  echo FLOKI_DEPLOY_ALREADY_PRESENT_REVIEW_FIRST
  exit 1
fi
test -f /etc/ssh/ssh_host_ed25519_key.pub
test "$(awk '{print $1}' /etc/ssh/ssh_host_ed25519_key.pub)" = ssh-ed25519
test "$(stat -c '%u' /home/celops)" = "$(id -u celops)"
command -v git >/dev/null
command -v python3 >/dev/null
command -v sudo >/dev/null
if ! command -v node >/dev/null; then
  apt-get update -qq
  apt-get install -y --no-install-recommends nodejs
fi
work=$(mktemp -d /root/celikom-enroll.XXXXXXXX)
trap 'rm -rf -- "$work"' EXIT
cat > "$work/gateway" <<'GATEWAY'
#!/bin/bash
set -euo pipefail
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
case "${SSH_ORIGINAL_COMMAND:-}" in
  status) exec sudo -n /usr/local/sbin/celikom-floki-ops status ;;
  stage-release-02455) exec sudo -n /usr/local/sbin/celikom-floki-ops stage-release-02455 ;;
  android-build-input) exec sudo -n /usr/local/sbin/celikom-android-build-input-export ;;
  *) echo FLOKI_DEPLOY_COMMAND_REFUSED >&2; exit 64 ;;
esac
GATEWAY
cat > "$work/ops" <<'OPS_SCRIPT'
#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
[[ $(id -u) == 0 && $# == 1 ]] || exit 64
exec 9>/run/lock/celikom-floki-ops.lock
flock -n 9 || { echo FLOKI_DEPLOY_BUSY; exit 75; }
# The first successful key-authenticated command revokes the enrollment copy.
rm -f -- /home/celops/.celikom-deploy-enrollment
case "$1" in
  status)
    echo FLOKI_DEPLOY_SSH_OK
    systemctl is-active nginx php8.3-fpm celikom-ci-runner.service celikom-mirror-sync.timer
    df -h /srv/celikom
    curl -fsS --max-time 15 https://api.celikom.com/api/v1/health
    echo
    ;;
  stage-release-02455)
    IMP=/root/celikom-release-import/windows-02455
    TOOLS=/root/celikom-release-tools
    MIRROR=/home/celikom-mirror/github-mirror.git
    COMMIT=d647a00d324e3a3820379e9f63f6725637ecebe8
    PIN=/root/celikom-secrets/windows-stable-public.der
    EXT=/srv/celikom/releases/private/extension
    install -d -m 700 /root/celikom-release-import "$IMP" "$IMP/0.24.55" "$TOOLS" /srv/celikom/releases/private "$EXT"
    # Root never executes runner or owner-writable files; read regular files
    # through non-following directory descriptors, verify trusted digest, copy.
    python3 - <<'PY'
import os, stat, hashlib, pathlib, tempfile, json, zipfile, shutil
def read_exact(path, size, digest):
    parts = pathlib.PurePosixPath(path).parts
    fd = os.open("/", os.O_DIRECTORY | os.O_RDONLY)
    try:
        for p in parts[1:-1]:
            next_fd = os.open(p, os.O_DIRECTORY | os.O_NOFOLLOW | os.O_RDONLY, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        f = os.open(parts[-1], os.O_NOFOLLOW | os.O_RDONLY | os.O_NONBLOCK, dir_fd=fd)
        with os.fdopen(f, "rb") as stream:
            st = os.fstat(stream.fileno())
            if not stat.S_ISREG(st.st_mode) or st.st_size != size:
                raise RuntimeError("unexpected release input size/type")
            data = stream.read(size+1)
    finally:
        os.close(fd)
    if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
        raise RuntimeError("release input digest mismatch")
    return data
def write_exact(path, data):
    p = pathlib.Path(path)
    if p.exists() or p.is_symlink():
        if p.is_symlink() or not p.is_file() or p.read_bytes() != data:
            raise RuntimeError("immutable release conflict")
        return
    fd, name = tempfile.mkstemp(dir=p.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(name, 0o600)
        os.link(name, p)
    finally:
        os.unlink(name)
root = "/root/celikom-release-import/windows-02455/"
for name, dest, size, digest in [
    ("CELIKOM-Windows-0.24.55.exe", "0.24.55/CELIKOM-Windows-0.24.55.exe", 85145078, "f4c9a7881164ac7a9b5681d9f3568e5cbd3a9915c9e1da7b475caa20d3fb6487"),
    ("latest.json", "latest.json", 851, "9601539c709a554ec7e1f774756c78e2bfdda148d11ea7dd11946a9a5ec66d1a"),
    ("latest.json.sig", "latest.json.sig", 71, "a5974b77e7df9a4fb148445c66fed7ca9ed6f3282b398838991fba8b9efb25c9"),
    ("manifest-public-key.der", "manifest-public-key.der", 91, "46b36bb222154316f2229c35cf65e6c953e0b6524dfb0aad8de05949dc143a95"),
]:
    data = read_exact("/home/celops/"+name, size, digest)
    write_exact(root+dest, data)
    if name == "latest.json": write_exact(root+"0.24.55/manifest.json", data)
    if name == "latest.json.sig": write_exact(root+"0.24.55/manifest.json.sig", data)
    if name == "manifest-public-key.der": write_exact("/root/celikom-secrets/windows-stable-public.der", data)
spool = "/srv/celikom/ci-runner/runner/celikom-build-spool/61d17d9eb97f3db5c58c906e30da6c19ee737090-45446268377-1/"
name = "celikom-extension-0.4.73.zip"
data = read_exact(spool+name, 2489436, "968e34ef72927ce5be5007d1ed210a9b6910b45d4fa423b67fdc3db16a75becb")
dest = "/srv/celikom/releases/private/extension/"+name
write_exact(dest, data)
with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None
    config = json.loads(z.read("api/config.json"))
    manifest = json.loads(z.read("manifest.json"))
    assert config["baseUrl"] == "https://api.celikom.com"
    assert manifest["version"] == "0.4.73"
    assert set(manifest["host_permissions"]) == {"https://api.celikom.com/*", "https://music.yandex.ru/*"}
print("EXTENSION_VERIFIED")
PY
    for file in windows-stable-publish-floki.mjs windows-stable-release-verify.mjs windows-stable-existing-latest.mjs; do
      runuser -u celikom-mirror -- git --git-dir="$MIRROR" show "$COMMIT:.github/scripts/$file" > "$TOOLS/$file"
    done
    cd "$TOOLS"
    test "$(git hash-object windows-stable-publish-floki.mjs)" = dcb83ff6d2ac3097e6ca76437f8b1fac51f05a44
    test "$(git hash-object windows-stable-release-verify.mjs)" = ae38c2c48a032fec0ad1eaae14c444e43dfb2b18
    test "$(git hash-object windows-stable-existing-latest.mjs)" = bb4d19672d45bdd0393497c3b33280308d67ef32
    install -d -m 755 /srv/celikom/releases/windows /srv/celikom/releases/windows/stable
    STABLE=/srv/celikom/releases/windows/stable
    if [[ -L "$STABLE/current" ]]; then
      test "$(readlink "$STABLE/current")" = versions/0.24.55
      cmp "$STABLE/current/manifest.json" "$IMP/latest.json"
      cmp "$STABLE/current/manifest.json.sig" "$IMP/latest.json.sig"
      cmp "$STABLE/current/CELIKOM-Windows-0.24.55.exe" "$IMP/0.24.55/CELIKOM-Windows-0.24.55.exe"
      echo FLOKI_WINDOWS_FEED_ALREADY_STAGED
    else
      node "$TOOLS/windows-stable-publish-floki.mjs" "$IMP" 0.24.55 2 "$PIN"
    fi
    curl -fsS --max-time 15 https://api.celikom.com/api/v1/health
    echo
    echo CELIKOM_RELEASE_STORAGE_READY
    ;;
  *) exit 64 ;;
esac
OPS_SCRIPT
# Check generated scripts before changing account/SSH configuration.
bash -n "$work/gateway"
bash -n "$work/ops"
bash -n .github/scripts/floki-android-build-input-export.sh
cat > "$work/sudoers" <<'SUDOERS'
celikom-deploy ALL=(root) NOPASSWD: /usr/local/sbin/celikom-floki-ops status, /usr/local/sbin/celikom-floki-ops stage-release-02455, /usr/local/sbin/celikom-android-build-input-export
SUDOERS
visudo -cf "$work/sudoers"
ssh-keygen -q -t ed25519 -N '' -C celikom-floki-deploy -f "$work/key"
useradd --system --no-create-home --home-dir "$HOME_DIR" --shell /bin/bash "$USER_NAME"
install -d -o root -g root -m 755 "$HOME_DIR" "$HOME_DIR/.ssh"
install -o root -g root -m 755 "$work/gateway" "$GATE"
install -o root -g root -m 755 "$work/ops" "$OPS"
install -o root -g root -m 755 .github/scripts/floki-android-build-input-export.sh /usr/local/sbin/celikom-android-build-input-export
install -o root -g root -m 440 "$work/sudoers" "$RULE"
printf 'restrict,command="%s" %s\n' "$GATE" "$(cat "$work/key.pub")" > "$work/authorized_keys"
install -o root -g root -m 644 "$work/authorized_keys" "$HOME_DIR/.ssh/authorized_keys"
# Secret format: the trusted server host key on line 1, then the new private key.
# Never print this bundle; it is transferred once to the owner's clipboard.
printf '95.133.160.111 %s\n' "$(awk '{print $1 " " $2}' /etc/ssh/ssh_host_ed25519_key.pub)" > "$work/enrollment"
cat "$work/key" >> "$work/enrollment"
install -o celops -g "$(id -gn celops)" -m 600 "$work/enrollment" "$ENROLL"
sshd -t
visudo -c >/dev/null
echo FLOKI_DEPLOY_ENROLLMENT_READY
echo 'Use the existing authenticated SSH connection to transfer the enrollment bundle to GitHub; never paste it into chat.'
