#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

RUNNER="bash -lc"
if command -v conda >/dev/null 2>&1; then
  if conda env list | grep -q '^photonflow'; then
    RUNNER="conda run -n photonflow bash -lc"
  fi
fi

echo "==> Generate docs"
${RUNNER} "PYTHONPATH=backend/src python backend/scripts/generate_param_docs.py"

echo "==> Run backend tests"
${RUNNER} "PYTHONPATH=backend/src python -m unittest discover -s backend/tests"

echo "==> Done"
