from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

INTAKE = (
    ROOT
    / "data/legal_reviews/global_cz_outbound/"
    "stage5_remaining80_batch_01_intake.json"
)

MLI_EVIDENCE = (
    ROOT
    / "data/legal_reviews/global_cz_outbound/"
    "stage5_remaining80_batch_01_mli_evidence.json"
)

MF_INVENTORY = (
    ROOT
    / "data/legal_consolidation/"
    "mf_inventory.json"
)

SOURCE_MANIFEST = (
    ROOT
    / "data/manifests/"
    "source_manifest.json"
)

LEGACY_CHAINS = (
    ROOT
    / "data/legal_consolidation/"
    "remaining_294_instrument_chains.json"
)

DOMESTIC_EU = (
    ROOT
    / "data/legal_consolidation/"
    "cz_domestic_eu_candidates.json"
)

OUTPUT = (
    ROOT
    / "data/legal_reviews/global_cz_outbound/"
    "stage5_remaining80_batch_01_legal_chain_dossier.json"
)

ARTICLE_HEADINGS_BY_INCOME = {
    "dividend": {"dividendy"},
    # Some treaties title the interest article by the underlying
    # debt-claim concept rather than using the Czech word for interest.
    "interest": {"uroky", "prijmyzpohledavek"},
    # ``licencnopoplatky`` is the stable OCR form in several
    # repository-parsed Czech official publications (``Licencnõ``).
    "royalty": {"licencnipoplatky", "licencnopoplatky"},
}

ARTICLE_KEYS = {
    "article",
    "article_no",
    "article_number",
    "articlenumber",
    "number",
    "no",
}

TEXT_KEYS = {
    "text",
    "content",
    "body",
    "paragraph",
    "paragraphs",
    "title",
    "heading",
    "raw_text",
    "source_text",
    "article_text",
}


def load(path: Path) -> Any:
    if not path.is_file():
        raise RuntimeError(
            f"Required file missing: {path.relative_to(ROOT)}"
        )

    return json.loads(
        path.read_text(encoding="utf-8")
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def normalize(value: Any) -> str:
    if not isinstance(value, str):
        return ""

    text = unicodedata.normalize(
        "NFKD",
        value,
    )

    text = "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )

    return re.sub(
        r"\s+",
        " ",
        text,
    ).strip().casefold()


def walk(value: Any, path: str = "$"):
    yield path, value

    if isinstance(value, dict):

        for key, item in value.items():
            yield from walk(
                item,
                f"{path}.{key}",
            )

    elif isinstance(value, list):

        for index, item in enumerate(value):
            yield from walk(
                item,
                f"{path}[{index}]",
            )


def collect_text(value: Any) -> str:
    parts = []

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, dict):

        for key, item in value.items():

            if (
                str(key).casefold() in TEXT_KEYS
                and isinstance(item, str)
            ):
                parts.append(item.strip())

            elif isinstance(item, list):

                for child in item:
                    if isinstance(child, str):
                        parts.append(child.strip())

    return "\n".join(
        part
        for part in parts
        if part
    )


def explicit_article_number(
    node: dict[str, Any],
) -> int | None:

    for key, value in node.items():

        if str(key).casefold() not in ARTICLE_KEYS:
            continue

        if isinstance(value, int):
            if 1 <= value <= 99:
                return value

        if isinstance(value, str):

            match = re.search(
                r"\b([1-9][0-9]?)\b",
                value,
            )

            if match:
                return int(match.group(1))

    return None


def article_anchor_match(
    text: str,
    article: int,
) -> bool:

    normalized = normalize(text)

    patterns = [
        rf"\barticle\s*{article}\b",
        rf"\bart\.?\s*{article}\b",
        rf"\bclanek\s*{article}\b",
        rf"\bcl\.?\s*{article}\b",
    ]

    return any(
        re.search(pattern, normalized)
        for pattern in patterns
    )


