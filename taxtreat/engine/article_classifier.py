import re

from taxtreat.parser.article_selection import article_type


def classify_article(title: str, text: str = "") -> str:
    if not title:
        return "other"

    income_type = article_type({"title": title, "text": text})
    if income_type is not None:
        return income_type

    text = title.lower()
    normalized = re.sub(r"[^a-záčďéěíňóřšťúůýž\s]", " ", text)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    if any(keyword in normalized for keyword in ["dividendy", "dividends", "dividend"]):
        return "dividend"
    if any(keyword in normalized for keyword in ["úroky", "uroky", "interest", "interests", "interest"]):
        return "interest"
    if any(keyword in normalized for keyword in ["licencni poplatky", "licencni", "royalties", "royalty", "licenční poplatky"]):
        return "royalty"
    if any(keyword in normalized for keyword in ["stálá provozovna", "stala provozovna", "permanent establishment", "permanent establishments", "pe"]):
        return "permanent_establishment"
    if any(keyword in normalized for keyword in ["zisky podniků", "zisky podniku", "business profits", "business profit", "business"]):
        return "business_profits"
    if any(keyword in normalized for keyword in ["kapitálové zisky", "kapitalove zisky", "capital gains", "capital gain"]):
        return "capital_gains"
    if any(keyword in normalized for keyword in ["zaměstnání", "zamestnani", "employment", "employee", "employees"]):
        return "employment"

    return "other"
