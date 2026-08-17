from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def repl(path, pairs):
    path = ROOT / path
    text = path.read_text(encoding='utf-8')
    for old, new in pairs:
        text = text.replace(old, new)
    path.write_text(text, encoding='utf-8')


def main():
    # Main workspace: remove the last legacy "kontrola/result" vocabulary and
    # keep a single information-only positioning throughout the page.
    repl('app/web/workspace.html', [
        ('TaxTreat – pracovní prostor pro kontrolu české srážkové daně', 'TaxTreat – informační pracovní prostor pro českou srážkovou daň'),
        ('Platby, příjemci a úkoly vyžadující pozornost.', 'Platby, příjemci a informace navázané na zadané údaje.'),
        ('České subjekty, jejichž platby jsou v TaxTreat kontrolovány.', 'České subjekty, jejichž platby jsou v TaxTreat zpracovávány.'),
        ('Kontrola nové platby →', 'Nový výpočet →'),
        ('Spusť první kontrolu platby pro tohoto příjemce.', 'Spusť první výpočet pro tohoto příjemce.'),
        ('Zatím bez kontrol plateb', 'Zatím bez výpočtů'),
        ('Výstup vznikne po dokončení kontroly platby.', 'Výstup vznikne po dokončení výpočtu podle zadaných údajů.'),
        ('Smluvní partneři</span><strong>101', 'Podporované jurisdikce</span><strong>101'),
        ('U každé dokončené kontroly jsou uvedeny', 'U každého dokončeného výpočtu jsou uvedeny'),
        ('Informace podle zadaných údajů kontroly', 'Informace podle zadaných údajů'),
        ('Jak výsledek číst', 'Použité právní pravidlo'),
        ('Informace podle zadaných údajů se zobrazí po vyhodnocení platby kanonickým pravidlovým enginem.', 'Po zpracování zadaných údajů se zde zobrazí přiřazené právní pravidlo a související informace.'),
        ('Vyhodnotit vstupní údaje →', 'Zobrazit pravidla a výpočet →'),
        ('TaxTreat je výpočetní nástroj. Výstup nepředstavuje právní ani daňové poradenství a není závazným stanoviskem.', 'TaxTreat je informační nástroj. Automatizovaně zobrazuje informace z právních zdrojů a údajů zadaných uživatelem; neposkytuje individuální právní ani daňové poradenství, doporučení ani závazné stanovisko.'),
    ])

    # Legacy /ui gets the same positioning and PDF-only action.
    repl('app/web/index.html', [
        ('TaxTreat je informační výpočetní nástroj.', 'TaxTreat je informační nástroj.'),
        ('<button id="report-button" class="secondary" type="button">\n            Stáhnout výsledek\n          </button>', '<button id="report-button" class="secondary" type="button">\n            Tisk / PDF\n          </button>'),
    ])

    # Replace legacy HTML-download export with the same print/PDF flow used by workspace.
    p = ROOT / 'app/web/app.js'
    text = p.read_text(encoding='utf-8')
    old = '''  reportButton.addEventListener("click", async () => {
    if (!currentPayload) return;
    reportError.hidden = true;
    reportButton.disabled = true;
    try {
      const response = await postJson("/analysis/report", currentPayload);
      const blob = new Blob([response.html], { type: "text/html;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = response.report.report_id + ".html";
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      reportError.textContent = "Výstup nebylo možné vytvořit: " + error.message;
      reportError.hidden = false;
    } finally {
      reportButton.disabled = false;
    }
  });'''
    new = '''  reportButton.addEventListener("click", async () => {
    if (!currentPayload) return;
    reportError.hidden = true;
    const reportWindow = window.open("", "_blank");
    if (!reportWindow) {
      reportError.textContent = "Prohlížeč zablokoval nové okno. Povol vyskakovací okna pro TaxTreat a zkus Tisk / PDF znovu.";
      reportError.hidden = false;
      return;
    }
    reportButton.disabled = true;
    reportWindow.document.write("<!doctype html><title>TaxTreat</title><p style='font-family:system-ui;padding:32px'>Připravuji PDF výstup…</p>");
    try {
      const response = await postJson("/analysis/report", currentPayload);
      reportWindow.document.open();
      reportWindow.document.write(response.html);
      reportWindow.document.close();
      reportWindow.opener = null;
      let printed = false;
      const printOutput = () => {
        if (printed) return;
        printed = true;
        reportWindow.focus();
        reportWindow.print();
      };
      reportWindow.addEventListener("load", printOutput, { once: true });
      window.setTimeout(printOutput, 250);
    } catch (error) {
      reportWindow.close();
      reportError.textContent = "Výstup nebylo možné vytvořit: " + error.message;
      reportError.hidden = false;
    } finally {
      reportButton.disabled = false;
    }
  });'''
    if old not in text:
        raise RuntimeError('legacy report download handler marker missing')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')

    # Report wording polish: concise, non-advisory and not repetitive.
    repl('taxtreat/services/reporting.py', [
        ('Automatizovaný přehled právních pravidel a výpočtu podle zadaných údajů vztahujícího se k údajům zadaným uživatelem.', 'Automatizovaný přehled právních pravidel a výpočtu vycházejícího z údajů zadaných uživatelem.'),
        ('Pro tento výsledek nebyl vybrán konkrétní právní zdroj.', 'Pro tento informační výstup nebyl přiřazen konkrétní právní zdroj.'),
    ])

    # Align stale tests with the intentionally changed client contract.
    repl('tests/test_stage7a_calculation.py', [
        ('assert "2485" in payload["html"]', 'assert "2 485" in payload["html"]'),
        ('assert "Výsledek vyžaduje doplnění údajů" in payload["html"]', 'assert "Zadané údaje zatím neumožňují přiřadit konkrétní pravidlo" in payload["html"]'),
    ])
    repl('tests/test_stage7a_reporting.py', [
        ('assert "nepředstavuje právní ani daňové poradenství" in report["disclaimer"]', 'assert "neposkytuje doporučení ani právní či daňové poradenství" in report["disclaimer"]'),
        ('assert "právních pravidel uvedených v tomto výstupu" in final["risk_assessment"]', 'assert "přiřadil právní pravidlo k údajům zadaným uživatelem" in final["risk_assessment"]'),
        ('assert "Srážková daň</span><strong>150 Kč" in html', 'assert "<th>Srážková daň</th><td>150 Kč</td>" in html'),
        ('assert "Přepočet ČNB" not in html', 'assert "Kurz ČNB" not in html'),
        ('assert "Příjem se v České republice nezdaňuje" in html', 'assert "pravidlo bez českého zdanění" in html'),
        ('assert "Česká daň k odvodu</span><strong>0 Kč" in html', 'assert "<th>Česká daň k odvodu</th><td>0 Kč</td>" in html'),
        ('assert "Použitá sazba</span><strong>Neuplatňuje se" in html', 'assert "Sazba Neuplatňuje se" in html'),
    ])
    repl('tests/test_information_only_positioning.py', [
        ('assert "neposkytuje individuální daňové nebo právní poradenství" in legacy_html', 'assert "neposkytuje individuální daňové nebo právní poradenství" in legacy_html.lower()'),
        ('assert "neposkytuje individuální daňové nebo právní poradenství" in workspace_html', 'assert "neposkytuje individuální daňové nebo právní poradenství" in workspace_html.lower()'),
    ])

    # Stage 7B tests should protect the new design/wording rather than the removed UI.
    repl('tests/test_stage7b_ui.py', [
        ('assert "není právním ani daňovým poradenstvím" in html', 'assert "neposkytuje individuální daňové nebo právní poradenství" in html.lower()'),
        ('assert "Kontroly plateb" in html', 'assert "Výpočty" in html'),
        ('assert "Výsledek kontroly" in html', 'assert "Informace podle zadaných údajů" in html'),
        ('assert "Jak výsledek číst" in html', 'assert "Použité právní pravidlo" in html'),
        ('assert "Podmínky a další kroky" in html', 'assert "Podmínky použitého pravidla" in html'),
        ('assert "TaxTreat je výpočetní nástroj" in html', 'assert "TaxTreat je informační nástroj" in html'),
        ('assert "nepředstavuje právní ani daňové poradenství" in html', 'assert "neposkytuje individuální právní ani daňové poradenství" in html.lower()'),
        ('assert "/ui-assets/workspace.css?v=20260817-1" in html', 'assert "/ui-assets/workspace.css?v=20260817-2" in html'),
        ('assert "/ui-assets/workspace.js?v=20260817-1" in html', 'assert "/ui-assets/workspace.js?v=20260817-2" in html'),
        ('assert "/ui-assets/workspace-designs.css?v=20260817-1" in html', 'assert "/ui-assets/workspace-designs.css?v=20260817-2" in html'),
        ('assert "Příjem se v České republice nezdaňuje" in javascript', 'assert "pravidlo bez českého zdanění" in javascript'),
        ('assert "VÝSLEDEK DOKONČEN" in source\n    assert "VÝPOČET DOKONČEN" not in source', 'assert "VÝPOČET DOKONČEN" in source\n    assert "VÝSLEDEK DOKONČEN" not in source'),
    ])

    # Current asset version used to detect stale deployments.
    repl('app/web/workspace.js', [
        ('const BUILD_VERSION = "20260817-1"', 'const BUILD_VERSION = "20260817-2"'),
    ])

    # Stage7B browser artifact script follows current public labels and PDF-only export.
    p = ROOT / 'scripts/capture_stage7b_ui.py'
    text = p.read_text(encoding='utf-8')
    text = text.replace('name="Nová kontrola platby →"', 'name="Nový výpočet →"')
    text = text.replace('"VÝSLEDEK DOKONČEN"', '"VÝPOČET DOKONČEN"')
    old = '''            with page.expect_download() as download_info:
                page.locator("#report-button").click()
            download = download_info.value
            if not download.suggested_filename.endswith(".html"):
                raise AssertionError(
                    "Professional report download did not produce HTML."
                )'''
    new = '''            page.add_init_script("window.print = () => { window.__taxtreatPrintCalled = true; };")
            with page.expect_popup() as report_popup_info:
                page.locator("#report-button").click()
            report_page = report_popup_info.value
            report_page.wait_for_load_state("domcontentloaded")
            report_page.get_by_role("heading", name="Informace k české srážkové dani", exact=True).wait_for()
            report_page.wait_for_function("() => window.__taxtreatPrintCalled === true", timeout=5000)
            report_page.close()'''
    if old not in text:
        raise RuntimeError('Stage7B HTML-download acceptance marker missing')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')

    print('Final information-only redesign alignment applied')


if __name__ == '__main__':
    main()
