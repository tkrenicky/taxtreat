from __future__ import annotations

from taxtreat.tools.build_sk_treaty_semantic_candidates import (
    build_semantic_candidate,
)


def test_extracts_rate_candidates_without_releasing_rate():
    article = (
        "Článok 10 Dividendy. Daň však nesmie presiahnuť 5 percent hrubej sumy "
        "dividend, ak skutočný vlastník je spoločnosť, ktorá vlastní najmenej "
        "10 percent hlasovacích práv. V ostatných prípadoch 15 percent."
    )
    result = build_semantic_candidate(article)

    rates = [row["rate_percent"] for row in result["rate_candidates"]]
    assert rates == [5.0, 10.0, 15.0]
    assert result["beneficial_owner_wording_present"] is True
    assert result["ownership_linked_rate_candidate_count"] >= 1
    assert result["semantic_status"] == "machine_candidate_not_legal_conclusion"
    assert result["approval_eligible"] is False
    assert result["runtime_status"] == "not_released"


def test_detects_exclusive_residence_taxation_as_candidate_only():
    article = (
        "Článok 11 Úroky. Úroky majúce zdroj v jednom zmluvnom štáte a "
        "vyplácané rezidentovi druhého zmluvného štátu sa môžu zdaniť iba "
        "v tomto druhom štáte."
    )
    result = build_semantic_candidate(article)

    assert result["exclusive_residence_taxation_candidate"] is True
    assert result["rate_candidates"] == []
    assert result["semantic_status"] == "machine_candidate_not_legal_conclusion"


def test_detects_pe_carveout_wording():
    article = (
        "Ustanovenia odsekov 1 a 2 sa nepoužijú, ak príjemca vykonáva činnosť "
        "prostredníctvom stálej prevádzkarne a pohľadávka patrí k tejto stálej "
        "prevádzkarni."
    )
    result = build_semantic_candidate(article)
    assert result["pe_or_fixed_base_carveout_wording_present"] is True


def test_detects_holding_period_candidates():
    article = (
        "Podmienka vlastníctva musí byť splnená počas obdobia 365 dní, "
        "ktoré zahŕňa deň výplaty dividend."
    )
    result = build_semantic_candidate(article)
    assert result["holding_period_candidates"] == [
        {
            "value": 365,
            "unit": "dní",
            "context": result["holding_period_candidates"][0]["context"],
            "context_sha256": result["holding_period_candidates"][0]["context_sha256"],
        }
    ]


def test_candidate_parser_does_not_turn_percentages_into_final_legal_conclusion():
    article = "Článok 12 Licenčné poplatky. Daň nepresiahne 10 % hrubej sumy."
    result = build_semantic_candidate(article)

    assert result["rate_candidates"][0]["rate_percent"] == 10.0
    assert "final_rate" not in result
    assert "treaty_rate" not in result
    assert result["human_review_status"] == "not_started"
