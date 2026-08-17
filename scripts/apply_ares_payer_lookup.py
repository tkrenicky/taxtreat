from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Expected marker missing: {label}")
    return text.replace(old, new, 1)


def patch_backend() -> None:
    path = ROOT / "app" / "main.py"
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "from typing import Any, Literal\n",
        "from typing import Any, Literal\nfrom urllib.error import HTTPError, URLError\nfrom urllib.request import Request, urlopen\n",
        "urllib imports",
    )
    marker = '''@app.get("/health")
def health_check():
    """Backward-compatible liveness alias."""
    return liveness()


'''
    endpoint = '''@app.get("/health")
def health_check():
    """Backward-compatible liveness alias."""
    return liveness()


def _normalize_ares_subject(payload: dict[str, Any]) -> dict[str, Any]:
    sidlo = payload.get("sidlo") or {}
    data_boxes = payload.get("datoveSchranky") or []
    data_box = ""
    if isinstance(data_boxes, list) and data_boxes:
        first = data_boxes[0]
        if isinstance(first, dict):
            data_box = str(first.get("datovaSchranka") or first.get("idDatoveSchranky") or "")
        elif first:
            data_box = str(first)

    address = str(sidlo.get("textovaAdresa") or "").strip()
    if not address:
        street = str(sidlo.get("nazevUlice") or sidlo.get("nazevCastiObce") or "").strip()
        house = str(sidlo.get("cisloDomovni") or "").strip()
        orientation = str(sidlo.get("cisloOrientacni") or "").strip()
        number = house + (f"/{orientation}" if orientation else "")
        municipality = str(sidlo.get("nazevObce") or "").strip()
        psc = str(sidlo.get("psc") or "").strip()
        address = " ".join(part for part in (street, number) if part).strip()
        locality = " ".join(part for part in (psc, municipality) if part).strip()
        address = ", ".join(part for part in (address, locality) if part)

    return {
        "source": "ARES",
        "source_url": f"https://ares.gov.cz/ekonomicke-subjekty?ico={payload.get('ico', '')}",
        "ico": str(payload.get("ico") or ""),
        "name": str(payload.get("obchodniJmeno") or ""),
        "vat_id": str(payload.get("dic") or ""),
        "address": address,
        "legal_form": str(payload.get("pravniForma") or ""),
        "data_box": data_box,
        "established_at": str(payload.get("datumVzniku") or ""),
    }


@app.get("/company-registry/ares/{ico}")
def company_registry_ares(ico: str):
    normalized_ico = "".join(character for character in ico if character.isdigit())
    if len(normalized_ico) != 8:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_ICO", "message": "IČO musí obsahovat 8 číslic."},
        )

    url = (
        "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/"
        f"ekonomicke-subjekty/{normalized_ico}"
    )
    request = Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "TaxTreat/0.2 (+https://taxtreat.vercel.app)"},
    )
    try:
        with urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404:
            raise HTTPException(
                status_code=404,
                detail={"code": "ARES_NOT_FOUND", "message": "Subjekt s tímto IČO nebyl v ARES nalezen."},
            ) from exc
        raise HTTPException(
            status_code=502,
            detail={"code": "ARES_UNAVAILABLE", "message": "ARES nyní není dostupný."},
        ) from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=502,
            detail={"code": "ARES_UNAVAILABLE", "message": "ARES nyní není dostupný."},
        ) from exc

    if not isinstance(payload, dict) or not payload.get("ico"):
        raise HTTPException(
            status_code=502,
            detail={"code": "ARES_INVALID_RESPONSE", "message": "ARES vrátil neočekávanou odpověď."},
        )
    return _normalize_ares_subject(payload)


'''
    text = replace_once(text, marker, endpoint, "ARES endpoint insertion")
    path.write_text(text, encoding="utf-8")


def patch_html() -> None:
    path = ROOT / "app" / "web" / "workspace.html"
    text = path.read_text(encoding="utf-8")
    old = '''      <label><span>Název *</span><input name="payer_name" value="Demo CZ s.r.o." required></label>
      <label><span>IČO</span><input name="payer_id" inputmode="numeric" placeholder="např. 12345678"></label>
      <label><span>DIČ</span><input name="payer_vat_id" placeholder="např. CZ12345678"></label>
      <label><span>Stát</span><input value="Česká republika" disabled></label>'''
    new = '''      <label><span>IČO *</span><div class="ico-lookup"><input name="payer_id" inputmode="numeric" maxlength="8" pattern="[0-9]{8}" placeholder="např. 27082440" required><button class="secondary compact" type="button" data-ares-lookup>Načíst z ARES</button></div><small id="ares-lookup-status" class="lookup-status" aria-live="polite">Po zadání 8 číslic TaxTreat načte identifikační údaje z ARES.</small></label>
      <label><span>Název *</span><input name="payer_name" value="Demo CZ s.r.o." required></label>
      <label><span>DIČ</span><input name="payer_vat_id" placeholder="např. CZ12345678"></label>
      <label><span>Sídlo</span><input name="payer_address" placeholder="Načte se z ARES"></label>
      <label><span>Právní forma</span><input name="payer_legal_form" placeholder="Načte se z ARES"></label>
      <label><span>Datová schránka</span><input name="payer_data_box" placeholder="Načte se z ARES"></label>
      <label><span>Datum vzniku</span><input name="payer_established_at" type="date"></label>
      <label><span>Stát</span><input value="Česká republika" disabled></label>'''
    text = replace_once(text, old, new, "payer dialog ARES fields")
    path.write_text(text, encoding="utf-8")


