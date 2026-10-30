"""Write non-secret release evidence from this CI run; not a signing step."""
from pathlib import Path
import json
import os
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from ci_provenance import prepare_provenance, validate_provenance

dex = ROOT / "android-native-classes2.dex"
commit = os.environ.get("GITHUB_SHA", "")
record = prepare_provenance(ROOT, commit, dex)
assert validate_provenance(record, ROOT, dex) == commit
output = ROOT / "ci-dex-provenance.json"
output.write_text(json.dumps(record, indent=2) + "\n")
print("PASS: current CI commit, Java sources, pinned signer and byte-identical JDK17 DEX bound", commit)
