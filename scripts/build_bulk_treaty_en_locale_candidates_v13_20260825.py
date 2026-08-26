from __future__ import annotations

import json
import urllib.parse

import build_bulk_treaty_en_locale_candidates_v9_20260825 as v9
import build_bulk_treaty_en_locale_candidates_v12_20260825 as v12


MF_INVENTORY = v9.ROOT / "data" / "legal_consolidation" / "mf_inventory.json"
_original_registry_entries = v9._registry_entries


def _is_psp_print_source(source: dict) -> bool:
    url = str(source.get("url") or "")
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower().removeprefix("www.")
    return host == "psp.cz" and parsed.path.lower().endswith("/sqw/text/tiskt.sqw")


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
    mf = _mf_base_sources()
    countries = set(merged) | set(mf)
    rebuilt: dict = {}
    for country in countries:
        explicit = v9._sources(merged.get(country)) if country in merged else []
        # PSP ratification-print discovery is retained in the registry for targeted
        # later use, but omitted from this scalable batch after proving expensive and
        # low-yield. Partner-government sources remain first-class.
        explicit = [source for source in explicit if not _is_psp_print_source(source)]
        seen = {str(source.get("url") or "") for source in explicit}
        combined = list(explicit)
        combined.extend(source for source in mf.get(country, []) if source["url"] not in seen)
        if combined:
            rebuilt[country] = {"sources": combined}
    return rebuilt


def main() -> int:
    # Extend pair validation only for explicitly verified partner names that were not
    # present in the original v9 marker table. This does not relax the pair gate.
    v9.PARTNER_MARKERS.update({
        "BR": ("brazil", "federative republic of brazil"),
    })
    # Source-acquisition extension only. Exact partner-government sources plus Czech
    # official base-treaty publications are evaluated by the existing pair/article/
    # Stage6 rate gates. Nothing here can promote REVIEW or overwrite an EN locale.
    v9._registry_entries = _registry_entries_with_mf
    v9.core._request = v12._request
    return v9.main()


if __name__ == "__main__":
    raise SystemExit(main())
