from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data/legal_reviews/sk_outbound"
SEMANTIC = BASE / "treaty_semantic_candidates.json"
ARTICLES = BASE / "treaty_article_machine_extraction.json"
COVERAGE = BASE / "human_review_coverage.json"
INVENTORY = BASE / "treaty_instrument_inventory.json"
OUTPUT = ROOT / "data/legal_rules_sk"
SUMMARY = BASE / "structured_treaty_rule_materialization_summary.json"

RISKY_INTEREST = (
    "osloboden",
    "výlučne",
    "len v druhom",
    "bez ohľadu na ustanovenia odseku 2",
    "bez ohľadu na ustanovenia odseku 1",
    "nepresiahne:",
)

ROYALTY_UI_CATEGORIES = {
    "copyright": "copyright_literary_artistic_scientific_nonfilm_nonsoftware",
    "film": "cinematographic_films_or_broadcast_media",
    "software": "computer_software",
    "industrial_ip": "patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
    "equipment_financial": "financial_lease_of_equipment",
    "equipment_operating": "operating_lease_or_other_use_of_equipment",
    "other": "other",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def is_safe_simple(scope: dict, article: dict) -> bool:
    rates = scope.get("rate_candidates") or []
    if scope.get("exclusive_residence_taxation_candidate"):
        return (
            scope.get("income_type") == "interest"
            and len(rates) <= 1
            and int(scope.get("ownership_linked_rate_candidate_count") or 0) == 0
            and not scope.get("holding_period_candidates")
            and bool(scope.get("source_sha256"))
            and scope.get("semantic_status") == "machine_candidate_not_legal_conclusion"
        )
    if len(rates) != 1:
        return False
    if int(scope.get("ownership_linked_rate_candidate_count") or 0) != 0:
        return False
    if scope.get("holding_period_candidates"):
        return False
    if not scope.get("source_sha256"):
        return False
    if scope.get("semantic_status") != "machine_candidate_not_legal_conclusion":
        return False

    text = str(article.get("article_text") or "").lower()
    income = scope["income_type"]
    if income == "interest" and any(token in text for token in RISKY_INTEREST):
        return False
    if income == "dividend" and ("osloboden" in text or "nepresiahne:" in text):
        return False
    if income == "royalty":
        start = re.search(r"(?:\(2\)|\b2\.\s)", text)
        paragraph_2 = text[:1200]
        if start:
            tail = text[start.start():]
            end = re.search(r"(?:\(3\)|\b3\.\s)", tail[3:])
            paragraph_2 = tail[: (3 + end.start()) if end else 1200]
        if (
            "písm" in paragraph_2
            or "podľa písmena" in paragraph_2
            or "len v tomto" in paragraph_2
            or "iba v tomto" in paragraph_2
        ):
            return False
    return True


def conditions(scope: dict) -> list[dict]:
    result = [{
        "fact": "recipient_is_treaty_resident",
        "fact_source": "transaction",
        "operator": "==",
        "value": True,
    }]
    rate = (scope.get("rate_candidates") or [{}])[0]
    if scope.get("beneficial_owner_wording_present") or rate.get("beneficial_owner_context"):
        result.append({
            "fact": "beneficial_owner",
            "fact_source": "transaction",
            "operator": "==",
            "value": True,
        })
    if scope.get("pe_or_fixed_base_carveout_wording_present"):
        result.append({
            "fact": "permanent_establishment_connection",
            "fact_source": "transaction",
            "operator": "==",
            "value": False,
        })
    return result


def _article_paragraph_two(text: str) -> str:
    lowered = text.lower()
    start = re.search(r"(?:\(2\)|\b2\.\s)", lowered)
    if not start:
        return lowered[:2200]
    tail = lowered[start.start():]
    end = re.search(r"(?:\(3\)|\b3\.\s)", tail[3:])
    return tail[: (3 + end.start()) if end else 2600]


def _percent(value: str) -> float:
    return float(value.replace(",", "."))


_WORD_PERCENT_RATES = {
    "jeden": 1.0,
    "dva": 2.0,
    "dve": 2.0,
    "tri": 3.0,
    "štyri": 4.0,
    "päť": 5.0,
    "šesť": 6.0,
    "sedem": 7.0,
    "osem": 8.0,
    "deväť": 9.0,
    "desať": 10.0,
    "jedenásť": 11.0,
    "dvanásť": 12.0,
    "trinásť": 13.0,
    "štrnásť": 14.0,
    "pätnásť": 15.0,
    "dvadsať": 20.0,
    "dvadsaťpäť": 25.0,
}


def _source_text_residence_only(article: dict) -> bool:
    """Return True only for an explicit exclusive-residence rule in the operative opening text."""
    text = str(article.get("article_text") or "").lower()
    opening = text[:1600]
    patterns = (
        r"(?:podliehajú|podlieha|budú\s+podliehať)\s+zdaneniu\s+(?:len|iba|výlučne)\s+v\s+(?:tomto\s+)?druhom",
        r"(?:sa\s+)?(?:zdaňujú|zdania|zdaní|zdanené)\s+(?:len|iba|výlučne)\s+v\s+(?:tomto\s+)?druhom",
        r"(?:budú\s+)?zdanené\s+(?:len|iba|výlučne)\s+v\s+(?:tomto\s+)?druhom",
    )
    return any(re.search(pattern, opening, flags=re.S) for pattern in patterns)


def _single_word_percent_rate(scope: dict, article: dict) -> float | None:
    """
    Recover one unambiguous source-state ceiling written as a Slovak number word.

    This is intentionally narrower than semantic extraction: it is used only
    when no numeric rate candidate exists, paragraph 2 contains exactly one
    word-percent rate, and no explicit exception/category branch makes that
    rate conditional.
    """
    if scope.get("rate_candidates"):
        return None
    if not scope.get("source_sha256"):
        return None
    if scope.get("semantic_status") != "machine_candidate_not_legal_conclusion":
        return None
    if int(scope.get("ownership_linked_rate_candidate_count") or 0) != 0:
        return None
    if scope.get("holding_period_candidates"):
        return None

    text = str(article.get("article_text") or "").lower()
    para = _article_paragraph_two(text)
    matches: list[float] = []
    for word, rate in _WORD_PERCENT_RATES.items():
        if re.search(rf"\b{re.escape(word)}\s+percent", para):
            matches.append(rate)
    unique = sorted(set(matches))
    if len(unique) != 1:
        return None

    income = str(scope.get("income_type") or "")
    if income == "interest" and re.search(
        r"osloboden|nepodliehajú\s+dani|sa\s+nezdaňujú|bez\s+ohľadu\s+na\s+ustanovenia",
        text,
    ):
        return None
    if income == "dividend" and "osloboden" in text:
        return None
    if income == "royalty" and re.search(r"odseku\s*3\s*písm|podľa\s+písmena|písm\.", para):
        return None
    return unique[0]


def dividend_branches(scope: dict, article: dict) -> list[dict] | None:
    if scope.get("income_type") != "dividend":
        return None
    text = _article_paragraph_two(str(article.get("article_text") or ""))
    if not text or not scope.get("source_sha256"):
        return None

    fallback_match = re.search(
        r"([0-9]+(?:[,.][0-9]+)?)\s*%[^.;]{0,180}(?:vo\s+všetkých\s+ostatných\s+prípadoch|"
        r"v\s+ostatných\s+prípadoch|vo\s+všetkých\s+iných\s+prípadoch)",
        text,
        flags=re.S,
    )
    if not fallback_match:
        return None
    fallback_rate = _percent(fallback_match.group(1))

    ownership_match = re.search(
        r"([0-9]+(?:[,.][0-9]+)?)\s*%[^.;]{0,650}?"
        r"(?:priamo\s+(?:vlastní|má|drží)|hlasovac(?:ích|ie|ích\s+práv|ích\s+podielov)|"
        r"vlastní\s+priamo)[^.;]{0,260}?najmenej\s+([0-9]+(?:[,.][0-9]+)?)\s*%",
        text,
        flags=re.S,
    )
    if not ownership_match:
        ownership_match = re.search(
            r"([0-9]+(?:[,.][0-9]+)?)\s*%[^.;]{0,650}?najmenej\s+"
            r"([0-9]+(?:[,.][0-9]+)?)\s*%[^.;]{0,260}?"
            r"(?:priamo|hlasovac)",
            text,
            flags=re.S,
        )
    if not ownership_match:
        # Older treaties often require a corporate ownership threshold but do
        # not use the word 'directly'. The threshold itself is still explicit
        # in Article 10 and can be represented without inventing directness.
        ownership_match = re.search(
            r"([0-9]+(?:[,.][0-9]+)?)\s*%[^.;]{0,700}?"
            r"(?:spoločnosť|spoločnosťou)[^.;]{0,320}?"
            r"(?:vlastní|má|drží)[^.;]{0,120}?najmenej\s+"
            r"([0-9]+(?:[,.][0-9]+)?)\s*%",
            text,
            flags=re.S,
        )
    if not ownership_match:
        return None

    qualifying_rate = _percent(ownership_match.group(1))
    threshold = _percent(ownership_match.group(2))
    if qualifying_rate == fallback_rate:
        return None

    candidate_rates = {
        float(row["rate_percent"])
        for row in scope.get("rate_candidates", [])
        if row.get("rate_percent") is not None
    }
    if qualifying_rate not in candidate_rates or fallback_rate not in candidate_rates:
        return None

    qualifying_context = ownership_match.group(0)
    qualifying_conditions = conditions(scope)
    qualifying_conditions.append({
        "fact": "recipient_entity_type",
        "fact_source": "transaction",
        "operator": "in",
        "value": ["company", "corporate", "company_other_than_partnership"],
    })
    if "hlasovac" in qualifying_context:
        qualifying_conditions.append({
            "fact": "voting_interest_percent",
            "fact_source": "transaction",
            "operator": ">=",
            "value": threshold,
        })
    else:
        if "priamo" in qualifying_context:
            qualifying_conditions.append(
                {"fact": "direct_ownership", "fact_source": "transaction", "operator": "==", "value": True}
            )
        qualifying_conditions.append(
            {"fact": "ownership_percent", "fact_source": "transaction", "operator": ">=", "value": threshold}
        )

    holding = re.search(r"(?:počas\s+obdobia\s+)?(365)\s+dní", qualifying_context)
    if holding:
        qualifying_conditions.append({
            "fact": "holding_period_days",
            "fact_source": "transaction",
            "operator": ">=",
            "value": int(holding.group(1)),
        })

    return [
        {"rate": qualifying_rate, "priority": 650, "conditions": qualifying_conditions},
        {"rate": fallback_rate, "priority": 600, "conditions": conditions(scope)},
    ]


def interest_branches(scope: dict, article: dict) -> list[dict] | None:
    if scope.get("income_type") != "interest" or not scope.get("source_sha256"):
        return None
    text = str(article.get("article_text") or "").lower()
    common = conditions(scope)

    residence_only = bool(scope.get("exclusive_residence_taxation_candidate")) or bool(
        re.search(
            r"(?:zdaniť|zdanené|podliehajú\s+dani)[^.;]{0,120}(?:len|iba|výlučne)[^.;]{0,120}"
            r"(?:druhom\s+zmluvnom\s+štáte|štáte,\s+ktorého\s+je\s+príjemca\s+rezidentom)",
            text,
            flags=re.S,
        )
    )
    if residence_only:
        return [{
            "rate": 0.0,
            "priority": 650,
            "conditions": common,
            "tax_treatment": "exclusive_foreign_taxation",
            "suffix": "INTEREST-RESIDENCE-ONLY",
        }]

    rates = [
        float(row["rate_percent"])
        for row in scope.get("rate_candidates", [])
        if row.get("rate_percent") is not None
    ]
    unique_rates = sorted(set(rates))
    if len(unique_rates) != 1:
        return None
    general_rate = unique_rates[0]

    has_explicit_exemption = bool(re.search(
        r"(?:osloboden(?:é|ý|á|ia)|nepodliehajú\s+dani|sa\s+nezdaňujú|"
        r"bez\s+ohľadu\s+na\s+ustanovenia\s+odseku\s+[12])",
        text,
    ))
    if not has_explicit_exemption:
        return None

    special = list(common)
    special.append({
        "fact": "article_11_special_exemption",
        "fact_source": "transaction",
        "operator": "==",
        "value": True,
    })
    ordinary = list(common)
    ordinary.append({
        "fact": "article_11_special_exemption",
        "fact_source": "transaction",
        "operator": "==",
        "value": False,
    })
    return [
        {
            "rate": 0.0,
            "priority": 700,
            "conditions": special,
            "tax_treatment": "exclusive_foreign_taxation",
            "suffix": "INTEREST-SPECIAL-EXEMPTION",
        },
        {"rate": general_rate, "priority": 600, "conditions": ordinary, "suffix": "INTEREST-GENERAL"},
    ]


def _royalty_categories_from_text(text: str) -> list[str]:
    lowered = text.lower()
    categories: list[str] = []
    if any(token in lowered for token in ("autorsk", "literár", "umeleck", "vedeck")):
        categories.append(ROYALTY_UI_CATEGORIES["copyright"])
    if any(token in lowered for token in ("kinematograf", "film", "televíz", "rozhlas", "rádio")):
        categories.append(ROYALTY_UI_CATEGORIES["film"])
    if any(token in lowered for token in ("počítač", "software", "programové vybaven")):
        categories.append(ROYALTY_UI_CATEGORIES["software"])
    if any(token in lowered for token in (
        "patent", "ochrann", "známk", "návrh", "model", "plán", "tajného vzorca",
        "tajnej receptúry", "výrobného postupu", "proces", "know-how", "skúsenost",
    )):
        categories.append(ROYALTY_UI_CATEGORIES["industrial_ip"])
    financial_lease = any(token in lowered for token in (
        "finančný prenájom", "finančného prenájmu", "finančnom prenájme", "financial lease",
    ))
    operating_lease = any(token in lowered for token in (
        "operatívny prenájom", "operatívneho prenájmu", "prevádzkový prenájom",
        "prevádzkového prenájmu", "operating lease",
    ))
    if financial_lease:
        categories.append(ROYALTY_UI_CATEGORIES["equipment_financial"])
    if operating_lease:
        categories.append(ROYALTY_UI_CATEGORIES["equipment_operating"])
    if "zariaden" in lowered and not financial_lease and not operating_lease:
        categories.extend([
            ROYALTY_UI_CATEGORIES["equipment_financial"],
            ROYALTY_UI_CATEGORIES["equipment_operating"],
        ])
    if "všetkých ostatných" in lowered or "všetky ostatné" in lowered:
        categories.append(ROYALTY_UI_CATEGORIES["other"])
    return list(dict.fromkeys(categories))


def _all_royalty_categories() -> list[str]:
    return list(dict.fromkeys(ROYALTY_UI_CATEGORIES.values()))


def _definition_letter(text: str, letter: str) -> str | None:
    lowered = text.lower()
    definition = re.search(r"(?:\(3\)|\b3\.\s)[\s\S]{0,4200}", lowered)
    haystack = definition.group(0) if definition else lowered
    match = re.search(
        rf"(?:^|[;:.]\s*){letter}\)\s*([\s\S]*?)(?=(?:[;:.]\s*)[a-d]\)\s|(?:\(4\)|\b4\.\s)|$)",
        haystack,
    )
    return match.group(1) if match else None


def _categories_for_rate_clause(article_text: str, clause: str) -> list[str]:
    categories = _royalty_categories_from_text(clause)
    ref = re.search(
        r"(?:odseku|odsek)\s*3\s*(?:písm(?:ena|eno)?\.?\s*)?([a-d])\)?",
        clause,
    )
    if ref:
        definition = _definition_letter(article_text, ref.group(1))
        if definition:
            categories = _royalty_categories_from_text(definition)
    return categories


def _lettered_royalty_rate_branches(scope: dict, article_text: str) -> list[dict] | None:
    para = _article_paragraph_two(article_text)
    matches = list(re.finditer(
        r"(?:^|[;:.]\s*)([a-d])\)\s*([0-9]+(?:[,.][0-9]+)?)\s*%\s*([\s\S]*?)"
        r"(?=(?:[;:.]\s*)[a-d]\)\s*[0-9]|(?:\(3\)|\b3\.\s)|$)",
        para,
    ))
    if len(matches) < 2:
        return None

    parsed = []
    assigned: set[str] = set()
    fallback_rows = []
    for match in matches:
        clause = match.group(3).strip()
        rate = _percent(match.group(2))
        is_fallback = bool(re.search(r"(?:všetkých|všetky)\s+(?:ostatných|ostatné)", clause))
        categories = _categories_for_rate_clause(article_text, clause)
        row = (rate, clause, categories)
        if is_fallback:
            fallback_rows.append(row)
        else:
            if not categories:
                return None
            assigned.update(categories)
            parsed.append(row)

    if len(fallback_rows) > 1:
        return None
    if fallback_rows:
        rate, clause, _ = fallback_rows[0]
        complement = [cat for cat in _all_royalty_categories() if cat not in assigned]
        if not complement:
            return None
        parsed.append((rate, clause, complement))

    candidate_rates = {
        float(row["rate_percent"])
        for row in scope.get("rate_candidates", [])
        if row.get("rate_percent") is not None
    }
    if not candidate_rates:
        return None
    if any(rate not in candidate_rates for rate, _, _ in parsed):
        return None

    common = conditions(scope)
    branches: list[dict] = []
    for branch_index, (rate, _, categories) in enumerate(parsed, start=1):
        for category_index, category in enumerate(categories, start=1):
            branches.append({
                "rate": rate,
                "priority": 690,
                "conditions": [
                    *common,
                    {"fact": "royalty_category", "fact_source": "transaction", "operator": "==", "value": category},
                ],
                "suffix": f"ROYALTY-LETTER-{branch_index}-{category_index}",
            })
    return branches or None


def royalty_branches(scope: dict, article: dict) -> list[dict] | None:
    """Materialize source-explicit royalty categories, never percentage lists alone."""
    if scope.get("income_type") != "royalty" or not scope.get("source_sha256"):
        return None
    text = str(article.get("article_text") or "").lower()
    common = conditions(scope)

    residence_only = bool(re.search(
        r"licenčné\s+poplatky[^.]{0,240}(?:môžu\s+sa\s+zdaniť|sa\s+zdania)\s+(?:len|iba|výlučne)\s+v\s+tomto\s+druhom\s+štáte",
        text,
    ))
    percentages = {_percent(value) for value in re.findall(r"([0-9]+(?:[,.][0-9]+)?)\s*%", _article_paragraph_two(text))}
    if residence_only and not percentages:
        return [{
            "rate": 0.0,
            "priority": 650,
            "conditions": common,
            "tax_treatment": "exclusive_foreign_taxation",
            "suffix": "ROYALTY-RESIDENCE-ONLY",
        }]

    ref = re.search(
        r"(?:odseku|odsek)\s*3\s*(?:písm(?:ena|eno)?\.?\s*)?([ab])\)?[^%]{0,240}"
        r"([0-9]+(?:[,.][0-9]+)?)\s*%",
        text,
        flags=re.S,
    )
    if not ref:
        ref = re.search(
            r"licenčné\s+poplatky[^.]{0,240}(?:3\s*([ab])\))[^%]{0,240}"
            r"([0-9]+(?:[,.][0-9]+)?)\s*%",
            text,
            flags=re.S,
        )
    if residence_only and ref:
        taxed_letter = ref.group(1)
        taxed_rate = _percent(ref.group(2))
        other_letter = "a" if taxed_letter == "b" else "b"
        taxed_text = _definition_letter(text, taxed_letter)
        other_text = _definition_letter(text, other_letter)
        if taxed_text and other_text:
            taxed_categories = _royalty_categories_from_text(taxed_text)
            exempt_categories = _royalty_categories_from_text(other_text)
            if taxed_categories and exempt_categories:
                branches: list[dict] = []
                for index, category in enumerate(exempt_categories, start=1):
                    branches.append({
                        "rate": 0.0,
                        "priority": 680,
                        "conditions": [
                            *common,
                            {"fact": "royalty_category", "fact_source": "transaction", "operator": "==", "value": category},
                        ],
                        "tax_treatment": "exclusive_foreign_taxation",
                        "suffix": f"ROYALTY-RESIDENCE-{other_letter.upper()}-{index}",
                    })
                for index, category in enumerate(taxed_categories, start=1):
                    branches.append({
                        "rate": taxed_rate,
                        "priority": 680,
                        "conditions": [
                            *common,
                            {"fact": "royalty_category", "fact_source": "transaction", "operator": "==", "value": category},
                        ],
                        "suffix": f"ROYALTY-SOURCE-{taxed_letter.upper()}-{index}",
                    })
                return branches

    lettered = _lettered_royalty_rate_branches(scope, text)
    if lettered:
        return lettered
    return None

def _make_rule(
    *,
    scope: dict,
    article: dict,
    country: str,
    income: str,
    rate: float | None,
    priority: int,
    rule_conditions: list[dict],
    rule_suffix: str,
    treaty_valid_from: dict[str, str],
    coverage: dict,
    tax_treatment: str | None = None,
    effect: str = "rate",
) -> dict:
    article_text = str(article["article_text"])
    source_hash = str(scope["source_sha256"])
    rule = {
        "rule_id": f"SK-{country}-{income.upper()}-TREATY-{rule_suffix}",
        "income_type": income,
        "source_country": "SK",
        "recipient_country": country,
        "legal_instrument": "treaty",
        "legal_layer": "treaty",
        "article": str(scope["actual_article"]),
        "paragraph": None,
        "rate": rate,
        "priority": priority,
        "conditions": rule_conditions,
        "effect": effect,
        "effective_from": treaty_valid_from[country],
        "verification_status": "needs_review",
        "source_text": article_text,
        "source_id": f"SK-SLOVLEX-{source_hash[:16].upper()}",
        "source_url": scope["source_url"],
        "source_excerpt_hash": hashlib.sha256(article_text.encode("utf-8")).hexdigest(),
        "verification_authority": "sk_legal_review_coverage_pattern_reconciliation",
        "reviewer_id": "sk_legal_review_coverage",
        "reviewed_at": "2026-08-21",
        "approval_dataset_release": coverage["dataset_release"],
        "approval_created_at": "2026-09-01",
        "dataset_release": "sk-structured-treaty-rules-2026-09-01.4",
        "evidence_source_ids": [f"SK-SLOVLEX-{source_hash[:16].upper()}"],
        "decision_status": "REVIEW_REQUIRED",
        "final_rate_allowed": False,
        "automatic_production_approval_forbidden": True,
    }
    if tax_treatment:
        rule["tax_treatment"] = tax_treatment
    return rule


def main() -> int:
    semantic = load(SEMANTIC)
    articles = load(ARTICLES)
    coverage = load(COVERAGE)
    inventory = load(INVENTORY)
    treaty_valid_from = {
        row["recipient_country"]: row["treaty_valid_from"]
        for row in inventory["relationships"]
    }

    assert coverage["coverage"]["legal_review_covered_scopes"] == 225
    assert coverage["coverage"]["uncovered_scopes"] == 0
    assert coverage["individual_review"]["substantive_machine_discrepancies"] == 0

    article_by = {
        (row["recipient_country"], row["income_type"]): row
        for row in articles["scopes"]
    }

    grouped: dict[str, list[dict]] = defaultdict(list)
    unresolved = []
    materialized = []
    materialization_modes = defaultdict(int)

    for scope in semantic["scopes"]:
        key = (scope["recipient_country"], scope["income_type"])
        article = article_by[key]
        country = scope["recipient_country"]
        income = scope["income_type"]

        branches = dividend_branches(scope, article)
        if branches:
            for index, branch in enumerate(branches, start=1):
                grouped[country].append(_make_rule(
                    scope=scope,
                    article=article,
                    country=country,
                    income=income,
                    rate=float(branch["rate"]),
                    priority=int(branch["priority"]),
                    rule_conditions=branch["conditions"],
                    rule_suffix=f"DIVIDEND-BRANCH-{index}",
                    treaty_valid_from=treaty_valid_from,
                    coverage=coverage,
                ))
            materialized.append(f"SK-{country}-{income}")
            materialization_modes["source_text_dividend_branch_pair"] += 1
            continue

        branches = interest_branches(scope, article)
        if branches:
            for branch in branches:
                grouped[country].append(_make_rule(
                    scope=scope,
                    article=article,
                    country=country,
                    income=income,
                    rate=float(branch["rate"]),
                    priority=int(branch["priority"]),
                    rule_conditions=branch["conditions"],
                    rule_suffix=str(branch.get("suffix") or "INTEREST-BRANCH"),
                    treaty_valid_from=treaty_valid_from,
                    coverage=coverage,
                    tax_treatment=branch.get("tax_treatment"),
                ))
            materialized.append(f"SK-{country}-{income}")
            materialization_modes[
                "source_text_interest_special_exemption" if len(branches) > 1
                else "source_text_interest_residence_only"
            ] += 1
            continue

        branches = royalty_branches(scope, article)
        if branches:
            for branch in branches:
                grouped[country].append(_make_rule(
                    scope=scope,
                    article=article,
                    country=country,
                    income=income,
                    rate=float(branch["rate"]),
                    priority=int(branch["priority"]),
                    rule_conditions=branch["conditions"],
                    rule_suffix=str(branch.get("suffix") or "ROYALTY-BRANCH"),
                    treaty_valid_from=treaty_valid_from,
                    coverage=coverage,
                    tax_treatment=branch.get("tax_treatment"),
                ))
            materialized.append(f"SK-{country}-{income}")
            materialization_modes[
                "source_text_royalty_category_branches" if len(branches) > 1
                else "source_text_royalty_residence_only"
            ] += 1
            continue

        if _source_text_residence_only(article):
            grouped[country].append(_make_rule(
                scope=scope,
                article=article,
                country=country,
                income=income,
                rate=0.0,
                priority=650,
                rule_conditions=conditions(scope),
                rule_suffix=f"{income.upper()}-SOURCE-TEXT-RESIDENCE-ONLY",
                treaty_valid_from=treaty_valid_from,
                coverage=coverage,
                tax_treatment="exclusive_foreign_taxation",
            ))
            materialized.append(f"SK-{country}-{income}")
            materialization_modes["source_text_explicit_residence_only"] += 1
            continue

        word_rate = _single_word_percent_rate(scope, article)
        if word_rate is not None:
            grouped[country].append(_make_rule(
                scope=scope,
                article=article,
                country=country,
                income=income,
                rate=float(word_rate),
                priority=600,
                rule_conditions=conditions(scope),
                rule_suffix=f"{income.upper()}-SOURCE-TEXT-WORD-RATE",
                treaty_valid_from=treaty_valid_from,
                coverage=coverage,
            ))
            materialized.append(f"SK-{country}-{income}")
            materialization_modes["source_text_single_word_rate"] += 1
            continue

        if not is_safe_simple(scope, article):
            unresolved.append({
                "recipient_country": country,
                "income_type": income,
                "rate_candidates": [row.get("rate_percent") for row in scope.get("rate_candidates", [])],
                "exclusive_residence_taxation_candidate": bool(scope.get("exclusive_residence_taxation_candidate")),
                "ownership_linked_rate_candidate_count": int(scope.get("ownership_linked_rate_candidate_count") or 0),
                "holding_period_candidates": scope.get("holding_period_candidates", []),
            })
            # Preserve complete 75 x 3 runtime scope coverage without inventing
            # a treaty rate. The unresolved source-backed rule is deliberately
            # unverified and has no structured rate, so the legal engine stays
            # REVIEW_REQUIRED even when its common entitlement conditions match.
            grouped[country].append(_make_rule(
                scope=scope,
                article=article,
                country=country,
                income=income,
                rate=None,
                priority=900,
                rule_conditions=conditions(scope),
                rule_suffix="UNRESOLVED-FAIL-CLOSED",
                treaty_valid_from=treaty_valid_from,
                coverage=coverage,
                effect="review_gate",
            ))
            continue

        exclusive_residence = bool(scope.get("exclusive_residence_taxation_candidate"))
        rate = 0.0 if exclusive_residence else float(scope["rate_candidates"][0]["rate_percent"])
        grouped[country].append(_make_rule(
            scope=scope,
            article=article,
            country=country,
            income=income,
            rate=rate,
            priority=600,
            rule_conditions=conditions(scope),
            rule_suffix="SIMPLE-1",
            treaty_valid_from=treaty_valid_from,
            coverage=coverage,
            tax_treatment="exclusive_foreign_taxation" if exclusive_residence else None,
        ))
        materialized.append(f"SK-{country}-{income}")
        materialization_modes[
            "exclusive_residence_interest" if exclusive_residence else "simple_single_rate"
        ] += 1

    OUTPUT.mkdir(parents=True, exist_ok=True)
    for path in OUTPUT.glob("*.json"):
        path.unlink()

    for country, rules in sorted(grouped.items()):
        payload = {
            "country_pair": {"source_country": "SK", "recipient_country": country},
            "rules": sorted(rules, key=lambda row: (row["income_type"], -row["priority"], row["rule_id"])),
        }
        (OUTPUT / f"{country.lower()}.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    summary = {
        "schema_version": 4,
        "dataset_release": "sk-structured-treaty-rules-2026-09-01.4",
        "source_country": "SK",
        "total_scopes": 225,
        "materialized_scopes": len(materialized),
        "decision_materialized_scopes": len(materialized),
        "fail_closed_placeholder_scopes": len(unresolved),
        "structured_scope_coverage": len(materialized) + len(unresolved),
        "unresolved_scopes": len(unresolved),
        "materialized_country_packages": len(grouped),
        "materialized_scope_keys": sorted(materialized),
        "materialization_modes": dict(sorted(materialization_modes.items())),
        "unresolved_by_income": {income: sum(1 for row in unresolved if row["income_type"] == income) for income in ("dividend", "interest", "royalty")},
        "unresolved": unresolved,
        "policy": {
            "machine_rate_list_alone_is_never_sufficient_for_complex_branch_materialization": True,
            "source_text_explicit_dividend_branch_pairs_materialized": True,
            "source_text_fallback_phrase_required_for_dividend_branch_pair": True,
            "source_text_explicit_interest_exemption_branches_materialized": True,
            "source_text_explicit_residence_only_materialized": True,
            "source_text_single_word_rate_requires_one_unambiguous_paragraph_two_ceiling": True,
            "source_text_word_rate_complex_exemptions_and_category_splits_remain_fail_closed": True,
            "ordinary_interest_rate_requires_special_exemption_false_when_exemption_exists": True,
            "source_text_explicit_royalty_definition_letter_branches_materialized": True,
            "royalty_category_materialization_uses_atomic_ui_taxonomy": True,
            "unmapped_royalty_categories_remain_fail_closed": True,
            "stage_rules_remain_needs_review_until_all_protocol_mli_and_release_gates_are_satisfied": True,
            "czech_rule_reuse_forbidden": True,
            "all_225_scopes_have_runtime_structured_coverage": True,
            "unresolved_scopes_use_rate_null_fail_closed_placeholders": True,
            "rule_level_finalization_remains_closed_for_unresolved_scopes": True,
            "automatic_production_approval_forbidden": True,
        },
    }
    SUMMARY.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"SK decision-materialized rules: {len(materialized)}/225 scopes")
    print(f"SK structured runtime coverage: {len(materialized) + len(unresolved)}/225 scopes")
    print(f"country packages: {len(grouped)}")
    print(f"unresolved: {len(unresolved)}")
    print(f"modes: {dict(sorted(materialization_modes.items()))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
