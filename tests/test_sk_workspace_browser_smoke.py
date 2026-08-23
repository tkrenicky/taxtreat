from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "scripts" / "verify_sk_workspace_browser.sh"


def test_browser_smoke_covers_cz_sk_cz_round_trip_and_release_gate():
    text = SMOKE.read_text(encoding="utf-8")

    assert 'document.body.dataset.sourceCountry === "CZ"' in text
    assert 's.value="SK"' in text
    assert 'document.body.dataset.sourceCountry === "SK"' in text
    assert 'runtimeReleased === false' in text
    assert 'aria-disabled' in text
    assert 's.value="CZ"' in text
    assert 'return to CZ source country' in text


def test_browser_smoke_checks_slovak_fx_compliance_and_copy_isolation():
    text = SMOKE.read_text(encoding="utf-8")

    assert 'value === "EUR"' in text
    assert '/exchange-rates/cnb' in text
    assert 'prohibited for Slovak' in text
    assert 'OZN4311v26' in text
    assert '15th_day_of_following_calendar_month' in text
    assert 'ordinaryAnnualWhtReturnConfigured === false' in text
    assert 'Väzba príjmu na stálu prevádzkareň v SR' in text
    assert 'a[0] === "75" && a[1] === "225"' in text
    assert 'a[0] === "101" && a[1] === "303"' in text
