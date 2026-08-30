from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "data" / "legal_reviews" / "sk_outbound" / "cooperating_states_source_2026.json"
BODY_PATH = ROOT / "data" / "legal_sources" / "slovak_mf_cooperating_states_2026" / "49561.pdf"

# The official PDF uses Slovak jurisdiction names. Every source spelling is
# explicit so a newly appearing or changed name fails closed.
SOURCE_NAME_TO_CODE = {
    "Albánsko": "AL", "Andorra": "AD", "Antigua a Barbuda": "AG", "Argentína": "AR",
    "Arménsko": "AM", "Aruba": "AW", "Austrália": "AU", "Azerbajdžan": "AZ",
    "Barbados": "BB", "Belgicko": "BE", "Benin": "BJ", "Bielorusko": "BY",
    "Bosna a Hercegovina": "BA", "Botswana": "BW", "Brazília": "BR", "Brunej": "BN",
    "Bulharsko": "BG", "Burkina Faso": "BF", "Cookove ostrovy": "CK", "Curacao": "CW",
    "Cyprus": "CY", "Česká republika": "CZ", "Čierna Hora": "ME", "Čile": "CL",
    "Čína": "CN", "Dánsko": "DK", "Dominika": "DM", "Dominikánska republika": "DO",
    "Ekvádor": "EC", "El Salvador": "SV", "Estónsko": "EE", "Eswatini": "SZ",
    "Etiópia": "ET", "Faerské ostrovy": "FO", "Filipíny": "PH", "Fínsko": "FI",
    "Francúzsko": "FR", "Ghana": "GH", "Gibraltár": "GI", "Grécko": "GR",
    "Grenada": "GD", "Grónsko": "GL", "Gruzínsko": "GE", "Guatemala": "GT",
    "Holandsko": "NL", "Hongkong": "HK", "Chorvátsko": "HR", "India": "IN",
    "Indonézia": "ID", "Irán": "IR", "Írsko": "IE", "Island": "IS", "Izrael": "IL",
    "Jamajka": "JM", "Japonsko": "JP", "Jordánsko": "JO", "Juhoafrická republika": "ZA",
    "Kamerun": "CM", "Kanada": "CA", "Kapverdské ostrovy": "CV", "Katar": "QA",
    "Kazachstan": "KZ", "Keňa": "KE", "Kirgizská republika": "KG", "Kolumbia": "CO",
    "Kórea": "KR", "Kostarika": "CR", "Kuvajt": "KW", "Libanon": "LB", "Libéria": "LR",
    "Lichtenštajnsko": "LI", "Litva": "LT", "Líbya": "LY", "Lotyšsko": "LV",
    "Luxembursko": "LU", "Macao": "MO", "Madagaskar": "MG", "Maďarsko": "HU",
    "Malajzia": "MY", "Maldivy": "MV", "Malta": "MT", "Maroko": "MA", "Maršalove ostrovy": "MH",
    "Maurícius": "MU", "Mauritánia": "MR", "Mexiko": "MX", "Moldavsko": "MD", "Monako": "MC",
    "Mongolsko": "MN", "Montserrat": "MS", "Namíbia": "NA", "Nauru": "NR", "Nemecko": "DE",
    "Nigéria": "NG", "Niue": "NU", "Nórsko": "NO", "Nový Zéland": "NZ", "Omán": "OM",
    "Pakistan": "PK", "Papua Nová Guinea": "PG", "Paraguaj": "PY", "Peru": "PE", "Poľsko": "PL",
    "Portugalsko": "PT", "Rakúsko": "AT", "Rumunsko": "RO", "Rwanda": "RW", "San Maríno": "SM",
    "Saudská Arábia": "SA", "Senegal": "SN", "Severné Macedónsko": "MK", "Seychely": "SC",
    "Singapur": "SG", "Slovinsko": "SI", "Spojené arabské emiráty": "AE",
    "Spojené kráľovstvo Veľkej Británie a Severného Írska": "GB", "Srbsko": "RS", "Srí Lanka": "LK",
    "Sv. Krištof a Nevis": "KN", "Sv. Lucia": "LC", "Sv. Martin": "MF", "Sv. Vincent a Grenadíny": "VC",
    "Sýria": "SY", "Španielsko": "ES", "Švajčiarsko": "CH", "Švédsko": "SE", "Taiwan": "TW",
    "Taliansko": "IT", "Thajsko": "TH", "Tunisko": "TN", "Turecko": "TR", "Turkmenistan": "TM",
    "Uganda": "UG", "Ukrajina": "UA", "Uruguaj": "UY", "USA": "US", "Uzbekistan": "UZ",
    "Vietnam": "VN",
}

