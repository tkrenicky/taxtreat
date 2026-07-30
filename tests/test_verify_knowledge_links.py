import subprocess

def test_verify_knowledge_links():
    subprocess.run(
        ["python", "-m", "taxtreat.tools.verify_knowledge_links"],
        check=True,
    )
