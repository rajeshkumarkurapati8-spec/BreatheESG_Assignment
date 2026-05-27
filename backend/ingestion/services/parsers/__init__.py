from ingestion.models import SourceType
from ingestion.services.parsers.sap_fuel import SapFuelParser
from ingestion.services.parsers.travel_api import TravelApiParser
from ingestion.services.parsers.utility_electricity import UtilityElectricityParser

PARSER_REGISTRY = {
    SourceType.SAP_FUEL: SapFuelParser,
    SourceType.UTILITY_ELECTRICITY: UtilityElectricityParser,
    SourceType.CORPORATE_TRAVEL: TravelApiParser,
}


def get_parser(source_type: str):
    parser_cls = PARSER_REGISTRY.get(source_type)
    if not parser_cls:
        raise ValueError(f"No parser registered for source_type={source_type!r}")
    return parser_cls()
