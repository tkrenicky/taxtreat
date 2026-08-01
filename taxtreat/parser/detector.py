import re

ARTICLE1 = re.compile(
    r"(?:Článek|CÏ\s*laÂ?\s*nek|Article)\s*0*1\b",
    re.IGNORECASE,
)


def find_start(pages):
    # Parsing starts at Article 1. Requiring the word SMLOUVA on the same page
    # incorrectly rejects publications where the title and Article 1 are split
    # across pages.
    for i, page in enumerate(pages):
        if ARTICLE1.search(page):
            return i

    raise RuntimeError("Treaty start not found.")


def extract_treaty(pages):
    start = find_start(pages)
    return "\n".join(pages[start:]), start + 1
