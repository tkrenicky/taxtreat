from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import pytest

from taxtreat.tools import run_country_review_preparation as runner


def _fixture(tmp_path: Path) -> tuple[dict, dict]:
    partners = []
    scopes = []
    for index in range(2):
        article_paths = {}
        for income, article in (("dividend", 10), ("interest", 11), ("royalty", 12)):
            path = tmp_path / f"{index}-{income}.txt"
            text = (
                f"Article {article} {income.title()}\n"
                "(1) If the beneficial owner is resident in the other State, "
                "the tax shall not exceed 10 percent of the gross amount."
            )
            path.write_text(text, encoding="utf-8")
            article_paths[income] = path
            scopes.append({
                "source_country": "XX",
                "partner_label": f"Partner {index}",
                "income_type": income,
                "machine_mli_flag": False,
                "machine_status_instrument_flag": False,
                "instrument_chain": {"official_links": [f"https://official.example/{index}/{income}"]},
            })
        partners.append({
            "partner_label": f"Partner {index}",
            "sources": [{
                "final_url": f"https://official.example/{index}",
                "role_candidate": "current_consolidated_view",
                "article_candidates": [
                    {
                        "article_number": article,
                        "text_sha256": hashlib.sha256(article_paths[income].read_bytes()).hexdigest(),
                        "artifact_path": str(article_paths[income]),
                        "substantive_article_candidate": True,
                        "semantic_income_detected": income,
                    }
                    for income, article in (("dividend", 10), ("interest", 11), ("royalty", 12))
                ],
            }],
        })
    return (
        {"source_country": "XX", "status": "review_queue_not_released", "scopes": scopes},
        {"source_country": "XX", "status": "article_text_candidates_not_reviewed", "partners": partners},
    )


def test_prepare_country_review_runs_scope_evidence_and_review_gate(tmp_path: Path):
    queue, articles = _fixture(tmp_path)
    scope_evidence, review_pack = runner.prepare_country_review(
        review_queue=queue,
        article_inventory=articles,
        artifact_root=tmp_path,
    )
    assert scope_evidence["scope_count"] == 6
    assert scope_evidence["complete_scope_count"] == 6
    assert review_pack["scope_count"] == 6
    assert review_pack["review_ready_scope_count"] == 6
    assert review_pack["blocked_scope_count"] == 0
    assert all(row["review_ready"] is True for row in review_pack["rows"])


def test_prepare_country_review_fails_closed_on_country_or_scope_mismatch(tmp_path: Path):
    queue, articles = _fixture(tmp_path)
    bad_articles = dict(articles)
    bad_articles["source_country"] = "YY"
    with pytest.raises(ValueError, match="source-country mismatch"):
        runner.prepare_country_review(review_queue=queue, article_inventory=bad_articles, artifact_root=tmp_path)

    queue, articles = _fixture(tmp_path)
    queue["scopes"] = queue["scopes"][:-1]
    with pytest.raises(ValueError, match="Scope-count mismatch"):
        runner.prepare_country_review(review_queue=queue, article_inventory=articles, artifact_root=tmp_path)

    queue, articles = _fixture(tmp_path)
    queue["scopes"] = []
    with pytest.raises(ValueError, match="no scopes"):
        runner.prepare_country_review(review_queue=queue, article_inventory=articles, artifact_root=tmp_path)


def test_write_review_outputs_persists_json_and_excel_compatible_csv(tmp_path: Path):
    queue, articles = _fixture(tmp_path)
    scope_evidence, review_pack = runner.prepare_country_review(
        review_queue=queue,
        article_inventory=articles,
        artifact_root=tmp_path,
    )
    scope_path = tmp_path / "nested" / "scope.json"
    review_path = tmp_path / "nested" / "review.json"
    csv_path = tmp_path / "nested" / "review.csv"
    runner.write_review_outputs(
        scope_evidence=scope_evidence,
        review_pack=review_pack,
        scope_output=scope_path,
        review_json_output=review_path,
        review_csv_output=csv_path,
    )
    assert json.loads(scope_path.read_text(encoding="utf-8"))["scope_count"] == 6
    assert json.loads(review_path.read_text(encoding="utf-8"))["review_ready_scope_count"] == 6
    assert csv_path.read_bytes().startswith(b"\xef\xbb\xbf")
    assert len(list(csv.DictReader(csv_path.open(encoding="utf-8-sig", newline="")))) == 6


def test_review_preparation_cli_runs_without_country_specific_code(tmp_path: Path, monkeypatch):
    queue, articles = _fixture(tmp_path)
    queue_path = tmp_path / "queue.json"
    articles_path = tmp_path / "articles.json"
    scope_path = tmp_path / "scope.json"
    review_path = tmp_path / "review.json"
    csv_path = tmp_path / "review.csv"
    queue_path.write_text(json.dumps(queue), encoding="utf-8")
    articles_path.write_text(json.dumps(articles), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", [
        "run_country_review_preparation",
        "--queue", str(queue_path),
        "--articles", str(articles_path),
        "--artifact-root", str(tmp_path),
        "--scope-output", str(scope_path),
        "--review-json-output", str(review_path),
        "--review-csv-output", str(csv_path),
    ])
    runner.main()
    assert json.loads(review_path.read_text(encoding="utf-8"))["source_country"] == "XX"
    assert csv_path.is_file()


def test_load_optional_none_and_json(tmp_path: Path):
    assert runner._load(None) is None
    path = tmp_path / "x.json"
    path.write_text('{"x": 1}', encoding="utf-8")
    assert runner._load(path) == {"x": 1}
