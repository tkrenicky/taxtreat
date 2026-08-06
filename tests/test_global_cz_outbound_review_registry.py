from taxtreat.tools.build_global_cz_outbound_review_registry import (
    build_global_registry,
)


def test_registry_contains_exactly_300_scopes():
    registry = build_global_registry()

    assert len(registry["packs"]) == 300


def test_registry_contains_100_countries():
    registry = build_global_registry()

    assert len(
        {
            pack["recipient_country"]
            for pack in registry["packs"]
        }
    ) == 100


def test_each_country_contains_three_income_types():
    registry = build_global_registry()

    by_country = {}

    for pack in registry["packs"]:
        by_country.setdefault(
            pack["recipient_country"],
            set(),
        ).add(pack["income_type"])

    assert len(by_country) == 100

    for income_types in by_country.values():
        assert income_types == {
            "dividend",
            "interest",
            "royalty",
        }


def test_all_scopes_remain_fail_closed():
    registry = build_global_registry()

    for pack in registry["packs"]:
        assert (
            pack["status"]
            == "awaiting_primary_review"
        )
        assert pack["approval_eligible"] is False
        assert (
            pack["promotable_to_active_rules"]
            is False
        )
        assert (
            pack["review"]["review_outcome"]
            is None
        )
        assert (
            pack["review"][
                "proposed_rule_snapshot"
            ]
            is None
        )


def test_all_packs_have_stable_identity():
    registry = build_global_registry()

    packet_ids = [
        pack["packet_id"]
        for pack in registry["packs"]
    ]

    hashes = [
        pack["review_pack_sha256"]
        for pack in registry["packs"]
    ]

    assert len(packet_ids) == len(set(packet_ids))
    assert all(len(value) == 64 for value in hashes)


def test_all_packs_have_domestic_legal_layer():
    registry = build_global_registry()

    for pack in registry["packs"]:
        assert (
            pack["legal_layers"][
                "domestic_and_eu"
            ]
            is not None
        )


def test_pack_accepts_missing_relief_candidate():
    from taxtreat.tools.build_global_cz_outbound_review_registry import (
        build_pack,
    )

    domestic_scope = {
        "recipient_country": "XX",
        "recipient_country_name": "Test country",
        "income_type": "dividend",
        "consolidation_blockers": [],
        "domestic_rate_candidate": {
            "source_id": "DOMESTIC-SOURCE"
        },
        "relief_candidate": None,
    }

    pack = build_pack(
        domestic_scope,
        chain=None,
        protocol=None,
        mli_effects=[],
        batch_row=None,
    )

    assert pack["packet_id"] == (
        "CZ-XX-DIV-LEGAL-REVIEW"
    )
    assert "DOMESTIC-SOURCE" in (
        pack["supporting_source_ids"]
    )
    assert pack["status"] == "awaiting_primary_review"
    assert pack["approval_eligible"] is False
    assert (
        pack["promotable_to_active_rules"]
        is False
    )


def test_pack_accepts_missing_domestic_rate_candidate():
    from taxtreat.tools.build_global_cz_outbound_review_registry import (
        build_pack,
    )

    domestic_scope = {
        "recipient_country": "XY",
        "recipient_country_name": "Test country two",
        "income_type": "interest",
        "consolidation_blockers": [],
        "domestic_rate_candidate": None,
        "relief_candidate": None,
    }

    pack = build_pack(
        domestic_scope,
        chain=None,
        protocol=None,
        mli_effects=[],
        batch_row=None,
    )

    assert pack["supporting_source_ids"] == []
    assert pack["candidate_readiness"] == "blocked"
    assert (
        "missing_instrument_chain_or_priority_review_row"
        in pack["blockers"]
    )


def test_write_outputs_creates_all_global_files(
    tmp_path,
    monkeypatch,
):
    import json

    import taxtreat.tools.build_global_cz_outbound_review_registry as module

    output_dir = tmp_path / "global"
    packs_dir = output_dir / "packs"

    monkeypatch.setattr(
        module,
        "OUTPUT_DIR",
        output_dir,
    )
    monkeypatch.setattr(
        module,
        "PACKS_DIR",
        packs_dir,
    )
    monkeypatch.setattr(
        module,
        "INDEX_PATH",
        output_dir / "global_review_index.json",
    )
    monkeypatch.setattr(
        module,
        "QUEUE_PATH",
        output_dir / "global_review_queue.json",
    )
    monkeypatch.setattr(
        module,
        "COVERAGE_PATH",
        output_dir / "global_review_coverage.json",
    )

    registry = module.build_global_registry()
    module.write_outputs(registry)

    assert module.INDEX_PATH.exists()
    assert module.QUEUE_PATH.exists()
    assert module.COVERAGE_PATH.exists()

    pack_files = list(packs_dir.glob("*.json"))

    assert len(pack_files) == 300

    coverage = json.loads(
        module.COVERAGE_PATH.read_text(
            encoding="utf-8"
        )
    )

    assert coverage["actual_scopes"] == 300
    assert coverage["actual_countries"] == 100
    assert coverage["all_scopes_fail_closed"] is True
    assert coverage["income_type_counts"] == {
        "dividend": 100,
        "interest": 100,
        "royalty": 100,
    }

    queue = json.loads(
        module.QUEUE_PATH.read_text(
            encoding="utf-8"
        )
    )

    assert queue["summary"] == {
        "total_scopes": 300,
        "awaiting_primary_review": 300,
        "awaiting_independent_approval": 0,
        "promotable_scopes": 0,
    }


