import pytest

from taxtreat.tools.apply_sk_api_integration import build_integrated_main


BASE = '''from taxtreat.services.reporting import (\n    build_professional_report,\n    render_report_html,\n)\n\napp.mount(\n    "/ui-assets",\n    StaticFiles(directory=WEB_ROOT),\n    name="ui-assets",\n)\n\ndef require_analysis_source_release(\n    source_country: str,\n    recipient_country: str,\n):\n    source = source_country.upper()\n    recipient = recipient_country.upper()\n\n    if source != "CZ":\n        return None\n\n    treaty_pair_id = f"{source}-{recipient}"\n'''


def test_patcher_wires_router_and_explicit_non_cz_release_gate():
    integrated = build_integrated_main(BASE)

    assert "from app.sk_prerelease import router as sk_prerelease_router" in integrated
    assert "app.include_router(sk_prerelease_router)" in integrated
    assert "require_source_country_analysis_release(source)" in integrated
    assert '"code": decision.code' in integrated
    assert '"UNSUPPORTED_SOURCE_COUNTRY"' in integrated
    assert 'if source != "CZ":\n        return None' not in integrated


def test_patcher_is_idempotent():
    once = build_integrated_main(BASE)
    twice = build_integrated_main(once)
    assert twice == once


def test_patcher_refuses_to_guess_if_expected_gate_changed():
    changed = BASE.replace('if source != "CZ":\n        return None', 'if source != "CZ":\n        raise RuntimeError("changed")')
    with pytest.raises(RuntimeError, match="release gate"):
        build_integrated_main(changed)
