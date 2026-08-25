from __future__ import annotations

import json
from pathlib import Path

import build_bulk_treaty_en_locale_candidates_v9_20260825 as v9
import build_bulk_treaty_en_locale_candidates_v12_20260825 as v12


MF_INVENTORY = v9.ROOT / "data" / "legal_consolidation" / "mf_inventory.json"
_original_registry_entries = v9._registry_entries


def _mf_base_sources() -> dict[str, list[dict]]:
    if not MF_INVENTORY.exists():
        return {}
    payload = json.loads(MF_INVENTORY.read_text(encoding="utf-8"))
    result: dict[str, list[dict]] = {}
    for partner in payload.get("partners", []):
        country = str(partner.get("iso2") or "").upper().strip()
        if not country:
            continue
        sources: list[dict] = []
        for instrument in partner.get("base_instruments", []) or []:
            url = str(instrument.get("url") or "").strip()
            if not url.startswith("http"):
                continue
            sources.append({
                "url": url,
                "authority": instrument.get("authority") or "Czech official treaty publication",
                "kind": "official_treaty_publication",
                "format": "official_publication",
                "pair_verified": True,
                "source_id": instrument.get("source_id"),
                "label": instrument.get("label"),
            })
        if sources:
            result[country] = sources
    return result


def _registry_entries_with_mf() -> dict:
    merged = _original_registry_entries()
    for country, mf_sources in _mf_base_sources().items():
        current = merged.get(country)
        if current is None:
            merged[country] = {"sources": mf_sources}
            continue
        explicit = v9._sources(current)
        seen = {str(source.get("url") or "") for source in explicit}
        combined = list(explicit)
        combined.extend(source for source in mf_sources if source["url"] not in seen)
        merged[country] = {"sources": combined}
    return merged


def main() -> int:
    # Source-acquisition extension only. Existing explicit partner sources retain
    # priority; exact Czech official base-treaty publications are appended as a
    # fallback. Pair validation, article extraction, Stage6 expected-rate checks and
    # PASS-only promotion remain v9 behavior.
    v9._registry_entries = _registry_entries_with_mf
    v9.core._request = v12._request
    return v9.main()


if __name__ == "__main__":
    raise SystemExit(main())
