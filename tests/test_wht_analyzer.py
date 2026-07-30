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


class FakeRuleBuilder:
    def __init__(self, rules):
        self.rules = rules
        self.requested_treaty_ids = []

    def build_rules(self, treaty_id):
        self.requested_treaty_ids.append(treaty_id)
        return self.rules


def test_wht_analyzer_returns_error_when_no_rules_are_built():
    builder = FakeRuleBuilder([])
    analyzer = WHTAnalyzer(
        repository=object(),
        rule_builder=builder,
    )

    request = AnalysisRequest(
        treaty_id=999,
        transaction_type="dividend",
    )

    report = analyzer.analyze(request)

    assert builder.requested_treaty_ids == [999]
    assert report.treaty_id == 999
    assert report.transaction_type == "dividend"
    assert report.rule is None
    assert report.validation_result is None
    assert report.decision_result is None
    assert report.errors == [
        "No rules could be built for the requested treaty"
    ]


def test_wht_analyzer_returns_error_when_transaction_rule_is_missing():
    from taxtreat.engine.models import Rule

    builder = FakeRuleBuilder(
        [
            Rule(
                article=10,
                transaction_type="dividend",
                rate=5.0,
            )
        ]
    )
    analyzer = WHTAnalyzer(
        repository=object(),
        rule_builder=builder,
    )

    request = AnalysisRequest(
        treaty_id=1,
        transaction_type="interest",
    )

    report = analyzer.analyze(request)

    assert report.rule is None
    assert report.validation_result is None
    assert report.decision_result is None
    assert report.errors == [
        "No rule found for transaction type interest"
    ]


def test_select_rule_skips_objects_without_transaction_type():
    from taxtreat.engine.models import Rule

    analyzer = WHTAnalyzer(
        repository=object(),
        rule_builder=FakeRuleBuilder([]),
    )

    selected = analyzer._select_rule(
        [
            object(),
            Rule(
                article=11,
                transaction_type="interest",
                rate=10.0,
            ),
        ],
        "interest",
    )

    assert selected is not None
    assert selected.article == 11
    assert selected.transaction_type == "interest"


def test_select_rule_returns_none_when_no_rule_matches():
    from taxtreat.engine.models import Rule

    analyzer = WHTAnalyzer(
        repository=object(),
        rule_builder=FakeRuleBuilder([]),
    )

    selected = analyzer._select_rule(
        [
            Rule(
                article=10,
                transaction_type="dividend",
            )
        ],
        "royalty",
    )

    assert selected is None


class FakeRuleBuilder:
    def __init__(self, rules):
        self.rules = rules
        self.requested_treaty_ids = []

    def build_rules(self, treaty_id):
        self.requested_treaty_ids.append(treaty_id)
        return self.rules


def test_wht_analyzer_returns_error_when_no_rules_are_built():
    builder = FakeRuleBuilder([])
    analyzer = WHTAnalyzer(
        repository=object(),
        rule_builder=builder,
    )

    request = AnalysisRequest(
        treaty_id=999,
        transaction_type="dividend",
    )

    report = analyzer.analyze(request)

    assert builder.requested_treaty_ids == [999]
    assert report.treaty_id == 999
    assert report.transaction_type == "dividend"
    assert report.rule is None
    assert report.validation_result is None
    assert report.decision_result is None
    assert report.errors == [
        "No rules could be built for the requested treaty"
    ]


def test_wht_analyzer_returns_error_when_transaction_rule_is_missing():
    from taxtreat.engine.models import Rule

    builder = FakeRuleBuilder(
        [
            Rule(
                article=10,
                transaction_type="dividend",
                rate=5.0,
            )
        ]
    )
    analyzer = WHTAnalyzer(
        repository=object(),
        rule_builder=builder,
    )

    request = AnalysisRequest(
        treaty_id=1,
        transaction_type="interest",
    )

    report = analyzer.analyze(request)

    assert report.rule is None
    assert report.validation_result is None
    assert report.decision_result is None
    assert report.errors == [
        "No rule found for transaction type interest"
    ]


def test_select_rule_skips_objects_without_transaction_type():
    from taxtreat.engine.models import Rule

    analyzer = WHTAnalyzer(
        repository=object(),
        rule_builder=FakeRuleBuilder([]),
    )

    selected = analyzer._select_rule(
        [
            object(),
            Rule(
                article=11,
                transaction_type="interest",
                rate=10.0,
            ),
        ],
        "interest",
    )

    assert selected is not None
    assert selected.article == 11
    assert selected.transaction_type == "interest"


def test_select_rule_returns_none_when_no_rule_matches():
    from taxtreat.engine.models import Rule

    analyzer = WHTAnalyzer(
        repository=object(),
        rule_builder=FakeRuleBuilder([]),
    )

    selected = analyzer._select_rule(
        [
            Rule(
                article=10,
                transaction_type="dividend",
            )
        ],
        "royalty",
    )

    assert selected is None
