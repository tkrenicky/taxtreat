from taxtreat.tools.release_dashboard import render


def test_release_dashboard_separates_quality_dimensions():
    output = render()
    assert "Parser datasets: 100" in output
    assert "Source auditability: complete (100/100)" in output
    assert "Registered legal scopes: 300/300" in output
    assert "Official instrument inventories: 100/100" in output
    assert (
        "Remaining base-treaty candidates: 294/294 (293 with rates; 1 no-cap)"
        in output
    )
    assert "Protocol candidates: 33 scopes / 11 partners / 12 instruments" in output
    assert "Czech domestic-law candidates: 300/300 (294/294 remaining scopes)" in output
    assert "Section 19 relief candidates: 90 scopes / 30 partners (84 remaining scopes)" in output
    assert "Remaining instrument chains: 294 assembled / 0 blocked (0 partners)" in output
    assert (
        "Candidate legal-review queue: 294/294 packets; "
        "294 awaiting primary review; 0 independently approved; 0 promotable"
        in output
    )
    assert (
        "Official MLI WHT effect candidates: 64/64; "
        "signed without current effect: 7"
        in output
    )
    assert "Status-instrument candidates: 2 partners" in output
    assert "Review-ready legal scopes: 6/300" in output
    assert "Pending legal consolidation: 294/300" in output
    assert "Verified legal scopes: 0/300" in output
    assert "Production ready: False" in output
