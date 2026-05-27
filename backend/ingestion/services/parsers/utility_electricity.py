"""
Utility portal electricity CSV parser.
"""
from decimal import Decimal

from emissions.models import EmissionScope
from emissions.services.calculation import calculate_emissions, resolve_emission_factor
from ingestion.services.normalization import NormalizationEngine
from ingestion.services.parsers.base import BaseIngestionParser
from ingestion.services.types import NormalizedRow, RowParseResult
from ingestion.services.validation import ValidationEngine

UTILITY_COLUMN_MAP = {
    "meter_id": "meter_id",
    "meter": "meter_id",
    "billing_start": "billing_start",
    "start_date": "billing_start",
    "billing_end": "billing_end",
    "end_date": "billing_end",
    "kwh_usage": "kwh_usage",
    "kwh": "kwh_usage",
    "usage_kwh": "kwh_usage",
    "tariff_type": "tariff_type",
    "tariff": "tariff_type",
    "facility_name": "facility_name",
    "facility": "facility_name",
}


def _normalize_row_keys(row: dict) -> dict:
    out = {}
    for k, v in row.items():
        key = str(k).strip().lower().replace(" ", "_")
        out[UTILITY_COLUMN_MAP.get(key, key)] = v
    return out


class UtilityElectricityParser(BaseIngestionParser):
    def parse_row(self, row: dict, row_number: int) -> RowParseResult:
        mapped = _normalize_row_keys(row)
        raw_payload = dict(mapped)
        errors: list[str] = []

        meter_id = str(mapped.get("meter_id") or "").strip()
        if not meter_id:
            errors.append("Missing meter_id")

        billing_start, err_s = ValidationEngine.validate_date(
            mapped.get("billing_start"), "billing_start"
        )
        if err_s:
            errors.append(err_s)

        billing_end, err_e = ValidationEngine.validate_date(
            mapped.get("billing_end"), "billing_end"
        )
        if err_e:
            errors.append(err_e)

        period_err = ValidationEngine.validate_billing_period(billing_start, billing_end)
        if period_err:
            errors.append(period_err)

        kwh, kwh_err = ValidationEngine.validate_positive_decimal(
            mapped.get("kwh_usage"), "kwh_usage"
        )
        if kwh_err:
            errors.append(kwh_err)

        if errors:
            return RowParseResult(raw_payload=raw_payload, validation_errors=errors)

        assert billing_start and billing_end and kwh is not None
        activity_date = NormalizationEngine.billing_period_midpoint(billing_start, billing_end)
        category = "purchased_electricity"
        factor = resolve_emission_factor(category)
        emissions = calculate_emissions(kwh, factor)

        raw_payload["billing_midpoint"] = activity_date.isoformat()

        normalized = NormalizedRow(
            emission_scope=EmissionScope.SCOPE_2,
            category=category,
            activity_date=activity_date,
            normalized_unit="kwh",
            normalized_quantity=kwh,
            emission_factor=factor,
            calculated_emissions_kg_co2e=emissions,
            source_system="utility_portal",
            calculation_notes=f"{kwh} kWh × {factor} kg CO2e/kWh (midpoint {activity_date})",
        )
        return RowParseResult(
            raw_payload=raw_payload,
            validation_errors=[],
            normalized=normalized,
        )

    def apply_spike_check(
        self, result: RowParseResult, tenant_id: int
    ) -> RowParseResult:
        """Called by pipeline after DB history may exist; updates suspicious flags."""
        from emissions.services.suspicious import check_utility_usage_spike

        if not result.normalized:
            return result
        meter_id = str(result.raw_payload.get("meter_id") or "")
        if not meter_id:
            return result
        flagged, reason = check_utility_usage_spike(
            tenant_id=tenant_id,
            meter_id=meter_id,
            kwh_usage=result.normalized.normalized_quantity,
        )
        if flagged:
            result.normalized.suspicious_flag = True
            result.normalized.suspicious_reason = reason
        return result
