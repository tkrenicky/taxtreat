from taxtreat.db.repository import TreatyRepository
from taxtreat.engine.extractors import dividend_rule
from taxtreat.engine.models import Rule


def interest_rule(article_text: str) -> Rule:
    return Rule(article=11, transaction_type="interest")


def royalties_rule(article_text: str) -> Rule:
    return Rule(article=12, transaction_type="royalties")


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
        return royalties_rule(article_text)
