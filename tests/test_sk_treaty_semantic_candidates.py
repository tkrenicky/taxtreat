from __future__ import annotations

import json

import taxtreat.tools.build_sk_treaty_semantic_candidates as semantic_module
from taxtreat.tools.build_sk_treaty_semantic_candidates import (
    build_candidates,
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


def test_title_mismatch_never_enters_semantic_candidate_layer(tmp_path, monkeypatch):
    scopes = []
    for i in range(225):
        status = "article_extracted"
        title_status = "expected_income_title_matched"
        text = "Článok 10 Dividendy. Daň nepresiahne 10 %."
        if i == 0:
            status = "article_extracted_title_mismatch_requires_resolution"
            title_status = "expected_income_title_not_matched"
            text = "Článok 10 Prepojené podniky. 10 %."
        scopes.append({
            "packet_id": f"SK-X{i}-dividend-TREATY-SOURCE",
            "recipient_country": f"X{i}",
            "income_type": "dividend",
            "article_text": text,
            "machine_extraction_status": status,
            "title_validation_status": title_status,
            "source_url": "https://example.invalid",
            "source_sha256": "x",
            "approval_eligible": False,
            "runtime_status": "not_released",
        })

    path = tmp_path / "extraction.json"
    path.write_text(
        json.dumps({"scope_count": 225, "scopes": scopes}),
        encoding="utf-8",
    )
    monkeypatch.setattr(semantic_module, "EXTRACTION_PATH", path)

    payload = build_candidates()
    first = payload["scopes"][0]
    assert first["semantic_status"] == "blocked_missing_validated_article_text"
    assert first["source_extraction_status"] == (
        "article_extracted_title_mismatch_requires_resolution"
    )
    assert all(row["approval_eligible"] is False for row in payload["scopes"])
