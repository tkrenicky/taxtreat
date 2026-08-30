from taxtreat.tools.apply_sk_report_localization_order_fix import (
    COMPLIANCE_BLOCK,
    build_fixed_text,
)


BROKEN = '''_SK_REPLACEMENTS = (
    ("586/1992 Sb.", "595/2003 Z. z."),
    (" ZDP)", " zákona č. 595/2003 Z. z.)"),
    ("Odvod srážkové daně", "Odvod zrážkovej dane"),
''' + COMPLIANCE_BLOCK + ''')
'''


def test_order_fixer_moves_exact_compliance_rules_before_generic_zdp_rule():
    fixed = build_fixed_text(BROKEN)

    assert fixed.count(COMPLIANCE_BLOCK) == 1
    assert fixed.index(COMPLIANCE_BLOCK) < fixed.index(
        '(" ZDP)", " zákona č. 595/2003 Z. z.)")'
    )


def test_order_fixer_is_idempotent():
    fixed = build_fixed_text(BROKEN)
    assert build_fixed_text(fixed) == fixed
