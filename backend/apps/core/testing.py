"""
Helpers shared by the test suites.

MongoDB (standalone) has no transactions, so Django flushes the test database
after every test. Each test therefore builds the data it needs with these
small factories instead of relying on data migrations.
"""

import importlib

from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase

from apps.lookups.constants import LookupTypeCode
from apps.lookups.models import LookupValue

User = get_user_model()
PASSWORD = "Str0ng-Passw0rd!"

_default_lookups = importlib.import_module("apps.lookups.migrations.0002_default_lookups")
_notification_events = importlib.import_module("apps.lookups.migrations.0003_notification_events")


def create_default_lookups():
    """Create the same categories, priorities and e-mail events the data migrations create."""
    _default_lookups.create_defaults(django_apps, None)
    _notification_events.create_events(django_apps, None)


def make_user(username, role=User.Role.REQUESTER, **extra):
    return User.objects.create_user(
        username=username,
        email=extra.pop("email", f"{username}@acme-support.io"),  # deliverable-looking (tests never really send)
        password=PASSWORD,
        first_name=extra.pop("first_name", username.title()),
        role=role,
        **extra,
    )


def category(code="bug"):
    return LookupValue.objects.of_type(LookupTypeCode.TICKET_CATEGORY).get(code=code)


def priority(code="medium"):
    return LookupValue.objects.of_type(LookupTypeCode.TICKET_PRIORITY).get(code=code)


class ApiTestCase(APITestCase):
    """Base class: default lookups, one requester, one agent and API clients."""

    def setUp(self):
        create_default_lookups()
        self.requester = make_user("ragavan")
        self.other_requester = make_user("karthik")
        self.agent = make_user("meera", role=User.Role.AGENT)
        self.anon = APIClient()

    def client_for(self, user):
        client = APIClient()
        client.force_authenticate(user)
        return client
