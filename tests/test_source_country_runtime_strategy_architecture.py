from pathlib import Path

from taxtreat.countries.registry import get_country_config


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_dataset_strategy_is_country_configured():
    assert (
        get_country_config("CZ").runtime_dataset_strategy
        == "canonical_stage6"
    )
    assert (
        get_country_config("SK").runtime_dataset_strategy
        == "source_country_manifest"
    )


def test_runtime_metadata_has_no_direct_cz_branch():
    text = (
        ROOT
        / "taxtreat"
        / "services"
        / "source_country_runtime_metadata.py"
    ).read_text(encoding="utf-8")

    assert 'code == "CZ"' not in text


def test_release_gate_has_no_direct_cz_branch():
    text = (
        ROOT
        / "taxtreat"
        / "services"
        / "source_country_release_gate.py"
    ).read_text(encoding="utf-8")

    assert 'code == "CZ"' not in text


def test_localized_context_has_no_direct_sk_branch():
    text = (
        ROOT
        / "taxtreat"
        / "services"
        / "reporting"
        / "localized_context.py"
    ).read_text(encoding="utf-8")

    assert 'source_country == "SK"' not in text
