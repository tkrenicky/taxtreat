from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_treaty_verbatim_registry.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("verbatim_registry", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_registry_covers_all_runtime_treaty_provisions():
    module = _load_module()
    result = module.build_registry()

    assert result["counts"]["unique_used_treaty_provisions"] == 303
    assert result["counts"]["unique_official_source_instruments"] == 101
    assert len(result["provisions"]) == 303
    assert len({item["key"] for item in result["provisions"]}) == 303


def test_verbatim_gate_is_fail_closed_until_every_provision_has_pdf_provenance():
    module = _load_module()
    result = module.build_registry()

    verified = result["counts"]["verified_against_authoritative_pdf"]
    assert result["release_gate"]["complete"] is (verified == 303)

    for item in result["provisions"]:
        if item["verification_status"] == "verified_against_authoritative_pdf":
            assert item["canonical_text_present"] is True
            assert item["canonical_text_sha256"]
            assert item["official_pdf_sha256"]
