from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "taxtreat" / "services" / "reporting" / "client_report.py"

_OLD = '''    calc_base = calc_tax = net_amount = "—"\n    fx_line = ""\n    if calculation.get("status") == "CALCULATED":\n        gross_czk = calculation.get("gross_amount_czk")\n        tax_czk = calculation.get("withholding_tax_czk")\n        net_czk = calculation.get("net_amount_czk")\n        if net_czk in (None, "") and gross_czk not in (None, "") and tax_czk not in (None, ""):\n            try:\n                net_czk = float(gross_czk) - float(tax_czk)\n            except (TypeError, ValueError):\n                net_czk = None\n        calc_base = f"{_number(gross_czk)} Kč"\n        calc_tax = f"{_number(tax_czk)} Kč"\n        net_amount = f"{_number(net_czk)} Kč" if net_czk not in (None, "") else "—"\n        fx = calculation.get("exchange_rate") or {}\n        if fx:\n            fx_url = escape(str(fx.get("source_url") or ""), quote=True)\n            fx_link = f'<a href="{fx_url}">Kurzovní lístek ČNB ↗</a>' if fx_url else ""\n            fx_line = (\n                f"1 {escape(str(fx.get('currency') or currency))} = {_number(fx.get('czk_per_unit'), 6)} Kč"\n                f" · {_date(fx.get('effective_date'))} · {fx_link}"\n            )\n'''

_NEW = '''    calc_base = calc_tax = net_amount = "—"\n    fx_line = ""\n    if calculation.get("status") == "CALCULATED":\n        source_country = str(scope.get("source_country") or "CZ").upper()\n        if source_country == "SK":\n            gross_value = calculation.get("gross_amount_eur")\n            tax_value = calculation.get("withholding_tax_eur")\n            net_value = calculation.get("net_amount_eur")\n            calc_unit = "EUR"\n        else:\n            gross_value = calculation.get("gross_amount_czk")\n            tax_value = calculation.get("withholding_tax_czk")\n            net_value = calculation.get("net_amount_czk")\n            calc_unit = "Kč"\n        if net_value in (None, "") and gross_value not in (None, "") and tax_value not in (None, ""):\n            try:\n                net_value = float(gross_value) - float(tax_value)\n            except (TypeError, ValueError):\n                net_value = None\n        calc_base = f"{_number(gross_value)} {calc_unit}"\n        calc_tax = f"{_number(tax_value)} {calc_unit}"\n        net_amount = f"{_number(net_value)} {calc_unit}" if net_value not in (None, "") else "—"\n        fx = calculation.get("exchange_rate") or {}\n        if fx:\n            fx_url = escape(str(fx.get("source_url") or ""), quote=True)\n            if source_country == "SK":\n                fx_source = escape(str(fx.get("source") or "ECB/NBS"))\n                fx_link = f'<a href="{fx_url}">Kurz {fx_source} ↗</a>' if fx_url else ""\n                fx_line = (\n                    f"1 {escape(str(fx.get('currency') or currency))} = {_number(fx.get('eur_per_unit'), 6)} EUR"\n                    f" · {_date(fx.get('effective_date'))} · {fx_link}"\n                )\n            else:\n                fx_link = f'<a href="{fx_url}">Kurzovní lístek ČNB ↗</a>' if fx_url else ""\n                fx_line = (\n                    f"1 {escape(str(fx.get('currency') or currency))} = {_number(fx.get('czk_per_unit'), 6)} Kč"\n                    f" · {_date(fx.get('effective_date'))} · {fx_link}"\n                )\n'''


def build_report(text: str) -> str:
    if "gross_amount_eur" in text and "calc_unit = \"EUR\"" in text:
        return text
    count = text.count(_OLD)
    if count != 1:
        raise RuntimeError(f"Expected one report calculation anchor, found {count}; refusing to patch.")
    return text.replace(_OLD, _NEW, 1)


def main() -> None:
    original = REPORT_PATH.read_text(encoding="utf-8")
    updated = build_report(original)
    if updated == original:
        print("SK report calculation rendering already applied; no changes.")
        return
    REPORT_PATH.write_text(updated, encoding="utf-8")
    print("Applied SK report calculation rendering to client_report.py")


if __name__ == "__main__":
    main()
