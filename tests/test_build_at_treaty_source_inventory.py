from taxtreat.tools.build_at_treaty_source_inventory import build_inventory, parse_bmf_treaty_list


SAMPLE = """
<html><body>
  <h2>A</h2>
  <h3>Ägypten / Egypt</h3>
  <p>Unterzeichnung / Date of Signature | 16.10.1962</p>
  <p>Inkrafttreten / Entry into Force | 28.10.1963</p>
  <p>Anwendbar ab / Effective From | 1961</p>
  <p>Abkommenstext / Treaty Text |
    <a href="https://www.ris.bka.gv.at/egypt">BGBl 293/1963</a>
    <a href="https://www.ris.bka.gv.at/egypt-mli">MLI Text</a>
  </p>
  <p>Durch das mehrseitige Übereinkommen (MLI) modifiziert.</p>
  <h3>Algerien / Algeria</h3>
  <p>Unterzeichnung / Date of Signature | 17.6.2003</p>
  <p>Inkrafttreten / Entry into Force | 1.12.2006</p>
  <p>Anwendbar ab / Effective From | 2006/2007</p>
  <p><a href="https://www.ris.bka.gv.at/algeria">BGBl III 176/2006</a></p>
  <h2>B</h2>
</body></html>
"""


def test_parse_bmf_treaty_list_extracts_partner_dates_links_and_mli_discovery_flag():
    rows = parse_bmf_treaty_list(SAMPLE)

    assert [row.partner_label for row in rows] == ["Ägypten / Egypt", "Algerien / Algeria"]
    assert rows[0].signature == "16.10.1962"
    assert rows[0].entry_into_force == "28.10.1963"
    assert rows[0].effective_from == "1961"
    assert rows[0].mli_flag is True
    assert rows[1].mli_flag is False
    assert rows[0].treaty_links == (
        "https://www.ris.bka.gv.at/egypt",
        "https://www.ris.bka.gv.at/egypt-mli",
    )


def test_machine_inventory_is_explicitly_non_release_and_expands_three_tax_treat_scopes():
    inventory = build_inventory(SAMPLE, as_of="2026-08-24")

    assert inventory["source_country"] == "AT"
    assert inventory["status"] == "machine_source_inventory_not_reviewed"
    assert inventory["treaty_partner_count"] == 2
    assert inventory["treaty_scope_count"] == 6
    assert inventory["mli_flagged_relationship_count"] == 1
    assert any("does not constitute legal review" in item for item in inventory["release_constraints"])
    assert any("bilateral matching" in item for item in inventory["release_constraints"])


def test_parser_fails_closed_when_official_page_shape_no_longer_contains_treaties():
    try:
        parse_bmf_treaty_list("<html><body><h1>changed page</h1></body></html>")
    except ValueError as exc:
        assert "No treaty records parsed" in str(exc)
    else:
        raise AssertionError("parser must fail closed on an unrecognized source page")
