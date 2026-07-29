from taxtreat.db.repository import TreatyRepository
from taxtreat.engine.extractors import dividend_rule


class RuleEngine:
    def __init__(self, repository: TreatyRepository):
        self.repository = repository

    def extract_dividend_rule(self):
        article_text = self.repository.get_full_article_text(10)
        return dividend_rule(article_text)


def build_dividend_rule(article_number: int, db_path=None):
    repository = TreatyRepository(db_path or "taxtreat.db")
    engine = RuleEngine(repository)
    return engine.extract_dividend_rule()
