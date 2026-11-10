"""Compare sanitized live metadata with audited source; never read deployment credentials."""
import hashlib
import json
import pathlib
import sys

observed = json.loads(pathlib.Path(sys.argv[1]).read_text())
hashes = observed.pop("source_sha256")
matches = {}
for name, digest in hashes.items():
    path = pathlib.Path("server") / name
    matches[name] = path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == digest
observed["audited_source_matches"] = matches
observed["all_audited_source_matches"] = all(matches.values())
print(json.dumps(observed, sort_keys=True))
