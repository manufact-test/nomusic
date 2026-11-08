#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
out="$(mktemp -d)"
trap 'rm -rf "$out"' EXIT
javac -encoding UTF-8 -d "$out" src/pro/celikom/oneplayer/SourceGate.java test/TestSourceGate.java
java -cp "$out" TestSourceGate
