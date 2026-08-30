from pathlib import Path

p = Path("taxtreat/services/reporting.py")
text = p.read_text(encoding="utf-8")

imp = "from taxtreat.services.report_locales import english_excerpt_for_citation\n"
if imp not in text:
    anchor = "from typing import Any, Mapping\n"
    if anchor not in text:
        raise SystemExit("import anchor missing")
    text = text.replace(anchor, anchor + "\n" + imp, 1)

if "english_excerpt_unavailable" not in text:
    start = text.index("    citations = [")
    end = text.index("\n\n    report = {", start)
    block = """
    if language == "en":
        recipient_country = str(request.get("recipient_country") or "")
        for citation in citations:
            if citation.get("legal_layer") not in {"treaty", "protocol", "mli"}:
                continue
            locale = english_excerpt_for_citation(citation, recipient_country)
            citation["canonical_source_url"] = citation.get("source_url")
            if locale:
                citation.update(locale)
                if locale.get("excerpt_source_url"):
                    citation["source_url"] = locale["excerpt_source_url"]
            else:
                citation["excerpt"] = None
                citation["excerpt_language"] = None
                citation["excerpt_status"] = "english_excerpt_unavailable"
                citation["excerpt_status_label"] = "English excerpt unavailable"
"""
    text = text[:end] + block + text[end:]

if "source-provenance" not in text:
    start = text.index("    source_items = []\n", text.index("def render_report_html"))
    end = text.index("    if not source_items:", start)
    block = '''    source_items = []
    for source in sources:
        url = escape(str(source.get("source_url") or ""), quote=True)
        excerpt = escape(str(source.get("excerpt") or ""))
        excerpt_html = f"<blockquote>{excerpt}</blockquote>" if excerpt else ""
        provenance = ""
        if en and source.get("legal_layer") in {"treaty", "protocol", "mli"}:
            status_label = escape(str(source.get("excerpt_status_label") or "English source status not available"))
            authority = escape(str(source.get("excerpt_authority") or ""))
            detail = f" · {authority}" if authority else ""
            provenance = f'<p class="source-provenance"><strong>English text status:</strong> {status_label}{detail}</p>'
        link_label = "Source for displayed text" if en else "Oficiální zdroj"
        source_items.append(
            f'<article class="legal-source"><div class="source-head"><h3>{_source_title(source, language)}</h3>'
            f'<a href="{url}">{link_label} ↗</a></div>{provenance}{excerpt_html}</article>'
        )
'''
    text = text[:start] + block + text[end:]

css = "blockquote{{margin:12px 0 0;padding:14px 16px;border-left:3px solid #9ebcb1;background:#f7f9f7;color:#40534d;white-space:pre-line;font:11px/1.55 Georgia,serif}}\n"
extra = ".source-provenance{{margin:8px 0 0;color:var(--muted);font-size:10px}} .source-provenance strong{{color:#536a63}}\n"
if extra not in text:
    if css not in text:
        raise SystemExit("CSS anchor missing")
    text = text.replace(css, css + extra, 1)

p.write_text(text, encoding="utf-8")
print("report provenance patch applied")
