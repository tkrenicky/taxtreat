import subprocess

def test_source_validator():
    subprocess.run(
        ["python", "-m", "taxtreat.tools.validate_sources"],
        check=True,
    )
