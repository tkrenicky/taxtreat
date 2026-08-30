from .editorial import *
from .client_report import *
from .english_release_localization import finalize_english_report_html
from .html_localization import localize_report_html
from .release_polish import render_report_html as _render_release_report_html


def render_report_html(report):
    localized = localize_report_html(
        _render_release_report_html(report),
        report,
    )
    return finalize_english_report_html(localized, report)
