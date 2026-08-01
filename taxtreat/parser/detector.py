import re

ARTICLE1 = re.compile(
    r"(Článek|CÏ\s*laÂ?\s*nek|Article)\s*1",
    re.IGNORECASE,
)


def find_starts(pages):
    """Return every treaty start found in a source publication."""

    return [
        i
        for i, page in enumerate(pages)
        if "SMLOUVA" in page.upper() and ARTICLE1.search(page)
    ]


def find_start(pages):
    starts = find_starts(pages)
    if starts:
        return starts[0]
    raise RuntimeError("Treaty start not found.")


def treaty_ranges(pages):
    """Return page ranges for each treaty embedded in a publication.

    A Czech collection PDF may contain several notices and treaties. Treating
    the first treaty as the requested one can silently associate legal rules
    with the wrong country, so every detected treaty is exposed as a separate
    candidate range.
    """

    starts = find_starts(pages)
    if not starts:
        raise RuntimeError("Treaty start not found.")

    return [
        (start, starts[index + 1] if index + 1 < len(starts) else len(pages))
        for index, start in enumerate(starts)
    ]


def extract_treaty_candidates(pages):
    return [
        ("\n".join(pages[start:end]), start + 1, start, end)
        for start, end in treaty_ranges(pages)
    ]


def extract_treaty(pages):
    treaty_text, start_page, _, _ = extract_treaty_candidates(pages)[0]
    return treaty_text, start_page
