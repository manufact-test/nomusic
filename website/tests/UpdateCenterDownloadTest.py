#!/usr/bin/env python3
"""HTTP contract checks using a fake APK. NOT a signature/release verification."""
import hashlib
import json
import pathlib
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "public/update-center.php"
CERT = "67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f"

def fetch(url, method="GET"):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method=method), timeout=2) as response:
            return response.status, response.headers, response.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()

def run():
    if not shutil.which("php"):
        raise SystemExit("PHP CLI required for HTTP regression")
    with tempfile.TemporaryDirectory() as temp:
        root = pathlib.Path(temp)
        public = root / "public"
        private = root / "celikom-private/android-updates"
        releases = private / "releases"
        public.mkdir()
        releases.mkdir(parents=True)
        shutil.copyfile(SOURCE, public / "update-center.php")
        data = bytes(range(256)) * 500
        digest = hashlib.sha256(data).hexdigest()
        filename = f"57-{digest}.apk"
        (releases / filename).write_bytes(data)
        manifest = {
            "schemaVersion": 1, "channel": "stable", "enabled": True,
            "packageName": "pro.celikom.nativeprobe", "versionCode": 57,
            "versionName": "0.3.56", "apkUrl": "https://example.test/releases/android/" + filename,
            "apkSha256": digest, "sizeBytes": len(data), "signerSha256": CERT,
            "minSdk": 28, "publishedAt": "2026-10-30T00:00:00Z", "notesRu": "Test"
        }
        pointer = private / "stable.json"
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        proc = subprocess.Popen(["php", "-S", f"127.0.0.1:{port}",
            "-t", str(public), str(public / "update-center.php")],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        base = f"http://127.0.0.1:{port}"
        try:
            for _ in range(50):
                try:
                    fetch(base + "/download/android")
                    break
                except Exception:
                    time.sleep(0.1)
            assert fetch(base + "/download/android")[0] == 503
            pointer.write_text(json.dumps(manifest))
            for path in ("/download/android", "/download/android/", "/releases/android/" + filename):
                status, headers, body = fetch(base + path)
                assert status == 200, (path, status)
                assert body == data, path
                assert headers.get_content_type() == "application/vnd.android.package-archive"
                assert headers["Content-Length"] == str(len(data))
                assert headers["Content-Disposition"] == 'attachment; filename="CELIKOM-Android.apk"'
                status, head, body = fetch(base + path, "HEAD")
                assert status == 200 and head["Content-Length"] == str(len(data)) and not body
            status, headers, body = fetch(base + "/updates/android/stable.json")
            assert status == 200 and json.loads(body)["versionCode"] == 57
            status, _, _ = fetch(base + "/releases/android/57-" + "0"*64 + ".apk")
            assert status == 404
            manifest["signerSha256"] = "a"*64
            pointer.write_text(json.dumps(manifest))
            assert fetch(base + "/download/android")[0] == 503
            manifest["signerSha256"] = CERT
            manifest["sizeBytes"] = len(data)+1
            pointer.write_text(json.dumps(manifest))
            assert fetch(base + "/download/android")[0] == 503
            manifest["sizeBytes"] = len(data)
            pointer.write_text(json.dumps(manifest))
            assert fetch(base + "/download/android", "POST")[0] == 405
            print("PASS: download GET/HEAD, MIME, headers, immutable route, JSON, rejects missing/invalid release")
        finally:
            proc.terminate()
            proc.wait(timeout=5)

if __name__ == "__main__":
    run()
