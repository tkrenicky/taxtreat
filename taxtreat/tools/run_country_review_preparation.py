from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from taxtreat.tools.build_country_human_review_pack import build_human_review_pack, write_csv
from taxtreat.tools.build_treaty_scope_machine_evidence import build_scope_machine_evidence
from taxtreat.tools.review_bundle_provenance import build_review_bundle_provenance


def _load(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def prepare_country_review(
    *,
    review_queue: dict[str, Any],
    article_inventory: dict[str, Any],
    artifact_root: Path,
    royalty_audit: dict[str, Any] | None = None,
    language_evidence: dict[str, Any] | None = None,
    article_reconciliation: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    queue_country = str(review_queue.get("source_country") or "").strip().upper()
    article_country = str(article_inventory.get("source_country") or "").strip().upper()
    if not queue_country or queue_country != article_country:
        raise ValueError(
            f"Review queue/article inventory source-country mismatch: {queue_country!r} vs {article_country!r}"
        )

    provenance = build_review_bundle_provenance(
        review_queue=review_queue,
        article_inventory=article_inventory,
        royalty_audit=royalty_audit,
        language_evidence=language_evidence,
        article_reconciliation=article_reconciliation,
    )

    scope_evidence = build_scope_machine_evidence(article_inventory, artifact_root=artifact_root)
    if scope_evidence["source_country"] != queue_country:
        raise ValueError("Scope evidence source country does not match review queue")

    expected_scope_count = len(review_queue.get("scopes") or [])
    if expected_scope_count <= 0:
        raise ValueError("Review queue contains no scopes")
    if scope_evidence["scope_count"] != expected_scope_count:
        raise ValueError(
            f"Scope-count mismatch: review queue {expected_scope_count} vs machine evidence {scope_evidence['scope_count']}"
        )

    scope_evidence["review_bundle_id"] = provenance["review_bundle_id"]
    scope_evidence["review_bundle_provenance"] = provenance

    review_pack = build_human_review_pack(
        review_queue,
        royalty_audit=royalty_audit,
        language_evidence=language_evidence,
        article_reconciliation=article_reconciliation,
        scope_evidence=scope_evidence,
        review_bundle_provenance=provenance,
    )
    if review_pack["scope_count"] != expected_scope_count:
        raise ValueError("Human-review pack scope count does not match review queue")
    if review_pack.get("review_bundle_id") != provenance["review_bundle_id"]:
        raise ValueError("Human-review pack provenance binding failed")

    return scope_evidence, review_pack


def write_review_outputs(
    *,
    scope_evidence: dict[str, Any],
    review_pack: dict[str, Any],
    scope_output: Path,
    review_json_output: Path,
    review_csv_output: Path,
) -> None:
    for path in (scope_output, review_json_output, review_csv_output):
        path.parent.mkdir(parents=True, exist_ok=True)
    scope_output.write_text(
        json.dumps(scope_evidence, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    review_json_output.write_text(
        json.dumps(review_pack, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_csv(review_pack, review_csv_output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--articles", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--royalty-audit", type=Path)
    parser.add_argument("--language-evidence", type=Path)
    parser.add_argument("--article-reconciliation", type=Path)
    parser.add_argument("--scope-output", type=Path, required=True)
    parser.add_argument("--review-json-output", type=Path, required=True)
    parser.add_argument("--review-csv-output", type=Path, required=True)
    args = parser.parse_args()

    scope_evidence, review_pack = prepare_country_review(
        review_queue=_load(args.queue) or {},
        article_inventory=_load(args.articles) or {},
        artifact_root=args.artifact_root,
        royalty_audit=_load(args.royalty_audit),
        language_evidence=_load(args.language_evidence),
        article_reconciliation=_load(args.article_reconciliation),
    )
    write_review_outputs(
        scope_evidence=scope_evidence,
        review_pack=review_pack,
        scope_output=args.scope_output,
        review_json_output=args.review_json_output,
        review_csv_output=args.review_csv_output,
    )
    print(
        "Country review preparation:",
        review_pack["source_country"],
        review_pack["scope_count"],
        "scopes /",
        review_pack["review_ready_scope_count"],
        "review-ready /",
        review_pack["blocked_scope_count"],
        "blocked / bundle",
        review_pack["review_bundle_id"],
    )


if __name__ == "__main__":
    main()
