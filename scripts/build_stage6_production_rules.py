from __future__ import annotations

import hashlib
import itertools
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

# Allow direct execution as:
# python scripts/build_stage6_production_rules.py
# without relying on caller-specific PYTHONPATH.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BASE = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)

QUEUE = BASE / "cz_country_qa_queue.json"
APPROVAL = BASE / "stage6_production_approval.json"
READINESS = (
    BASE
    / "stage6_production_materialization_readiness.json"
)
GATE = BASE / "production_source_release_gate_v2.json"

REGISTRY = (
    ROOT
    / "data"
    / "registries"
    / "legal_evidence_sources.json"
)

OUTPUT_DIR = ROOT / "data" / "legal_rules_stage6"

PROMOTION = BASE / "stage6_rule_promotion.json"
SUMMARY = BASE / "stage6_rule_promotion_summary.json"

PILOT_AT = ROOT / "data/legal_rules/rakousko.json"
PILOT_CH = ROOT / "data/legal_rules/svycarsko.json"

INCOMES = ("dividend", "interest", "royalty")

DATASET_RELEASE = (
    "stage6-production-rules-2026-08-12.1"
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_hash(payload: dict[str, Any]) -> str:
    clone = dict(payload)
    clone.pop("package_sha256", None)

    encoded = json.dumps(
        clone,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def iso_date(value: Any) -> str | None:
    if not isinstance(value, str):
        return None

    if not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}",
        value,
    ):
        return None

    try:
        datetime.strptime(
            value,
            "%Y-%m-%d",
        )
    except ValueError:
        return None

    return value


def normalize_condition(
    raw: dict[str, Any],
) -> dict[str, Any]:
    fact = (
        raw.get("fact")
        or raw.get("condition_type")
    )

    if not fact:
        raise RuntimeError(
            f"Condition missing fact: {raw}"
        )

    operator = raw.get("operator")

    if operator not in {
        "==",
        "!=",
        ">=",
        ">",
        "<=",
        "<",
        "in",
        "not in",
    }:
        raise RuntimeError(
            f"Unsupported condition operator: {raw}"
        )

    source = raw.get(
        "fact_source",
        "transaction",
    )

    if source not in {
        "transaction",
        "legal",
        "determination",
    }:
        source = "transaction"

    return {
        "fact": fact,
        "operator": operator,
        "value": raw.get("value"),
        "fact_source": source,
    }


def normalize_condition_list(
    raw: Any,
) -> list[dict[str, Any]]:
    if raw is None:
        return []

    if isinstance(raw, dict):
        return [
            normalize_condition(raw)
        ]

    if not isinstance(raw, list):
        raise RuntimeError(
            f"Unexpected condition structure: {raw}"
        )

    result: list[dict[str, Any]] = []

    for node in raw:
        if isinstance(node, dict):
            result.append(
                normalize_condition(node)
            )
        else:
            raise RuntimeError(
                f"Unexpected condition node: {node}"
            )

    return result


def normalize_one_of_option(
    option: Any,
) -> list[dict[str, Any]]:
    if isinstance(option, dict):
        # A one-of alternative may itself be a grouped
        # all-of branch. Preserve it as a conjunction.
        if "all_of" in option:
            if set(option) != {"all_of"}:
                raise RuntimeError(
                    "Nested one-of all_of branch contains "
                    f"unexpected sibling keys: {option}"
                )

            return normalize_condition_list(
                option["all_of"]
            )

        return normalize_condition_list(
            option
        )

    if isinstance(option, list):
        return normalize_condition_list(
            option
        )

    if isinstance(option, str):
        # The approved IRD projection contains exactly three
        # human-readable association alternatives. They are
        # legal determinations rather than raw numeric
        # transaction facts. Represent them explicitly as
        # determination booleans so absence of a confirmed
        # determination remains fail-closed.
        association_map = {
            (
                "payer directly holds at least 25% of "
                "recipient capital or voting rights"
            ): (
                "ird_association_payer_directly_holds_"
                "25_percent_recipient"
            ),
            (
                "recipient directly holds at least 25% of "
                "payer capital or voting rights"
            ): (
                "ird_association_recipient_directly_holds_"
                "25_percent_payer"
            ),
            (
                "one person directly holds at least 25% of "
                "both payer and recipient capital or voting rights"
            ): (
                "ird_association_common_person_directly_holds_"
                "25_percent_both"
            ),
        }

        fact = association_map.get(option)

        if fact is None:
            raise RuntimeError(
                "Unmapped prose one-of option: "
                f"{option}"
            )

        return [
            {
                "fact": fact,
                "operator": "==",
                "value": True,
                "fact_source": "determination",
            }
        ]

    raise RuntimeError(
        f"Unexpected one-of option: {option}"
    )


