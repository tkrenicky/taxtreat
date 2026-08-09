from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

INTAKE = (
    ROOT
    / "data/legal_reviews/global_cz_outbound/"
    "stage5_remaining80_batch_01_intake.json"
)

MF_INVENTORY = (
    ROOT
    / "data/legal_consolidation/"
    "mf_inventory.json"
)

MLI_EFFECTS = (
    ROOT
    / "data/legal_consolidation/"
    "mli_wht_effects.json"
)

OECD_PDF = (
    ROOT
    / "data/legal_reviews/global_cz_outbound/"
    "stage5_batch01_mli_sources/"
    "oecd_mli_signatories_parties_2026-06-18.pdf"
)

OECD_TXT = (
    ROOT
    / "data/legal_reviews/global_cz_outbound/"
    "stage5_batch01_mli_sources/"
    "oecd_mli_signatories_parties_2026-06-18.txt"
)

MF_HTML = (
    ROOT
    / "data/legal_reviews/global_cz_outbound/"
    "stage5_batch01_mli_sources/"
    "cz_mf_treaty_overview_2026.html"
)

MF_TXT = (
    ROOT
    / "data/legal_reviews/global_cz_outbound/"
    "stage5_batch01_mli_sources/"
    "cz_mf_treaty_overview_2026.txt"
)

OUTPUT = (
    ROOT
    / "data/legal_reviews/global_cz_outbound/"
    "stage5_remaining80_batch_01_mli_evidence.json"
)


def load(path: Path):
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def partner(
    inventory: dict,
    code: str,
) -> dict:

    matches = [
        row
        for row in inventory["partners"]
        if row.get("iso2") == code
    ]

    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one MF inventory row for {code}"
        )

    return matches[0]


def has_effect_reference(
    effects,
    code: str,
) -> bool:

    token = f"CZ-{code}-MLI-".upper()

    def walk(value):

        if isinstance(value, str):
            yield value

        elif isinstance(value, dict):
            for key, item in value.items():
                yield str(key)
                yield from walk(item)

        elif isinstance(value, list):
            for item in value:
                yield from walk(item)

    return any(
        token in text.upper()
        for text in walk(effects)
    )


def matching_lines(
    text: str,
    pattern: str,
) -> list[str]:

    regex = re.compile(
        pattern,
        flags=re.I,
    )

    return [
        line.strip()
        for line in text.splitlines()
        if regex.search(line)
    ]


