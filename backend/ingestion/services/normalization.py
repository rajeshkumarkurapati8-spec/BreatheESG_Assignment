"""
Normalization engine — dates, units, categories.
"""
from datetime import date
from decimal import Decimal

from emissions.models import PlantCodeLookup
from ingestion.services.validation import ValidationEngine

# 1 US gallon ≈ 3.78541 liters; 1 m³ gas ≈ 1000 L equivalent (rough MVP factor)
GALLONS_TO_LITERS = Decimal("3.78541")
M3_TO_LITERS = Decimal("1000")


class NormalizationEngine:
    @staticmethod
    def parse_activity_date(value: str | None) -> date | None:
        return ValidationEngine.parse_date(value)

    @staticmethod
    def billing_period_midpoint(start: date, end: date) -> date:
        delta = (end - start).days // 2
        from datetime import timedelta

        return start + timedelta(days=delta)

    @staticmethod
    def fuel_to_liters(quantity: Decimal, unit: str) -> tuple[Decimal, str | None]:
        u = unit.strip().lower().replace(" ", "").replace("³", "3")
        if u in ("l", "liter", "litre", "liters", "litres", "ltr"):
            return quantity, None
        if u in ("gal", "gallon", "gallons"):
            return (quantity * GALLONS_TO_LITERS).quantize(Decimal("0.000001")), None
        if u in ("m3",):
            return (quantity * M3_TO_LITERS).quantize(Decimal("0.000001")), None
        return quantity, f"Cannot convert unit {unit!r} to liters"

    @staticmethod
    def resolve_plant(werk_code: str) -> dict:
        code = (werk_code or "").strip().upper()
        if not code:
            return {"code": "", "plant_name": "Unknown", "country": "", "unmapped": True}
        try:
            plant = PlantCodeLookup.objects.get(code=code)
            return {
                "code": plant.code,
                "plant_name": plant.plant_name,
                "country": plant.country,
                "unmapped": plant.code == "UNKNOWN",
            }
        except PlantCodeLookup.DoesNotExist:
            return {
                "code": code,
                "plant_name": "Unmapped Plant",
                "country": "",
                "unmapped": True,
            }

    @staticmethod
    def map_fuel_category(fuel_type: str) -> str:
        return "stationary_combustion"

    @staticmethod
    def normalize_fuel_type_key(fuel_type: str) -> str:
        return fuel_type.strip().lower()