def expand_eu_conditions(
    candidate: dict[str, Any],
) -> list[list[dict[str, Any]]]:
    base = normalize_condition_list(
        candidate.get("all_of") or []
    )

    groups: list[
        list[list[dict[str, Any]]]
    ] = []

    for key in (
        "holding_period_one_of",
        "association_one_of",
        "association_period_one_of",
    ):
        raw = candidate.get(key)

        if raw in (None, [], {}):
            continue

        if not isinstance(raw, list):
            raise RuntimeError(
                f"{key} must be a list."
            )

        options = [
            normalize_one_of_option(option)
            for option in raw
        ]

        if not options:
            raise RuntimeError(
                f"{key} has no alternatives."
            )

        groups.append(options)

    if not groups:
        return [base]

    expanded = []

    for combination in itertools.product(
        *groups
    ):
        merged = list(base)

        for option_conditions in combination:
            merged.extend(
                option_conditions
            )

        expanded.append(merged)

    return expanded


queue = read_json(QUEUE)
approval = read_json(APPROVAL)
readiness = read_json(READINESS)
gate = read_json(GATE)
registry = read_json(REGISTRY)

packages = queue["packages"]

approval_by_pair = {
    row["treaty_pair_id"]: row
    for row in approval["records"]
}

readiness_by_pair = {
    row["treaty_pair_id"]: row
    for row in readiness["records"]
}

gate_by_pair = {
    row["treaty_pair_id"]: row
    for row in gate["treaty_partners"]
}

source_registry = {
    row["source_id"]: row
    for row in registry["sources"]
}

if len(packages) != 101:
    raise RuntimeError(
        f"Expected 101 packages, got {len(packages)}."
    )

if sum(
    len(row["income_scopes"])
    for row in packages
) != 303:
    raise RuntimeError(
        "Expected exactly 303 WHT scopes."
    )

if approval["counts"][
    "production_approved_packages"
] != 101:
    raise RuntimeError(
        "Production approval is not 101/101."
    )

if readiness["counts"][
    "materialization_ready_packages"
] != 101:
    raise RuntimeError(
        "Readiness is not 101/101."
    )

if gate["counts"][
    "rule_promoted_packages"
] != 0:
    raise RuntimeError(
        "Canonical gate unexpectedly already promoted."
    )

if gate["counts"]["released_packages"] != 0:
    raise RuntimeError(
        "Canonical gate unexpectedly released."
    )

approval_created_at = (
    approval["created_at"]
    .replace("Z", "+00:00")
)

approval_date = (
    datetime.fromisoformat(
        approval_created_at
    )
    .date()
    .isoformat()
)

approval_release = approval[
    "dataset_release"
]


def registry_url(
    source_id: str | None,
) -> str | None:
    if not source_id:
        return None

    row = source_registry.get(
        source_id
    )

    if not row:
        return None

    urls = row.get(
        "official_urls"
    ) or []

    for url in urls:
        if (
            isinstance(url, str)
            and url.startswith("https://")
        ):
            return url

    return None


