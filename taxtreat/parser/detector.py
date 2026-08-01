import re

ARTICLE1 = re.compile(r"^Článek\s+0*1\s*$", re.IGNORECASE | re.MULTILINE)
ARTICLE2 = re.compile(r"^Článek\s+0*2\s*$", re.IGNORECASE | re.MULTILINE)
_CONFIRMATION_WINDOW_PAGES = 6


def find_start(pages):
    """Find Article 1 after page-level normalization.

    The treaty title and Article 1 frequently occur on different pages.  A
    nearby Article 2 confirms the preferred candidate and avoids choosing an
    isolated Article 1 mention on a contents page.  If Article 2 is not visible
    in the window, the first genuine Article 1 heading remains a safe fallback;
    the article parser will still reject unusable text later.
    """

    candidates = [index for index, page in enumerate(pages) if ARTICLE1.search(page)]

    for position, index in enumerate(candidates):
        next_candidate = (
            candidates[position + 1]
            if position + 1 < len(candidates)
            else len(pages)
        )
        window_end = min(
            index + _CONFIRMATION_WINDOW_PAGES,
            next_candidate,
        )
        window = "\n".join(pages[index:window_end])
        if ARTICLE2.search(window):
            return index

    if candidates:
        return candidates[0]

    raise RuntimeError("Treaty start not found.")


def extract_treaty(pages):
    start = find_start(pages)
    return "\n".join(pages[start:]), start + 1
