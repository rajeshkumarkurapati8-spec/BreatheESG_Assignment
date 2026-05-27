"""Shared types between parsers and the ingestion pipeline."""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any


@dataclass
class NormalizedRow:
    """Intermediate normalized row before persisting NormalizedEmissionRecord."""

    emission_scope: str
    category: str
    activity_date: date
    normalized_unit: str
    normalized_quantity: Decimal
    emission_factor: Decimal
    calculated_emissions_kg_co2e: Decimal
    source_system: str
    suspicious_flag: bool = False
    suspicious_reason: str = ""
    calculation_notes: str = ""


@dataclass
class RowParseResult:
    raw_payload: dict[str, Any]
    validation_errors: list[str] = field(default_factory=list)
    normalized: NormalizedRow | None = None
