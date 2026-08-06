from taxtreat.validation.legal_text_quality import (
    inspect_legal_text,
    quality_result,
)


def test_detects_isolated_ocr_pipe():
    result = quality_result(
        "Ustanovení odstavců | a 2 se nepoužijí."
    )

    assert result[
        "automated_quality_gate_passed"
    ] is False

    assert "isolated_ocr_pipe" in {
        finding["code"]
        for finding in result["findings"]
    }


def test_detects_known_encoding_damage():
    findings = inspect_legal_text(
        "Poškozený text õ Â Ï."
    )

    codes = {
        finding.code
        for finding in findings
    }

    assert (
        "known_pdf_encoding_corruption"
        in codes
    )


def test_detects_glued_legal_text():
    result = quality_result(
        "Příjem má zdroj vtomto druhém státě."
    )

    assert result["warning_count"] >= 1
    assert result["clean_text_verified"] is False


def test_clean_sample_passes_automatic_gate_only():
    result = quality_result(
        "Dividendy mohou být zdaněny "
        "v tomto druhém státě."
    )

    assert result[
        "automated_quality_gate_passed"
    ] is True

    assert result["clean_text_verified"] is False
    assert result["legal_text_verified"] is False


def test_detects_glued_used_in_phrase():
    result = quality_result(
        "Výraz použitýv tomto článku označuje příjmy."
    )

    assert result["error_count"] >= 1

    assert "glued_words" in {
        finding["code"]
        for finding in result["findings"]
    }


def test_detects_likely_owner_ocr_error():
    result = quality_result(
        "Skutečný vlasmík dividend je rezidentem."
    )

    assert result["error_count"] >= 1

    assert "likely_ocr_word_substitution" in {
        finding["code"]
        for finding in result["findings"]
    }


def test_detects_stray_quote_after_comma():
    result = quality_result(
        'Poplatky jsou zdaněny ve státě,"v němž mají zdroj.'
    )

    assert result["warning_count"] >= 1

    assert "stray_quote_inside_sentence" in {
        finding["code"]
        for finding in result["findings"]
    }
