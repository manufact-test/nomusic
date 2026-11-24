#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
python3 - <<'PY'
from pathlib import Path
from urllib.parse import urlparse
candidates=[Path("/root/celikom-cutover-prepared/api.env"),Path("/srv/celikom/app/staging-20261122/.env")]
for p in candidates:
 if not p.is_file(): continue
 vals={}
 for line in p.read_text(errors="ignore").splitlines():
  line=line.strip()
  if not line or line.startswith("#") or "=" not in line: continue
  k,v=line.split("=",1); vals[k.strip()]=v.strip().strip("\"'")
 host=vals.get("MAIL_HOST") or vals.get("SMTP_HOST") or vals.get("BREVO_SMTP_HOST")
 port=vals.get("MAIL_PORT") or vals.get("SMTP_PORT") or vals.get("BREVO_SMTP_PORT")
 dsn=vals.get("MAILER_DSN") or vals.get("SMTP_DSN")
 if dsn and not host:
  u=urlparse(dsn)
  host=u.hostname
  port=port or str(u.port or (465 if u.scheme=="smtps" else 587))
 if host:
  print("SMTP_TARGET",host,int(port or 587))
  break
else:
 raise SystemExit("SMTP_HOST_NOT_FOUND_IN_EXPECTED_PRIVATE_CONFIGS")
PY
read -r HOST PORT < <(python3 - <<'PY'
from pathlib import Path
from urllib.parse import urlparse
for p in [Path("/root/celikom-cutover-prepared/api.env"),Path("/srv/celikom/app/staging-20261122/.env")]:
 if not p.is_file(): continue
 d={}
 for l in p.read_text(errors="ignore").splitlines():
  l=l.strip()
  if l and not l.startswith("#") and "=" in l:
   k,v=l.split("=",1); d[k.strip()]=v.strip().strip("\"'")
 h=d.get("MAIL_HOST") or d.get("SMTP_HOST") or d.get("BREVO_SMTP_HOST")
 po=d.get("MAIL_PORT") or d.get("SMTP_PORT") or d.get("BREVO_SMTP_PORT")
 x=d.get("MAILER_DSN") or d.get("SMTP_DSN")
 if x and not h:
  u=urlparse(x); h=u.hostname; po=po or str(u.port or (465 if u.scheme=="smtps" else 587))
 if h:
  print(h,po or 587); break
PY
)
echo '=== SMTP DNS and TCP/TLS reachability only; no credentials or mail sent ==='
getent ahostsv4 "$HOST" | head -n 2
if timeout 12 openssl s_client -starttls smtp -connect "$HOST:$PORT" -servername "$HOST" -brief </dev/null 2>&1 | grep -E 'CONNECTION ESTABLISHED|Protocol version|Ciphersuite|Verification:|Verify return code|CONNECTED'; then
  echo CELIKOM_SMTP_TLS_HANDSHAKE_OK
else
  echo CELIKOM_SMTP_TLS_HANDSHAKE_NOT_CONFIRMED
  exit 1
fi
