#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
GATE=/usr/local/sbin/celikom-deploy-gateway
HELPER=/usr/local/sbin/celikom-android-build-input-export
RULE=/etc/sudoers.d/celikom-deploy
[[ -f "$GATE" && ! -L "$GATE" && $(stat -c '%u:%a' "$GATE") == 0:755 ]]
[[ -f "$RULE" && ! -L "$RULE" && $(stat -c '%u:%a' "$RULE") == 0:440 ]]
[[ ! -e "$HELPER" && ! -L "$HELPER" ]]
work=$(mktemp -d /root/celikom-android-export.XXXXXXXX)
trap 'rm -rf -- "$work"' EXIT
cat > "$work/helper" <<'HELPER_SCRIPT'
#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
[[ $(id -u) == 0 && $# == 0 ]] || exit 64
FILE=/srv/celikom-releases/private/android-build-inputs/CELIKOM-0.3.22-install.apk
[[ -f "$FILE" && ! -L "$FILE" ]]
[[ $(stat -c '%u:%a:%s' "$FILE") == 0:600:8587421 ]]
[[ $(sha256sum "$FILE" | cut -d' ' -f1) == 170b1883e292570d28a3b5c619cf000eaccd9d11ee85ca6f6c08f7b50e5f72c9 ]]
exec cat -- "$FILE"
HELPER_SCRIPT
python3 - "$GATE" "$work/gateway" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1]).read_text()
needle='  stage-release-02455) exec sudo -n /usr/local/sbin/celikom-floki-ops stage-release-02455 ;;'
assert p.count(needle)==1 and 'android-build-input)' not in p
p=p.replace(needle,needle+'\n  android-build-input) exec sudo -n /usr/local/sbin/celikom-android-build-input-export ;;')
pathlib.Path(sys.argv[2]).write_text(p)
PY
cat > "$work/sudoers" <<'SUDOERS'
celikom-deploy ALL=(root) NOPASSWD: /usr/local/sbin/celikom-floki-ops status, /usr/local/sbin/celikom-floki-ops stage-release-02455, /usr/local/sbin/celikom-android-build-input-export
SUDOERS
bash -n "$work/helper"
bash -n "$work/gateway"
visudo -cf "$work/sudoers"
install -o root -g root -m 755 "$work/helper" "$HELPER"
install -o root -g root -m 755 "$work/gateway" "$GATE"
install -o root -g root -m 440 "$work/sudoers" "$RULE"
visudo -c >/dev/null
echo CELIKOM_ANDROID_READONLY_EXPORT_READY
