from .editorial import *
from .editorial import render_report_html as _render_report_html


def render_report_html(report):
    html = _render_report_html(report)
    return html.replace(
        "<h1>",
        '<h1 aria-label="Informace k české srážkové dani">',
        1,
    )
