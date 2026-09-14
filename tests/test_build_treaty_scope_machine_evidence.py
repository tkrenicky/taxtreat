from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from taxtreat.tools import build_treaty_scope_machine_evidence as scope_module
from taxtreat.tools.build_treaty_scope_machine_evidence import build_scope_machine_evidence


def _candidate(path: Path, number: int, income: str | None, *, substantive: bool = True):
    return {
        "article_number": number,
        "text_sha256": str(number) * 64,
        "artifact_path": str(path),
        "substantive_article_candidate": substantive,
        "semantic_income_detected": income,
    }


def _inventory(partner: str, candidates: list[dict], *, source_url: str = "https://ris.bka.gv.at/treaty") -> dict:
    return {
        "source_country": "AT",
        "status": "article_text_candidates_not_reviewed",
        "partners": [{
            "partner_label": partner,
            "sources": [{
                "final_url": source_url,
                "role_candidate": "current_consolidated_view",
                "article_candidates": candidates,
            }],
        }],
    }


def test_scope_evidence_preserves_rate_conditions_and_non_rate_treatments(tmp_path: Path):
    dividend = tmp_path / "dividend.txt"
    dividend.write_text(
        "Artikel 8 Dividenden\n"
        "(1) Dividenden dürfen im Quellenstaat besteuert werden.\n"
        "(2) Ist der Nutzungsberechtigte eine Gesellschaft, die mindestens 10 Prozent des Kapitals hält, "
        "darf die Steuer 5 Prozent des Bruttobetrages der Dividenden nicht übersteigen.\n"
        "(3) In allen anderen Fällen darf die Steuer 15 Prozent des Bruttobetrages nicht übersteigen.\n"
        "(4) Die Absätze gelten nicht, wenn die Beteiligung einer Betriebsstätte zuzurechnen ist.",
        encoding="utf-8",
    )
    interest = tmp_path / "interest.txt"
    interest.write_text(
        "Artikel 9 Zinsen\n"
        "(1) Zinsen, deren Nutzungsberechtigter im anderen Staat ansässig ist, dürfen nur in diesem Staat besteuert werden.\n"
        "(2) Diese Regel gilt nicht bei Zurechnung zu einer Betriebsstätte.",
        encoding="utf-8",
    )
    royalty = tmp_path / "royalty.txt"
    royalty.write_text(
        "Artikel 10 Lizenzgebühren\n"
        "(1) Lizenzgebühren für Software dürfen mit höchstens 5 v. H. des Bruttobetrages besteuert werden.\n"
        "(2) Lizenzgebühren für Patente, Marken und Know-how dürfen mit höchstens 10 v. H. des Bruttobetrages besteuert werden.",
        encoding="utf-8",
    )
    inventory = _inventory(
        "Legacy / Legacy",
        [
            _candidate(dividend, 8, "dividend"),
            _candidate(interest, 9, "interest"),
            _candidate(royalty, 10, "royalty"),
        ],
        source_url="https://ris.bka.gv.at/legacy",
    )
    result = build_scope_machine_evidence(inventory, artifact_root=tmp_path)
    assert result["scope_count"] == 3
    assert result["complete_scope_count"] == 3
    assert result["blocked_scope_count"] == 0
    scopes = {row["income_type"]: row for row in result["scopes"]}

    div = scopes["dividend"]
    assert div["actual_article_numbers_machine"] == [8]
    assert sorted(branch["rate_percent"] for branch in div["rate_branches_machine"] if branch["rate_percent"] is not None) == [5.0, 15.0]
    five = next(branch for branch in div["rate_branches_machine"] if branch["rate_percent"] == 5.0)
    assert five["ownership_threshold_percent_machine"] == 10.0
    assert five["beneficial_owner_required_machine"] is True
    assert five["pe_carveout_machine"] is True
    assert "5 Prozent" in five["condition_evidence_text"]

    intr = scopes["interest"]
    assert intr["rate_branches_machine"][0]["rate_percent"] is None
    assert intr["rate_branches_machine"][0]["treatment_candidate"] == "residence_only"
    assert intr["rate_branches_machine"][0]["pe_carveout_machine"] is True

    roy = scopes["royalty"]
    assert sorted(branch["rate_percent"] for branch in roy["rate_branches_machine"]) == [5.0, 10.0]
    software = next(branch for branch in roy["rate_branches_machine"] if branch["rate_percent"] == 5.0)
    other = next(branch for branch in roy["rate_branches_machine"] if branch["rate_percent"] == 10.0)
    assert software["category_discriminator_machine"] == "software"
    assert "industrial_ip_knowhow" in other["category_discriminator_machine"]
    assert result["policy"]["residence_only_is_non_rate_treatment_not_synthetic_zero"] is True


