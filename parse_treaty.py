import json
import argparse

from taxtreat.parser.extractor import extract_pdf_pages
from taxtreat.parser.normalize import normalize_pages
from taxtreat.parser.detector import extract_treaty
from taxtreat.parser.article_parser import parse_articles
from taxtreat.parser.models import ParsedTreaty


parser = argparse.ArgumentParser()

parser.add_argument("pdf")
parser.add_argument("--country", required=True)
parser.add_argument("--title", required=True)
parser.add_argument("--output", required=True)

args = parser.parse_args()

pages = extract_pdf_pages(args.pdf)
pages = normalize_pages(pages)

treaty_text, start_page = extract_treaty(pages)

articles = parse_articles(treaty_text)

parsed = ParsedTreaty(
    country=args.country,
    source_title=args.title,
    source_path=args.pdf,
    start_page=start_page,
    articles=articles,
)

with open(args.output, "w", encoding="utf8") as f:
    json.dump(parsed.to_dict(), f, ensure_ascii=False, indent=2)

print()
print("Country:", parsed.country)
print("Treaty starts:", parsed.start_page)
print("Articles:", len(parsed.articles))
print()

for a in parsed.articles[:10]:
    print(a.number, "-", a.title)
