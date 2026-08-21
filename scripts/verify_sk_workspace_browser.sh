#!/usr/bin/env bash

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${TAXTREAT_E2E_PORT:-8765}"
BASE_URL="http://127.0.0.1:${PORT}"
SESSION="taxtreat-sk-e2e"
SERVER_LOG="/tmp/taxtreat-sk-e2e-uvicorn.log"
STATUS=0
SERVER_PID=""

cd "$ROOT" || STATUS=1

if ! command -v agent-browser >/dev/null 2>&1; then
  echo "BROWSER_SMOKE_UNAVAILABLE: agent-browser command is not installed in this Codespace."
  STATUS=2
else
  python -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT" >"$SERVER_LOG" 2>&1 &
  SERVER_PID=$!

  READY=0
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    if python - <<PY >/dev/null 2>&1
from urllib.request import urlopen
urlopen("$BASE_URL/health/live", timeout=1).read()
PY
    then
      READY=1
      break
    fi
    sleep 1
  done

  if [ "$READY" -ne 1 ]; then
    echo "FAIL: local TaxTreat server did not become ready."
    cat "$SERVER_LOG"
    STATUS=1
  else
    agent-browser --session "$SESSION" open "$BASE_URL/ui" >/dev/null 2>&1 || STATUS=1
    agent-browser --session "$SESSION" wait --load networkidle >/dev/null 2>&1 || STATUS=1

    check_eval() {
      LABEL="$1"
      EXPRESSION="$2"
      RESULT="$(agent-browser --session "$SESSION" eval "$EXPRESSION" 2>/dev/null)"
      if [ "$RESULT" = "true" ]; then
        echo "PASS: $LABEL"
      else
        echo "FAIL: $LABEL -> $RESULT"
        STATUS=1
      fi
    }

    run_eval() {
      EXPRESSION="$1"
      agent-browser --session "$SESSION" eval "$EXPRESSION" >/dev/null 2>&1 || STATUS=1
      agent-browser --session "$SESSION" wait 120 >/dev/null 2>&1 || STATUS=1
    }

    check_eval "initial CZ source country" 'document.body.dataset.sourceCountry === "CZ"'
    check_eval "initial CZ currency" 'document.querySelector("#workspace-payment [name=currency]").value === "CZK"'
    check_eval "initial CZ runtime released" 'window.TaxTreatWorkspaceSourceCountry.getActiveContext().runtimeReleased === true'

    run_eval '(() => { const s=document.querySelector("#active-source-country"); s.value="SK"; s.dispatchEvent(new Event("change", {bubbles:true})); return true; })()'

    check_eval "SK source country" 'document.body.dataset.sourceCountry === "SK"'
    check_eval "SK EUR currency" 'document.querySelector("#workspace-payment [name=currency]").value === "EUR"'
    check_eval "SK runtime remains prerelease" 'window.TaxTreatWorkspaceSourceCountry.getActiveContext().runtimeReleased === false'
    check_eval "SK submit is disabled semantically" 'document.querySelector("#workspace-submit").getAttribute("aria-disabled") === "true"'
    check_eval "SK submit copy" 'document.querySelector("#workspace-submit").textContent.includes("Slovenský výpočet zatím není vydán")'
    check_eval "SK FX field hidden" 'document.querySelector("#workspace-exchange-rate-field").hidden === true'
    check_eval "SK compliance form visible in contract" 'window.TaxTreatWorkspaceSourceCountry.getActiveContext().complianceFormCode === "OZN4311v26"'
    check_eval "SK 15-day compliance deadline contract" 'window.TaxTreatWorkspaceSourceCountry.getActiveContext().notificationDeadlineRule === "15th_day_of_following_calendar_month" && window.TaxTreatWorkspaceSourceCountry.getActiveContext().remittanceDeadlineRule === "15th_day_of_following_calendar_month"'
    check_eval "SK ordinary annual WHT return is not configured" 'window.TaxTreatWorkspaceSourceCountry.getActiveContext().ordinaryAnnualWhtReturnConfigured === false'
    check_eval "SK CNB fetch is prohibited" '(async () => { try { await window.fetch("/exchange-rates/cnb?currency=USD&date=2026-08-19"); return false; } catch (e) { return e.message.includes("prohibited for Slovak"); } })()'

    run_eval '(() => { document.querySelector("[data-nav=payers]").click(); return true; })()'
    check_eval "SK payer page copy" 'document.querySelector("[data-view=payers] .page-title span").textContent.includes("Slovenské subjekty")'

    run_eval '(() => { document.querySelector("[data-nav=recipients]").click(); return true; })()'
    run_eval '(() => { document.querySelector("[data-view=recipients] [data-open-recipient]").click(); return true; })()'
    check_eval "SK PE label" '[...document.querySelectorAll("[data-view=recipient-detail] dt")].some(n => n.textContent.includes("Väzba príjmu na stálu prevádzkareň v SR"))'

    run_eval '(() => { document.querySelector("[data-nav=sources]").click(); return true; })()'
    check_eval "SK source metrics 75 / 225" '(() => { const a=[...document.querySelectorAll("[data-view=sources] .source-metrics strong")].map(n=>n.textContent.trim()); return a[0] === "75" && a[1] === "225"; })()'

    run_eval '(() => { const s=document.querySelector("#active-source-country"); s.value="CZ"; s.dispatchEvent(new Event("change", {bubbles:true})); return true; })()'
    check_eval "return to CZ source country" 'document.body.dataset.sourceCountry === "CZ"'
    check_eval "return to CZ currency" 'document.querySelector("#workspace-payment [name=currency]").value === "CZK"'
    check_eval "return to CZ source metrics 101 / 303" '(() => { const a=[...document.querySelectorAll("[data-view=sources] .source-metrics strong")].map(n=>n.textContent.trim()); return a[0] === "101" && a[1] === "303"; })()'

    run_eval '(() => { document.querySelector("[data-nav=recipients]").click(); return true; })()'
    run_eval '(() => { document.querySelector("[data-view=recipients] [data-open-recipient]").click(); return true; })()'
    check_eval "return to CZ PE label" '[...document.querySelectorAll("[data-view=recipient-detail] dt")].some(n => n.textContent.includes("Vazba ke stálé provozovně v ČR"))'

    if [ "$STATUS" -eq 0 ]; then
      echo "BROWSER_SMOKE_OK"
    else
      echo "BROWSER_SMOKE_FAILED"
      agent-browser --session "$SESSION" screenshot --full >/dev/null 2>&1 || true
    fi
  fi

  agent-browser --session "$SESSION" close >/dev/null 2>&1 || true
fi

if [ -n "$SERVER_PID" ]; then
  kill "$SERVER_PID" >/dev/null 2>&1 || true
  wait "$SERVER_PID" >/dev/null 2>&1 || true
fi

echo "Browser smoke status: $STATUS"
