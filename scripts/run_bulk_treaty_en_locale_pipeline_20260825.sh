#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python -m py_compile \
  scripts/build_bulk_treaty_en_locale_candidates_v3_20260825.py \
  scripts/promote_bulk_treaty_en_locale_candidates_20260825.py

python scripts/build_bulk_treaty_en_locale_candidates_v3_20260825.py
python scripts/promote_bulk_treaty_en_locale_candidates_20260825.py

if [ -f scripts/validate_treaty_excerpt_locales_20260824.py ]; then
  python scripts/validate_treaty_excerpt_locales_20260824.py
fi

if [ -f scripts/validate_web_contract.py ]; then
  python scripts/validate_web_contract.py
fi

git status --short
