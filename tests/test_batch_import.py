import subprocess

def test_batch_import():
    subprocess.run(
        ["python", "-m", "taxtreat.importers.batch_import"],
        check=True,
    )
