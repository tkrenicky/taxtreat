from taxtreat.registry.cz_registry import generate_scope


def test_scope_generation():
    rows = generate_scope()

    assert len(rows) == 3
    assert rows[0]["payer"] == "CZ"
    assert rows[0]["recipient"] == "DE"
