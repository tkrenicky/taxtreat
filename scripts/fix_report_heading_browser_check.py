from pathlib import Path
p = Path('scripts/check_workspace_report_export.py')
t = p.read_text(encoding='utf-8')
t = t.replace('print_page.get_by_text("Informace k české srážkové dani", exact=True).wait_for()', 'print_page.get_by_role("heading", name="Informace k české srážkové dani", exact=True).wait_for()')
t = t.replace('stored_page.get_by_text("Informace k české srážkové dani", exact=True).wait_for()', 'stored_page.get_by_role("heading", name="Informace k české srážkové dani", exact=True).wait_for()')
t = t.replace('review_page.get_by_text("Informace k české srážkové dani", exact=True).wait_for()', 'review_page.get_by_role("heading", name="Informace k české srážkové dani", exact=True).wait_for()')
p.write_text(t, encoding='utf-8')
print('report heading checks fixed')
