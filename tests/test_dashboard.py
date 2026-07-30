import subprocess

def test_dashboard_runs():
    subprocess.run(
        ["python", "-m", "taxtreat.tools.knowledge_base_dashboard"],
        check=True,
    )