def normalized_heading(value: Any) -> str:
    normalized = re.sub(
        r"[^a-z0-9]",
        "",
        normalize(value),
    )
    # Some official OCR parses place the first paragraph number in the
    # structured title (for example ``1. Dividendy ...``).  Discard only
    # that leading paragraph marker; the income term still comes from the
    # treaty's own structured heading/title rather than a model article map.
    return re.sub(r"^\d+", "", normalized)


def income_article_evidence(
    parsed: Any,
    income: str,
) -> dict[str, Any]:

    hits = []

    seen = set()

    expected_headings = ARTICLE_HEADINGS_BY_INCOME[income]

    # Resolve only a structured article whose explicit number and
    # income heading agree. Article numbering is treaty-specific:
    # it must not be inferred from the OECD model sequence.
    for path, value in walk(parsed):

        if not isinstance(value, dict):
            continue

        article = explicit_article_number(value)

        if article is None:
            continue

        headings = [
            item
            for key, item in value.items()
            if str(key).casefold() in {"title", "heading"}
            and isinstance(item, str)
        ]

        # A small number of OCR parses preserve only ``1.`` as the title and
        # put the actual income heading at the start of the article text.
        # Treat that first line as the structured heading candidate only when
        # the parsed title contains no letters after normalization.
        if headings and not any(normalized_heading(item) for item in headings):
            article_text = value.get("text")
            if isinstance(article_text, str):
                headings.append(article_text.splitlines()[0][:160])

        if not any(
            normalized_heading(heading).startswith(expected_heading)
            for heading in headings
            for expected_heading in expected_headings
        ):
            continue

        text = collect_text(value)

        key = (
            path,
            text[:1000],
        )

        if key in seen:
            continue

        seen.add(key)

        hits.append(
            {
                "json_path": path,
                "resolution_method":
                    "structured_income_heading_and_article_number",
                "article_number": article,
                "heading": headings[0] if headings else None,
                "excerpt":
                    text[:1500] if text else None,
            }
        )

    resolved = len(hits) == 1

    return {
        "income_type": income,
        "article_number":
            hits[0]["article_number"] if resolved else None,
        "resolved": resolved,
        "resolution_status": (
            "resolved" if resolved
            else "unresolved" if not hits
            else "ambiguous"
        ),
        "evidence_count":
            len(hits),
        "evidence":
            hits[:5],
    }


def find_country_nodes(
    payload: Any,
    country: str,
) -> list[dict[str, Any]]:

    results = []

    token = country.upper()

    for path, value in walk(payload):

        if not isinstance(value, dict):
            continue

        strings = []

        for key, item in value.items():

            if isinstance(item, str):
                strings.append(
                    item.upper()
                )

            strings.append(
                str(key).upper()
            )

        if any(
            token == item
            or f"-{token}-" in item
            or item.endswith(f"-{token}")
            or item.startswith(f"{token}-")
            for item in strings
        ):

            results.append(
                {
                    "json_path":
                        path,
                    "snapshot":
                        value,
                }
            )

    return results[:20]


def scope_present(
    payload: Any,
    country: str,
    income: str,
) -> bool:

    expected = (
        f"CZ-{country}-{income}"
    ).casefold()

    for _, value in walk(payload):

        if (
            isinstance(value, str)
            and value.casefold() == expected
        ):
            return True

        if not isinstance(value, dict):
            continue

        flat = " ".join(
            str(item)
            for item in value.values()
            if isinstance(
                item,
                (str, int, float, bool)
            )
        ).casefold()

        if (
            country.casefold() in flat
            and income.casefold() in flat
        ):
            return True

    return False


