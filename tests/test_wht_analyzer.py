import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from taxtreat.db.repository import TreatyRepository
from taxtreat.services.analyze import AnalysisRequest, WHTAnalyzer


def test_wht_analyzer_builds_report_for_dividend_request():
    repository = TreatyRepository("taxtreat.db")
    analyzer = WHTAnalyzer(repository=repository)

    request = AnalysisRequest(
        treaty_id=1,
        transaction_type="dividend",
        facts={"ownership": 25, "beneficial_owner": True},
    )

    report = analyzer.analyze(request)

    assert report.treaty_id == 1
    assert report.transaction_type == "dividend"
    assert report.rule is not None
    assert report.validation_result is not None
    assert report.decision_result is not None
    assert report.decision_result.withholding_rate is not None
    assert report.decision_result.eligible is True
    assert report.validation_result.score >= 0
