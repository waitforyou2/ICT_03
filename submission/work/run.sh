#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Usage: bash work/run.sh <code-repository> <design-doc-path> <output-directory>" >&2
  exit 2
fi

WORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(realpath "$1")"
DOCS="$(realpath "$2")"
OUTPUT="$(mkdir -p "$3" && realpath "$3")"
CODEGRAPH_BIN="${WORK_DIR}/.runtime/node_modules/.bin/codegraph"

if [[ ! -x "${CODEGRAPH_BIN}" ]]; then
  bash "${WORK_DIR}/setup.sh"
fi

export PYTHONPATH="${WORK_DIR}/specdiff${PYTHONPATH:+:${PYTHONPATH}}"
export CODEGRAPH_TELEMETRY=0
export DO_NOT_TRACK=1
export CODEGRAPH_NO_DAEMON=1

python3 -m specdiff analyze \
  --repo "${REPO}" \
  --docs "${DOCS}" \
  --output "${OUTPUT}" \
  --cache "${WORK_DIR}/specdiff/cache" \
  --offline \
  --codegraph required \
  --codegraph-bin "${CODEGRAPH_BIN}"

test -s "${OUTPUT}/findings.json"
test -s "${OUTPUT}/output.md"
test -s "${OUTPUT}/run-summary.json"
echo "RUN_COMPLETE output=${OUTPUT}"
