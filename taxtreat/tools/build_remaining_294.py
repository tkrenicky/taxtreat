from __future__ import annotations

import argparse
from pathlib import Path

from taxtreat.consolidation.base_candidates import (
    build_base_candidates,
    write_base_candidates,
)
from taxtreat.consolidation.mf_inventory import (
    build_inventory,
    fetch_overview,
    write_inventory,
)
from taxtreat.consolidation.mli_effects import (
    refresh_mli_effects,
    write_mli_effects,
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--html",
        type=Path,
        help="Use a saved MF overview page instead of downloading it.",
    )
    parser.add_argument(
        "--refresh-mli",
        action="store_true",
        help="Download and extract the 62 official Czech MLI WHT notices.",
    )
    args = parser.parse_args(argv)
    html_text = (
        args.html.read_text(encoding="utf-8")
        if args.html is not None
        else fetch_overview()
    )
    inventory = build_inventory(html_text, retrieved_at="2026-08-03")
    write_inventory(inventory)
    if args.refresh_mli:
        write_mli_effects(refresh_mli_effects())
    candidates = build_base_candidates()
    write_base_candidates(candidates)
    with_rates = sum(bool(scope["rate_candidates"]) for scope in candidates["scopes"])
    print(f"Official instrument inventories: {len(inventory['partners'])}/100")
    print(f"Remaining base-treaty scopes: {len(candidates['scopes'])}/294")
    print(f"Scopes with extracted rate candidates: {with_rates}/294")


if __name__ == "__main__":  # pragma: no cover
    main()
