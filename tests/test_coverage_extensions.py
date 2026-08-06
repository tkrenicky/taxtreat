from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from taxtreat.consolidation import domestic_eu_effects
from taxtreat.consolidation import mli_effects
from taxtreat.db.repository import (
    AmbiguousArticleError,
    TreatyRepository,
    get_article_paragraph_texts,
)
from taxtreat.engine.models import Rule
from taxtreat.services.rule_builder import RuleBuilder


def test_domestic_candidate_rejects_unknown_relief_country(
    monkeypatch,
):
    monkeypatch.setattr(
        domestic_eu_effects,
        "RELIEF_ELIGIBLE_PARTNERS",
        {"XX"},
    )
    monkeypatch.setattr(
        domestic_eu_effects,
        "load_partner_registry",
        lambda: [
            {
                "iso2": "DE",
                "country": "Germany",
            }
        ],
    )

    with pytest.raises(
        ValueError,
        match="outside the treaty registry",
    ):
        domestic_eu_effects.build_domestic_eu_candidates()


def test_domestic_candidate_rejects_wrong_eu_count(
    monkeypatch,
):
    monkeypatch.setattr(
        domestic_eu_effects,
        "RELIEF_ELIGIBLE_PARTNERS",
        {"DE"},
    )
    monkeypatch.setattr(
        domestic_eu_effects,
        "EU_MEMBER_PARTNERS",
        {"DE"},
    )
    monkeypatch.setattr(
        domestic_eu_effects,
        "load_partner_registry",
        lambda: [
            {
                "iso2": "DE",
                "country": "Germany",
            }
        ],
    )

    with pytest.raises(
        ValueError,
        match="Expected 26 EU Member State",
    ):
        domestic_eu_effects.build_domestic_eu_candidates()


def test_domestic_candidate_rejects_wrong_relief_count(
    monkeypatch,
):
    partner_codes = {
        f"X{index:02d}"
        for index in range(30)
    }

    partners = [
        {
            "iso2": code,
            "country": code,
        }
        for code in sorted(partner_codes)
    ]

    monkeypatch.setattr(
        domestic_eu_effects,
        "load_partner_registry",
        lambda: partners,
    )
    monkeypatch.setattr(
        domestic_eu_effects,
        "EU_MEMBER_PARTNERS",
        set(sorted(partner_codes)[:26]),
    )
    monkeypatch.setattr(
        domestic_eu_effects,
        "RELIEF_ELIGIBLE_PARTNERS",
        set(sorted(partner_codes)[:29]),
    )

    with pytest.raises(
        ValueError,
        match="Expected 30 section 19",
    ):
        domestic_eu_effects.build_domestic_eu_candidates()


def test_write_domestic_candidates(tmp_path):
    target = tmp_path / "nested" / "domestic.json"
    payload = {"scopes": []}

    domestic_eu_effects.write_domestic_eu_candidates(
        payload,
        target,
    )

    assert json.loads(
        target.read_text(encoding="utf-8")
    ) == payload


def test_link_parser_collects_anchor_links():
    parser = mli_effects._LinkParser()
    parser.feed(
        '<a href="/one.pdf">One</a>'
        '<div href="/ignored.pdf"></div>'
        '<a>Missing</a>'
        '<a href="/two.pdf?a=1&amp;b=2">Two</a>'
    )

    assert parser.links == [
        "/one.pdf",
        "/two.pdf?a=1&b=2",
    ]


def test_pdf_url_accepts_official_attachment_patterns():
    assert mli_effects._pdf_url(
        "https://example.test/page",
        (
            b'<a href="/assets/attachments/'
            b'notice">Notice</a>'
        ),
    ) == (
        "https://example.test/assets/"
        "attachments/notice"
    )

    assert mli_effects._pdf_url(
        "https://example.test/page",
        b'<a href="/assets/cs/media/notice">Notice</a>',
    ) == (
        "https://example.test/assets/"
        "cs/media/notice"
    )


