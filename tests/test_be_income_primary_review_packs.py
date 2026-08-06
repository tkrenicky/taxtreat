import json
import pytest

from taxtreat.tools.build_be_income_primary_review_packs import (
    build_markdown,
    build_review_pack,
    output_paths,
)


@pytest.mark.parametrize(
    ("income_type", "packet_id"),
    [
        ("interest", "CZ-BE-INT-LEGAL-REVIEW"),
        ("royalty", "CZ-BE-ROY-LEGAL-REVIEW"),
    ],
)
def test_review_pack_targets_expected_scope(
    income_type,
    packet_id,
):
    payload = build_review_pack(income_type)

    assert payload["packet_id"] == packet_id
    assert payload["recipient_country"] == "BE"
    assert payload["income_type"] == income_type
    assert len(payload["review_row_sha256"]) == 64


@pytest.mark.parametrize(
    "income_type",
    ["interest", "royalty"],
)
def test_review_pack_contains_all_legal_layers(
    income_type,
):
    payload = build_review_pack(income_type)

    assert payload["treaty"]["rate_candidates"]
    assert payload["domestic_and_eu"][
        "domestic_rate_candidate"
    ]
    assert "protocols" in payload
    assert "mli_effects" in payload


@pytest.mark.parametrize(
    "income_type",
    ["interest", "royalty"],
)
def test_review_pack_remains_fail_closed(
    income_type,
):
    payload = build_review_pack(income_type)

    assert payload["status"] == "awaiting_primary_review"
    assert payload["promotable_to_active_rules"] is False
    assert payload["review_fields"]["review_outcome"] is None
    assert payload["policy"]["fail_closed"] is True


@pytest.mark.parametrize(
    "income_type",
    ["interest", "royalty"],
)
def test_markdown_contains_required_sections(
    income_type,
):
    markdown = build_markdown(
        build_review_pack(income_type)
    )

    assert (
        f"# Primary legal review – CZ → BE / {income_type}"
        in markdown
    )
    assert "## 1. Základní smlouva" in markdown
    assert "## 4. Protokoly" in markdown
    assert "## 5. MLI" in markdown
    assert "## 6. Otázky pro primary review" in markdown
    assert "## 7. Výsledek primary review" in markdown


def test_invalid_income_type_is_rejected():
    with pytest.raises(
        ValueError,
        match="Unsupported income type",
    ):
        build_review_pack("dividend")


@pytest.mark.parametrize(
    "income_type",
    ["interest", "royalty"],
)
def test_output_paths_are_income_specific(
    income_type,
):
    output_json, output_md = output_paths(
        income_type
    )

    assert income_type in output_json.name
    assert income_type in output_md.name


def test_rate_lines_handles_empty_candidates():
    from taxtreat.tools.build_be_income_primary_review_packs import (
        rate_lines,
    )

    assert rate_lines([]) == [
        "- Nebyly nalezeny žádné kandidátní sazby."
    ]


def test_find_scope_rejects_missing_scope():
    from taxtreat.tools.build_be_income_primary_review_packs import (
        find_scope,
    )

    with pytest.raises(
        ValueError,
        match="Expected one BE/interest scope, found 0",
    ):
        find_scope(
            [],
            country="BE",
            income_type="interest",
        )


def test_markdown_handles_no_protocol_documents():
    payload = build_review_pack("interest")
    payload["protocols"] = {"documents": []}

    markdown = build_markdown(payload)

    assert "- Nebyl nalezen žádný protokol." in markdown


def test_main_writes_both_review_packs(
    tmp_path,
    monkeypatch,
):
    import taxtreat.tools.build_be_income_primary_review_packs as module

    def temporary_output_paths(income_type):
        return (
            tmp_path / f"{income_type}.json",
            tmp_path / f"{income_type}.md",
        )

    monkeypatch.setattr(
        module,
        "output_paths",
        temporary_output_paths,
    )
    monkeypatch.setattr(
        module,
        "ROOT",
        tmp_path,
    )

    module.main()

    for income_type in ("interest", "royalty"):
        json_path = tmp_path / f"{income_type}.json"
        markdown_path = tmp_path / f"{income_type}.md"

        assert json_path.is_file()
        assert markdown_path.is_file()

        payload = json.loads(
            json_path.read_text(encoding="utf-8")
        )

        assert payload["income_type"] == income_type
        assert payload["status"] == "awaiting_primary_review"
        assert payload["promotable_to_active_rules"] is False
        assert (
            f"CZ → BE / {income_type}"
            in markdown_path.read_text(encoding="utf-8")
        )
