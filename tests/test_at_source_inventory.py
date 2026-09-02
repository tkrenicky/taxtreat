from __future__ import annotations

import json
from pathlib import Path

import pytest

from taxtreat.countries.registry import get_country_config, supported_source_countries


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "data" / "legal_reviews" / "at_outbound" / "source_inventory.json"


def _inventory() -> dict:
    return json.loads(INVENTORY.read_text(encoding="utf-8"))


def test_at_discovery_inventory_is_primary_source_only_and_fail_closed():
    data = _inventory()

    assert data["source_country"] == "AT"
    assert data["status"] == "discovery_only_not_released"
    assert data["scope"]["income_types"] == ["dividend", "interest", "royalty"]

    authorities = {row["authority"] for row in data["primary_sources"]}
    assert authorities <= {
        "Bundesministerium für Finanzen (Österreich)",
        "Rechtsinformationssystem des Bundes (RIS)",
    }

    urls = "\n".join(row["url"] for row in data["primary_sources"])
    assert "bmf.gv.at" in urls
    assert "ris.bka.gv.at" in urls

    constraints = "\n".join(data["release_constraints"])
    assert "remain unregistered" in constraints
    assert "fail-closed" in constraints
    assert "MLI matching" in constraints


def test_at_is_not_registered_or_runtime_released_by_discovery_batch():
    assert "AT" not in supported_source_countries()
    with pytest.raises(KeyError, match="Unsupported source country: AT"):
        get_country_config("AT")


def test_at_interest_is_explicitly_unresolved_not_inferred_from_dividend_or_royalty_rules():
    data = _inventory()
    interest = data["domestic_model_seed"]["interest"]

    assert interest["status"] == "requires_source_nexus_mapping"
    assert "§§ 27, 93-95 and 98" in interest["candidate_regime"]
    assert "§ 99a" in interest["candidate_regime"]


def test_at_dividend_and_royalty_seed_preserves_distinct_domestic_regimes():
    data = _inventory()
    seed = data["domestic_model_seed"]

    assert "§§ 27, 93-95" in seed["dividend"]["candidate_regime"]
    assert seed["dividend"]["eu_parent_relief_seed"] == "§ 94 EStG 1988"
    assert "§§ 28, 98, 99-100" in seed["royalty"]["candidate_regime"]
    assert "§ 99a" in seed["royalty"]["candidate_regime"]
    assert seed["royalty"]["status"] == "requires_category_mapping"


def test_interest_and_royalty_eu_exemption_is_explicitly_separate_from_base_domestic_scope():
    data = _inventory()
    section_99a = next(
        row for row in data["primary_sources"] if row["source_id"] == "AT-RIS-ESTG-99A"
    )

    observation = section_99a["relevant_observation"]
    assert "25%" in observation
    assert "one uninterrupted year" in observation
    assert "beneficial owner" in observation
    assert "confirmations available at payment" in observation

    constraints = "\n".join(data["release_constraints"])
    assert "documentary prerequisites at payment" in constraints
    assert "later refund eligibility" in constraints


def test_treaty_relief_substantive_and_relief_at_source_procedure_are_separate_layers():
    data = _inventory()
    procedural = next(
        row for row in data["primary_sources"] if row["source_id"] == "AT-BMF-RELIEF-AT-SOURCE"
    )

    assert "procedural" in procedural["use"]
    assert "must not be collapsed into treaty-rate eligibility" in procedural["caution"]
