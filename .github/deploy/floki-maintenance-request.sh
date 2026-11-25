#!/bin/bash
set -Eeuo pipefail
umask 077
# Idle, read-only maintenance checkpoint. The last additive backup failed before encryption.
# No restore, credentials, source freezes, DDL, uploads, or public changes here.
echo CELIKOM_FLOKI_MAINTENANCE_SAFE_NOOP_AFTER_CUTOVER
