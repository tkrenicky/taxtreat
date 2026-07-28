from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

MF_TREATIES = "https://mf.gov.cz/cs/zahranici-a-eu/smlouvy-o-zamezeni-dvojiho-zdaneni/prehled-platnych-smluv"
OECD_MLI = "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/beps-mli/beps-mli-position-czech-republic.pdf"
EURLEX_PSD = "https://eur-lex.europa.eu/eli/dir/2011/96/2015-02-17/eng"

_ALLOWED_HOSTS = (
    "mf.gov.cz",
    "mfcr.cz",
    "aplikace.mv.gov.cz",
    "aplikace.mvcr.cz",
    "e-sbirka.gov.cz",
)
_DATE_RE = re.compile(r"^\s*\d{1,2}\.\d{1,2}\.\d{4}\s*$")
_ARCHIVE_YEAR_RE = re.compile(r"^(?:19|20)\d{2}$")


@dataclass
class Document:
    url: str
    source_page: str
    title: str
    kind: str
    country_cs: str | None = None
    effective_from: str | None = None
    relation: str | None = None
    mime_type: str | None = None
    sha256: str | None = None
    local_path: str | None = None
    downloaded_at: str | None = None
    status: str = "discovered"
    error: str | None = None


class Crawler:
    def __init__(self, root: Path):
        self.root = root
        self.raw = root / "data" / "raw"
        self.raw.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "TaxTreatLegalIngest/0.2 (+compliance research)"}
        )
        self._download_cache: dict[str, Document] = {}

    def get(self, url: str) -> requests.Response:
        return self._get_with_timeout(url)

    def _get_with_timeout(self, url: str) -> requests.Response:
        response = self.session.get(url, timeout=(15, 60), allow_redirects=True)
        response.raise_for_status()
        return response

    @staticmethod
    def classify(title: str, url: str, relation: str | None = None) -> str:
        text = title.casefold()
        if "protokol" in text:
            return "protocol"
        if "úmluva č. 32/2020" in text or re.search(r"\bmli\b", text):
            return "mli"
        if "pokyn" in text:
            return "guidance"
        if "finanční zpravodaj" in text or re.search(r"\bfz\b", text):
            return "financial_bulletin"
        if "oprava" in text or "sdělení" in text:
            return "notice"
        if "directive" in text or "směrnic" in text:
            return "eu_directive"
        if relation == "treaty":
            return "treaty"
        if any(x in urlparse(url).netloc for x in ("mv.gov.cz", "e-sbirka.gov.cz")):
            return "treaty_or_statute"
        return "other"

    @staticmethod
    def _clean_text(node: Tag) -> str:
        return " ".join(node.get_text(" ", strip=True).split())

    @staticmethod
    def _normalise_date(value: str) -> str:
        day, month, year = value.strip().split(".")
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"

    @staticmethod
    def _valid_document_link(title: str, href: str) -> bool:
        clean_title = " ".join(title.split()).strip()
        if not clean_title or _ARCHIVE_YEAR_RE.fullmatch(clean_title):
            return False

        host = urlparse(href).netloc.casefold()
        if not host or not any(domain in host for domain in _ALLOWED_HOSTS):
            return False

        path = urlparse(href).path.casefold().rstrip("/")
        if any(part in path for part in ("/archiv", "/vyhledavani", "/prehled-pokynu-a-sdeleni")):
            return False
        return True

    def discover_links(self, page_url: str = MF_TREATIES) -> list[Document]:
        print(f"Načítám seznam: {page_url}", flush=True)
        html = self.get(page_url).text
        soup = BeautifulSoup(html, "lxml")
        docs: list[Document] = []
        treaty_rows = 0

        for row in soup.select("tr"):
            # MF uses <th> for the country name and <td> for the remaining columns.
            # Reading only <td> therefore skipped every real treaty row.
            cells = row.find_all(("th", "td"), recursive=False)
            if len(cells) < 3:
                # Fallback for any harmless wrapper introduced by a future page redesign.
                cells = row.find_all(("th", "td"))
            if len(cells) < 3:
                continue

            country = self._clean_text(cells[0])
            effective_text = self._clean_text(cells[1])
            if not country or not _DATE_RE.fullmatch(effective_text):
                continue

            treaty_rows += 1
            effective_from = self._normalise_date(effective_text)

            for cell_index, cell in enumerate(cells[2:], start=2):
                relation = "treaty" if cell_index == 2 else "financial_bulletin" if cell_index == 3 else "note"
                for anchor in cell.select("a[href]"):
                    href = urljoin(page_url, anchor.get("href", ""))
                    title = self._clean_text(anchor) or Path(urlparse(href).path).name
                    if not self._valid_document_link(title, href):
                        continue
                    docs.append(
                        Document(
                            url=href,
                            source_page=page_url,
                            title=title,
                            kind=self.classify(title, href, relation),
                            country_cs=country,
                            effective_from=effective_from,
                            relation=relation,
                        )
                    )

        if treaty_rows == 0:
            raise RuntimeError("Na stránce MF nebyl nalezen žádný platný řádek smlouvy.")

        unique = {(doc.country_cs, doc.url): doc for doc in docs}
        print(
            f"Nalezeno {treaty_rows} smluvních států a {len(unique)} vazeb na dokumenty.",
            flush=True,
        )
        return list(unique.values())

    @staticmethod
    def _detect_suffix(response: requests.Response, content: bytes) -> str:
        if content.startswith(b"%PDF-"):
            return ".pdf"
        stripped = content.lstrip()
        if stripped.startswith((b"<!DOCTYPE html", b"<html", b"<HTML")):
            return ".html"
        if stripped.startswith(b"<?xml"):
            return ".xml"
        content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        by_content_type = {
            "application/pdf": ".pdf",
            "text/html": ".html",
            "application/xhtml+xml": ".html",
            "application/xml": ".xml",
            "text/xml": ".xml",
        }
        if content_type in by_content_type:
            return by_content_type[content_type]
        suffix = Path(urlparse(response.url).path).suffix.lower()
        return suffix if suffix in {".pdf", ".html", ".htm", ".xml"} else ".bin"

    def download(self, doc: Document) -> Document:
        cached = self._download_cache.get(doc.url)
        if cached is not None:
            doc.mime_type = cached.mime_type
            doc.sha256 = cached.sha256
            doc.local_path = cached.local_path
            doc.downloaded_at = cached.downloaded_at
            doc.status = cached.status
            doc.error = cached.error
            return doc

        try:
            response = self.get(doc.url)
            content = response.content
            if not content:
                raise ValueError("Server vrátil prázdný soubor")

            digest = hashlib.sha256(content).hexdigest()
            suffix = self._detect_suffix(response, content)
            folder = self.raw / doc.kind
            folder.mkdir(parents=True, exist_ok=True)
            target = folder / f"{digest[:16]}{suffix}"
            if not target.exists():
                target.write_bytes(content)

            doc.mime_type = response.headers.get("content-type")
            doc.sha256 = digest
            doc.local_path = str(target.relative_to(self.root))
            doc.downloaded_at = datetime.now(timezone.utc).isoformat()
            doc.status = "downloaded"
        except Exception as exc:
            doc.status = "failed"
            doc.error = f"{type(exc).__name__}: {exc}"

        self._download_cache[doc.url] = doc
        return doc

    def run(self) -> list[Document]:
        print("TaxTreat crawler spuštěn.", flush=True)
        docs: list[Document] = []
        try:
            docs.extend(self.discover_links(MF_TREATIES))
        except Exception as exc:
            print(f"CHYBA při načítání seznamu: {type(exc).__name__}: {exc}", flush=True)

        docs.extend(
            [
                Document(OECD_MLI, OECD_MLI, "Czech Republic MLI position", "mli", relation="global"),
                Document(EURLEX_PSD, EURLEX_PSD, "Parent-Subsidiary Directive consolidated text", "eu_directive", relation="global"),
            ]
        )

        total_links = len(docs)
        unique_urls = len({doc.url for doc in docs})
        print(f"Ke stažení: {unique_urls} unikátních dokumentů ({total_links} vazeb).", flush=True)

        out: list[Document] = []
        for index, doc in enumerate(docs, 1):
            prefix = f"{doc.country_cs} | " if doc.country_cs else ""
            print(f"[{index}/{total_links}] {prefix}{doc.title}", flush=True)
            out.append(self.download(doc))
            if out[-1].status == "failed":
                print(f"  CHYBA: {out[-1].error}", flush=True)
            if doc.url not in self._download_cache or self._download_cache[doc.url] is doc:
                time.sleep(0.15)

        manifest = self.root / "data" / "processed" / "document_manifest.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps([asdict(item) for item in out], ensure_ascii=False, indent=2), encoding="utf-8")

        downloaded_urls = {item.url for item in out if item.status == "downloaded"}
        failed_urls = {item.url for item in out if item.status == "failed"}
        print(f"Crawler dokončen: {len(downloaded_urls)}/{unique_urls} staženo, {len(failed_urls)} chyb.", flush=True)
        return out


if __name__ == "__main__":
    Crawler(Path(__file__).resolve().parents[2]).run()
