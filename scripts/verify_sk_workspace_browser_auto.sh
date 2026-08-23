#!/usr/bin/env bash

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

if command -v agent-browser >/dev/null 2>&1; then
  exec bash scripts/verify_sk_workspace_browser.sh
fi

exec python scripts/verify_sk_workspace_playwright.py
