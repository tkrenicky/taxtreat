from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_DIR = ROOT / "reports" / "treaty_en_locale_bulk_candidates_v9_20260825"
SUMMARY = ROOT / "reports" / "treaty_en_locale_bulk_candidates_v9_20260825.json"
LOCALE_DIR = ROOT / "app" / "web" / "treaty-excerpt-locales"
PROMOTION_SUMMARY = ROOT / "reports" / "treaty_en_locale_bulk_promotion_20260825.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _promotion_status(en: dict) -> str:
    status = str(en.get("status") or "").strip()
    if status.startswith("candidate_official_"):
        return status.removeprefix("candidate_")
    if status.startswith("official_"):
        return status
    # Fail-safe metadata: the promotion gate proves official-source provenance and
    # English text, but authenticity must be established separately.
    return "official_source_english_text"


def main() -> int:
    if not SUMMARY.exists():
        raise SystemExit(f"missing extraction summary: {SUMMARY.relative_to(ROOT)}")
    summary = _load(SUMMARY)
    status_by_pair = {}
    for row in summary.get("results", []):
        country = str(row.get("country") or "").upper()
        for article, result in (row.get("articles") or {}).items():
            status_by_pair[(country, str(article))] = str((result or {}).get("status") or "")
    LOCALE_DIR.mkdir(parents=True, exist_ok=True)
    promoted, skipped = [], []
    for candidate_path in sorted(CANDIDATE_DIR.glob("*.json")):
        candidate = _load(candidate_path)
        country = str(candidate.get("recipient_country") or candidate_path.stem).upper()
        target_path = LOCALE_DIR / f"{country}.json"
        target = _load(target_path) if target_path.exists() else {"schema_version": 1, "source_country": "CZ", "recipient_country": country, "articles": {}}
        target_articles = target.setdefault("articles", {})
        changed = False
        for article, locale_entry in (candidate.get("articles") or {}).items():
            article = str(article)
            status = status_by_pair.get((country, article), "")
            en = (locale_entry or {}).get("en") or {}
            if status != "PASS":
                skipped.append({"country": country, "article": article, "reason": f"status={status or 'UNKNOWN'}"})
                continue
            text = str(en.get("text") or "").strip()
            source_url = str(en.get("source_url") or "").strip()
            if not text or not source_url.startswith("http"):
                skipped.append({"country": country, "article": article, "reason": "missing_text_or_source"})
                continue
            existing = ((target_articles.get(article) or {}).get("en") or {})
            if str(existing.get("text") or "").strip():
                skipped.append({"country": country, "article": article, "reason": "existing_locale_preserved"})
                continue
            promoted_entry = dict(locale_entry)
            promoted_en = dict(en)
            promoted_en["status"] = _promotion_status(en)
            promoted_entry["en"] = promoted_en
            target_articles[article] = promoted_entry
            promoted.append({"country": country, "article": article, "source_url": source_url, "locale_status": promoted_en["status"]})
            changed = True
        if changed:
            target_path.write_text(json.dumps(target, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    PROMOTION_SUMMARY.write_text(json.dumps({"schema_version": 1, "promoted_count": len(promoted), "skipped_count": len(skipped), "promoted": promoted, "skipped": skipped}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Bulk EN locale promotion: promoted={len(promoted)} skipped={len(skipped)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
