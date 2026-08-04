from __future__ import annotations

from taxtreat.pipeline.release import build_release_manifest


def render() -> str:
    manifest = build_release_manifest()
    parser = manifest["parser"]
    sources = manifest["sources"]
    legal = manifest["legal"]
    lines = [
        "TaxTreat release dashboard",
        f"Parser datasets: {parser['datasets']}",
        f"Relevant articles: {parser['relevant_articles']}",
        f"Source auditability: {sources['auditability']} "
        f"({sources['artifacts_with_hash']}/{sources['total']})",
        f"Registered legal scopes: {legal['scopes']}/300",
        "Official instrument inventories: "
        f"{legal['instrument_inventory_partners']}/100",
        "Remaining base-treaty candidates: "
        f"{legal['base_candidate_scopes']}/294 "
        f"({legal['base_candidate_scopes_with_rates']} with rates; "
        f"{legal['base_candidate_no_numeric_cap_scopes']} no-cap)",
        "Protocol candidates: "
        f"{legal['protocol_effect_candidate_scopes']} scopes / "
        f"{legal['protocol_effect_candidate_partners']} partners / "
        f"{legal['protocol_effect_candidate_documents']} instruments",
        "Czech domestic-law candidates: "
        f"{legal['domestic_candidate_scopes']}/300 "
        f"({legal['remaining_domestic_candidate_scopes']}/294 remaining scopes)",
        "Section 19 relief candidates: "
        f"{legal['eu_relief_candidate_scopes']} scopes / "
        f"{legal['eu_relief_candidate_partners']} partners "
        f"({legal['remaining_eu_relief_candidate_scopes']} remaining scopes)",
        "Remaining instrument chains: "
        f"{legal['instrument_chain_assembled_scopes']} assembled / "
        f"{legal['instrument_chain_blocked_scopes']} blocked "
        f"({legal['instrument_chain_blocked_partners']} partners)",
        "Candidate legal-review queue: "
        f"{legal['candidate_review_packets']}/294 packets; "
        f"{legal['candidate_review_awaiting_primary']} awaiting primary review; "
        f"{legal['candidate_review_independently_approved']} independently approved; "
        f"{legal['candidate_review_promotable']} promotable",
        "Official MLI WHT effect candidates: "
        f"{legal['mli_wht_effect_candidate_partners']}/64; "
        "signed without current effect: "
        f"{legal['mli_no_current_effect_determinations']}",
        "Status-instrument candidates: "
        f"{legal['status_instrument_candidate_partners']} partners",
        f"Review-ready legal scopes: {legal['review_ready_scopes']}/300",
        "Pending legal consolidation: "
        f"{legal['pending_consolidation_scopes']}/300",
        f"Verified legal scopes: {legal['verified_scopes']}/300",
        f"Golden cases: {manifest['golden_cases']}",
        f"Production ready: {manifest['production_ready']}",
    ]
    return "\n".join(lines)


def main() -> None:
    print(render())


if __name__ == "__main__":  # pragma: no cover
    main()
