from .editorial import *
from .client_report import *
from .html_localization import localize_report_html
from .release_polish import render_report_html as _render_release_report_html


def render_report_html(report):
    return localize_report_html(
        _render_release_report_html(report),
        report,
    )
