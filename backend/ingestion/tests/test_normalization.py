from decimal import Decimal

import pytest

from ingestion.services.normalization import NormalizationEngine


def test_fuel_gallons_to_liters():
    liters, err = NormalizationEngine.fuel_to_liters(Decimal("10"), "gallon")
    assert err is None
    assert liters == Decimal("37.854100")


def test_billing_midpoint():
    from datetime import date

    mid = NormalizationEngine.billing_period_midpoint(
        date(2024, 1, 1), date(2024, 1, 31)
    )
    assert mid == date(2024, 1, 16)
