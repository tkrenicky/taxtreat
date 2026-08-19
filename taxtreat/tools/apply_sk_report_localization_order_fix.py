from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "taxtreat" / "services" / "reporting" / "html_localization.py"

EARLY_ANCHOR = '''    ("586/1992 Sb.", "595/2003 Z. z."),
    (" ZDP)", " zákona č. 595/2003 Z. z.)"),
'''

COMPLIANCE_BLOCK = '''    (
        "Oznámení o příjmech plynoucích do zahraničí (§ 38da ZDP)",
        "Oznámenie o zrazení a odvedení dane (§ 43 ods. 11)",
    ),
    ("§ 38da ZDP", "§ 43 ods. 11"),
    ("§ 38d ZDP", "§ 43 ods. 11"),
'''

EARLY_REPLACEMENT = '''    ("586/1992 Sb.", "595/2003 Z. z."),
''' + COMPLIANCE_BLOCK + '''    (" ZDP)", " zákona č. 595/2003 Z. z.)"),
'''


def build_fixed_text(text: str) -> str:
    early_pos = text.find(EARLY_ANCHOR)
    block_pos = text.find(COMPLIANCE_BLOCK)

    if early_pos < 0:
        # Already fixed is accepted only when the compliance block is before
        # the generic ZDP replacement.
        generic_pos = text.find('    (" ZDP)", " zákona č. 595/2003 Z. z.)"),')
        if block_pos >= 0 and generic_pos >= 0 and block_pos < generic_pos:
            return text
        raise RuntimeError("Expected Slovak localization ordering anchor not found; refusing to patch.")

    if block_pos < 0:
        raise RuntimeError("Expected Slovak compliance localization block not found; refusing to patch.")
    if block_pos < early_pos:
        return text

    text = text.replace(EARLY_ANCHOR, EARLY_REPLACEMENT, 1)
    # Remove the original later occurrence, preserving the newly inserted first one.
    first = text.find(COMPLIANCE_BLOCK)
    second = text.find(COMPLIANCE_BLOCK, first + len(COMPLIANCE_BLOCK))
    if first < 0 or second < 0:
        raise RuntimeError("Could not identify duplicate compliance block after insertion; refusing to patch.")
    text = text[:second] + text[second + len(COMPLIANCE_BLOCK):]
    return text


def main() -> None:
    original = TARGET.read_text(encoding="utf-8")
    fixed = build_fixed_text(original)
    if fixed == original:
        print("SK report localization ordering already fixed; no changes.")
        return
    TARGET.write_text(fixed, encoding="utf-8")
    print("Applied SK report localization ordering fix.")


if __name__ == "__main__":
    main()
