from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

DEFAULT_GATE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "production_source_release_gate.json"
)


class SourceReleaseGateError(RuntimeError):
    """Base error for production source release-gate failures."""


class SourceNotReleasedError(SourceReleaseGateError):
    """Raised when a treaty pair is not approved for active use."""


class SourceGateConfigurationError(SourceReleaseGateError):
    """Raised when the release-gate dataset is missing or invalid."""


@dataclass(frozen=True)
class TreatySourceRelease:
    treaty_pair_id: str
    partner_country: str
    release_status: str
    active_rule_allowed: bool
    production_ready: bool
    fail_closed: bool
    release_blockers: tuple[str, ...]
    release_evidence: Mapping[str, Any]

    @property
    def is_released(self) -> bool:
        return (
            self.release_status == "released"
            and self.active_rule_allowed is True
            and self.production_ready is True
            and self.fail_closed is False
            and not self.release_blockers
        )


def _validate_entry(entry: Mapping[str, Any]) -> None:
    required = {
        "treaty_pair_id",
        "partner_country",
        "release_status",
        "active_rule_allowed",
        "production_ready",
        "fail_closed",
        "release_blockers",
        "release_evidence",
    }

    missing = required - set(entry)

    if missing:
        raise SourceGateConfigurationError(
            "Release-gate entry is missing fields: "
            + ", ".join(sorted(missing))
        )

    if not isinstance(entry["release_blockers"], list):
        raise SourceGateConfigurationError(
            f"{entry['treaty_pair_id']}: release_blockers must be a list"
        )

    if not isinstance(entry["release_evidence"], dict):
        raise SourceGateConfigurationError(
            f"{entry['treaty_pair_id']}: release_evidence must be an object"
        )


@lru_cache(maxsize=4)
def load_source_release_gate(
    gate_path: str | Path = DEFAULT_GATE_PATH,
) -> dict[str, TreatySourceRelease]:
    path = Path(gate_path)

    if not path.is_file():
        raise SourceGateConfigurationError(
            f"Production source release gate not found: {path}"
        )

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceGateConfigurationError(
            f"Unable to load production source release gate: {path}"
        ) from exc

    if payload.get("fail_closed") is not True:
        raise SourceGateConfigurationError(
            "Production source release gate must be globally fail-closed"
        )

    rows = payload.get("treaty_partners")

    if not isinstance(rows, list):
        raise SourceGateConfigurationError(
            "Production source release gate has no treaty_partners list"
        )

    releases: dict[str, TreatySourceRelease] = {}

    for entry in rows:
        if not isinstance(entry, dict):
            raise SourceGateConfigurationError(
                "Release-gate treaty entry must be an object"
            )

        _validate_entry(entry)

        pair_id = str(entry["treaty_pair_id"])

        if pair_id in releases:
            raise SourceGateConfigurationError(
                f"Duplicate treaty pair in release gate: {pair_id}"
            )

        releases[pair_id] = TreatySourceRelease(
            treaty_pair_id=pair_id,
            partner_country=str(entry["partner_country"]),
            release_status=str(entry["release_status"]),
            active_rule_allowed=bool(entry["active_rule_allowed"]),
            production_ready=bool(entry["production_ready"]),
            fail_closed=bool(entry["fail_closed"]),
            release_blockers=tuple(
                str(value)
                for value in entry["release_blockers"]
            ),
            release_evidence=dict(entry["release_evidence"]),
        )

    if len(releases) != payload.get("treaty_partner_count"):
        raise SourceGateConfigurationError(
            "Release-gate treaty count does not match its metadata"
        )

    return releases


def get_source_release(
    treaty_pair_id: str,
    *,
    gate_path: str | Path = DEFAULT_GATE_PATH,
) -> TreatySourceRelease:
    pair_id = treaty_pair_id.strip().upper()

    releases = load_source_release_gate(gate_path)

    try:
        return releases[pair_id]
    except KeyError as exc:
        raise SourceNotReleasedError(
            f"No production source release exists for {pair_id}"
        ) from exc


def require_released_source(
    treaty_pair_id: str,
    *,
    gate_path: str | Path = DEFAULT_GATE_PATH,
) -> TreatySourceRelease:
    release = get_source_release(
        treaty_pair_id,
        gate_path=gate_path,
    )

    if not release.is_released:
        blockers = ", ".join(release.release_blockers) or "unknown blockers"

        raise SourceNotReleasedError(
            f"{release.treaty_pair_id} is blocked from active use: "
            f"{blockers}"
        )

    return release


def source_is_released(
    treaty_pair_id: str,
    *,
    gate_path: str | Path = DEFAULT_GATE_PATH,
) -> bool:
    try:
        return require_released_source(
            treaty_pair_id,
            gate_path=gate_path,
        ).is_released
    except SourceReleaseGateError:
        return False
