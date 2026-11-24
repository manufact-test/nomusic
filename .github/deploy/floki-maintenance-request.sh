#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
python3 - <<'PY'
import pathlib,urllib.request,urllib.error,base64,hashlib,ssl,re
p=pathlib.Path("/srv/celikom/migration/sites-20261124/android-private/staging-owner-credentials.txt")
values={}
for line in p.read_text().splitlines():
    m=re.match(r"^\s*(HTTP Basic username|HTTP Basic password)\s*[:=]\s*(.*?)\s*$",line,re.I)
    if m: values[m[1].lower()]=m[2]
assert set(values)=={"http basic username","http basic password"}
auth="Basic "+base64.b64encode((values["http basic username"]+":"+values["http basic password"]).encode()).decode()
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None
opener=urllib.request.build_opener(NoRedirect,urllib.request.HTTPSHandler(context=ssl.create_default_context()))
def get(path,headers={}):
    return opener.open(urllib.request.Request("https://celikom.com"+path,headers={"Authorization":auth,**headers}),timeout=30)
for path,size,sha in [
    ("/downloads/windows/CELIKOM-Windows-0.24.55.exe",85145078,"f4c9a7881164ac7a9b5681d9f3568e5cbd3a9915c9e1da7b475caa20d3fb6487"),
    ("/downloads/extension/celikom-extension-0.4.73.zip",2489436,"968e34ef72927ce5be5007d1ed210a9b6910b45d4fa423b67fdc3db16a75becb")
]:
    with get(path) as f:
        assert f.status==200
        h=hashlib.sha256(); n=0
        while b:=f.read(1024*1024):
            n+=len(b); h.update(b)
        assert n==size and h.hexdigest()==sha
    print("AUTHENTICATED_DOWNLOAD_OK",path,n)
for path in ["/","/admin/"]:
    with get(path) as f: assert f.status==200 and len(f.read(2000000))>1000
    print("AUTHENTICATED_SITE_OK",path)
PY
echo '=== LOCAL API ROUTE CONFIG ==='
# Print only configuration directives necessary to review proxy routing.
for f in /etc/nginx/sites-enabled/*; do
  if grep -q '127.0.0.1:8081' "$f" && grep -q 'root /srv/celikom/app/' "$f"; then
    printf '%s\n' "$f"
    grep -E '^[[:space:]]*(listen|root|location|fastcgi_pass|fastcgi_param (SCRIPT_FILENAME|HTTPS|REMOTE_ADDR)|try_files|client_max_body_size|set_real_ip_from|real_ip_header|access_log|include)' "$f" || true
  fi
done
echo '=== FINAL IMPORT CAPACITY AND DATABASE STATE ==='
df -h /srv
docker inspect -f '{{.HostConfig.RestartPolicy.Name}} {{range .Mounts}}{{.Destination}} {{end}}' celikom-mdb-check-20261122
systemctl is-active mysql nginx php8.3-fpm
systemctl list-timers celikom-mirror-sync.timer --no-pager
echo CELIKOM_OWNER_DOWNLOADS_AND_CUTOVER_CAPACITY_VERIFIED
