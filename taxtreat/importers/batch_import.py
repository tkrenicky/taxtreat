from pathlib import Path
import subprocess
import sys

ROOT = Path("taxtreat")

def run(module):
    print(f"\nRunning {module}")
    subprocess.run([sys.executable, "-m", module], check=True)

print("=" * 60)
print("TAXTREAT BATCH IMPORT")
print("=" * 60)

run("taxtreat.importers.csv_importer")
run("taxtreat.importers.treaty_importer")
run("taxtreat.tools.validate_knowledge_base")

# Spusť pouze moduly, které opravdu existují
optional = [
    "taxtreat.tools.generate_reference_cases",
    "taxtreat.tools.generate_reference_case",
    "taxtreat.tools.verify_reference_cases",
]

for module in optional:
    module_path = ROOT / Path(module.replace(".", "/") + ".py")
    if module_path.exists():
        run(module)

print("\nDone.")
