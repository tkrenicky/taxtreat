from __future__ import annotations
import subprocess, sys, time
from pathlib import Path
from urllib.request import urlopen
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports' / 'workspace_design_preview'
OUT.mkdir(parents=True, exist_ok=True)
HOST='127.0.0.1'; PORT=8771; BASE=f'http://{HOST}:{PORT}'
process = subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host',HOST,'--port',str(PORT)], cwd=ROOT)
try:
    for _ in range(100):
        try:
            if urlopen(f'{BASE}/health/live', timeout=1).status == 200: break
        except OSError: time.sleep(.2)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={'width':1440,'height':1050}, locale='cs-CZ')
        page.goto(f'{BASE}/workspace-demo', wait_until='networkidle')
        page.screenshot(path=str(OUT/'workspace-dashboard.png'), full_page=True)
        page.get_by_role('button', name='Nová kontrola platby →').first.click()
        page.screenshot(path=str(OUT/'workspace-flow.png'), full_page=True)
        browser.close()
finally:
    process.terminate()
    try: process.wait(timeout=5)
    except subprocess.TimeoutExpired: process.kill()
print(OUT)
