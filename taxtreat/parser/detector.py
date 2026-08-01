import re

ARTICLE1 = re.compile(
    r"(Článek|CÏ\s*laÂ?\s*nek|Article)\s*1",
    re.IGNORECASE,
)


def find_start(pages):

    for i, page in enumerate(pages):

        if "SMLOUVA" in page.upper() and ARTICLE1.search(page):
            return i

    raise RuntimeError("Treaty start not found.")


def extract_treaty(pages):

    start = find_start(pages)

    return "\n".join(pages[start:]), start + 1
