from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "data" / "legal_rules_sk"
SUMMARY = (
    ROOT
    / "data"
    / "legal_reviews"
    / "sk_outbound"
    / "structured_treaty_rule_materialization_summary.json"
)


def _snapshot() -> dict[str, str]:
    paths = [*sorted(RULE_DIR.glob("*.json")), SUMMARY]
    assert len(paths) == 76
    return {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


def _regenerate_full_sk_cycle() -> None:
    subprocess.run(
        [sys.executable, "taxtreat/tools/build_sk_structured_treaty_rules.py"],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, "taxtreat/tools/apply_sk_mli_gates_to_structured_rules.py"],
        cwd=ROOT,
        check=True,
    )


def test_sk_structured_rule_full_regeneration_is_idempotent() -> None:
    """
    The supported regeneration unit is build + MLI application.

    The treaty builder intentionally rewrites data/legal_rules_sk, so testing
    it in isolation would incorrectly treat the temporary absence of MLI gates
    as a stable state. Two complete cycles must produce byte-identical runtime
    artifacts, including all verified pair-specific MLI gates.
    """
    _regenerate_full_sk_cycle()
    first = _snapshot()

    _regenerate_full_sk_cycle()
    second = _snapshot()

    assert second == first
