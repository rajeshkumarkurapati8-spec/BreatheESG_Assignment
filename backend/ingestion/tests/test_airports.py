from ingestion.services.parsers.airports import great_circle_km


def test_great_circle_fra_lhr():
    km = great_circle_km("FRA", "LHR")
    assert km is not None
    assert 500 < km < 800


def test_unknown_airport():
    assert great_circle_km("FRA", "ZZZ") is None
