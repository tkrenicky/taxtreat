from __future__ import annotations
import hashlib, json, re, time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

MF_TREATIES = "https://mf.gov.cz/cs/zahranici-a-eu/smlouvy-o-zamezeni-dvojiho-zdaneni/prehled-platnych-smluv"
MF_GUIDANCE = "https://mf.gov.cz/cs/zahranici-a-eu/smlouvy-o-zamezeni-dvojiho-zdaneni/prehled-pokynu-a-sdeleni"
OECD_MLI = "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/beps-mli/beps-mli-position-czech-republic.pdf"
EURLEX_PSD = "https://eur-lex.europa.eu/eli/dir/2011/96/2015-02-17/eng"

@dataclass
class Document:
    url: str
    source_page: str
    title: str
    kind: str
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
        self.session.headers.update({"User-Agent": "TaxTreatLegalIngest/0.1 (+compliance research)"})

    def get(self, url: str) -> requests.Response:
        r = self.session.get(url, timeout=60, allow_redirects=True)
        r.raise_for_status()
        return r

    @staticmethod
    def classify(title: str, url: str) -> str:
        t = title.lower()
        if "protokol" in t: return "protocol"
        if "úmluva č. 32/2020" in t or "mli" in t: return "mli"
        if "finanční zpravodaj" in t or re.search(r"\bfz\b", t): return "guidance"
        if "oprava" in t or "sdělení" in t: return "notice"
        if "directive" in t or "směrnic" in t: return "eu_directive"
        if any(x in urlparse(url).netloc for x in ["mv.gov.cz", "e-sbirka.gov.cz"]): return "treaty_or_statute"
        return "other"

    def discover_links(self, page_url: str) -> list[Document]:
        html = self.get(page_url).text
        soup = BeautifulSoup(html, "lxml")
        docs=[]
        for a in soup.select("a[href]"):
            href=urljoin(page_url,a.get("href"))
            title=" ".join(a.get_text(" ",strip=True).split()) or href.rsplit("/",1)[-1]
            host=urlparse(href).netloc
            if not host: continue
            if any(domain in host for domain in ["mf.gov.cz","mfcr.cz","aplikace.mv.gov.cz","aplikace.mvcr.cz","e-sbirka.gov.cz","oecd.org","eur-lex.europa.eu"]):
                docs.append(Document(url=href,source_page=page_url,title=title,kind=self.classify(title,href)))
        unique={d.url:d for d in docs}
        return list(unique.values())

    def download(self, doc: Document) -> Document:
        try:
            r=self.get(doc.url)
            content=r.content
            digest=hashlib.sha256(content).hexdigest()
            suffix=Path(urlparse(r.url).path).suffix.lower()
            if not suffix:
                ct=r.headers.get("content-type","").split(";",1)[0]
                suffix={"application/pdf":".pdf","text/html":".html","application/xml":".xml"}.get(ct,".bin")
            folder=self.raw/doc.kind
            folder.mkdir(parents=True,exist_ok=True)
            target=folder/f"{digest[:16]}{suffix}"
            target.write_bytes(content)
            doc.mime_type=r.headers.get("content-type")
            doc.sha256=digest
            doc.local_path=str(target.relative_to(self.root))
            doc.downloaded_at=datetime.now(timezone.utc).isoformat()
            doc.status="downloaded"
        except Exception as exc:
            doc.status="failed"; doc.error=f"{type(exc).__name__}: {exc}"
        return doc

    def run(self) -> list[Document]:
        docs=[]
        for page in [MF_TREATIES, MF_GUIDANCE]:
            docs.extend(self.discover_links(page))
        docs.extend([
            Document(OECD_MLI, OECD_MLI, "Czech Republic MLI position", "mli"),
            Document(EURLEX_PSD, EURLEX_PSD, "Parent-Subsidiary Directive consolidated text", "eu_directive"),
        ])
        unique={d.url:d for d in docs}
        out=[]
        for i,doc in enumerate(unique.values(),1):
            out.append(self.download(doc)); time.sleep(0.25)
        manifest=self.root/"data"/"processed"/"document_manifest.json"
        manifest.parent.mkdir(parents=True,exist_ok=True)
        manifest.write_text(json.dumps([asdict(x) for x in out],ensure_ascii=False,indent=2),encoding="utf-8")
        return out

if __name__ == "__main__":
    root=Path(__file__).resolve().parents[2]
    result=Crawler(root).run()
    ok=sum(x.status=="downloaded" for x in result)
    print(f"Downloaded {ok}/{len(result)} documents")
