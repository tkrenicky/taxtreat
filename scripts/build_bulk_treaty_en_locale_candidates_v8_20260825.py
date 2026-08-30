from __future__ import annotations

import build_bulk_treaty_en_locale_candidates_v7_20260825 as v7

v7.OUT_DIR = v7.ROOT / "reports" / "treaty_en_locale_bulk_candidates_v8_20260825"
v7.SUMMARY = v7.ROOT / "reports" / "treaty_en_locale_bulk_candidates_v8_20260825.json"
v7.PARTNER_MARKERS.update({
    "IE": ("ireland", "irish"),
    "MT": ("malta", "maltese"),
})

if __name__ == "__main__":
    raise SystemExit(v7.main())
