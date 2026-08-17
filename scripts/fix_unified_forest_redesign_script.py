from pathlib import Path
p = Path('scripts/apply_unified_forest_redesign.py')
t = p.read_text(encoding='utf-8')
t = t.replace("    renderer = r'''def render_report_html(report: Mapping[str, Any]) -> str:\n", "    renderer = r\"\"\"def render_report_html(report: Mapping[str, Any]) -> str:\n", 1)
t = t.replace("</main><footer>{escape(str(report['disclaimer']))}</footer></article></body></html>'''\n'''\n    p.write_text(prefix + renderer, encoding=\"utf-8\")", "</main><footer>{escape(str(report['disclaimer']))}</footer></article></body></html>'''\n\"\"\"\n    p.write_text(prefix + renderer, encoding=\"utf-8\")", 1)
p.write_text(t, encoding='utf-8')
print('quoting fixed')