def test_scope_evidence_fails_closed_when_semantic_article_or_branch_is_missing(tmp_path: Path):
    text = tmp_path / "article.txt"
    text.write_text("Article 10 Dividends without a machine-detectable rate branch.", encoding="utf-8")
    result = build_scope_machine_evidence(
        _inventory("Blocked / Blocked", [_candidate(text, 10, "dividend")], source_url="https://ris.bka.gv.at/blocked"),
        artifact_root=tmp_path,
    )
    scopes = {row["income_type"]: row for row in result["scopes"]}
    assert scopes["dividend"]["machine_evidence_complete"] is False
    assert "no_rate_or_residence_only_branch_detected" in scopes["dividend"]["machine_evidence_blockers"]
    assert "no_substantive_semantic_article_candidate" in scopes["interest"]["machine_evidence_blockers"]
    assert result["blocked_scope_count"] == 3


def test_scope_evidence_keeps_ownership_percent_out_of_rate_candidates(tmp_path: Path):
    text = tmp_path / "dividend.txt"
    text.write_text(
        "Article 10 Dividends\n"
        "(1) If the beneficial owner is a company which owns at least 25 percent of the capital, "
        "the tax shall not exceed 5 percent of the gross amount.\n"
        "(2) Otherwise the tax shall not exceed 15 percent of the gross amount.",
        encoding="utf-8",
    )
    inventory = _inventory("Partner", [_candidate(text, 10, "dividend")], source_url="https://official.example/treaty")
    inventory["source_country"] = "XX"
    row = build_scope_machine_evidence(inventory, artifact_root=tmp_path)["scopes"][0]
    assert sorted(branch["rate_percent"] for branch in row["rate_branches_machine"]) == [5.0, 15.0]
    assert 25.0 not in [branch["rate_percent"] for branch in row["rate_branches_machine"]]
    five = next(branch for branch in row["rate_branches_machine"] if branch["rate_percent"] == 5.0)
    assert five["ownership_threshold_percent_machine"] == 25.0


def test_holding_period_units_are_preserved_without_lossy_conversion(tmp_path: Path):
    text = tmp_path / "holding.txt"
    text.write_text(
        "Article 10 Dividends\n"
        "(1) If the beneficial owner has held the participation for an uninterrupted period of 365 days, "
        "the tax shall not exceed 5 percent of the gross amount.\n"
        "(2) Otherwise the tax shall not exceed 15 percent of the gross amount.",
        encoding="utf-8",
    )
    row = build_scope_machine_evidence(_inventory("Holding", [_candidate(text, 10, "dividend")]), artifact_root=tmp_path)["scopes"][0]
    branch = next(item for item in row["rate_branches_machine"] if item["rate_percent"] == 5.0)
    assert branch["holding_period_value_machine"] == 365
    assert branch["holding_period_unit_machine"] == "days"


@pytest.mark.parametrize(
    "text, expected",
    [
        ("uninterrupted period of 12 months", (12, "months")),
        ("holding period of 2 years", (2, "years")),
        ("period of 365 Tage", (365, "days")),
        ("12 months", (None, None)),
        ("holding period without number", (None, None)),
    ],
)
def test_holding_signal_variants(text, expected):
    assert scope_module._holding_signal(text) == expected


def test_percentage_and_category_helpers_cover_legacy_notation_and_no_match():
    mentions = scope_module._percentage_mentions("5 %, 10 vom Hundert and 15 v. H.")
    assert [row[0] for row in mentions] == [5.0, 10.0, 15.0]
    assert scope_module._royalty_category("ordinary payment") is None
    category = scope_module._royalty_category("software, film and patent royalties")
    assert set(category.split("|")) == {"software", "film_tv_radio", "industrial_ip_knowhow"}


