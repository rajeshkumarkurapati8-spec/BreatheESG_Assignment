import datetime
from decimal import Decimal

from ingestion.services.normalization import NormalizationEngine
from ingestion.services.validation import ValidationEngine


def test_gallons_to_liters_conversion():
    quantity = Decimal("10")

    liters, error = NormalizationEngine.fuel_to_liters(quantity, "gallons")

    assert error is None
    assert liters == Decimal("37.854100")


def test_mixed_sap_date_normalization():
    expected = datetime.date(2025, 12, 31)

    assert NormalizationEngine.parse_activity_date("31.12.2025") == expected
    assert NormalizationEngine.parse_activity_date("12/31/2025") == expected
    assert NormalizationEngine.parse_activity_date("2025/12/31") == expected
    assert NormalizationEngine.parse_activity_date("2025-12-31") == expected


def test_utility_billing_midpoint_date():
    start = datetime.date(2025, 1, 1)
    end = datetime.date(2025, 1, 31)

    midpoint = NormalizationEngine.billing_period_midpoint(start, end)

    assert midpoint == datetime.date(2025, 1, 16)


def test_invalid_unit_rejection():
    quantity = Decimal("100")

    normalized, error = NormalizationEngine.fuel_to_liters(quantity, "ounces")

    assert normalized == quantity
    assert error == "Cannot convert unit 'ounces' to liters"


def test_negative_quantity_validation():
    value, error = ValidationEngine.validate_positive_decimal("-12.4")

    assert value is None
    assert error == "Negative quantity not allowed: -12.4"