def test_pdf_url_rejects_page_without_pdf():
    with pytest.raises(
        ValueError,
        match="No official PDF",
    ):
        mli_effects._pdf_url(
            "https://example.test/page",
            b"<html></html>",
        )


def test_pdf_text_uses_pdftotext(monkeypatch):
    called = {}

    def fake_run(
        command,
        *,
        input,
        stdout,
        stderr,
        check,
    ):
        called["command"] = command
        called["input"] = input
        called["check"] = check
        return SimpleNamespace(
            stdout=b"Extracted text",
        )

    monkeypatch.setattr(
        mli_effects.subprocess,
        "run",
        fake_run,
    )

    assert mli_effects._pdf_text(
        b"PDF bytes"
    ) == "Extracted text"
    assert called == {
        "command": [
            "pdftotext",
            "-layout",
            "-",
            "-",
        ],
        "input": b"PDF bytes",
        "check": True,
    }


def test_wht_excerpt_rejects_missing_date():
    with pytest.raises(
        ValueError,
        match="effective date",
    ):
        mli_effects._wht_excerpt(
            "Text without relevant wording",
            2026,
        )


def test_build_mli_effects_rejects_multiple_notices():
    inventory = {
        "source_page": {
            "legal_data_cutoff": "2026-08-06",
        },
        "partners": [
            {
                "iso2": "DE",
                "country": "Germany",
                "related_instruments": [
                    {
                        "source_type": (
                            "mli_synthesised_notice"
                        ),
                        "source_id": "ONE",
                        "url": "https://one.test",
                    },
                    {
                        "source_type": (
                            "mli_synthesised_notice"
                        ),
                        "source_id": "TWO",
                        "url": "https://two.test",
                    },
                ],
            }
        ],
    }

    with pytest.raises(
        ValueError,
        match="exactly one MLI notice",
    ):
        mli_effects.build_mli_effects(
            inventory,
            documents={},
        )


def test_build_mli_effects_rejects_unknown_year(
    monkeypatch,
):
    monkeypatch.setattr(
        mli_effects,
        "EXPECTED_CZECH_WHT_YEAR",
        {},
    )

    inventory = {
        "source_page": {
            "legal_data_cutoff": "2026-08-06",
        },
        "partners": [
            {
                "iso2": "XX",
                "country": "Example",
                "related_instruments": [
                    {
                        "source_type": (
                            "mli_synthesised_notice"
                        ),
                        "source_id": "NOTICE",
                        "url": "https://notice.test",
                    }
                ],
            }
        ],
    }

    with pytest.raises(
        ValueError,
        match="No independently checked",
    ):
        mli_effects.build_mli_effects(
            inventory,
            documents={},
        )


def test_build_mli_effects_rejects_wrong_total(
    monkeypatch,
):
    monkeypatch.setattr(
        mli_effects,
        "EXPECTED_CZECH_WHT_YEAR",
        {"DE": 2026},
    )
    monkeypatch.setattr(
        mli_effects,
        "_wht_excerpt",
        lambda text, year: "excerpt",
    )

    inventory = {
        "source_page": {
            "legal_data_cutoff": "2026-08-06",
        },
        "partners": [
            {
                "iso2": "DE",
                "country": "Germany",
                "related_instruments": [
                    {
                        "source_type": (
                            "mli_synthesised_notice"
                        ),
                        "source_id": "NOTICE",
                        "url": "https://notice.test",
                    }
                ],
            }
        ],
    }

    with pytest.raises(
        ValueError,
        match="Expected 62 official MLI notices",
    ):
        mli_effects.build_mli_effects(
            inventory,
            documents={
                "https://notice.test": (
                    "https://notice.test/file.pdf",
                    "text",
                )
            },
        )


