from taxtreat.tools.release_dashboard import render


def test_release_dashboard_separates_quality_dimensions():
    output = render()
    assert "Parser datasets: 100" in output
    assert "Source auditability: blocked (0/100)" in output
    assert "Registered legal scopes: 300/300" in output
    assert "Official instrument inventories: 100/100" in output
    assert "Remaining base-treaty candidates: 294/294 (293 with rates)" in output
    assert "Protocol candidates: 33 scopes / 11 partners / 12 instruments" in output
    assert "Official MLI WHT effect candidates: 62/62" in output
    assert "Review-ready legal scopes: 6/300" in output
    assert "Pending legal consolidation: 294/300" in output
    assert "Verified legal scopes: 0/300" in output
    assert "Production ready: False" in output
