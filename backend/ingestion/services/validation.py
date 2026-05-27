"""
Validation engine for ingestion rows.
"""
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

# Common SAP / EU date formats seen in exports
DATE_FORMATS = (
    "%Y-%m-%d",
    "%d.%m.%Y",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%m/%d/%Y",
    "%Y/%m/%d",
    "%d.%m.%y",
)

IATA_CODE_PATTERN = re.compile(r"^[A-Z]{3}$")

FUEL_UNITS = {"l", "liter", "litre", "liters", "litres", "ltr", "gal", "gallon", "gallons", "m3", "m³"}
ELECTRICITY_UNITS = {"kwh", "kw-h", "mwh"}
DISTANCE_UNITS = {"km", "kilometer", "kilometers"}


class ValidationEngine:
    """Reusable validators for all ingestion pipelines."""

    @staticmethod
    def parse_date(value: str | None) -> date | None:
        if value is None or str(value).strip() == "":
            return None
        text = str(value).strip()
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def validate_date(value: str | None, field_name: str = "date") -> tuple[date | None, str | None]:
        parsed = ValidationEngine.parse_date(value)
        if parsed is None:
            return None, f"Invalid or missing {field_name}: {value!r}"
        return parsed, None

    @staticmethod
    def validate_positive_decimal(
        value, field_name: str = "quantity"
    ) -> tuple[Decimal | None, str | None]:
        if value is None or str(value).strip() == "":
            return None, f"Missing {field_name}"
        try:
            cleaned = str(value).strip().replace(",", ".")
            num = Decimal(cleaned)
        except (InvalidOperation, ValueError):
            return None, f"Invalid numeric {field_name}: {value!r}"
        if num < 0:
            return None, f"Negative {field_name} not allowed: {num}"
        return num, None

    @staticmethod
    def validate_unit(value: str | None, allowed: set[str], field_name: str = "unit") -> str | None:
        if not value or str(value).strip() == "":
            return f"Missing {field_name}"
        normalized = str(value).strip().lower().replace(" ", "")
        if normalized not in allowed:
            return f"Unsupported {field_name}: {value!r}"
        return None

    @staticmethod
    def validate_airport_code(code: str | None, field_name: str) -> str | None:
        if not code or str(code).strip() == "":
            return None  # optional unless flight
        upper = str(code).strip().upper()
        if not IATA_CODE_PATTERN.match(upper):
            return f"Invalid airport code for {field_name}: {code!r}"
        return None

    @staticmethod
    def validate_billing_period(start: date | None, end: date | None) -> str | None:
        if start is None or end is None:
            return "Missing billing period start or end"
        if start > end:
            return f"Billing start {start} is after end {end}"
        return None
