"""
Ingestion pipeline orchestrator — selects parser, persists raw + normalized rows.
"""
import csv
import io
import logging
from typing import Any

from django.db import transaction

from audit.services.logger import log_upload_completed, log_upload_failed, log_upload_started
from emissions.models import ApprovalStatus, NormalizedEmissionRecord
from ingestion.models import IngestionMethod, ProcessingStatus, RawRecord
from ingestion.services.parsers import get_parser
from ingestion.services.parsers.utility_electricity import UtilityElectricityParser
from ingestion.services.types import NormalizedRow, RowParseResult

logger = logging.getLogger(__name__)


def load_csv_rows(file_content: bytes | str) -> list[dict[str, Any]]:
    if isinstance(file_content, bytes):
        text = file_content.decode("utf-8-sig")
    else:
        text = file_content
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


def load_api_rows(api_payload: dict | list) -> list[dict[str, Any]]:
    if isinstance(api_payload, list):
        return api_payload
    if "trips" in api_payload:
        return api_payload["trips"]
    if "records" in api_payload:
        return api_payload["records"]
    raise ValueError("API payload must be a list or contain 'trips' / 'records' key")


def _persist_normalized(
    data_source,
    raw_record: RawRecord,
    normalized: NormalizedRow,
) -> NormalizedEmissionRecord:
    return NormalizedEmissionRecord.objects.create(
        tenant=data_source.tenant,
        raw_record=raw_record,
        emission_scope=normalized.emission_scope,
        category=normalized.category,
        activity_date=normalized.activity_date,
        normalized_unit=normalized.normalized_unit,
        normalized_quantity=normalized.normalized_quantity,
        emission_factor=normalized.emission_factor,
        calculated_emissions_kg_co2e=normalized.calculated_emissions_kg_co2e,
        source_system=normalized.source_system,
        suspicious_flag=normalized.suspicious_flag,
        suspicious_reason=normalized.suspicious_reason,
        approval_status=ApprovalStatus.PENDING,
    )


@transaction.atomic
def run_ingestion(
    data_source,
    *,
    file_content: bytes | str | None = None,
    api_payload: dict | list | None = None,
    performed_by=None,
) -> dict:
    """
    Run full ingestion for a DataSource.
    Returns processing_summary dict.
    """
    data_source.processing_status = ProcessingStatus.PROCESSING
    data_source.save(update_fields=["processing_status"])
    log_upload_started(data_source, performed_by)

    summary = {
        "rows_total": 0,
        "raw_created": 0,
        "normalized_created": 0,
        "validation_failed": 0,
        "suspicious_count": 0,
    }

    try:
        if data_source.ingestion_method == IngestionMethod.CSV_UPLOAD:
            if file_content is None:
                raise ValueError("CSV ingestion requires file_content")
            rows = load_csv_rows(file_content)
        else:
            if api_payload is None:
                raise ValueError("API ingestion requires api_payload")
            rows = load_api_rows(api_payload)

        parser = get_parser(data_source.source_type)
        is_utility = isinstance(parser, UtilityElectricityParser)
        results: list[RowParseResult] = parser.parse_rows(rows)
        summary["rows_total"] = len(results)

        for row_number, result in enumerate(results, start=1):
            if is_utility and result.normalized:
                result = parser.apply_spike_check(result, data_source.tenant_id)

            raw_record = RawRecord.objects.create(
                data_source=data_source,
                raw_payload=result.raw_payload,
                row_number=row_number,
                validation_errors=result.validation_errors,
            )
            summary["raw_created"] += 1

            if result.validation_errors:
                summary["validation_failed"] += 1
                continue

            if result.normalized:
                record = _persist_normalized(data_source, raw_record, result.normalized)
                summary["normalized_created"] += 1
                if record.suspicious_flag:
                    summary["suspicious_count"] += 1

        data_source.processing_status = ProcessingStatus.COMPLETED
        data_source.processing_summary = summary
        data_source.save(update_fields=["processing_status", "processing_summary"])
        log_upload_completed(data_source, performed_by, summary)
        return summary

    except Exception as exc:
        logger.exception("Ingestion failed for DataSource %s", data_source.pk)
        data_source.processing_status = ProcessingStatus.FAILED
        summary["error"] = str(exc)
        data_source.processing_summary = summary
        data_source.save(update_fields=["processing_status", "processing_summary"])
        log_upload_failed(data_source, performed_by, str(exc))
        raise


def create_data_source_and_ingest(
    *,
    tenant,
    source_type: str,
    ingestion_method: str,
    uploaded_by,
    original_filename: str = "",
    file_content: bytes | str | None = None,
    api_payload: dict | list | None = None,
):
    """Helper for management command / future upload API."""
    from ingestion.models import DataSource

    data_source = DataSource.objects.create(
        tenant=tenant,
        source_type=source_type,
        ingestion_method=ingestion_method,
        original_filename=original_filename,
        uploaded_by=uploaded_by,
        processing_status=ProcessingStatus.PENDING,
    )
    run_ingestion(
        data_source,
        file_content=file_content,
        api_payload=api_payload,
        performed_by=uploaded_by,
    )
    return data_source
