from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest

from taxtreat.consolidation.base_candidates import build_base_candidates
from taxtreat.consolidation import mf_inventory, mli_effects
from taxtreat.consolidation.mf_inventory import build_inventory


ROOT = Path(__file__).parents[1]
INVENTORY = ROOT / "data" / "legal_consolidation" / "mf_inventory.json"
CANDIDATES = (
    ROOT
    / "data"
    / "legal_consolidation"
    / "remaining_294_base_candidates.json"
)
MLI_EFFECTS = (
    ROOT / "data" / "legal_consolidation" / "mli_wht_effects.json"
)


def test_committed_mf_inventory_covers_every_treaty_partner():
    payload = json.loads(INVENTORY.read_text(encoding="utf-8"))
    partners = payload["partners"]

    assert payload["source_page"]["legal_data_cutoff"] == "2026-02-04"
    assert len(partners) == 100
    assert len({partner["iso2"] for partner in partners}) == 100
    assert all(partner["base_instruments"] for partner in partners)
    assert all(
        source["url"].startswith("https://")
        for partner in partners
        for group in (
            partner["base_instruments"],
            partner["financial_reporter_sources"],
            partner["related_instruments"],
        )
        for source in group
    )
    assert sum(partner["mli_listed"] for partner in partners) == 71
    assert sum(partner["protocol_listed"] for partner in partners) == 13


def test_committed_base_candidates_cover_exactly_the_remaining_294_scopes():
    payload = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    scopes = payload["scopes"]

    assert len(scopes) == 294
    assert {scope["recipient_country"] for scope in scopes}.isdisjoint(
        {"AT", "CH"}
    )
    assert len({scope["recipient_country"] for scope in scopes}) == 98
    assert {
        (scope["recipient_country"], scope["income_type"])
        for scope in scopes
    } == {
        (country, income_type)
        for country in {scope["recipient_country"] for scope in scopes}
        for income_type in {"dividend", "interest", "royalty"}
    }
    assert all(scope["verification_status"] == "needs_review" for scope in scopes)
    assert all("independent_legal_review" in scope["consolidation_blockers"] for scope in scopes)
    assert all(
        hashlib.sha256(scope["article_text"].encode("utf-8")).hexdigest()
        == scope["article_text_sha256"]
        for scope in scopes
    )


def test_known_false_percentages_are_quarantined_not_promoted():
    scopes = json.loads(CANDIDATES.read_text(encoding="utf-8"))["scopes"]
    chile_interest = next(
        scope
        for scope in scopes
        if scope["recipient_country"] == "CL"
        and scope["income_type"] == "interest"
    )
    germany_dividend = next(
        scope
        for scope in scopes
        if scope["recipient_country"] == "DE"
        and scope["income_type"] == "dividend"
    )

    assert {row["rate"] for row in chile_interest["rate_candidates"]} == {4.0, 15.0}
    assert [row["rate"] for row in chile_interest["discarded_rate_candidates"]] == [50.0]
    assert {row["rate"] for row in germany_dividend["rate_candidates"]} == {
        5.0,
        15.0,
        20.0,
    }
    assert "dividend_special_cases_not_fully_structured" in germany_dividend["risk_flags"]


def test_candidate_generation_is_deterministic():
    committed = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    assert build_base_candidates() == committed


def test_official_mli_wht_effect_candidates_are_hashed_and_date_sensitive():
    payload = json.loads(MLI_EFFECTS.read_text(encoding="utf-8"))
    effects = payload["effects"]
    by_code = {effect["recipient_country"]: effect for effect in effects}

    assert len(effects) == 62
    assert len(by_code) == 62
    assert by_code["AT"]["effective_from"] == "2021-01-01"
    assert by_code["CH"]["effective_from"] == "2022-01-01"
    assert by_code["DE"]["effective_from"] == "2026-01-01"
    assert by_code["ID"]["effective_from"] == "2027-01-01"
    assert all(effect["verification_status"] == "needs_review" for effect in effects)
    assert all(
        hashlib.sha256(effect["source_excerpt"].encode("utf-8")).hexdigest()
        == effect["source_excerpt_sha256"]
        for effect in effects
    )
    assert all(
        effect["source_page_url"].startswith("https://mf.gov.cz/")
        and effect["source_pdf_url"].startswith("https://mf.gov.cz/")
        for effect in effects
    )


def test_mf_html_parser_rejects_incomplete_partner_inventory():
    html = """
    <html><body><p>podle stavu k 4.2.2026</p><table>
      <tr><th>Smluvní stát</th><th>Platnost ode dne</th><th>Sbírka</th>
          <th>Finanční zpravodaj</th><th>Poznámka</th></tr>
      <tr><td>Albánie</td><td>10.9.1996</td>
          <td><a href="/base.pdf">270/1996 Sb.</a></td><td></td><td></td></tr>
    </table></body></html>
    """

    try:
        build_inventory(html, retrieved_at="2026-08-03")
    except ValueError as exc:
        assert "inventory mismatch" in str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("Incomplete inventory was accepted.")


