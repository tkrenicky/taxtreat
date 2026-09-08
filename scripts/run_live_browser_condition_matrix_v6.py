from __future__ import annotations

import sys
from typing import Any

import run_live_browser_condition_matrix as base
import run_live_browser_condition_matrix_v4 as v4
import run_live_browser_condition_matrix_v5 as v5


# Recipient-type options have locale-specific display labels and, because the
# historical HTML options do not carry explicit values, their values are also
# locale-specific. Select them by the stable semantic option order instead of
# by Czech UI copy so the same browser scenario works in /ui/cs and /ui/en.
RECIPIENT_TYPE_INDEX = {
    "Společnost": 0,
    "Fyzická osoba": 1,
    "Fond": 2,
    "Jiný subjekt": 3,
}


def ensure_recipient_type(page, desired_type: str) -> None:
    if desired_type == v4.CURRENT_RECIPIENT_TYPE:
        return

    page.locator('[data-flow-step="2"]:visible').click()
    page.wait_for_function(
        "() => Boolean(document.querySelector('.flow-step[data-step=\"2\"].active'))"
    )
    page.locator('.flow-step[data-step="2"] [data-edit-recipient]:visible').click()
    page.wait_for_function("() => Boolean(document.querySelector('#recipient-dialog')?.open)")
    dialog = page.locator("#recipient-dialog #recipient-edit-form")
    type_control = dialog.locator('[name="recipient_type"]')
    base.check(type_control.count() == 1, "recipient type control missing")

    option_index = RECIPIENT_TYPE_INDEX.get(desired_type)
    base.check(option_index is not None, f"unknown recipient type: {desired_type!r}")
    option_count = type_control.locator("option").count()
    base.check(
        option_count > option_index,
        f"recipient type option {option_index} missing; found {option_count} options",
    )
    type_control.select_option(index=option_index)

    dialog.locator('button[type="submit"]').click()
    page.wait_for_function("() => !document.querySelector('#recipient-dialog')?.open")
    page.locator('[data-next-step="3"]:visible').click()
    page.wait_for_function(
        "() => Boolean(document.querySelector('.flow-step[data-step=\"3\"].active'))"
    )
    v4.CURRENT_RECIPIENT_TYPE = desired_type


def install() -> None:
    v5.install()
    v4.ensure_recipient_type = ensure_recipient_type


def main() -> int:
    install()
    return base.main()


if __name__ == "__main__":
    sys.exit(main())
