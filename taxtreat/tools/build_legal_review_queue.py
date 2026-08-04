from __future__ import annotations

import argparse

from taxtreat.consolidation.legal_review_queue import (
    DEFAULT_OUTPUT,
    build_legal_review_queue,
    write_legal_review_queue,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the fail-closed legal-review queue."
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    payload = build_legal_review_queue()
    write_legal_review_queue(payload, args.output)
    print(
        "Built "
        f"{payload['summary']['total_packets']} legal-review packets; "
        f"{payload['summary']['promotable_packets']} are promotable."
    )


if __name__ == "__main__":  # pragma: no cover
    main()
