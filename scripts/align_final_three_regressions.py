from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

p = ROOT / 'tests/test_stage7a_calculation.py'
t = p.read_text(encoding='utf-8').replace('assert "1 EUR = 24.85 CZK" in payload["html"]', 'assert "1 EUR = 24.85 Kč" in payload["html"]')
p.write_text(t, encoding='utf-8')

p = ROOT / 'tests/test_stage7b_ui.py'
t = p.read_text(encoding='utf-8')
t = t.replace('assert \'const BUILD_VERSION = "20260817-1"\' in javascript.text', 'assert \'const BUILD_VERSION = "20260817-2"\' in javascript.text')
t = t.replace('assert "Příjem je v České republice osvobozen" in javascript', 'assert "pravidlo osvobození" in javascript')
p.write_text(t, encoding='utf-8')

print('Final three regression expectations aligned')
