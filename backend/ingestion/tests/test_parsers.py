from decimal import Decimal

import pytest

from ingestion.services.parsers.sap_fuel import SapFuelParser
from ingestion.services.parsers.travel_api import TravelApiParser
from ingestion.services.parsers.utility_electricity import UtilityElectricityParser


@pytest.mark.django_db
def test_sap_fuel_valid_row():
    parser = SapFuelParser()
    result = parser.parse_row(
        {
            "Werk": "DE01",
            "Brennstoffart": "Dieselkraftstoff",
            "Menge": "100",
            "Einheit": "L",
            "Buchungsdatum": "15.03.2024",
        },
        1,
    )
    assert not result.validation_errors
    assert result.normalized is not None
    assert result.normalized.normalized_unit == "liter"
    assert result.normalized.calculated_emissions_kg_co2e > 0


@pytest.mark.django_db
def test_sap_fuel_negative_quantity():
    parser = SapFuelParser()
    result = parser.parse_row(
        {
            "Werk": "DE01",
            "Brennstoffart": "Diesel",
            "Menge": "-5",
            "Einheit": "L",
            "Buchungsdatum": "2024-01-01",
        },
        1,
    )
    assert result.validation_errors
    assert result.normalized is None


def test_utility_valid_row():
    parser = UtilityElectricityParser()
    result = parser.parse_row(
        {
            "meter_id": "MTR-1",
            "billing_start": "2024-01-01",
            "billing_end": "2024-01-31",
            "kwh_usage": "1000",
            "tariff_type": "standard",
            "facility_name": "Plant A",
        },
        1,
    )
    assert not result.validation_errors
    assert result.normalized.emission_scope == "scope2"


def test_travel_invalid_airport():
    parser = TravelApiParser()
    result = parser.parse_row(
        {
            "employee_id": "E1",
            "trip_type": "air",
            "departure_airport": "FRA",
            "arrival_airport": "ZZZ",
            "hotel_nights": 0,
            "taxi_distance_km": 0,
            "trip_date": "2024-01-01",
        },
        1,
    )
    assert result.validation_errors


@pytest.mark.django_db
def test_utility_spike_no_history_not_flagged():
    from emissions.services.suspicious import check_utility_usage_spike
    from tenants.models import Tenant

    tenant = Tenant.objects.create(company_name="Spike Test Co", industry="Test")
    flagged, reason = check_utility_usage_spike(
        tenant_id=tenant.pk,
        meter_id="MTR-X",
        kwh_usage=Decimal("50000"),
    )
    assert flagged is False
    assert reason == ""
