from __future__ import annotations

from typing import Callable, Dict, Optional

from taxtreat.engine.extractors import dividend_rule, interest_rule, royalty_rule

Extractor = Callable[[str], object]


class ExtractorRegistry:
    def __init__(self) -> None:
        self._extractors: Dict[str, Extractor] = {}

    def register(self, article_type: str, extractor: Extractor) -> None:
        self._extractors[article_type] = extractor

    def get(self, article_type: str) -> Optional[Extractor]:
        return self._extractors.get(article_type)

    def has(self, article_type: str) -> bool:
        return article_type in self._extractors


DEFAULT_EXTRACTORS = {
    "dividend": dividend_rule,
    "interest": interest_rule,
    "royalty": royalty_rule,
}


def build_default_registry() -> ExtractorRegistry:
    registry = ExtractorRegistry()
    for article_type, extractor in DEFAULT_EXTRACTORS.items():
        registry.register(article_type, extractor)
    return registry


default_registry = build_default_registry()
