#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [[ ! -d ".git" ]]; then
  echo "No .git directory found. Skipping hook install."
  exit 0
fi

HOOKS_DIR=".git/hooks"
mkdir -p "${HOOKS_DIR}"

SRC="scripts/githooks/pre-commit"
DST="${HOOKS_DIR}/pre-commit"

cp "${SRC}" "${DST}"
chmod +x "${DST}"
echo "Installed git hook: ${DST}"
