"""
Create a demo tenant and users for local development / evaluation.
Password for all demo users: demo1234 (never use in production).
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from tenants.models import Tenant, User

DEMO_PASSWORD = "demo1234"


class Command(BaseCommand):
    help = "Seed demo tenant, analyst, and uploader users."

    def handle(self, *args, **options):
        with transaction.atomic():
            tenant, t_created = Tenant.objects.get_or_create(
                company_name="Acme Industrial GmbH",
                defaults={"industry": "Manufacturing"},
            )

            users_spec = [
                {
                    "username": "analyst",
                    "email": "analyst@acme-demo.local",
                    "is_analyst": True,
                    "is_uploader": False,
                },
                {
                    "username": "uploader",
                    "email": "uploader@acme-demo.local",
                    "is_analyst": False,
                    "is_uploader": True,
                },
            ]

            for spec in users_spec:
                user, u_created = User.objects.get_or_create(
                    username=spec["username"],
                    defaults={
                        "email": spec["email"],
                        "tenant": tenant,
                        "is_analyst": spec["is_analyst"],
                        "is_uploader": spec["is_uploader"],
                    },
                )
                user.tenant = tenant
                user.email = spec["email"]
                user.is_analyst = spec["is_analyst"]
                user.is_uploader = spec["is_uploader"]
                if u_created or not user.check_password(DEMO_PASSWORD):
                    user.set_password(DEMO_PASSWORD)
                user.save()

                self.stdout.write(
                    f"  {'Created' if u_created else 'Updated'} user: {user.username}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo tenant '{tenant.company_name}' ready. "
                f"Login: analyst / uploader — password: {DEMO_PASSWORD}"
            )
        )
