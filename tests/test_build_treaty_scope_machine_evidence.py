from pathlib import Path

from taxtreat.tools.build_treaty_scope_machine_evidence import build_scope_machine_evidence


def _candidate(path: Path, number: int, income: str):
    return {
        "article_number": number,
        "text_sha256": str(number) * 64,
        "artifact_path": str(path),
        "substantive_article_candidate": True,
        "semantic_income_detected": income,
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
    inventory = {
        "source_country": "AT",
        "status": "article_text_candidates_not_reviewed",
        "partners": [{
            "partner_label": "Legacy / Legacy",
            "sources": [{
                "final_url": "https://ris.bka.gv.at/legacy",
                "role_candidate": "current_consolidated_view",
                "article_candidates": [
                    _candidate(dividend, 8, "dividend"),
                    _candidate(interest, 9, "interest"),
                    _candidate(royalty, 10, "royalty"),
                ],
            }],
        }],
    }
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
    inventory = {
        "source_country": "AT",
        "status": "article_text_candidates_not_reviewed",
        "partners": [{
            "partner_label": "Blocked / Blocked",
            "sources": [{
                "final_url": "https://ris.bka.gv.at/blocked",
                "role_candidate": "published_instrument_or_protocol",
                "article_candidates": [_candidate(text, 10, "dividend")],
            }],
        }],
    }
    result = build_scope_machine_evidence(inventory, artifact_root=tmp_path)
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
    inventory = {
        "source_country": "XX",
        "status": "article_text_candidates_not_reviewed",
        "partners": [{
            "partner_label": "Partner",
            "sources": [{
                "final_url": "https://official.example/treaty",
                "role_candidate": "current_consolidated_view",
                "article_candidates": [_candidate(text, 10, "dividend")],
            }],
        }],
    }
    row = build_scope_machine_evidence(inventory, artifact_root=tmp_path)["scopes"][0]
    assert sorted(branch["rate_percent"] for branch in row["rate_branches_machine"]) == [5.0, 15.0]
    assert 25.0 not in [branch["rate_percent"] for branch in row["rate_branches_machine"]]


def test_scope_evidence_validates_input_and_missing_artifact(tmp_path: Path):
    bad = {"source_country": "AT", "status": "released", "partners": []}
    try:
        build_scope_machine_evidence(bad, artifact_root=tmp_path)
    except ValueError as exc:
        assert "not in machine-candidate state" in str(exc)
    else:
        raise AssertionError("released input must fail closed")

    inventory = {
        "source_country": "AT",
        "status": "article_text_candidates_not_reviewed",
        "partners": [{
            "partner_label": "Missing / Missing",
            "sources": [{
                "final_url": "https://ris.bka.gv.at/missing",
                "article_candidates": [_candidate(tmp_path / "missing.txt", 10, "dividend")],
            }],
        }],
    }
    try:
        build_scope_machine_evidence(inventory, artifact_root=tmp_path)
    except ValueError as exc:
        assert "Missing treaty article evidence" in str(exc)
    else:
        raise AssertionError("missing evidence file must fail closed")
