import json

import pytest

import taxtreat.services.source_country_runtime_metadata as metadata_module
from taxtreat.services.source_country_runtime_metadata import (
    source_country_runtime_dataset_version,
)


def test_cz_runtime_dataset_uses_existing_stage6_loader():
    value = source_country_runtime_dataset_version(
        "CZ",
        cz_release_loader=lambda: {"dataset_release": "cz-stage6-test"},
    )
    assert value == "cz-stage6-test"


def test_sk_release_manifest_can_be_used_as_production_dataset():
    dataset_version = source_country_runtime_dataset_version("SK")

    assert dataset_version.startswith("sk-source-country-release-")


def test_released_non_cz_dataset_identity_comes_from_own_manifest(tmp_path, monkeypatch):
    manifest = tmp_path / "release.json"
    manifest.write_text(
        json.dumps({
            "source_country": "SK",
            "release_status": "released",
            "release_eligible": True,
            "dataset_release": "sk-production-test",
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        metadata_module,
        "_source_release_manifest_path",
        lambda code: manifest,
    )

    assert source_country_runtime_dataset_version("SK") == "sk-production-test"


def test_non_cz_runtime_metadata_never_calls_cz_stage6_loader(tmp_path, monkeypatch):
    manifest = tmp_path / "release.json"
    manifest.write_text(
        json.dumps({
            "source_country": "SK",
            "release_status": "released",
            "release_eligible": True,
            "dataset_release": "sk-production-test",
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        metadata_module,
        "_source_release_manifest_path",
        lambda code: manifest,
    )

    def forbidden():
        raise AssertionError("CZ Stage 6 loader was touched by SK runtime metadata")

    assert source_country_runtime_dataset_version(
        "SK",
        cz_release_loader=forbidden,
    ) == "sk-production-test"
