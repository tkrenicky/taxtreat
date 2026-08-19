from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any

from taxtreat.countries.registry import get_country_config


@dataclass(frozen=True)
class SourceCountryReleaseDecision:
    source_country: str
    allowed: bool
    code: str
    release_status: str
    blockers: tuple[str, ...]


class SourceCountryNotReleasedError(RuntimeError):
    def __init__(self, decision: SourceCountryReleaseDecision):
        self.decision = decision
        super().__init__(
            f"{decision.source_country} source-country package is not released."
        )


class UnsupportedSourceCountryError(ValueError):
    pass


def require_source_country_analysis_release(
    source_country: str,
    *,
    released_country_gate: Callable[[str], Any] | None = None,
) -> SourceCountryReleaseDecision:
    code = str(source_country or "").upper()
    try:
        config = get_country_config(code)
    except KeyError as exc:
        raise UnsupportedSourceCountryError(code) from exc

    if not config.runtime_released:
        decision = SourceCountryReleaseDecision(
            source_country=code,
            allowed=False,
            code="SOURCE_COUNTRY_NOT_RELEASED",
            release_status="pre_release",
            blockers=(
                "source_country_runtime_release_false",
                "full_human_legal_review_not_completed",
            ),
        )
        raise SourceCountryNotReleasedError(decision)

    if released_country_gate is not None:
        released_country_gate(code)

    return SourceCountryReleaseDecision(
        source_country=code,
        allowed=True,
        code="SOURCE_COUNTRY_RELEASED",
        release_status="released",
        blockers=(),
    )
