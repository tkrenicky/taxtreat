from typing import List

from taxtreat.db.repository import TreatyRepository
from taxtreat.engine.article_classifier import classify_article
from taxtreat.engine.models import Rule
from taxtreat.engine.registry import default_registry


class RuleBuilder:
    def __init__(self, repository: TreatyRepository, registry=None):
        self.repository = repository
        self.registry = registry or default_registry

    def build_rules(self, treaty_id: int) -> list[Rule]:
        rules: List[Rule] = []

        articles = self.repository.conn.execute(
            """
            SELECT a.id, a.article_number, a.title
            FROM articles a
            JOIN treaty_versions tv ON tv.id = a.treaty_version_id
            JOIN treaties t ON t.id = tv.treaty_id
            WHERE t.id = ?
            ORDER BY a.article_number
            """,
            (treaty_id,),
        ).fetchall()

        for article in articles:
            article_type = classify_article(article["title"] or "")
            if article_type == "other":
                continue

            extractor = self.registry.get(article_type)
            if extractor is None:
                continue

            article_text = self.repository.get_full_article_text(article["article_number"])
            rule = extractor(article_text)
            if isinstance(rule, Rule):
                rules.append(rule)

        return rules
