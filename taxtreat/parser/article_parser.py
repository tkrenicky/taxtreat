import re
from .models import TreatyArticle

ARTICLE_RE = re.compile(
    r'^(?:Článek|CÏ\s*laÂ?\s*nek|Article)\s+(\d+)\s*$',
    re.MULTILINE | re.IGNORECASE,
)

def split_paragraphs(text: str) -> list[str]:
    text = text.strip()

    if not text:
        return []

    parts = re.split(r'(?=^\d+\.\s)', text, flags=re.MULTILINE)
    return [p.strip() for p in parts if p.strip()]


def parse_articles(text: str) -> list[TreatyArticle]:
    matches = list(ARTICLE_RE.finditer(text))

    if not matches:
        raise RuntimeError("No articles detected.")

    articles = []

    for i, match in enumerate(matches):

        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        block = text[start:end].strip()

        lines = [l.strip() for l in block.splitlines() if l.strip()]

        title = lines[0] if lines else ""
        body = "\n".join(lines[1:]) if len(lines) > 1 else ""

        articles.append(
            TreatyArticle(
                number=int(match.group(1)),
                title=title,
                text=body,
                paragraphs=split_paragraphs(body),
            )
        )

    return articles
