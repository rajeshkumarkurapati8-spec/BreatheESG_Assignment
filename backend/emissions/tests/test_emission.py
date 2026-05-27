import datetime
from decimal import Decimal

import pytest

from emissions.models import NormalizedEmissionRecord
from emissions.services.calculation import calculate_emissions, resolve_emission_factor
from emissions.services.suspicious import check_utility_usage_spike
from ingestion.models import DataSource, RawRecord
from tenants.models import Tenant


@pytest.mark.django_db
def test_fuel_emissions_calculation():
    emission_factor = resolve_emission_factor("stationary_combustion")
    result = calculate_emissions(Decimal("10"), emission_factor)

    assert emission_factor == Decimal("2.50")
    assert result == Decimal("25.000000")


@pytest.mark.django_db
def test_electricity_emissions_calculation():
    emission_factor = resolve_emission_factor("purchased_electricity")
    result = calculate_emissions(Decimal("100"), emission_factor)

    assert emission_factor == Decimal("0.40")
    assert result == Decimal("40.000000")


@pytest.mark.django_db
def test_travel_emissions_calculation():
    emission_factor = resolve_emission_factor("business_travel_air")
    result = calculate_emissions(Decimal("200"), emission_factor)

    assert emission_factor == Decimal("0.15")
    assert result == Decimal("30.000000")


@pytest.mark.django_db
def test_emission_factor_application_for_fuel_type():
    emission_factor = resolve_emission_factor("stationary_combustion", fuel_type="diesel")
    result = calculate_emissions(Decimal("10"), emission_factor)

    assert emission_factor == Decimal("2.68")
    assert result == Decimal("26.800000")


@pytest.mark.django_db
def test_suspicious_utility_spikes():
    tenant = Tenant.objects.create(company_name="Electric Co", industry="Utilities")
    base_date = datetime.date(2025, 6, 1)

    data_source = DataSource.objects.create(
        tenant=tenant,
        source_type="utility_electricity",
        ingestion_method="csv_upload",
        original_filename="test_meter.csv",
    )
    raw_record_payload = {"meter_id": "MTR-123"}
    for i, usage in enumerate((100, 105), start=1):
        raw_record = RawRecord.objects.create(
            data_source=data_source,
            raw_payload=raw_record_payload,
            row_number=i,
        )
        NormalizedEmissionRecord.objects.create(
            tenant=tenant,
            category="purchased_electricity",
            emission_scope="scope2",
            activity_date=base_date - datetime.timedelta(days=i * 30),
            normalized_unit="kwh",
            normalized_quantity=Decimal(usage),
            emission_factor=Decimal("0.40"),
            calculated_emissions_kg_co2e=(Decimal(usage) * Decimal("0.40")).quantize(Decimal("0.000001")),
            source_system="utility_portal",
            raw_record=raw_record,
        )

    flagged, reason = check_utility_usage_spike(
        tenant_id=tenant.pk,
        meter_id="MTR-123",
        kwh_usage=Decimal("210"),
    )

    assert flagged is True
    assert "Usage 210 kWh" in reason
    assert "rolling average" in reason

    no_flagged, no_reason = check_utility_usage_spike(
        tenant_id=tenant.pk,
        meter_id="MTR-123",
        kwh_usage=Decimal("200"),
    )

    assert no_flagged is False
    assert no_reason == ""
