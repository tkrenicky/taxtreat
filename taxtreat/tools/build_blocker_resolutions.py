from __future__ import annotations

from taxtreat.consolidation.blocker_resolutions import (
    build_blocker_resolutions,
    write_blocker_resolutions,
)


def main() -> None:
    payload = build_blocker_resolutions()
    write_blocker_resolutions(payload)
    print(
        "Resolved blocker candidates: "
        f"{payload['summary']['resolved_scopes']} scopes"
    )


if __name__ == "__main__":  # pragma: no cover
    main()