def base_source(
    package: dict[str, Any],
) -> tuple[str, str]:
    base = package["base_treaty"]

    source_id = base.get("source_id")

    if not source_id:
        raise RuntimeError(
            f"{package['treaty_pair_id']}: "
            "base treaty source_id missing."
        )

    urls = base.get(
        "official_urls"
    ) or []

    url = next(
        (
            value
            for value in urls
            if isinstance(value, str)
            and value.startswith("https://")
        ),
        None,
    )

    if url is None:
        url = registry_url(
            source_id
        )

    if url is None:
        raise RuntimeError(
            f"{package['treaty_pair_id']}: "
            "base treaty official URL missing."
        )

    return source_id, url


def domestic_source(
    package: dict[str, Any],
) -> tuple[str, str]:
    domestic = package[
        "czech_domestic_wht"
    ]

    source_id = domestic.get(
        "source_id"
    )

    if not source_id:
        raise RuntimeError(
            f"{package['treaty_pair_id']}: "
            "domestic source_id missing."
        )

    url = registry_url(
        source_id
    )

    # Canonical Czech source used by the
    # already-existing pilot dataset.
    if url is None:
        url = (
            "https://opendata.eselpoint.gov.cz/"
            "esel-esb/eli/cz/sb/1992/586/"
            "2026-04-01"
        )

    return source_id, url


def recursively_find_dates(
    node: Any,
    *,
    include_terms: tuple[str, ...],
    exclude_terms: tuple[str, ...] = (),
) -> list[str]:
    found: set[str] = set()

    def walk(
        value: Any,
        path: str = "",
    ) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = (
                    f"{path}.{key}"
                    if path
                    else key
                )

                low = child_path.lower()

                date_value = iso_date(
                    child
                )

                if (
                    date_value
                    and any(
                        term in low
                        for term
                        in include_terms
                    )
                    and not any(
                        term in low
                        for term
                        in exclude_terms
                    )
                ):
                    found.add(
                        date_value
                    )

                walk(
                    child,
                    child_path,
                )

        elif isinstance(value, list):
            for index, child in enumerate(
                value
            ):
                walk(
                    child,
                    f"{path}[{index}]",
                )

    walk(node)

    return sorted(found)


def treaty_effective_from(
    package: dict[str, Any],
) -> str:
    base = package.get(
        "base_treaty"
    ) or {}

    # Prefer an explicit WHT/application
    # effective date in the base instrument.
    dates = recursively_find_dates(
        base,
        include_terms=(
            "effective",
            "application",
            "applicable",
        ),
        exclude_terms=(
            "protocol",
            "mli",
        ),
    )

    if len(dates) == 1:
        return dates[0]

    evidence = package.get(
        "effective_date_evidence"
    ) or {}

    dates = recursively_find_dates(
        evidence,
        include_terms=(
            "wht",
            "withholding",
            "effective",
            "application",
        ),
        exclude_terms=(
            "protocol",
            "mli",
        ),
    )

    if len(dates) == 1:
        return dates[0]

    # Entry-into-force evidence is accepted
    # only where it is uniquely represented.
    dates = recursively_find_dates(
        {
            "base_treaty": base,
            "effective_date_evidence":
                evidence,
        },
        include_terms=(
            "entry_into_force",
            "entry-into-force",
        ),
        exclude_terms=(
            "protocol",
            "mli",
        ),
    )

    if len(dates) == 1:
        return dates[0]

    raise RuntimeError(
        f"{package['treaty_pair_id']}: "
        "cannot derive one unambiguous base "
        f"treaty effective date; candidates={dates}"
    )


def protocol_info(
    package: dict[str, Any],
) -> dict[str, Any]:
    chain = package.get(
        "current_instrument_chain"
    ) or {}

    protocol = (
        chain.get("protocol")
        or {}
    )

    effect = (
        protocol.get("candidate_effect")
        or {}
    )

    return effect


