import subprocess

def test_knowledge_quality():
    subprocess.run(
        ["python", "-m", "taxtreat.tools.knowledge_quality"],
        check=True,
    )
