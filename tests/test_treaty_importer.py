import subprocess
from pathlib import Path
import yaml

def test_importer():
    subprocess.run(
        ["python", "-m", "taxtreat.importers.treaty_importer"],
        check=True,
    )

    out = Path("knowledge_base/countries/CZ/CH-dividends.yaml")
    assert out.exists()

    data = yaml.safe_load(out.read_text())

    assert data["payer_country"] == "CZ"
    assert data["recipient_country"] == "CH"
    assert data["income_type"] == "dividends"