def protocol_applies_to_scope(
    package: dict[str, Any],
    scope: dict[str, Any],
) -> bool:
    effect = protocol_info(
        package
    )

    if effect.get("required") is not True:
        return False

    article = str(
        scope["article_number"]
    )

    serialized = json.dumps(
        effect,
        ensure_ascii=False,
        sort_keys=True,
    )

    # If the approved package explicitly
    # identifies affected articles/scopes,
    # use that exact mapping.
    for key in (
        "affected_articles",
        "articles",
        "article_numbers",
        "wht_articles",
    ):
        values = effect.get(key)

        if isinstance(values, list):
            normalized = {
                str(value)
                for value in values
            }

            return article in normalized

    for key in (
        "affected_income_types",
        "income_types",
    ):
        values = effect.get(key)

        if isinstance(values, list):
            return (
                scope["income_type"]
                in values
            )

    # A protocol explicitly required for the
    # approved current instrument chain but
    # without machine-readable scope mapping
    # is not silently applied to all scopes.
    # The consolidated treaty result remains
    # a treaty rule and protocol provenance is
    # retained separately in the package hash.
    return False


def protocol_effective_from(
    package: dict[str, Any],
    income: str,
) -> str:
    effect = protocol_info(
        package
    )

    dates = recursively_find_dates(
        effect,
        include_terms=(
            "effective",
            "application",
            "applicable",
            "wht",
        ),
    )

    if len(dates) == 1:
        return dates[0]

    evidence = package.get(
        "effective_date_evidence"
    ) or {}

    dates = recursively_find_dates(
        evidence,
        include_terms=(
            "protocol",
        ),
    )

    if len(dates) == 1:
        return dates[0]

    # Preserved pilot evidence is used only
    # for CZ-CH where the approved package
    # intentionally lacks the generic field.
    if package[
        "treaty_pair_id"
    ] == "CZ-CH":
        pilot = read_json(
            PILOT_CH
        )

        pilot_dates = {
            row.get("effective_from")
            for row in pilot["rules"]
            if row.get(
                "income_type"
            ) == income
            and row.get(
                "legal_instrument"
            ) == "protocol"
            and row.get(
                "effective_from"
            )
        }

        if len(pilot_dates) == 1:
            return next(
                iter(pilot_dates)
            )

    raise RuntimeError(
        f"{package['treaty_pair_id']}/{income}: "
        "protocol applies but effective date "
        f"is not uniquely evidenced: {dates}"
    )


def priority_for_conditions(
    conditions: list[dict[str, Any]],
    index: int,
    base: int,
) -> int:
    specificity = min(
        len(conditions),
        20,
    )

    return (
        base
        - specificity * 10
        + index
    )


def stage6_metadata(
    package: dict[str, Any],
) -> dict[str, Any]:
    return {
        "verification_status":
            "verified",
        "verification_authority":
            "stage6_governance_policy",
        "review_package_sha256":
            package["package_sha256"],
        "approval_dataset_release":
            approval_release,
        "approval_created_at":
            approval_date,
        "dataset_release":
            DATASET_RELEASE,
    }


def make_domestic_rule(
    package: dict[str, Any],
    income: str,
) -> dict[str, Any]:
    domestic = package[
        "czech_domestic_wht"
    ]

    source_id, source_url = (
        domestic_source(package)
    )

    rate = domestic[
        "standard_rate"
    ]

    effective_from = domestic[
        "effective_from"
    ]

    text = (
        "Current Czech domestic withholding "
        f"tax standard rate represented in the "
        f"approved Stage 6 package: {rate}%."
    )

    paragraph = (
        "1(b)(1)"
        if income == "dividend"
        else "1(a)(1)"
    )

    return {
        "rule_id":
            f"{package['treaty_pair_id']}-"
            f"{income.upper()}-DOMESTIC",
        "income_type": income,
        "source_country": "CZ",
        "recipient_country":
            package["partner_country"],
        "legal_instrument":
            "domestic_law",
        "legal_layer":
            "domestic",
        "article": 36,
        "paragraph": paragraph,
        "rate": float(rate),
        "priority": 900,
        "conditions": [],
        "effect": "rate",
        "effective_from":
            effective_from,
        "source_id": source_id,
        "source_url": source_url,
        "source_text": text,
        "source_excerpt_hash":
            sha256_text(text),
        "evidence_source_ids": [
            source_id
        ],
        "source_representation":
            "approved_structured_projection",
        **stage6_metadata(package),
    }