def test_fetch_mli_documents(
    monkeypatch,
):
    inventory = {
        "partners": [
            {
                "related_instruments": [
                    {
                        "source_type": (
                            "mli_synthesised_notice"
                        ),
                        "url": "https://notice.test",
                    },
                    {
                        "source_type": "protocol",
                        "url": "https://ignored.test",
                    },
                ]
            }
        ]
    }

    monkeypatch.setattr(
        mli_effects,
        "_download",
        lambda url: (
            b'<a href="/file.pdf">PDF</a>'
            if url == "https://notice.test"
            else b"PDF bytes"
        ),
    )
    monkeypatch.setattr(
        mli_effects,
        "_pdf_text",
        lambda value: "Extracted",
    )

    assert mli_effects.fetch_mli_documents(
        inventory
    ) == {
        "https://notice.test": (
            "https://notice.test/file.pdf",
            "Extracted",
        )
    }


def test_refresh_and_write_mli_effects(
    tmp_path,
    monkeypatch,
):
    inventory_path = tmp_path / "inventory.json"
    output_path = tmp_path / "nested" / "effects.json"

    inventory = {
        "partners": [],
        "source_page": {
            "legal_data_cutoff": "2026-08-06",
        },
    }

    inventory_path.write_text(
        json.dumps(inventory),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        mli_effects,
        "fetch_mli_documents",
        lambda payload: {},
    )
    monkeypatch.setattr(
        mli_effects,
        "build_mli_effects",
        lambda payload, documents: {
            "effects": [],
        },
    )

    payload = mli_effects.refresh_mli_effects(
        inventory_path=inventory_path,
    )

    assert payload == {"effects": []}

    mli_effects.write_mli_effects(
        payload,
        output_path,
    )

    assert json.loads(
        output_path.read_text(encoding="utf-8")
    ) == payload