def instrument_classification(
    partner: dict[str, Any],
) -> dict[str, Any]:

    related = [
        row
        for row in (
            partner.get(
                "related_instruments"
            )
            or []
        )
        if isinstance(row, dict)
    ]

    protocols = []
    status = []
    mli = []
    other = []

    for row in related:

        source_type = normalize(
            row.get("source_type")
        )

        combined = normalize(
            json.dumps(
                row,
                ensure_ascii=False,
            )
        )

        if (
            "protocol" in source_type
            or "protokol" in combined
            or "amend" in source_type
        ):
            protocols.append(row)

        elif (
            "status" in source_type
            or "suspens" in combined
            or "termination" in combined
            or "pozastav" in combined
            or "vypoved" in combined
        ):
            status.append(row)

        elif "mli" in source_type or "mli" in combined:
            mli.append(row)

        else:
            other.append(row)

    return {
        "protocols_and_amendments":
            protocols,
        "status_instruments":
            status,
        "mli_instruments":
            mli,
        "other_related_instruments":
            other,
    }


def evidence_fields(
    value: Any,
    keywords: tuple[str, ...],
) -> list[dict[str, Any]]:

    results = []

    for path, node in walk(value):

        if not isinstance(node, dict):
            continue

        for key, item in node.items():

            key_norm = normalize(str(key))

            if not any(
                word in key_norm
                for word in keywords
            ):
                continue

            if item in (
                None,
                "",
                [],
                {},
            ):
                continue

            results.append(
                {
                    "json_path":
                        f"{path}.{key}",
                    "value":
                        item,
                }
            )

    return results[:30]


