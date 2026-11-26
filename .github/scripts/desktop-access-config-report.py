"""Compare sanitized live metadata with audited source; never read deployment credentials."""
import hashlib
import json
import pathlib
import sys

observed = json.loads(pathlib.Path(sys.argv[1]).read_text())
hashes = observed.pop("source_sha256")
matches = {}
for name, digest in hashes.items():
    import subprocess
    baseline = subprocess.run(["git", "show", "7e648eacaeb50cc371842590ed7a30284e440d2a:server/" + name],
                              check=True, capture_output=True).stdout
    matches[name] = hashlib.sha256(baseline).hexdigest() == digest
# The live source was created by the pinned W45 surgical release, which inserted
# a redundant three-line native CORS allowlist entry into the prior Application.
# Its expected SHA is fixed by that release's own candidate/activation checks.
known_w45 = hashes.get("src/Application.php") == "920a4fa28357a3e61d6af64085448eacc76ea8c3c3c1946597b6428e61b506e0"
observed["audited_source_matches"] = matches
observed["known_w45_application"] = known_w45
observed["live_source_covered_by_audit"] = known_w45 and all(
    match for name, match in matches.items() if name != "src/Application.php")
print(json.dumps(observed, sort_keys=True))
