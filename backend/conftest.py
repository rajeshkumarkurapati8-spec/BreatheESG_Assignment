import pytest
from django.core.management import call_command


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture(autouse=True)
def seed_plant_codes(db):
    call_command("seed_plant_codes")

