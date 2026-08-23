from taxtreat.tools.apply_sk_report_calculation_rendering import build_report


BASE = '''    calc_base = calc_tax = net_amount = "—"
    fx_line = ""
    if calculation.get("status") == "CALCULATED":
        gross_czk = calculation.get("gross_amount_czk")
        tax_czk = calculation.get("withholding_tax_czk")
        net_czk = calculation.get("net_amount_czk")
        if net_czk in (None, "") and gross_czk not in (None, "") and tax_czk not in (None, ""):
            try:
                net_czk = float(gross_czk) - float(tax_czk)
            except (TypeError, ValueError):
                net_czk = None
        calc_base = f"{_number(gross_czk)} Kč"
        calc_tax = f"{_number(tax_czk)} Kč"
        net_amount = f"{_number(net_czk)} Kč" if net_czk not in (None, "") else "—"
        fx = calculation.get("exchange_rate") or {}
        if fx:
            fx_url = escape(str(fx.get("source_url") or ""), quote=True)
            fx_link = f'<a href="{fx_url}">Kurzovní lístek ČNB ↗</a>' if fx_url else ""
            fx_line = (
                f"1 {escape(str(fx.get('currency') or currency))} = {_number(fx.get('czk_per_unit'), 6)} Kč"
                f" · {_date(fx.get('effective_date'))} · {fx_link}"
            )
'''


def test_patcher_adds_source_country_specific_calculation_rendering():
    patched = build_report(BASE)
    assert 'source_country == "SK"' in patched
    assert "withholding_tax_eur" in patched
    assert "net_amount_transaction_currency" in patched
    assert "foreign_units_per_eur" in patched
    assert "1 EUR =" in patched
    assert "gross_amount_czk" in patched  # CZ path remains present.


def test_patcher_is_idempotent():
    once = build_report(BASE)
    assert build_report(once) == once
