from pathlib import Path

import pytest
import yaml

from taxtreat.tools.validate_knowledge_base import validate_file


FILES = sorted(Path("knowledge_base/countries").rglob("*.yaml"))


@pytest.mark.parametrize("path", FILES, ids=lambda path: path.stem)
def test_knowledge_base_file_is_valid(path):
    assert validate_file(path) == []


@pytest.mark.parametrize("path", FILES, ids=lambda path: path.stem)
def test_knowledge_base_yaml_can_be_loaded(path):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert isinstance(data, dict)
    assert data["id"]
