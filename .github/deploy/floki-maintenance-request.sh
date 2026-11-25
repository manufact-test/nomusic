#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Read-only audit of failed least-privilege intake bootstrap. Do not modify
# sudoers, account privileges, keys, databases, or production configuration.
name=celikom-windows-intake
if getent passwd "$name" >/dev/null; then echo WINDOWS_INTAKE_ACCOUNT_REMAINS; exit 1; fi
for p in /var/lib/celikom-windows-intake /usr/local/lib/celikom-windows-intake /etc/celikom-windows-intake /home/celops/.celikom-windows-intake-enrollment; do
  test ! -e "$p" && test ! -L "$p"
done
echo WINDOWS_INTAKE_FAILED_INSTALL_FULLY_ROLLED_BACK
visudo -c >/dev/null
for u in nobody www-data celikom-mirror celikom-deploy; do
  printf 'SUDO_LIST_ACCOUNT=%s\n' "$u"
  set +e
  output=$(sudo -n -l -U "$u" 2>&1)
  rc=$?
  set -e
  printf 'SUDO_LIST_STATUS=%s\n' "$rc"
  # Only the policy's yes/no classification, not command arguments or keys.
  if printf '%s\n' "$output" | grep -qiE 'not allowed to run sudo|not allowed to execute|may not run sudo'; then
    echo SUDO_LIST_VERDICT=NO_ALLOWED_COMMANDS
  elif printf '%s\n' "$output" | grep -qiE 'may run the following commands'; then
    echo SUDO_LIST_VERDICT=ALLOWED_COMMANDS_PRESENT
  else
    echo SUDO_LIST_VERDICT=OTHER_RESPONSE
  fi
done
echo WINDOWS_INTAKE_SUDO_AUDIT_OK
