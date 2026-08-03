from taxtreat.registry.cz_registry import generate_scope


def test_scope_generation():
    rows = generate_scope()

    assert len(rows) == 300
    assert rows[0]["payer"] == "CZ"
    assert rows[0]["recipient"] == "AL"
    assert len({row["recipient"] for row in rows}) == 100
    assert {row["income_type"] for row in rows} == {
        "dividend",
        "interest",
        "royalty",
    }
