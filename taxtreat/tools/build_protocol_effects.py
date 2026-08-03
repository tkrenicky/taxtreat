from __future__ import annotations

from taxtreat.consolidation.protocol_effects import (
    build_protocol_effects,
    write_protocol_effects,
)


def main() -> int:
    payload = build_protocol_effects()
    write_protocol_effects(payload)
    print(
        "Built "
        f"{len(payload['scopes'])} protocol-effect candidates from "
        f"{len(payload['documents'])} official instruments."
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
