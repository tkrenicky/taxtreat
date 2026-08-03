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
        f"({legal['base_candidate_scopes_with_rates']} with rates)",
        "Official MLI WHT effect candidates: "
        f"{legal['mli_wht_effect_candidate_partners']}/62",
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