def make_treaty_rules(
    package: dict[str, Any],
    scope: dict[str, Any],
) -> list[dict[str, Any]]:
    pair = package[
        "treaty_pair_id"
    ]
    income = scope[
        "income_type"
    ]

    nodes = scope.get(
        "material_conditions"
    ) or []

    rates = scope.get(
        "candidate_rates"
    ) or []

    # CZ-GR dividends intentionally contain
    # no numeric treaty cap. Do not invent one.
    if (
        pair == "CZ-GR"
        and income == "dividend"
    ):
        if rates or nodes:
            raise RuntimeError(
                "CZ-GR dividend unexpectedly "
                "contains numeric treaty rate."
            )

        return []

    if not nodes:
        raise RuntimeError(
            f"{pair}/{income}: "
            "material conditions missing."
        )

    source_id, source_url = (
        base_source(package)
    )

    article_hash = scope[
        "article_text_sha256"
    ]

    source_text = scope[
        "candidate_excerpt"
    ]

    if (
        not isinstance(source_text, str)
        or not source_text.strip()
    ):
        raise RuntimeError(
            f"{pair}/{income}: candidate excerpt missing."
        )

    if (
        not isinstance(article_hash, str)
        or not re.fullmatch(
            r"[0-9a-fA-F]{64}",
            article_hash,
        )
    ):
        raise RuntimeError(
            f"{pair}/{income}: approved article hash invalid."
        )

    # article_text_sha256 binds the reviewed full treaty
    # article. source_excerpt_hash must instead bind the
    # exact candidate_excerpt placed into LegalRule.source_text,
    # because the runtime validator explicitly verifies that
    # relationship.
    source_excerpt_hash = sha256_text(
        source_text
    )

    result = []

    for index, node in enumerate(
        nodes,
        start=1,
    ):
        rate = node.get("rate")

        if not isinstance(
            rate,
            (int, float),
        ):
            raise RuntimeError(
                f"{pair}/{income}: "
                "non-numeric treaty rate."
            )

        conditions = (
            normalize_condition_list(
                node.get("conditions")
                or []
            )
        )

        is_protocol = (
            protocol_applies_to_scope(
                package,
                scope,
            )
        )

        if is_protocol:
            instrument = "protocol"
            layer = "protocol"
            effective_from = (
                protocol_effective_from(
                    package,
                    income,
                )
            )
        else:
            instrument = "treaty"
            layer = "treaty"
            effective_from = (
                treaty_effective_from(
                    package
                )
            )

        result.append(
            {
                "rule_id":
                    f"{pair}-"
                    f"{income.upper()}-"
                    f"CURRENT-{index}",
                "income_type": income,
                "source_country": "CZ",
                "recipient_country":
                    package["partner_country"],
                "legal_instrument":
                    instrument,
                "legal_layer": layer,
                "article":
                    scope[
                        "article_number"
                    ],
                "paragraph": None,
                "rate": float(rate),
                "priority":
                    priority_for_conditions(
                        conditions,
                        index,
                        700,
                    ),
                "conditions":
                    conditions,
                "effect": "rate",
                "effective_from":
                    effective_from,
                "source_id":
                    source_id,
                "source_url":
                    source_url,
                "source_text":
                    source_text,
                "source_excerpt_hash":
                    source_excerpt_hash,
                "approved_article_text_sha256":
                    article_hash,
                "evidence_source_ids": [
                    source_id
                ],
                "source_representation":
                    "approved_treaty_excerpt",
                **stage6_metadata(
                    package
                ),
            }
        )

    return result


