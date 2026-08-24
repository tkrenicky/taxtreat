from taxtreat.tools.build_at_treaty_source_inventory import build_inventory, parse_bmf_treaty_list


SAMPLE = """
<html><body>
  <h2>A</h2>
  <h3>Ägypten / Egypt</h3>
  <div class="table-responsive"><table><tbody>
    <tr><td>Unterzeichnung / <span>Date of Signature</span></td><td>16.10.1962</td></tr>
    <tr><td>Inkrafttreten / <span>Entry into Force</span></td><td>28.10.1963</td></tr>
    <tr><td>Anwendbar ab / <span>Effective From</span></td><td>1961</td></tr>
    <tr><td>Abkommenstext / <span>Treaty Text</span></td><td>
      <a href="https://www.ris.bka.gv.at/egypt">BGBl 293/1963</a>
      <a href="https://www.ris.bka.gv.at/egypt-mli">MLI Text</a>
    </td></tr>
    <tr><td>Erlässe / Decrees</td><td><a href="https://findok.bmf.gv.at/not-treaty">Decree</a></td></tr>
  </tbody></table></div>
  <p>Durch das mehrseitige Übereinkommen (MLI) modifiziert.</p>

  <h3>Argentinien / Argentina</h3>
  <div class="table-responsive"><table><tbody>
    <tr><td>Unterzeichnung / Date of Signature</td><td>6.12.2019</td></tr>
    <tr><td>Inkrafttreten / Entry into Force</td><td>12.6.2026</td></tr>
    <tr><td>Anwendbar ab / Effective From</td><td>1.1.2027</td></tr>
    <tr><td>Abkommenstext / Treaty Text</td><td><a href="https://www.ris.bka.gv.at/argentina">BGBl III 77/2026</a></td></tr>
  </tbody></table></div>

  <h3>Libyen / Libya</h3>
  <div class="table-responsive"><table><tbody>
    <tr><td>Unterzeichnung / Date of Signature</td><td>16.9.2010</td></tr>
    <tr><td>Inkrafttreten / Entry into Force</td><td></td></tr>
    <tr><td>Anwendbar ab / Effective From</td><td></td></tr>
    <tr><td>Abkommenstext / Treaty Text</td><td></td></tr>
  </tbody></table></div>

  <h3>UdSSR / USSR</h3>
  <div class="table-responsive"><table><tbody>
    <tr><td>Unterzeichnung / Date of Signature</td><td>10.4.1981</td></tr>
    <tr><td>Inkrafttreten / Entry into Force</td><td>1.10.1982</td></tr>
    <tr><td>Anwendbar ab / Effective From</td><td>1979</td></tr>
    <tr><td>Abkommenstext / Treaty Text</td><td><a href="https://www.ris.bka.gv.at/ussr">BGBl</a></td></tr>
  </tbody></table></div>
  <h2>B</h2>
</body></html>
"""


def test_parse_bmf_treaty_list_extracts_real_table_shape_dates_treaty_links_and_mli_signal():
    rows = parse_bmf_treaty_list(SAMPLE)

    assert [row.partner_label for row in rows] == [
        "Ägypten / Egypt",
        "Argentinien / Argentina",
        "Libyen / Libya",
        "UdSSR / USSR",
    ]
    egypt = rows[0]
    assert egypt.signature == "16.10.1962"
    assert egypt.entry_into_force == "28.10.1963"
    assert egypt.effective_from == "1961"
    assert egypt.mli_flag is True
    assert egypt.applicability_status == "current_candidate"
    assert egypt.release_universe_candidate is True
    assert egypt.treaty_links == (
        "https://www.ris.bka.gv.at/egypt",
        "https://www.ris.bka.gv.at/egypt-mli",
    )
    assert "https://findok.bmf.gv.at/not-treaty" not in egypt.treaty_links


def test_machine_inventory_separates_current_future_signed_and_historical_records():
    inventory = build_inventory(SAMPLE, as_of="2026-08-24")

    assert inventory["source_country"] == "AT"
    assert inventory["status"] == "machine_source_inventory_not_reviewed"
    assert inventory["source_page_record_count"] == 4
    assert inventory["treaty_partner_count"] == 4
    assert inventory["treaty_scope_count"] == 12
    assert inventory["release_universe_candidate_count"] == 1
    assert inventory["release_universe_scope_count"] == 3
    assert inventory["mli_flagged_relationship_count"] == 1
    assert inventory["applicability_status_counts"] == {
        "current_candidate": 1,
        "historical_parent_instrument": 1,
        "in_force_future_effective": 1,
        "signed_not_in_force": 1,
    }

    by_partner = {row["partner_label"]: row for row in inventory["records"]}
    assert by_partner["Argentinien / Argentina"]["applicability_status"] == "in_force_future_effective"
    assert by_partner["Libyen / Libya"]["applicability_status"] == "signed_not_in_force"
    assert by_partner["UdSSR / USSR"]["applicability_status"] == "historical_parent_instrument"
    assert all(
        by_partner[name]["release_universe_candidate"] is False
        for name in ["Argentinien / Argentina", "Libyen / Libya", "UdSSR / USSR"]
    )


def test_machine_inventory_is_explicitly_non_release():
    inventory = build_inventory(SAMPLE, as_of="2026-08-24")
    constraints = "\n".join(inventory["release_constraints"])

    assert "does not constitute legal review" in constraints
    assert "bilateral matching" in constraints
    assert "future-effective" in constraints
    assert "treaty-text row" in constraints


def test_parser_fails_closed_when_official_page_shape_no_longer_contains_treaties():
    try:
        parse_bmf_treaty_list("<html><body><h1>changed page</h1></body></html>")
    except ValueError as exc:
        assert "No treaty records parsed" in str(exc)
    else:
        raise AssertionError("parser must fail closed on an unrecognized source page")
