from __future__ import annotations

import argparse
from collections.abc import Callable
import sys

from taxtreat.consolidation.legal_review_queue import (
    build_legal_review_queue,
    write_legal_review_queue,
)
from taxtreat.pipeline.release import (
    build_legal_registry,
    build_release_manifest,
    build_source_manifest,
    validate_release,
)


Step = tuple[str, Callable[[], object]]


def build_review_queue() -> None:
    write_legal_review_queue(build_legal_review_queue())


STEPS: list[Step] = [
    ("Build source manifest", build_source_manifest),
    ("Build legal-review queue", build_review_queue),
    ("Build canonical legal registry", build_legal_registry),
    ("Build release manifest", build_release_manifest),
]


def run(*, production: bool = False) -> None:
    for name, step in STEPS:
        print(f"RUN  {name}")
        step()
        print(f"OK   {name}")
    validate_release(production=production)
    print("Pipeline finished successfully.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build a TaxTreat dataset release.")
    parser.add_argument(
        "--production",
        action="store_true",
        help="Require all production source and legal approval gates.",
    )
    args = parser.parse_args(argv)
    try:
        run(production=args.production)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":  # pragma: no cover - exercised via module smoke test
    main()