ENTRY_RE = re.compile(r"(?m)^\s*(\d{1,3})\.\s+")
FOOTNOTE_RE = re.compile(r"[iI]{1,3}\)$")
CONTRACT_MARKERS = ("Zmluva", "Dohovor")


def _body_text(body: bytes) -> str:
    reader = PdfReader(__import__("io").BytesIO(body))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _normalize(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    return FOOTNOTE_RE.sub("", value).strip()


def canonical_code_for_source_name(source_name: str) -> str:
    normalized = _normalize(source_name)
    matches = [
        name for name in SOURCE_NAME_TO_CODE
        if _normalize(name) == normalized
    ]
    if len(matches) != 1:
        raise ValueError(f"Unknown or ambiguous official country name: {source_name}")
    return SOURCE_NAME_TO_CODE[matches[0]]


def parse_official_body(body: bytes) -> list[dict[str, Any]]:
    text = _body_text(body)
    starts = list(ENTRY_RE.finditer(text))
    entries: list[dict[str, Any]] = []
    names = sorted(SOURCE_NAME_TO_CODE, key=len, reverse=True)
    for index, match in enumerate(starts):
        number = int(match.group(1))
        if number != len(entries) + 1:
            raise ValueError(f"Unexpected official list entry number: {number}")
        block = text[match.end() : starts[index + 1].start() if index + 1 < len(starts) else len(text)]
        block = _normalize(block)
        block = re.sub(
            r"Zmluva o zamedzení dvojitého zdanenia \d+/\d+ "
            r"\d{2}\.\d{2}\.\d{4} \d+ Zmluvný štát/jurisdikcia "
            r"Typ zmluvy Zb\./ Z\. z\. Dátum účinnosti",
            "",
            block,
        )
        block = _normalize(block)
        candidates = []
        for name in names:
            country_column = re.split(r"\b(?:Zmluva|Dohovor)\b", block, maxsplit=1)[0]
            if re.search(rf"(?<!\w){re.escape(name)}(?:i{{1,3}}\))?(?!\w)", country_column):
                candidates.append(name)
        if not candidates:
            for name in names:
                if re.search(rf"(?<!\w){re.escape(name)}(?:i{{1,3}}\))?(?!\w)", block):
                    candidates.append(name)
        if len(candidates) != 1:
            raise ValueError(f"Entry {number} has ambiguous or unmappable country name: {candidates}")
        name = candidates[0]
        entries.append({"entry_number": number, "source_name": name, "canonical_code": canonical_code_for_source_name(name)})
    if len(entries) != 138:
        raise ValueError(f"Expected 138 official entries, found {len(entries)}")
    return entries


def ingest(*, retrieved_at: str | None = None) -> dict[str, Any]:
    body = BODY_PATH.read_bytes()
    body_sha256 = hashlib.sha256(body).hexdigest()
    parsed = parse_official_body(body)
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    official = source["official_list"]
    if (official["valid_from"], official["valid_to"], official["mf_document_id"]) != ("2026-01-01", "2026-12-31", 49561):
        raise ValueError("Unexpected official 2026 MF SR source identity or effective period")
    source["official_list"].update({
        "official_attachment_url": "https://www.mfsr.sk/files/archiv/39/Zoznam-spolupracujucich-statov-podla-2-pism-x-zakona-c-595_2003-Z-z_1.1.2026.pdf",
        "source_body_path": str(BODY_PATH.relative_to(ROOT)),
        "source_body_sha256": body_sha256,
        "source_body_retrieved_at": retrieved_at or source["official_list"].get("source_body_retrieved_at") or date.today().isoformat(),
        "source_body_content_type": "application/pdf",
    })
    source["cooperating_state_codes"] = [entry["canonical_code"] for entry in parsed]
    source["parsed_countries"] = parsed
    source["mapping_ambiguities"] = []
    source["official_list"]["attachment_access_status"] = "official_body_ingested_and_hash_verified"
    source["official_list"]["country_list_ingestion_status"] = "official_document_body_parsed_deterministically"
    SOURCE_PATH.write_text(json.dumps(source, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return source


if __name__ == "__main__":
    result = ingest()
    print(json.dumps({"source_body_sha256": result["official_list"]["source_body_sha256"], "parsed_countries": len(result["parsed_countries"]), "mapping_ambiguities": result["mapping_ambiguities"]}, ensure_ascii=False, indent=2))
