from .editorial import *
from .client_report import *
from .html_localization import localize_report_html
from .release_polish import render_report_html as _render_release_report_html
from .domestic_exemption_polish import apply_domestic_exemption_polish
from .treaty_secondary_polish import apply_treaty_secondary_polish
from .report_pagination_polish import apply_report_pagination_polish


def render_report_html(report):
    return localize_report_html(
        apply_report_pagination_polish(
            apply_treaty_secondary_polish(
                apply_domestic_exemption_polish(
                    _render_release_report_html(report),
                    report,
                ),
                report,
            ),
            report,
        ),
        report,
    )
