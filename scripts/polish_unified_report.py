from pathlib import Path
p = Path('taxtreat/services/reporting.py')
t = p.read_text(encoding='utf-8')
t = t.replace("            f\"Sazba české srážkové daně: {result['rate']} %\",", "            f\"Sazba české srážkové daně: {_format_rate(result['rate'])}\",", 1)
p.write_text(t, encoding='utf-8')
print('report rate formatting polished')
