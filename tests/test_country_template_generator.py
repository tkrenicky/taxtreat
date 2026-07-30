from pathlib import Path
import subprocess

import yaml


def test_country_template_generator():
    subprocess.run(
        ["python", "-m", "taxtreat.tools.create_country_templates"],
        check=True,
    )

    files = list(Path("knowledge_base/countries/CZ").glob("*.yaml"))

    assert files

    for file in files:
        data = yaml.safe_load(file.read_text(encoding="utf-8"))

        assert data["payer_country"] == "CZ"
        assert data["income_type"] in {"dividends", "interest", "royalties"}
        assert data["status"] in {"draft", "reviewed", "verified"}
