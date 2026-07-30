import subprocess
from pathlib import Path

def test_country_matrix():
    subprocess.run(
        ["python", "-m", "taxtreat.tools.build_country_matrix"],
        check=True,
    )

    assert Path("reports/country_matrix.csv").exists()
