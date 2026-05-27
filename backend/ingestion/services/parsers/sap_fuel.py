"""
SAP MM fuel / procurement CSV parser.
Handles German column names and messy exports.
"""
from decimal import Decimal

from emissions.models import EmissionScope
from emissions.services.calculation import calculate_emissions, resolve_emission_factor
from ingestion.services.normalization import NormalizationEngine
from ingestion.services.parsers.base import BaseIngestionParser
from ingestion.services.types import NormalizedRow, RowParseResult
from ingestion.services.validation import FUEL_UNITS, ValidationEngine

# Column aliases (lowercase keys after normalization)
SAP_COLUMN_MAP = {
    "werk": "werk",
    "plant": "werk",
    "plant_code": "werk",
    "brennstoffart": "fuel_type",
    "fuel_type": "fuel_type",
    "fuel": "fuel_type",
    "menge": "quantity",
    "quantity": "quantity",
    "qty": "quantity",
    "einheit": "unit",
    "unit": "unit",
    "buchungsdatum": "activity_date",
    "booking_date": "activity_date",
    "posting_date": "activity_date",
    "date": "activity_date",
}


def _normalize_row_keys(row: dict) -> dict:
    out = {}
    for k, v in row.items():
        key = str(k).strip().lower().replace(" ", "_")
        mapped = SAP_COLUMN_MAP.get(key, key)
        out[mapped] = v
    return out


class SapFuelParser(BaseIngestionParser):
    def parse_row(self, row: dict, row_number: int) -> RowParseResult:
        mapped = _normalize_row_keys(row)
        raw_payload = dict(mapped)
        errors: list[str] = []

        werk = str(mapped.get("werk") or "").strip()
        fuel_type = str(mapped.get("fuel_type") or "").strip()
        unit_raw = str(mapped.get("unit") or "").strip()
        date_raw = mapped.get("activity_date")

        plant_info = NormalizationEngine.resolve_plant(werk)
        raw_payload["resolved_plant"] = plant_info
        plant_unmapped = bool(plant_info.get("unmapped") and werk)

        activity_date, date_err = ValidationEngine.validate_date(date_raw, "Buchungsdatum")
        if date_err:
            errors.append(date_err)

        quantity, qty_err = ValidationEngine.validate_positive_decimal(
            mapped.get("quantity"), "Menge"
        )
        if qty_err:
            errors.append(qty_err)

        unit_err = ValidationEngine.validate_unit(unit_raw, FUEL_UNITS, "Einheit")
        if unit_err:
            errors.append(unit_err)

        if not fuel_type:
            errors.append("Missing Brennstoffart (fuel type)")

        if errors:
            return RowParseResult(raw_payload=raw_payload, validation_errors=errors)

        assert quantity is not None and activity_date is not None
        liters, conv_err = NormalizationEngine.fuel_to_liters(quantity, unit_raw)
        if conv_err:
            return RowParseResult(
                raw_payload=raw_payload,
                validation_errors=[conv_err],
            )

        fuel_key = NormalizationEngine.normalize_fuel_type_key(fuel_type)
        category = NormalizationEngine.map_fuel_category(fuel_type)
        factor = resolve_emission_factor(category, fuel_key)
        emissions = calculate_emissions(liters, factor)

        suspicious = plant_unmapped
        suspicious_reason = (
            f"Unmapped Werk code ({werk}) — verify plant assignment." if plant_unmapped else ""
        )

        normalized = NormalizedRow(
            emission_scope=EmissionScope.SCOPE_1,
            category=category,
            activity_date=activity_date,
            normalized_unit="liter",
            normalized_quantity=liters,
            emission_factor=factor,
            calculated_emissions_kg_co2e=emissions,
            source_system="sap_mm",
            suspicious_flag=suspicious,
            suspicious_reason=suspicious_reason,
            calculation_notes=(
                f"{liters} L × {factor} kg CO2e/L ({fuel_type} @ {plant_info['plant_name']})"
            ),
        )
        return RowParseResult(
            raw_payload=raw_payload,
            validation_errors=[],
            normalized=normalized,
        )
