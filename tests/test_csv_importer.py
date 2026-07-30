import subprocess
from pathlib import Path
import yaml

def test_csv_importer():
    subprocess.run(
        ["python", "-m", "taxtreat.importers.csv_importer"],
        check=True,
    )

    files = list(Path("knowledge_base/countries/CZ").glob("*.yaml"))

    assert files

    for file in files:
        data = yaml.safe_load(file.read_text())

        assert "payer_country" in data
        assert "recipient_country" in data
        assert "income_type" in data
