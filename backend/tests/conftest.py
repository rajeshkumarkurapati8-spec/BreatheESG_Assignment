import pytest
from django.core.management import call_command


@pytest.fixture
def demo_users(db):
    call_command("seed_demo_users")
    call_command("seed_plant_codes")


@pytest.fixture
def analyst_user(demo_users):
    from tenants.models import User

    return User.objects.get(username="analyst")


@pytest.fixture
def uploader_user(demo_users):
    from tenants.models import User

    return User.objects.get(username="uploader")


@pytest.fixture
def analyst_client(analyst_user):
    from rest_framework.test import APIClient

    client = APIClient()
    client.enforce_csrf_checks = False
    client.force_authenticate(user=analyst_user)
    return client


@pytest.fixture
def uploader_client(uploader_user):
    from rest_framework.test import APIClient

    client = APIClient()
    client.enforce_csrf_checks = False
    client.force_authenticate(user=uploader_user)
    return client
