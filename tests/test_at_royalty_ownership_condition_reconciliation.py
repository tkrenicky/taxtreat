import json
from pathlib import Path


DATA_PATH = Path("data/legal_reviews/at_outbound/royalty_ownership_condition_reconciliation_2026.json")


def test_at_royalty_ownership_conditions_remain_separate_from_rate_taxonomy():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    rows = {row["partner_label"]: row for row in data["rows"]}

    assert data["schema_version"] == 2
    assert data["source_country"] == "AT"
    assert data["status"] == "targeted_ownership_condition_review_seed_not_released"
    assert data["partner_count"] == 9
    assert set(rows) == {
        "Belgien / Belgium",
        "Großbritannien / United Kingdom",
        "Irland / Ireland",
        "Italien / Italy",
        "Luxemburg / Luxembourg",
        "Niederlande / Netherlands",
        "Portugal / Portugal",
        "Schweden / Sweden",
        "Slowenien / Slovenia",
    }
    assert rows["Belgien / Belgium"]["classification"] == "ownership_condition_controls_source_taxing_right"
    assert rows["Großbritannien / United Kingdom"]["classification"] == "ownership_condition_controls_source_taxing_right"
    assert rows["Irland / Ireland"]["classification"] == "ownership_condition_controls_source_taxing_right_nonstandard_article_numbering"
    assert rows["Italien / Italy"]["classification"] == "ownership_condition_controls_source_taxing_right"
    assert rows["Luxemburg / Luxembourg"]["classification"] == "ownership_condition_with_nonstandard_numbering_requires_instrument_chronology"
    assert rows["Niederlande / Netherlands"]["classification"] == "ownership_condition_controls_source_taxing_right_nonstandard_article_numbering"
    assert rows["Portugal / Portugal"]["classification"] == "ownership_condition_selects_rate_branch"
    assert rows["Schweden / Sweden"]["classification"] == "ownership_condition_controls_source_taxing_right_nonstandard_article_numbering"
    assert rows["Slowenien / Slovenia"]["classification"] == "ownership_condition_in_older_candidate_requires_instrument_chronology"
    assert {row["threshold_percent"] for row in rows.values()} == {25, 50}
    assert all(row["controlling_text_selected"] is False for row in rows.values())
    assert all(row["legal_review_completed"] is False for row in rows.values())
    assert all(row["projection_released"] is False for row in rows.values())
    assert data["policy"]["ownership_threshold_is_not_a_royalty_rate"] is True
    assert data["policy"]["single_rate_candidate_does_not_make_ownership_condition_irrelevant"] is True
    assert data["policy"]["nonstandard_article_numbering_does_not_establish_controlling_text"] is True
    assert data["policy"]["no_treaty_result_is_released_by_this_seed"] is True