def test_main_builds_valid_global_registry(
    tmp_path,
    monkeypatch,
):
    import taxtreat.tools.build_global_cz_outbound_review_registry as module

    output_dir = tmp_path / "global"

    monkeypatch.setattr(
        module,
        "OUTPUT_DIR",
        output_dir,
    )
    monkeypatch.setattr(
        module,
        "PACKS_DIR",
        output_dir / "packs",
    )
    monkeypatch.setattr(
        module,
        "INDEX_PATH",
        output_dir / "global_review_index.json",
    )
    monkeypatch.setattr(
        module,
        "QUEUE_PATH",
        output_dir / "global_review_queue.json",
    )
    monkeypatch.setattr(
        module,
        "COVERAGE_PATH",
        output_dir / "global_review_coverage.json",
    )

    module.main()

    assert module.COVERAGE_PATH.exists()


def test_main_rejects_wrong_scope_count(
    tmp_path,
    monkeypatch,
):
    import pytest

    import taxtreat.tools.build_global_cz_outbound_review_registry as module

    output_dir = tmp_path / "wrong-scopes"

    monkeypatch.setattr(
        module,
        "OUTPUT_DIR",
        output_dir,
    )
    monkeypatch.setattr(
        module,
        "PACKS_DIR",
        output_dir / "packs",
    )
    monkeypatch.setattr(
        module,
        "INDEX_PATH",
        output_dir / "global_review_index.json",
    )
    monkeypatch.setattr(
        module,
        "QUEUE_PATH",
        output_dir / "global_review_queue.json",
    )
    monkeypatch.setattr(
        module,
        "COVERAGE_PATH",
        output_dir / "global_review_coverage.json",
    )

    registry = module.build_global_registry()
    registry["packs"] = registry["packs"][:-1]

    monkeypatch.setattr(
        module,
        "build_global_registry",
        lambda: registry,
    )

    with pytest.raises(
        RuntimeError,
        match="exactly 300 scopes",
    ):
        module.main()


def test_main_rejects_wrong_country_count(
    tmp_path,
    monkeypatch,
):
    import pytest

    import taxtreat.tools.build_global_cz_outbound_review_registry as module

    output_dir = tmp_path / "wrong-countries"

    monkeypatch.setattr(
        module,
        "OUTPUT_DIR",
        output_dir,
    )
    monkeypatch.setattr(
        module,
        "PACKS_DIR",
        output_dir / "packs",
    )
    monkeypatch.setattr(
        module,
        "INDEX_PATH",
        output_dir / "global_review_index.json",
    )
    monkeypatch.setattr(
        module,
        "QUEUE_PATH",
        output_dir / "global_review_queue.json",
    )
    monkeypatch.setattr(
        module,
        "COVERAGE_PATH",
        output_dir / "global_review_coverage.json",
    )

    registry = module.build_global_registry()

    for pack in registry["packs"]:
        if pack["recipient_country"] == "US":
            pack["recipient_country"] = "DE"

    monkeypatch.setattr(
        module,
        "build_global_registry",
        lambda: registry,
    )

    with pytest.raises(
        RuntimeError,
        match="exactly 100 countries",
    ):
        module.main()


def test_main_rejects_non_fail_closed_scope(
    tmp_path,
    monkeypatch,
):
    import pytest

    import taxtreat.tools.build_global_cz_outbound_review_registry as module

    output_dir = tmp_path / "not-fail-closed"

    monkeypatch.setattr(
        module,
        "OUTPUT_DIR",
        output_dir,
    )
    monkeypatch.setattr(
        module,
        "PACKS_DIR",
        output_dir / "packs",
    )
    monkeypatch.setattr(
        module,
        "INDEX_PATH",
        output_dir / "global_review_index.json",
    )
    monkeypatch.setattr(
        module,
        "QUEUE_PATH",
        output_dir / "global_review_queue.json",
    )
    monkeypatch.setattr(
        module,
        "COVERAGE_PATH",
        output_dir / "global_review_coverage.json",
    )

    registry = module.build_global_registry()
    registry["packs"][0][
        "promotable_to_active_rules"
    ] = True

    monkeypatch.setattr(
        module,
        "build_global_registry",
        lambda: registry,
    )

    with pytest.raises(
        RuntimeError,
        match="fail-closed",
    ):
        module.main()


def test_duplicate_scope_is_rejected():
    import pytest

    from taxtreat.tools.build_global_cz_outbound_review_registry import (
        index_by_scope,
    )

    rows = [
        {
            "recipient_country": "DE",
            "income_type": "dividend",
        },
        {
            "recipient_country": "DE",
            "income_type": "dividend",
        },
    ]

    with pytest.raises(
        ValueError,
        match="Duplicate scope",
    ):
        index_by_scope(rows)
