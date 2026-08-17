from pathlib import Path

p = Path('scripts/check_workspace_report_export.py')
t = p.read_text(encoding='utf-8')
t = t.replace('name="Nová kontrola platby →"', 'name="Nový výpočet →"')
t = t.replace('"button", name="Kontroly plateb", exact=True', '"button", name="Výpočty", exact=True')
t = t.replace('review_page.get_by_text("Česká srážková daň", exact=True)', 'review_page.get_by_text("Informace k české srážkové dani", exact=True)')
p.write_text(t, encoding='utf-8')
print('browser acceptance labels aligned')
