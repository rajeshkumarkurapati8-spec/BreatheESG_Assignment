"""
Simplified emission factors for MVP (kg CO2e per activity unit).
Real deployments would use DEFRA/EPA/eGRID with versioning.
"""
from decimal import Decimal

# Fuel — per liter
DIESEL_KG_PER_LITER = Decimal("2.68")
PETROL_KG_PER_LITER = Decimal("2.31")
HEATING_OIL_KG_PER_LITER = Decimal("2.96")
DEFAULT_FUEL_KG_PER_LITER = Decimal("2.50")

# Electricity — per kWh (grid average placeholder)
ELECTRICITY_KG_PER_KWH = Decimal("0.40")

# Travel — per km or per night
FLIGHT_KG_PER_KM = Decimal("0.15")
TAXI_KG_PER_KM = Decimal("0.21")
HOTEL_KG_PER_NIGHT = Decimal("30.0")

# SAP fuel type (German / English) → factor per liter after normalization
FUEL_TYPE_FACTORS: dict[str, Decimal] = {
    "diesel": DIESEL_KG_PER_LITER,
    "dieselkraftstoff": DIESEL_KG_PER_LITER,
    "benzin": PETROL_KG_PER_LITER,
    "petrol": PETROL_KG_PER_LITER,
    "gasoline": PETROL_KG_PER_LITER,
    "heizöl": HEATING_OIL_KG_PER_LITER,
    "heizoel": HEATING_OIL_KG_PER_LITER,
    "heating oil": HEATING_OIL_KG_PER_LITER,
}
