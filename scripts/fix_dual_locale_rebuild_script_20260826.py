from pathlib import Path

path = Path('scripts/rebuild_web_locale_engines_20260826.py')
text = path.read_text(encoding='utf-8')
old_start = "MODULE = r'''from __future__ import annotations"
new_start = 'MODULE = r"""from __future__ import annotations'
if old_start not in text:
    raise SystemExit('module opening marker missing')
text = text.replace(old_start, new_start, 1)
old_end = "\n'''\n\n\ndef replace_once(text: str, old: str, new: str, label: str) -> str:"
new_end = '\n"""\n\n\ndef replace_once(text: str, old: str, new: str, label: str) -> str:'
if old_end not in text:
    raise SystemExit('module closing marker missing')
text = text.replace(old_end, new_end, 1)
path.write_text(text, encoding='utf-8')
print('dual locale rebuild generator quoting fixed')
