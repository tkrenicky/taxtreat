from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class TextQualityFinding:
    code: str
    severity: str
    excerpt: str
    offset: int


SUSPICIOUS_CHARACTERS = {
    "\ufffd": "unicode_replacement_character",
    "õ": "known_pdf_encoding_corruption",
    "Õ": "known_pdf_encoding_corruption",
    "Â": "known_pdf_encoding_corruption",
    "Ï": "known_pdf_encoding_corruption",
    "Ê": "known_pdf_encoding_corruption",
}

PATTERNS = (
    (
        "isolated_ocr_pipe",
        "error",
        re.compile(r"(?<!\S)\|(?!\S)"),
    ),
    (
        "embedded_control_character",
        "error",
        re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"),
    ),
    (
        "glued_preposition",
        "warning",
        re.compile(
            r"(?iu)\b(?:v|z|s|k)"
            r"(?:tomto|tom|druhém|ostatním|němž|kterém)\b"
        ),
    ),
    (
        "glued_legal_term",
        "warning",
        re.compile(
            r"(?iu)\b(?:rezident|stát|částka|dividendy|úroky|poplatky)"
            r"(?:tohoto|tomto|druhého|smluvního|každého)\b"
        ),
    ),
    (
        "broken_article_reference",
        "error",
        re.compile(
            r"(?iu)\b(?:odstavců?|odstavce|článku)\s*[|Il]\s+"
            r"(?:a|až|nebo)\s+\d+\b"
        ),
    ),
    (
        "suspicious_spaced_word",
        "warning",
        re.compile(
            r"(?iu)\b(?:Č\s+l\s+á\s+n\s+e\s+k|"
            r"d\s+i\s+v\s+i\s+d\s+e\s+n\s+d\s+y)\b"
        ),
    ),
    (
        "glued_words",
        "error",
        re.compile(
            r"(?iu)\b(?:"
            r"použitýv|použitav|použitév|"
            r"uvedenýv|uvedenav|uvedenév|"
            r"rezidenttohoto|rezidenttomto|"
            r"státěani|státěnebo|"
            r"částkaplateb|"
            r"znerozdělených|znerozdélenych|"
            r"přihlédnutímk|prihlednutimk"
            r")\b"
        ),
    ),
    (
        "likely_ocr_word_substitution",
        "error",
        re.compile(
            r"(?iu)\b(?:"
            r"vlasmík|vlasmik|"
            r"vlastmík|vlastmik|"
            r"vyplacejici|"
            r"nerozdélenych"
            r")\b"
        ),
    ),
    (
        "stray_quote_inside_sentence",
        "warning",
        re.compile(
            r'(?u),\s*["”](?=\s*'
            r'(?:v|ve|a|nebo|který|která|které)\b)'
        ),
    ),

)


def _excerpt(
    text: str,
    start: int,
    *,
    radius: int = 55,
) -> str:
    left = max(0, start - radius)
    right = min(len(text), start + radius)

    return " ".join(
        text[left:right].split()
    )


def inspect_legal_text(
    text: str,
) -> list[TextQualityFinding]:
    findings: list[TextQualityFinding] = []

    normalized = unicodedata.normalize(
        "NFC",
        text,
    )

    for character, code in (
        SUSPICIOUS_CHARACTERS.items()
    ):
        position = normalized.find(character)

        while position >= 0:
            findings.append(
                TextQualityFinding(
                    code=code,
                    severity="error",
                    excerpt=_excerpt(
                        normalized,
                        position,
                    ),
                    offset=position,
                )
            )

            position = normalized.find(
                character,
                position + 1,
            )

    for code, severity, pattern in PATTERNS:
        for match in pattern.finditer(normalized):
            findings.append(
                TextQualityFinding(
                    code=code,
                    severity=severity,
                    excerpt=_excerpt(
                        normalized,
                        match.start(),
                    ),
                    offset=match.start(),
                )
            )

    findings.sort(
        key=lambda finding: (
            finding.offset,
            finding.code,
        )
    )

    return findings


def quality_result(text: str) -> dict:
    findings = inspect_legal_text(text)

    error_count = sum(
        finding.severity == "error"
        for finding in findings
    )

    warning_count = sum(
        finding.severity == "warning"
        for finding in findings
    )

    return {
        "character_count": len(text),
        "error_count": error_count,
        "warning_count": warning_count,
        "finding_count": len(findings),
        "automated_quality_gate_passed":
            error_count == 0,
        "clean_text_verified": False,
        "legal_text_verified": False,
        "findings": [
            asdict(finding)
            for finding in findings
        ],
    }
