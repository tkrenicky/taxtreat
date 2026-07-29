import re

RATE_RE = re.compile(
    r"(?:tax|rate|exceed)[^.]{0,60}?(\d+(?:\.\d+)?)\s*%",
    re.IGNORECASE,
)

OWNERSHIP_RE = re.compile(
    r"(?:holds?|ownership|capital)[^.]{0,40}?(\d+(?:\.\d+)?)\s*%",
    re.IGNORECASE,
)

def extract_dividend_rule(text):
    return {
        "transaction_type": "dividend",
        "withholding_rates": [float(x) for x in RATE_RE.findall(text)],
        "ownership_thresholds": [float(x) for x in OWNERSHIP_RE.findall(text)],
    }

HOLDING_RE = re.compile(
    r"(?:for at least|during)[^.]{0,30}?(\d+)\s*(?:days?|months?|years?)",
    re.IGNORECASE,
)

BENEFICIAL_OWNER_RE = re.compile(
    r"beneficial owner",
    re.IGNORECASE,
)

def extract_dividend_rule(text):
    holding = HOLDING_RE.search(text)

    return {
        "transaction_type": "dividend",
        "withholding_rates": [float(x) for x in RATE_RE.findall(text)],
        "ownership_thresholds": [float(x) for x in OWNERSHIP_RE.findall(text)],
        "holding_period": holding.group(0) if holding else None,
        "beneficial_owner_required": bool(BENEFICIAL_OWNER_RE.search(text)),
    }
