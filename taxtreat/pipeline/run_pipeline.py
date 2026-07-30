from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


STEPS = [
    ("Archive official sources", "python -m taxtreat.tools.fetch_official_sources"),
    ("Parse treaties", "python -m taxtreat.parsers.parse_all"),
    ("Extract structured data", "python -m taxtreat.extractors.extract_all"),
    ("Validate records", "python -m taxtreat.validation.validate_all"),
    ("Calculate confidence", "python -m taxtreat.validation.score_all"),
    ("Quality gate", "python -m taxtreat.validation.quality_gate_all"),
    ("Build database", "python -m taxtreat.pipeline.build_database"),
]


def main():
    failures = []

    for name, command in STEPS:
        print(f"\n{'=' * 70}")
        print(name)
        print('=' * 70)

        result = subprocess.run(
            command,
            shell=True,
            cwd=ROOT,
        )

        if result.returncode:
            failures.append(name)
            break

    if failures:
        print("\nPipeline failed:")
        for step in failures:
            print(f" - {step}")
        sys.exit(1)

    print("\nPipeline finished successfully.")


if __name__ == "__main__":
    main()
