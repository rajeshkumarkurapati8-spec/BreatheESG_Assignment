"""
Mock Concur/Navan-style corporate travel API ingestion.
"""
from decimal import Decimal

from emissions.models import EmissionScope
from emissions.services import factors
from emissions.services.calculation import calculate_emissions
from ingestion.services.parsers.airports import great_circle_km
from ingestion.services.parsers.base import BaseIngestionParser
from ingestion.services.types import NormalizedRow, RowParseResult
from ingestion.services.validation import ValidationEngine

VALID_TRIP_TYPES = {"air", "hotel", "ground", "mixed"}


class TravelApiParser(BaseIngestionParser):
    def parse_row(self, row: dict, row_number: int) -> RowParseResult:
        raw_payload = dict(row)
        errors: list[str] = []

        employee_id = str(row.get("employee_id") or "").strip()
        trip_type = str(row.get("trip_type") or "mixed").strip().lower()
        dep = str(row.get("departure_airport") or "").strip().upper()
        arr = str(row.get("arrival_airport") or "").strip().upper()
        hotel_nights_raw = row.get("hotel_nights")
        taxi_km_raw = row.get("taxi_distance_km")

        if not employee_id:
            errors.append("Missing employee_id")
        if trip_type not in VALID_TRIP_TYPES:
            errors.append(f"Invalid trip_type: {trip_type!r}")

        for code, label in ((dep, "departure_airport"), (arr, "arrival_airport")):
            if code:
                err = ValidationEngine.validate_airport_code(code, label)
                if err:
                    errors.append(err)

        hotel_nights = Decimal("0")
        if hotel_nights_raw not in (None, ""):
            hn, hn_err = ValidationEngine.validate_positive_decimal(
                hotel_nights_raw, "hotel_nights"
            )
            if hn_err:
                errors.append(hn_err)
            else:
                hotel_nights = hn or Decimal("0")

        taxi_km = Decimal("0")
        if taxi_km_raw not in (None, ""):
            tk, tk_err = ValidationEngine.validate_positive_decimal(
                taxi_km_raw, "taxi_distance_km"
            )
            if tk_err:
                errors.append(tk_err)
            else:
                taxi_km = tk or Decimal("0")

        if trip_type == "air" and (not dep or not arr):
            errors.append("Air trip requires departure and arrival airports")

        if errors:
            return RowParseResult(raw_payload=raw_payload, validation_errors=errors)

        flight_km = Decimal("0")
        flight_em = Decimal("0")
        if dep and arr:
            distance = great_circle_km(dep, arr)
            if distance is None:
                errors.append(f"Unknown airport pair: {dep} → {arr}")
                return RowParseResult(raw_payload=raw_payload, validation_errors=errors)
            flight_km = distance
            flight_em = calculate_emissions(flight_km, factors.FLIGHT_KG_PER_KM)

        hotel_em = calculate_emissions(hotel_nights, factors.HOTEL_KG_PER_NIGHT)
        taxi_em = calculate_emissions(taxi_km, factors.TAXI_KG_PER_KM)
        total_em = flight_em + hotel_em + taxi_em

        if total_em <= 0:
            errors.append("No travel activity quantities to calculate emissions")
            return RowParseResult(raw_payload=raw_payload, validation_errors=errors)

        # Activity date from payload or default
        from datetime import date as date_cls

        trip_date_raw = row.get("trip_date") or row.get("activity_date")
        if trip_date_raw:
            activity_date, date_err = ValidationEngine.validate_date(trip_date_raw, "trip_date")
            if date_err:
                errors.append(date_err)
                return RowParseResult(raw_payload=raw_payload, validation_errors=errors)
        else:
            activity_date = date_cls.today()

        primary_qty = flight_km if flight_km > 0 else (hotel_nights if hotel_nights > 0 else taxi_km)
        primary_unit = "km" if flight_km > 0 or taxi_km > 0 else "night"
        if primary_qty <= 0:
            primary_qty = Decimal("1")
            primary_unit = "trip"

        effective_factor = (total_em / primary_qty).quantize(Decimal("0.000001"))

        if flight_km > 0:
            category = "business_travel_air"
        elif hotel_nights > 0:
            category = "business_travel_hotel"
        else:
            category = "business_travel_ground"

        if trip_type == "mixed" or (flight_km > 0 and (hotel_nights > 0 or taxi_km > 0)):
            category = "business_travel_combined"

        notes = (
            f"Flight: {flight_km} km → {flight_em} kg; "
            f"Hotel: {hotel_nights} nights → {hotel_em} kg; "
            f"Taxi: {taxi_km} km → {taxi_em} kg"
        )
        raw_payload["flight_km"] = str(flight_km)
        raw_payload["calculated_breakdown"] = {
            "flight_kg_co2e": str(flight_em),
            "hotel_kg_co2e": str(hotel_em),
            "taxi_kg_co2e": str(taxi_em),
        }

        normalized = NormalizedRow(
            emission_scope=EmissionScope.SCOPE_3,
            category=category,
            activity_date=activity_date,
            normalized_unit=primary_unit,
            normalized_quantity=primary_qty,
            emission_factor=effective_factor,
            calculated_emissions_kg_co2e=total_em.quantize(Decimal("0.000001")),
            source_system="concur_mock",
            calculation_notes=notes,
        )
        return RowParseResult(
            raw_payload=raw_payload,
            validation_errors=[],
            normalized=normalized,
        )
