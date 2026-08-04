from __future__ import annotations

import argparse

from taxtreat.consolidation.instrument_chains import (
    DEFAULT_OUTPUT,
    build_instrument_chains,
    write_instrument_chains,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build fail-closed instrument-chain candidates."
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    payload = build_instrument_chains()
    write_instrument_chains(payload, args.output)
    print(
        "Built "
        f"{payload['summary']['candidate_chain_assembled_scopes']} assembled "
        "candidate chains and "
        f"{payload['summary']['candidate_chain_blocked_scopes']} blocked chains."
    )


if __name__ == "__main__":  # pragma: no cover
    main()
