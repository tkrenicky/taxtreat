import subprocess
from pathlib import Path

def test_export_progress():
    subprocess.run(
        ["python", "-m", "taxtreat.tools.export_progress"],
        check=True,
    )

    assert Path("reports/knowledge_base_progress.csv").exists()
