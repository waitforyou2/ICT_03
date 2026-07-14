#!/usr/bin/env bash
set -euo pipefail

WORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="${WORK_DIR}/.runtime"
PACKAGE="@colbymchenry/codegraph@1.4.1"

command -v npm >/dev/null 2>&1 || {
  echo "ERROR: npm is required to install ${PACKAGE}." >&2
  exit 2
}

mkdir -p "${RUNTIME_DIR}"
npm install --prefix "${RUNTIME_DIR}" --no-audit --no-fund --save-exact "${PACKAGE}"

CODEGRAPH_BIN="${RUNTIME_DIR}/node_modules/.bin/codegraph"
test -x "${CODEGRAPH_BIN}" || {
  echo "ERROR: CodeGraph executable was not installed at ${CODEGRAPH_BIN}." >&2
  exit 3
}

CODEGRAPH_TELEMETRY=0 DO_NOT_TRACK=1 "${CODEGRAPH_BIN}" --version
python3 -m compileall -q "${WORK_DIR}/specdiff/specdiff"
echo "SETUP_COMPLETE"
