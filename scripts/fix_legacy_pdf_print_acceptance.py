from pathlib import Path

p = Path('app/web/app.js')
t = p.read_text(encoding='utf-8')
old = '''      const printOutput = () => {
        if (printed) return;
        printed = true;
        reportWindow.focus();
        reportWindow.print();
      };'''
new = '''      const printOutput = () => {
        if (printed) return;
        printed = true;
        reportWindow.__taxtreatPrintCalled = true;
        reportWindow.focus();
        reportWindow.print();
      };'''
if old not in t:
    raise RuntimeError('legacy print callback marker missing')
p.write_text(t.replace(old, new, 1), encoding='utf-8')
print('legacy PDF print acceptance marker fixed')
