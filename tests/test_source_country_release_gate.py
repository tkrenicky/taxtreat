import pytest

from taxtreat.services.source_country_release_gate import (
    SourceCountryNotReleasedError,
    UnsupportedSourceCountryError,
    require_source_country_analysis_release,
)


def test_sk_is_rejected_at_source_country_release_layer_before_analysis():
    with pytest.raises(SourceCountryNotReleasedError) as exc_info:
        require_source_country_analysis_release("sk")

    decision = exc_info.value.decision
    assert decision.source_country == "SK"
    assert decision.allowed is False
    assert decision.code == "SOURCE_COUNTRY_NOT_RELEASED"
    assert decision.release_status == "pre_release"
    assert "source_country_runtime_release_false" in decision.blockers
    assert "full_human_legal_review_not_completed" in decision.blockers


def test_cz_remains_released_and_can_delegate_to_existing_pair_gate():
    calls = []

    decision = require_source_country_analysis_release(
        "CZ",
        released_country_gate=lambda code: calls.append(code),
    )

    assert calls == ["CZ"]
    assert decision.allowed is True
    assert decision.code == "SOURCE_COUNTRY_RELEASED"
    assert decision.release_status == "released"
    assert decision.blockers == ()


def test_unknown_source_country_fails_closed():
    with pytest.raises(UnsupportedSourceCountryError):
        require_source_country_analysis_release("XX")