def _synthetic_complete_mf_html() -> str:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    rows = []
    for partner in inventory["partners"]:
        year, month, day = partner["entry_into_force"].split("-")

        def links(items):
            return " ".join(
                f'<a href="{item["url"]}">{item["label"]}</a>'
                for item in items
            )

        rows.append(
            "<tr>"
            f'<td>{partner["country"]}</td>'
            f"<td>{int(day)}.{int(month)}.{year}</td>"
            f'<td>{links(partner["base_instruments"])}</td>'
            f'<td>{links(partner["financial_reporter_sources"])}</td>'
            f'<td>{links(partner["related_instruments"])}</td>'
            "</tr>"
        )
    return (
        "<html><body><p>podle stavu k 4.2.2026</p><table>"
        "<tr><th>Smluvní stát</th><th>Platnost ode dne</th>"
        "<th>Sbírka</th><th>Finanční zpravodaj</th><th>Poznámka</th></tr>"
        + "".join(rows)
        + "</table></body></html>"
    )


def test_mf_html_parser_complete_path_and_write(tmp_path):
    payload = build_inventory(
        _synthetic_complete_mf_html(),
        retrieved_at="2026-08-03",
    )
    target = tmp_path / "inventory.json"
    mf_inventory.write_inventory(payload, target)

    assert len(payload["partners"]) == 100
    assert payload["source_page"]["retrieved_at"] == "2026-08-03"
    assert json.loads(target.read_text(encoding="utf-8")) == payload


@pytest.mark.parametrize(
    "html, message",
    [
        ("<html><p>podle stavu k 4.2.2026</p></html>", "was not found"),
        (
            "<p>podle stavu k 4.2.2026</p><table>"
            "<tr><th>Smluvní stát</th></tr><tr><td>Albánie</td></tr></table>",
            "five cells",
        ),
        (
            "<p>podle stavu k 4.2.2026</p><table>"
            "<tr><th>Smluvní stát</th><th>x</th><th>x</th><th>x</th><th>x</th></tr>"
            "<tr><td>Unknown</td><td>1.1.2020</td><td>x</td><td>x</td><td>x</td></tr>"
            "</table>",
            "unknown partner",
        ),
    ],
)
def test_mf_html_parser_structural_failures(html, message):
    with pytest.raises(ValueError, match=message):
        build_inventory(html, retrieved_at="2026-08-03")


def test_mf_inventory_fetch_uses_official_page(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b"official page"

    monkeypatch.setattr(mf_inventory, "urlopen", lambda *args, **kwargs: Response())
    assert mf_inventory.fetch_overview() == "official page"


def _synthetic_mli_documents(inventory):
    years_by_url = {}
    for partner in inventory["partners"]:
        notice = next(
            (
                source
                for source in partner["related_instruments"]
                if source["source_type"] == "mli_synthesised_notice"
            ),
            None,
        )
        if notice is None:
            continue
        year = mli_effects.EXPECTED_CZECH_WHT_YEAR[partner["iso2"]]
        years_by_url.setdefault(notice["url"], set()).add(year)
    return {
        url: (
            url + ".pdf",
            "\n".join(
                "Článek 2. Pokud jde o daně vybírané srážkou u zdroje, "
                f"použijí se od 1. ledna {year} nebo později."
                for year in sorted(years)
            ),
        )
        for url, years in years_by_url.items()
    }


def test_mli_candidate_builder_complete_path_and_write(tmp_path):
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    payload = mli_effects.build_mli_effects(
        inventory,
        documents=_synthetic_mli_documents(inventory),
    )
    target = tmp_path / "mli.json"
    mli_effects.write_mli_effects(payload, target)

    assert len(payload["effects"]) == 62
    assert json.loads(target.read_text(encoding="utf-8")) == payload


def test_mli_candidate_builder_rejects_missing_expected_date(monkeypatch):
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    documents = _synthetic_mli_documents(inventory)
    monkeypatch.delitem(mli_effects.EXPECTED_CZECH_WHT_YEAR, "AL")
    with pytest.raises(ValueError, match="No independently checked"):
        mli_effects.build_mli_effects(inventory, documents=documents)


def test_mli_pdf_link_and_fetch_helpers(monkeypatch):
    page = "https://mf.gov.cz/page"
    assert mli_effects._pdf_url(
        page,
        b'<a href="/assets/attachments/source.pdf">PDF</a>',
    ) == "https://mf.gov.cz/assets/attachments/source.pdf"
    with pytest.raises(ValueError, match="No official PDF"):
        mli_effects._pdf_url(page, b"<html></html>")

    monkeypatch.setattr(
        mli_effects,
        "_download",
        lambda url: (
            b'<a href="/assets/attachments/source.pdf">PDF</a>'
            if url == page
            else b"pdf bytes"
        ),
    )
    monkeypatch.setattr(mli_effects, "_pdf_text", lambda value: "pdf text")
    inventory = {
        "partners": [
            {
                "related_instruments": [
                    {"source_type": "mli_synthesised_notice", "url": page}
                ]
            }
        ]
    }
    assert mli_effects.fetch_mli_documents(inventory) == {
        page: (
            "https://mf.gov.cz/assets/attachments/source.pdf",
            "pdf text",
        )
    }