def patch_css() -> None:
    path = ROOT / "app" / "web" / "workspace.css"
    text = path.read_text(encoding="utf-8")
    text += "\n.ico-lookup{display:grid;grid-template-columns:1fr auto;gap:8px}.ico-lookup .secondary{min-width:132px;padding:10px 12px}.lookup-status{display:block;margin-top:6px;color:var(--muted);font-size:.72rem}.lookup-status.success{color:var(--green)}.lookup-status.error{color:var(--red)}@media(max-width:700px){.ico-lookup{grid-template-columns:1fr}.ico-lookup .secondary{width:100%}}\n"
    path.write_text(text, encoding="utf-8")


def patch_js() -> None:
    path = ROOT / "app" / "web" / "workspace.js"
    text = path.read_text(encoding="utf-8")
    old_payers = '''  let payers = [
    { key: "demo-cz", name: "Demo CZ s.r.o.", id: "12345678", vatId: "CZ12345678" },
    { key: "alfa-cz", name: "Alfa Services CZ a.s.", id: "87654321", vatId: "CZ87654321" }
  ];'''
    new_payers = '''  let payers = [
    { key: "demo-cz", name: "Demo CZ s.r.o.", id: "12345678", vatId: "CZ12345678", address: "", legalForm: "", dataBox: "", establishedAt: "" },
    { key: "alfa-cz", name: "Alfa Services CZ a.s.", id: "87654321", vatId: "CZ87654321", address: "", legalForm: "", dataBox: "", establishedAt: "" }
  ];'''
    text = replace_once(text, old_payers, new_payers, "payer model extension")

    old_dialog = '''    payerForm.elements.payer_name.value = selected?.name || "";
    payerForm.elements.payer_id.value = selected?.id || "";
    payerForm.elements.payer_vat_id.value = selected?.vatId || "";
    payerDialog.showModal();'''
    new_dialog = '''    payerForm.elements.payer_name.value = selected?.name || "";
    payerForm.elements.payer_id.value = selected?.id || "";
    payerForm.elements.payer_vat_id.value = selected?.vatId || "";
    payerForm.elements.payer_address.value = selected?.address || "";
    payerForm.elements.payer_legal_form.value = selected?.legalForm || "";
    payerForm.elements.payer_data_box.value = selected?.dataBox || "";
    payerForm.elements.payer_established_at.value = selected?.establishedAt || "";
    document.querySelector("#ares-lookup-status").className = "lookup-status";
    document.querySelector("#ares-lookup-status").textContent = "Po zadání 8 číslic TaxTreat načte identifikační údaje z ARES.";
    payerDialog.showModal();'''
    text = replace_once(text, old_dialog, new_dialog, "payer dialog hydration")

    marker = '''  document.querySelectorAll("[data-close-payer]").forEach((button) => button.addEventListener("click", () => payerDialog.close()));
  payerForm.addEventListener("submit", (event) => {'''
    lookup = '''  document.querySelectorAll("[data-close-payer]").forEach((button) => button.addEventListener("click", () => payerDialog.close()));

  let aresLookupTimer = null;
  async function lookupPayerFromAres() {
    const ico = String(payerForm.elements.payer_id.value || "").replace(/\\D/g, "");
    const status = document.querySelector("#ares-lookup-status");
    if (ico.length !== 8) {
      status.className = "lookup-status error";
      status.textContent = "IČO musí obsahovat přesně 8 číslic.";
      return;
    }
    status.className = "lookup-status";
    status.textContent = "Načítám údaje z ARES…";
    try {
      const response = await fetch(`/company-registry/ares/${ico}`, { cache: "no-store" });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail?.message || "ARES lookup failed");
      payerForm.elements.payer_id.value = body.ico || ico;
      payerForm.elements.payer_name.value = body.name || payerForm.elements.payer_name.value;
      payerForm.elements.payer_vat_id.value = body.vat_id || payerForm.elements.payer_vat_id.value;
      payerForm.elements.payer_address.value = body.address || "";
      payerForm.elements.payer_legal_form.value = body.legal_form || "";
      payerForm.elements.payer_data_box.value = body.data_box || "";
      payerForm.elements.payer_established_at.value = body.established_at || "";
      status.className = "lookup-status success";
      status.textContent = "Údaje byly načteny z ARES. Před uložením je můžeš upravit.";
    } catch (_problem) {
      status.className = "lookup-status error";
      status.textContent = "Údaje se z ARES nepodařilo načíst. Pole můžeš vyplnit ručně.";
    }
  }
  document.querySelector("[data-ares-lookup]").addEventListener("click", lookupPayerFromAres);
  payerForm.elements.payer_id.addEventListener("input", () => {
    window.clearTimeout(aresLookupTimer);
    const ico = String(payerForm.elements.payer_id.value || "").replace(/\\D/g, "");
    if (ico.length === 8) aresLookupTimer = window.setTimeout(lookupPayerFromAres, 450);
  });

  payerForm.addEventListener("submit", (event) => {'''
    text = replace_once(text, marker, lookup, "ARES UI lookup")

    old_values = '''    const values = { name: String(data.get("payer_name")).trim(), id: String(data.get("payer_id")).trim(), vatId: String(data.get("payer_vat_id")).trim() };'''
    new_values = '''    const values = {
      name: String(data.get("payer_name")).trim(),
      id: String(data.get("payer_id")).trim(),
      vatId: String(data.get("payer_vat_id")).trim(),
      address: String(data.get("payer_address")).trim(),
      legalForm: String(data.get("payer_legal_form")).trim(),
      dataBox: String(data.get("payer_data_box")).trim(),
      establishedAt: String(data.get("payer_established_at")).trim()
    };'''
    text = replace_once(text, old_values, new_values, "payer save values")

    old_meta = '    const meta = document.createElement("p"); meta.textContent = `Česká republika · IČO ${item.id || "neuvedeno"}${item.vatId ? ` · DIČ ${item.vatId}` : ""}`;'
    new_meta = '    const meta = document.createElement("p"); meta.textContent = `Česká republika · IČO ${item.id || "neuvedeno"}${item.vatId ? ` · DIČ ${item.vatId}` : ""}${item.address ? ` · ${item.address}` : ""}`;'
    text = replace_once(text, old_meta, new_meta, "payer card address")
    path.write_text(text, encoding="utf-8")


