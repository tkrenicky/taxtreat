from dataclasses import dataclass, field, asdict

@dataclass
class TreatyArticle:
    number: int
    title: str
    text: str
    paragraphs: list[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

@dataclass
class ParsedTreaty:
    country: str
    source_title: str
    source_path: str
    start_page: int | None
    identity_validation: dict[str, object] | None = None
    source_resolution: dict[str, object] | None = None
    articles: list[TreatyArticle] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
