from taxtreat.services.calculation import build_withholding_compliance_schedule


def test_end_of_following_month_moves_weekend_deadline_to_monday():
    schedule = build_withholding_compliance_schedule(
        "2026-01-15",
        income_type="dividend",
        decision_status="FINAL",
        rate_percent=15,
    )

    assert schedule["tax_remittance_deadline"] == "2026-03-02"
    assert schedule["notification_deadline"] == "2026-03-02"
