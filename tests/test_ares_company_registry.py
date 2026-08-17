from app.main import _normalize_ares_subject


def test_normalize_ares_subject_exposes_form_fields():
    payload = {
        "ico": "27082440",
        "obchodniJmeno": "Google Czech Republic, s.r.o.",
        "dic": "CZ27082440",
        "pravniForma": "112",
        "datumVzniku": "2003-10-08",
        "sidlo": {"textovaAdresa": "Stroupežnického 3191/17, 150 00 Praha 5"},
        "datoveSchranky": [{"datovaSchranka": "amqg4i4"}],
    }
    result = _normalize_ares_subject(payload)
    assert result["ico"] == "27082440"
    assert result["name"] == "Google Czech Republic, s.r.o."
    assert result["vat_id"] == "CZ27082440"
    assert result["address"] == "Stroupežnického 3191/17, 150 00 Praha 5"
    assert result["legal_form"] == "112"
    assert result["data_box"] == "amqg4i4"
    assert result["established_at"] == "2003-10-08"
