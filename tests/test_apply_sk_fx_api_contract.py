from taxtreat.tools.apply_sk_fx_api_contract import build_integrated_main


BASE = '''class CnbExchangeRate(BaseModel):
    source: str = Field(pattern=r"^(?i:CNB)$")

    @field_validator("source", "currency")
    @classmethod
    def normalize_codes(cls, value: str) -> str:
        return value.upper()


class TransactionAmount(BaseModel):
    exchange_rate: CnbExchangeRate | None = None

def analyze(payload):
    calculation = build_source_country_withholding_tax_calculation(
        source_country,
        amount,
        decision_status=result.status.value,
        rate_percent=result.rate,
        tax_treatment=(
            result.tax_treatment.value
            if getattr(result, "tax_treatment", None) is not None
            else None
        ),
    )
    analysis["withholding_tax_calculation"] = calculation
'''


def test_patcher_adds_sk_ecb_nbs_contract_and_withholding_date():
    patched = build_integrated_main(BASE)
    assert "class SkExchangeRate(BaseModel):" in patched
    assert 'pattern=r"^(?i:ECB|NBS)$"' in patched
    assert "foreign_units_per_eur: Decimal" in patched
    assert "CnbExchangeRate | SkExchangeRate | None" in patched
    assert "transaction_date=payload.transaction_date" in patched


def test_patcher_is_idempotent():
    once = build_integrated_main(BASE)
    assert build_integrated_main(once) == once