def test_clause_fallback_and_rate_context_disambiguation():
    assert scope_module._clauses("plain unnumbered treaty text") == ["plain unnumbered treaty text"]
    text = "owns at least 25 percent of the capital, the tax shall not exceed 5 percent of the gross amount"
    mentions = scope_module._percentage_mentions(text)
    assert scope_module._is_ownership_percentage(text, mentions[0][1], mentions[0][2]) is True
    assert scope_module._is_ownership_percentage(text, mentions[1][1], mentions[1][2]) is False


def test_scope_evidence_uses_numeric_fallback_only_when_semantic_signal_absent(tmp_path: Path):
    text = tmp_path / "standard.txt"
    text.write_text("Article 10\n(1) The tax shall not exceed 15 percent of the gross amount.", encoding="utf-8")
    candidate = _candidate(text, 10, None)
    row = build_scope_machine_evidence(_inventory("Fallback", [candidate]), artifact_root=tmp_path)["scopes"][0]
    assert row["income_type"] == "dividend"
    assert row["actual_article_numbers_machine"] == [10]
    assert row["rate_branches_machine"][0]["rate_percent"] == 15.0


def test_scope_evidence_skips_rejected_candidate_and_rejects_bad_source_url(tmp_path: Path):
    text = tmp_path / "rate.txt"
    text.write_text("Article 10 Dividends\n(1) Tax shall not exceed 15 percent of gross amount.", encoding="utf-8")
    rejected = _candidate(text, 10, "dividend", substantive=False)
    result = build_scope_machine_evidence(_inventory("Rejected", [rejected]), artifact_root=tmp_path)
    assert result["complete_scope_count"] == 0

    accepted = _candidate(text, 10, "dividend")
    result = build_scope_machine_evidence(
        _inventory("Bad URL", [accepted], source_url="http://not-official.example/treaty"),
        artifact_root=tmp_path,
    )
    row = result["scopes"][0]
    assert "official_source_url_missing" in row["machine_evidence_blockers"]


def test_scope_evidence_rejects_missing_country_partner_and_bad_state(tmp_path: Path):
    with pytest.raises(ValueError, match="missing source_country"):
        build_scope_machine_evidence({"status": "article_text_candidates_not_reviewed", "partners": []}, artifact_root=tmp_path)
    with pytest.raises(ValueError, match="not in machine-candidate state"):
        build_scope_machine_evidence({"source_country": "AT", "status": "released", "partners": []}, artifact_root=tmp_path)
    with pytest.raises(ValueError, match="partner without label"):
        build_scope_machine_evidence(
            {"source_country": "AT", "status": "article_text_candidates_not_reviewed", "partners": [{"partner_label": "", "sources": []}]},
            artifact_root=tmp_path,
        )


def test_scope_evidence_validates_missing_artifact(tmp_path: Path):
    inventory = _inventory("Missing / Missing", [_candidate(tmp_path / "missing.txt", 10, "dividend")])
    with pytest.raises(ValueError, match="Missing treaty article evidence"):
        build_scope_machine_evidence(inventory, artifact_root=tmp_path)


def test_scope_evidence_cli_writes_machine_evidence(tmp_path: Path, monkeypatch):
    text = tmp_path / "article.txt"
    text.write_text("Article 10 Dividends\n(1) Tax shall not exceed 15 percent of the gross amount.", encoding="utf-8")
    inventory = _inventory("CLI / CLI", [_candidate(text, 10, "dividend")])
    input_path = tmp_path / "inventory.json"
    output_path = tmp_path / "scope.json"
    input_path.write_text(json.dumps(inventory), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", [
        "build_treaty_scope_machine_evidence",
        "--input", str(input_path),
        "--artifact-root", str(tmp_path),
        "--output", str(output_path),
    ])
    scope_module.main()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["scope_count"] == 3
    assert payload["status"] == "scope_machine_evidence_not_reviewed_not_released"
