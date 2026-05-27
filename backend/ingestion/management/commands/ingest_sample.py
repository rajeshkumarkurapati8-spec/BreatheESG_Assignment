"""
Ingest sample seed files into the demo tenant.
Usage:
  python manage.py ingest_sample --source sap_fuel
  python manage.py ingest_sample --source utility_electricity
  python manage.py ingest_sample --source corporate_travel
  python manage.py ingest_sample --all
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand

from ingestion.models import IngestionMethod, SourceType
from ingestion.services.pipeline import create_data_source_and_ingest
from tenants.models import Tenant, User

SEED_DIR = Path(__file__).resolve().parents[3] / "seed_data"

SOURCES = {
    "sap_fuel": {
        "source_type": SourceType.SAP_FUEL,
        "method": IngestionMethod.CSV_UPLOAD,
        "filename": "sap_fuel_messy.csv",
    },
    "utility_electricity": {
        "source_type": SourceType.UTILITY_ELECTRICITY,
        "method": IngestionMethod.CSV_UPLOAD,
        "filename": "utility_electricity.csv",
    },
    "corporate_travel": {
        "source_type": SourceType.CORPORATE_TRAVEL,
        "method": IngestionMethod.API_MOCK,
        "filename": "travel_api_batch.json",
    },
}


class Command(BaseCommand):
    help = "Ingest sample seed datasets for demo tenant."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            choices=list(SOURCES.keys()),
            help="Which sample dataset to ingest.",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Ingest all sample datasets.",
        )
        parser.add_argument(
            "--tenant",
            default="Acme Industrial GmbH",
            help="Tenant company_name (default: demo tenant).",
        )
        parser.add_argument(
            "--user",
            default="uploader",
            help="Username performing upload (default: uploader).",
        )

    def handle(self, *args, **options):
        if not options["all"] and not options["source"]:
            self.stderr.write("Provide --source or --all")
            return

        tenant = Tenant.objects.get(company_name=options["tenant"])
        user = User.objects.get(username=options["user"], tenant=tenant)

        keys = list(SOURCES.keys()) if options["all"] else [options["source"]]

        for key in keys:
            spec = SOURCES[key]
            path = SEED_DIR / spec["filename"]
            if not path.exists():
                self.stderr.write(self.style.ERROR(f"Missing seed file: {path}"))
                continue

            self.stdout.write(f"Ingesting {key} from {path.name}...")

            if spec["method"] == IngestionMethod.CSV_UPLOAD:
                file_content = path.read_bytes()
                data_source = create_data_source_and_ingest(
                    tenant=tenant,
                    source_type=spec["source_type"],
                    ingestion_method=spec["method"],
                    uploaded_by=user,
                    original_filename=spec["filename"],
                    file_content=file_content,
                )
            else:
                api_payload = json.loads(path.read_text(encoding="utf-8"))
                data_source = create_data_source_and_ingest(
                    tenant=tenant,
                    source_type=spec["source_type"],
                    ingestion_method=spec["method"],
                    uploaded_by=user,
                    original_filename=spec["filename"],
                    api_payload=api_payload,
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"  DataSource #{data_source.pk} — {data_source.processing_status} — "
                    f"{data_source.processing_summary}"
                )
            )
