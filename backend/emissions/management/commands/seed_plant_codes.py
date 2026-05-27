from django.core.management.base import BaseCommand

from emissions.models import PlantCodeLookup

# Realistic SAP-style plant codes (fictional but believable for demo)
DEFAULT_PLANTS = [
    {"code": "DE01", "plant_name": "Hamburg Manufacturing", "country": "DE"},
    {"code": "DE02", "plant_name": "Munich Assembly", "country": "DE"},
    {"code": "DE03", "plant_name": "Berlin Office Campus", "country": "DE"},
    {"code": "PL01", "plant_name": "Wroclaw Distribution", "country": "PL"},
    {"code": "NL01", "plant_name": "Rotterdam Logistics Hub", "country": "NL"},
    {"code": "FR01", "plant_name": "Lyon Production", "country": "FR"},
    {"code": "UK01", "plant_name": "Manchester Plant", "country": "GB"},
    {"code": "US01", "plant_name": "Austin TX Facility", "country": "US"},
    {"code": "US02", "plant_name": "Chicago Regional Office", "country": "US"},
    {"code": "UNKNOWN", "plant_name": "Unmapped Plant (Review Required)", "country": "XX"},
]


class Command(BaseCommand):
    help = "Seed PlantCodeLookup reference table for SAP Werk resolution."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing plant codes before seeding.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            deleted, _ = PlantCodeLookup.objects.all().delete()
            self.stdout.write(f"Cleared {deleted} plant code(s).")

        created = 0
        updated = 0
        for row in DEFAULT_PLANTS:
            _, was_created = PlantCodeLookup.objects.update_or_create(
                code=row["code"],
                defaults={
                    "plant_name": row["plant_name"],
                    "country": row["country"],
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Plant codes: {created} created, {updated} updated "
                f"({len(DEFAULT_PLANTS)} total)."
            )
        )
