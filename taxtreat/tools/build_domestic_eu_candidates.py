from __future__ import annotations

from taxtreat.consolidation.domestic_eu_effects import (
    build_domestic_eu_candidates,
    write_domestic_eu_candidates,
)


def main() -> int:
    payload = build_domestic_eu_candidates()
    write_domestic_eu_candidates(payload)
    relief_scopes = sum(
        row["relief_candidate"] is not None for row in payload["scopes"]
    )
    print(
        f"Built {len(payload['scopes'])} Czech domestic candidates; "
        f"{relief_scopes} contain section 19 relief candidates."
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
