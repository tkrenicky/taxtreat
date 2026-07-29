import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from taxtreat.db.repository import TreatyRepository
from taxtreat.engine.article_classifier import classify_article
from taxtreat.engine.decision_engine import evaluate
from taxtreat.engine.extractors import dividend_rule
from taxtreat.engine.validation import RuleValidator


def test_switzerland_dividends_integration():
    repo = TreatyRepository("taxtreat.db")

    article = repo.get_article(10)
    assert article is not None, "Expected the Switzerland dividend article to be present in the database"

    title = article.get("title", "")
    classification = classify_article(title)
    assert classification == "dividend", f"Expected dividend classification for article title {title!r}"

    paragraphs = repo.get_article_paragraphs(10)
    assert paragraphs, "Expected the dividend article to have stored paragraphs"

    article_text = repo.get_full_article_text(10)
    rule = dividend_rule(article_text)

    assert rule is not None
    assert rule.extraction_status in {"confirmed", "needs_review", "incomplete"}
    assert len(rule.rates) > 0, "Expected at least one extracted dividend rate"

    validator = RuleValidator()
    validation_result = validator.validate([rule])

    print("Article:", article)
    print("Classification:", classification)
    print("Extracted rates:")
    for index, rate in enumerate(rule.rates):
        print(
            f"  [{index}] rate={rate.rate}, legal_basis={rate.legal_basis}, "
            f"conditions={[condition.condition_type.value for condition in rate.conditions]}"
        )

    print("Conditions linked to each rate:")
    for index, rate in enumerate(rule.rates):
        print(f"  [{index}] {[(condition.condition_type.value, condition.value, condition.unit) for condition in rate.conditions]}")

    print("Source paragraph:", rule.paragraph)
    print("Extraction status:", rule.extraction_status)
    print("Validation score:", validation_result.score)
    print("Validation warnings:", validation_result.warnings)
    print("Validation errors:", validation_result.errors)

    scenarios = [
        ("A. ownership = 25, beneficial_owner = True", {"ownership": 25, "beneficial_owner": True}),
        ("B. ownership = 5, beneficial_owner = True", {"ownership": 5, "beneficial_owner": True}),
        ("C. ownership missing, beneficial_owner = True", {"beneficial_owner": True}),
        ("D. ownership = 25, beneficial_owner = False", {"ownership": 25, "beneficial_owner": False}),
    ]

    for label, facts in scenarios:
        result = evaluate(rule, facts)
        assert result.withholding_rate is not None, f"Expected a withholding rate for {label}"
        print(f"Scenario {label}")
        print(f"  selected withholding rate: {result.withholding_rate}")
        print(f"  legal basis: {getattr(result, 'selected_legal_basis', None)}")
        print(f"  eligible: {result.eligible}")
        print(f"  requires_review: {result.requires_review}")
        print(f"  satisfied conditions: {result.satisfied_conditions}")
        print(f"  failed conditions: {result.failed_conditions}")
        print(f"  missing facts: {result.missing_facts}")
        print(f"  explanation: {result.explanation}")
