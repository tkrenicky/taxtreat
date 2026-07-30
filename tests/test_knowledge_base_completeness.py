import subprocess

def test_missing_pairs_script_runs():
    subprocess.run(
        ["python", "-m", "taxtreat.tools.find_missing_pairs"],
        check=True,
    )