def main():

    intake = load(INTAKE)
    inventory = load(MF_INVENTORY)
    effects = load(MLI_EFFECTS)

    oecd = OECD_TXT.read_text(
        encoding="utf-8",
        errors="replace",
    )

    mf = MF_TXT.read_text(
        encoding="utf-8",
        errors="replace",
    )

    countries = set(
        intake["batch"]["countries"]
    )

    if "EE" not in countries:
        raise RuntimeError(
            "EE not present in Batch 01"
        )

    if "NG" not in countries:
        raise RuntimeError(
            "NG not present in Batch 01"
        )

    ee = partner(
        inventory,
        "EE",
    )

    ng = partner(
        inventory,
        "NG",
    )

    if ee.get("mli_listed") is not True:
        raise RuntimeError(
            "MF inventory no longer marks EE MLI-listed"
        )

    if ee.get(
        "mli_notice_available"
    ) is not True:
        raise RuntimeError(
            "MF inventory no longer has EE MLI notice"
        )

    if ng.get("mli_listed") is not True:
        raise RuntimeError(
            "MF inventory no longer marks NG MLI-listed"
        )

    if ng.get(
        "mli_notice_available"
    ) is not False:
        raise RuntimeError(
            "MF inventory NG notice status changed; "
            "manual review required"
        )

    ee_effect = has_effect_reference(
        effects,
        "EE",
    )

    ng_effect = has_effect_reference(
        effects,
        "NG",
    )

    if ee_effect:
        raise RuntimeError(
            "EE now already exists in mli_wht_effects; "
            "do not create stale gap evidence"
        )

    if ng_effect:
        raise RuntimeError(
            "NG now already exists in mli_wht_effects; "
            "do not create stale gap evidence"
        )

    ee_mf_sources = [
        row
        for row in ee.get(
            "related_instruments",
            []
        )
        if row.get(
            "source_type"
        )
        in {
            "mli_convention",
            "mli_effect_notice",
            "mli_synthesised_notice",
        }
    ]

    ng_mf_sources = [
        row
        for row in ng.get(
            "related_instruments",
            []
        )
        if row.get(
            "source_type"
        )
        in {
            "mli_convention",
            "mli_effect_notice",
            "mli_synthesised_notice",
        }
    ]

    ee_oecd_lines = matching_lines(
        oecd,
        r"\bEstonia\b",
    )

    ng_oecd_lines = matching_lines(
        oecd,
        r"\bNigeria\b",
    )

    cz_oecd_lines = matching_lines(
        oecd,
        r"\bCzechia\b",
    )

    if not ee_oecd_lines:
        raise RuntimeError(
            "Estonia row not found in OECD source"
        )

    if not ng_oecd_lines:
        raise RuntimeError(
            "Nigeria row not found in OECD source"
        )

    if not cz_oecd_lines:
        raise RuntimeError(
            "Czechia row not found in OECD source"
        )

    if not any(
        "15-01-2021" in line
        and "01-05-2021" in line
        for line in ee_oecd_lines
    ):
        raise RuntimeError(
            "Estonia deposit/entry evidence not found"
        )

    if not any(
        "17-08-2017" in line
        for line in ng_oecd_lines
    ):
        raise RuntimeError(
            "Nigeria signature evidence not found"
        )

    evidence = {
        "schema_version": 1,
        "dataset_release":
            "stage5-batch01-mli-evidence-2026-08-09.1",
        "purpose": (
            "Repository-backed review evidence resolving the "
            "mechanical Batch 01 MLI gaps for EE and NG. "
            "This dataset is not a production legal rule and "
            "does not constitute human legal approval."
        ),
        "verification_status":
            "needs_review",
        "production_releasable":
            False,
        "safety_boundary": {
            "official_sources_only":
                True,
            "extraction_is_not_verification":
                True,
            "provenance_is_not_approval":
                True,
            "no_automatic_mli_effect_mapping":
                True,
            "human_review_required":
                True,
        },
        "official_source_snapshots": {
            "oecd_mli_signatories_parties": {
                "official_url": (
                    "https://www.oecd.org/content/dam/oecd/"
                    "en/topics/policy-sub-issues/beps-mli/"
                    "beps-mli-signatories-and-parties.pdf/"
                    "_jcr_content/renditions/original./"
                    "beps-mli-signatories-and-parties.pdf"
                ),
                "status_date":
                    "2026-06-18",
                "pdf_path":
                    str(OECD_PDF.relative_to(ROOT)),
                "pdf_sha256":
                    sha256(OECD_PDF),
                "text_path":
                    str(OECD_TXT.relative_to(ROOT)),
                "text_sha256":
                    sha256(OECD_TXT),
            },
            "czech_mf_treaty_overview": {
                "official_url": (
                    "https://mf.gov.cz/cs/"
                    "zahranici-a-eu/"
                    "smlouvy-o-zamezeni-dvojiho-zdaneni/"
                    "prehled-platnych-smluv"
                ),
                "html_path":
                    str(MF_HTML.relative_to(ROOT)),
                "html_sha256":
                    sha256(MF_HTML),
                "text_path":
                    str(MF_TXT.relative_to(ROOT)),
                "text_sha256":
                    sha256(MF_TXT),
            },
        },
        "countries": {
            "EE": {
                "country":
                    "Estonsko",
                "repository_inventory": {
                    "mli_listed":
                        True,
                    "mli_notice_available":
                        True,
                    "mli_effect_reference_present":
                        False,
                    "official_mli_instruments":
                        ee_mf_sources,
                },
                "oecd_current_party_evidence": {
                    "matching_lines":
                        ee_oecd_lines,
                    "deposit_date_evidenced":
                        "2021-01-15",
                    "entry_into_force_evidenced":
                        "2021-05-01",
                },
                "czechia_current_party_evidence": {
                    "matching_lines":
                        cz_oecd_lines,
                },
                "candidate_resolution": {
                    "status":
                        "structured_effect_mapping_pending_review",
                    "reason": (
                        "Official MLI/effect-notice evidence exists "
                        "in repository inventory, but no corresponding "
                        "structured CZ-EE effect exists in "
                        "mli_wht_effects.json."
                    ),
                    "verification_status":
                        "needs_review",
                    "production_releasable":
                        False,
                    "next_required_action":
                        "human_review_of_mli_matching_and_article_35_effect",
                },
            },
            "NG": {
                "country":
                    "Nigérie",
                "repository_inventory": {
                    "mli_listed":
                        True,
                    "mli_notice_available":
                        False,
                    "mli_effect_reference_present":
                        False,
                    "official_mli_instruments":
                        ng_mf_sources,
                },
                "oecd_current_signatory_evidence": {
                    "matching_lines":
                        ng_oecd_lines,
                    "signature_date_evidenced":
                        "2017-08-17",
                    "deposit_of_ratification_evidenced":
                        False,
                    "entry_into_force_evidenced":
                        False,
                },
                "candidate_resolution": {
                    "status":
                        "counterparty_ratification_not_evidenced",
                    "reason": (
                        "Current OECD official signatories/parties "
                        "source contains Nigeria's signature but does "
                        "not evidence a deposit of ratification or "
                        "entry into force."
                    ),
                    "verification_status":
                        "needs_review",
                    "production_releasable":
                        False,
                    "next_required_action":
                        "human_confirmation_of_current_bilateral_mli_non_effect",
                },
            },
        },
        "result": {
            "original_mechanical_gap_count":
                3,
            "unclassified_gap_count":
                0,
            "production_rules_created":
                0,
            "verified_rules_created":
                0,
        },
    }

    OUTPUT.write_text(
        json.dumps(
            evidence,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "Batch 01 MLI evidence generated successfully."
    )

    print(
        "EE:",
        evidence["countries"]["EE"][
            "candidate_resolution"
        ]["status"],
    )

    print(
        "NG:",
        evidence["countries"]["NG"][
            "candidate_resolution"
        ]["status"],
    )

    print("Verification: needs_review")
    print("Production releasable: false")
    print("Unclassified mechanical gaps: 0")


if __name__ == "__main__":
    main()
