from scripts.rebind_semantic_remediation_package_hashes_20260901 import rebind


def test_semantic_remediation_package_hashes_are_current():
    assert rebind(check=True) == []
