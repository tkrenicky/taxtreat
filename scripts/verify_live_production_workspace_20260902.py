from __future__ import annotations
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

URL="https://taxtreat.vercel.app/workspace-demo"
OUT=Path("reports/live_production_workspace_smoke_20260902.json")

def main():
    result={"url":URL,"blockers":[],"details":{}}
    page_errors=[]
    console_errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page()
        page.on("pageerror",lambda exc: page_errors.append(str(exc)))
        page.on("console",lambda msg: console_errors.append(msg.text) if msg.type=="error" else None)
        response=page.goto(URL,wait_until="domcontentloaded",timeout=20000)
        result["details"]["http_status"]=response.status if response else None
        if not response or response.status!=200:
            result["blockers"].append(f"Production workspace HTTP status is {response.status if response else 'none'}")
        page.wait_for_selector("#workspace-payment", state="attached", timeout=12000)
        try:
            page.wait_for_function("() => document.querySelector('#new-recipient-form select[name=recipient_country]')?.options.length >= 101",timeout=12000)
        except Exception:
            pass
        result["details"]["country_options"]=page.locator("#new-recipient-form select[name=recipient_country] option").count()-1
        result["details"]["source_countries"]=page.evaluate("() => Object.keys(window.TaxTreatSourceCountries?.countries || {})")
        result["details"]["build_version"]=page.evaluate("() => window.TaxTreatWorkspace?.buildVersion || null")
        for nav in ["dashboard","payers","recipients","reviews","sources"]:
            loc=page.locator(f"[data-nav='{nav}']").first
            if loc.count():
                loc.click()
                page.wait_for_timeout(80)
                if not page.locator(f"[data-view='{nav}']").is_visible():
                    result["blockers"].append(f"Live navigation failed: {nav}")
            else:
                result["blockers"].append(f"Live navigation button missing: {nav}")
        en=page.locator("#taxtreat-language-controls button[data-lang='en']")
        cs=page.locator("#taxtreat-language-controls button[data-lang='cs']")
        result["details"]["language_controls"]={"en":en.count(),"cs":cs.count()}
        if en.count() and cs.count():
            en.click(); page.wait_for_timeout(700)
            result["details"]["lang_after_en"]=page.evaluate("document.documentElement.lang")
            result["details"]["notice_after_en"]=page.locator(".information-only-note").inner_text()
            cs.click(); page.wait_for_timeout(700)
            result["details"]["lang_after_cs"]=page.evaluate("document.documentElement.lang")
        else:
            result["blockers"].append("Live CZ/EN language controls missing")
        if result["details"]["country_options"]!=101:
            result["blockers"].append(f"Live recipient selector exposes {result['details']['country_options']} countries, expected 101")
        result["details"]["page_errors"]=page_errors
        result["details"]["console_errors"]=console_errors
        if page_errors:
            result["blockers"].append(f"Live page emitted {len(page_errors)} uncaught page errors")
        browser.close()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__=="__main__":
    main()
