from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

MANIFEST = (
    ROOT
    / "data/legal_consolidation/"
    "stage5_execution_manifest.json"
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

MLI_EFFECTS = (
    ROOT
    / "data/legal_consolidation/"
    "mli_wht_effects.json"
)

OUTPUT = (
    ROOT
    / "data/legal_reviews/global_cz_outbound/"
    "stage5_remaining80_batch_01_intake.json"
)

INCOMES = (
    "dividend",
    "interest",
    "royalty",
)

COUNTRY_KEYS = {
    "recipient_country",
    "recipient_country_code",
    "partner_country",
    "partner_country_code",
    "treaty_partner",
    "treaty_partner_code",
    "jurisdiction",
    "jurisdiction_code",
    "iso2",
}

INCOME_KEYS = {
    "income_type",
    "payment_type",
    "transaction_type",
    "income",
}

INCOME_NORMALIZE = {
    "dividend": "dividend",
    "dividends": "dividend",
    "interest": "interest",
    "royalty": "royalty",
    "royalties": "royalty",
}


def load(path: Path) -> Any:
    if not path.is_file():
        raise RuntimeError(
            f"Required file missing: {path.relative_to(ROOT)}"
        )

    try:
        return json.loads(
            path.read_text(encoding="utf-8")
        )
    except Exception as exc:
        raise RuntimeError(
            f"Invalid JSON: {path.relative_to(ROOT)}: {exc}"
        ) from exc


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""

    text = unicodedata.normalize("NFKD", value)

    text = "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )

    text = text.casefold()

    text = re.sub(
        r"[^a-z0-9]+",
        "",
        text,
    )

    return text


def normalize_instrument_label(value: Any) -> str:
    return normalize_text(value)


def walk_dicts(value: Any):
    if isinstance(value, dict):
        yield value

        for item in value.values():
            yield from walk_dicts(item)

    elif isinstance(value, list):
        for item in value:
            yield from walk_dicts(item)


def walk_strings(value: Any):
    if isinstance(value, str):
        yield value

    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from walk_strings(item)

    elif isinstance(value, list):
        for item in value:
            yield from walk_strings(item)


def normalize_country(value: Any) -> str | None:
    if not isinstance(value, str):
        return None

    text = value.strip().upper()

    if re.fullmatch(r"[A-Z]{2}", text):
        return text

    return None


def normalize_income(value: Any) -> str | None:
    if not isinstance(value, str):
        return None

    return INCOME_NORMALIZE.get(
        value.strip().lower()
    )


def dict_country(node: dict[str, Any]) -> str | None:
    for key in COUNTRY_KEYS:
        if key not in node:
            continue

        code = normalize_country(node[key])

        if code:
            return code

    return None


def dict_income(node: dict[str, Any]) -> str | None:
    for key in INCOME_KEYS:
        if key not in node:
            continue

        income = normalize_income(node[key])

        if income:
            return income

    return None


def scope_present(
    payload: Any,
    country: str,
    income: str,
) -> bool:

    expected = f"CZ-{country}-{income}".lower()

    for text in walk_strings(payload):
        if text.strip().lower() == expected:
            return True

    for node in walk_dicts(payload):
        if (
            dict_country(node) == country
            and dict_income(node) == income
        ):
            return True

    return False


def base_labels(
    partner: dict[str, Any],
) -> set[str]:

    result = set()

    for instrument in (
        partner.get("base_instruments") or []
    ):
        if not isinstance(instrument, dict):
            continue

        label = normalize_instrument_label(
            instrument.get("label")
        )

        if label:
            result.add(label)

    return result


def resolve_source_manifest_row(
    partner: dict[str, Any],
    sources: list[dict[str, Any]],
) -> tuple[dict[str, Any], str]:

    partner_country = normalize_text(
        partner.get("country")
    )

    labels = base_labels(partner)

    title_matches = []

    for source in sources:
        source_title = normalize_instrument_label(
            source.get("source_title")
        )

        if source_title and source_title in labels:
            title_matches.append(source)

    if len(title_matches) == 1:
        return (
            title_matches[0],
            "base_instrument_title",
        )

    country_matches = [
        source
        for source in sources
        if normalize_text(source.get("country"))
        == partner_country
        and partner_country
    ]

    if len(country_matches) == 1:
        return (
            country_matches[0],
            "country_identity",
        )

    if title_matches and country_matches:
        intersection = [
            source
            for source in title_matches
            if source in country_matches
        ]

        if len(intersection) == 1:
            return (
                intersection[0],
                "base_title_and_country_identity",
            )

    diagnostics = {
        "country": partner.get("country"),
        "iso2": partner.get("iso2"),
        "base_labels": sorted(labels),
        "title_match_count": len(title_matches),
        "country_match_count": len(country_matches),
        "title_match_countries": [
            row.get("country")
            for row in title_matches
        ],
        "country_match_titles": [
            row.get("source_title")
            for row in country_matches
        ],
    }

    raise RuntimeError(
        "Cannot deterministically resolve canonical source "
        f"manifest row: {diagnostics}"
    )


def validate_source_manifest_row(
    source: dict[str, Any],
) -> dict[str, Any]:

    parsed_value = source.get("parsed_path")
    artifact_value = source.get("artifact_uri")

    if not isinstance(parsed_value, str):
        raise RuntimeError(
            "Source manifest row lacks parsed_path"
        )

    if not isinstance(artifact_value, str):
        raise RuntimeError(
            "Source manifest row lacks artifact_uri"
        )

    parsed_path = ROOT / parsed_value
    artifact_path = ROOT / artifact_value

    if not parsed_path.is_file():
        raise RuntimeError(
            f"Canonical parsed source missing: {parsed_value}"
        )

    if not artifact_path.is_file():
        raise RuntimeError(
            f"Canonical raw artifact missing: {artifact_value}"
        )

    if source.get("artifact_available") is not True:
        raise RuntimeError(
            "Source manifest does not mark artifact available: "
            f"{source.get('source_id')}"
        )

    expected_raw_hash = source.get("sha256")

    if not isinstance(expected_raw_hash, str):
        raise RuntimeError(
            "Source manifest lacks raw artifact SHA-256"
        )

    observed_raw_hash = digest(artifact_path)

    if observed_raw_hash != expected_raw_hash:
        raise RuntimeError(
            "Raw official-source artifact hash mismatch: "
            f"{artifact_value}"
        )

    return {
        "path": parsed_value,
        "parsed_sha256": digest(parsed_path),
        "artifact_uri": artifact_value,
        "artifact_sha256": observed_raw_hash,
    }


def source_types(
    partner: dict[str, Any],
) -> list[str]:

    values = {"base_treaty"}

    for item in (
        partner.get("related_instruments") or []
    ):
        if not isinstance(item, dict):
            continue

        value = item.get("source_type")

        if value is not None:
            values.add(str(value))

    return sorted(values)


def has_mli_effect_reference(
    payload: Any,
    country: str,
) -> bool:

    token = f"CZ-{country}-MLI-".upper()

    return any(
        token in text.upper()
        for text in walk_strings(payload)
    )


def main() -> None:

    execution = load(MANIFEST)
    inventory = load(MF_INVENTORY)
    source_manifest = load(SOURCE_MANIFEST)
    legacy = load(LEGACY_CHAINS)
    domestic_eu = load(DOMESTIC_EU)

    mli_effects = (
        load(MLI_EFFECTS)
        if MLI_EFFECTS.is_file()
        else None
    )

    batches = execution.get(
        "remaining80_work_batches"
    )

    if not isinstance(batches, list):
        raise RuntimeError(
            "Execution manifest lacks remaining80 batches"
        )

    if len(batches) != 8:
        raise RuntimeError(
            "Expected eight remaining80 batches"
        )

    batch = batches[0]
    countries = batch.get("countries")

    if (
        not isinstance(countries, list)
        or len(countries) != 10
        or len(set(countries)) != 10
    ):
        raise RuntimeError(
            "Batch 01 must contain 10 unique countries"
        )

    remaining80 = set(
        execution["cohorts"]["remaining80"]["countries"]
    )

    if not set(countries) <= remaining80:
        raise RuntimeError(
            "Batch 01 contains country outside remaining80"
        )

    partners = inventory.get("partners")

    if not isinstance(partners, list):
        raise RuntimeError(
            "MF inventory lacks partners list"
        )

    partner_index = {
        str(row.get("iso2", "")).upper(): row
        for row in partners
        if isinstance(row, dict)
    }

    missing = [
        code
        for code in countries
        if code not in partner_index
    ]

    if missing:
        raise RuntimeError(
            f"Batch countries missing from MF inventory: {missing}"
        )

    sources = source_manifest.get("sources")

    if not isinstance(sources, list):
        raise RuntimeError(
            "source_manifest.json lacks sources list"
        )

    sources = [
        row
        for row in sources
        if isinstance(row, dict)
    ]

    source_dataset_hashes = {
        str(MANIFEST.relative_to(ROOT)):
            digest(MANIFEST),
        str(MF_INVENTORY.relative_to(ROOT)):
            digest(MF_INVENTORY),
        str(SOURCE_MANIFEST.relative_to(ROOT)):
            digest(SOURCE_MANIFEST),
        str(LEGACY_CHAINS.relative_to(ROOT)):
            digest(LEGACY_CHAINS),
        str(DOMESTIC_EU.relative_to(ROOT)):
            digest(DOMESTIC_EU),
    }

    if MLI_EFFECTS.is_file():
        source_dataset_hashes[
            str(MLI_EFFECTS.relative_to(ROOT))
        ] = digest(MLI_EFFECTS)

    operational = {
        row["country"]: row
        for row in execution[
            "remaining80_operational_inventory"
        ]
    }

    entries = []

    for code in countries:

        partner = partner_index[code]

        source, resolution_method = (
            resolve_source_manifest_row(
                partner,
                sources,
            )
        )

        resolved_files = (
            validate_source_manifest_row(source)
        )

        evidence_gaps: list[str] = []

        if source.get("identity_status") != "validated":
            evidence_gaps.append(
                "source_identity_not_validated"
            )

        if source.get("authority_class") != "official":
            evidence_gaps.append(
                "source_authority_not_official"
            )

        if (
            partner.get("mli_listed") is True
            and partner.get(
                "mli_notice_available"
            ) is not True
        ):
            evidence_gaps.append(
                "mf_inventory_mli_notice_not_available"
            )

        mli_reference = None

        if mli_effects is not None:
            mli_reference = (
                has_mli_effect_reference(
                    mli_effects,
                    code,
                )
            )

            if (
                partner.get("mli_listed") is True
                and mli_reference is False
            ):
                evidence_gaps.append(
                    "mli_effect_reference_not_found"
                )

        scopes = []

        for income in INCOMES:

            legacy_present = scope_present(
                legacy,
                code,
                income,
            )

            domestic_present = scope_present(
                domestic_eu,
                code,
                income,
            )

            scope_gaps = []

            if not legacy_present:
                scope_gaps.append(
                    "legacy_frozen_scope_reference_not_found"
                )

            if not domestic_present:
                scope_gaps.append(
                    "domestic_eu_candidate_reference_not_found"
                )

            scopes.append(
                {
                    "scope_id": (
                        f"CZ-{code}-{income}"
                    ),
                    "source_country": "CZ",
                    "recipient_country": code,
                    "income_type": income,
                    "legacy_remaining_294_reference_present":
                        legacy_present,
                    "domestic_eu_candidate_reference_present":
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
                    "intake_evidence_gaps":
                        scope_gaps,
                }
            )

        entries.append(
            {
                "country": code,
                "country_name":
                    partner.get("country"),
                "workflow_class":
                    operational[code][
                        "workflow_class"
                    ],
                "official_instrument_inventory": {
                    "dataset":
                        str(
                            MF_INVENTORY.relative_to(
                                ROOT
                            )
                        ),
                    "inventory_status":
                        partner.get(
                            "inventory_status"
                        ),
                    "entry_into_force":
                        partner.get(
                            "entry_into_force"
                        ),
                    "protocol_listed":
                        bool(
                            partner.get(
                                "protocol_listed"
                            )
                        ),
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
                    "base_instruments":
                        partner.get(
                            "base_instruments"
                        )
                        or [],
                    "related_instruments":
                        partner.get(
                            "related_instruments"
                        )
                        or [],
                    "source_types":
                        source_types(partner),
                },
                "canonical_base_treaty_source": {
                    "resolution_status":
                        "resolved_via_source_manifest",
                    "resolution_method":
                        resolution_method,
                    "source_manifest_dataset":
                        str(
                            SOURCE_MANIFEST.relative_to(
                                ROOT
                            )
                        ),
                    "source_manifest_country":
                        source.get("country"),
                    "source_id":
                        source.get("source_id"),
                    "source_title":
                        source.get("source_title"),
                    "identity_status":
                        source.get(
                            "identity_status"
                        ),
                    "identity_warnings":
                        source.get(
                            "identity_warnings"
                        )
                        or [],
                    "authority_class":
                        source.get(
                            "authority_class"
                        ),
                    "extraction_authority_class":
                        source.get(
                            "extraction_authority_class"
                        ),
                    "official_urls":
                        source.get(
                            "official_urls"
                        )
                        or [],
                    "parsed_path":
                        resolved_files["path"],
                    "parsed_sha256":
                        resolved_files[
                            "parsed_sha256"
                        ],
                    "artifact_uri":
                        resolved_files[
                            "artifact_uri"
                        ],
                    "artifact_sha256":
                        resolved_files[
                            "artifact_sha256"
                        ],
                },
                "mli_effect_reference_present":
                    mli_reference,
                "intake_evidence_gaps":
                    sorted(
                        set(evidence_gaps)
                    ),
                "stage5_required_legal_gates": [
                    "official_treaty_identity",
                    "official_treaty_document",
                    "article_10",
                    "article_11",
                    "article_12",
                    "protocols_and_amendments",
                    "mli_position",
                    "mli_matching",
                    "mli_effective_dates",
                    "authentic_languages",
                    "prevailing_language_rule",
                    "official_english_version_if_relevant",
                    "withholding_effective_date",
                    "czech_domestic_law_layer",
                    "eu_directive_layer_if_relevant",
                    "structured_rule_mapping",
                    "exact_evidence_and_provenance",
                    "human_primary_legal_review",
                    "independent_approval_before_release",
                ],
                "stage5_release_status":
                    "needs_review",
                "production_releasable":
                    False,
                "scopes":
                    scopes,
            }
        )

    all_scopes = [
        scope
        for entry in entries
        for scope in entry["scopes"]
    ]

    if len(entries) != 10:
        raise RuntimeError(
            "Expected exactly 10 country entries"
        )

    if len(all_scopes) != 30:
        raise RuntimeError(
            "Expected exactly 30 scope entries"
        )

    unresolved = [
        entry["country"]
        for entry in entries
        if entry[
            "canonical_base_treaty_source"
        ]["resolution_status"]
        != "resolved_via_source_manifest"
    ]

    if unresolved:
        raise RuntimeError(
            "Canonical parsed evidence unresolved for: "
            f"{unresolved}"
        )

    output = {
        "schema_version": 2,
        "dataset_release":
            "stage5-remaining80-batch01-intake-2026-08-09.2",
        "purpose": (
            "Stage 5 evidence-intake dossier for the first "
            "remaining80 batch. Repository-backed source "
            "identity and evidence availability only. "
            "This dataset is not legal approval and does "
            "not create a production legal conclusion."
        ),
        "safety_boundary": {
            "official_source_is_authority":
                True,
            "extraction_is_not_verification":
                True,
            "provenance_is_not_approval":
                True,
            "legacy_remaining_294_is_frozen_reference_only":
                True,
            "candidate_is_not_production_rule":
                True,
            "human_review_required":
                True,
            "independent_approval_required_before_release":
                True,
            "production_release_created_by_this_dataset":
                False,
        },
        "batch": {
            "batch_id":
                batch["batch_id"],
            "countries":
                countries,
            "country_count":
                10,
            "scope_count":
                30,
        },
        "source_dataset_hashes":
            source_dataset_hashes,
        "terminal_status_counts": {
            "verified": 0,
            "blocked": 0,
            "pending": 30,
        },
        "production_releasable_scope_count":
            0,
        "canonical_base_treaty_source_resolution": {
            "resolved": 10,
            "unresolved": 0,
        },
        "entries":
            entries,
    }

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT.write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "Stage 5 remaining80 Batch 01 intake "
        "generated successfully."
    )

    print(
        "Countries:",
        ", ".join(countries),
    )

    print("Country count:", len(entries))
    print("Scope count:", len(all_scopes))

    print(
        "Canonical parsed sources:",
        "10/10 resolved",
    )

    print(
        "Terminal:",
        "0 verified / 0 blocked / 30 pending",
    )

    print("Production releasable: 0")

    gap_counts: dict[str, int] = {}

    for entry in entries:

        for gap in entry[
            "intake_evidence_gaps"
        ]:
            gap_counts[gap] = (
                gap_counts.get(gap, 0) + 1
            )

        for scope in entry["scopes"]:
            for gap in scope[
                "intake_evidence_gaps"
            ]:
                gap_counts[gap] = (
                    gap_counts.get(gap, 0) + 1
                )

    print()
    print("Remaining evidence gaps:")

    if not gap_counts:
        print("  none at mechanical intake level")

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
