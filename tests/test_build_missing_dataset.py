import subprocess
from pathlib import Path

def test_build_missing_dataset():
    subprocess.run(
        ["python", "-m", "taxtreat.tools.build_missing_dataset"],
        check=True,
    )

    assert Path("reports/missing_dataset.csv").exists()
