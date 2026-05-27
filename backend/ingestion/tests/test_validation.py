import pytest

from ingestion.services.validation import ValidationEngine


@pytest.mark.parametrize(
    "value,expected",
    [
        ("15.03.2024", "2024-03-15"),
        ("03/15/2024", "2024-03-15"),
        ("2024-03-15", "2024-03-15"),
    ],
)
def test_parse_date_formats(value, expected):
    parsed = ValidationEngine.parse_date(value)
    assert parsed.isoformat() == expected


def test_parse_date_invalid():
    assert ValidationEngine.parse_date("not-a-date") is None


def test_validate_negative_quantity():
    qty, err = ValidationEngine.validate_positive_decimal(-10, "qty")
    assert qty is None
    assert "Negative" in err


def test_validate_airport_code():
    assert ValidationEngine.validate_airport_code("FRA", "dep") is None
    assert ValidationEngine.validate_airport_code("fra1", "dep") is not None


def test_validate_billing_period():
    from datetime import date

    err = ValidationEngine.validate_billing_period(date(2024, 6, 1), date(2024, 1, 1))
    assert err is not None
