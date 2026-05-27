"""
Minimal IATA airport coordinates for great-circle distance (MVP).
"""
import math
from decimal import Decimal

# lat, lon in degrees — subset for demo travel data
AIRPORT_COORDS: dict[str, tuple[float, float]] = {
    "FRA": (50.0379, 8.5622),
    "MUC": (48.3538, 11.7861),
    "HAM": (53.6304, 9.9882),
    "LHR": (51.4700, -0.4543),
    "CDG": (49.0097, 2.5479),
    "AMS": (52.3105, 4.7683),
    "JFK": (40.6413, -73.7781),
    "ORD": (41.9742, -87.9073),
    "SFO": (37.6213, -122.3790),
    "DXB": (25.2532, 55.3657),
    "SIN": (1.3644, 103.9915),
    "BER": (52.3667, 13.5033),
    "XXX": (0.0, 0.0),  # invalid test code — distance 0
}


def great_circle_km(departure: str, arrival: str) -> Decimal | None:
    dep = departure.strip().upper()
    arr = arrival.strip().upper()
    if dep not in AIRPORT_COORDS or arr not in AIRPORT_COORDS:
        return None
    if dep == arr:
        return Decimal("0")

    lat1, lon1 = AIRPORT_COORDS[dep]
    lat2, lon2 = AIRPORT_COORDS[arr]
    r = 6371.0  # Earth radius km

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return Decimal(str(round(r * c, 2)))