def _repository_database(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE articles (
            id INTEGER PRIMARY KEY,
            treaty_version_id INTEGER NOT NULL,
            article_number INTEGER NOT NULL,
            title TEXT
        );

        CREATE TABLE paragraphs (
            id INTEGER PRIMARY KEY,
            article_id INTEGER NOT NULL,
            paragraph_number TEXT,
            text TEXT NOT NULL
        );

        INSERT INTO articles
            (id, treaty_version_id, article_number, title)
        VALUES
            (1, 100, 10, 'Dividends'),
            (2, 200, 10, 'Other dividends');

        INSERT INTO paragraphs
            (id, article_id, paragraph_number, text)
        VALUES
            (1, 1, '1', 'First'),
            (2, 2, '1', 'Second');
        """
    )
    connection.commit()
    connection.close()


def test_paragraph_text_lookup_with_treaty_version(
    tmp_path,
):
    db_path = tmp_path / "repository.db"
    _repository_database(db_path)

    connection = sqlite3.connect(db_path)

    assert get_article_paragraph_texts(
        connection,
        10,
        treaty_version_id=100,
    ) == ["First"]

    with pytest.raises(
        AmbiguousArticleError,
    ):
        get_article_paragraph_texts(
            connection,
            10,
        )

    connection.close()


def test_rule_builder_skips_other_and_missing_extractors(
    monkeypatch,
):
    class FakeConnection:
        def execute(self, query, parameters):
            return self

        def fetchall(self):
            return [
                {
                    "id": 1,
                    "article_number": 10,
                    "title": "Other",
                },
                {
                    "id": 2,
                    "article_number": 11,
                    "title": "Interest",
                },
                {
                    "id": 3,
                    "article_number": 12,
                    "title": "Royalties",
                },
            ]

    class FakeRepository:
        conn = FakeConnection()

        def get_full_article_text(
            self,
            *,
            article_id,
        ):
            return f"TEXT {article_id}"

    class FakeRegistry:
        def get(self, article_type):
            if article_type == "interest":
                return None

            return lambda text: {
                "not": "a Rule instance",
            }

    classifications = iter(
        [
            "other",
            "interest",
            "royalty",
        ]
    )

    monkeypatch.setattr(
        "taxtreat.services.rule_builder."
        "classify_article",
        lambda title, text: next(classifications),
    )

    builder = RuleBuilder(
        FakeRepository(),
        registry=FakeRegistry(),
    )

    assert builder.build_rules(1) == []


def test_protocol_effects_rejects_source_mismatch(
    tmp_path,
    monkeypatch,
):
    from taxtreat.consolidation import protocol_effects

    inventory = {
        "source_page": {
            "legal_data_cutoff": "2026-08-06",
        },
        "partners": [
            {
                "iso2": "XX",
                "protocol_listed": True,
                "mli_listed": False,
                "related_instruments": [
                    {
                        "source_type": "protocol",
                        "source_id": "OFFICIAL",
                        "label": "Official protocol",
                        "url": "https://example.test/protocol",
                        "authority": "Authority",
                    }
                ],
            }
        ],
    }

    base_payload = {
        "scopes": [
            {
                "recipient_country": "XX",
                "income_type": income_type,
                "rate_candidates": [],
            }
            for income_type in (
                "dividend",
                "interest",
                "royalty",
            )
        ]
    }

    inventory_path = tmp_path / "inventory.json"
    base_path = tmp_path / "base.json"

    inventory_path.write_text(
        json.dumps(inventory),
        encoding="utf-8",
    )
    base_path.write_text(
        json.dumps(base_payload),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        protocol_effects,
        "PROTOCOL_DOCUMENTS",
        {
            "XX": [
                {
                    "source_id": "CURATED",
                    "entry_into_force": "2020-01-01",
                    "candidate_effective_from": "2021-01-01",
                    "source_document_sha256": "a" * 64,
                }
            ]
        },
    )
    monkeypatch.setattr(
        protocol_effects,
        "PROTOCOL_EFFECTS",
        {
            "XX": {
                income_type: {
                    "effect_kind": "test",
                    "evidence_anchor": "test",
                }
                for income_type in (
                    "dividend",
                    "interest",
                    "royalty",
                )
            }
        },
    )

    with pytest.raises(
        ValueError,
        match="Protocol source mismatch",
    ):
        protocol_effects.build_protocol_effects(
            inventory_path=inventory_path,
            base_candidates_path=base_path,
        )


def test_protocol_effects_rejects_wrong_output_total(
    tmp_path,
    monkeypatch,
):
    from taxtreat.consolidation import protocol_effects

    inventory = {
        "source_page": {
            "legal_data_cutoff": "2026-08-06",
        },
        "partners": [
            {
                "iso2": "XX",
                "protocol_listed": True,
                "mli_listed": True,
                "related_instruments": [
                    {
                        "source_type": "protocol",
                        "source_id": "P1",
                        "label": "Protocol",
                        "url": "https://example.test/protocol",
                        "authority": "Authority",
                    }
                ],
            }
        ],
    }

    base_payload = {
        "scopes": [
            {
                "recipient_country": "XX",
                "income_type": income_type,
                "rate_candidates": [
                    {
                        "rate": 5.0,
                        "conditions": [],
                    }
                ],
            }
            for income_type in (
                "dividend",
                "interest",
                "royalty",
            )
        ]
    }

    inventory_path = tmp_path / "inventory.json"
    base_path = tmp_path / "base.json"

    inventory_path.write_text(
        json.dumps(inventory),
        encoding="utf-8",
    )
    base_path.write_text(
        json.dumps(base_payload),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        protocol_effects,
        "PROTOCOL_DOCUMENTS",
        {
            "XX": [
                {
                    "source_id": "P1",
                    "entry_into_force": "2020-01-01",
                    "candidate_effective_from": "2021-01-01",
                    "source_document_sha256": "a" * 64,
                }
            ]
        },
    )
    monkeypatch.setattr(
        protocol_effects,
        "PROTOCOL_EFFECTS",
        {
            "XX": {
                income_type: {
                    "effect_kind": "test",
                    "evidence_anchor": "test",
                }
                for income_type in (
                    "dividend",
                    "interest",
                    "royalty",
                )
            }
        },
    )
    monkeypatch.setattr(
        protocol_effects,
        "LATER_STATUS_INSTRUMENTS",
        {
            "XX": "LATER-STATUS",
        },
    )

    with pytest.raises(
        ValueError,
        match="Expected 12 protocol instruments",
    ):
        protocol_effects.build_protocol_effects(
            inventory_path=inventory_path,
            base_candidates_path=base_path,
        )


def test_write_protocol_effects(tmp_path):
    from taxtreat.consolidation.protocol_effects import (
        write_protocol_effects,
    )

    target = tmp_path / "nested" / "protocols.json"
    payload = {
        "documents": [],
        "scopes": [],
    }

    write_protocol_effects(payload, target)

    assert json.loads(
        target.read_text(encoding="utf-8")
    ) == payload


@pytest.mark.parametrize(
    "payload, message",
    [
        (
            ["not-an-object"],
            "must be an object",
        ),
        (
            [
                {
                    "country": "",
                    "iso2": "DE",
                    "parsed_file": "de.json",
                }
            ],
            "requires country",
        ),
        (
            [
                {
                    "country": "Germany",
                    "iso2": "d1",
                    "parsed_file": "de.json",
                }
            ],
            "Invalid partner ISO-like code",
        ),
        (
            [
                {
                    "country": "Germany",
                    "iso2": "DE",
                    "parsed_file": "de.txt",
                }
            ],
            "Invalid parsed treaty filename",
        ),
        (
            [
                {
                    "country": "One",
                    "iso2": "DE",
                    "parsed_file": "same.json",
                },
                {
                    "country": "Two",
                    "iso2": "FR",
                    "parsed_file": "same.json",
                },
            ],
            "Duplicate parsed treaty filename",
        ),
    ],
)
def test_additional_partner_registry_validation(
    tmp_path,
    payload,
    message,
):
    from taxtreat.registry.legal_scope import (
        load_partner_registry,
    )

    path = tmp_path / "registry.json"
    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match=message,
    ):
        load_partner_registry(path)


def test_be_dividend_markdown_without_protocols():
    from taxtreat.tools.build_be_dividend_primary_review_pack import (
        build_markdown,
        build_review_pack,
    )

    payload = build_review_pack()
    payload["protocols"] = {
        "documents": [],
    }

    markdown = build_markdown(payload)

    assert (
        "- Nebyl nalezen žádný protokol."
        in markdown
    )


def test_be_dividend_main_writes_outputs(
    tmp_path,
    monkeypatch,
):
    import taxtreat.tools.build_be_dividend_primary_review_pack as module

    output_json = tmp_path / "review.json"
    output_md = tmp_path / "review.md"

    monkeypatch.setattr(
        module,
        "OUTPUT_JSON",
        output_json,
    )
    monkeypatch.setattr(
        module,
        "OUTPUT_MD",
        output_md,
    )
    monkeypatch.setattr(
        module,
        "ROOT",
        tmp_path,
    )

    module.main()

    assert output_json.exists()
    assert output_md.exists()

    payload = json.loads(
        output_json.read_text(encoding="utf-8")
    )

    assert payload["status"] == (
        "awaiting_primary_review"
    )
    assert (
        payload["promotable_to_active_rules"]
        is False
    )


def test_mli_download_reads_response(
    monkeypatch,
):
    from taxtreat.consolidation import mli_effects

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(
            self,
            exc_type,
            exc_value,
            traceback,
        ):
            return False

        def read(self):
            return b"official-document"

    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["user_agent"] = request.headers[
            "User-agent"
        ]
        return FakeResponse()

    monkeypatch.setattr(
        mli_effects,
        "urlopen",
        fake_urlopen,
    )

    result = mli_effects._download(
        "https://example.test/document"
    )

    assert result == b"official-document"
    assert captured == {
        "url": "https://example.test/document",
        "timeout": 60,
        "user_agent": (
            "TaxTreat-official-source-refresh/1.0"
        ),
    }


@pytest.mark.parametrize(
    "title, expected",
    [
        ("DIVIDENDY", "dividend"),
        ("ÚROKY", "interest"),
        ("LICENČNÍ POPLATKY", "royalty"),
    ],
)
def test_article_classifier_fallback_income_types(
    monkeypatch,
    title,
    expected,
):
    import taxtreat.engine.article_classifier as module

    monkeypatch.setattr(
        module,
        "article_type",
        lambda payload: None,
    )

    assert module.classify_article(title) == expected