def patch_browser_test() -> None:
    path = ROOT / "scripts" / "check_workspace_report_export.py"
    text = path.read_text(encoding="utf-8")
    marker = '''            verify_recipient_catalog_and_entry(page)
            finish_workspace_calculation(page)
'''
    replacement = '''            page.route(
                "**/company-registry/ares/27082440",
                lambda route: route.fulfill(
                    status=200,
                    content_type="application/json",
                    body='{"source":"ARES","ico":"27082440","name":"Google Czech Republic, s.r.o.","vat_id":"CZ27082440","address":"Stroupežnického 3191/17, 150 00 Praha 5","legal_form":"112","data_box":"amqg4i4","established_at":"2003-10-08"}',
                ),
            )
            page.goto(f"{BASE_URL}/workspace-demo", wait_until="networkidle")
            page.get_by_role("button", name="Plátci", exact=True).click()
            page.get_by_role("button", name="Přidat plátce", exact=True).click()
            payer_form = page.locator("#payer-form")
            payer_form.locator('input[name="payer_id"]').fill("27082440")
            payer_form.locator('input[name="payer_name"]').wait_for()
            page.wait_for_function("() => document.querySelector('#payer-form input[name=payer_name]').value.includes('Google Czech')", timeout=5000)
            if payer_form.locator('input[name="payer_address"]').input_value() != "Stroupežnického 3191/17, 150 00 Praha 5":
                raise AssertionError("ARES lookup did not populate payer address.")
            if payer_form.locator('input[name="payer_data_box"]').input_value() != "amqg4i4":
                raise AssertionError("ARES lookup did not populate payer data box.")
            page.get_by_role("button", name="Zrušit", exact=True).last.click()

            verify_recipient_catalog_and_entry(page)
            finish_workspace_calculation(page)
'''
    text = replace_once(text, marker, replacement, "ARES browser acceptance")
    path.write_text(text, encoding="utf-8")


def patch_unit_test() -> None:
    path = ROOT / "tests" / "test_ares_company_registry.py"
    path.write_text('''from app.main import _normalize_ares_subject\n\n\ndef test_normalize_ares_subject_exposes_form_fields():\n    payload = {\n        "ico": "27082440",\n        "obchodniJmeno": "Google Czech Republic, s.r.o.",\n        "dic": "CZ27082440",\n        "pravniForma": "112",\n        "datumVzniku": "2003-10-08",\n        "sidlo": {"textovaAdresa": "Stroupežnického 3191/17, 150 00 Praha 5"},\n        "datoveSchranky": [{"datovaSchranka": "amqg4i4"}],\n    }\n    result = _normalize_ares_subject(payload)\n    assert result["ico"] == "27082440"\n    assert result["name"] == "Google Czech Republic, s.r.o."\n    assert result["vat_id"] == "CZ27082440"\n    assert result["address"] == "Stroupežnického 3191/17, 150 00 Praha 5"\n    assert result["legal_form"] == "112"\n    assert result["data_box"] == "amqg4i4"\n    assert result["established_at"] == "2003-10-08"\n''', encoding="utf-8")


def main() -> None:
    patch_backend()
    patch_html()
    patch_css()
    patch_js()
    patch_browser_test()
    patch_unit_test()
    print("ARES payer lookup applied.")


if __name__ == "__main__":
    main()
