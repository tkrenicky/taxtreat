from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from taxtreat.countries.registry import get_country_config


ROOT = Path(__file__).resolve().parents[2]


def _source_release_manifest_path(code: str) -> Path:
    config = get_country_config(code)

    if config.release_manifest_path is not None:
        return Path(config.release_manifest_path)

    return (
        ROOT
        / "data"
        / "legal_reviews"
        / f"{code.lower()}_outbound"
        / "source_country_release_manifest.json"
    )


def source_country_runtime_dataset_version(
    source_country: str,
    *,
    cz_release_loader: Callable[[], dict[str, Any]] | None = None,
) -> str:
    code = str(source_country or "").upper()
    config = get_country_config(code)

    if config.runtime_dataset_strategy == "canonical_stage6":
        if cz_release_loader is None:
            raise ValueError(
                f"{code} runtime dataset version requires the canonical Stage 6 loader."
            )
        payload = cz_release_loader()
        dataset = str(payload.get("dataset_release") or "")
        if not dataset:
            raise ValueError(
                f"{code} Stage 6 source release has no dataset identifier."
            )
        return dataset

    if config.runtime_dataset_strategy != "source_country_manifest":
        raise ValueError(
            f"Unsupported runtime dataset strategy for {code}: "
            f"{config.runtime_dataset_strategy}"
        )

    path = _source_release_manifest_path(code)
    if not path.is_file():
        raise ValueError(f"No source-country release manifest for {code}.")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid source-country release manifest for {code}.") from exc

    if payload.get("source_country") != code:
        raise ValueError(f"Source-country release manifest mismatch for {code}.")
    if payload.get("release_status") != "released" or payload.get("release_eligible") is not True:
        raise ValueError(f"Source-country runtime dataset is not released for {code}.")

    dataset = str(payload.get("dataset_release") or "")
    if not dataset:
        raise ValueError(f"Released source-country manifest has no dataset identifier for {code}.")
    return dataset