def main() -> None:

    intake = load(INTAKE)
    mli_evidence = load(MLI_EVIDENCE)
    inventory = load(MF_INVENTORY)
    source_manifest = load(SOURCE_MANIFEST)
    legacy = load(LEGACY_CHAINS)
    domestic_eu = load(DOMESTIC_EU)

    countries = intake["batch"]["countries"]

    if len(countries) != 10:
        raise RuntimeError(
            "Batch 01 must contain exactly 10 countries"
        )

    partners = {
        row["iso2"]: row
        for row in inventory["partners"]
        if isinstance(row, dict)
        and row.get("iso2")
    }

    intake_entries = {
        row["country"]: row
        for row in intake["entries"]
    }

    output_entries = []

    total_scopes = 0
    resolved_articles = 0

    for country in countries:

        if country not in partners:
            raise RuntimeError(
                f"Missing MF inventory partner: {country}"
            )

        if country not in intake_entries:
            raise RuntimeError(
                f"Missing intake entry: {country}"
            )

        partner = partners[country]
        intake_entry = intake_entries[country]

        canonical = intake_entry[
            "canonical_base_treaty_source"
        ]

        parsed_path = (
            ROOT
            / canonical["parsed_path"]
        )

        parsed = load(parsed_path)

        article_map = {
            income:
                income_article_evidence(
                    parsed,
                    income,
                )
            for income in ARTICLE_HEADINGS_BY_INCOME
        }

        resolved_articles += sum(
            1
            for item in article_map.values()
            if item["resolved"]
        )

        instruments = (
            instrument_classification(
                partner
            )
        )

        language_evidence = (
            evidence_fields(
                {
                    "partner": partner,
                    "source":
                        canonical,
                    "source_manifest":
                        source_manifest,
                },
                (
                    "language",
                    "jazyk",
                    "authentic",
                    "prevailing",
                ),
            )
        )

        effective_date_evidence = (
            evidence_fields(
                {
                    "partner": partner,
                    "source":
                        canonical,
                },
                (
                    "effective",
                    "entry_into_force",
                    "entry into force",
                    "withholding",
                    "applicable_from",
                    "valid_from",
                ),
            )
        )

        legacy_nodes = (
            find_country_nodes(
                legacy,
                country,
            )
        )

        country_gaps = []

        for income in ARTICLE_HEADINGS_BY_INCOME:

            if not article_map[income][
                "resolved"
            ]:
                country_gaps.append(
                    f"{income}_article_source_location_not_resolved"
                )

        if not language_evidence:
            country_gaps.append(
                "language_authority_evidence_not_resolved"
            )

        if not effective_date_evidence:
            country_gaps.append(
                "effective_date_evidence_not_resolved"
            )

        if instruments[
            "status_instruments"
        ]:
            country_gaps.append(
                "status_instrument_effect_requires_human_review"
            )

        if not legacy_nodes:
            country_gaps.append(
                "legacy_instrument_chain_reference_not_resolved"
            )

        mli_status = {
            "source":
                "mf_inventory",
            "mli_listed":
                bool(
                    partner.get(
                        "mli_listed"
                    )
                ),
            "mli_notice_available":
                bool(
                    partner.get(
                        "mli_notice_available"
                    )
                ),
            "batch01_specific_evidence":
                None,
        }

        if country in (
            mli_evidence.get(
                "countries"
            )
            or {}
        ):

            mli_status[
                "batch01_specific_evidence"
            ] = (
                mli_evidence[
                    "countries"
                ][country]
            )

        scopes = []

        for income in ARTICLE_HEADINGS_BY_INCOME:

            scope_id = (
                f"CZ-{country}-{income}"
            )

            scope_gaps = []

            article_info = (
                article_map[income]
            )

            if not article_info["resolved"]:
                scope_gaps.append(
                    f"{income}_article_source_location_not_resolved"
                )

            domestic_present = (
                scope_present(
                    domestic_eu,
                    country,
                    income,
                )
            )

            if not domestic_present:
                scope_gaps.append(
                    "domestic_eu_layer_reference_not_resolved"
                )

            scopes.append(
                {
                    "scope_id":
                        scope_id,
                    "recipient_country":
                        country,
                    "income_type":
                        income,
                    "treaty_article":
                        article_info["article_number"],
                    "article_evidence":
                        article_info,
                    "domestic_eu_layer_reference_present":
                        domestic_present,
                    "verification_status":
                        "needs_review",
                    "stage5_terminal_status":
                        "pending",
                    "production_releasable":
                        False,
                    "human_primary_review_complete":
                        False,
                    "independent_approval_complete":
                        False,
                    "legal_chain_gaps":
                        sorted(
                            set(scope_gaps)
                        ),
                }
            )

        total_scopes += len(scopes)

        output_entries.append(
            {
                "country":
                    country,
                "country_name":
                    intake_entry[
                        "country_name"
                    ],
                "canonical_treaty_source": {
                    "source_id":
                        canonical[
                            "source_id"
                        ],
                    "source_title":
                        canonical[
                            "source_title"
                        ],
                    "parsed_path":
                        canonical[
                            "parsed_path"
                        ],
                    "parsed_sha256":
                        sha256(
                            parsed_path
                        ),
                    "artifact_uri":
                        canonical[
                            "artifact_uri"
                        ],
                    "artifact_sha256":
                        canonical[
                            "artifact_sha256"
                        ],
                    "authority_class":
                        canonical[
                            "authority_class"
                        ],
                    "official_urls":
                        canonical[
                            "official_urls"
                        ],
                },
                "base_instruments":
                    partner.get(
                        "base_instruments"
                    )
                    or [],
                "related_instrument_chain":
                    instruments,
                "legacy_remaining294_reference": {
                    "reference_only":
                        True,
                    "matched_nodes":
                        legacy_nodes,
                },
                "article_evidence":
                    article_map,
                "mli_layer":
                    mli_status,
                "language_authority_evidence":
                    language_evidence,
                "effective_date_evidence":
                    effective_date_evidence,
                "country_level_gaps":
                    sorted(
                        set(country_gaps)
                    ),
                "verification_status":
                    "needs_review",
                "stage5_terminal_status":
                    "pending",
                "production_releasable":
                    False,
                "human_primary_review_complete":
                    False,
                "independent_approval_complete":
                    False,
                "scopes":
                    scopes,
            }
        )

    if total_scopes != 30:
        raise RuntimeError(
            f"Expected 30 scopes, found {total_scopes}"
        )

    gap_counts: dict[str, int] = {}

    for entry in output_entries:

        for gap in entry[
            "country_level_gaps"
        ]:

            gap_counts[gap] = (
                gap_counts.get(
                    gap,
                    0,
                )
                + 1
            )

        for scope in entry["scopes"]:

            for gap in scope[
                "legal_chain_gaps"
            ]:

                gap_counts[gap] = (
                    gap_counts.get(
                        gap,
                        0,
                    )
                    + 1
                )

    dossier = {
        "schema_version": 1,
        "dataset_release":
            "stage5-remaining80-batch01-legal-chain-2026-08-09.1",
        "purpose": (
            "Review-only legal-chain dossier for Stage 5 "
            "remaining80 Batch 01. It assembles repository-backed "
            "evidence for treaty dividend, interest, and royalty "
            "articles, related instruments, "
            "MLI status, domestic/EU references, language and "
            "effective-date evidence. It does not create a verified "
            "or production legal conclusion."
        ),
        "batch": {
            "countries":
                countries,
            "country_count":
                len(output_entries),
            "scope_count":
                total_scopes,
        },
        "source_hashes": {
            str(
                INTAKE.relative_to(
                    ROOT
                )
            ):
                sha256(INTAKE),
            str(
                MLI_EVIDENCE.relative_to(
                    ROOT
                )
            ):
                sha256(MLI_EVIDENCE),
            str(
                MF_INVENTORY.relative_to(
                    ROOT
                )
            ):
                sha256(MF_INVENTORY),
            str(
                SOURCE_MANIFEST.relative_to(
                    ROOT
                )
            ):
                sha256(SOURCE_MANIFEST),
            str(
                LEGACY_CHAINS.relative_to(
                    ROOT
                )
            ):
                sha256(LEGACY_CHAINS),
            str(
                DOMESTIC_EU.relative_to(
                    ROOT
                )
            ):
                sha256(DOMESTIC_EU),
        },
        "safety_boundary": {
            "official_source_is_authority":
                True,
            "parsed_extraction_is_not_verification":
                True,
            "legacy_remaining294_is_reference_only":
                True,
            "candidate_is_not_production_rule":
                True,
            "no_rate_or_legal_conclusion_generated":
                True,
            "human_primary_review_required":
                True,
            "independent_approval_required":
                True,
        },
        "article_resolution_summary": {
            "possible_country_articles":
                30,
            "resolved_country_articles":
                resolved_articles,
            "unresolved_country_articles":
                30 - resolved_articles,
        },
        "terminal_status_counts": {
            "verified": 0,
            "blocked": 0,
            "pending": 30,
        },
        "production_releasable_scope_count":
            0,
        "gap_counts":
            dict(
                sorted(
                    gap_counts.items()
                )
            ),
        "entries":
            output_entries,
    }

    OUTPUT.write_text(
        json.dumps(
            dossier,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "Stage 5 Batch 01 legal-chain dossier generated."
    )

    print(
        "Countries:",
        ", ".join(countries),
    )

    print(
        "Country count:",
        len(output_entries),
    )

    print(
        "Scope count:",
        total_scopes,
    )

    print(
        "Article locations resolved:",
        f"{resolved_articles}/30",
    )

    print(
        "Terminal:",
        "0 verified / 0 blocked / 30 pending",
    )

    print(
        "Production releasable:",
        0,
    )

    print()
    print("Gap summary:")

    if not gap_counts:
        print(
            "  none at automated evidence-assembly level"
        )

    else:

        for key, count in sorted(
            gap_counts.items(),
            key=lambda item: (
                -item[1],
                item[0],
            ),
        ):

            print(
                f"  {key}: {count}"
            )


if __name__ == "__main__":
    main()
