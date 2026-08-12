from taxtreat.engine.registry import build_default_registry


def test_default_extractor_registry_reports_membership():
    registry = build_default_registry()

    assert registry.has("dividend") is True
    assert registry.has("unknown") is False
