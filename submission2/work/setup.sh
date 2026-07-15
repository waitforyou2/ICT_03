#!/usr/bin/env bash
set -euo pipefail

WORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="${WORK_DIR}/.runtime"
SKILL_DIR="${WORK_DIR}/skills/design-implementation-repair"
PACKAGE="@colbymchenry/codegraph@1.4.1"

if command -v python3 >/dev/null 2>&1 && python3 --version >/dev/null 2>&1; then
  PYTHON_BIN=python3
elif command -v python >/dev/null 2>&1 && python --version >/dev/null 2>&1; then
  PYTHON_BIN=python
else
  echo "ERROR: python3 is required." >&2
  exit 2
fi

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

export CODEGRAPH_TELEMETRY=0
export DO_NOT_TRACK=1
export CODEGRAPH_NO_DAEMON=1
"${CODEGRAPH_BIN}" --version
"${PYTHON_BIN}" -m compileall -q "${SKILL_DIR}/scripts"
echo "SETUP_COMPLETE"
