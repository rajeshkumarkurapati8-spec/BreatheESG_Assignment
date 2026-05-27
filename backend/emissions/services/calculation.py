from decimal import Decimal

from emissions.services import factors


def resolve_emission_factor(category: str, fuel_type: str | None = None) -> Decimal:
    """Return kg CO2e per normalized unit for a category."""
    if fuel_type:
        key = fuel_type.strip().lower()
        if key in factors.FUEL_TYPE_FACTORS:
            return factors.FUEL_TYPE_FACTORS[key]

    category_key = category.strip().lower()
    mapping = {
        "stationary_combustion": factors.DEFAULT_FUEL_KG_PER_LITER,
        "purchased_electricity": factors.ELECTRICITY_KG_PER_KWH,
        "business_travel_air": factors.FLIGHT_KG_PER_KM,
        "business_travel_ground": factors.TAXI_KG_PER_KM,
        "business_travel_hotel": factors.HOTEL_KG_PER_NIGHT,
        "business_travel_combined": factors.FLIGHT_KG_PER_KM,
    }
    return mapping.get(category_key, factors.DEFAULT_FUEL_KG_PER_LITER)


def calculate_emissions(quantity: Decimal, emission_factor: Decimal) -> Decimal:
    """quantity × factor, rounded to 6 decimal places."""
    return (quantity * emission_factor).quantize(Decimal("0.000001"))
