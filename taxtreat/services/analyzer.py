from taxtreat.db.repository import TreatyRepository
from taxtreat.engine.extractors import dividend_rule, interest_rule, royalty_rule
from taxtreat.engine.models import Rule


def royalties_rule(article_text: str) -> Rule:
    """Backward-compatible alias for the royalty extractor."""
    return royalty_rule(article_text)


class TreatyAnalyzer:
    def __init__(self, repository: TreatyRepository):
        self.repository = repository

    def analyze_dividends(self) -> Rule:
        article_text = self.repository.get_full_article_text(10)
        return dividend_rule(article_text)

    def analyze_interest(self) -> Rule:
        article_text = self.repository.get_full_article_text(11)
        return interest_rule(article_text)

    def analyze_royalties(self) -> Rule:
        article_text = self.repository.get_full_article_text(12)
        return royalty_rule(article_text)
