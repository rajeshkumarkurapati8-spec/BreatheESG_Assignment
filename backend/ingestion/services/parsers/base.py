from abc import ABC, abstractmethod

from ingestion.services.types import RowParseResult


class BaseIngestionParser(ABC):
    """Parse one logical row into raw payload + optional normalized output."""

    @abstractmethod
    def parse_row(self, row: dict, row_number: int) -> RowParseResult:
        pass

    def parse_rows(self, rows: list[dict]) -> list[RowParseResult]:
        return [self.parse_row(row, i + 1) for i, row in enumerate(rows)]
