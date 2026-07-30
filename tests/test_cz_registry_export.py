from pathlib import Path

def test_registry_exists():
    assert Path("taxtreat/tools/update_cz_treaty_registry.py").exists()