def make_eu_rules(
    package: dict[str, Any],
    income: str,
) -> list[dict[str, Any]]:
    interaction = (
        package.get(
            "eu_directive_interaction"
        )
        or {}
    ).get(income)

    if not isinstance(
        interaction,
        dict,
    ):
        return []

    if (
        interaction.get(
            "candidate_status"
        )
        != "relief_candidate_consolidated"
    ):
        return []

    candidate = interaction.get(
        "candidate"
    )

    if not isinstance(
        candidate,
        dict,
    ):
        raise RuntimeError(
            f"{package['treaty_pair_id']}/{income}: "
            "EU candidate missing."
        )

    rate = candidate.get(
        "rate"
    )

    if not isinstance(
        rate,
        (int, float),
    ):
        raise RuntimeError(
            f"{package['treaty_pair_id']}/{income}: "
            "EU rate missing."
        )

    directive_source_id = candidate.get(
        "directive_source_id"
    )

    explicit_source_id = (
        directive_source_id
        or candidate.get("source_id")
        or candidate.get("legal_source_id")
    )

    legal_reference = str(
        candidate.get("legal_reference")
        or ""
    ).strip()

    regime = str(
        candidate.get("regime")
        or ""
    ).strip()

    source_id = None
    source_url = None
    source_basis = None
    legal_instrument = None

    if explicit_source_id:
        source_id = explicit_source_id
        source_url = registry_url(
            source_id
        )

        if source_url is None:
            raise RuntimeError(
                f"{package['treaty_pair_id']}/{income}: "
                f"no official URL for explicit source "
                f"{source_id}."
            )

        source_basis = (
            "explicit_candidate_source"
        )

        legal_instrument = (
            "eu_directive"
            if directive_source_id
            else "domestic_law"
        )

    elif legal_reference.lower().startswith(
        "section "
    ):
        # The approved candidate directly cites a Czech
        # statutory provision. Bind it to the approved
        # Czech domestic-law source already carried by
        # the package. This covers domestic reliefs,
        # including reliefs represented inside the
        # consolidated EU-interaction structure.
        source_id, source_url = domestic_source(
            package
        )

        source_basis = (
            "approved_czech_statutory_reference"
        )

        legal_instrument = (
            "domestic_law"
        )

    elif "domestic" in regime.lower():
        source_id, source_url = domestic_source(
            package
        )

        source_basis = (
            "approved_czech_domestic_regime"
        )

        legal_instrument = (
            "domestic_law"
        )

    else:
        raise RuntimeError(
            f"{package['treaty_pair_id']}/{income}: "
            "relief candidate lacks an explicit official "
            "source and does not contain a machine-readable "
            "Czech statutory provenance basis. "
            f"legal_reference={legal_reference!r}, "
            f"regime={regime!r}"
        )

    branches = expand_eu_conditions(
        candidate
    )

    representation = json.dumps(
        candidate,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    # This is deliberately labelled as an
    # approved structured representation,
    # not as a verbatim directive quotation.
    representation_hash = (
        sha256_text(
            representation
        )
    )

    effective_from = (
        candidate.get(
            "effective_from"
        )
        or package[
            "czech_domestic_wht"
        ]["effective_from"]
    )

    if iso_date(
        effective_from
    ) is None:
        raise RuntimeError(
            f"{package['treaty_pair_id']}/{income}: "
            "EU relief effective_from invalid."
        )

    rules = []

    for index, conditions in enumerate(
        branches,
        start=1,
    ):
        rules.append(
            {
                "rule_id":
                    f"{package['treaty_pair_id']}-"
                    f"{income.upper()}-"
                    f"EU-RELIEF-{index}",
                "income_type": income,
                "source_country": "CZ",
                "recipient_country":
                    package[
                        "partner_country"
                    ],
                "legal_instrument":
                    legal_instrument,
                "legal_layer":
                    "eu_relief",
                "article":
                    candidate.get(
                        "legal_reference"
                    ),
                "paragraph": None,
                "rate": float(rate),
                "priority":
                    priority_for_conditions(
                        conditions,
                        index,
                        200,
                    ),
                "conditions":
                    conditions,
                "effect": "rate",
                "effective_from":
                    effective_from,
                "source_id":
                    source_id,
                "source_url":
                    source_url,
                "source_text":
                    representation,
                "source_excerpt_hash":
                    representation_hash,
                "evidence_source_ids": [
                    source_id
                ],
                "source_representation":
                    (
                        "approved_structured_"
                        "candidate_not_verbatim_quote"
                    ),
                "source_basis":
                    source_basis,
                "anti_abuse_review_required":
                    bool(
                        candidate.get(
                            "anti_abuse_review_required"
                        )
                    ),
                **stage6_metadata(
                    package
                ),
            }
        )

    return rules


# Fail closed before writing output.
preflight = []

for package in packages:
    pair = package[
        "treaty_pair_id"
    ]
    phash = package[
        "package_sha256"
    ]

    # package_sha256 is the canonical hash already produced
    # by the reviewed Stage 5/6 package pipeline. Do not
    # independently reconstruct it here using a different
    # JSON serialization contract. Production materialization
    # instead requires byte-for-byte equality of that canonical
    # hash across all downstream governance artifacts.
    approval_row = (
        approval_by_pair.get(pair)
    )
    readiness_row = (
        readiness_by_pair.get(pair)
    )
    gate_row = (
        gate_by_pair.get(pair)
    )

    if (
        approval_row is None
        or approval_row[
            "package_sha256"
        ] != phash
        or approval_row[
            "production_approval_status"
        ] != "production_approved"
    ):
        preflight.append(
            f"{pair}: approval binding failed"
        )

    if (
        readiness_row is None
        or readiness_row[
            "package_sha256"
        ] != phash
        or readiness_row[
            "materialization_ready"
        ] is not True
    ):
        preflight.append(
            f"{pair}: readiness binding failed"
        )

    if (
        gate_row is None
        or gate_row[
            "package_sha256"
        ] != phash
        or gate_row[
            "production_approval_status"
        ] != "production_approved"
        or gate_row[
            "rule_promotion_status"
        ] != "not_promoted"
        or gate_row[
            "release_status"
        ] != "blocked"
    ):
        preflight.append(
            f"{pair}: canonical gate binding failed"
        )

if preflight:
    raise RuntimeError(
        "PRE-FLIGHT FAILED:\n"
        + "\n".join(preflight)
    )


tmp_dir = (
    ROOT
    / "data"
    / ".legal_rules_stage6_tmp"
)

if tmp_dir.exists():
    shutil.rmtree(tmp_dir)

tmp_dir.mkdir(
    parents=True
)

records = []
scope_keys = set()
total_rules = 0

for package in sorted(
    packages,
    key=lambda row:
        row["treaty_pair_id"],
):
    pair = package[
        "treaty_pair_id"
    ]
    country = package[
        "partner_country"
    ]

    scopes = {
        row["income_type"]: row
        for row
        in package["income_scopes"]
    }

    if set(scopes) != set(
        INCOMES
    ):
        raise RuntimeError(
            f"{pair}: incomplete 3-scope universe."
        )

    rules = []

    for income in INCOMES:
        scope_keys.add(
            (pair, income)
        )

        rules.append(
            make_domestic_rule(
                package,
                income,
            )
        )

        rules.extend(
            make_treaty_rules(
                package,
                scopes[income],
            )
        )

        rules.extend(
            make_eu_rules(
                package,
                income,
            )
        )

    payload = {
        "schema_version": 3,
        "country_pair": {
            "source_country": "CZ",
            "recipient_country":
                country,
        },
        "stage6_production": {
            "treaty_pair_id": pair,
            "package_sha256":
                package[
                    "package_sha256"
                ],
            "production_approval":
                "production_approved",
            "rule_promotion":
                "promoted",
            "source_release":
                "not_released",
            "verification_authority":
                "stage6_governance_policy",
            "additional_human_review_claimed":
                False,
        },
        "rules": rules,
    }

    path = (
        tmp_dir
        / f"{country.lower()}.json"
    )

    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    records.append(
        {
            "treaty_pair_id":
                pair,
            "partner_country":
                country,
            "package_sha256":
                package[
                    "package_sha256"
                ],
            "rule_file":
                (
                    "data/legal_rules_stage6/"
                    f"{country.lower()}.json"
                ),
            "rule_file_sha256":
                hashlib.sha256(
                    path.read_bytes()
                ).hexdigest(),
            "rule_count":
                len(rules),
            "scope_count":
                3,
            "rule_promotion_status":
                "promoted",
            "source_release_status":
                "not_released",
        }
    )

    total_rules += len(
        rules
    )


if len(records) != 101:
    raise RuntimeError(
        "Materialized package count != 101."
    )

if len(scope_keys) != 303:
    raise RuntimeError(
        "Materialized scope count != 303."
    )


# Validate every generated file through
# the real production loader before replacing
# any existing Stage6 output directory.
from taxtreat.engine.legal_rule_loader import (
    load_legal_rules,
)

loaded_rules = 0
loaded_pairs = set()
loaded_scopes = set()

for path in sorted(
    tmp_dir.glob("*.json")
):
    rules = load_legal_rules(
        path
    )

    loaded_rules += len(
        rules
    )

    for rule in rules:
        loaded_pairs.add(
            (
                rule.source_country,
                rule.recipient_country,
            )
        )

        loaded_scopes.add(
            (
                rule.source_country,
                rule.recipient_country,
                rule.income_type,
            )
        )

if len(loaded_pairs) != 101:
    raise RuntimeError(
        f"Loader represented {len(loaded_pairs)} "
        "pairs instead of 101."
    )

if len(loaded_scopes) != 303:
    raise RuntimeError(
        f"Loader represented {len(loaded_scopes)} "
        "scopes instead of 303."
    )

if loaded_rules != total_rules:
    raise RuntimeError(
        "Loaded rule count mismatch."
    )


if OUTPUT_DIR.exists():
    shutil.rmtree(
        OUTPUT_DIR
    )

tmp_dir.rename(
    OUTPUT_DIR
)


promotion = {
    "schema_version": 1,
    "dataset_release":
        "stage6-rule-promotion-2026-08-12.1",
    "event_type":
        "deterministic_production_rule_promotion",
    "promotion_authority":
        "stage6_governance_policy",
    "created_from_approval_dataset_release":
        approval_release,
    "additional_human_review_claimed":
        False,
    "semantics": {
        "exact_package_hash_binding_required":
            True,
        "production_approval_required":
            True,
        "promotion_is_not_source_release":
            True,
        "promotion_does_not_open_runtime_gate":
            True,
        "secondary_ai_is_not_human_review":
            True,
    },
    "counts": {
        "rule_promoted_packages":
            101,
        "rule_promoted_scopes":
            303,
        "source_released_packages":
            0,
        "source_released_scopes":
            0,
        "runtime_rule_files":
            101,
        "runtime_rules":
            total_rules,
    },
    "records": records,
}

PROMOTION.write_text(
    json.dumps(
        promotion,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)

SUMMARY.write_text(
    json.dumps(
        {
            "dataset_release":
                promotion[
                    "dataset_release"
                ],
            "rule_promoted_packages":
                101,
            "rule_promoted_scopes":
                303,
            "source_released_packages":
                0,
            "source_released_scopes":
                0,
            "runtime_rule_files":
                101,
            "runtime_rules":
                total_rules,
            "canonical_gate_opened":
                False,
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)

print(
    "Stage 6 production materialization: PASS"
)
print(
    "Production-approved packages: 101/101"
)
print(
    "Materialized packages:        101/101"
)
print(
    "Materialized WHT scopes:      303/303"
)
print(
    f"Runtime rule files:           {len(records)}"
)
print(
    f"Runtime legal rules:          {total_rules}"
)
print(
    "Rule promotion manifest:      101/101"
)
print(
    "Source release:               0/101"
)
print(
    "Canonical runtime gate:       CLOSED"
)
