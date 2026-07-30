from pathlib import Path

from taxtreat.pipeline.build_database import OUTPUT_DIR


def test_output_directory_exists():
    assert OUTPUT_DIR.name == "generated"


def test_pipeline_module_exists():
    assert Path("taxtreat/pipeline/build_database.py").exists()
