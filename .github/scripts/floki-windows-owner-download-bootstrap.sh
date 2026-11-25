#!/bin/bash
# One-time root-only private owner download route. Future releases change
# ONLY immutable verified files and the latest hardlink, never Nginx config.
set -Eeuo pipefail
umask 077
[[ "$(id -u)" == 0 ]]
SITE=/etc/nginx/sites-enabled/celikom-site-https
[[ -f "$SITE" ]]
REAL=$(readlink -f "$SITE")
[[ "$REAL" == /etc/nginx/sites-available/* && ! -L "$REAL" ]]
backup=$(mktemp -d /root/celikom-windows-owner-route-backup.XXXXXXXX)
cp -a "$REAL" "$backup/site.conf"
done_ok=0
rollback(){
  if [[ "$done_ok" != 1 ]]; then
    cp -a "$backup/site.conf" "$REAL"
    nginx -t && systemctl reload nginx
    echo WINDOWS_OWNER_NGINX_ROLLBACK_DONE
  fi
}
trap rollback EXIT
python3 - "$REAL" <<'PY'
import os,pathlib,re,stat,sys,tempfile
p=pathlib.Path(sys.argv[1])
s=p.read_text()
begin="    # BEGIN CELIKOM OWNER DOWNLOADS\n"
end="    # END CELIKOM OWNER DOWNLOADS\n"
assert s.count(begin)==1 and s.count(end)==1,"OWNER_DOWNLOAD_MARKER_CONFLICT"
assert 'auth_basic "CELIKOM private review";' in s and "auth_basic_user_file" in s
assert "location = /downloads/windows/CELIKOM-Windows-0.24.55.exe" in s
marker="    # CELIKOM OWNER WINDOWS SIGNED DYNAMIC ROUTES"
if marker in s:
    assert s.count(marker)==1 and "CELIKOM-Windows-latest.exe" in s
    print("WINDOWS_OWNER_DYNAMIC_NGINX_ALREADY_PRESENT")
    raise SystemExit(0)
assert "location = /downloads/windows/CELIKOM-Windows-latest.exe" not in s
assert "(?<celikomwinver>" not in s
routes=r'''    # CELIKOM OWNER WINDOWS SIGNED DYNAMIC ROUTES
    # Only files separately copied from root-pinned P-256 verified releases.
    # Site-level Basic Authentication is deliberately inherited.
    location ~ ^/downloads/windows/CELIKOM-Windows-(?<celikomwinver>(?:0|[1-9][0-9]{0,3})\.(?:0|[1-9][0-9]{0,3})\.(?:0|[1-9][0-9]{0,4}))\.exe$ {
        alias /srv/celikom-releases/owner-downloads/CELIKOM-Windows-$celikomwinver.exe;
        default_type application/octet-stream;
        add_header Content-Disposition 'attachment; filename="CELIKOM-Windows-$celikomwinver.exe"' always;
        add_header X-Robots-Tag "noindex, nofollow" always;
        add_header Cache-Control "private, no-store" always;
        access_log off;
        limit_except GET { deny all; }
    }
    location = /downloads/windows/CELIKOM-Windows-latest.exe {
        alias /srv/celikom-releases/owner-downloads/CELIKOM-Windows-latest.exe;
        default_type application/octet-stream;
        add_header Content-Disposition 'attachment; filename="CELIKOM-Windows-latest.exe"' always;
        add_header X-Robots-Tag "noindex, nofollow" always;
        add_header Cache-Control "private, no-store" always;
        access_log off;
        limit_except GET { deny all; }
    }
'''
s=s.replace(end,routes+end)
st=p.stat()
fd,tmp=tempfile.mkstemp(prefix=".windows-owner-route-",dir=p.parent)
try:
    with os.fdopen(fd,"w") as f:
        f.write(s);f.flush();os.fsync(f.fileno())
    os.chown(tmp,st.st_uid,st.st_gid)
    os.chmod(tmp,stat.S_IMODE(st.st_mode))
    os.replace(tmp,p)
finally:
    if os.path.lexists(tmp):os.unlink(tmp)
print("WINDOWS_OWNER_PRIVATE_DYNAMIC_NGINX_INSTALLED")
PY
nginx -t
systemctl reload nginx
python3 - <<'PY'
import urllib.request,urllib.error
for path in (
    "/downloads/windows/CELIKOM-Windows-latest.exe",
    "/downloads/windows/CELIKOM-Windows-0.24.56.exe",
    "/downloads/windows/CELIKOM-Windows-0.24.55.exe"):
    url="https://celikom.com"+path
    try:
        with urllib.request.urlopen(urllib.request.Request(url),timeout=18) as r:
            raise RuntimeError("ANONYMOUS_RELEASE_EXPOSED:"+str(r.status))
    except urllib.error.HTTPError as e:
        assert e.code==401,("PRIVATE_OWNER_GATE_FAILED",path,e.code)
    print("WINDOWS_OWNER_PRIVATE_ROUTE_401",path)
PY
done_ok=1
echo WINDOWS_OWNER_NGINX_DYNAMIC_ROUTE_READY
