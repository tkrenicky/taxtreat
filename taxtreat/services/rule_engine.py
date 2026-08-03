from collections.abc import Callable

from taxtreat.db.repository import TreatyRepository
from taxtreat.engine.extractors import dividend_rule, interest_rule, royalty_rule


class RuleEngine:
    def __init__(self, repository: TreatyRepository):
        self.repository = repository

    def extract_dividend_rule(self):
        return dividend_rule(self.repository.get_full_article_text(10))

    def extract_interest_rule(self):
        return interest_rule(self.repository.get_full_article_text(11))

    def extract_royalty_rule(self):
        return royalty_rule(self.repository.get_full_article_text(12))


def _build_rule(
    article_number: int,
    extractor: Callable,
    db_path=None,
):
    repository = TreatyRepository(db_path or "taxtreat.db")
    return extractor(repository.get_full_article_text(article_number))


def build_dividend_rule(article_number: int = 10, db_path=None):
    return _build_rule(article_number, dividend_rule, db_path)


def build_interest_rule(article_number: int = 11, db_path=None):
    return _build_rule(article_number, interest_rule, db_path)


def build_royalty_rule(article_number: int = 12, db_path=None):
    return _build_rule(article_number, royalty_rule, db_path)
