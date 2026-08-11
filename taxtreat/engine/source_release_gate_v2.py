from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]

DEFAULT_GATE_PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "production_source_release_gate_v2.json"
)


class CanonicalSourceGateError(RuntimeError):
    pass


class CanonicalSourceNotReleasedError(
    CanonicalSourceGateError
):
    pass


@dataclass(frozen=True)
class CanonicalSourceRelease:
    treaty_pair_id: str
    partner_country: str
    package_sha256: str

    human_review_status: str
    independent_qa_status: str
    production_approval_status: str
    rule_promotion_status: str

    release_status: str
    active_rule_allowed: bool
    production_ready: bool
    fail_closed: bool

    release_blockers: tuple[str, ...]
    release_evidence: Mapping[str, Any]

    @property
    def is_released(self) -> bool:
        return (
            self.human_review_status
            == "human_review_complete"
            and self.independent_qa_status
            in {"complete", "not_required"}
            and self.production_approval_status
            == "production_approved"
            and self.rule_promotion_status
            == "promoted"
            and self.release_status
            == "released"
            and self.active_rule_allowed is True
            and self.production_ready is True
            and self.fail_closed is False
            and not self.release_blockers
        )


@lru_cache(maxsize=4)
def load_canonical_source_release_gate(
    path: str | Path = DEFAULT_GATE_PATH,
) -> dict[str, CanonicalSourceRelease]:

    path = Path(path)

    if not path.is_file():
        raise CanonicalSourceGateError(
            f"Canonical production gate missing: {path}"
        )

    payload = json.loads(
        path.read_text(encoding="utf-8")
    )

    if payload.get("schema_version") != 2:
        raise CanonicalSourceGateError(
            "Canonical production gate requires schema version 2."
        )

    if payload.get("fail_closed") is not True:
        raise CanonicalSourceGateError(
            "Canonical production gate must be fail-closed."
        )

    if payload.get("treaty_partner_count") != 101:
        raise CanonicalSourceGateError(
            "Canonical production gate must contain 101 packages."
        )

    if payload.get("universe", {}).get("scope_count") != 303:
        raise CanonicalSourceGateError(
            "Canonical production gate must represent 303 scopes."
        )

    rows = payload.get("treaty_partners")

    if not isinstance(rows, list):
        raise CanonicalSourceGateError(
            "Canonical gate requires treaty_partners."
        )

    releases = {}

    for row in rows:
        pair_id = row["treaty_pair_id"]

        if pair_id in releases:
            raise CanonicalSourceGateError(
                f"Duplicate treaty pair: {pair_id}"
            )

        package_sha = row.get("package_sha256")

        if (
            not isinstance(package_sha, str)
            or len(package_sha) != 64
        ):
            raise CanonicalSourceGateError(
                f"{pair_id}: invalid package hash."
            )

        releases[pair_id] = CanonicalSourceRelease(
            treaty_pair_id=pair_id,
            partner_country=row["partner_country"],
            package_sha256=package_sha,

            human_review_status=
                row["human_review_status"],

            independent_qa_status=
                row["independent_qa_status"],

            production_approval_status=
                row["production_approval_status"],

            rule_promotion_status=
                row["rule_promotion_status"],

            release_status=row["release_status"],
            active_rule_allowed=
                row["active_rule_allowed"],
            production_ready=
                row["production_ready"],
            fail_closed=row["fail_closed"],

            release_blockers=tuple(
                row["release_blockers"]
            ),

            release_evidence=dict(
                row["release_evidence"]
            ),
        )

    if len(releases) != 101:
        raise CanonicalSourceGateError(
            "Canonical gate does not contain 101 unique packages."
        )

    return releases


def get_canonical_source_release(
    treaty_pair_id: str,
    *,
    gate_path: str | Path = DEFAULT_GATE_PATH,
) -> CanonicalSourceRelease:

    pair_id = treaty_pair_id.strip().upper()

    gate = load_canonical_source_release_gate(
        gate_path
    )

    try:
        return gate[pair_id]
    except KeyError as exc:
        raise CanonicalSourceNotReleasedError(
            f"No canonical release record exists for {pair_id}."
        ) from exc


def require_canonical_released_source(
    treaty_pair_id: str,
    *,
    gate_path: str | Path = DEFAULT_GATE_PATH,
) -> CanonicalSourceRelease:

    release = get_canonical_source_release(
        treaty_pair_id,
        gate_path=gate_path,
    )

    if not release.is_released:
        blockers = (
            ", ".join(release.release_blockers)
            or "unknown blockers"
        )

        raise CanonicalSourceNotReleasedError(
            f"{release.treaty_pair_id} is not released: "
            f"{blockers}"
        )

    return release
