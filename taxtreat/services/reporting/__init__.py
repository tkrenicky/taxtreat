from .editorial import *
from .editorial import render_report_html as _render_report_html


def render_report_html(report):
    html = _render_report_html(report)

    # Keep the established accessible document name while allowing the visible
    # cover title to describe the actual transaction.
    html = html.replace(
        "<h1>",
        '<h1 aria-label="Informace k české srážkové dani">',
        1,
    )

    # Do not expose the internal deterministic report identifier in the client
    # document. It remains available in the structured report data only.
    report_id = str(report.get("report_id") or "")
    if report_id:
        html = html.replace(f"Report {report_id}", "")
        html = html.replace(report_id, "")

    # Use concise professional section names and retain the source hook used by
    # the PDF/browser acceptance contract.
    html = html.replace(
        '<div class="section-title"><h2>Výpočet a právní logika</h2>',
        '<div class="section-title"><h2>Použité právní pravidlo</h2>',
        1,
    )
    html = html.replace(
        '<div class="section-title"><h2>Právní základ a oficiální zdroje</h2>',
        '<div class="section-title"><h2>Právní základ</h2>',
        1,
    )
    html = html.replace(
        '<div class="docmeta"><b>Právní základ</b>',
        '<div class="docmeta"><b>Oficiální právní zdroje</b>',
        1,
    )
    html = html.replace('class="source-card', 'class="legal-source source-card')

    return html
